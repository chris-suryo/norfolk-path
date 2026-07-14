#!/usr/bin/env python3
"""Render scripts/island_map.gd to a full-island preview PNG + validate it.

This is a DEV-ONLY tool (never part of the game build — see tools/.gdignore).
It is the design loop's eyes: it turns the ASCII map into a picture composited
from the real Cute Fantasy tiles, laid out exactly the way the engine renders
them, so a level can be seen and checked before it ever runs in Godot.

Usage (from anywhere):
    python tools/preview_map.py

Outputs:
    docs/island-preview.png   full composite of the current map
    a validation report to stdout (0 problems = the map obeys the design rules)

No third-party deps — pure stdlib PNG decode/encode.

KEEP IN SYNC: the terrain classification and EDGE_BY_LAND_MASK table below
mirror scripts/level.gd. If you change autotiling there, change it here too.
"""
import os
import re
import struct
import sys
import zlib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_GD = os.path.join(REPO, "scripts", "island_map.gd")
PACK = os.path.join(REPO, "assets", "cute_fantasy", "Cute_Fantasy_Free")
OUT = os.path.join(REPO, "docs", "island-preview.png")

TILE = 16

# --- mirror of scripts/level.gd -----------------------------------------------
EDGE_BY_LAND_MASK = {  # land-neighbor bitmask N=1 S=2 E=4 W=8 -> atlas cell
    1: (1, 0), 2: (1, 2), 4: (2, 1), 8: (0, 1),
    5: (2, 0), 9: (0, 0), 6: (2, 2), 10: (0, 2),
}
CENTER = (1, 1)


def terrain_of(ch):
    if ch in "~B":
        return "water"
    if ch in "#S":
        return "path"
    if ch == "D":
        return "farm"
    return "grass"


# --- PNG stdlib codec ---------------------------------------------------------
def decode_png(path):
    d = open(path, "rb").read()
    pos, w, h, idat = 8, 0, 0, b""
    while pos < len(d):
        ln, tag = struct.unpack(">I4s", d[pos : pos + 8])
        data = d[pos + 8 : pos + 8 + ln]
        if tag == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", data[:10])
            if not (bd == 8 and ct == 6):
                raise ValueError(f"{path}: need 8-bit RGBA (bd={bd} ct={ct})")
        elif tag == b"IDAT":
            idat += data
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 4
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p : p + stride])
        p += stride
        for x in range(stride):
            a = line[x - 4] if x >= 4 else 0
            b = prev[x]
            c = prev[x - 4] if x >= 4 else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out[y * stride : (y + 1) * stride] = line
        prev = line
    return w, h, out


def encode_png(w, h, rgba, path):
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        raw += rgba[y * stride : (y + 1) * stride]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    open(path, "wb").write(png)


# --- map loading --------------------------------------------------------------
def load_map(path=MAP_GD):
    """Load an ASCII map from a .gd (const MAP block) or a raw .txt file."""
    src = open(path, encoding="utf-8").read()
    m = re.search(r'const MAP :=\s*"""\n(.*?)"""', src, re.S)
    body = m.group(1) if m else src
    return body.strip("\n").split("\n")


# --- autotiling (mirror of level.gd) -----------------------------------------
def cell(rows, x, y):
    if y < 0 or y >= len(rows) or x < 0 or x >= len(rows[y]):
        return "~"
    return rows[y][x]


def land_mask(rows, x, y, kind):
    """Non-`kind`-neighbor bitmask (N=1 S=2 E=4 W=8) for a terrain cell."""

    def is_same(dx, dy):
        return terrain_of(cell(rows, x + dx, y + dy)) == kind

    mask = 0
    if not is_same(0, -1):
        mask |= 1
    if not is_same(0, 1):
        mask |= 2
    if not is_same(1, 0):
        mask |= 4
    if not is_same(-1, 0):
        mask |= 8
    return mask


def edge_pick(rows, x, y, kind, has_inner=True):
    """Atlas cell for a terrain cell. `has_inner`=False for 3-row sheets
    (farmland/sand) that only have the 3x3 blob, no inner-corner/variant rows."""

    def is_same(dx, dy):
        return terrain_of(cell(rows, x + dx, y + dy)) == kind

    mask = land_mask(rows, x, y, kind)
    if mask == 0:
        if has_inner:
            for dx, dy, res in ((1, 1, (0, 3)), (-1, 1, (1, 3)), (1, -1, (0, 4)), (-1, -1, (1, 4))):
                if not is_same(dx, dy):
                    return res
            if (x * 7 + y * 13) % 17 == 0:
                return ((x + y) % 3, 5)
        return CENTER
    return EDGE_BY_LAND_MASK.get(mask, CENTER)


