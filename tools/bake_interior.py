#!/usr/bin/env python3
"""Bake the cottage interior: emit BOTH its collision map (.gd) and its baked
below-player ground image (.png) from one room layout.

Interiors are small levels (docs/level-design.md). They reuse the invisible-
tilemap trick: walls paint the colliding tile source, floor the non-colliding
one (level.gd.terrain_of maps X->WATER/collide, _ and > ->GRASS/free), and this
baked PNG carries ALL the visuals — floor, walls, and furniture composited in.
Furniture is decorative here (baked, no per-item collider) — a prototype.

Kept OUT of tools/preview_map.py on purpose: that renderer + its validate() are
for OUTDOOR maps (shorelines, >=2-wide regions); 1-tile interior walls would
trip H1. Regenerate the interior with this instead.

    python tools/bake_interior.py

Writes scripts/cottage_map.gd + assets/generated/cottage-interior-ground.png.
"""

from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
PACK = REPO / "assets/cute_fantasy/packs/Cute_Fantasy/Cute_Fantasy/Buildings"
INT = PACK / "Houses_Interiors"
DECOR = PACK / "House_Decor"
TILE = 16

# --- room layout (single source of truth for map + bake) ---------------------
# A cozy 13x9 cottage: 1-tile wall border, a doorway gap at the bottom centre,
# the player spawns just inside it. Furniture is placed as a small mini-story.
ROOM_W, ROOM_H = 13, 9
DOOR_COL = 6
SPAWN = (6, 7)  # one tile inside the doorway (arrival from the valley)

# tile regions (px x, y, w, h) on their sheets
FLOOR_TILE = (64, 0, 32, 32)  # Wood_Floor_Tiles: warm parquet, a 2x2 block
WALL_BODY = (176, 64, 16, 16)  # Interior_Walls: stone cobble (contrasts floor)
WALL_TOP = (176, 48, 16, 16)  # Interior_Walls: stone cobble top row

# furniture: (sheet dir, filename, src rect px, dest cell col,row). Drawn in
# order, so a rug listed first sits under the pieces that follow.
FURNITURE = [
    (DECOR, "Carpets.png", (0, 80, 48, 48), (5, 4)),  # teal rug 3x3, centre
    (DECOR, "Fireplaces.png", (32, 0, 32, 48), (2, 1)),  # brick fireplace 2x3, left
    (DECOR, "Beds.png", (0, 0, 32, 32), (9, 1)),  # double bed 2x2, top-right
]


def build_grid() -> list:
    rows = []
    for y in range(ROOM_H):
        row = []
        for x in range(ROOM_W):
            if y == 0 or y == ROOM_H - 1 or x == 0 or x == ROOM_W - 1:
                row.append("X")  # wall (collision)
            else:
                row.append("_")  # floor (free)
        rows.append(row)
    # doorway gap in the bottom wall + the spawn tile just inside it
    rows[ROOM_H - 1][DOOR_COL] = ">"  # exit mat (back to the valley)
    rows[SPAWN[1]][SPAWN[0]] = "S"
    return rows


def sub(path: Path, rect) -> Image.Image:
    x, y, w, h = rect
    return Image.open(path).convert("RGBA").crop((x, y, x + w, y + h))


def render(grid: list) -> Image.Image:
    img = Image.new("RGBA", (ROOM_W * TILE, ROOM_H * TILE), (0, 0, 0, 0))
    floor = sub(INT / "Wood_Floor_Tiles.png", FLOOR_TILE)
    wall_body = sub(INT / "Interior_Walls.png", WALL_BODY)
    wall_top = sub(INT / "Interior_Walls.png", WALL_TOP)
    # floor everywhere first (so doorway + under-wall read as a continuous room)
    for y in range(ROOM_H):
        for x in range(ROOM_W):
            fx, fy = (x * TILE) % floor.width, (y * TILE) % floor.height
            img.paste(floor.crop((fx, fy, fx + TILE, fy + TILE)), (x * TILE, y * TILE))
    # walls on top of the floor
    for y in range(ROOM_H):
        for x in range(ROOM_W):
            if grid[y][x] == "X":
                tile = wall_top if y == 0 else wall_body
                img.paste(tile, (x * TILE, y * TILE), tile)
    # furniture (decorative) between the walls
    for base, name, rect, (cx, cy) in FURNITURE:
        spr = sub(base / name, rect)
        img.alpha_composite(spr, (cx * TILE, cy * TILE))
    # re-stamp the top wall over any furniture that pokes into it, so the room
    # frame always reads clean
    for x in range(ROOM_W):
        if grid[0][x] == "X":
            img.paste(wall_top, (x * TILE, 0), wall_top)
    return img


def write_gd(grid: list) -> None:
    body = "\n".join("".join(r) for r in grid)
    text = (
        "extends RefCounted\n\n"
        "## GENERATED interior map — do not hand-edit; regenerate with\n"
        "## `python tools/bake_interior.py` (emits this + the baked ground PNG).\n"
        "## Symbols: X wall (collision), _ floor, S spawn, > exit mat (back out).\n"
        "## Packed into the Web export as a resource; consumed via LevelRegistry.\n\n"
        'const MAP := """\n' + body + '\n"""\n'
    )
    (REPO / "scripts/cottage_map.gd").write_text(text, encoding="utf-8")


def main() -> None:
    grid = build_grid()
    write_gd(grid)
    out = REPO / "assets/generated/cottage-interior-ground.png"
    render(grid).save(out)
    print("wrote scripts/cottage_map.gd (%dx%d) + %s" % (ROOM_W, ROOM_H, out.name))


if __name__ == "__main__":
    main()
