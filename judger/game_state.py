#!/usr/bin/env python3
"""
Game state module for the "botwar ship" game.
"""
import json
import math
import random
from typing import List, Dict, Any

from items.danger import Danger
from items.gold import Gold
from items.shield import Shield
from items.treasure import Treasure
from models.coordinate import Coordinate
from models.map import Map
from models.move import Move
from models.player import Player
from utils.constants import *


class GameState:
    """
    GameState class representing the current state of the game.
    """

    def __init__(self, radius: int, max_moves: int):
        """
        Initialize a new game state.
        """
        self.started = False
        self.map = Map(radius=radius)
        self.players = list[Player] ()
        self.turn = 0
        self.moves_left = max_moves + 1 # +1 for the starting position
        self.max_moves = max_moves
        self._initialize_treasure_appearance_turn(max_moves)

    def _initialize_treasure_appearance_turn(self, max_moves: int):
        """
        Initialize the treasure appearance turn.
        Calculate the treasure appearance turn based on the max moves.

        Args:
            max_moves: The maximum number of moves in the game
        """
        min_threshold = math.ceil(max_moves * TREASURE_MIN_THRESHOLD)
        max_threshold = math.floor(max_moves * TREASURE_MAX_THRESHOLD)
        self.treasure_appearance_turn = random.randint(min_threshold, max_threshold)

    def spawn_treasure_if_scheduled(self):
        """
        When the current turn matches treasure_appearance_turn, create and place
        treasure at the map center (no-op otherwise).
        """
        if self.turn != self.treasure_appearance_turn:
            return

        total_gold = sum(player.gold for player in self.players)
        treasure_value = max(total_gold // TREASURE_VALUE_DIVISOR, TREASURE_MIN_VALUE)

        center = Coordinate(0, 0, 0)
        cell = self.map.get_cell(center)

        if isinstance(cell.get_item(), Gold):
            treasure_value += cell.get_item().value
        if not cell.is_empty():
            cell.clear_item()
        self.map.add_item(center, Treasure(treasure_value))

    def transform_to_next_turn(self):
        """
        Advance turn counter, decrement moves left, clear per-turn player markers.
        """
        self.turn += 1
        self.moves_left -= 1
        for player in self.players:
            player.missiles_fired = []
            player.distributed_gold_to = []

    def validate_missile(self, player: Player, targets: List[Coordinate]) -> bool:
        """
        Check if missile targets are valid for a player.
        """
        if not player.alive:
            return False
        if len(targets) == 0 or len(targets) > MAX_MISSILES_EACH_TURN:
            return False
        if player.missiles < len(targets):
            return False
        cells = [(t.q, t.r, t.s) for t in targets]
        if len(cells) != len(set(cells)):
            return False
        for target in targets:
            if not self.map.is_valid_coordinate(target) or target == player.position:
                return False
        return True

    def apply_movements(self, moves: List[Move]):
        """
        For each player: move ship from move.direction, then record valid missile fire
        (missiles_fired, missiles count). Resolution vs map/ships is handle_missiles().

        Args:
            moves: One Move per player, same order as self.players
        """
        for player in self.players:
            player.missiles_fired = []

        for i, player in enumerate(self.players):
            if player.alive and moves[i]:
                direction = moves[i].direction
                if direction:
                    player.move(direction, self.map)

        for i, move in enumerate(moves):
            player = self.players[i]
            targets = move.missile_targets
            if not self.validate_missile(player, targets):
                continue
            for target in move.missile_targets:
                player.missiles_fired.append(target)
            player.missiles -= len(move.missile_targets)

    def check_collisions(self):
        """
        Detect ship collisions: same final cell, or two ships swapping positions.
        """
        previous_positions = {
            i: self.players[i].previous_position
            for i in range(len(self.players))
            if self.players[i].previous_position
        }

        current_positions = {
            i: self.players[i].position
            for i in range(len(self.players))
        }

        for idx, player in enumerate(self.players):
            if not player.alive:
                continue
            position = player.position
            prev_position = player.previous_position

            for other_idx, other_position in current_positions.items():
                if idx != other_idx and position == other_position:
                    player.alive = False

            for other_idx, other_prev_position in previous_positions.items():
                other_position = current_positions[other_idx]
                if idx != other_idx and position == other_prev_position and prev_position == other_position:
                    player.alive = False

    def apply_item_effects(self):
        """
        Apply the effects of items at each alive player's cell.
        """
        for player in self.players:
            if not player.alive:
                continue

            cell = self.map.get_cell(player.position)
            if not cell.is_empty():
                item = cell.get_item()
                item = item.apply_effect(player, self.map)
                cell.set_item(item)

    def hit_by_missiles(self, positions: List[Coordinate]):
        """
        Update the map based on the missile.

        Args:
            positions: The array of positions of missile target.
        """
        for pos in positions:
            if self.map.is_valid_coordinate(pos):
                if isinstance(self.map.get_cell(pos).get_item(), Danger):
                    self.map.remove_item(pos)

    def handle_missiles(self):
        """
        Apply missile effects using each player's missiles_fired (set by apply_movements).
        """
        missile_targets: dict[Coordinate, int] = {}
        for player in self.players:
            for target in player.missiles_fired:
                missile_targets[target] = missile_targets.get(target, 0) + 1

        self.hit_by_missiles(missile_targets.keys())

        for player in self.players:
            pos = player.position
            if pos not in missile_targets:
                continue
            hit_count = missile_targets[pos]
            if hit_count <= 0:
                continue
            gold_lost = player.hit_by_missile(hit_count, self.moves_left)
            if gold_lost > 0:
                self._distribute_lost_gold(player, gold_lost)

    def _distribute_lost_gold(self, player: Player, gold_amount: int):
        """
        Distribute lost gold to nearby empty cells.

        Args:
            player: Player who lost the gold
            gold_amount: Amount of gold to distribute
        """
        position = player.position
        valid_cells: List[Coordinate] = []
        for q_offset in range(-GOLD_DISTRIBUTION_RADIUS, GOLD_DISTRIBUTION_RADIUS + 1):
            for r_offset in range(max(-GOLD_DISTRIBUTION_RADIUS, -q_offset - GOLD_DISTRIBUTION_RADIUS),
                                  min(GOLD_DISTRIBUTION_RADIUS + 1, -q_offset + GOLD_DISTRIBUTION_RADIUS + 1)):
                s_offset = -q_offset - r_offset

                if q_offset == 0 and r_offset == 0:
                    continue

                new_coord = Coordinate(
                    position.q + q_offset,
                    position.r + r_offset,
                    position.s + s_offset,
                )

                if not self.map.is_valid_coordinate(new_coord):
                    continue

                if any(p.position == new_coord for p in self.players):
                    continue

                cell = self.map.get_cell(new_coord)
                if cell.is_empty() \
                        or isinstance(cell.get_item(), Gold) \
                        or isinstance(cell.get_item(), Treasure):
                    valid_cells.append(new_coord)

        if not valid_cells:
            return

        player.distributed_gold_to = random.choices(valid_cells, k=gold_amount)
        for coord in player.distributed_gold_to:
            cell = self.map.get_cell(coord)
            if isinstance(cell.get_item(), Gold):
                gold_value = cell.get_item().value + 1
                cell.clear_item()
                self.map.add_item(coord, Gold(gold_value))
            elif isinstance(cell.get_item(), Treasure):
                gold_value = cell.get_item().value + 1
                cell.clear_item()
                self.map.add_item(coord, Treasure(gold_value))
            else:
                self.map.add_item(coord, Gold(1))

    def _initialize_map(self, map_data: Dict[str, Any]):
        """
        Initialize the map from the provided map data.
        
        Args:
            map_data: Map data from the JSON file
        """
        self.map = Map(radius=map_data["map_radius"])

        # Add cells to the map
        for cell_data in map_data.get("cells", []):
            q = cell_data.get("q", 0)
            r = cell_data.get("r", 0)
            s = cell_data.get("s", 0)
            value = cell_data.get("value", 0)

            coord = Coordinate(q, r, s)

            # Create the appropriate item based on the value
            if isinstance(value, int) and value > 0:
                self.map.add_item(coord, Gold(value))
            elif value == "S":
                self.map.add_item(coord, Shield())
            elif value == "D":
                self.map.add_item(coord, Danger())

    def _initialize_players(self):
        """
        Initialize the players for the game.
        """
        self.players = [Player(team_id=i, missiles=MAX_MISSILES) for i in range(1, NUM_OF_PLAYERS+1)]

    def check_game_end(self) -> bool:
        """
        Check if the game has ended (all ships sunk or max moves reached).

        Returns:
            True if the game has ended, False otherwise
        """
        # Check if there are no moves left
        if self.moves_left <= 0:
            return True

        # Check if all ships have sunk
        all_sunk = True
        for player in self.players:
            if player.alive:
                all_sunk = False
                break

        return all_sunk

    def to_json(self) -> str:
        """
        Convert the game state to a JSON string.

        Returns:
            JSON string representation of the game state
        """
        state_dict = self.to_dict()
        return json.dumps(state_dict, indent=2)

    # def from_json(self, json_str: str) -> 'GameState':
    #     """
    #     Load the game state from a JSON string.
    #
    #     Args:
    #         json_str: JSON string representation of the game state
    #
    #     Returns:
    #         The updated game state
    #     """
    #     state_dict = json.loads(json_str)
    #     return self.from_dict(state_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the game state to a dictionary.

        Returns:
            Dictionary representation of the game state
        """
        return {
            "players": [
                {
                    "q": player.position.q if player.position else 0,
                    "r": player.position.r if player.position else 0,
                    "s": player.position.s if player.position else 0,
                    "points": player.gold,
                    "shield": player.shield,
                    "alive": player.alive,
                    "missiles": player.missiles,
                    "missiles_fired": [
                        {"q": target.q, "r": target.r, "s": target.s}
                        for target in player.missiles_fired
                    ],
                    "distributed_gold_to": [
                        {"q": coord.q, "r": coord.r, "s": coord.s}
                        for coord in player.distributed_gold_to
                    ]
                }
                for i, player in enumerate(self.players)
            ],
            "map": {
                "end_game": self.check_game_end(),
                "moveleft": min(self.moves_left, self.max_moves),
                "current_step": self.turn,
                "max_moves": self.max_moves,
                "radius": self.map.radius,
                "cells": self.map.to_dict_list()
            }
        }
