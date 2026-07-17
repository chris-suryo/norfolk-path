#!/usr/bin/env python3
"""Verify the curated modular-character catalog before it reaches the web build."""

from __future__ import annotations

import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CREATOR = ROOT / "assets" / "game" / "creator"
SIZE = (576, 3584)
# The weapon overlays have their own sheet geometries (64px frames):
# sword = 4x9 attack frames, bow = 6x3 draw/release frames.
TOOL_SIZES = {
    Path("tool/Iron_Sword.png"): (256, 576),
    Path("tool/Wooden_Bow.png"): (384, 192),
}

HAIR_COLORS = ("Black", "Blonde", "Brown", "Ginger", "Grey")
SHIRT_COLORS = {
    "Farmer_Shirt": ("Black", "Blue", "Green", "Orange", "Pink", "Purple", "Red", "White_and_Brown"),
    "Lumberjack_Shirt": ("Black", "Blue", "Brown", "Green", "Orange", "Pink", "Purple", "Red", "White"),
    "Classic": ("Black", "Blue", "Brown", "Green", "Orange", "Pink", "Purple", "Red"),
}
PANTS_COLORS = ("Black", "Blue", "Brown", "Green", "Orange", "Pink", "Purple", "Red")
SHOES_COLORS = ("Black", "Blue", "Brown", "Green", "Orange", "Pink", "Purple", "Red", "White")


def expected_files() -> set[Path]:
    files = {
        Path("body/Player_Base_animations.png"),
        Path("accessory/Farmer_Hat_1.png"),
    }
    files.update(Path(f"hair/Hair_{style}_{color}.png") for style in range(1, 7) for color in HAIR_COLORS)
    for style, colors in SHIRT_COLORS.items():
        if style == "Classic":
            files.update(Path(f"shirt/Shirt_1_{color}.png") for color in colors)
        else:
            files.update(Path(f"shirt/{style}_1_{color}.png") for color in colors)
    files.update(Path(f"pants/Pants_1_{color}.png") for color in PANTS_COLORS)
    files.update(Path(f"shoes/Shoes_1_{color}.png") for color in SHOES_COLORS)
    files.update(TOOL_SIZES)
    return files


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as file:
        header = file.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("not a PNG with an IHDR header")
    return struct.unpack(">II", header[16:24])


def main() -> None:
    expected = expected_files()
    actual = {path.relative_to(CREATOR) for path in CREATOR.rglob("*.png")} if CREATOR.exists() else set()
    problems: list[str] = []
    for path in sorted(expected - actual):
        problems.append(f"MISSING: {path.as_posix()}")
    for path in sorted(actual - expected):
        problems.append(f"UNEXPECTED: {path.as_posix()}")
    for relative in sorted(expected & actual):
        path = CREATOR / relative
        try:
            size = png_size(path)
        except ValueError as error:
            problems.append(f"INVALID PNG: {relative.as_posix()} ({error})")
            continue
        expected_size = TOOL_SIZES.get(relative, SIZE)
        if size != expected_size:
            problems.append(
                f"WRONG SIZE: {relative.as_posix()} is {size[0]}x{size[1]}, expected {expected_size[0]}x{expected_size[1]}"
            )

    print(f"checked {len(actual)} character layers; expected {len(expected)} modular sheets incl. the weapon overlays.")
    if problems:
        print("FAIL:")
        print("\n".join(f"  - {problem}" for problem in problems))
        sys.exit(1)
    print("OK: curated character layers are complete, aligned, and ready for the creator.")


if __name__ == "__main__":
    main()
