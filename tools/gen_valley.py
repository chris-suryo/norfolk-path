"""Generate the Norfolk Path valley maps (round 4: less procedural, more varied).

Structure only — the preview tool layers ground texture / shore / detail. Here we
shape: an undulating golden path with cobble spurs that reach each door, buildings
in context (apron + spur + lamps + fenced yard + flowerbeds), a smooth rounded
library lake with a moored boat, a gently bending bridged brook, two distinct farm
plots (carrots + wheat), loosely-clustered animal flocks, and a VARIED tree border
(uneven depth, gaps, clumps, a scrub buffer) so the frame doesn't read machine-made.
Guarantees rectangular + >=2-wide path/water/farm; validate to 0 problems.
"""
import math
import sys

W, H = 144, 48
PY = 24  # golden-path base row


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


def scatter(g, cells, ch, only_grass=True):
    for x, y in cells:
        if 0 <= y < H and 0 <= x < W and (not only_grass or g[y][x] == "."):
            g[y][x] = ch


def hh(a, b=0):
    """Deterministic 1-D-ish hash in [0,1) for border/flock jitter."""
    n = (a * 374761393 + b * 668265263) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n & 0xFFFFFF) / 0xFFFFFF


def ellipse(g, cx, cy, rx, ry, ch, only=None):
    for y in range(max(0, cy - ry - 1), min(H, cy + ry + 2)):
        for x in range(max(0, cx - rx - 1), min(W, cx + rx + 2)):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                if only is None or g[y][x] == only:
                    g[y][x] = ch


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
    """Gently undulating golden path. Combined slope stays < 1 tile/col so a
    thick (4-wide) band never pinches the edge autotiler. Held flat across the
    brook (cols 62-68) so its 4-thick band meets the bridge as a clean rectangle."""
    xc = 65 if 62 <= x <= 68 else x
    return PY + int(round(3.5 * math.sin((xc - 4) / 19.0) + 1.5 * math.sin((xc - 4) / 8.0)))


def brook_cx(y):
    """Centre column of the bending brook; held straight where the path crosses
    (rows 20-30) so the bridge sits on a clean rectangle of water."""
    if 20 <= y <= 30:
        return 65
    return 65 + int(round(1.3 * math.sin((y - 3) / 8.0)))


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


def draw_path(g, x0, x1, thick=4):
    for x in range(x0, x1 + 1):
        y = path_y(x)
        for t in range(thick):
            put(g, x, y + t, "#")


def grove(g, cx, cy, n, spread=4, salt=0):
    """A cluster of trees around (cx, cy) — reads as a natural grove."""
    for i in range(n):
        r = (i * 7 + salt * 13) % 97 / 97.0
        r2 = (i * 11 + salt * 5) % 89 / 89.0
        gx = cx + int((r - 0.5) * 2 * spread)
        gy = cy + int((r2 - 0.5) * 2 * spread)
        putg(g, gx, gy, "T" if (gx + gy) % 3 else "t")


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


def building(g, bx, by, sym, fence=True, lamps=True):
    """Place a building in context: a cobble ribbon that REACHES the door and runs
    to the path, flanking lamps, a fenced yard behind, and a flowerbed cluster.
    The apron/spur go on the path-facing side; the fence goes on the far side."""
    put(g, bx, by, sym)
    ty = path_y(bx)
    step = 1 if ty > by else -1                 # direction from building to path
    y = by
    while y != ty:                              # continuous cobble door -> path
        y += step
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


