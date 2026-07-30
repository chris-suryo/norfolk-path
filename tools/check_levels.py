#!/usr/bin/env python3
"""CI rules for the connected-levels graph + dialogue coverage.

The bug classes these encode were hunted by hand once (world-alive slice
pressure test); this locks them in forever, per the testing-loop
self-improvement rule (docs/testing-loop.md):

  1. every transition targets a REGISTERED level
  2. a transition's named entry exists in its target (else it silently falls
     back to the target's "S" spawn — flagged, because a typo'd entry id would
     strand arrivals at the wrong door)
  3. arrival cells are in-bounds and walkable (not water/wall)
  4. an arrival cell must not sit INSIDE a return trigger back to where the
     player came from (bounce loop; the arm-guard mitigates but placement
     should never rely on it)
  5. trigger rects sit inside their source map
  6. every map is rectangular; every ground PNG exists on disk
  7. every interior has exactly one spawn "S" ADJACENT to exactly one exit
     mat ">" (the door pocket)
  8. every talker symbol on every map (villager N, Ariana $, library L) has a
     dialogue_data entry, and no villager id in dialogue_data is orphaned

Run:  python tools/check_levels.py
"""

import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Terrain the player cannot stand on (see level.gd terrain_of): open water +
# on-water props + interior walls. "B" (bridge) IS walkable.
BLOCKED = set("~Okal@X")


def read(rel):
    return open(os.path.join(REPO, rel), encoding="utf-8").read()


def map_rows(rel):
    m = re.search(r'const MAP := """\n(.*?)"""', read(rel), re.S)
    if not m:
        sys.exit(f"check_levels: no MAP const in {rel}")
    return m.group(1).strip("\n").split("\n")


def parse_registry():
    src = read("scripts/level_registry.gd")
    preloads = dict(re.findall(r'const (\w+) := preload\("res://(scripts/[\w/]+\.gd)"\)', src))
    levels = {}
    for lid, body in re.findall(r'"(\w+)":\n\t\{(.*?)\n\t\},', src, re.S):
        const = re.search(r'"map": (\w+)', body).group(1)
        levels[lid] = {
            "rows": map_rows(preloads[const]),
            "ground": re.search(r'"ground": "res://([^"]+)"', body).group(1),
            "entries": {
                e: (int(x), int(y))
                for e, x, y in re.findall(r'"(\w+)": Vector2i\((\d+), (\d+)\)', body)
            },
            "transitions": [
                (int(x), int(y), int(w), int(h), to, en)
                for x, y, w, h, to, en in re.findall(
                    r'Rect2i\((\d+), (\d+), (\d+), (\d+)\), "to": "(\w+)", "entry": "(\w+)"',
                    body,
                )
            ],
        }
    if not levels:
        sys.exit("check_levels: no levels parsed from level_registry.gd")
    return levels


def check_graph(levels):
    problems = []
    for lid, lv in levels.items():
        rows = lv["rows"]
        height, width = len(rows), len(rows[0])
        if any(len(r) != width for r in rows):
            problems.append(f"{lid}: map is not rectangular")
        if not os.path.exists(os.path.join(REPO, lv["ground"])):
            problems.append(f"{lid}: ground image missing ({lv['ground']})")
        for x, y, w, h, to, entry in lv["transitions"]:
            if y + h > height or x + w > width:
                problems.append(f"{lid}: trigger {(x, y, w, h)} out of bounds")
            if to not in levels:
                problems.append(f"{lid}: transition targets unknown level '{to}'")
                continue
            target = levels[to]
            trows = target["rows"]
            if entry in target["entries"]:
                ax, ay = target["entries"][entry]
            else:
                spawns = [
                    (cx, cy)
                    for cy, r in enumerate(trows)
                    for cx, c in enumerate(r)
                    if c == "S"
                ]
                if not spawns:
                    problems.append(f"{lid}->{to}: entry '{entry}' missing and no S fallback")
                    continue
                if target["entries"]:
                    problems.append(
                        f"{lid}->{to}: entry '{entry}' not named in target "
                        f"(silently falls back to S — likely a typo)"
                    )
                ax, ay = spawns[0]
            if not (0 <= ay < len(trows) and 0 <= ax < len(trows[0])):
                problems.append(f"{lid}->{to}: arrival ({ax},{ay}) out of bounds")
                continue
            if trows[ay][ax] in BLOCKED:
                problems.append(
                    f"{lid}->{to}: arrival ({ax},{ay}) lands on non-walkable "
                    f"'{trows[ay][ax]}'"
                )
            for tx, ty, tw, th, tto, _ten in target["transitions"]:
                if tto == lid and tx <= ax < tx + tw and ty <= ay < ty + th:
                    problems.append(
                        f"{lid}->{to}: arrival ({ax},{ay}) sits inside the return "
                        f"trigger back to {tto}"
                    )
    return problems


