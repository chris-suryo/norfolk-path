#!/usr/bin/env python3
"""Render an ASCII world map to a preview PNG + validate it.

DEV-ONLY tool (never part of the game build — see tools/.gdignore). It is the
design loop's eyes: it turns the ASCII map into a picture composited from the
real Cute Fantasy tiles, laid out the way the engine renders them, so a level
can be seen and checked before it ever runs in Godot.

Usage:
    python tools/preview_map.py                                  # current island
    python tools/preview_map.py --map foo.txt --out foo.png --scale 3

Sprites come from two roots: the committed FREE pack (terrain, base props) and
the paid FULL pack library (buildings + extra animals) — the tool reads PNGs
directly, so the FULL pack's .gdignore is irrelevant here. No third-party deps.

KEEP IN SYNC: the terrain classification + EDGE_BY_LAND_MASK table mirror
scripts/level.gd. Legend lives in docs/level-design.md.
"""
import os
import re
import struct
import sys
import zlib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_GD = os.path.join(REPO, "scripts", "island_map.gd")
PACK = os.path.join(REPO, "assets", "cute_fantasy", "Cute_Fantasy_Free")
FULL = os.path.join(REPO, "assets", "cute_fantasy", "packs", "Cute_Fantasy", "Cute_Fantasy")
OUT = os.path.join(REPO, "docs", "island-preview.png")

TILE = 16

# --- mirror of scripts/level.gd -----------------------------------------------
EDGE_BY_LAND_MASK = {  # land-neighbor bitmask N=1 S=2 E=4 W=8 -> atlas cell
    1: (1, 0), 2: (1, 2), 4: (2, 1), 8: (0, 1),
    5: (2, 0), 9: (0, 0), 6: (2, 2), 10: (0, 2),
}
CENTER = (1, 1)

# Terrain symbols (everything else is grass, incl. all the building/prop chars).
WATER_SYMS = "~B"
PATH_SYMS = "#S"
FARM_SYMS = "D"


def terrain_of(ch):
    if ch in WATER_SYMS:
        return "water"
    if ch in PATH_SYMS:
        return "path"
    if ch in FARM_SYMS:
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
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    open(path, "wb").write(png)


def upscale(w, h, rgba, factor):
    if factor <= 1:
        return w, h, rgba
    nw, nh = w * factor, h * factor
    out = bytearray(nw * nh * 4)
    for y in range(h):
        for f in range(factor):
            drow = (y * factor + f) * nw * 4
            for x in range(w):
                s = (y * w + x) * 4
                px = rgba[s : s + 4]
                base = drow + x * factor * 4
                for g in range(factor):
                    out[base + g * 4 : base + g * 4 + 4] = px
    return nw, nh, out


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


def tex2(rel):
    return decode_png(os.path.join(FULL, rel))


