"""Generate the Norfolk Path valley maps (round 2: organic + contextual).

Structure only — the preview tool layers ground texture / shore / detail. Here we
shape: a gently curved golden path with cobble spurs to every building, buildings
in context (cobble apron + fence yard + lamps + flowerbeds), an organic (elliptic)
library lake + a wavy stream, and dense tree borders framing the play space.
Guarantees rectangular + >=2-wide path/water; validate to 0 problems.
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


def scatter(g, cells, ch, only_grass=True):
    for x, y in cells:
        if 0 <= y < H and 0 <= x < W and (not only_grass or g[y][x] == "."):
            g[y][x] = ch


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


BROOK_X = (64, 65, 66)  # the stream columns; path crosses on a bridge here


def path_y(x):
    """Gently undulating golden path. Combined slope stays < 1 tile/col so a
    thick (4-wide) band never pinches the edge autotiler. The path is held
    flat across the brook (cols 62-68) so its 4-thick band meets the bridge as
    a clean rectangle instead of a diagonal 1-wide nub at the water lip."""
    xc = 65 if 62 <= x <= 68 else x
    return PY + int(round(3.5 * math.sin((xc - 4) / 19.0) + 1.5 * math.sin((xc - 4) / 8.0)))


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


def spur(g, bx, by, ch="c"):
    """2-wide vertical connector from a building's door down/up to the path."""
    ty = path_y(bx)
    lo, hi = sorted((by, ty))
    for y in range(lo, hi + 1):
        for dx in (0, 1):
            if g[y][bx + dx] == ".":
                g[y][bx + dx] = ch if ch == "c" else "#"


def building(g, bx, by, sym, fence=True, lamps=True):
    """Place a building in context: cobble apron at the door, a spur to the path,
    flanking lamps, a partial fence yard, and a flowerbed cluster."""
    put(g, bx, by, sym)
    rect(g, bx, by + 1, bx + 1, by + 2, "c")          # cobble apron at the door
    spur(g, bx, by + 2, "c")                            # connect to the path
    if lamps:
        put(g, bx - 2, by + 1, "i")
        put(g, bx + 2, by + 1, "i")
    if fence:
        for x in range(bx - 3, bx + 4):
            put(g, x, by - 2, "F")
        put(g, bx - 3, by - 1, "F")
        put(g, bx + 3, by - 1, "F")
    scatter(g, [(bx - 2, by + 2), (bx + 2, by + 2), (bx - 1, by + 3), (bx + 1, by + 3)], "f")


def putg(g, x, y, ch):  # place only on open grass
    if 0 <= y < H and 0 <= x < W and g[y][x] == ".":
        g[y][x] = ch


def tree_border(g):
    """Dense tree bands framing the valley (north/south/west edges), grass only."""
    for x in range(0, W):
        for y in range(0, 3 + (x * 7 % 3)):
            putg(g, x, y, "T" if (x + y) % 3 else "t")
        for y in range(H - 3 - (x * 5 % 3), H):
            putg(g, x, y, "T" if (x + y) % 2 else "t")
    for y in range(0, H):
        for x in range(0, 2 + (y * 3 % 2)):
            putg(g, x, y, "T" if (x + y) % 2 else "t")