def check_interiors(levels):
    problems = []
    for lid, lv in levels.items():
        rows = lv["rows"]
        if "X" not in "".join(rows):
            continue  # outdoor map
        spawns = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "S"]
        mats = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == ">"]
        if len(spawns) != 1 or len(mats) != 1:
            problems.append(f"{lid}: expected 1 spawn + 1 exit mat, got {len(spawns)}/{len(mats)}")
            continue
        (sx, sy), (mx, my) = spawns[0], mats[0]
        if abs(sx - mx) + abs(sy - my) != 1:
            problems.append(f"{lid}: spawn {spawns[0]} not adjacent to exit mat {mats[0]}")
    return problems


def check_dialogue(levels):
    problems = []
    ids = set(re.findall(r'^\t"(\w+)":', read("scripts/dialogue_data.gd"), re.M))
    all_villagers = set()
    all_notes = set()
    all_persons = set()
    for lid, lv in levels.items():
        rows = lv["rows"]
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c == "N":
                    vid = f"villager_{x}_{y}"
                    all_villagers.add(vid)
                    if vid not in ids:
                        problems.append(f"{lid}: villager at ({x},{y}) has no dialogue entry '{vid}'")
                elif c == "!":
                    # Interior examine-trigger — main.gd derives this exact id.
                    nid = f"note_{lid}_{x}_{y}"
                    all_notes.add(nid)
                    if nid not in ids:
                        problems.append(f"{lid}: note at ({x},{y}) has no dialogue entry '{nid}'")
                elif c == "P":
                    # Interior resident — main.gd derives this exact id.
                    pid = f"person_{lid}_{x}_{y}"
                    all_persons.add(pid)
                    if pid not in ids:
                        problems.append(f"{lid}: person at ({x},{y}) has no dialogue entry '{pid}'")
        joined = "".join(rows)
        if "$" in joined and "ariana" not in ids:
            problems.append(f"{lid}: Ariana ('$') present but no 'ariana' dialogue entry")
        if "L" in joined and "library_door" not in ids:
            problems.append(f"{lid}: library ('L') present but no 'library_door' entry")
    for vid in sorted(i for i in ids if i.startswith("villager_")):
        if vid not in all_villagers:
            problems.append(f"dialogue_data: '{vid}' matches no villager cell on any map")
    for nid in sorted(i for i in ids if i.startswith("note_")):
        if nid not in all_notes:
            problems.append(f"dialogue_data: '{nid}' matches no note cell on any map")
    for pid in sorted(i for i in ids if i.startswith("person_")):
        if pid not in all_persons:
            problems.append(f"dialogue_data: '{pid}' matches no person cell on any map")
    return problems


def main():
    levels = parse_registry()
    problems = check_graph(levels) + check_interiors(levels) + check_dialogue(levels)
    n_trans = sum(len(lv["transitions"]) for lv in levels.values())
    print(f"levels: checked {len(levels)} levels, {n_trans} transitions")
    if problems:
        print("FAIL:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print(
        "OK: transitions resolve, arrivals walkable, no bounce placements, "
        "interiors doored, dialogue covered."
    )


if __name__ == "__main__":
    main()
