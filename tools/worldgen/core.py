"""Shared grid primitives for the world generator.

Extracted from tools/gen_valley.py (the proven valley machinery) and
parameterized: no module-level W/H, everything works on a Grid. Determinism
is absolute — the only randomness source is the seeded rng handed in by the
caller, so the same brief + seed always produces byte-identical maps (CI and
composites depend on this).
"""


class Grid:
    def __init__(self, width, height, fill="."):
        self.w = width
        self.h = height
        self.g = [[fill for _ in range(width)] for _ in range(height)]

    def get(self, x, y, default="~"):
        if 0 <= y < self.h and 0 <= x < self.w:
            return self.g[y][x]
        return default  # out of bounds reads as water (matches preview rule)

    def put(self, x, y, ch):
        if 0 <= y < self.h and 0 <= x < self.w:
            self.g[y][x] = ch

    def put_grass(self, x, y, ch):
        """Place only on open grass; True on success."""
        if 0 <= y < self.h and 0 <= x < self.w and self.g[y][x] == ".":
            self.g[y][x] = ch
            return True
        return False

    def put_water(self, x, y, ch):
        if 0 <= y < self.h and 0 <= x < self.w and self.g[y][x] == "~":
            self.g[y][x] = ch
            return True
        return False

    def text(self):
        return "\n".join("".join(r) for r in self.g) + "\n"


def rrect(grid, x0, y0, x1, y1, r, ch, only="."):
    """Rounded-rectangle fill — long flat sides + rounded corners so shores
    read smooth (few 45-degree stair runs). Straight from gen_valley."""
    for y in range(max(0, y0), min(grid.h, y1 + 1)):
        for x in range(max(0, x0), min(grid.w, x1 + 1)):
            dx = max(0, (x0 + r) - x, x - (x1 - r))
            dy = max(0, (y0 + r) - y, y - (y1 - r))
            if dx * dx + dy * dy <= r * r and (only is None or grid.g[y][x] == only):
                grid.g[y][x] = ch


EDGE_MASKS = {1, 2, 4, 8, 5, 9, 6, 10}


def _is_water(grid, x, y):
    return grid.get(x, y, "~") in "~B"


def fix_water(grid):
    """Erode thin water fingers (bad autotile masks) into grass -> clean blobs."""
    changed = True
    while changed:
        changed = False
        for y in range(grid.h):
            for x in range(grid.w):
                if grid.g[y][x] != "~":
                    continue
                m = 0
                if not _is_water(grid, x, y - 1):
                    m |= 1
                if not _is_water(grid, x, y + 1):
                    m |= 2
                if not _is_water(grid, x + 1, y):
                    m |= 4
                if not _is_water(grid, x - 1, y):
                    m |= 8
                if m and m not in EDGE_MASKS:
                    grid.g[y][x] = "."
                    changed = True


def sweep_isolated_water(grid, min_size=20):
    """Flood-fill every water region; anything smaller than a real lake/river
    is a stray -> back to grass (the NW-lake-corner bug class)."""
    seen = set()
    for sy in range(grid.h):
        for sx in range(grid.w):
            if grid.g[sy][sx] in "~B" and (sx, sy) not in seen:
                stack, comp = [(sx, sy)], []
                seen.add((sx, sy))
                while stack:
                    x, y = stack.pop()
                    comp.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if (
                            0 <= ny < grid.h
                            and 0 <= nx < grid.w
                            and grid.g[ny][nx] in "~B"
                            and (nx, ny) not in seen
                        ):
                            seen.add((nx, ny))
                            stack.append((nx, ny))
                if len(comp) < min_size:
                    for x, y in comp:
                        grid.g[y][x] = "."


def widen_walkables(grid, ch="#"):
    """Kill 1-wide pinches in a walkable band: any ch cell with no orthogonal
    ch neighbor on one axis gets a partner below/right (H1: regions >= 2 wide)."""
    for y in range(grid.h):
        for x in range(grid.w):
            if grid.g[y][x] != ch:
                continue
            if grid.get(x - 1, y, "") != ch and grid.get(x + 1, y, "") != ch:
                if grid.get(x + 1, y, "") == ".":
                    grid.g[y][x + 1] = ch
            if grid.get(x, y - 1, "") != ch and grid.get(x, y + 1, "") != ch:
                if grid.get(x, y + 1, "") == ".":
                    grid.g[y + 1][x] = ch
