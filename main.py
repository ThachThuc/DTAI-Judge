#!/usr/bin/env python3
"""
Entry point for the "botwar ship" game.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from judger.judger import Judger
from utils.constants import MATCH_INFO_STATUS_RUNNING, MATCH_INFO_TZ


def _match_created_at_iso() -> str:
    """Local Vietnam time (UTC+7) when the match is created (written to info.json)."""
    return datetime.now(MATCH_INFO_TZ).replace(microsecond=0).isoformat()


def _agent_display_name(agent_path: str) -> str:
    """Label for info.json agent field: bundle directory name, or executable file stem."""
    p = Path(agent_path).expanduser().resolve()
    if p.is_dir():
        return p.name
    stem = p.stem
    return stem if stem else p.name


def write_match_info(
    output_dir: str,
    map_path: str,
    players: list[str],
    agent_paths: list[str],
) -> None:
    """
    Write {output_dir}/info.json (map id + per-slot player id and agent name).
    Agent name is taken from the agent path (folder name or file stem).
    """
    if len(players) != 3 or len(agent_paths) != 3:
        raise ValueError("players and agent_paths must each have length 3")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    map_id = Path(map_path).stem
    agents = [
        {"player": players[i], "agent": _agent_display_name(agent_paths[i])}
        for i in range(3)
    ]
    (out / "info.json").write_text(
        json.dumps(
            {
                "map": map_id,
                "agents": agents,
                "status": MATCH_INFO_STATUS_RUNNING,
                "created_at": _match_created_at_iso(),
            },
            ensure_ascii=False,
            indent=4,
        )
        + "\n",
        encoding="utf-8",
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="botwar ship - Hexagonal grid-based strategy game")
    parser.add_argument("--map", required=True, help="Path to the map JSON file")
    parser.add_argument(
        "--agents",
        nargs=3,
        required=True,
        help="Paths to the three agent executables or bundles",
    )
    parser.add_argument(
        "--players",
        nargs=3,
        metavar=("P1", "P2", "P3"),
        default=["P1", "P2", "P3"],
        help="Three player ids for match metadata (one per slot)",
    )
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
    write_match_info(args.output, args.map, list(args.players), list(args.agents))

    judger = Judger(args.agents, args.map, args.output)
    judger.run_game()


if __name__ == "__main__":
    main()
