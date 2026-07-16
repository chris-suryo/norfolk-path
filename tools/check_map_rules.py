#!/usr/bin/env python3
"""CI rules for island_map.gd — bug classes found by audits, enforced forever.

Every rule here started life as a real finding (docs/map-visual-audit.md,
docs/playtest-findings.md). When a future audit finds a new CLASS of map bug,
add the rule here — that's the testing-loop's self-improvement step
(docs/testing-loop.md).

Rules:
  1. every beehive '%' has a tree in its 8-neighborhood (M3: floating hives)
  2. every small cobble 'c' group (a doorstep, <=4 cells) sits within 2 cells
     of a building anchor (M2: orphan steps)
  3. singleton props stay singleton: chest, well, windmill, tent, library,
     stall, spawn (census: accidental clones)
  4. every fence cell F/| touches another fence cell of its family
     (M4: floating fragments)
  5. decor mushrooms 'm' keep Manhattan distance >= 10 from the bombschroom
     spawn at (117,33) — encounter_manager.gd — so the enemy tell stays
     unambiguous (census finding)
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TREES = set("Tt4567")
BUILDINGS = set("AGJEYLH")
BOMB_SPAWN = (117, 33)


def main() -> None:
    src = (REPO / "scripts" / "island_map.gd").read_text(encoding="utf-8")
    rows = re.search(r'const MAP := """\n(.*?)"""', src, re.S).group(1)
    rows = rows.rstrip("\n").split("\n")
    height, width = len(rows), len(rows[0])
    problems = []

    def nb8(x, y):
        return [
            rows[y + dy][x + dx]
            for dy in (-1, 0, 1)
            for dx in (-1, 0, 1)
            if (dx or dy) and 0 <= y + dy < height and 0 <= x + dx < width
        ]

    def cells(sym):
        return [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == sym]

    # 1. beehives hang from trees
    for (x, y) in cells("%"):
        if not set(nb8(x, y)) & TREES:
            problems.append(f"beehive ({x},{y}) has no adjacent tree")

    # 2. doorsteps anchored to a building
    seen = set()
    for (x, y) in cells("c"):
        if (x, y) in seen:
            continue
        stack, group = [(x, y)], []
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in seen:
                continue
            seen.add((cx, cy))
            group.append((cx, cy))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if 0 <= ny < height and 0 <= nx < width and rows[ny][nx] == "c":
                    if (nx, ny) not in seen:
                        stack.append((nx, ny))
        if len(group) > 4:  # plaza-scale cobble is deliberate ground, not a step
            continue
        near = any(
            rows[ny][nx] in BUILDINGS
            for gx, gy in group
            for ny in range(max(0, gy - 2), min(height, gy + 3))
            for nx in range(max(0, gx - 2), min(width, gx + 3))
        )
        if not near:
            problems.append(f"doorstep group {group} has no building within 2 cells")

    # 3. singletons stay singleton
    for sym, label in [("x", "chest"), ("W", "well"), ("z", "windmill"),
                       ("s", "tent"), ("L", "library"), ("H", "stall"), ("S", "spawn")]:
        n = len(cells(sym))
        if n != 1:
            problems.append(f"{label} '{sym}' expected exactly once, found {n}")

    # 4. no floating fence fragments
    for sym in "F|":
        for (x, y) in cells(sym):
            if sym not in nb8(x, y):
                problems.append(f"fence '{sym}' at ({x},{y}) is a floating fragment")

    # 5. decor mushrooms keep distance from the bombschroom
    for (x, y) in cells("m"):
        d = abs(x - BOMB_SPAWN[0]) + abs(y - BOMB_SPAWN[1])
        if d < 10:
            problems.append(f"decor mushroom ({x},{y}) only {d} cells from bombschroom spawn")

    # 6. every connected path region contacts >= 2 distinct POIs — a road goes
    #    from somewhere TO somewhere (rulebook H10; map audit M1 dead-end class)
    poi_syms = set(BUILDINGS) | set("WHSBc")
    seen_p = set()
    for (x, y) in cells("#"):
        if (x, y) in seen_p:
            continue
        stack, region = [(x, y)], []
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in seen_p:
                continue
            seen_p.add((cx, cy))
            region.append((cx, cy))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if 0 <= ny < height and 0 <= nx < width and rows[ny][nx] == "#":
                    if (nx, ny) not in seen_p:
                        stack.append((nx, ny))
        contacts = set()
        for (px, py) in region:
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-2, -1, 0, 1, 2):
                    nx, ny = px + dx, py + dy
                    if 0 <= ny < height and 0 <= nx < width and rows[ny][nx] in poi_syms:
                        contacts.add((nx, ny, rows[ny][nx]))
        kinds = {c[2] for c in contacts}
        if len(kinds) < 2:
            problems.append(
                f"path region of {len(region)} cells near {region[0]} contacts "
                f"{sorted(kinds) or 'no'} POI kinds — a road must go from somewhere to somewhere"
            )

    # 7. no straight line of >= 5 identical decor symbols (rulebook H11; the
    #    flower-grid-column class from map audit M13)
    decor = "wfm&ru"
    for sym in decor:
        pts = set(cells(sym))
        for (x, y) in pts:
            for dx, dy in ((1, 0), (0, 1)):
                if (x - dx, y - dy) in pts:
                    continue  # not the run's start
                n = 0
                while (x + n * dx, y + n * dy) in pts:
                    n += 1
                if n >= 5:
                    problems.append(
                        f"decor '{sym}' forms a straight run of {n} from ({x},{y}) — grid artifact"
                    )

    print(f"map rules: checked {width}x{height} map")
    if problems:
        print("FAIL:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print(
        "OK: hives treed, steps anchored, singletons unique, fences connected, "
        "mushrooms clear, paths go somewhere, no decor grids."
    )


if __name__ == "__main__":
    main()
