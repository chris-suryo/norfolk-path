"""Generate the Norfolk Path valley maps (140 wide) as ASCII .txt.

Builds a grid with guaranteed rectangularity + >=2-wide path/water, then places
region features. Three variants share the golden-path spine, differ in emphasis.
Water symbols (~) drive terrain; props (buildings/animals) sit on GRASS cells so
they never pinch water — pond life goes on the grass shoreline, not in the water.
"""
import sys

W, H = 140, 44
PY = 21  # main path occupies rows PY, PY+1


def blank():
    return [["." for _ in range(W)] for _ in range(H)]


def rect(g, x0, y0, x1, y1, ch):
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            g[y][x] = ch


def hpath(g, x0, x1, y):
    for x in range(x0, x1 + 1):
        g[y][x] = "#"
        g[y + 1][x] = "#"


def vpath(g, y0, y1, x):
    for y in range(y0, y1 + 1):
        g[y][x] = "#"
        g[y][x + 1] = "#"


def put(g, x, y, ch):
    if 0 <= y < H and 0 <= x < W:
        g[y][x] = ch


def scatter(g, cells, ch, only_grass=True):
    for x, y in cells:
        if 0 <= y < H and 0 <= x < W and (not only_grass or g[y][x] == "."):
            g[y][x] = ch


def terrain(g, variant):
    # valley frame: 2 rows top/bottom, west 3 cols, east 2 cols.
    rect(g, 0, 0, W - 1, 1, "~")
    rect(g, 0, H - 2, W - 1, H - 1, "~")
    rect(g, 0, 0, 2, H - 1, "~")
    rect(g, W - 2, 0, W - 1, H - 1, "~")

    # library pond/lake: big water block filling the SE, SOUTH of the path so it
    # never crosses it (same clean pond for every variant).
    rect(g, 104, 29, W - 1, H - 3, "~")

    # mid stream: 2-wide vertical channel top->bottom, bridged on the path.
    sx = 66
    rect(g, sx, 2, sx + 1, H - 3, "~")

    # the golden path: one continuous 2-wide corridor W->E on the north grass.
    hpath(g, 3, 126, PY)
    for yy in (PY, PY + 1):        # bridge over the stream
        for xx in (sx, sx + 1):
            g[yy][xx] = "B"

    # woods S-bend: detour the path south between cols 78-96 (skip in variant 2).
    if variant != 2:
        for x in range(80, 95):   # erase the straight middle
            g[PY][x] = "."
            g[PY + 1][x] = "."
        vpath(g, PY, 27, 78)
        vpath(g, PY, 27, 95)
        hpath(g, 78, 96, 27)


