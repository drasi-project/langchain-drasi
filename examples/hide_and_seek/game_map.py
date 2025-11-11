"""Game map definition and collision detection for the Invisible Hide and Seek game.

The game is played on a 64x24 grid with walls.
"""

import random
from typing import Tuple, Set

# Map dimensions
MAP_WIDTH = 64
MAP_HEIGHT = 24

# Wall segments defined as (x1, y1, x2, y2) for horizontal/vertical lines
WALLS = [
    # Top border
    (0, 0, MAP_WIDTH-1, 0),
    # Bottom border
    (0, MAP_HEIGHT-1, MAP_WIDTH-1, MAP_HEIGHT-1),
    # Left border
    (0, 0, 0, MAP_HEIGHT-1),
    # Right border
    (MAP_WIDTH-1, 0, MAP_WIDTH-1, MAP_HEIGHT-1),

    # Internal walls - row 1-3
    (26, 1, 26, 3),
    (46, 1, 46, 3),

    # Horizontal wall - row 4
    (0, 4, 11, 4),
    (16, 4, 26, 4),
    (32, 4, 46, 4),
    (51, 4, MAP_WIDTH-1, 4),

    # Internal walls - row 5-8
    (11, 5, 11, 8),
    (26, 5, 26, 6),
    (46, 5, 46, 8),

    # Horizontal wall - row 9
    (0, 9, 8, 9),
    (16, 9, 26, 9),
    (30, 9, 46, 9),
    (51, 9, 58, 9),

    # Horizontal wall - row 13
    #(0, 13, MAP_WIDTH-1, 13),
]


def _generate_wall_cells() -> Set[Tuple[int, int]]:
    """Generate a set of all wall cell coordinates."""
    wall_cells = set()
    for wall in WALLS:
        x1, y1, x2, y2 = wall
        if x1 == x2:  # Vertical wall
            for y in range(min(y1, y2), max(y1, y2) + 1):
                wall_cells.add((x1, y))
        else:  # Horizontal wall
            for x in range(min(x1, x2), max(x1, x2) + 1):
                wall_cells.add((x, y1))
    return wall_cells


# Pre-compute wall cells for efficient collision detection
WALL_CELLS = _generate_wall_cells()


def is_wall(x: int, y: int) -> bool:
    """Check if a position is a wall."""
    return (x, y) in WALL_CELLS


def is_valid_position(x: int, y: int) -> bool:
    """Check if a position is valid (within bounds and not a wall)."""
    if x < 0 or x >= MAP_WIDTH or y < 0 or y >= MAP_HEIGHT:
        return False
    return not is_wall(x, y)


def get_random_spawn_position() -> Tuple[int, int]:
    """Get a random valid spawn position that is not a wall."""
    while True:
        x = random.randint(1, MAP_WIDTH - 2)
        y = random.randint(1, MAP_HEIGHT - 2)
        if is_valid_position(x, y):
            return x, y


def get_map_string() -> str:
    """Return a string representation of the map for debugging."""
    lines = []
    for y in range(MAP_HEIGHT):
        line = ""
        for x in range(MAP_WIDTH):
            if is_wall(x, y):
                line += "#"
            else:
                line += " "
        lines.append(line)
    return "\n".join(lines)


def get_adjacent_positions(x: int, y: int) -> list[Tuple[int, int]]:
    """Get all valid adjacent positions (up, down, left, right)."""
    candidates = [
        (x, y - 1),  # up
        (x, y + 1),  # down
        (x - 1, y),  # left
        (x + 1, y),  # right
    ]
    return [(cx, cy) for cx, cy in candidates if is_valid_position(cx, cy)]


def distance(x1: int, y1: int, x2: int, y2: int) -> float:
    """Calculate Manhattan distance between two positions."""
    return abs(x1 - x2) + abs(y1 - y2)
