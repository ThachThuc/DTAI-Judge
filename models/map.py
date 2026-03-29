#!/usr/bin/env python3
"""
Map module for the "botwar ship" game.
"""
import copy
from typing import Dict, List, Optional, Any

from items.treasure import Treasure
from models.coordinate import Coordinate
from models.cell import Cell
from utils.validators import validate_coordinate_bounds


class Map:
    """
    Map class representing the hexagonal grid of cells in the game.
    """

    def __init__(self, radius: int):
        """
        Initialize an empty map.
        """
        self.radius = radius
        self.cells = {}  # Dictionary of Coordinate to Cell

    def get_cell(self, coord: Coordinate) -> Cell:
        """
        Get the cell at the specified coordinate.
        
        Args:
            coord: The coordinate to get the cell for
            
        Returns:
            The cell at the coordinate (creates an empty one if not present)
        """
        if coord not in self.cells:
            self.cells[coord] = Cell()
        return self.cells[coord]

    def set_cell(self, coord: Coordinate, cell: Cell):
        """
        Set the cell at the specified coordinate.
        
        Args:
            coord: The coordinate to set the cell for
            cell: The cell to set
        """
        self.cells[coord] = cell

    def get_neighbors(self, coord: Coordinate) -> Dict[Coordinate, Cell]:
        """
        Get the neighboring cells of the specified coordinate.
        
        Args:
            coord: The coordinate to get neighbors for
            
        Returns:
            Dictionary of neighbor coordinates to cells
        """
        neighbors = {}
        for neighbor_coord in coord.neighbors():
            if self.is_valid_coordinate(neighbor_coord):
                neighbors[neighbor_coord] = self.get_cell(neighbor_coord)
        return neighbors

    def is_valid_coordinate(self, coord: Coordinate) -> bool:
        """
        Check if a coordinate is valid in the map.
        
        Args:
            coord: The coordinate to check
            
        Returns:
            True if the coordinate is valid, False otherwise
        """
        # Basic validation that cube coordinates sum to 0
        if not coord.validate():
            return False

        # Assuming the map has a maximum radius of 10 from center
        # This can be adjusted based on the actual map size
        return validate_coordinate_bounds(coord.q, coord.r, coord.s, self.radius)

    def manhattan_distance(self, coord1: Coordinate, coord2: Coordinate) -> int:
        """
        Calculate the Manhattan distance between two coordinates.
        
        Args:
            coord1: First coordinate
            coord2: Second coordinate
            
        Returns:
            Manhattan distance between the coordinates
        """
        return coord1.distance_to(coord2)

    def add_item(self, coord: Coordinate, item):
        """
        Add an item to the map at the specified coordinate.
        
        Args:
            coord: The coordinate to add the item at
            item: The item to add
        """
        cell = self.get_cell(coord)
        cell.set_item(item)

    def remove_item(self, coord: Coordinate):
        """
        Remove any item at the specified coordinate.
        
        Args:
            coord: The coordinate to remove the item from
        """
        cell = self.get_cell(coord)
        cell.clear_item()

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert the map to a list of cell dictionaries.
        
        Returns:
            List of cell dictionaries
        """
        result = []

        for coord, cell in self.cells.items():
            if not cell.is_empty():
                item = cell.get_item()

                # Get the item value string representation
                value = self._get_item_value(item)

                result.append({
                    "q": coord.q,
                    "r": coord.r,
                    "s": coord.s,
                    "value": value,
                    "is_treasure": isinstance(item, Treasure),
                })

        return result

    def _get_item_value(self, item) -> Any:
        """
        Get the value representation of an item.

        Args:
            item: The item to get the value for

        Returns:
            Value representation of the item
        """
        from items.gold import Gold
        from items.shield import Shield
        from items.danger import Danger
        from items.treasure import Treasure

        if isinstance(item, Gold):
            return item.value
        elif isinstance(item, Shield):
            return "S"
        elif isinstance(item, Danger):
            return "D"
        elif isinstance(item, Treasure):
            return item.value
        else:
            return 0
