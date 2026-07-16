#!/usr/bin/env python3
"""Bake every interior level: per-room collision map (.gd) + ground image (.png)
from one spec dict.

Interiors are small levels (docs/level-design.md). They reuse the invisible-
tilemap trick: walls paint the colliding tile source, floor the non-colliding
one (level.gd.terrain_of maps X->WATER/collide, _ and > ->GRASS/free), and the
baked PNG carries ALL the visuals — floor, walls, windows, furniture. Furniture
is decorative (baked, no per-item collider).

Each INTERIORS entry is an archetype: room size, wall/floor style, furniture
mini-story. Wall styles use the SEAMLESS mid-section tiles of Interior_Walls
(the framed section-edge tiles caused the vertical seam "slits" Chris flagged).
Furniture rects are ENCLOSING boxes — grab() trims to the sprite's opaque bbox,
so a rect only needs to contain its sprite without touching a neighbour.

Kept OUT of tools/preview_map.py on purpose: that renderer + its validate() are
for OUTDOOR maps (shorelines, >=2-wide regions); 1-tile interior walls would
trip H1. Regenerate all interiors with:

    python tools/bake_interior.py

Writes scripts/<id>_map.gd + assets/generated/<id>-ground.png per room.
"""

from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
PACK = REPO / "assets/cute_fantasy/packs/Cute_Fantasy/Cute_Fantasy/Buildings"
INT = PACK / "Houses_Interiors"
DECOR = PACK / "House_Decor"
TILE = 16

# --- wall styles: (top-row tile, body tile) on Interior_Walls.png -------------
# Seamless mid-section columns (verified by tiling strips): plaster c1, wood c3,
# stone c4, brick c5. Row 3 (y48) = top trim, row 4 (y64) = body.
WALLS = {
    "plaster": ((16, 48, 16, 16), (16, 64, 16, 16)),
    "wood": ((48, 48, 16, 16), (48, 64, 16, 16)),
    "stone": ((64, 48, 16, 16), (64, 64, 16, 16)),
    "brick": ((80, 48, 16, 16), (80, 64, 16, 16)),
}

# --- floor styles: a 2x2-tile block on Wood_Floor_Tiles.png -------------------
FLOORS = {
    "parquet": (64, 0, 32, 32),
    "wood_dark": (0, 0, 32, 32),
    "wood_mix": (32, 0, 32, 32),
    "diag": (96, 0, 32, 32),
    "stone_blue": (0, 64, 32, 32),
    "tile_blue": (64, 64, 32, 32),
}

# --- furniture library: name -> (sheet file, enclosing rect px) ---------------
SPRITES = {
    "fireplace": ("Fireplaces.png", (32, 0, 32, 48)),
    "bed": ("Beds.png", (0, 0, 32, 32)),
    "rug_teal": ("Carpets.png", (0, 80, 48, 48)),
    "rug_green": ("Carpets.png", (0, 160, 48, 48)),
    "bookshelf_big": ("BookShelves.png", (17, 1, 30, 28)),
    "bookshelf_small": ("BookShelves.png", (1, 1, 14, 28)),
    "table_dark": ("Tables.png", (8, 88, 48, 32)),
    # dark chair set (matches table_dark): named by the way the chair FACES.
    "chair_right": ("Chairs.png", (129, 8, 12, 21)),
    "chair_up": ("Chairs.png", (146, 8, 12, 21)),
    "chair_down": ("Chairs.png", (162, 11, 12, 18)),
    "chair_left": ("Chairs.png", (179, 8, 12, 21)),
    "lamp_cream": ("Standing_Lamps.png", (0, 0, 16, 32)),
    "lamp_teal": ("Standing_Lamps.png", (32, 0, 16, 32)),
    "lamp_gold": ("Standing_Lamps.png", (128, 0, 16, 32)),
    "plant_leafy": ("House_Plants.png", (16, 0, 16, 32)),
    "plant_sunflower": ("House_Plants.png", (64, 0, 16, 32)),
    "plant_blue": ("House_Plants.png", (112, 0, 16, 32)),
    "plant_big": ("House_Plants.png", (128, 0, 32, 64)),
    "clock_wall": ("Clocks.png", (32, 0, 16, 16)),
    "clock_grand": ("Clocks.png", (0, 0, 16, 32)),
    "window_warm": ("windows.png", (0, 0, 16, 32)),
    "window_wide": ("windows.png", (48, 0, 32, 32)),
    "stove": ("Kitchen_Furniture.png", (0, 0, 16, 32)),
    "sink": ("Kitchen_Furniture.png", (0, 32, 16, 32)),
    "fridge": ("Kitchen_Furniture.png", (0, 64, 16, 32)),
    "pans": ("Kitchen_Furniture.png", (64, 72, 32, 20)),
    "barrel": ("Indoor_Decor.png", (48, 128, 16, 32)),
    "barrel_water": ("Indoor_Decor.png", (16, 128, 16, 32)),
    "barrel_berry": ("Indoor_Decor.png", (0, 128, 16, 32)),
    "crate": ("Indoor_Decor.png", (64, 0, 16, 16)),
}

