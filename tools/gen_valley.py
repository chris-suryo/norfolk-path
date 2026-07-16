"""Generate the Norfolk Path valley maps (round 5: real river, longer wilder walk).

Structure only — the preview tool layers ground texture / shore / detail. Round 5:
the map grows to 192 wide (a longer first-level walk), the stream becomes a real
6-wide RIVER running edge-to-edge top-to-bottom under a stone bridge, the village
gets a well plaza / windmill / orchard / picket garden / second (horse) pen, the
woods double in depth with mixed oak+birch+spruce groves and a dressed camp
clearing (the future skeleton arena), and the library climax shifts palette via
golden birch + fruit trees. A post-build self-check asserts every building's
cobble spur actually reaches the road (fail loud, not in the eyeball pass).
Guarantees rectangular + >=2-wide path/water/farm; validate to 0 problems.
"""
import math
import sys

W, H = 192, 48
PY = 24        # golden-path base row
RIVER_CX = 76  # river centre column (held straight at the bridge)


def blank():
    return [["." for _ in range(W)] for _ in range(H)]


def rect(g, x0, y0, x1, y1, ch):
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            g[y][x] = ch


def put(g, x, y, ch):
    if 0 <= y < H and 0 <= x < W:
        g[y][x] = ch


def putg(g, x, y, ch):  # place only on open grass; returns True on success
    if 0 <= y < H and 0 <= x < W and g[y][x] == ".":
        g[y][x] = ch
        return True
    return False


def putw(g, x, y, ch):  # place only on open water (swimmers, the boat)
    if 0 <= y < H and 0 <= x < W and g[y][x] == "~":
        g[y][x] = ch
        return True
    return False


def scatter(g, cells, ch, only_grass=True):
    for x, y in cells:
        if 0 <= y < H and 0 <= x < W and (not only_grass or g[y][x] == "."):
            g[y][x] = ch


def hh(a, b=0):
    """Deterministic 1-D-ish hash in [0,1) for border/flock jitter."""
    n = (a * 374761393 + b * 668265263) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n & 0xFFFFFF) / 0xFFFFFF


def rrect(g, x0, y0, x1, y1, r, ch, only="."):
    """Rounded-rectangle fill — long flat sides + rounded corners, so shores
    read smooth (few 45-degree stair runs) rather than a stair-stepped ellipse."""
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            dx = max(0, (x0 + r) - x, x - (x1 - r))
            dy = max(0, (y0 + r) - y, y - (y1 - r))
            if dx * dx + dy * dy <= r * r and (only is None or g[y][x] == only):
                g[y][x] = ch


EDGE_MASKS = {1, 2, 4, 8, 5, 9, 6, 10}


def path_y(x):
    """Gently undulating golden path (slope < 1 tile/col so the 4-thick band
    never pinches the autotiler). Near the river the meander RAMPS into a flat
    hold so the band meets the stone bridge as a clean rectangle — a hard
    hold would jump 2 rows at the window edge and pinch. East of the woods the
    meander blends back to the base row: the final approach to the library is
    a straight, lamp-lined avenue (and stays clear of the lake rows)."""
    dx = x - RIVER_CX
    if abs(dx) < 8:
        t = max(0.0, (abs(dx) - 2) / 6.0)   # 0 at the bridge .. 1 at |dx|=8
        xc = RIVER_CX + dx * t
    else:
        xc = x
    yv = 3.5 * math.sin((xc - 4) / 19.0) + 1.5 * math.sin((xc - 4) / 8.0)
    ta = min(1.0, max(0.0, (x - 144) / 12.0))   # avenue blend 144..156
    return PY + int(round(yv * (1.0 - ta)))


def river_cx(y):
    """Centre column of the river; held straight where the path crosses."""
    if 18 <= y <= 30:
        return RIVER_CX
    return RIVER_CX + int(round(2.2 * math.sin(y / 7.0)))


def _is_water(g, x, y):
    if y < 0 or y >= H or x < 0 or x >= W:
        return True  # border reads as water (matches the tool's OOB rule)
    return g[y][x] in "~B"


def fix_water(g):
    """Erode thin water fingers (bad autotile masks) into grass -> clean blobs."""
    changed = True
    while changed:
        changed = False
        for y in range(H):
            for x in range(W):
                if g[y][x] != "~":
                    continue
                m = 0
                if not _is_water(g, x, y - 1):
                    m |= 1
                if not _is_water(g, x, y + 1):
                    m |= 2
                if not _is_water(g, x + 1, y):
                    m |= 4
                if not _is_water(g, x - 1, y):
                    m |= 8
                if m and m not in EDGE_MASKS:
                    g[y][x] = "."
                    changed = True


