#!/usr/bin/env python3
"""Brief-driven level generator — the gallery front door.

  python tools/worldgen/generate.py --brief briefs/cove.json --seeds 5 \
      --out artifacts/worldgen/cove

Per seed: build passes -> HARD-rule gates (check_map_rules + preview_map's
2-wide validation, the same gates CI runs) -> composite render -> row in the
contact sheet. Candidates that fail any gate are discarded and say so — a
gallery only ever shows rule-clean maps. Same brief + seed = byte-identical
map (no wall-clock, no unseeded randomness).
"""

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from worldgen.core import Grid  # noqa: E402
from worldgen import passes  # noqa: E402


def build(brief, seed):
    rng = random.Random(seed)
    grid = Grid(brief["width"], brief["height"])
    pois = brief.get("pois", {})
    passes.water_pass(grid, rng, brief.get("water", []))
    passes.border_pass(grid, rng, brief.get("border", {}))
    passes.path_pass(grid, rng, brief.get("paths", []), pois)
    passes.poi_pass(grid, rng, pois)
    passes.pen_pass(grid, rng, brief.get("pens", []))
    passes.scatter_pass(grid, rng, brief.get("scatter", []))
    return grid


def gate(txt_path):
    """Run the exact CI gates against a candidate. Returns list of problems."""
    problems = []
    r = subprocess.run(
        [sys.executable, str(REPO / "tools" / "check_map_rules.py"), str(txt_path)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        problems += [l for l in r.stdout.splitlines() if l.strip().startswith("-")]
    return problems


def render(txt_path, png_path, scale=1):
    r = subprocess.run(
        [
            sys.executable,
            str(REPO / "tools" / "preview_map.py"),
            "--map",
            str(txt_path),
            "--out",
            str(png_path),
            "--scale",
            str(scale),
        ],
        capture_output=True,
        text=True,
    )
    ok = r.returncode == 0  # preview exits 1 on 2-wide validation problems
    return ok, r.stdout.strip().splitlines()[-3:]


def contact_sheet(rows, out_path):
    from PIL import Image, ImageDraw

    imgs = [(label, Image.open(p)) for label, p in rows]
    w = max(i.width for _, i in imgs)
    scale = min(1.0, 1600 / w)
    imgs = [
        (label, i.resize((int(i.width * scale), int(i.height * scale)))) for label, i in imgs
    ]
    total_h = sum(i.height + 26 for _, i in imgs) + 10
    sheet = Image.new("RGB", (int(w * scale) + 20, total_h), (24, 26, 30))
    d = ImageDraw.Draw(sheet)
    y = 6
    for label, img in imgs:
        d.text((10, y), label, fill=(255, 230, 150))
        sheet.paste(img, (10, y + 18))
        y += img.height + 26
    sheet.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--seed-base", type=int, default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=int, default=1)
    args = ap.parse_args()

    brief = json.loads(Path(args.brief).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = args.seed_base if args.seed_base is not None else brief.get("seed", 1)

    survivors = []
    for i in range(args.seeds):
        seed = base + i
        name = f"{brief['name']}-s{seed}"
        grid = build(brief, seed)
        txt = out / f"{name}.txt"
        txt.write_text(grid.text())
        problems = gate(txt)
        if problems:
            print(f"[{name}] DISCARDED — {len(problems)} rule problem(s):")
            for p in problems[:6]:
                print("   " + p)
            continue
        png = out / f"{name}.png"
        ok, tail = render(txt, png, args.scale)
        if not ok:
            print(f"[{name}] DISCARDED — render/validation failed: {tail}")
            continue
        print(f"[{name}] PASS — all gates green")
        survivors.append((name, png))

    if survivors:
        sheet = out / f"{brief['name']}-gallery.png"
        contact_sheet(survivors, sheet)
        print(f"\ngallery: {sheet}  ({len(survivors)}/{args.seeds} candidates survived)")
    else:
        print("\nNO candidate survived the gates — tune the brief.")
        sys.exit(1)


if __name__ == "__main__":
    main()
