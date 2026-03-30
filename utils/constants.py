#!/usr/bin/env python3
"""
Constants module for the "botwar ship" game.
"""

# Game constants
import os
from pathlib import Path
import pwd
from zoneinfo import ZoneInfo


TOTAL_GOLD = 300
MAX_MISSILES = 6
MAX_MISSILES_EACH_TURN = 2
MAP_RADIUS = 10
NUM_OF_PLAYERS = 3

# Item values
MIN_GOLD_VALUE = 1
MAX_GOLD_VALUE = 6


# Treasure appearance
TREASURE_MIN_THRESHOLD = 0.5  # K*0.5 where K is max moves
TREASURE_MAX_THRESHOLD = 0.6  # K*0.6
TREASURE_MIN_VALUE = 10
TREASURE_VALUE_DIVISOR = 12  # max(d/12, 10) where d is total gold collected

# Gold distribution
GOLD_DISTRIBUTION_RADIUS = 3  # Manhattan distance for distributing lost gold
TIMEOUT = 1.5  # Timeout for agent execution in seconds

# Execute agent config
JUDGE_DIR = Path(os.getcwd()) / "runguard" / "judgedir"
RUNGUARD_CMD = f'sudo -n runguard/runguard -r "{JUDGE_DIR}" --filesize=4194304 --streamsize=1024 --memsize=4194304 --no-core --walltime=1.5 --user={pwd.getpwuid(os.getuid())[0]}'

# data/matches/<id>/info.json
MATCH_INFO_STATUS_RUNNING = "RUNNING"
MATCH_INFO_STATUS_COMPLETED = "COMPLETED"
MATCH_INFO_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

