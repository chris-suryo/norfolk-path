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
import math
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

WATER_SYMS = "~BOkal@"  # boat / capybaras / swimming duck+swan sit ON water (tile kept under)
PATH_SYMS = "#Sg"  # g = grape-bower arch OVER the path (path continues underneath)
FARM_SYMS = "DQ"  # D = mixed veggie field (carrot/beet/turnip rows), Q = wheat field


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


def _vnoise1(x, y, salt, period):
    """One octave of smooth value noise: bilinear (smoothstep) blend of a coarse
    `rng` lattice sampled every `period` tiles."""
    fx, fy = x / period, y / period
    x0, y0 = math.floor(fx), math.floor(fy)
    tx, ty = fx - x0, fy - y0
    sx = tx * tx * (3 - 2 * tx)
    sy = ty * ty * (3 - 2 * ty)
    v00, v10 = rng(x0, y0, salt), rng(x0 + 1, y0, salt)
    v01, v11 = rng(x0, y0 + 1, salt), rng(x0 + 1, y0 + 1, salt)
    a = v00 + (v10 - v00) * sx
    b = v01 + (v11 - v01) * sx
    return a + (b - a) * sy


def vnoise(x, y, salt=0):
    """Two-octave value noise in [0,1). Thresholding it gives irregular, organic
    patches (no grid alignment) — unlike a per-block hash, which checkerboards."""
    return 0.65 * _vnoise1(x, y, salt, 6) + 0.35 * _vnoise1(x, y, salt + 101, 3)


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


