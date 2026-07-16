#!/usr/bin/env python3
"""Symbol-coverage self-check (the sandbox-runnable twin of main.gd's
_check_symbol_coverage assert).

Fails LOUD if any unique character in a level's MAP is not handled by the prop
table (scripts/prop_table.gd PROPS) OR the terrain/fence symbol sets
(scripts/main.gd TERRAIN_SYMS / FENCE_SYMS) — i.e. anything that would silently
render as blank grass in-engine.

Covers EVERY level map registered in scripts/level_registry.gd (its preload
paths), so a second level can never ship an unhandled symbol.

Run before every commit:  python tools/check_symbols.py
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel):
    return open(os.path.join(REPO, rel), encoding="utf-8").read()


def level_map_scripts():
    """The map .gd scripts registered in LevelRegistry (its preload paths), so
    this check stays in sync with the levels the game can actually load."""
    src = read("scripts/level_registry.gd")
    paths = re.findall(r'preload\("res://(scripts/[\w/]+\.gd)"\)', src)
    if not paths:
        sys.exit("check_symbols: no level map preloads found in level_registry.gd")
    return paths


def map_symbols(rel):
    src = read(rel)
    m = re.search(r'const MAP :=\s*"""\n(.*?)"""', src, re.S)
    if not m:
        sys.exit(f"check_symbols: could not find MAP const in {rel}")
    body = m.group(1).strip("\n")
    return set(ch for row in body.split("\n") for ch in row)


def _unescape(tok):
    return tok.replace('\\"', '"').replace("\\\\", "\\")


def prop_keys():
    src = read("scripts/prop_table.gd")
    block = re.search(r"const PROPS :=\s*\{(.*?)\n\}", src, re.S)
    if not block:
        sys.exit("check_symbols: could not find PROPS in prop_table.gd")
    keys = re.findall(r'^\t"((?:\\.|[^"])+)":', block.group(1), re.M)
    return set(_unescape(k) for k in keys)


def const_array(name):
    src = read("scripts/main.gd")
    m = re.search(name + r"\s*:=\s*\[(.*?)\]", src, re.S)
    if not m:
        sys.exit(f"check_symbols: could not find {name} in main.gd")
    return set(_unescape(t) for t in re.findall(r'"((?:\\.|[^"])+)"', m.group(1)))


def main():
    handled = prop_keys() | const_array("TERRAIN_SYMS") | const_array("FENCE_SYMS")
    scripts = level_map_scripts()
    failed = False
    for rel in scripts:
        used = map_symbols(rel)
        missing = sorted(used - handled)
        status = "MISSING " + "".join(missing) if missing else "all handled"
        print(f"{rel}: {len(used)} unique symbols — {status}")
        if missing:
            failed = True
    if failed:
        print("FAIL: unhandled symbols would render as blank grass.")
        sys.exit(1)
    print(f"OK: every symbol across {len(scripts)} level map(s) is covered.")


if __name__ == "__main__":
    main()