# --- the rooms ----------------------------------------------------------------
# furniture: (sprite name, col, row) — bottom-center of the trimmed sprite lands
# on the bottom-center of that cell. windows: list of top-wall columns.
INTERIORS = {
    # G @ (21,17) — the original cozy hearth room (id kept for save-v4 compat).
    "cottage": {
        "size": (13, 9),
        "wall": "stone",
        "floor": "parquet",
        "windows": [3, 9],
        "furniture": [
            ("rug_teal", 5, 6),
            ("fireplace", 2, 2),
            ("bed", 9, 2),
            ("plant_leafy", 11, 2),
            ("lamp_cream", 1, 2),
            ("clock_wall", 6, 1),
        ],
    },
    # A @ (10,19) — kitchen/dining home. (Stone walls: the seamless wood wall
    # tile camouflages against wooden floors — the room frame vanished.)
    "home_a1": {
        "size": (11, 8),
        "wall": "stone",
        "floor": "wood_mix",
        "windows": [4, 7],
        "furniture": [
            ("stove", 1, 2),
            ("sink", 2, 2),
            ("pans", 3, 1),
            ("fridge", 9, 2),
            ("clock_wall", 6, 1),
            ("rug_green", 4, 5),
            ("table_dark", 4, 4),
            ("chair_right", 2, 4),
            ("chair_left", 6, 4),
        ],
    },
    # A @ (27,34) — the plant-lover's home.
    "home_a2": {
        "size": (11, 8),
        "wall": "plaster",
        "floor": "diag",
        "windows": [2, 5, 8],
        "furniture": [
            ("plant_big", 1, 3),
            ("plant_sunflower", 3, 2),
            ("plant_blue", 9, 2),
            ("plant_leafy", 9, 5),
            ("rug_teal", 4, 5),
            ("bed", 6, 2),
            ("lamp_teal", 8, 2),
        ],
    },
    # G @ (38,36) — the study.
    "home_g2": {
        "size": (13, 9),
        "wall": "plaster",
        "floor": "parquet",
        "windows": [6],
        "furniture": [
            ("bookshelf_big", 2, 2),
            ("bookshelf_small", 4, 2),
            ("bookshelf_big", 9, 2),
            ("clock_grand", 11, 2),
            ("rug_green", 6, 6),
            ("table_dark", 6, 5),
            ("chair_up", 6, 6),
            ("lamp_gold", 1, 5),
        ],
    },
    # J @ (14,35) — the small bedroom (J is the smallest house).
    "home_j1": {
        "size": (9, 7),
        "wall": "plaster",
        "floor": "wood_dark",
        "windows": [4],
        "furniture": [
            ("bed", 2, 2),
            ("rug_teal", 3, 4),
            ("plant_leafy", 6, 2),
            ("lamp_cream", 7, 4),
        ],
    },
    # E @ (33,20) — the big family room.
    "home_e1": {
        "size": (13, 9),
        "wall": "brick",
        "floor": "parquet",
        "windows": [3, 9],
        "furniture": [
            ("fireplace", 6, 2),
            ("bed", 2, 2),
            ("clock_wall", 10, 1),
            ("plant_sunflower", 11, 2),
            ("rug_green", 6, 6),
            ("table_dark", 6, 5),
            ("chair_right", 4, 5),
            ("chair_left", 9, 5),
        ],
    },
    # Y @ (43,17) — barn storage. (Brick walls read barn-red; wood-wall tiles
    # camouflage against the plank floor.)
    "barn_int": {
        "size": (14, 10),
        "wall": "brick",
        "floor": "wood_dark",
        "windows": [4, 9],
        "furniture": [
            ("barrel", 1, 2),
            ("barrel", 2, 2),
            ("barrel_water", 1, 3),
            ("barrel_berry", 12, 2),
            ("crate", 11, 2),
            ("crate", 12, 3),
            ("crate", 6, 4),
            ("crate", 7, 4),
            ("barrel", 6, 5),
            ("crate", 2, 7),
            ("barrel", 12, 7),
        ],
    },
}

