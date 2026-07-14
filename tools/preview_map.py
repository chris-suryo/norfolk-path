#!/usr/bin/env python3
"""Render an ASCII world map to a preview PNG + validate it.

DEV-ONLY tool (never part of the game build — see tools/.gdignore). Composites
the real Cute Fantasy tiles the way the engine paints them, so a level can be
seen and checked before it runs in Godot.

Density model (matches the Stardew references in references/): the ASCII map
defines STRUCTURE (terrain shapes, buildings, trees), and the tool procedurally
LAYERS the lushness — grass-shade variation, a dense scatter of tufts/flowers,
sandy shores with reeds/lily-pads/rocks, cobble aprons — all as render overlays
keyed off terrain (NOT map symbols), so they never affect autotiling/validation.

Usage:
    python tools/preview_map.py --map foo.txt --out foo.png --scale 3
    python tools/preview_map.py --map foo.txt --out crop.png --scale 5 --crop 4,6,44,40

KEEP IN SYNC: terrain classification + EDGE_BY_LAND_MASK mirror scripts/level.gd.
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

EDGE_BY_LAND_MASK = {
    1: (1, 0), 2: (1, 2), 4: (2, 1), 8: (0, 1),
    5: (2, 0), 9: (0, 0), 6: (2, 2), 10: (0, 2),
}
CENTER = (1, 1)

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
    if ch == "c":
        return "cobble"
    return "grass"


def rng(x, y, salt=0):
    """Deterministic per-cell hash in [0,1)."""
    n = (x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)
    n = (n ^ (n >> 13)) & 0xFFFFFFFF
    n = (n * 1274126177) & 0xFFFFFFFF
    return n / 0xFFFFFFFF


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


def crop(w, h, rgba, box):
    x0, y0, x1, y1 = box
    nw, nh = x1 - x0, y1 - y0
    out = bytearray(nw * nh * 4)
    for y in range(nh):
        src = ((y0 + y) * w + x0) * 4
        out[y * nw * 4 : (y + 1) * nw * 4] = rgba[src : src + nw * 4]
    return nw, nh, out


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


def load_map(path=MAP_GD):
    src = open(path, encoding="utf-8").read()
    m = re.search(r'const MAP :=\s*"""\n(.*?)"""', src, re.S)
    body = m.group(1) if m else src
    return body.strip("\n").split("\n")


def cell(rows, x, y):
    if y < 0 or y >= len(rows) or x < 0 or x >= len(rows[y]):
        return "~"
    return rows[y][x]


def land_mask(rows, x, y, kind):
    def same(dx, dy):
        return terrain_of(cell(rows, x + dx, y + dy)) == kind

    mask = 0
    if not same(0, -1):
        mask |= 1
    if not same(0, 1):
        mask |= 2
    if not same(1, 0):
        mask |= 4
    if not same(-1, 0):
        mask |= 8
    return mask


def edge_pick(rows, x, y, kind, has_inner=True):
    def same(dx, dy):
        return terrain_of(cell(rows, x + dx, y + dy)) == kind

    mask = land_mask(rows, x, y, kind)
    if mask == 0:
        if has_inner:
            for dx, dy, res in ((1, 1, (0, 3)), (-1, 1, (1, 3)), (1, -1, (0, 4)), (-1, -1, (1, 4))):
                if not same(dx, dy):
                    return res
            if (x * 7 + y * 13) % 17 == 0:
                return ((x + y) % 3, 5)
        return CENTER
    return EDGE_BY_LAND_MASK.get(mask, CENTER)


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
    w, h, _ = src
    blit(canvas, cw, ch, src, 0, 0, w, h, px_ - w // 2, py_ + foot - h)


def render(rows, out_path, scale=1, crop_box=None):
    w, h = len(rows[0]), len(rows)
    cw, ch = w * TILE, h * TILE
    canvas = bytearray(cw * ch * 4)

    # --- terrain + autotile sheets (FREE pack, proven autotiler) ---
    path_sheet = tex("Tiles/Path_Tile.png")
    water_sheet = tex("Tiles/Water_Tile.png")
    farm_sheet = tex("Tiles/FarmLand_Tile.png")
    # --- ground texture + detail (FULL pack) ---
    grasses = [tex2("Tiles/Grass/Grass_%d_Middle.png" % i) for i in (1, 2, 3, 4)]
    sand = tex2("Tiles/Beach/Beach_Tiles.png")            # cell (3,0) = solid sand
    cobble_t = tex2("Tiles/Cobble_Road/Cobble_Road_1.png")  # cell (1,1) = cobble
    ga = "Outdoor decoration/Outdoor_Decor_Animations/Grass_Animations/"
    tufts = [tex2(ga + "Grass_%d_Anim.png" % i) for i in (1, 2, 3)]
    fgrass = [tex2(ga + "Flower_Grass_%d_Anim.png" % i) for i in (1, 3, 5, 7, 9, 11, 13, 15)]
    flowers = tex2("Outdoor decoration/Flowers.png")     # 10x10 @16; cols 0-4 = no pot
    ores = tex2("Outdoor decoration/Ores.png")           # col 0 = grey rocks
    wp = "Outdoor decoration/Outdoor_Decor_Animations/Water_Decor_Animations/Water_Plants/"
    reeds = [tex2(wp + "Water_Grass_%d_Anim.png" % i) for i in (1, 2)]
    waterdec = tex2("Tiles/Water/Water_Decoration.png")  # 3x1 lily pads

    # --- props (existing) ---
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

    decor_region = {
        "r": (0, 48, 16, 16), "u": (0, 32, 16, 16), "w": (0, 16, 16, 16),
        "f": (32, 176, 16, 16), "v": (64, 32, 16, 16), "i": (64, 64, 16, 64),
        "n": (48, 0, 16, 16), "q": (96, 32, 16, 16), "m": (32, 112, 16, 16),
    }
    buildings = {"H": (stall, 8), "L": (inn, 8), "A": (house_a, 8), "G": (house_g, 8),
                 "J": (house_j, 8), "Y": (barn, 8), "W": (well, 6), "P": (coop, 8),
                 "Z": (silo, 6)}
    flower_cells = [(0, 0), (2, 0), (4, 0), (1, 2), (3, 2), (0, 4), (2, 4), (4, 4), (1, 8), (3, 8)]

    def is_water(x, y):
        return terrain_of(cell(rows, x, y)) == "water"

    def near_water(x, y):
        return is_water(x - 1, y) or is_water(x + 1, y) or is_water(x, y - 1) or is_water(x, y + 1)

    # ---- pass 1: base terrain (grass shade / path / water / farm / cobble / sand) ----
    for y in range(h):
        for x in range(w):
            t = terrain_of(rows[y][x])
            gx, gy = x * TILE, y * TILE
            if t == "water":
                cx, cy = edge_pick(rows, x, y, "water")
                blit(canvas, cw, ch, water_sheet, cx * TILE, cy * TILE, TILE, TILE, gx, gy)
            elif t == "path":
                cx, cy = edge_pick(rows, x, y, "path")
                blit(canvas, cw, ch, path_sheet, cx * TILE, cy * TILE, TILE, TILE, gx, gy)
            elif t == "farm":
                cx, cy = edge_pick(rows, x, y, "farm", has_inner=False)
                blit(canvas, cw, ch, farm_sheet, cx * TILE, cy * TILE, TILE, TILE, gx, gy)
            elif t == "cobble":
                blit(canvas, cw, ch, cobble_t, 16, 16, TILE, TILE, gx, gy)
            else:
                # soft grass-shade PATCHES (3x3, biased to one base shade) rather
                # than per-cell random, so it reads textured not checkerboarded.
                p = rng(x // 3, y // 3, 5)
                g = grasses[0 if p < 0.74 else 1]  # subtle 2-shade patches
                blit(canvas, cw, ch, g, 0, 0, TILE, TILE, gx, gy)
                if near_water(x, y):  # sandy shore ring on the land side
                    blit(canvas, cw, ch, sand, 48, 0, TILE, TILE, gx, gy)

    # ---- pass 2: ground/shore detail (procedural overlays; no symbol change) ----
    for y in range(h):
        for x in range(w):
            t = terrain_of(rows[y][x])
            cx_, cy_ = x * TILE + 8, y * TILE + 8
            if t == "water":
                if near_water_land(rows, x, y) and rng(x, y, 11) < 0.5:
                    if rng(x, y, 12) < 0.5:
                        blit(canvas, cw, ch, waterdec, (int(rng(x, y, 13) * 3) % 3) * 16, 0,
                             16, 16, cx_ - 8, cy_ - 8)
                    else:
                        rd = reeds[int(rng(x, y, 14) * 2) % 2]
                        blit(canvas, cw, ch, rd, 0, 0, 16, 16, cx_ - 8, cy_ - 10)
            elif t == "farm":  # crop rows on the tilled plots (so they aren't bare)
                if rng(x, y, 41) < 0.72:
                    reg = (64, 32) if (x + y) % 2 == 0 else (96, 32)
                    blit(canvas, cw, ch, decor, reg[0], reg[1], 16, 16, cx_ - 8, cy_ - 9)
            elif t == "grass":
                if near_water(x, y):  # sand shore: occasional rocks / reeds
                    if rng(x, y, 21) < 0.2:
                        blit(canvas, cw, ch, ores, 0, (int(rng(x, y, 22) * 4) % 4) * 16,
                             16, 16, cx_ - 8, cy_ - 10)
                    continue
                r = rng(x, y, 31)
                jx = int(rng(x, y, 32) * 6) - 3
                jy = int(rng(x, y, 33) * 6) - 3
                if r < 0.34:
                    tu = tufts[int(rng(x, y, 34) * 3) % 3]
                    blit(canvas, cw, ch, tu, 0, 0, 16, 16, cx_ - 8 + jx, cy_ - 8 + jy)
                elif r < 0.52:
                    fg = fgrass[int(rng(x, y, 35) * len(fgrass)) % len(fgrass)]
                    blit(canvas, cw, ch, fg, 0, 0, 16, 16, cx_ - 8 + jx, cy_ - 8 + jy)
                elif r < 0.66:
                    fc = flower_cells[int(rng(x, y, 36) * len(flower_cells)) % len(flower_cells)]
                    blit(canvas, cw, ch, flowers, fc[0] * 16, fc[1] * 16, 16, 16,
                         cx_ - 8 + jx, cy_ - 8 + jy)
                elif r < 0.69:
                    blit(canvas, cw, ch, ores, 0, (int(rng(x, y, 37) * 4) % 4) * 16, 16, 16,
                         cx_ - 8 + jx, cy_ - 6)

    # bridge under props
    bcells = [(x, y) for y in range(h) for x in range(w) if rows[y][x] == "B"]
    if bcells:
        bx = (sum(p[0] for p in bcells) / len(bcells) + 0.5) * TILE
        by = (sum(p[1] for p in bcells) / len(bcells) + 0.5) * TILE
        blit(canvas, cw, ch, bridge, 5, 0, 38, 54, int(bx) - 19, int(by) - 27)

    # ---- pass 3: props/buildings, painter-sorted by base Y ----
    items = [(y, rows[y][x], x) for y in range(h) for x in range(w)]
    for y, sym, x in sorted(items, key=lambda i: i[0]):
        px_, py_ = x * TILE + 8, y * TILE + 8
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

    if crop_box:
        x0, y0, x1, y1 = crop_box
        cw, ch, canvas = crop(cw, ch, canvas, (x0 * TILE, y0 * TILE, x1 * TILE, y1 * TILE))
    cw, ch, canvas = upscale(cw, ch, canvas, scale)
    encode_png(cw, ch, canvas, out_path)
    return cw, ch


def near_water_land(rows, x, y):
    """A water cell that touches land (grass/path/cobble) — the shoreline."""
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        t = terrain_of(cell(rows, x + dx, y + dy))
        if t in ("grass", "path", "cobble"):
            return True
    return False


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
    ap.add_argument("--map", default=MAP_GD)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--crop", default=None, help="x0,y0,x1,y1 in tiles (render a close-up)")
    args = ap.parse_args()

    rows = load_map(args.map)
    problems = validate(rows)
    box = tuple(int(v) for v in args.crop.split(",")) if args.crop else None
    cw, ch = render(rows, args.out, args.scale, box)
    print(f"rendered {cw}x{ch}px -> {os.path.relpath(args.out, REPO)}")
    if problems:
        print(f"\n{len(problems)} validation problem(s):")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("validation: 0 problems (map obeys the design rules)")


if __name__ == "__main__":
    main()