def blit_scaled(canvas, cw, ch, src, sx, sy, sw, sh, dx, dy, dw, dh):
    """Nearest-neighbour scaled blit — used to size the bridge sprite to cover the
    whole crossing so no water/gap shows around it (the 'two bridges' fix)."""
    w, _, px = src
    for yy in range(dh):
        ty = dy + yy
        if ty < 0 or ty >= ch:
            continue
        syy = sy + (yy * sh) // dh
        for xx in range(dw):
            tx = dx + xx
            if tx < 0 or tx >= cw:
                continue
            sxx = sx + (xx * sw) // dw
            o = (syy * w + sxx) * 4
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
    water_sheet = tex2("Tiles/Water/Water_Tile_1.png")  # integrated shore edge
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
    inn = tex2("Buildings/Buildings/Unique_Buildings/Inn/Inn_Black.png")  # darker library (Chris's pick)
    barn = tex2("Buildings/Buildings/Unique_Buildings/Barn/Barn_Base_Red.png")
    house_a = tex2("Buildings/Buildings/Houses/Wood/House_1_Wood_Base_Blue.png")
    house_g = tex2("Buildings/Buildings/Houses/Wood/House_2_Wood_Base_Red.png")
    house_j = tex2("Buildings/Buildings/Houses/Stone/House_4_Stone_Base_Blue.png")
    house_e = tex2("Buildings/Buildings/Houses/Limestone/House_3_Limestone_Base_Red.png")
    coop = tex2("Buildings/Buildings/Unique_Buildings/Coop/Coop_Base_Blue.png")
    silo = tex2("Buildings/Buildings/Unique_Buildings/Silo/Silo.png")
    well = tex2("Outdoor decoration/Well.png")
    bench = tex2("Outdoor decoration/Benches.png")
    duck = tex2("Animals/Duck/Duck_01.png")
    horse = tex2("Animals/Horse/Horse_01.png")
    capy = tex2("Animals/Kapybara/Static/Kapybara_Idle.png")
    villager = tex2("NPCs (Premade)/Farmer_Bob.png")

    # --- round-4 additions: distinct shop, crops, waterlife, more animals, boat ---
    shop = tex2("Buildings/Buildings/Unique_Buildings/Fisherman_House/Fisherman_House_Base_Red.png")
    awning = stall                                            # one 48x48 stall = storefront canopy
    scarecrow = tex2("Outdoor decoration/Scarecrows.png")    # 5 x 32x32
    haybale = tex2("Outdoor decoration/Hay_Bales.png")       # 3 x 16x16
    barrels = tex2("Outdoor decoration/barrels.png")         # 96x64 grid
    boat = tex2("Outdoor decoration/Boat.png")               # 48x48
    goose = tex2("Animals/Goose/Goose_01.png")               # 32px frames
    swan = tex2("Animals/Swan/Swan_01.png")
    frog = tex2("Animals/Frog/Frog_01.png")
    butterfly = tex2("Animals/Butterfly/Butterfly.png")      # 16px frames
    mouse = tex2("Animals/Mouse/Mouse_01.png")
    cattail = tex2(wp + "Cattail_1_Anim.png")                # 128x16 -> 16x16 frame 0
    lily = tex2(wp + "Lillypad_Green_1_Anim.png")            # 128x16 -> 16x16 frame 0

    # --- round-5 additions: promo-look variety (trees, river life, camp, farms) ---
    birch_s = tex2("Trees/Small_Birch_Tree.png")             # golden birch, (32,0,32,64)
    birch_b = tex2("Trees/Big_Birch_Tree.png")               # (32,0,32,80)
    spruce_s = tex2("Trees/Small_Spruce_Tree.png")           # (32,0,32,64)
    spruce_b = tex2("Trees/Big_Spruce_tree.png")             # (64,0,64,80) [sic lowercase]
    apple_t = tex2("Crops/Apple_Tree.png")                   # 32x64 fruit trees
    cherry_t = tex2("Crops/Cherry_Tree.png")
    crops_sheet = tex2("Crops/Crops.png")                    # 16x32 blocks; col5 = mature, col0 = crop sign
    bower = tex2("Crops/Grapes_Bower.png")                   # mature grape arch = (96,80,96,80)
    windmill = tex2("Buildings/Buildings/Unique_Buildings/Windmill/Windmill.png")  # 2 aligned 64x112 halves
    tent = tex2("Buildings/Buildings/Tent/Tent_Small.png")   # 48x96
    oa = "Outdoor decoration/Outdoor_Decor_Animations/Other_Animations/"
    campfire = tex2(oa + "Campfire_Anim.png")                # 8 frames of 16x32
    campdecor = tex2("Outdoor decoration/Camp_Decor.png")    # 5 x 16x16 camp props
    berries2 = tex2("Crops/Berries.png")                     # (0,0)/(32,0) full bushes
    beehive = tex2("Animals/Bee/Bee_Hive.png")               # 16x16
    trough = tex2("Outdoor decoration/Water_Troughs.png")    # (16,0,32,32) filled horizontal
    lamp2 = tex2("Outdoor decoration/Lanter_Posts.png")      # [sic] 16x48 cells
    wfence = tex2("Outdoor decoration/White_Fence.png")      # picket pieces, 16px grid
    stone_bridge = tex2("Tiles/Bridge/Bridge_Stone_Horizontal.png")  # deck = (0,0,128,48)
    wd = "Outdoor decoration/Outdoor_Decor_Animations/Water_Decor_Animations/"
    wlog = tex2(wd + "Other_Water_Decor/Log_1_Water_Anim.png")   # 8 frames of 32x16
    wrock = tex2(wd + "Water_Rocks/Rock_3_Water_Anim.png")       # frames of 16x16
    fish = tex2("Tiles/Water/Fish_Animated_Tile.png")            # 16 frames of 16x16
    rooster = tex2("Animals/Chicken/Rooster.png")                # 32x32 frames
    capy2 = tex2("Animals/Kapybara/Static/Albino_Kapybara_Idle.png")  # 32x32 frames

    decor_region = {
        "r": (0, 48, 16, 16), "u": (0, 32, 16, 16), "w": (0, 16, 16, 16),
        "f": (32, 176, 16, 16), "v": (64, 32, 16, 16), "i": (64, 64, 16, 64),
        "n": (48, 0, 16, 16), "q": (96, 32, 16, 16), "m": (32, 112, 16, 16),
    }
    buildings = {"L": (inn, 8), "A": (house_a, 8), "G": (house_g, 8),
                 "J": (house_j, 8), "E": (house_e, 8), "Y": (barn, 8), "W": (well, 6),
                 "P": (coop, 8), "Z": (silo, 6)}
    flower_cells = [(0, 0), (2, 0), (4, 0), (1, 2), (3, 2), (0, 4), (2, 4), (4, 4), (1, 8), (3, 8)]

    def is_water(x, y):
        return terrain_of(cell(rows, x, y)) == "water"

    def near_water(x, y):
        return is_water(x - 1, y) or is_water(x + 1, y) or is_water(x, y - 1) or is_water(x, y + 1)

    # connected water-region sizes: dress only LARGE bodies (the lake), so the
    # narrow brook doesn't get a busy reed/lily fringe.
    region_size = {}
    seen = set()
    for sy in range(h):
        for sx in range(w):
            if is_water(sx, sy) and (sx, sy) not in seen:
                stack, comp = [(sx, sy)], []
                seen.add((sx, sy))
                while stack:
                    ax, ay = stack.pop()
                    comp.append((ax, ay))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        bx, by = ax + dx, ay + dy
                        if 0 <= bx < w and 0 <= by < h and is_water(bx, by) and (bx, by) not in seen:
                            seen.add((bx, by))
                            stack.append((bx, by))
                for c in comp:
                    region_size[c] = len(comp)
    BIG_WATER = 250  # lake ~600 cells; brook ~130 -> only the lake is dressed

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
                # ORGANIC grass-shade patches: threshold value-noise (not a block
                # hash) across 3 shades so patches are irregular blobs, biased to
                # the base shade — never a visible grid/checkerboard.
                n = vnoise(x, y, 5)
                g = grasses[0] if n < 0.54 else (grasses[1] if n < 0.78 else grasses[2])
                blit(canvas, cw, ch, g, 0, 0, TILE, TILE, gx, gy)

    # ---- pass 2: ground/shore detail (procedural overlays; no symbol change) ----
    for y in range(h):
        for x in range(w):
            t = terrain_of(rows[y][x])
            cx_, cy_ = x * TILE + 8, y * TILE + 8
            if t == "water" and region_size.get((x, y), 0) >= BIG_WATER:
                # dress BIG water (lake + river) in CLUMPS: cattails at the banks,
                # lily rafts + sparse fish shadows / water rocks / a floating log in
                # the open water (the promo look). Tiny puddles stay clean.
                if near_water_land(rows, x, y):
                    if vnoise(x, y, 80) < 0.44 and rng(x, y, 11) < 0.55:
                        blit(canvas, cw, ch, cattail, 0, 0, 16, 16, cx_ - 8, cy_ - 12)
                elif vnoise(x, y, 81) > 0.60 and rng(x, y, 15) < 0.4:   # lily-pad rafts
                    blit(canvas, cw, ch, lily, 0, 0, 16, 16, cx_ - 8, cy_ - 8)
                elif rng(x, y, 90) < 0.02:                               # fish shadow
                    blit(canvas, cw, ch, fish, 0, 0, 16, 16, cx_ - 8, cy_ - 8)
                elif rng(x, y, 91) < 0.012:                              # water rock
                    blit(canvas, cw, ch, wrock, 0, 0, 16, 16, cx_ - 8, cy_ - 8)
                elif rng(x, y, 92) < 0.005:                              # floating log
                    blit(canvas, cw, ch, wlog, 0, 0, 32, 16, cx_ - 16, cy_ - 8)
            elif t == "farm":
                # real crop sprites from the FULL Crops.png (16x32 blocks: col5 =
                # mature plant, col0 = that crop's own little sign). Each field gets
                # its sign at the bottom-left corner cell (the promo-5 look).
                def farm_at(ax, ay):
                    return terrain_of(cell(rows, ax, ay)) == "farm"
                if rows[y][x] == "Q":          # wheat field: golden grain rows
                    crop_by = 0
                else:                           # mixed veggie field: carrot/beet/turnip rows
                    crop_by = (64, 576, 192)[y % 3]
                if not farm_at(x - 1, y) and not farm_at(x, y + 1):
                    blit(canvas, cw, ch, crops_sheet, 0, crop_by, 16, 32, cx_ - 8, cy_ - 24)
                elif rng(x, y, 42) < 0.88:
                    sx_ = 80 if rng(x, y, 43) < 0.8 else 64   # mostly mature, some younger
                    blit(canvas, cw, ch, crops_sheet, sx_, crop_by, 16, 32, cx_ - 8, cy_ - 24)
            elif t == "grass":
                # CLUSTERED, sparser detail: ~30% of 4x4 "beds" are lush, rest bare;
                # rocks only in rare clumps, never near the water (per Chris's notes).
                jx = int(rng(x, y, 32) * 6) - 3
                jy = int(rng(x, y, 33) * 6) - 3
                # coarse 5x5 "beds": a minority are lush flowerbeds; between them
                # the grass is mostly bare with the odd subtle tuft, so flowers
                # read as grouped clumps rather than an even per-cell sprinkle.
                dense = rng(x // 5, y // 5, 50) < 0.22
                if rng(x, y, 31) < (0.55 if dense else 0.07):
                    p = rng(x, y, 34)
                    if dense:
                        cut_t, cut_g = 0.30, 0.60   # beds skew floral
                    else:
                        cut_t, cut_g = 0.62, 0.86   # between-bed specks skew grassy
                    if p < cut_t:
                        tu = tufts[int(rng(x, y, 35) * 3) % 3]
                        blit(canvas, cw, ch, tu, 0, 0, 16, 16, cx_ - 8 + jx, cy_ - 8 + jy)
                    elif p < cut_g:
                        fg = fgrass[int(rng(x, y, 36) * len(fgrass)) % len(fgrass)]
                        blit(canvas, cw, ch, fg, 0, 0, 16, 16, cx_ - 8 + jx, cy_ - 8 + jy)
                    else:
                        fc = flower_cells[int(rng(x, y, 37) * len(flower_cells)) % len(flower_cells)]
                        blit(canvas, cw, ch, flowers, fc[0] * 16, fc[1] * 16, 16, 16,
                             cx_ - 8 + jx, cy_ - 8 + jy)
                elif (not near_water(x, y) and rng(x // 3, y // 3, 60) < 0.05
                      and rng(x, y, 61) < 0.6):
                    blit(canvas, cw, ch, ores, 0, (int(rng(x, y, 62) * 4) % 4) * 16, 16, 16,
                         cx_ - 8 + jx, cy_ - 6)

    # bridge under props — one clean span covering the WHOLE crossing (bbox of all
    # B cells + a tile of overhang), scaled from the east-west bridge piece
    # (sheet cols 5-42) so no water/gap shows around it. Fixes the "two bridges".
    bcells = [(x, y) for y in range(h) for x in range(w) if rows[y][x] == "B"]
    if bcells:
        bx0 = min(p[0] for p in bcells) * TILE - 6
        bx1 = (max(p[0] for p in bcells) + 1) * TILE + 6
        by0 = min(p[1] for p in bcells) * TILE - 6
        by1 = (max(p[1] for p in bcells) + 1) * TILE + 6
        # STONE bridge (the pack-promo hero look), composed from the sheet's three
        # bands — parapet rail / stone deck slabs / parapet rail — so only the slab
        # band stretches vertically and the rails keep their real proportions.
        dw, dh = bx1 - bx0, by1 - by0
        blit_scaled(canvas, cw, ch, stone_bridge, 0, 0, 128, 16, bx0, by0, dw, 16)
        blit_scaled(canvas, cw, ch, stone_bridge, 0, 16, 128, 32, bx0, by0 + 16, dw, dh - 32)
        blit_scaled(canvas, cw, ch, stone_bridge, 0, 48, 128, 16, bx0, by0 + dh - 16, dw, 16)

    # ---- pass 3: props/buildings, painter-sorted by base Y ----
    items = [(y, rows[y][x], x) for y in range(h) for x in range(w)]
    for y, sym, x in sorted(items, key=lambda i: i[0]):
        px_, py_ = x * TILE + 8, y * TILE + 8
        if sym == "T":
            blit(canvas, cw, ch, oak, 0, 0, 64, 80, px_ - 32, py_ - 70)
        elif sym == "t":
            blit(canvas, cw, ch, oak_s, 32, 0, 32, 48, px_ - 16, py_ - 40)
        elif sym == "H":                                 # Evan's market stall (blue awning)
            blit(canvas, cw, ch, stall, 96, 0, 48, 48, px_ - 24, py_ + 8 - 48)
        elif sym in buildings:
            src, foot = buildings[sym]
            blit_building(canvas, cw, ch, src, px_, py_, foot)
        elif sym == "b":
            blit(canvas, cw, ch, bench, 0, 0, 32, 32, px_ - 16, py_ - 18)
        elif sym == "C":
            blit(canvas, cw, ch, chicken, 0, 0, 32, 32, px_ - 16, py_ - 26)
        elif sym in "d$":                                # duck (decor) / Ariana ($ = dialogue anchor)
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
        elif sym in "UVRj":                              # goose / swan / frog / mouse
            sheet = {"U": goose, "V": swan, "R": frog, "j": mouse}[sym]
            blit(canvas, cw, ch, sheet, 0, 0, 32, 32, px_ - 16, py_ - 22)
        elif sym in "al":                                # SWIMMING duck / swan (row 8 = on-water pose)
            sheet = duck if sym == "a" else swan
            blit(canvas, cw, ch, sheet, 0, 256, 32, 32, px_ - 16, py_ - 20)
        elif sym == "@":                                 # albino capybara (in the lake)
            blit(canvas, cw, ch, capy2, 0, 0, 32, 32, px_ - 16, py_ - 18)
        elif sym == "4":                                 # small golden birch
            blit(canvas, cw, ch, birch_s, 32, 0, 32, 64, px_ - 16, py_ - 56)
        elif sym == "5":                                 # big golden birch
            blit(canvas, cw, ch, birch_b, 32, 0, 32, 80, px_ - 16, py_ - 70)
        elif sym == "6":                                 # small spruce
            blit(canvas, cw, ch, spruce_s, 32, 0, 32, 64, px_ - 16, py_ - 56)
        elif sym == "7":                                 # big spruce
            blit(canvas, cw, ch, spruce_b, 64, 0, 64, 80, px_ - 32, py_ - 70)
        elif sym == "8":                                 # apple tree
            blit(canvas, cw, ch, apple_t, 0, 0, 32, 64, px_ - 16, py_ - 56)
        elif sym == "9":                                 # cherry tree
            blit(canvas, cw, ch, cherry_t, 0, 0, 32, 64, px_ - 16, py_ - 56)
        elif sym == "g":                                 # grape-bower arch over the path
            blit(canvas, cw, ch, bower, 96, 80, 96, 80, px_ - 48, py_ + 16 - 80)
        elif sym == "z":                                 # windmill (two pre-aligned halves)
            blit(canvas, cw, ch, windmill, 0, 0, 64, 112, px_ - 32, py_ + 8 - 112)
            blit(canvas, cw, ch, windmill, 64, 0, 64, 112, px_ - 32, py_ + 8 - 112)
        elif sym == "s":                                 # small camp tent
            blit(canvas, cw, ch, tent, 0, 0, 48, 96, px_ - 24, py_ + 8 - 96)
        elif sym == "0":                                 # campfire
            blit(canvas, cw, ch, campfire, 0, 0, 16, 32, px_ - 8, py_ + 8 - 32)
        elif sym == "1":                                 # camp prop (log seat / pot / pack)
            blit(canvas, cw, ch, campdecor, (int(rng(x, y, 70) * 5) % 5) * 16, 0, 16, 16,
                 px_ - 8, py_ - 8)
        elif sym == "%":                                 # beehive
            blit(canvas, cw, ch, beehive, 0, 0, 16, 16, px_ - 8, py_ - 10)
        elif sym == "&":                                 # berry bush (red / purple)
            blit(canvas, cw, ch, berries2, 0 if rng(x, y, 71) < 0.6 else 32, 0, 16, 16,
                 px_ - 8, py_ - 8)
        elif sym == "=":                                 # water trough (filled)
            blit(canvas, cw, ch, trough, 16, 0, 32, 32, px_ - 16, py_ + 8 - 32)
        elif sym == "+":                                 # lamp post variant (library avenue)
            blit(canvas, cw, ch, lamp2, 0 if rng(x, y, 72) < 0.5 else 16, 0, 16, 48,
                 px_ - 8, py_ + 8 - 48)
        elif sym == "^":                                 # rooster
            blit(canvas, cw, ch, rooster, 0, 0, 32, 32, px_ - 16, py_ - 26)
        elif sym == "|":                                 # white picket fence (garden run)
            blit(canvas, cw, ch, wfence, 16, 0, 16, 16, px_ - 8, py_ - 8)
        elif sym == "y":                                 # butterfly (flits above grass)
            blit(canvas, cw, ch, butterfly, 0, 0, 16, 16, px_ - 8, py_ - 20)
        elif sym == "O":                                 # boat moored at the shore
            blit(canvas, cw, ch, boat, 0, 0, 48, 48, px_ - 24, py_ - 34)
        elif sym == "M":                                 # market awning / storefront canopy
            blit(canvas, cw, ch, awning, 0, 0, 48, 48, px_ - 24, py_ + 8 - 48)
        elif sym == "K":                                 # scarecrow (wheat field)
            blit(canvas, cw, ch, scarecrow, 0, 0, 32, 32, px_ - 16, py_ + 8 - 32)
        elif sym == "2":                                 # hay bale
            blit(canvas, cw, ch, haybale, 0, 0, 16, 16, px_ - 8, py_ - 8)
        elif sym == "3":                                 # barrel / crate of goods
            blit(canvas, cw, ch, barrels, 0, 0, 16, 16, px_ - 8, py_ - 10)
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
    """Pick the fence cell from the FREE Fences.png 4x4 sheet, INCLUDING the
    corner pieces (cols 1-3 x rows 0/3 form a closed frame) so pens close at
    the corners instead of reading as dashed lines."""
    left = cell(rows, x - 1, y) == "F"
    right = cell(rows, x + 1, y) == "F"
    up = cell(rows, x, y - 1) == "F"
    down = cell(rows, x, y + 1) == "F"
    if down and right and not left and not up:
        return (1, 0)                                   # top-left corner
    if down and left and not right and not up:
        return (3, 0)                                   # top-right corner
    if up and right and not left and not down:
        return (1, 3)                                   # bottom-left corner
    if up and left and not right and not down:
        return (3, 3)                                   # bottom-right corner
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
