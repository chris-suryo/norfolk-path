"""Mechanical audit of island_map.gd: clones, floating props, singleton reuse."""
import re
import sys
from pathlib import Path

# repo root derived from this file's location; override with argv[1] if needed
_REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
SRC = (_REPO / "scripts" / "island_map.gd").read_text(encoding="utf-8")
m = re.search(r'const MAP := """\n(.*?)"""', SRC, re.S)
rows = m.group(1).rstrip("\n").split("\n")
W, H = len(rows[0]), len(rows)
print(f"map {W}x{H}, uniform={all(len(r) == W for r in rows)}")

def cells(sym):
    return [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == sym]

TREES = set("Tt4567")

# 1. cast + singleton props
for sym, label in [("N", "villager"), ("$", "Ariana"), ("x", "chest"), ("H", "stall"),
                   ("W", "well"), ("z", "windmill"), ("s", "tent"), ("L", "library"),
                   ("m", "mushroom-decor"), ("%", "beehive"), ("K", "scarecrow"),
                   ("b", "bench"), ("g", "grape-arch")]:
    pos = cells(sym)
    print(f"{label:15s} x{len(pos):2d}: {pos}")

# 2. beehive adjacency to trees (floating if no tree neighbor incl. diagonals)
print("\nbeehive tree-adjacency:")
for (x, y) in cells("%"):
    nb = [rows[y + dy][x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)
          if (dx or dy) and 0 <= y + dy < H and 0 <= x + dx < W]
    print(f"  ({x},{y}) neighbors={''.join(nb)} tree-adjacent={bool(set(nb) & TREES)}")

# 3. same-symbol tree runs (horizontal >=5)
print("\ntree clone runs (horiz >=6):")
for y, r in enumerate(rows):
    for match in re.finditer(r"(T{6,}|t{6,}|4{6,}|6{6,})", r):
        print(f"  y={y} x={match.start()}-{match.end() - 1} '{match.group()[0]}' x{len(match.group())}")

# 4. mushrooms near camp/enemy spawns (bombschroom at 117,33 per encounter_manager)
print("\nmushroom decor distance to bombschroom spawn (117,33):")
for (x, y) in cells("m"):
    print(f"  ({x},{y}) dist={abs(x - 117) + abs(y - 33)}")

# 5. villager N neighbors (context)
print("\nvillager contexts:")
for (x, y) in cells("N"):
    row = rows[y]
    print(f"  ({x},{y}): ...{row[max(0, x - 8):x + 9]}...")
