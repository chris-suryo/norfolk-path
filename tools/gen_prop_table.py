#!/usr/bin/env python3
"""Generate scripts/prop_table.gd — the data table main.gd uses to place every
map prop as a live y-sorted node, mirroring tools/preview_map.py's pass 3.

Why generated: the coordinates must match the preview exactly, and this script
VALIDATES every sheet path + atlas region against the pack on disk (a check that
runs in the sandbox, unlike the Godot engine). Emits a pure-data GDScript const
dict; main.gd interprets it. Re-run after changing any pass-3 sprite.

Placement math: preview blits a sheet region at top-left (px_+ax, py_+ay) where
(px_,py_) is the cell centre. A Godot Sprite2D (centered=true, region_rect=r) at
the cell centre needs offset = (ax + rw/2, ay + rh/2) to land identically.
"""
import os
import struct
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FREE = "assets/cute_fantasy/Cute_Fantasy_Free/"
FULL = "assets/cute_fantasy/packs/Cute_Fantasy/Cute_Fantasy/"
FREE_RES = "res://" + FREE
FULL_RES = "res://" + FULL


def dims(rel):
    d = open(os.path.join(REPO, rel), "rb").read(33)
    return struct.unpack(">II", d[16:24])


# sheet key -> relative path (FREE or FULL)
SHEETS = {
    "oak": FREE + "Outdoor decoration/Oak_Tree.png",
    "oak_s": FREE + "Outdoor decoration/Oak_Tree_Small.png",
    "fences": FREE + "Outdoor decoration/Fences.png",
    "chicken": FREE + "Animals/Chicken/Chicken.png",
    "cow": FREE + "Animals/Cow/Cow.png",
    "pig": FREE + "Animals/Pig/Pig.png",
    "sheep": FREE + "Animals/Sheep/Sheep.png",
    "decor": FREE + "Outdoor decoration/Outdoor_Decor_Free.png",
    "chest": FREE + "Outdoor decoration/Chest.png",
    "stall": FULL + "Buildings/Buildings/Unique_Buildings/Stalls/Market_Stalls.png",
    "inn": FULL + "Buildings/Buildings/Unique_Buildings/Inn/Inn_Black.png",
    "house_a": FULL + "Buildings/Buildings/Houses/Wood/House_1_Wood_Base_Blue.png",
    "house_g": FULL + "Buildings/Buildings/Houses/Wood/House_2_Wood_Base_Red.png",
    "house_j": FULL + "Buildings/Buildings/Houses/Stone/House_4_Stone_Base_Blue.png",
    "house_e": FULL + "Buildings/Buildings/Houses/Limestone/House_3_Limestone_Base_Red.png",
    "barn": FULL + "Buildings/Buildings/Unique_Buildings/Barn/Barn_Base_Red.png",
    "well": FULL + "Outdoor decoration/Well.png",
    "bench": FULL + "Outdoor decoration/Benches.png",
    "duck": FULL + "Animals/Duck/Duck_01.png",
    "capy": FULL + "Animals/Kapybara/Static/Kapybara_Idle.png",
    "capy2": FULL + "Animals/Kapybara/Static/Albino_Kapybara_Idle.png",
    "horse": FULL + "Animals/Horse/Horse_01.png",
    "villager": FULL + "NPCs (Premade)/Farmer_Bob.png",
    "goose": FULL + "Animals/Goose/Goose_01.png",
    "swan": FULL + "Animals/Swan/Swan_01.png",
    "frog": FULL + "Animals/Frog/Frog_01.png",
    "mouse": FULL + "Animals/Mouse/Mouse_01.png",
    "birch_s": FULL + "Trees/Small_Birch_Tree.png",
    "birch_b": FULL + "Trees/Big_Birch_Tree.png",
    "spruce_s": FULL + "Trees/Small_Spruce_Tree.png",
    "spruce_b": FULL + "Trees/Big_Spruce_tree.png",
    "apple_t": FULL + "Crops/Apple_Tree.png",
    "cherry_t": FULL + "Crops/Cherry_Tree.png",
    "bower": FULL + "Crops/Grapes_Bower.png",
    "windmill": FULL + "Buildings/Buildings/Unique_Buildings/Windmill/Windmill.png",
    "tent": FULL + "Buildings/Buildings/Tent/Tent_Small.png",
    "campfire": FULL + "Outdoor decoration/Outdoor_Decor_Animations/Other_Animations/Campfire_Anim.png",
    "campdecor": FULL + "Outdoor decoration/Camp_Decor.png",
    "beehive": FULL + "Animals/Bee/Bee_Hive.png",
    "berries2": FULL + "Crops/Berries.png",
    "trough": FULL + "Outdoor decoration/Water_Troughs.png",
    "lamp2": FULL + "Outdoor decoration/Lanter_Posts.png",
    "rooster": FULL + "Animals/Chicken/Rooster.png",
    "wfence": FULL + "Outdoor decoration/White_Fence.png",
    "butterfly": FULL + "Animals/Butterfly/Butterfly.png",
    "boat": FULL + "Outdoor decoration/Boat.png",
    "scarecrow": FULL + "Outdoor decoration/Scarecrows.png",
    "haybale": FULL + "Outdoor decoration/Hay_Bales.png",
    "barrels": FULL + "Outdoor decoration/barrels.png",
}