def sweep_isolated_water(g, min_size=20):
    """Remove stray disconnected water tiles (the NW-lake-corner bug class):
    flood-fill every ~/B region; any region smaller than the real lake/river
    (< min_size cells) is a stray -> convert back to grass."""
    seen = set()
    for sy in range(H):
        for sx in range(W):
            if g[sy][sx] in "~B" and (sx, sy) not in seen:
                stack, comp = [(sx, sy)], []
                seen.add((sx, sy))
                while stack:
                    x, y = stack.pop()
                    comp.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < W and 0 <= ny < H and g[ny][nx] in "~B" \
                                and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
                if len(comp) < min_size:
                    for x, y in comp:
                        g[y][x] = "."


def draw_path(g, x0, x1, thick=4):
    for x in range(x0, x1 + 1):
        y = path_y(x)
        for t in range(thick):
            put(g, x, y + t, "#")


def grove(g, cx, cy, n, spread=4, salt=0, kinds="Tt"):
    """A cluster of trees around (cx, cy); kinds mixes species (T/t oak,
    4/5 birch, 6/7 spruce) so groves read as a natural mixed wood."""
    for i in range(n):
        r = (i * 7 + salt * 13) % 97 / 97.0
        r2 = (i * 11 + salt * 5) % 89 / 89.0
        r3 = (i * 13 + salt * 7) % 83 / 83.0
        gx = cx + int((r - 0.5) * 2 * spread)
        gy = cy + int((r2 - 0.5) * 2 * spread)
        putg(g, gx, gy, kinds[int(r3 * len(kinds)) % len(kinds)])


def flock(g, cx, cy, kinds, n, spread=3, salt=0):
    """Scatter n animals of the given kinds into a LOOSE cluster (not a row)."""
    placed = 0
    for i in range(n * 4):
        if placed >= n:
            break
        jx = int((hh(i, salt) - 0.5) * 2 * spread)
        jy = int((hh(i, salt + 7) - 0.5) * 2 * spread)
        k = kinds[int(hh(i, salt + 3) * len(kinds)) % len(kinds)]
        if putg(g, cx + jx, cy + jy, k):
            placed += 1


DOORS = []  # (bx, by, step) of every placed building — for the doorstep check


def building(g, bx, by, sym, fence=True, lamps=True):
    """Place a building with a short doorstep, lamps, a fenced yard and flowers.

    A full cobble ribbon from every door to the road looked procedural and cut
    through the village lawn. Players can walk on grass, so the doorstep is a
    visual cue rather than a forced route.
    """
    put(g, bx, by, sym)
    ty = path_y(bx)
    step = 1 if ty > by else -1                 # direction from building to path
    DOORS.append((bx, by, step))
    for distance in range(1, 3):                # a deliberate, two-tile doorstep
        y = by + step * distance
        for dx in (0, 1):
            if g[y][bx + dx] in ".fF":
                g[y][bx + dx] = "c"
    if lamps:
        put(g, bx - 2, by + step, "i")
        put(g, bx + 2, by + step, "i")
    if fence:                                   # yard fence on the side away from path
        fy = by - 2 * step
        for x in range(bx - 3, bx + 4):
            if g[by - step][x] != "c":
                put(g, x, fy, "F")
        put(g, bx - 3, by - step, "F")
        put(g, bx + 3, by - step, "F")
    scatter(g, [(bx - 2, by + step), (bx + 2, by + step)], "f")


def check_connected(g):
    """Fail loud if a generated building loses its immediate cobble doorstep."""
    bad = []
    for bx, by, step in DOORS:
        if not any(g[by + step][bx + dx] == "c" for dx in (0, 1)):
            bad.append((bx, by))
    if bad:
        raise SystemExit(f"Buildings missing a cobble doorstep: {bad}")


def pen(g, x0, y0, x1, y1):
    """A closed fence rectangle (corner pieces close it in the renderer)."""
    for x in range(x0, x1 + 1):
        put(g, x, y0, "F")
        put(g, x, y1, "F")
    for y in range(y0, y1 + 1):
        put(g, x0, y, "F")
        put(g, x1, y, "F")


