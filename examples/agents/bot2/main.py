#!/usr/bin/env python3
from collections import deque
import random

def read_tokens(file):
    return file.readline().strip().split()


def in_hexagon(q, r, s, N):
    # Condition for a cell to be within the hexagonal map: q + r + s == 0 and max(|q|,|r|,|s|) <= N
    return (q + r + s == 0) and (max(abs(q), abs(r), abs(s)) <= N)


directions = {
    "E": (1, 0, -1),
    "NE": (1, -1, 0),
    "NW": (0, -1, 1),
    "W": (-1, 0, 1),
    "SW": (-1, 1, 0),
    "SE": (0, 1, -1),
}


def choose_starting_position(N, team, non_empty):
    candidates = []
    # Iterate over all valid cells in the map according to Cube coordinates system
    for q in range(-N, N + 1):
        for r in range(-N, N + 1):
            s = -q - r
            if not in_hexagon(q, r, s, N):
                continue
            # Condition based on team:
            if team == 1 and not (q > 0 > r):
                continue
            if team == 2 and not (r > 0 > s):
                continue
            if team == 3 and not (s > 0 > q):
                continue
            # The cell must be empty (not in non_empty)
            if (q, r, s) in non_empty:
                continue
            candidates.append((q, r, s))
    # Prioritize the cells closest to the origin (by the sum of distances)
    candidates.sort(key=lambda pos: (abs(pos[0]) + abs(pos[1]) + abs(pos[2]), pos))
    if candidates:
        return candidates[0]
    return (0, 0, 0)


def bfs_move(N, start, board, shield):
    """
    Use BFS to find a safe and beneficial "move."
    The goal is to find a cell containing gold (numeric value >= 1) or a shield cell ("S").
    If no such cell is found, return the first adjacent safe cell.
    """
    queue = deque([start])
    parent = {start: None}
    direct = {start: None}
    target = None
    direction_items = list(directions.items())
    random.shuffle(direction_items)

    while queue:
        current = queue.popleft()
        # If it's not the start cell, check if the current cell is the target
        if current != start:
            if current in board:
                val = board[current]
                # A cell with gold (numeric value) or shield "S" is considered a target
                if (val.isdigit() and int(val) > 0) or (val == "S"):
                    target = current
                    break
        # Explore adjacent cells in the 6 directions of the Cube system
        cur_q, cur_r, cur_s = current

        for d, (dq, dr, ds) in direction_items:
            nxt = (cur_q + dq, cur_r + dr, cur_s + ds)
            if nxt in parent:
                continue  # already visited
            if not in_hexagon(nxt[0], nxt[1], nxt[2], N):
                continue
            # Check safety: if the cell contains Danger ('D') and the ship has no shield -> unsafe
            cell_val = board.get(nxt, "0")
            if cell_val == "D" and not shield:
                continue
            parent[nxt] = current
            direct[nxt] = d
            queue.append(nxt)

    # If a target cell is found, reconstruct the path from start to target
    if target:
        path = []
        cur = target
        while cur is not None:
            path.append(direct[cur])
            cur = parent[cur]
        # The move is the first step on the path (if there are more than one cell)
        if len(path) >= 2:
            return path[len(path) - 2]
    return "O"


def choose_move(N, cur_pos, shield, board):
    # Use BFS to determine the move from the current position
    return bfs_move(N, cur_pos, board, shield)


def main():
    with open("MAP.INP", "r") as fin:
        tokens = read_tokens(fin)
        if len(tokens) < 3:
            return
        N, K, P = map(int, tokens)

        if P == 0:
            # Phase: choose starting position
            team_line = fin.readline().strip()
            if not team_line:
                return
            team = int(team_line)
            C = int(fin.readline().strip())
            non_empty = set()
            for _ in range(C):
                line = fin.readline().strip().split()
                if len(line) < 4:
                    continue
                q, r, s = int(line[0]), int(line[1]), int(line[2])
                # Value is not used for position selection
                non_empty.add((q, r, s))
            chosen = choose_starting_position(N, team, non_empty)
            with open("ACT.OUT", "w") as fout:
                fout.write(f"{chosen[0]} {chosen[1]} {chosen[2]}")
        else:
            # Phase: move
            # The second line contains the current ship information
            tokens_ship = read_tokens(fin)
            if len(tokens_ship) < 6:
                return
            cur_q, cur_r, cur_s = int(tokens_ship[0]), int(tokens_ship[1]), int(tokens_ship[2])
            # A: alive, G: gold, S: shield status, M: number of missiles
            shield = bool(int(tokens_ship[4]))
            num_missiles = int(tokens_ship[5])
            enemy_states = []
            for _ in range(2):
                tokens_enemy_ship = read_tokens(fin)
                if len(tokens_enemy_ship) < 6:
                    return
                enemy_states.append(tuple(map(int, tokens_enemy_ship)))
            # Read information about non-empty cells on the board (excluding the ship)
            C = int(fin.readline().strip())
            board = {}
            for _ in range(C):
                line = fin.readline().strip().split()
                if len(line) < 4:
                    continue
                q, r, s = int(line[0]), int(line[1]), int(line[2])
                value = line[3]
                board[(q, r, s)] = value
            chosen = choose_move(N, (cur_q, cur_r, cur_s), shield, board)

            with open("ACT.OUT", "w") as fout:
                fout.write(f"{chosen}")


if __name__ == "__main__":
    main()
