#!/usr/bin/env python3
"""Bake every interior level: per-room collision map (.gd) + ground image (.png)
from one spec dict.

Interiors are small levels (docs/level-design.md) on the invisible-tilemap
trick: `X` cells paint the colliding tile source, floor `_`/`>` the free one,
and the baked PNG carries ALL visuals. v2 (round-3 findings):

- The top wall is TWO rows tall — a real hanging band, so windows, clocks and
  pan racks sit ON the wall instead of at floor level.
- SOLID furniture is cell-aligned (bottom-left cell + a cells-wide/tall
  footprint) and its footprint is emitted as `X` cells — walking into a bed or
  table now collides, exactly like outdoors. Rugs and wall-mounted decor stay
  non-solid.
- Overlap VALIDATION, fail-loud: solid footprints may not overlap each other,
  the spawn, the exit mat, or the door column; an underlay (rug) listed after
  a solid item it pixel-overlaps is an ordering error (that was the rug-over-
  the-bed bug). Rug-first-then-table-on-top remains legal and correct.

Kept OUT of tools/preview_map.py on purpose (its outdoor validators would trip
on 1-tile walls). Regenerate all interiors with:

    python tools/bake_interior.py

Writes scripts/<id>_map.gd + assets/generated/<id>-ground.png per room.
"""

import math
import sys
from pathlib import Path

from PIL import Image

import interior_furnish

REPO = Path(__file__).resolve().parents[1]
PACK = REPO / "assets/cute_fantasy/packs/Cute_Fantasy/Cute_Fantasy/Buildings"
INT = PACK / "Houses_Interiors"
DECOR = PACK / "House_Decor"
TILE = 16
WALL_TOP_ROWS = 2  # the hanging band

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

# --- furniture library: name -> (sheet file, enclosing rect px, kind) ---------
# kind: "solid" (cell-aligned, collides), "underlay" (rug — draw first, walk
# over), "wall" (hangs in the wall band, no collision).
SPRITES = {
    "fireplace": ("Fireplaces.png", (32, 0, 32, 48), "solid"),
    "bed": ("Beds.png", (0, 0, 32, 32), "solid"),
    "rug_teal": ("Carpets.png", (0, 80, 48, 48), "underlay"),
    "rug_green": ("Carpets.png", (0, 160, 48, 48), "underlay"),
    "bookshelf_big": ("BookShelves.png", (17, 1, 30, 28), "solid"),
    "bookshelf_small": ("BookShelves.png", (1, 1, 14, 28), "solid"),
    "table_dark": ("Tables.png", (8, 88, 48, 32), "solid"),
    # dark chair set (matches table_dark): named by the way the chair FACES.
    "chair_right": ("Chairs.png", (129, 8, 12, 21), "solid"),
    "chair_up": ("Chairs.png", (146, 8, 12, 21), "solid"),
    "chair_down": ("Chairs.png", (162, 11, 12, 18), "solid"),
    "chair_left": ("Chairs.png", (179, 8, 12, 21), "solid"),
    "lamp_cream": ("Standing_Lamps.png", (0, 0, 16, 32), "solid"),
    "lamp_teal": ("Standing_Lamps.png", (32, 0, 16, 32), "solid"),
    "lamp_gold": ("Standing_Lamps.png", (128, 0, 16, 32), "solid"),
    "plant_leafy": ("House_Plants.png", (16, 0, 16, 32), "solid"),
    "plant_sunflower": ("House_Plants.png", (64, 0, 16, 32), "solid"),
    "plant_blue": ("House_Plants.png", (112, 0, 16, 32), "solid"),
    "plant_big": ("House_Plants.png", (128, 0, 32, 64), "solid"),
    "clock_wall": ("Clocks.png", (32, 0, 16, 16), "wall"),
    "clock_grand": ("Clocks.png", (0, 0, 16, 32), "solid"),
    "window_warm": ("windows.png", (0, 0, 16, 32), "wall"),
    "stove": ("Kitchen_Furniture.png", (0, 0, 16, 32), "solid"),
    "sink": ("Kitchen_Furniture.png", (0, 32, 16, 32), "solid"),
    "fridge": ("Kitchen_Furniture.png", (0, 64, 16, 32), "solid"),
    "pans": ("Kitchen_Furniture.png", (64, 72, 32, 20), "wall"),
    "barrel": ("Indoor_Decor.png", (48, 128, 16, 32), "solid"),
    "barrel_water": ("Indoor_Decor.png", (16, 128, 16, 32), "solid"),
    "barrel_berry": ("Indoor_Decor.png", (0, 128, 16, 32), "solid"),
    "crate": ("Indoor_Decor.png", (64, 0, 16, 16), "solid"),
}

