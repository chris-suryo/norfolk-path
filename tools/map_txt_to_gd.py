#!/usr/bin/env python3
"""Wrap a worldgen .txt map into a Godot .gd script exposing `const MAP`.

Level maps must live in a .gd const, not a .txt: the Web export packs only Godot
resources, so a plain text file silently vanishes from browser builds (see
scripts/island_map.gd's note). The worldgen pipeline emits .txt candidates; this
turns the chosen one into the packed-in map script the LevelRegistry preloads.

Deterministic and re-runnable — regenerate the .txt from its brief+seed, then
re-run this; the .gd is a pure function of the .txt.

Usage:
    python tools/map_txt_to_gd.py <input.txt> <output.gd> [--source "<regen cmd>"]
"""

import argparse
import sys
from pathlib import Path


def build(txt: str, source: str) -> str:
    grid = txt.strip("\n")
    header = [
        "extends RefCounted",
        "",
        "## GENERATED level map — do not hand-edit; regenerate from its brief+seed.",
    ]
    if source:
        header.append("## Source: %s" % source)
    header += [
        "## Packed into the Web export as a resource (a .txt would vanish from the",
        "## build). Consumed via LevelRegistry (which preloads this and reads MAP).",
        "",
        'const MAP := """',
        grid,
        '"""',
        "",
    ]
    return "\n".join(header)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="the worldgen .txt map")
    ap.add_argument("output", help="the .gd script to write")
    ap.add_argument("--source", default="", help="regen command, recorded in the header")
    args = ap.parse_args()

    txt = Path(args.input).read_text(encoding="utf-8")
    Path(args.output).write_text(build(txt, args.source), encoding="utf-8")
    print("wrote %s (%d rows)" % (args.output, len(txt.strip(chr(10)).split(chr(10)))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
