"""Generation passes: brief -> grid, in fixed order.

Each pass consumes its slice of the brief. Stamps carry the CURRENT taste
(round-2 state): buildings get lamps + flowers, NO cobble doorsteps, NO
auto yard-fences — the rulebook, not this file, is where taste lives.
"""

from .core import rrect, fix_water, sweep_isolated_water, widen_walkables
from .sampling import poisson_disc, NoiseField, jittered_polyline

TREE_KINDS = "TtT4t6"


def water_pass(grid, rng, spec):
    for body in spec:
        kind = body["type"]
        if kind == "lake":
            x0, y0, x1, y1 = body["rect"]
            rrect(grid, x0, y0, x1, y1, body.get("round", 6), "~")
            # organic shore: nibble/bulge ONLY the shoreline band — deep water
            # stays water (eroding the interior punched grass islands into the
            # lake; vision review S7)
            noise = NoiseField(rng, grid.w, grid.h, scale=6.0)

            def near_shore(x, y):
                return any(
                    grid.get(x + dx, y + dy, "~") == "."
                    for dy in (-2, -1, 0, 1, 2)
                    for dx in (-2, -1, 0, 1, 2)
                )

            for y in range(max(0, y0 - 2), min(grid.h, y1 + 3)):
                for x in range(max(0, x0 - 2), min(grid.w, x1 + 3)):
                    n = noise.at(x, y)
                    if grid.g[y][x] == "~" and n < 0.22 and near_shore(x, y):
                        grid.g[y][x] = "."
                    elif grid.g[y][x] == "." and n > 0.85:
                        near = any(
                            grid.get(x + dx, y + dy, "") == "~"
                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        )
                        if near:
                            grid.g[y][x] = "~"
    fix_water(grid)
    sweep_isolated_water(grid)


def border_pass(grid, rng, spec):
    """Varied tree frame (gaps, clumps, mixed species) — gen_valley's border,
    driven by the caller's rng instead of a fixed hash."""
    import math

    depth = spec.get("depth", 2.3)
    gap = spec.get("gap", 0.10)
    for x in range(grid.w):
        d = 1 + int(depth * (0.5 + 0.5 * math.sin(x / 6.0 + rng.random() * 0.2)))
        if rng.random() < gap:
            continue
        if rng.random() < 0.12:
            d += 2
        for y in range(d):
            grid.put_grass(x, y, TREE_KINDS[rng.randrange(len(TREE_KINDS))])
        ds = 1 + int(depth * 0.75 * (0.5 + 0.5 * math.sin(x / 5.0 + 1.7)))
        if rng.random() < gap * 1.5:
            continue
        for y in range(grid.h - ds, grid.h):
            grid.put_grass(x, y, TREE_KINDS[rng.randrange(len(TREE_KINDS))])
    for y in range(grid.h):
        for side, w in (("w", 1 + int(1.6 * (0.5 + 0.5 * __import__("math").sin(y / 5.0)))),):
            if rng.random() < 0.12:
                continue
            for x in range(w):
                grid.put_grass(x, y, "T" if rng.random() < 0.5 else "t")
            for x in range(grid.w - w, grid.w):
                grid.put_grass(x, y, "T" if rng.random() < 0.5 else "t")


def path_pass(grid, rng, paths, pois):
    """Jittered desire-line bands between POI anchors, 2-3 wide, then pinch-fixed."""

    def anchor(ref):
        if isinstance(ref, list):
            return tuple(ref)
        return tuple(pois[ref]["at"])

    for p in paths:
        pts = [anchor(p["from"])] + [tuple(v) for v in p.get("via", [])] + [anchor(p["to"])]
        line = jittered_polyline(rng, pts, wobble=p.get("wobble", 2.0))
        r = p.get("width", 3) / 2.0 + 0.4  # circular brush: rounder band edges
        ri = int(r) + 1
        for (x, y) in line:
            for dy in range(-ri, ri + 1):
                for dx in range(-ri, ri + 1):
                    if dx * dx + dy * dy <= r * r:
                        if grid.get(x + dx, y + dy, "") in (".", "f", "w"):
                            grid.put(x + dx, y + dy, "#")
    widen_walkables(grid, "#")
    # fill concave notches (a grass cell walled by 3+ path sides pinches the
    # autotiler) until stable — smooths the jittered band's inner corners
    changed = True
    while changed:
        changed = False
        for y in range(grid.h):
            for x in range(grid.w):
                if grid.g[y][x] != ".":
                    continue
                n = sum(
                    1
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if grid.get(x + dx, y + dy, "") == "#"
                )
                if n >= 3:
                    grid.g[y][x] = "#"
                    changed = True


def poi_pass(grid, rng, pois):
    """Stamp POIs. Round-2 taste: lamps + flowers at buildings, no cobble steps."""
    for pid, p in pois.items():
        x, y = p["at"]
        sym = p["sym"]
        grid.put(x, y, sym)
        if p.get("lamps"):
            grid.put_grass(x - 2, y + 1, "i")
            grid.put_grass(x + 2, y + 1, "i")
        if p.get("flowers", True) and sym in "AGJEYLH":
            grid.put_grass(x - 3, y + 1, "f")
            grid.put_grass(x + 3, y + 1, "w")
        for extra in p.get("props", []):
            ex, ey, es = extra
            grid.put_grass(x + ex, y + ey, es)


def pen_pass(grid, rng, pens):
    """Closed fence rectangles with animals + feed inside (mini-story S5)."""
    for pen in pens:
        x0, y0, x1, y1 = pen["rect"]
        for x in range(x0, x1 + 1):
            grid.put(x, y0, "F")
            grid.put(x, y1, "F")
        for y in range(y0, y1 + 1):
            grid.put(x0, y, "F")
            grid.put(x1, y, "F")
        spots = [
            (x, y) for y in range(y0 + 1, y1) for x in range(x0 + 1, x1) if grid.g[y][x] == "."
        ]
        rng.shuffle(spots)
        for sym in pen.get("contents", ""):
            if spots:
                x, y = spots.pop()
                grid.put(x, y, sym)


def scatter_pass(grid, rng, spec):
    """Poisson-disc + noise-field scatter: organic spacing, spatial density
    variation, species mixing. Replaces hash-grid scatter (rulebook S1/S2)."""
    for layer in spec:
        kinds = layer["kinds"]
        radius = layer.get("radius", 4.0)
        keep = layer.get("keep", 0.6)
        noise = NoiseField(rng, grid.w, grid.h, scale=layer.get("noise_scale", 16.0))
        for (fx, fy) in poisson_disc(rng, grid.w, grid.h, radius):
            x, y = int(fx), int(fy)
            if noise.at(x, y) > keep:
                continue
            grid.put_grass(x, y, kinds[rng.randrange(len(kinds))])
