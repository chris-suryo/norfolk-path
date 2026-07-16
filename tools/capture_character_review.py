#!/usr/bin/env python3
"""Render representative P1/P2 modular-character frames for visual review."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "game" / "creator"
FRAME = 64
SCALE = 2
STATES = (("IDLE", 0, 2), ("WALK", 4, 3), ("SWORD", 9, 2), ("ROLL", 18, 4), ("DOWN", 53, 5))
PROFILES = (
    ("P1", 1, "Black", "Farmer_Shirt", "Green", "Brown", "Brown", False),
    ("P2", 2, "Brown", "Lumberjack_Shirt", "Blue", "Blue", "Brown", False),
)


def path_for(profile: tuple[str, int, str, str, str, str, str, bool]) -> list[Path]:
    _name, hair_style, hair_color, shirt_style, shirt_color, pants_color, shoes_color, has_hat = profile
    shirt_name = f"Shirt_1_{shirt_color}.png" if shirt_style == "Classic" else f"{shirt_style}_1_{shirt_color}.png"
    paths = [
        ASSETS / "body" / "Player_Base_animations.png",
        ASSETS / "pants" / f"Pants_1_{pants_color}.png",
        ASSETS / "shoes" / f"Shoes_1_{shoes_color}.png",
        ASSETS / "shirt" / shirt_name,
        ASSETS / "hair" / f"Hair_{hair_style}_{hair_color}.png",
    ]
    if has_hat:
        paths.append(ASSETS / "accessory" / "Farmer_Hat_1.png")
    return paths


def compose(profile: tuple[str, int, str, str, str, str, str, bool], row: int, column: int) -> Image.Image:
    image = Image.new("RGBA", (FRAME, FRAME))
    box = (column * FRAME, row * FRAME, (column + 1) * FRAME, (row + 1) * FRAME)
    for path in path_for(profile):
        with Image.open(path) as sheet:
            image.alpha_composite(sheet.convert("RGBA").crop(box))
    sword_row = {6: 0, 9: 1, 12: 2}.get(row)
    if sword_row is not None:
        sword_box = (column * FRAME, sword_row * FRAME, (column + 1) * FRAME, (sword_row + 1) * FRAME)
        with Image.open(ASSETS / "tool" / "Iron_Sword.png") as sword_sheet:
            image.alpha_composite(sword_sheet.convert("RGBA").crop(sword_box))
    return image


def capture(destination: Path) -> None:
    width = len(STATES) * 128
    height = 48 + len(PROFILES) * 160
    image = Image.new("RGBA", (width, height), (20, 27, 30, 255))
    draw = ImageDraw.Draw(image)
    for index, (name, _row, _column) in enumerate(STATES):
        draw.text((index * 128 + 34, 14), name, fill=(255, 223, 112, 255))
    for profile_index, profile in enumerate(PROFILES):
        y = 48 + profile_index * 160
        draw.text((12, y + 68), profile[0], fill=(238, 223, 190, 255))
        for state_index, (_name, row, column) in enumerate(STATES):
            frame = compose(profile, row, column).resize((FRAME * SCALE, FRAME * SCALE), Image.Resampling.NEAREST)
            image.alpha_composite(frame, (state_index * 128, y))
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture modular character review frames.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    capture(args.output)
    print(f"Character review snapshot: {args.output}")


if __name__ == "__main__":
    main()
