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

    print(f"checked {len(refs)} asset references; {len(ignored)} gdignored dirs.")
    if problems:
        print("FAIL:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("OK: every referenced asset exists, is exportable, and ANIMAL_ANIM is consistent.")


if __name__ == "__main__":
    main()