def tree_border(g):
    """A VARIED tree frame: uneven band depth with gaps and clumps, mixed
    species, plus a scrubby buffer just inside. South band runs THINNER with
    more gaps than round 4 (Chris: still a little dense near the bottom)."""
    def band(x, phase, salt, amp=2.3, gap=0.10, clump=2):
        d = 1 + int(amp * (0.5 + 0.5 * math.sin(x / 6.0 + phase)))
        if hh(x, salt + 20) < gap:
            return 0                                                # a gap
        if hh(x, salt + 30) < 0.12:
            return d + clump                                        # a dense clump
        return d

    border_kinds = "TtT4t6"
    for x in range(W):
        dn = band(x, 0.0, 0)
        for y in range(dn):
            putg(g, x, y, border_kinds[int(hh(x * 7 + y, 3) * 6) % 6])
        if hh(x, 4) < 0.20:                                         # scrub buffer
            putg(g, x, dn + int(hh(x, 5) * 2), "t")
        ds = band(x, 1.7, 40, amp=1.7, gap=0.15, clump=1)           # thinner south band
        for y in range(H - ds, H):
            putg(g, x, y, border_kinds[int(hh(x * 5 + y, 8) * 6) % 6])
        if hh(x, 9) < 0.16:
            putg(g, x, H - ds - 1 - int(hh(x, 10) * 2), "t")
    for y in range(H):                                             # west edge
        dw = 1 + int(1.6 * (0.5 + 0.5 * math.sin(y / 5.0)))
        if hh(y, 11) < 0.12:
            dw = 0
        for x in range(dw):
            putg(g, x, y, "T" if hh(x + y * 3, 12) < 0.5 else "t")


def make_water(g, variant):
    # library lake in the SE — rounded rectangle, pulled up off the map bottom so
    # its whole shore lands on visible grass
    x0 = 148 if variant == 3 else 152
    rrect(g, x0, 30, W - 1, 41, 6, "~")
    # the RIVER: 6 wide, gently bending, edge-to-edge top-to-bottom (a real river,
    # not a canal segment); held straight where the stone bridge crosses
    for y in range(H):
        cx = river_cx(y)
        for x in range(cx - 2, cx + 4):
            if g[y][x] == "#":
                g[y][x] = "B"
            elif g[y][x] == ".":
                g[y][x] = "~"


