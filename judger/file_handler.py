#!/usr/bin/env python3
"""
File handler module for the "botwar ship" game.
"""
import json
from typing import Dict, Any, List

from models.move import Move
from models.coordinate import Coordinate
from models.direction import Direction
from judger.game_state import GameState


class FileHandler:
    """
    FileHandler class for handling file I/O operations in the game.
    """

    def read_json(self, path: str) -> Dict[str, Any]:
        """
        Read a JSON file and return its contents as a dictionary.
        
        Args:
            path: Path to the JSON file
            
        Returns:
            Dictionary containing the JSON data
        """
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def write_json(self, data: Dict[str, Any], path: str):
        """
        Write a dictionary to a JSON file.
        
        Args:
            data: Dictionary to write
            path: Path to the output JSON file
        """
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def read_txt(self, path: str) -> str:
        """
        Read a text file and return its contents as a string.
        
        Args:
            path: Path to the text file
            
        Returns:
            String containing the file contents
        """
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_txt(self, data: str, path: str):
        """
        Write a string to a text file.
        
        Args:
            data: String to write
            path: Path to the output text file
        """
        with open(path, 'w', encoding='utf-8') as f:
            f.write(data)

    def parse_agent_input(self, input_str: str, team_id: int) -> Move:
        """
        Parse agent input string into a Move object.
        
        Format for move phase:
        [direction] [missile_targets]
        
        Direction is one of: NE, E, SE, SW, W, NW
        Missile targets are space-separated coordinates: q r s
        
        Args:
            input_str: Input string from the agent
            team_id: Team ID (0-2)
            
        Returns:
            Move object representing the parsed move
        """
        lines = input_str.strip().split('\n')

        # Parse direction
        direction_str = lines[0].strip().upper()

        direction = Direction.O
        for d in Direction:
            if d.name == direction_str:
                direction = d.spin(team_id)
                break

        # Parse missile targets if any
        missile_targets = []

        if len(lines) > 1:
            if lines[1].strip().isdigit():
                for idx in range(int(lines[1])):
                    try:
                        q, r, s = map(int, lines[2 + idx].strip().split())
                        missile_targets.append(Coordinate(q, r, s).spin(team_id))
                    except ValueError:
                        # Invalid, skip all missile targets
                        missile_targets = []
                        break

        return Move(direction, missile_targets)

    def format_agent_output(self, state: GameState, team_id: int) -> str:
        """
        Format game state as input for the specified team's agent.
        
        Phase 0 format (position selection):
        N K P
        T
        C
        q r s value
        ...
        
        Phase 1 format (movement):
        N K P
        q0 r0 s0 A0 G0 S0 R0
        q1 r1 s1 A1 G1 S1 R1
        q2 r2 s2 A2 G2 S2 R2
        C
        q r s value
        ...
        
        Args:
            state: Current game state
            team_id: Team ID (0-2)
            
        Returns:
            Formatted string for the agent
        """
        output_lines = []

        if not state.started:
            # Phase 0: Position selection
            output_lines.append(f"{state.map.radius} {state.max_moves} 0")
            output_lines.append("1")

        else:
            # Phase 1: Movement
            output_lines.append(f"{state.map.radius} {state.moves_left} 1")

            # Players info
            players = [state.players[(team_id + i) % 3] for i in range(3)]
            coord = players[0].position.spin(-team_id)
            output_lines.append(
                f"{coord.q} {coord.r} {coord.s} {players[0].gold} {int(players[0].shield)} {players[0].missiles}")
            for player in players[1:]:
                coord = player.position.spin(-team_id)
                output_lines.append(
                    f"{coord.q} {coord.r} {coord.s} {int(player.alive)} {player.gold} {int(player.shield)}")

        # Count non-empty cells
        non_empty_cells = []
        for coord, cell in state.map.cells.items():
            if not cell.is_empty():
                item = cell.get_item()
                value = self._get_item_value_str(item)
                non_empty_cells.append((coord.spin(-team_id), value))

        output_lines.append(str(len(non_empty_cells)))

        # Add the cell data
        for coord, value in non_empty_cells:
            output_lines.append(f"{coord.q} {coord.r} {coord.s} {value}")

        return '\n'.join(output_lines)

    def _get_item_value_str(self, item) -> str:
        """
        Get the string representation of an item's value.

        Args:
            item: Item object

        Returns:
            String representation of the item value
        """
        from items.gold import Gold
        from items.shield import Shield
        from items.danger import Danger
        from items.treasure import Treasure

        if isinstance(item, Gold):
            return str(item.value)
        elif isinstance(item, Shield):
            return "S"
        elif isinstance(item, Danger):
            return "D"
        elif isinstance(item, Treasure):
            return str(item.value)
        else:
            return "0"