# Symbols handled specially in main.gd (NOT emitted into the flat table):
#   F, | : fence adjacency logic (piece + collider depend on neighbours)
#   S    : player spawn        H : special (drawn from stall sheet, has a Shop node)
#   $, C : dialogue/critter anchors are placed too, but also draw as props here.
# Everything else -> table entry: (sheet, rx, ry, rw, rh, ax, ay, col_w, col_h)
# ax/ay = the preview blit top-left offset from cell centre; col_* = collider (0 = none).
SPEC = {
    "T": ("oak", 0, 0, 64, 80, -32, -70, 12, 8),
    "t": ("oak_s", 32, 0, 32, 48, -16, -40, 8, 6),
    "H": ("stall", 96, 0, 48, 48, -24, -40, 26, 10),
    "b": ("bench", 0, 0, 32, 32, -16, -18, 26, 8),
    "C": ("chicken", 0, 0, 32, 32, -16, -26, 0, 0),
    "d": ("duck", 0, 0, 32, 32, -16, -22, 0, 0),
    "$": ("duck", 0, 0, 32, 32, -16, -22, 0, 0),
    "k": ("capy", 0, 0, 32, 32, -16, -18, 0, 0),
    "@": ("capy2", 0, 0, 32, 32, -16, -18, 0, 0),
    "h": ("horse", 0, 0, 32, 32, -16, -26, 0, 0),
    "N": ("villager", 0, 0, 64, 64, -32, -54, 0, 0),
    "o": ("cow", 0, 0, 32, 32, -16, -26, 0, 0),
    "p": ("pig", 0, 0, 32, 32, -16, -26, 0, 0),
    "e": ("sheep", 0, 0, 32, 32, -16, -26, 0, 0),
    "U": ("goose", 0, 0, 32, 32, -16, -22, 0, 0),
    "R": ("frog", 0, 0, 32, 32, -16, -22, 0, 0),
    "j": ("mouse", 0, 0, 32, 32, -16, -22, 0, 0),
    "a": ("duck", 0, 256, 32, 32, -16, -20, 0, 0),
    "l": ("swan", 0, 256, 32, 32, -16, -20, 0, 0),
    "4": ("birch_s", 32, 0, 32, 64, -16, -56, 8, 6),
    "5": ("birch_b", 32, 0, 32, 80, -16, -70, 12, 8),
    "6": ("spruce_s", 32, 0, 32, 64, -16, -56, 8, 6),
    "7": ("spruce_b", 64, 0, 64, 80, -32, -70, 12, 8),
    "8": ("apple_t", 0, 0, 32, 64, -16, -56, 8, 6),
    "9": ("cherry_t", 0, 0, 32, 64, -16, -56, 8, 6),
    "g": ("bower", 96, 80, 96, 80, -48, -64, 0, 0),
    "z": ("windmill", 0, 0, 128, 112, -64, -104, 28, 14),
    "s": ("tent", 0, 0, 48, 96, -24, -88, 26, 12),
    "0": ("campfire", 0, 0, 16, 32, -8, -24, 12, 10),
    "1": ("campdecor", 0, 0, 16, 16, -8, -8, 0, 0),
    "%": ("beehive", 0, 0, 16, 16, -8, -10, 10, 8),
    "&": ("berries2", 0, 0, 16, 16, -8, -8, 0, 0),
    "=": ("trough", 16, 0, 32, 32, -16, -24, 28, 10),
    "+": ("lamp2", 0, 0, 16, 48, -8, -40, 6, 8),
    "^": ("rooster", 0, 0, 32, 32, -16, -26, 0, 0),
    "y": ("butterfly", 0, 0, 16, 16, -8, -20, 0, 0),
    "O": ("boat", 0, 0, 48, 48, -24, -34, 0, 0),
    "K": ("scarecrow", 0, 0, 32, 32, -16, -24, 6, 10),
    "2": ("haybale", 0, 0, 16, 16, -8, -8, 12, 8),
    "3": ("barrels", 0, 0, 16, 16, -8, -10, 10, 8),
    "x": ("chest", 0, 0, 16, 16, -8, -12, 12, 8),
    "|": ("wfence", 16, 0, 16, 16, -8, -8, 14, 6),
    # FREE Outdoor_Decor_Free regions (see preview_map decor_region):
    "r": ("decor", 0, 48, 16, 16, -8, -8, 12, 8),
    "u": ("decor", 0, 32, 16, 16, -8, -8, 10, 6),
    "w": ("decor", 0, 16, 16, 16, -8, -8, 0, 0),
    "f": ("decor", 32, 176, 16, 16, -8, -8, 0, 0),
    "m": ("decor", 32, 112, 16, 16, -8, -8, 0, 0),
    "n": ("decor", 48, 0, 16, 16, -8, -8, 8, 10),
    "i": ("decor", 64, 64, 16, 64, -8, -56, 6, 12),
}