def build(variant):
    DOORS.clear()
    g = blank()
    draw_path(g, 3, 174)
    make_water(g, variant)
    fix_water(g)
    sweep_isolated_water(g)        # kill stray disconnected water tiles
    tree_border(g)

    # ===== REGION 1: VILLAGE (cols 6-52) =====
    building(g, 10, 19, "A")
    building(g, 21, 17, "G")
    building(g, 33, 20, "E")                  # limestone house
    building(g, 43, 17, "Y", fence=False)     # barn
    building(g, 14, 35, "J")
    building(g, 27, 34, "A", fence=False)
    building(g, 38, 36, "G", fence=False)
    # well PLAZA: a small cobble square off the path — the village centre
    pyw = path_y(18)
    rect(g, 15, pyw - 3, 20, pyw - 1, "c")
    put(g, 16, pyw - 4, "W")
    put(g, 19, pyw - 4, "b")
    put(g, 14, pyw - 2, "i")
    scatter(g, [(21, pyw - 2), (14, pyw - 4)], "f")
    # picket-fenced flower garden in front of the limestone house
    for x in list(range(30, 33)) + list(range(35, 38)):
        putg(g, x, 24, "|")
    scatter(g, [(31, 25), (36, 25), (30, 26), (37, 26)], "f")
    # small kitchen-garden farmstead near spawn (balances the dense SW corner)
    rect(g, 4, 7, 9, 10, "D")                  # carrot patch
    put(g, 5, 6, "K")                          # scarecrow
    scatter(g, [(10, 8), (10, 10)], "2")       # hay bales
    flock(g, 8, 13, ["C", "C", "^"], 3, spread=2, salt=61)   # chickens + rooster
    scatter(g, [(11, 7)], "%")                 # beehive
    scatter(g, [(11, 8), (6, 12)], "y")        # bees
    # orchard corner east of the barn
    scatter(g, [(48, 19), (50, 22), (47, 23)], "8")
    scatter(g, [(52, 20), (49, 26)], "9")
    # two DISTINCT farms: mixed veggies (west) + wheat (east, windmill + scarecrow)
    rect(g, 6, 38, 12, 42, "D")
    rect(g, 44, 37, 51, 42, "Q")
    put(g, 55, 35, "z")                        # windmill beside the wheat, clear of crop rows
    put(g, 43, 38, "K")                        # scarecrow
    scatter(g, [(43, 40), (52, 38), (52, 41)], "2")    # hay bales
    scatter(g, [(53, 34)], "%")                         # one purposeful hive by the orchard edge
    scatter(g, [(53, 33), (42, 41), (13, 39)], "y")     # butterflies around flowers and the hive
    # livestock pen + NEW horse paddock, each with a trough, flocks not rows
    pen(g, 16, 37, 25, 43)
    put(g, 17, 39, "=")
    flock(g, 21, 40, ["o", "o", "p", "e", "e"], 6, spread=3, salt=11)
    pen(g, 28, 39, 37, 44)
    put(g, 36, 41, "=")
    put(g, 29, 44, "2")
    flock(g, 32, 42, ["h", "h"], 2, spread=2, salt=15)
    # village life: chickens + a rooster, villagers, butterflies
    flock(g, 12, 23, ["C", "C", "N"], 3, spread=3, salt=12)
    flock(g, 30, 27, ["C", "^", "C"], 3, spread=3, salt=13)
    flock(g, 45, 30, ["C", "N"], 2, spread=3, salt=14)
    scatter(g, [(8, 28), (26, 30), (41, 24)], "y")
    g[path_y(6)][6] = "S"

    # ===== REGION 2: PATH & EVAN'S SHOP (cols 54-72) =====
    put(g, 55, path_y(55) + 2, "g")            # grape-bower gate: leaving the village
    # a little more life by the north-row village houses (between houses + road)
    flock(g, 25, 23, ["C", "C", "o"], 3, spread=2, salt=62)
    flock(g, 16, 22, ["C", "^"], 2, spread=2, salt=63)
    flock(g, 37, 24, ["C", "e"], 2, spread=2, salt=64)
    put(g, 62, 16, "H")                        # Evan's market STALL (real Market_Stalls sprite)
    put(g, 65, 17, "n")                        # hanging shop sign
    scatter(g, [(59, 17), (66, 18), (60, 19)], "3")    # barrels/crates of goods
    put(g, 63, 19, "N")                        # Evan at the counter
    grove(g, 57, 30, 5, spread=3, salt=21, kinds="Tt4")
    grove(g, 69, 31, 5, spread=3, salt=22, kinds="TtT")
    scatter(g, [(68, 18), (70, 19)], "T")
    scatter(g, [(66, 21), (69, 22), (66, 31), (69, 32)], "F")   # slime clearing frame
    scatter(g, [(58, 22), (71, 20)], "y")

    # ===== the RIVER (cols ~74-79) + geese on the banks =====
    flock(g, 72, 12, ["U", "U"], 2, spread=2, salt=31)
    flock(g, 81, 36, ["U", "R"], 2, spread=2, salt=32)
    putw(g, 77, 8, "l")                        # a swan drifting upriver

    # ===== REGION 3: WOODS (cols 82-148) — the long wild stretch =====
    put(g, 84, path_y(84) + 2, "g")            # bower gate: entering the woods
    put(g, 86, path_y(86) - 1, "n")            # trailhead signpost
    grove(g, 86, 16, 7, spread=4, salt=1, kinds="Tt46")
    grove(g, 97, 14, 8, spread=5, salt=2, kinds="TT7t")
    grove(g, 108, 17, 7, spread=4, salt=3, kinds="t645")
    grove(g, 120, 15, 8, spread=5, salt=7, kinds="TtT6")
    grove(g, 132, 17, 7, spread=4, salt=8, kinds="T7t4")
    grove(g, 143, 15, 7, spread=4, salt=9, kinds="Tt65")
    grove(g, 88, 32, 7, spread=4, salt=4, kinds="T6t7")
    grove(g, 100, 34, 8, spread=5, salt=5, kinds="TtT4")
    grove(g, 112, 33, 6, spread=4, salt=6, kinds="t6T5")
    grove(g, 134, 34, 8, spread=5, salt=10, kinds="Tt76")
    grove(g, 145, 32, 6, spread=4, salt=16, kinds="T4t6")
    # understory: stumps, berries, mushrooms, boulders, small life
    scatter(g, [(90, 20), (104, 31), (117, 19), (129, 33), (140, 20)], "u")
    scatter(g, [(94, 18), (110, 35), (124, 17), (137, 31), (146, 19)], "&")
    scatter(g, [(92, 33), (106, 19), (122, 35), (131, 19), (142, 34)], "m")
    scatter(g, [(98, 20), (126, 32), (144, 17)], "r")
    scatter(g, [(96, 32), (128, 18)], "j")
    scatter(g, [(102, 20), (136, 33)], "R")
    scatter(g, [(93, 21), (115, 34), (141, 18)], "y")
    # the CAMP CLEARING (future skeleton arena — dressing only, mobs next slice);
    # everything sits SOUTH of the road so the tall tent never covers the path
    put(g, 118, 34, "s")                       # small tent
    put(g, 122, 33, "0")                       # campfire
    scatter(g, [(120, 34), (124, 34), (123, 31)], "1")   # camp props
    scatter(g, [(119, 31), (125, 32)], "u")               # stump seats
    put(g, 116, 32, "r")
    # FOREST FILL: clumpy tree cover across the whole woods band so it reads as
    # a real forest, not parkland — keeps a 3-tile corridor along the path and
    # leaves the camp clearing open
    fill_kinds = "TtT4t6T7"
    for x in range(84, 149):
        for y in range(2, H - 2):
            if abs(x - 122) <= 6 and abs(y - 31) <= 4:
                continue                        # the camp clearing stays open
            band = path_y(x)
            if band - 3 <= y <= band + 6:
                continue                        # breathing room along the road
            p = 0.5 if hh(x // 4 + 31, y // 4) < 0.42 else 0.06
            if hh(x * 3 + 1, y * 5 + 2) < p:
                putg(g, x, y, fill_kinds[int(hh(x + 7, y + 9) * 8) % 8])

    # ===== REGION 4: LIBRARY & LAKE (cols 152-190) =====
    for lx in (150, 157):                      # lamp-lit final approach
        put(g, lx, path_y(lx) - 1, "+")
        put(g, lx, path_y(lx) + 4, "+")
    building(g, 162, 17, "L", fence=False)     # Inn_Black = the darker library
    put(g, 166, 20, "N")                        # Irene
    put(g, 165, 19, "x")                        # chest anchored beside the door
    scatter(g, [(156, 22), (170, 22), (156, 27), (172, 27)], "i")
    scatter(g, [(158, 26), (168, 26), (174, 26)], "b")
    scatter(g, [(158, 24), (168, 24), (166, 28), (172, 24), (154, 26)], "f")
    # the climax palette shift: golden birch + fruit trees around the library
    grove(g, 154, 22, 5, spread=3, salt=41, kinds="454")
    grove(g, 181, 24, 6, spread=4, salt=42, kinds="45t4")
    grove(g, 176, 20, 4, spread=3, salt=44, kinds="544")
    scatter(g, [(158, 21), (171, 21)], "8")
    scatter(g, [(153, 28), (175, 22)], "9")
    # lake life: swimmers IN the water, waterfowl + fisherman on the shore
    flock(g, 166, 29, ["d", "d", "U"], 4, spread=4, salt=43)
    put(g, 163, 29, "$")                        # Ariana (unique dialogue anchor), on the shoreline
    scatter(g, [(157, 29), (178, 29)], "R")
    putg(g, 156, 29, "N")                       # fisherman villager by the boat
    putw(g, 158, 33, "O")                       # moored boat
    putw(g, 162, 35, "a")                       # swimming ducks
    putw(g, 170, 33, "a")
    putw(g, 175, 36, "a")
    putw(g, 167, 37, "l")                       # swan
    putw(g, 165, 33, "k")                       # capybara (open water, clear of the shore/boat)
    putw(g, 181, 34, "@")                       # albino capybara

    # ===== VARIANT EMPHASIS =====
    if variant == 2:
        building(g, 50, 13, "P")               # coop
        put(g, 41, 33, "Z")                     # silo
        building(g, 8, 33, "E", fence=False)
        rect(g, 6, 6, 12, 9, "D")
        flock(g, 51, 17, ["C", "^"], 2, spread=2, salt=51)
    if variant == 3:
        for bx, by in ((21, 17), (27, 34)):     # thin the village
            put(g, bx, by, ".")
        for i, (cx, cy) in enumerate(((8, 12), (40, 13), (50, 33), (60, 34),
                                      (90, 12), (102, 12), (33, 9), (18, 9),
                                      (114, 12), (126, 34), (138, 12), (148, 34))):
            grove(g, cx, cy, 5, spread=3, salt=70 + i, kinds="Tt46")
        scatter(g, [(46, 20), (72, 34), (56, 33), (110, 20), (130, 20)], "m")
        scatter(g, [(30, 22), (86, 20), (100, 33), (144, 33)], "&")
        scatter(g, [(34, 24), (94, 21), (118, 33)], "y")

    check_connected(g)
    return "\n".join("".join(r) for r in g) + "\n"


if __name__ == "__main__":
    v = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    out = sys.argv[2] if len(sys.argv) > 2 else f"valley-{v}.txt"
    txt = build(v)
    open(out, "w").write(txt)
    print("wrote", out)
