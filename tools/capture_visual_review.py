#!/usr/bin/env python3
"""Capture a repeatable visual-review snapshot of the current world map.

This wraps preview_map.py so each snapshot contains one full-map image and
three readable zone crops. The output is intentionally local/generated; GitHub
Actions uploads the same folder as a per-push artifact for team review.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PREVIEW = ROOT / "tools" / "preview_map.py"

# The live Valley 1 map is 192 x 48 tiles. These crops overlap neither content
# nor each other, making it easy to compare a changed zone to an earlier run.
CAPTURES = (
    ("overview", None),
    ("west", "0,0,64,48"),
    ("middle", "64,0,128,48"),
    ("east", "128,0,192,48"),
)


def git_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "working-tree"


def capture(output_dir: Path, scale: int) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    images: list[dict[str, str]] = []

    for name, crop in CAPTURES:
        destination = output_dir / f"{name}.png"
        command = [sys.executable, str(PREVIEW), "--out", str(destination), "--scale", str(scale)]
        if crop:
            command.extend(["--crop", crop])
        subprocess.run(command, cwd=ROOT, check=True)
        images.append({"name": name, "file": destination.name, "crop": crop or "full map"})

    return images


def write_readme(output_dir: Path, revision: str, created_at: str, images: list[dict[str, str]]) -> None:
    lines = [
        "# Visual review snapshot",
        "",
        f"- Revision: `{revision}`",
        f"- Captured: {created_at}",
        "- Source: `scripts/island_map.gd` rendered through `tools/preview_map.py`",
        "",
        "## Review order",
        "",
        "1. Read `overview.png` for route clarity, pacing, and repeated visual motifs.",
        "2. Review west, middle, and east at native pixel scale for awkward overlaps, isolated props, and empty space.",
        "3. Cross-check any traversal concern in the running game; this renderer validates layout, not live collisions or animation.",
        "",
        "## Questions for each zone",
        "",
        "- Does every path, landmark, field, and prop have a clear purpose?",
        "- Do repeated sprites read as a deliberate group rather than copied stamps?",
        "- Are tall sprites layered naturally, with no accidental roof/foreground overlaps?",
        "- Does the scene feel authored, varied, and navigable rather than mechanically generated?",
        "",
        "## Files",
        "",
    ]
    lines.extend(f"- `{item['file']}` — {item['crop']}" for item in images)
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture a map visual-review snapshot.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Base directory for snapshots (default: artifacts/visual-review).",
    )
    parser.add_argument("--scale", type=int, default=2, help="Pixel scale for every image (default: 2).")
    parser.add_argument(
        "--label",
        help="Optional stable label for the snapshot directory instead of a timestamp.",
    )
    args = parser.parse_args()

    if args.scale < 1:
        parser.error("--scale must be at least 1")

    revision = git_revision()
    created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    label = args.label or f"{revision}-{timestamp}"
    base = args.output_dir or ROOT / "artifacts" / "visual-review"
    output_dir = (base / label).resolve()

    images = capture(output_dir, args.scale)
    manifest = {"revision": revision, "captured_at": created_at, "images": images}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_readme(output_dir, revision, created_at, images)
    print(f"Visual review snapshot: {output_dir}")


if __name__ == "__main__":
    main()