# Buildings drawn via blit_building (whole sheet, foot offset) — derive region +
# offset from the sheet dims so we don't hand-copy 240x192 etc.
BUILDINGS = {  # sym: (sheet_key, foot, collider_w, collider_h)
    "L": ("inn", 8, 90, 18),
    "A": ("house_a", 8, 52, 14),
    "G": ("house_g", 8, 52, 14),
    "J": ("house_j", 8, 52, 14),
    "E": ("house_e", 8, 52, 14),
    "Y": ("barn", 8, 60, 16),
    "W": ("well", 6, 20, 12),
}


def build_table():
    table = {}
    errors = []
    used_sheets = set()
    for sym, (key, rx, ry, rw, rh, ax, ay, cw, ch) in SPEC.items():
        rel = SHEETS[key]
        sw, sh = dims(rel)
        if rx + rw > sw or ry + rh > sh:
            errors.append(f"{sym}: region ({rx},{ry},{rw},{rh}) exceeds {key} {sw}x{sh}")
        used_sheets.add(key)
        table[sym] = (key, rx, ry, rw, rh, ax + rw / 2.0, ay + rh / 2.0, cw, ch)
    for sym, (key, foot, cw, ch) in BUILDINGS.items():
        rel = SHEETS[key]
        sw, sh = dims(rel)
        used_sheets.add(key)
        # whole sheet, centered offset = (0, foot - sh/2)
        table[sym] = (key, 0, 0, sw, sh, 0.0, foot - sh / 2.0, cw, ch)
    return table, used_sheets, errors


def res_path(rel):
    return "res://" + rel


def emit(table, used_sheets):
    lines = [
        "class_name PropTable",
        "extends RefCounted",
        "",
        "## GENERATED by tools/gen_prop_table.py — do not edit by hand.",
        "## Data table for main.gd: map symbol -> how to draw + collide a prop,",
        "## mirroring tools/preview_map.py pass 3. Regenerate after sprite changes.",
        "",
        "## sheet key -> preloaded texture path.",
        "const SHEETS := {",
    ]
    for key in sorted(used_sheets):
        lines.append('\t"%s": "%s",' % (key, res_path(SHEETS[key])))
    lines.append("}")
    lines.append("")
    lines.append("## symbol -> [sheet_key, region(x,y,w,h), sprite_offset(x,y), collider(w,h)]")
    lines.append("## collider (0,0) = decor, no collision. Offset is from the cell centre.")
    lines.append("const PROPS := {")
    for sym in sorted(table):
        key, rx, ry, rw, rh, ox, oy, cw, ch = table[sym]
        esc = '\\"' if sym == '"' else ("\\\\" if sym == "\\" else sym)
        lines.append(
            '\t"%s": ["%s", Rect2(%d, %d, %d, %d), Vector2(%g, %g), Vector2(%g, %g)],'
            % (esc, key, rx, ry, rw, rh, ox, oy, cw, ch)
        )
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    table, used, errors = build_table()
    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    out = os.path.join(REPO, "scripts", "prop_table.gd")
    open(out, "w").write(emit(table, used))
    print(f"wrote scripts/prop_table.gd: {len(table)} symbols, {len(used)} sheets, 0 region errors")