def blit_building(canvas, cw, ch, src, px_, py_, foot=8):
    """Draw a whole building centered on px_ with its base ~foot px below the
    cell center (so it sits on the ground and Y-sorts by its base)."""
    w, h, _ = src
    blit(canvas, cw, ch, src, 0, 0, w, h, px_ - w // 2, py_ + foot - h)


def render(rows, out_path, scale=1):
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
    chicken = tex("Animals/Chicken/Chicken.png")
    cow = tex("Animals/Cow/Cow.png")
    pig = tex("Animals/Pig/Pig.png")
    sheep = tex("Animals/Sheep/Sheep.png")
    decor = tex("Outdoor decoration/Outdoor_Decor_Free.png")
    chest = tex("Outdoor decoration/Chest.png")
    player = tex("Player/Player.png")

    # FULL-pack buildings + extra fauna (whole sprites unless noted).
    stall = tex2("Buildings/Buildings/Unique_Buildings/Stalls/Market_Stalls.png")
    inn = tex2("Buildings/Buildings/Unique_Buildings/Inn/Inn_Blue.png")
    barn = tex2("Buildings/Buildings/Unique_Buildings/Barn/Barn_Base_Red.png")
    house_a = tex2("Buildings/Buildings/Houses/Wood/House_1_Wood_Base_Blue.png")
    house_g = tex2("Buildings/Buildings/Houses/Wood/House_2_Wood_Base_Red.png")
    house_j = tex2("Buildings/Buildings/Houses/Stone/House_4_Stone_Base_Blue.png")
    coop = tex2("Buildings/Buildings/Unique_Buildings/Coop/Coop_Base_Blue.png")
    silo = tex2("Buildings/Buildings/Unique_Buildings/Silo/Silo.png")
    well = tex2("Outdoor decoration/Well.png")
    bench = tex2("Outdoor decoration/Benches.png")
    duck = tex2("Animals/Duck/Duck_01.png")
    horse = tex2("Animals/Horse/Horse_01.png")
    capy = tex2("Animals/Kapybara/Static/Kapybara_Idle.png")
    villager = tex2("NPCs (Premade)/Farmer_Bob.png")

    # Decoration atlas regions (16px grid in Outdoor_Decor_Free.png).
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
    buildings = {"H": (stall, 8), "L": (inn, 8), "A": (house_a, 8), "G": (house_g, 8),
                 "J": (house_j, 8), "Y": (barn, 8), "W": (well, 6), "P": (coop, 8),
                 "Z": (silo, 6)}

    # terrain: grass under everything, then water/path/farm edge tiles.
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
        elif sym in buildings:
            src, foot = buildings[sym]
            blit_building(canvas, cw, ch, src, px_, py_, foot)
        elif sym == "b":
            blit(canvas, cw, ch, bench, 0, 0, 32, 32, px_ - 16, py_ - 18)
        elif sym == "C":
            blit(canvas, cw, ch, chicken, 0, 0, 32, 32, px_ - 16, py_ - 26)
        elif sym == "d":
            blit(canvas, cw, ch, duck, 0, 0, 32, 32, px_ - 16, py_ - 22)
        elif sym == "k":
            blit(canvas, cw, ch, capy, 0, 0, 32, 32, px_ - 16, py_ - 18)
        elif sym == "h":
            blit(canvas, cw, ch, horse, 0, 0, 32, 32, px_ - 16, py_ - 26)
        elif sym == "N":
            blit(canvas, cw, ch, villager, 0, 0, 64, 64, px_ - 32, py_ - 54)
        elif sym == "S":
            blit(canvas, cw, ch, player, 0, 0, 32, 32, px_ - 16, py_ - 24)
            blit(canvas, cw, ch, player, 0, 0, 32, 32, px_ - 16 + 18, py_ - 24)
        elif sym == "F":
            piece = _fence_piece(rows, x, y)
            blit(canvas, cw, ch, fences, piece[0] * 16, piece[1] * 16, 16, 16, px_ - 8, py_ - 8)
        elif sym in "ope":
            sheet = {"o": cow, "p": pig, "e": sheep}[sym]
            blit(canvas, cw, ch, sheet, 0, 0, 32, 32, px_ - 16, py_ - 26)
        elif sym == "x":
            blit(canvas, cw, ch, chest, 0, 0, 16, 16, px_ - 8, py_ - 12)
        elif sym in decor_region:
            rx, ry, rw, rh = decor_region[sym]
            blit(canvas, cw, ch, decor, rx, ry, rw, rh, px_ - rw // 2, py_ + 8 - rh)

    cw, ch, canvas = upscale(cw, ch, canvas, scale)
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

    def count(sym):
        return sum(r.count(sym) for r in rows)

    if count("S") != 1:
        problems.append(f"expected exactly one spawn 'S', found {count('S')}")
    if count("H") != 1:
        problems.append(f"expected exactly one shop 'H', found {count('H')}")
    if count("L") not in (0, 1):
        problems.append(f"expected at most one library 'L', found {count('L')}")
    return problems


def main():
    import argparse

    ap = argparse.ArgumentParser(description="Render + validate an island/world map.")
    ap.add_argument("--map", default=MAP_GD, help="map source (.gd const MAP block, or a .txt)")
    ap.add_argument("--out", default=OUT, help="output PNG path")
    ap.add_argument("--scale", type=int, default=1, help="integer upscale factor (default 1)")
    args = ap.parse_args()

    rows = load_map(args.map)
    problems = validate(rows)
    cw, ch = render(rows, args.out, args.scale)
    print(f"rendered {cw}x{ch}px -> {os.path.relpath(args.out, REPO)}")
    if problems:
        print(f"\n{len(problems)} validation problem(s):")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("validation: 0 problems (map obeys the design rules)")


if __name__ == "__main__":
    main()
