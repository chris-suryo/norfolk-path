"""Organic placement primitives — the established algorithms, used deliberately.

- Bridson Poisson-disc sampling: even-but-organic point sets (no clumps, no
  grids) for trees/flowers/rocks. This is what kills the "scattered by a
  computer" look at the source instead of patching it afterward.
- Value-noise density field: low-frequency spatial variation so scatter is
  DENSER in some regions and sparser in others (rulebook S1 density gradients)
  rather than uniform everywhere.

Both take an explicit random.Random so generation stays deterministic per seed.
"""

import math


def poisson_disc(rng, width, height, radius, k=20):
    """Bridson's algorithm: points >= radius apart, blue-noise distributed."""
    cell = radius / math.sqrt(2.0)
    gw, gh = int(width / cell) + 1, int(height / cell) + 1
    grid = [[None] * gw for _ in range(gh)]
    points, active = [], []

    def fits(px, py):
        gx, gy = int(px / cell), int(py / cell)
        for ny in range(max(0, gy - 2), min(gh, gy + 3)):
            for nx in range(max(0, gx - 2), min(gw, gx + 3)):
                q = grid[ny][nx]
                if q is not None:
                    dx, dy = q[0] - px, q[1] - py
                    if dx * dx + dy * dy < radius * radius:
                        return False
        return True

    def add(px, py):
        points.append((px, py))
        active.append((px, py))
        grid[int(py / cell)][int(px / cell)] = (px, py)

    add(rng.uniform(0, width), rng.uniform(0, height))
    while active:
        i = rng.randrange(len(active))
        ax, ay = active[i]
        for _ in range(k):
            ang = rng.uniform(0, math.tau)
            d = rng.uniform(radius, 2 * radius)
            px, py = ax + math.cos(ang) * d, ay + math.sin(ang) * d
            if 0 <= px < width and 0 <= py < height and fits(px, py):
                add(px, py)
                break
        else:
            active.pop(i)
    return points


class NoiseField:
    """Smooth value noise in [0,1): random lattice values, bilinear blend."""

    def __init__(self, rng, width, height, scale=14.0):
        self.scale = scale
        self.gw = int(width / scale) + 2
        self.gh = int(height / scale) + 2
        self.v = [[rng.random() for _ in range(self.gw)] for _ in range(self.gh)]

    def at(self, x, y):
        fx, fy = x / self.scale, y / self.scale
        ix, iy = int(fx), int(fy)
        tx, ty = fx - ix, fy - iy
        tx = tx * tx * (3 - 2 * tx)  # smoothstep
        ty = ty * ty * (3 - 2 * ty)
        v00 = self.v[iy][ix]
        v10 = self.v[iy][ix + 1]
        v01 = self.v[iy + 1][ix]
        v11 = self.v[iy + 1][ix + 1]
        return (v00 * (1 - tx) + v10 * tx) * (1 - ty) + (v01 * (1 - tx) + v11 * tx) * ty


def jittered_polyline(rng, points, wobble=2.0, step=3):
    """Interpolate a path through control points with organic wobble — desire
    lines, not CAD lines (rulebook S6). Returns integer cells, slope-limited
    so a widened band stays autotile-safe."""
    out = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        dist = max(abs(x1 - x0), abs(y1 - y0))
        n = max(1, int(dist / step))
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            if 0 < i < n:  # never jitter the anchors
                y += math.sin(t * math.pi * 2 + x * 0.35) * wobble * 0.6
                y += (rng.random() - 0.5) * wobble
                x += (rng.random() - 0.5) * wobble * 0.5
            out.append((int(round(x)), int(round(y))))
    # connect: walk one cell at a time in BOTH axes so the chain is
    # 4-connected — a band stamped around it can never fragment
    filled = [out[0]]
    for (x, y) in out[1:]:
        px, py = filled[-1]
        while (px, py) != (x, y):
            if px != x:
                px += 1 if x > px else -1
                filled.append((px, py))
            if py != y:
                py += 1 if y > py else -1
                filled.append((px, py))
        filled.append((x, y))
    return filled