def tree_border(g):
    """A VARIED tree frame: uneven band depth (0-4 tiles) with occasional gaps and
    denser clumps, a mix of big/small oaks, plus a scrubby buffer of stray trees a
    little further in — so the edge doesn't read as one mechanical wall of trees."""
    def band(x, phase, salt):
        d = 1 + int(2.3 * (0.5 + 0.5 * math.sin(x / 6.0 + phase)))  # 1..3
        if hh(x, salt + 20) < 0.10:
            return 0                                                # a gap
        if hh(x, salt + 30) < 0.12:
            return d + 2                                            # a dense clump
        return d

    for x in range(W):
        dn = band(x, 0.0, 0)
        for y in range(dn):
            putg(g, x, y, "T" if hh(x * 7 + y, 3) < 0.55 else "t")
        if hh(x, 4) < 0.20:                                         # scrub buffer
            putg(g, x, dn + int(hh(x, 5) * 2), "t")
        ds = band(x, 1.7, 40)
        for y in range(H - ds, H):
            putg(g, x, y, "T" if hh(x * 5 + y, 8) < 0.5 else "t")
        if hh(x, 9) < 0.20:
            putg(g, x, H - ds - 1 - int(hh(x, 10) * 2), "t")
    for y in range(H):                                             # west edge
        dw = 1 + int(1.6 * (0.5 + 0.5 * math.sin(y / 5.0)))
        if hh(y, 11) < 0.12:
            dw = 0
        for x in range(dw):
            putg(g, x, y, "T" if hh(x + y * 3, 12) < 0.5 else "t")


def make_water(g, variant):
    # library lake in the SE — a rounded rectangle pulled UP off the map bottom so
    # its south + corner shores land on visible grass (dressed all the way round),
    # not buried under the tree border.
    x0 = 100 if variant == 3 else 104
    rrect(g, x0, 30, W - 1, 41, 6, "~")
    # gently-bending 3-wide brook, held straight across the path for a clean bridge
    for y in range(3, H - 3):
        cx = brook_cx(y)
        for x in (cx - 1, cx, cx + 1):
            if g[y][x] == "#":
                g[y][x] = "B"
            elif g[y][x] == ".":
                g[y][x] = "~"