# --- the rooms ----------------------------------------------------------------
# furniture: (name, col, row) — for "solid"/"underlay": the BOTTOM-LEFT cell of
# a cell-aligned footprint (footprint = ceil(w/16) x ceil(h/16) cells ending on
# that row). For "wall": drawn hanging in the wall band at that column (row is
# the band row the piece's bottom sits on). windows: top-wall band columns.
# Floor area: rows WALL_TOP_ROWS .. h-2 (row h-1 is the bottom wall + doorway).
INTERIORS = {
    # G @ (21,17) — the original cozy hearth room (id kept for save-v4 compat).
    "cottage": {
        "size": (13, 10),
        "wall": "stone",
        "floor": "parquet",
        "windows": [3, 9],
        "notes": [(2, 4)],  # by the hearth
        "furniture": [
            ("rug_teal", 5, 6),
            ("fireplace", 2, 3),
            ("bed", 9, 3),
            ("plant_leafy", 11, 3),
            ("lamp_cream", 1, 4),
            ("clock_wall", 6, 1),
        ],
    },
    # A @ (10,19) — kitchen/dining home.
    "home_a1": {
        "size": (11, 9),
        "wall": "stone",
        "floor": "wood_mix",
        "windows": [4, 7],
        "notes": [(1, 4)],  # at the stove
        "furniture": [
            ("stove", 1, 3),
            ("sink", 2, 3),
            ("pans", 3, 1),
            ("fridge", 9, 3),
            ("clock_wall", 6, 1),
            ("rug_green", 4, 6),
            ("table_dark", 4, 5),
            ("chair_right", 3, 5),
            ("chair_left", 7, 5),
        ],
    },
    # A @ (27,34) — the plant-lover's home.
    "home_a2": {
        "size": (11, 9),
        "wall": "plaster",
        "floor": "diag",
        "windows": [2, 5, 8],
        "notes": [(3, 5)],  # among the plants
        "furniture": [
            ("plant_big", 1, 4),
            ("plant_sunflower", 3, 3),
            ("bed", 6, 3),
            ("plant_blue", 9, 3),
            ("rug_teal", 4, 6),
            ("plant_leafy", 9, 6),
            ("lamp_teal", 1, 6),
        ],
    },
    # G @ (38,36) — the fireside parlor. Deliberately shelf-free: the big
    # bookshelf + grand-clock kit lives ONLY in the library now, so entering this
    # house no longer pre-spoils the library reveal (R4-14).
    "home_g2": {
        "size": (13, 10),
        "wall": "plaster",
        "floor": "tile_blue",
        "windows": [3, 9],
        # PROCEDURAL (see home_j1): furnisher-generated; list below is the fallback.
        "furnish": {"type": "parlor"},
        "notes": [(3, 6)],  # fireside
        "furniture": [
            ("rug_teal", 5, 7),
            ("fireplace", 2, 3),
            ("plant_leafy", 11, 3),
            ("table_dark", 5, 6),
            ("chair_right", 4, 6),
            ("chair_left", 8, 6),
            ("plant_blue", 11, 7),
            ("lamp_gold", 1, 6),
            ("clock_wall", 6, 1),
        ],
    },
    # J @ (14,35) — a small spare bedroom. Wood walls + a storage crate give it
    # its own character so it reads as a different household than the cottage's
    # hearth bedroom (R4-14). Rug clear of the bed (round-3 fix).
    "home_j1": {
        "size": (9, 8),
        "wall": "wood",
        "floor": "wood_mix",
        "windows": [4],
        # PROCEDURAL: the furnisher generates this room (seed = id); the
        # hand-authored list below is the kept fallback — delete "furnish" to revert.
        "furnish": {"type": "bedroom"},
        "notes": [(3, 4)],  # bedside
        "furniture": [
            ("bed", 1, 3),
            ("crate", 7, 3),
            ("plant_sunflower", 6, 3),
            ("rug_teal", 3, 6),
            ("lamp_teal", 7, 5),
        ],
    },
    # E @ (33,20) — the family living/dining room. No bed (it's a common room,
    # not a fourth bedroom) so the three bed-centric houses stop reading as one
    # room at three sizes (R4-14).
    "home_e1": {
        "size": (13, 10),
        "wall": "brick",
        "floor": "parquet",
        "windows": [3, 9],
        "notes": [(7, 4)],  # by the family hearth
        "furniture": [
            ("fireplace", 6, 3),
            ("plant_big", 1, 4),
            ("clock_wall", 10, 1),
            ("plant_sunflower", 11, 3),
            ("lamp_cream", 11, 6),
            ("rug_green", 5, 7),
            ("table_dark", 5, 6),
            ("chair_right", 4, 6),
            ("chair_left", 8, 6),
        ],
    },
    # Y @ (43,17) — barn storage.
    # L @ (162,17) — Irene's library: the grandest room in the valley. Shelf
    # bank across the top wall around a grand clock, twin reading desks with a
    # centre aisle between them, rug at the heart. The boss fight stays
    # OUTSIDE; this room is pure story space.
    "library": {
        "size": (17, 12),
        "wall": "stone",
        "floor": "wood_dark",
        "windows": [4, 12],
        # PROCEDURAL (see home_j1): furnisher-generated; list below is the fallback.
        "furnish": {"type": "library"},
        "notes": [(4, 4), (11, 4)],  # in front of the shelf banks
        "furniture": [
            ("rug_teal", 7, 9),
            ("bookshelf_big", 1, 3),
            ("bookshelf_big", 3, 3),
            ("bookshelf_big", 5, 3),
            ("clock_grand", 8, 3),
            ("bookshelf_big", 10, 3),
            ("bookshelf_big", 12, 3),
            ("bookshelf_small", 14, 3),
            ("lamp_gold", 1, 6),
            ("chair_right", 2, 6),
            ("table_dark", 3, 6),
            ("chair_left", 6, 6),
            ("chair_right", 9, 6),
            ("table_dark", 10, 6),
            ("chair_left", 13, 6),
            ("plant_leafy", 14, 8),
            ("plant_blue", 1, 8),
        ],
    },
    "barn_int": {
        "size": (14, 11),
        "wall": "brick",
        "floor": "wood_dark",
        "windows": [4, 9],
        "notes": [(3, 4)],  # by the stores
        "furniture": [
            ("barrel", 1, 3),
            ("barrel", 2, 3),
            ("barrel_water", 1, 5),
            ("barrel_berry", 12, 3),
            ("crate", 11, 2),
            ("crate", 12, 4),
            ("crate", 6, 5),
            ("crate", 7, 5),
            ("barrel", 6, 7),
            ("crate", 2, 8),
            ("barrel", 12, 8),
        ],
    },
    # z @ (56,39) — the windmill's ground floor: a working mill storeroom. Grain
    # and flour barrels line both walls, a work table sits center, hand-authored
    # (no mill ROOM_TEMPLATE / no sack sprite exists) in the barn_int style.
    "windmill": {
        "size": (11, 9),
        "wall": "wood",
        "floor": "wood_mix",
        "windows": [3, 7],
        "notes": [(3, 6)],  # the miller's worktable
        "furniture": [
            ("barrel", 1, 3),
            ("barrel_water", 1, 5),
            ("barrel_berry", 1, 7),
            ("crate", 2, 6),
            ("barrel", 9, 3),
            ("barrel_water", 9, 5),
            ("barrel_berry", 9, 7),
            ("crate", 8, 6),
            ("table_dark", 4, 5),
            ("lamp_gold", 8, 3),
            ("plant_leafy", 2, 3),
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
    fname, (x, y, w, h), _kind = SPRITES[name]
    img = sheet(DECOR, fname).crop((x, y, x + w, y + h))
    bbox = img.getbbox()
    if bbox is None:
        raise SystemExit(f"bake_interior: sprite '{name}' rect is empty")
    return img.crop(bbox)


def footprint(name: str) -> tuple:
    spr = grab(name)
    return math.ceil(spr.width / TILE), math.ceil(spr.height / TILE)


def build_grid(w: int, h: int) -> list:
    door = w // 2
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            wall = y < WALL_TOP_ROWS or y == h - 1 or x == 0 or x == w - 1
            row.append("X" if wall else "_")
        rows.append(row)
    rows[h - 1][door] = ">"  # exit mat back outside
    rows[h - 2][door] = "S"  # arrival tile just inside the doorway
    return rows


def validate_and_stamp(interior_id: str, spec: dict, grid: list) -> None:
    """Overlap rules + emit solid footprints as X collision cells."""
    w, h = spec["size"]
    door = w // 2
    reserved = {(door, h - 1), (door, h - 2)}  # mat + spawn
    solid_cells = {}
    solid_boxes = []  # (name, pixel box) for underlay-ordering checks
    problems = []
    for name, col, row in spec["furniture"]:
        _f, _r, kind = SPRITES[name]
        spr = grab(name)
        fw, fh = footprint(name)
        px = col * TILE + (fw * TILE - spr.width) // 2
        py = (row + 1) * TILE - spr.height
        box = (px, py, px + spr.width, py + spr.height)
        if kind == "wall":
            continue
        if kind == "underlay":
            for prior, pbox in solid_boxes:
                if box[0] < pbox[2] and pbox[0] < box[2] and box[1] < pbox[3] and pbox[1] < box[3]:
                    problems.append(
                        f"{interior_id}: underlay '{name}' at ({col},{row}) is listed AFTER "
                        f"solid '{prior}' it overlaps — it would draw on top (rug-over-bed bug)"
                    )
            continue
        cells = {(c, r) for c in range(col, col + fw) for r in range(row - fh + 1, row + 1)}
        for cell in cells:
            cx, cy = cell
            if not (0 <= cx < w and 0 <= cy < h):
                problems.append(f"{interior_id}: '{name}' footprint cell {cell} out of bounds")
            elif cell in reserved:
                problems.append(f"{interior_id}: '{name}' blocks the door pocket at {cell}")
            elif cell in solid_cells:
                problems.append(
                    f"{interior_id}: '{name}' footprint overlaps '{solid_cells[cell]}' at {cell}"
                )
        for cell in cells:
            solid_cells[cell] = name
        solid_boxes.append((name, box))
    # Interactable "note" cells: a walkable floor tile the game turns into an
    # examine-trigger (main.gd spawns an Interactable there, wired to a dialogue
    # id derived from the level + cell). Stamped AFTER furniture so the floor
    # check sees the final grid: a note must land on clear floor ("_"), never on
    # furniture, a wall, or the door pocket — placed a step in front of the piece
    # it comments on. Fail loud, like every other overlap rule.
    for (col, row) in spec.get("notes", []):
        if not (0 <= col < w and 0 <= row < h):
            problems.append(f"{interior_id}: note cell ({col},{row}) out of bounds")
        elif (col, row) in reserved:
            problems.append(f"{interior_id}: note ({col},{row}) blocks the door pocket")
        elif (col, row) in solid_cells:
            problems.append(
                f"{interior_id}: note ({col},{row}) sits on furniture "
                f"'{solid_cells[(col, row)]}' — place it on adjacent floor"
            )
        elif grid[row][col] == "X":
            problems.append(f"{interior_id}: note ({col},{row}) is a wall cell, not floor")
    if problems:
        raise SystemExit("bake_interior FAIL:\n  - " + "\n  - ".join(problems))
    for (cx, cy) in solid_cells:
        if 0 <= cx < w and 0 <= cy < h and grid[cy][cx] == "_":
            grid[cy][cx] = "X"
    for (col, row) in spec.get("notes", []):
        grid[row][col] = "!"


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
    # ... walls: trim on row 0, body below (the 2-row band + borders). The exit
    # mat cell ('>') stays FLOOR — painting the whole border by geometry walled
    # over the doorway and made every exit invisible (round-3.5 regression; the
    # transition still worked, players just saw solid wall).
    for y in range(h):
        for x in range(w):
            border = y < WALL_TOP_ROWS or y == h - 1 or x == 0 or x == w - 1
            if border and grid[y][x] != ">":
                tile = wall_top if y == 0 else wall_body
                img.paste(tile, (x * TILE, y * TILE), tile)
    # ... windows set into the wall band ...
    for col in spec.get("windows", []):
        win = grab("window_warm")
        img.alpha_composite(win, (col * TILE, WALL_TOP_ROWS * TILE - win.height))
    # ... furniture in spec order (underlays first by convention, validated).
    for name, col, row in spec["furniture"]:
        spr = grab(name)
        _f, _r, kind = SPRITES[name]
        fw2, fh2 = footprint(name)
        if kind == "wall":
            px = col * TILE + (TILE - spr.width) // 2 if spr.width <= TILE else col * TILE
            py = (row + 1) * TILE - spr.height + 8  # hang low in the band
        else:
            px = col * TILE + (fw2 * TILE - spr.width) // 2
            py = (row + 1) * TILE - spr.height
        img.alpha_composite(spr, (px, py))
    return img


def write_gd(interior_id: str, grid: list) -> None:
    body = "\n".join("".join(r) for r in grid)
    text = (
        "extends RefCounted\n\n"
        "## GENERATED interior map — do not hand-edit; regenerate with\n"
        "## `python tools/bake_interior.py` (emits this + the baked ground PNG).\n"
        "## Symbols: X wall/solid furniture (collision), _ floor, S spawn,\n"
        "## > exit mat (back out), ! examine-trigger (walkable; main.gd spawns\n"
        "## an Interactable here — dialogue id note_<level>_<x>_<y>).\n"
        "## Packed into the Web export as a resource; consumed via LevelRegistry.\n\n"
        'const MAP := """\n' + body + '\n"""\n'
    )
    (REPO / f"scripts/{interior_id}_map.gd").write_text(text, encoding="utf-8")


def catalog() -> dict:
    """name -> (fw, fh, kind) for every sprite — the abstract catalog the
    procedural furnisher places against (it never touches the art itself)."""
    return {name: (*footprint(name), SPRITES[name][2]) for name in SPRITES}


def resolve_furniture(interior_id: str, spec: dict, cat: dict) -> dict:
    """A room may opt into procedural furnishing via a ``furnish`` block
    (``{"type": ..., "seed": ...}``); then its furniture list is GENERATED
    (deterministic per id), else the hand-authored ``furniture`` is used. Either
    way the result flows through the same validate/render pipeline + backstop."""
    if "furnish" not in spec:
        return spec
    fspec = spec["furnish"]
    resolved = dict(spec)
    resolved["furniture"] = interior_furnish.furnish(
        fspec["type"], spec["size"], spec.get("windows", []), fspec.get("seed", interior_id), cat
    )
    return resolved


def main() -> None:
    # `--only <id>` bakes a single room (fast iteration); default bakes all.
    only = sys.argv[2] if len(sys.argv) >= 3 and sys.argv[1] == "--only" else None
    cat = catalog()
    for interior_id, raw in INTERIORS.items():
        if only is not None and interior_id != only:
            continue
        spec = resolve_furniture(interior_id, raw, cat)
        w, h = spec["size"]
        grid = build_grid(w, h)
        validate_and_stamp(interior_id, spec, grid)
        write_gd(interior_id, grid)
        out = REPO / f"assets/generated/{interior_id}-ground.png"
        render(spec, grid).save(out)
        print(f"wrote scripts/{interior_id}_map.gd ({w}x{h}) + {out.name}")


if __name__ == "__main__":
    main()