# --- composite ----------------------------------------------------------------
def blit(canvas, cw, ch, src, sx, sy, sw, sh, dx, dy):
    w, _, px = src
    for yy in range(sh):
        ty = dy + yy
        if ty < 0 or ty >= ch:
            continue
        for xx in range(sw):
            tx = dx + xx
            if tx < 0 or tx >= cw:
                continue
            o = ((sy + yy) * w + (sx + xx)) * 4
            a = px[o + 3]
            if a == 0:
                continue
            d = (ty * cw + tx) * 4
            if a == 255:
                canvas[d : d + 4] = px[o : o + 4]
            else:
                for k in range(3):
                    canvas[d + k] = (px[o + k] * a + canvas[d + k] * (255 - a)) // 255
                canvas[d + 3] = 255


def tex(rel):
    return decode_png(os.path.join(PACK, rel))


def render(rows, out_path):
    w, h = len(rows[0]), len(rows)
    cw, ch = w * TILE, h * TILE
    canvas = bytearray(cw * ch * 4)

    grass = tex("Tiles/Grass_Middle.png")
    path_sheet = tex("Tiles/Path_Tile.png")
    water_sheet = tex("Tiles/Water_Tile.png")
    farm_sheet = tex("Tiles/FarmLand_Tile.png")
    oak = tex("Outdoor decoration/Oak_Tree.png")
    oak_s = tex("Outdoor decoration/Oak_Tree_Small.png")
    fences = tex("Outdoor decoration/Fences.png")
    bridge = tex("Outdoor decoration/Bridge_Wood.png")
    house = tex("Outdoor decoration/House_1_Wood_Base_Blue.png")
    chicken = tex("Animals/Chicken/Chicken.png")
    cow = tex("Animals/Cow/Cow.png")
    pig = tex("Animals/Pig/Pig.png")
    sheep = tex("Animals/Sheep/Sheep.png")
    decor = tex("Outdoor decoration/Outdoor_Decor_Free.png")
    chest = tex("Outdoor decoration/Chest.png")
    player = tex("Player/Player.png")
    # Decoration atlas regions (16px grid in Outdoor_Decor_Free.png). Chosen to
    # read clearly on grass at zoom (tiny sprigs were invisible, so dropped).
    decor_region = {
        "r": (0, 48, 16, 16),    # grey rock
        "u": (0, 32, 16, 16),    # tree stump
        "w": (0, 16, 16, 16),    # wildflowers (meadow)
        "f": (32, 176, 16, 16),  # garden flowers (potted, upright)
        "v": (64, 32, 16, 16),   # carrot / veg plant
        "i": (64, 64, 16, 64),   # tall lamp post
        "n": (48, 0, 16, 16),    # wooden sign
        "q": (96, 32, 16, 16),   # wheat / grain
        "m": (32, 112, 16, 16),  # mushroom
    }

    # terrain: grass under everything, then water/path edge tiles.
    for y in range(h):
        for x in range(w):
            blit(canvas, cw, ch, grass, 0, 0, TILE, TILE, x * TILE, y * TILE)
            t = terrain_of(rows[y][x])
            if t == "water":
                cx, cy = edge_pick(rows, x, y, "water")
                blit(canvas, cw, ch, water_sheet, cx * TILE, cy * TILE, TILE, TILE, x * TILE, y * TILE)
            elif t == "path":
                cx, cy = edge_pick(rows, x, y, "path")
                blit(canvas, cw, ch, path_sheet, cx * TILE, cy * TILE, TILE, TILE, x * TILE, y * TILE)
            elif t == "farm":
                cx, cy = edge_pick(rows, x, y, "farm", has_inner=False)
                blit(canvas, cw, ch, farm_sheet, cx * TILE, cy * TILE, TILE, TILE, x * TILE, y * TILE)

    # bridge sits under all props (engine: unsorted GroundProps).
    bcells = [(x, y) for y in range(h) for x in range(w) if rows[y][x] == "B"]
    if bcells:
        bx = (sum(p[0] for p in bcells) / len(bcells) + 0.5) * TILE
        by = (sum(p[1] for p in bcells) / len(bcells) + 0.5) * TILE
        blit(canvas, cw, ch, bridge, 5, 0, 38, 54, int(bx) - 19, int(by) - 27)

    # props/entities, painter-sorted by body-origin Y (mirror of engine y-sort).
    items = []
    for y in range(h):
        for x in range(w):
            items.append((y * TILE + TILE // 2, rows[y][x], x, y))
    for _key, sym, x, y in sorted(items, key=lambda i: i[0]):
        px_, py_ = x * TILE + TILE // 2, y * TILE + TILE // 2
        if sym == "T":
            blit(canvas, cw, ch, oak, 0, 0, 64, 80, px_ - 32, py_ - 70)
        elif sym == "t":
            blit(canvas, cw, ch, oak_s, 32, 0, 32, 48, px_ - 16, py_ - 40)
        elif sym in "HL":
            # H = Evan's shop, L = the library — same house sprite (only
            # building art in the pack); the brief differentiates them by
            # position, not tileset.
            blit(canvas, cw, ch, house, 0, 0, 96, 128, px_ - 48, py_ - 120)
        elif sym == "C":
            blit(canvas, cw, ch, chicken, 0, 0, 32, 32, px_ - 16, py_ - 26)
        elif sym == "S":
            blit(canvas, cw, ch, player, 0, 0, 32, 32, px_ - 16, py_ - 24)
            blit(canvas, cw, ch, player, 0, 0, 32, 32, px_ - 16 + 18, py_ - 24)
        elif sym == "F":
            piece = _fence_piece(rows, x, y)
            blit(canvas, cw, ch, fences, piece[0] * 16, piece[1] * 16, 16, 16, px_ - 8, py_ - 8)
        elif sym in "ope":
            # Farm animals (2x2 sheets, frame 0). o=cow, p=pig, e=sheep.
            sheet = {"o": cow, "p": pig, "e": sheep}[sym]
            blit(canvas, cw, ch, sheet, 0, 0, 32, 32, px_ - 16, py_ - 26)
        elif sym == "x":
            blit(canvas, cw, ch, chest, 0, 0, 16, 16, px_ - 8, py_ - 12)
        elif sym in decor_region:
            rx, ry, rw, rh = decor_region[sym]
            # Anchor each prop's base near the cell (tall lamp hangs upward).
            blit(canvas, cw, ch, decor, rx, ry, rw, rh, px_ - rw // 2, py_ + 8 - rh)

    encode_png(cw, ch, canvas, out_path)
    return cw, ch


def _fence_piece(rows, x, y):
    left = cell(rows, x - 1, y) == "F"
    right = cell(rows, x + 1, y) == "F"
    up = cell(rows, x, y - 1) == "F"
    down = cell(rows, x, y + 1) == "F"
    if left or right:
        return (2, 0) if (left and right) else ((1, 0) if right else (3, 0))
    if up or down:
        return (0, 1) if (up and down) else ((0, 0) if down else (0, 2))
    return (0, 3)


# --- validation ---------------------------------------------------------------
def validate(rows):
    problems = []
    w = len(rows[0])
    for y, row in enumerate(rows):
        if len(row) != w:
            problems.append(f"row {y}: width {len(row)} != {w} (map must be rectangular)")

    # thin channels: a water/path cell with a land cardinal neighbor whose
    # mask isn't in the edge table (strips / 3-sided pinches the art can't tile)
    for y in range(len(rows)):
        for x in range(len(rows[y])):
            t = terrain_of(rows[y][x])
            if t not in ("water", "path", "farm"):
                continue
            mask = land_mask(rows, x, y, t)
            if mask and mask not in EDGE_BY_LAND_MASK:
                problems.append(
                    f"({x},{y}) '{rows[y][x]}' {t}: region too thin / pinched "
                    f"(land-mask {mask} has no edge tile — widen to >= 2)"
                )

    # entity symbols land on the terrain they expect
    def count(sym):
        return sum(r.count(sym) for r in rows)

    # (terrain_of already classes S as path and H/L/C as grass by definition;
    # the singleton counts below are the real guardrail.)
    if count("S") != 1:
        problems.append(f"expected exactly one spawn 'S', found {count('S')}")
    if count("H") != 1:
        problems.append(f"expected exactly one shop 'H', found {count('H')}")
    if count("L") not in (0, 1):
        problems.append(f"expected at most one library 'L', found {count('L')}")
    return problems


def main():
    import argparse

    ap = argparse.ArgumentParser(description="Render + validate an island map.")
    ap.add_argument(
        "--map", default=MAP_GD, help="map source (.gd with a const MAP block, or a raw .txt); default: island_map.gd"
    )
    ap.add_argument("--out", default=OUT, help="output PNG path; default: docs/island-preview.png")
    args = ap.parse_args()

    rows = load_map(args.map)
    problems = validate(rows)
    cw, ch = render(rows, args.out)
    print(f"rendered {cw}x{ch}px -> {os.path.relpath(args.out, REPO)}")
    if problems:
        print(f"\n{len(problems)} validation problem(s):")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("validation: 0 problems (map obeys the design rules)")


if __name__ == "__main__":
    main()
