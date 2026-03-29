#!/usr/bin/env python3
"""
Judger module for the "botwar ship" game.
"""
import json
import logging
import os
import random
import shutil
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List

from judger.file_handler import FileHandler
from judger.game_state import GameState
from models.coordinate import Coordinate
from models.move import Move
from utils.constants import *
from utils.system import subprocess_args
from utils.validators import validate_team_constraints

# set tmpdir for runguard
os.environ["TMPDIR"] = os.path.join(JUDGE_DIR, "tmp")


def _agent_storage_dir(agent_path: str) -> str:
    """Directory holding STATE.OUT: bundle folder for onedir agents, else parent of the file."""
    p = os.path.abspath(agent_path)
    return p if os.path.isdir(p) else os.path.dirname(p)


class Judger:
    """
    Judger: game rules, state updates, and orchestration (agent execution, runguard).
    """

    def __init__(
        self,
        agent_paths: List[str],
        map_path: str,
        log_dir: str,
    ):
        """
        Args:
            agent_paths: Paths to the three agent executables
            map_path: Path to the map JSON file
            log_dir: Directory for exporting game data
        """
        self.agent_paths = agent_paths
        self.log_dir = log_dir
        self.logger = logging.getLogger("Judger")

        self.file_handler = FileHandler()

        map_data = self.file_handler.read_json(map_path)

        if "max_moves" not in map_data:
            raise ValueError("Required parameter 'max_moves' not found in map file")
        max_moves = map_data["max_moves"]

        if "map_radius" not in map_data:
            raise ValueError("Required parameter 'map_radius' not found in map file")
        map_radius = map_data["map_radius"]

        self.game_state = GameState(radius=map_radius, max_moves=max_moves)

        self.game_state._initialize_map(map_data)

        self.game_state._initialize_players()

        self.step_report = list()

        self.logger.info(f"Game initialized with map: {map_path}")

    def run_game(self):
        """
        Run the game until completion (all ships sink or max moves reached).
        """
        self.cleanup_state_files()

        start_positions = self.execute_agents()

        self.process_start_positions(start_positions)

        self.export_step_report(self.log_dir)

        self.game_state.transform_to_next_turn()

        while not self.game_state.check_game_end():
            moves = self.execute_agents()

            self.process_turn(moves)

            self.export_step_report(self.log_dir)

            self.game_state.transform_to_next_turn()

        self.cleanup_state_files()

    def cleanup_state_files(self):
        """Clean up any state files generated during the game."""
        for agent_path in self.agent_paths:
            state_file = os.path.join(_agent_storage_dir(agent_path), "STATE.OUT")
            if os.path.exists(state_file):
                os.remove(state_file)

    def execute_agents(self) -> list[str]:
        """Execute all agent programs and get their responses."""
        with ProcessPoolExecutor(max_workers=NUM_OF_PLAYERS) as executor:
            return list(executor.map(self.execute_agent, range(NUM_OF_PLAYERS)))

    def execute_agent(self, id: int) -> str:
        """
        Execute an agent program and get its response.

        Args:
            id: index of player

        Returns:
            The agent's response as a string
        """
        if id < 0 or id >= len(self.game_state.players):
            return ""
        if not self.game_state.players[id].alive:
            return ""

        agent_path = self.agent_paths[id]
        input_data = self.generate_agent_inputs(id)
        try:
            # Create a temporary file for the input
            input_file = "MAP.INP"
            # get agent directory path
            agent_path = os.path.abspath(agent_path)
            agent_dir = os.path.dirname(agent_path)

            with open(os.path.join(agent_dir, input_file), "w") as f:
                f.write(input_data)

            # Execute the agent with the input file
            result = subprocess.run(
                [agent_path, input_file],
                cwd=agent_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.logger.error(f"Agent execution failed: {result.stderr}")
                return ""

            output_file = "ACT.OUT"
            with open(os.path.join(agent_dir, output_file), "r") as f:
                return f.read()

        except subprocess.TimeoutExpired:
            self.logger.error(f"Agent execution timed out: {agent_path}")
            return ""
        except Exception as e:
            self.logger.error(f"Error executing agent: {str(e)}")
            return ""

    def process_start_positions(self, position_strings: List[str]):
        """
        Process the starting positions chosen by the agents.

        Args:
            position_strings: List of starting positions for each player
        """
        for i, position_str in enumerate(position_strings):
            try:
                q, r, s = map(int, position_str.strip().split())
            except Exception:
                q, r, s = 0, 0, 0
            coord = Coordinate(q, r, s).spin(i)
            player = self.game_state.players[i]

            valid_position = True

            if not self.game_state.map.is_valid_coordinate(coord):
                valid_position = False

            if not validate_team_constraints(i + 1, coord.q, coord.r, coord.s):
                valid_position = False

            cell = self.game_state.map.get_cell(coord)
            if not cell.is_empty():
                valid_position = False

            if not valid_position:
                coord = self.get_random_start_position(team_id=i + 1)
            player.position = coord

        self.game_state.started = True
        self.mark_substep()

    def get_random_start_position(self, team_id: int) -> Coordinate:
        """
        Get a random starting position for the specified team.

        Args:
            team_id: The team ID

        Returns:
            Random starting position for the team
        """
        empty_cells = []
        for q in range(-self.game_state.map.radius, self.game_state.map.radius + 1):
            for r in range(
                max(-self.game_state.map.radius, -q - self.game_state.map.radius),
                min(self.game_state.map.radius + 1, -q + self.game_state.map.radius + 1),
            ):
                s = -q - r
                coord = Coordinate(q, r, s)
                if self.game_state.map.is_valid_coordinate(coord):
                    cell = self.game_state.map.get_cell(coord)
                    if cell.is_empty():
                        empty_cells.append(coord)

        valid_cells = []
        for coord in empty_cells:
            q, r, s = coord.q, coord.r, coord.s
            if validate_team_constraints(team_id, q, r, s):
                valid_cells.append(coord)

        return random.choice(valid_cells)

    def process_turn(self, moves: List[str]) -> GameState:
        """
        Process a turn with the provided moves.

        Args:
            moves: List of move strings from the agents

        Returns:
            Updated game state
        """
        parsed_moves = []
        for i, move_str in enumerate(moves):
            if self.game_state.players[i].alive and move_str:
                move = self.file_handler.parse_agent_input(move_str, i)
                parsed_moves.append(move)
            else:
                parsed_moves.append(Move())

        self.mark_substep()

        self.game_state.apply_movements(parsed_moves)

        self.game_state.check_collisions()

        self.game_state.apply_item_effects()
        self.mark_substep()

        self.game_state.handle_missiles()
        self.mark_substep()

        self.game_state.spawn_treasure_if_scheduled()
        self.mark_substep()

        return self.game_state

    def generate_agent_inputs(self, team_id: int) -> str:
        """
        Generate input strings for all agents based on the current game state.

        Args:
            team_id: Team ID of the agent

        Returns:
            Input string for the agent
        """
        return self.file_handler.format_agent_output(self.game_state, team_id)

    def mark_substep(self):
        """Mark substep in step report."""
        self.step_report.append(self.game_state.to_dict())

    def export_step_report(self, log_dir: str):
        """Export the step report in result forder."""
        log_path = os.path.join(log_dir, f"{self.game_state.turn}.json")
        with open(log_path, "w") as f:
            json.dump(self.step_report, f)
        self.step_report.clear()
