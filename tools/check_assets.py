#!/usr/bin/env python3
"""Asset-reference self-check (a companion to check_symbols.py, same fail-loud
discipline).

Every res:// asset a scene/script/resource references must:
  (a) exist on disk, and
  (b) NOT live under a .gdignore'd directory — Godot skips those at import, so
      the reference would resolve to nothing at runtime (a blank sprite / failed
      load). This is the guard for trimming the web build: gdignoring an unused
      pack dir is only safe if nothing we ship references into it.

Also checks that every symbol keyed in main.gd's ANIMAL_ANIM table is a real
prop-table entry (so the ambient-animal wiring can't reference a symbol that
isn't actually placed/handled).

Run before every commit:  python tools/check_assets.py
"""
import os
import re
import struct
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_RE = re.compile(r"res://(assets/[^\"')\s]+\.(?:png|ttf|otf|wav|ogg|tres))")


def read(rel):
    return open(os.path.join(REPO, rel), encoding="utf-8").read()


def gdignored_prefixes():
    prefixes = []
    for dirpath, _dirs, files in os.walk(os.path.join(REPO, "assets")):
        if ".gdignore" in files:
            prefixes.append(os.path.relpath(dirpath, REPO).replace("\\", "/"))
    return prefixes


def asset_refs():
    refs = set()
    sources = ["project.godot"]
    for sub in ("scenes", "scripts", "assets"):
        for dirpath, _dirs, files in os.walk(os.path.join(REPO, sub)):
            for f in files:
                if f.endswith((".gd", ".tscn", ".tres", ".godot")):
                    sources.append(os.path.relpath(os.path.join(dirpath, f), REPO))
    for src in sources:
        path = os.path.join(REPO, src)
        if not os.path.exists(path):
            continue
        for m in ASSET_RE.findall(read(src)):
            refs.add((m, src.replace("\\", "/")))
    return refs


def animal_symbols():
    src = read("scripts/main.gd")
    block = re.search(r"const ANIMAL_ANIM :=\s*\{(.*?)\n\}", src, re.S)
    return set(re.findall(r'^\t"(.)":', block.group(1), re.M)) if block else set()


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def animal_frame_problems():
    """Every ANIMAL_ANIM idle/walk index must fit its sheet (hframes*vframes).

    Bug class caught by the playtest bot's console log: the chicken declared a
    6-frame walk on a 4-frame sheet — silent per-frame set_frame errors and a
    stuck animation that no human playtest noticed.
    """
    src = read("scripts/main.gd")
    block = re.search(r"const ANIMAL_ANIM :=\s*\{(.*?)\n\}", src, re.S).group(1)
    pt = read("scripts/prop_table.gd")
    sheets = dict(re.findall(r'"(\w+)":\s*\n?\s*"res://([^"]+)"', pt))
    props = dict(re.findall(r'^\t"(.)": \["(\w+)"', pt, re.M))
    problems = []
    for m in re.finditer(r'"(.)":\s*\n?\s*\{([^}]*)\}', block, re.S):
        sym, body = m.group(1), m.group(2)

        def field(key, default=None):
            f = re.search(r'"%s":\s*(\d+)' % key, body)
            return int(f.group(1)) if f else default

        sheet = sheets.get(props.get(sym, ""))
        if not sheet:
            continue  # missing prop entry is reported elsewhere
        size = png_size(os.path.join(REPO, sheet))
        if not size:
            continue
        fs = field("frame_size", 32)
        hframes, vframes = size[0] // fs, size[1] // fs
        total = hframes * vframes
        top = field("idle", 0) * hframes + field("idle_n", 1) - 1
        if field("walk") is not None:
            top = max(top, field("walk") * hframes + field("walk_n", 6) - 1)
        if top >= total:
            problems.append(
                f"ANIMAL_ANIM '{sym}': max frame index {top} exceeds sheet "
                f"{sheet} ({hframes}x{vframes} = {total} frames)"
            )
    return problems


def prop_keys():
    block = re.search(r"const PROPS :=\s*\{(.*?)\n\}", read("scripts/prop_table.gd"), re.S)
    keys = re.findall(r'^\t"((?:\\.|[^"])+)":', block.group(1), re.M)
    return set(k.replace('\\"', '"').replace("\\\\", "\\") for k in keys)


def main():
    ignored = gdignored_prefixes()
    problems = []
    refs = asset_refs()
    for path, src in sorted(refs):
        if not os.path.exists(os.path.join(REPO, path)):
            problems.append(f"MISSING on disk: {path}  (referenced by {src})")
            continue
        for ig in ignored:
            if path == ig or path.startswith(ig + "/"):
                problems.append(f"GDIGNORED but referenced: {path}  (under {ig}/, from {src})")
                break
    props = prop_keys()
    for sym in sorted(animal_symbols() - props):
        problems.append(f"ANIMAL_ANIM key '{sym}' has no prop-table entry")
    problems += animal_frame_problems()

    print(f"checked {len(refs)} asset references; {len(ignored)} gdignored dirs.")
    if problems:
        print("FAIL:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("OK: every referenced asset exists, is exportable, and ANIMAL_ANIM is consistent.")


if __name__ == "__main__":
    main()
