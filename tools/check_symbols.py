#!/usr/bin/env python3
"""Symbol-coverage self-check (the sandbox-runnable twin of main.gd's
_check_symbol_coverage assert).

Fails LOUD if any unique character in scripts/island_map.gd's MAP is not handled
by the prop table (scripts/prop_table.gd PROPS) OR the terrain/fence symbol sets
(scripts/main.gd TERRAIN_SYMS / FENCE_SYMS) — i.e. anything that would silently
render as blank grass in-engine (the 47-symbol gap this slice exists to close).

Run before every commit:  python tools/check_symbols.py
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel):
    return open(os.path.join(REPO, rel), encoding="utf-8").read()


def map_symbols():
    src = read("scripts/island_map.gd")
    m = re.search(r'const MAP :=\s*"""\n(.*?)"""', src, re.S)
    if not m:
        sys.exit("check_symbols: could not find MAP const in island_map.gd")
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
    used = map_symbols()
    handled = prop_keys() | const_array("TERRAIN_SYMS") | const_array("FENCE_SYMS")
    missing = sorted(used - handled)
    print(f"map uses {len(used)} unique symbols; {len(handled)} are handled.")
    if missing:
        print("FAIL: unhandled symbols (would render as blank grass): " + "".join(missing))
        sys.exit(1)
    print("OK: every map symbol is covered by the prop table / terrain / fence sets.")


if __name__ == "__main__":
    main()