def place(g, variant):
    # ===== REGION 1: THE VILLAGE (cols 4-40) =====
    put(g, 8, 12, "A")
    put(g, 16, 11, "G")
    put(g, 26, 12, "J")
    put(g, 34, 11, "Y")     # barn
    put(g, 12, 30, "A")
    put(g, 22, 31, "G")
    put(g, 31, 30, "J")
    put(g, 19, 27, "W")     # wells
    put(g, 14, 17, "W")
    rect(g, 6, 33, 13, 37, "D")     # farm plots (solid rectangles)
    rect(g, 28, 33, 37, 37, "D")
    if variant == 2:
        rect(g, 5, 5, 15, 9, "D")
        rect(g, 30, 5, 39, 9, "D")
    # fenced pasture with livestock (south)
    for x in range(17, 27):
        put(g, x, 34, "F")
        put(g, x, 39, "F")
    for y in range(34, 40):
        put(g, 17, y, "F")
        put(g, 26, y, "F")
    scatter(g, [(19, 36), (22, 37), (24, 35), (20, 38)], "o")
    scatter(g, [(21, 35), (23, 38)], "e")
    scatter(g, [(18, 37), (25, 36)], "p")
    scatter(g, [(10, 14), (18, 14), (28, 15), (11, 28), (24, 29), (33, 28)], "C")
    scatter(g, [(13, 24), (21, 18), (30, 25), (9, 25)], "N")
    scatter(g, [(x, 19) for x in range(6, 40, 3)], "w")
    scatter(g, [(x, 24) for x in range(6, 40, 4)], "f")
    scatter(g, [(7, 15), (17, 16), (27, 16), (35, 15)], "v")
    scatter(g, [(x, 32) for x in range(6, 14, 2)], "v")     # crop rows by the plots
    scatter(g, [(x, 32) for x in range(28, 38, 2)], "q")
    scatter(g, [(9, 38), (11, 38), (35, 38), (32, 38)], "q")
    if variant == 3:
        scatter(g, [(6, 6), (12, 7), (33, 7)], "t")     # wilder village
    g[PY][5] = "S"      # spawn on the path, far west

    # ===== REGION 2: PATH & EVAN'S STALL (cols 42-66) =====
    put(g, 50, 18, "H")     # Evan's Market_Stalls, roadside
    put(g, 48, 17, "N")     # Evan
    scatter(g, [(46, 16), (54, 16)], "f")
    scatter(g, [(44, 15), (47, 26), (52, 27), (58, 14), (62, 26), (44, 27), (57, 26)], "T")
    scatter(g, [(49, 14), (55, 25), (60, 15), (63, 27), (46, 25)], "t")
    scatter(g, [(56, 16), (59, 17), (56, 26), (59, 27)], "F")    # slime clearing frame
    scatter(g, [(61, 16), (45, 18)], "r")
    scatter(g, [(53, 25), (58, 25)], "u")

    # ===== REGION 3: THE WOODS (cols 68-98) =====
    scatter(g, [(70, 15), (73, 26), (76, 14), (84, 15), (88, 24), (92, 15),
                (96, 25), (72, 31), (98, 31), (94, 16), (76, 31), (100, 26),
                (69, 25), (74, 17), (98, 17)], "T")
    scatter(g, [(82, 31), (89, 16), (93, 31), (97, 15), (71, 17), (79, 32),
                (85, 31), (95, 17), (70, 32)], "t")
    scatter(g, [(83, 24), (91, 24), (83, 31), (91, 31)], "F")    # skeleton pocket
    scatter(g, [(78, 18), (95, 24), (73, 33)], "r")
    scatter(g, [(81, 18), (93, 18), (77, 33)], "u")
    scatter(g, [(80, 20), (90, 20), (85, 34)], "m")

    # ===== REGION 4: LIBRARY & LAKE (cols 100-137) =====
    pond_top = 29
    lib_x = 114
    put(g, lib_x, 23, "L")          # Inn = the library, looking over the pond
    put(g, lib_x + 4, 25, "N")      # Irene, beside it
    # reading garden between the path and the pond
    scatter(g, [(108, 24), (120, 24), (108, 27), (120, 27)], "i")   # lamp posts
    scatter(g, [(110, 26), (118, 26)], "b")                         # benches
    scatter(g, [(112, 27), (116, 27), (110, 24), (122, 26), (119, 28)], "f")
    put(g, 122, 24, "x")                                            # chest
    scatter(g, [(106, 18), (110, 15), (124, 16), (128, 24), (131, 18),
                (133, 14), (129, 11), (135, 20)], "T")
    scatter(g, [(108, 16), (126, 15), (130, 26), (132, 22)], "t")
    scatter(g, [(112, 17), (120, 16), (127, 20), (133, 24)], "w")
    scatter(g, [(128, 18), (131, 26)], "f")
    # pond life on the GRASS shoreline (row just above the pond) + Ariana
    sh = pond_top - 1
    scatter(g, [(110, sh), (117, sh), (124, sh), (129, sh)], "d")   # ambient ducks
    put(g, 126, sh, "k")                                            # capybara
    put(g, 114, sh, "d")                                            # Ariana

    # ===== VARIANT EMPHASIS =====
    if variant == 2:   # settled homestead: coop, silo, a second pen, more crops
        put(g, 43, 12, "P")     # chicken coop
        put(g, 39, 30, "Z")     # silo
        put(g, 45, 31, "A")     # extra cottage
        for x in range(31, 39):
            put(g, x, 24, "F")
            put(g, x, 28, "F")
        for y in range(24, 29):
            put(g, 31, y, "F")
            put(g, 38, y, "F")
        scatter(g, [(33, 26), (36, 27), (34, 25), (37, 26)], "e")   # sheep pen
        scatter(g, [(43, 15), (46, 28), (41, 20)], "C")
        scatter(g, [(41, 26), (44, 20), (42, 32)], "q")
    if variant == 3:   # wild valley: thin the village, thicken the trees/verges
        for hx, hy in ((26, 12), (31, 30), (22, 31)):     # remove some houses
            put(g, hx, hy, ".")
        scatter(g, [(6, 6), (12, 8), (33, 6), (38, 30), (40, 14), (5, 27),
                    (64, 8), (60, 34), (104, 34), (100, 12), (72, 8), (90, 8),
                    (46, 30), (54, 8), (36, 8)], "T")
        scatter(g, [(8, 8), (36, 9), (62, 10), (106, 34), (48, 28), (58, 32)], "t")
        scatter(g, [(40, 12), (44, 26), (52, 30), (68, 33)], "m")
        scatter(g, [(10, 7), (30, 8), (50, 34)], "w")


def build(variant):
    g = blank()
    terrain(g, variant)
    place(g, variant)
    return "\n".join("".join(r) for r in g) + "\n"


if __name__ == "__main__":
    v = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    out = sys.argv[2] if len(sys.argv) > 2 else f"valley-{v}.txt"
    open(out, "w").write(build(v))
    print("wrote", out)
