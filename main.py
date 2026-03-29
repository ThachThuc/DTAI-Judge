#!/usr/bin/env python3
"""
Entry point for the "botwar ship" game.
"""
import argparse
import os
import sys

from judger.judger import Judger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="botwar ship - Hexagonal grid-based strategy game")
    parser.add_argument("--map", required=True, help="Path to the map JSON file")
    parser.add_argument("--agents", nargs=3, required=True, help="Paths to the three agent executables")
    parser.add_argument("--output", required=True, help="Output directory for game logs")
    return parser.parse_args()


def main():
    """Main function to start the game."""
    args = parse_args()

    os.makedirs(args.output, exist_ok=True)

    step0 = os.path.join(args.output, "0.json")
    if os.path.exists(step0):
        print(
            f"Error: step 0 already exists ({step0}). "
            "Use a different --output directory or remove existing logs.",
            file=sys.stderr,
        )
        sys.exit(1)

    judger = Judger(args.agents, args.map, args.output)
    judger.run_game()


if __name__ == "__main__":
    main()
