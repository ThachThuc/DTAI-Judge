#!/usr/bin/env python3
"""
Coordinate module for the "botwar ship" game.
"""
from typing import List, Tuple

from models.direction import Direction
from utils.validators import validate_coordinate


class Coordinate:
    """
    Coordinate class representing a position in the hexagonal grid
    using cube coordinates (q, r, s).
    """

    def __init__(self, q: int, r: int, s: int):
        """
        Initialize a coordinate with q, r, s values.
        
        Args:
            q: q-coordinate
            r: r-coordinate
            s: s-coordinate
        """
        self.q = q
        self.r = r
        self.s = s

    def validate(self) -> bool:
        """
        Validate that q + r + s = 0 (required for cube coordinates).
        
        Returns:
            True if the coordinate is valid, False otherwise
        """
        return validate_coordinate(self.q, self.r, self.s)

    def next(self, direction: 'Direction') -> 'Coordinate':
        """
        Get the coordinate in the specified direction.

        Args:
            direction: Direction to move in

        Returns:
            Coordinate in the specified direction
        """
        coordinate = direction.to_coordinate()
        return Coordinate(self.q + coordinate[0], self.r + coordinate[1], self.s + coordinate[2])

    def neighbors(self) -> List['Coordinate']:
        """
        Get the six neighboring coordinates.
        
        Returns:
            List of six neighboring coordinates
        """
        return [self.next(d) for d in Direction.all_non_origin()]

    def distance_to(self, other: 'Coordinate') -> int:
        """
        Calculate the Manhattan distance to another coordinate.
        
        Args:
            other: Another coordinate
            
        Returns:
            Manhattan distance to the other coordinate
        """
        return (abs(self.q - other.q) + abs(self.r - other.r) + abs(self.s - other.s)) // 2

    def spin(self, steps: int) -> 'Coordinate':
        """
        Spin the coordinate around the origin by 120 degrees per step.

        Args:
            steps: Number of steps to spin (positive for clockwise, negative for counterclockwise)

        Returns:
            Spun coordinate
        """
        q, r, s = self.q, self.r, self.s
        while steps < 0:
            steps += 3
        while steps > 0:
            q, r, s = s, q, r
            steps -= 1
        return Coordinate(q, r, s)

    def to_tuple(self) -> Tuple[int, int, int]:
        """
        Convert the coordinate to a tuple.

        Returns:
            Tuple representation of the coordinate
        """
        return self.q, self.r, self.s

    def __eq__(self, other):
        """Check if two coordinates are equal."""
        if not isinstance(other, Coordinate):
            return False
        return self.q == other.q and self.r == other.r and self.s == other.s

    def __hash__(self):
        """Hash function for using coordinates as dictionary keys."""
        return hash((self.q, self.r, self.s))

    def __str__(self):
        """String representation of the coordinate."""
        return f"({self.q}, {self.r}, {self.s})"

    def __repr__(self):
        """Detailed string representation of the coordinate."""
        return f"Coordinate(q={self.q}, r={self.r}, s={self.s})"