_sheet_cache = {}


def sheet(base: Path, name: str) -> Image.Image:
    key = str(base / name)
    if key not in _sheet_cache:
        _sheet_cache[key] = Image.open(base / name).convert("RGBA")
    return _sheet_cache[key]


def grab(name: str) -> Image.Image:
    """The named sprite, cropped by its enclosing rect then trimmed to content."""
    fname, (x, y, w, h) = SPRITES[name]
    img = sheet(DECOR, fname).crop((x, y, x + w, y + h))
    bbox = img.getbbox()
    if bbox is None:
        raise SystemExit("bake_interior: sprite '%s' rect is empty" % name)
    return img.crop(bbox)


def build_grid(w: int, h: int) -> list:
    door = w // 2
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            row.append("X" if y == 0 or y == h - 1 or x == 0 or x == w - 1 else "_")
        rows.append(row)
    rows[h - 1][door] = ">"  # exit mat back outside
    rows[h - 2][door] = "S"  # arrival tile just inside the doorway
    return rows


def render(spec: dict, grid: list) -> Image.Image:
    w, h = spec["size"]
    img = Image.new("RGBA", (w * TILE, h * TILE), (0, 0, 0, 0))
    top_rect, body_rect = WALLS[spec["wall"]]
    wall_top = sheet(INT, "Interior_Walls.png").crop(
        (top_rect[0], top_rect[1], top_rect[0] + 16, top_rect[1] + 16)
    )
    wall_body = sheet(INT, "Interior_Walls.png").crop(
        (body_rect[0], body_rect[1], body_rect[0] + 16, body_rect[1] + 16)
    )
    fx, fy, fw, fh = FLOORS[spec["floor"]]
    floor = sheet(INT, "Wood_Floor_Tiles.png").crop((fx, fy, fx + fw, fy + fh))
    # floor everywhere (doorway + under-wall read as a continuous room) ...
    for y in range(h):
        for x in range(w):
            px, py = (x * TILE) % floor.width, (y * TILE) % floor.height
            img.paste(floor.crop((px, py, px + TILE, py + TILE)), (x * TILE, y * TILE))
    # ... walls on top ...
    for y in range(h):
        for x in range(w):
            if grid[y][x] == "X":
                tile = wall_top if y == 0 else wall_body
                img.paste(tile, (x * TILE, y * TILE), tile)
    # ... windows set into the top wall ...
    for col in spec.get("windows", []):
        win = grab("window_warm")
        img.alpha_composite(win, (col * TILE, TILE - win.height // 2))
    # ... furniture, bottom-center anchored on its cell.
    for name, cx, cy in spec["furniture"]:
        spr = grab(name)
        px = cx * TILE + (TILE - spr.width) // 2
        py = (cy + 1) * TILE - spr.height
        img.alpha_composite(spr, (px, py))
    return img


def write_gd(interior_id: str, grid: list) -> None:
    body = "\n".join("".join(r) for r in grid)
    text = (
        "extends RefCounted\n\n"
        "## GENERATED interior map — do not hand-edit; regenerate with\n"
        "## `python tools/bake_interior.py` (emits this + the baked ground PNG).\n"
        "## Symbols: X wall (collision), _ floor, S spawn, > exit mat (back out).\n"
        "## Packed into the Web export as a resource; consumed via LevelRegistry.\n\n"
        'const MAP := """\n' + body + '\n"""\n'
    )
    (REPO / ("scripts/%s_map.gd" % interior_id)).write_text(text, encoding="utf-8")


def main() -> None:
    for interior_id, spec in INTERIORS.items():
        w, h = spec["size"]
        grid = build_grid(w, h)
        write_gd(interior_id, grid)
        out = REPO / ("assets/generated/%s-ground.png" % interior_id)
        render(spec, grid).save(out)
        print("wrote scripts/%s_map.gd (%dx%d) + %s" % (interior_id, w, h, out.name))


if __name__ == "__main__":
    main()