def build(variant):
    g = blank()
    draw_path(g, 3, 132)
    make_water(g, variant)
    fix_water(g)
    tree_border(g)

    # ===== REGION 1: VILLAGE (cols 6-42) — more houses, staggered, close to road =====
    building(g, 10, 19, "A")                  # north row sits nearer the path so the
    building(g, 21, 17, "G")                  # cobble spurs are short, not long ribbons
    building(g, 33, 20, "E")                  # limestone house (distinct)
    building(g, 41, 17, "Y", fence=False)     # barn
    building(g, 14, 35, "J")
    building(g, 27, 34, "A")
    building(g, 38, 36, "G")
    put(g, 18, 32, "W")                       # well
    # two DISTINCT farms: carrots (west) + wheat (east) with a scarecrow + hay
    rect(g, 6, 38, 11, 42, "D")               # carrot field
    rect(g, 44, 38, 50, 43, "Q")              # wheat field
    put(g, 47, 37, "K")                        # scarecrow guarding the wheat
    scatter(g, [(43, 40), (43, 42), (51, 39)], "2")   # hay bales
    # livestock pen with a loosely-clustered flock (not a row)
    for x in range(16, 26):
        put(g, x, 37, "F")
        put(g, x, 43, "F")
    for y in range(37, 44):
        put(g, 16, y, "F")
        put(g, 25, y, "F")
    flock(g, 21, 40, ["o", "o", "p", "e"], 6, spread=3, salt=11)
    # chickens + villagers, loosely clustered
    flock(g, 12, 20, ["C", "C", "N"], 3, spread=3, salt=12)
    flock(g, 30, 20, ["C", "N", "C"], 3, spread=4, salt=13)
    flock(g, 34, 30, ["C", "N"], 2, spread=3, salt=14)
    scatter(g, [(8, 24), (26, 27), (43, 22)], "y")     # butterflies in the meadow
    g[path_y(6)][6] = "S"

    # ===== REGION 2: PATH & EVAN'S SHOP (cols 46-64) — one distinct building =====
    building(g, 52, 15, "H", fence=False)     # Evan's shop (Fisherman house)
    put(g, 52, 16, "M")                        # market awning against the shopfront
    put(g, 55, 17, "n")                        # hanging shop sign
    scatter(g, [(49, 17), (55, 19), (50, 19)], "3")    # barrels/crates of goods
    put(g, 53, 19, "N")                        # Evan at the counter
    grove(g, 47, 30, 5, spread=3, salt=21)     # framing groves
    grove(g, 61, 31, 5, spread=3, salt=22)
    scatter(g, [(58, 18), (60, 19)], "T")
    scatter(g, [(56, 20), (59, 21), (56, 30), (59, 31)], "F")   # slime clearing frame
    scatter(g, [(48, 22), (62, 20)], "y")

    # ===== REGION 3: WOODS (cols 68-100) — trees clustered into groves =====
    grove(g, 72, 17, 7, spread=4, salt=1)       # north-side groves
    grove(g, 84, 16, 8, spread=5, salt=2)
    grove(g, 97, 17, 7, spread=4, salt=3)
    grove(g, 74, 32, 7, spread=4, salt=4)       # south-side groves
    grove(g, 96, 32, 8, spread=5, salt=5)
    grove(g, 70, 31, 5, spread=3, salt=6)
    scatter(g, [(83, 20), (91, 20), (83, 30), (91, 30)], "F")   # skeleton pocket
    scatter(g, [(80, 22), (88, 22), (85, 35)], "m")             # mushrooms
    scatter(g, [(78, 21), (94, 34)], "j")                        # mice
    scatter(g, [(76, 20), (90, 33)], "y")

    # ===== REGION 4: LIBRARY & LAKE (cols 104-143, lake top row 30) =====
    building(g, 114, 17, "L", fence=False)     # Inn_Black = darker library, its lake
    put(g, 118, 20, "N")                        # Irene
    scatter(g, [(108, 22), (120, 22), (108, 27), (122, 27)], "i")   # lamp posts
    scatter(g, [(110, 26), (118, 26), (124, 26)], "b")             # benches
    scatter(g, [(110, 24), (118, 24), (116, 28), (122, 24), (106, 26)], "f")
    put(g, 123, 22, "x")                        # chest
    grove(g, 106, 22, 5, spread=3, salt=41)     # groves framing the reading garden
    grove(g, 133, 24, 6, spread=4, salt=42)
    # lake life: a loose flock of waterfowl on the shore, a boat, a capybara IN the lake
    flock(g, 120, 29, ["d", "d", "U", "V"], 6, spread=4, salt=43)   # ducks/geese/swan
    scatter(g, [(112, 29), (128, 29)], "R")     # frogs on the shore
    putg(g, 116, 29, "d")                        # Ariana (grass shoreline)
    put(g, 128, 34, "O")                         # moored boat (on lake water)
    put(g, 111, 32, "k")                         # capybara wading IN the lake (water-backed)

    # ===== VARIANT EMPHASIS =====
    if variant == 2:
        building(g, 45, 12, "P")               # coop
        put(g, 42, 33, "Z")                     # silo
        building(g, 8, 34, "E")
        rect(g, 6, 6, 12, 9, "D")
        flock(g, 46, 16, ["C", "C"], 2, spread=2, salt=51)
    if variant == 3:
        for bx, by in ((22, 11), (27, 34)):     # thin the village
            put(g, bx, by, ".")
        for i, (cx, cy) in enumerate(((8, 12), (40, 14), (46, 33), (58, 34),
                                      (72, 13), (90, 13), (33, 9), (18, 9))):
            grove(g, cx, cy, 5, spread=3, salt=70 + i)   # trees reclaim the valley
        scatter(g, [(42, 20), (68, 34), (52, 33)], "m")
        scatter(g, [(30, 22), (80, 20), (100, 33)], "y")

    return "\n".join("".join(r) for r in g) + "\n"


if __name__ == "__main__":
    v = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    out = sys.argv[2] if len(sys.argv) > 2 else f"valley-{v}.txt"
    open(out, "w").write(build(v))
    print("wrote", out)
