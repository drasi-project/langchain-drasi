"""Pathfinding utilities for Terminator agents."""

from collections import deque

from game_map import (
    get_adjacent_positions,
    MAP_WIDTH,
    MAP_HEIGHT,
    WALL_CELLS,
)


def find_path_bfs(
    agent_id: str,
    start: tuple[int, int],
    goal: tuple[int, int]
) -> list[tuple[int, int]]:
    """Find shortest path from start to goal using BFS, avoiding walls."""
    if start == goal:
        print(f"[{agent_id}] BFS: start == goal at {start}")
        return []

    # Check if goal is a wall
    if goal in WALL_CELLS:
        print(f"[{agent_id}] BFS: goal {goal} is a WALL!")
        return []

    queue = deque([(start, [])])
    visited = {start}
    max_iterations = MAP_WIDTH * MAP_HEIGHT  # Safety limit

    iteration = 0
    while queue and iteration < max_iterations:
        iteration += 1
        (x, y), path = queue.popleft()

        # Check all adjacent positions
        for next_x, next_y in get_adjacent_positions(x, y):
            if (next_x, next_y) in visited:
                continue

            visited.add((next_x, next_y))
            new_path = path + [(next_x, next_y)]

            # Found the goal
            if (next_x, next_y) == goal:
                print(f"[{agent_id}] BFS: Found path in {iteration} iterations, {len(new_path)} steps")
                return new_path

            queue.append(((next_x, next_y), new_path))

    # No path found
    print(f"[{agent_id}] BFS: No path found from {start} to {goal} (visited {len(visited)} cells)")
    return []


def get_local_map_view(center_x: int, center_y: int, radius: int = 15) -> str:
    """Generate an ASCII map view centered on a position."""
    lines = []
    min_x = max(0, center_x - radius)
    max_x = min(MAP_WIDTH - 1, center_x + radius)
    min_y = max(0, center_y - radius)
    max_y = min(MAP_HEIGHT - 1, center_y + radius)

    lines.append(f"Map view centered at ({center_x},{center_y}), range x:{min_x}-{max_x}, y:{min_y}-{max_y}")

    for y in range(min_y, max_y + 1):
        line = f"{y:2d} "
        for x in range(min_x, max_x + 1):
            if x == center_x and y == center_y:
                line += "T"
            elif (x, y) in WALL_CELLS:
                line += "#"
            else:
                line += "."
        lines.append(line)

    return "\n".join(lines)