def make_water(g, variant):
    # library lake in the SE, south of the path — a rounded rectangle so the
    # shore reads as long smooth runs (few 45-degree stairs) not a stepped ellipse
    x0 = 100 if variant == 3 else 104
    rrect(g, x0, 30, W - 1, H - 3, 6, "~")
    # straight brook (3-wide) crossing the path with a clean bridge
    for y in range(3, H - 3):
        for x in (64, 65, 66):
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

    # ===== REGION 1: VILLAGE (cols 6-42) =====
    building(g, 12, 12, "A")
    building(g, 24, 11, "G")
    building(g, 36, 12, "Y", fence=False)     # barn
    building(g, 14, 34, "J")
    building(g, 30, 35, "A")
    put(g, 20, 31, "W")
    rect(g, 7, 38, 12, 42, "D")               # farm plots
    rect(g, 33, 38, 40, 42, "D")
    for x in range(17, 27):                   # livestock pen
        put(g, x, 37, "F")
        put(g, x, 43, "F")
    for y in range(37, 44):
        put(g, 17, y, "F")
        put(g, 26, y, "F")
    scatter(g, [(19, 40), (22, 41), (24, 39), (20, 42), (23, 40)], "o")
    scatter(g, [(21, 39), (25, 42)], "e")
    scatter(g, [(18, 41), (25, 39)], "p")
    scatter(g, [(10, 18), (28, 17), (16, 30), (34, 30), (9, 40), (38, 39)], "C")
    scatter(g, [(15, 20), (31, 19), (11, 32)], "N")
    g[path_y(6)][6] = "S"

    # ===== REGION 2: PATH & EVAN'S STALL (cols 46-64) =====
    building(g, 52, 15, "H", fence=False)     # Evan's Market_Stalls
    put(g, 50, 14, "N")                        # Evan
    scatter(g, [(47, 18), (49, 30), (55, 31), (60, 17), (62, 30), (46, 31)], "T")
    scatter(g, [(51, 30), (58, 18), (63, 31), (48, 17)], "t")
    scatter(g, [(56, 20), (59, 21), (56, 30), (59, 31)], "F")   # slime clearing frame

    # ===== REGION 3: WOODS (cols 68-100) — trees clustered into groves =====
    grove(g, 72, 17, 7, spread=4, salt=1)       # north-side groves
    grove(g, 84, 16, 8, spread=5, salt=2)
    grove(g, 97, 17, 7, spread=4, salt=3)
    grove(g, 74, 32, 7, spread=4, salt=4)       # south-side groves
    grove(g, 96, 32, 8, spread=5, salt=5)
    grove(g, 70, 31, 5, spread=3, salt=6)
    scatter(g, [(83, 20), (91, 20), (83, 30), (91, 30)], "F")   # skeleton pocket
    scatter(g, [(80, 22), (88, 22), (85, 35)], "m")

    # ===== REGION 4: LIBRARY & LAKE (cols 104-143, lake top at row 30) =====
    building(g, 114, 17, "L", fence=False)     # Inn = library, above its lake
    put(g, 118, 20, "N")                        # Irene
    scatter(g, [(108, 22), (120, 22), (108, 27), (122, 27)], "i")   # lamp posts
    scatter(g, [(110, 26), (118, 26), (114, 28), (124, 26)], "b")   # benches
    scatter(g, [(110, 24), (118, 24), (116, 28), (122, 24), (106, 26)], "f")
    put(g, 123, 22, "x")                        # chest
    grove(g, 106, 22, 5, spread=3, salt=41)     # groves framing the reading garden
    grove(g, 132, 24, 6, spread=4, salt=42)
    # pond life on the grass shoreline (row 29, just above the lake top)
    scatter(g, [(112, 29), (120, 29), (126, 29)], "d")
    putg(g, 116, 29, "d")                        # Ariana (grass shoreline only)
    putg(g, 109, 29, "k")                        # capybara (grass shoreline only)

    # ===== VARIANT EMPHASIS =====
    if variant == 2:
        building(g, 44, 12, "P")               # coop
        put(g, 40, 34, "Z")                     # silo
        building(g, 45, 35, "A")
        rect(g, 6, 6, 14, 9, "D")
        scatter(g, [(43, 16), (46, 30)], "C")
    if variant == 3:
        for bx, by in ((24, 11), (30, 35)):     # thin the village
            put(g, bx, by, ".")
        for i, (cx, cy) in enumerate(((8, 12), (40, 14), (46, 33), (58, 34),
                                      (72, 13), (90, 13), (33, 9), (18, 9))):
            grove(g, cx, cy, 5, spread=3, salt=70 + i)   # trees reclaim the valley
        scatter(g, [(42, 20), (68, 34), (52, 33)], "m")

    return "\n".join("".join(r) for r in g) + "\n"


if __name__ == "__main__":
    v = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    out = sys.argv[2] if len(sys.argv) > 2 else f"valley-{v}.txt"
    open(out, "w").write(build(v))
    print("wrote", out)
