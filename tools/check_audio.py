#!/usr/bin/env python3
"""Audio self-check (companion to check_assets.py, same fail-loud discipline).

Guards three invariants:
  (a) every id in Audio.SFX / Audio.TRACKS (scripts/audio.gd) points at a file
      that exists on disk — a renamed/deleted sample fails CI, not a silent
      no-op at runtime;
  (b) every audio FILE under assets/audio/ is either generated (sfx/, covered
      by the blanket LICENSES.md section) or, for music/, individually
      mentioned in assets/audio/LICENSES.md — no orphan-licensed audio ever
      lands in the repo;
  (c) the generator's output set matches Audio.SFX's id set exactly, so
      gen_audio.py and audio.gd can't drift apart.

Run before every commit:  python tools/check_audio.py
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(REPO, "assets", "audio")
AUDIO_EXTS = (".wav", ".ogg", ".mp3")


def read(rel):
    return open(os.path.join(REPO, rel), encoding="utf-8").read()


def dict_entries(src, const_name):
    block = re.search(r"const %s := \{(.*?)\n\}" % const_name, src, re.S)
    if block is None:
        # An empty one-liner (`const TRACKS := {}`) has no block body.
        if re.search(r"const %s := \{\}" % const_name, src):
            return {}
        raise SystemExit(f"check_audio FAIL: const {const_name} not found in audio.gd")
    return dict(re.findall(r'"([\w]+)":\s*"res://([^"]+)"', block.group(1)))


def main():
    problems = []
    src = read("scripts/audio.gd")
    sfx = dict_entries(src, "SFX")
    tracks = dict_entries(src, "TRACKS")

    # (a) every registered id resolves to a real file
    for id_, rel in list(sfx.items()) + list(tracks.items()):
        if not os.path.exists(os.path.join(REPO, rel)):
            problems.append(f"audio id '{id_}' points at missing file {rel}")

    # (b) licensing coverage for on-disk audio files
    licenses = read("assets/audio/LICENSES.md") if os.path.exists(
        os.path.join(AUDIO_DIR, "LICENSES.md")) else ""
    for dirpath, _dirs, files in os.walk(AUDIO_DIR):
        for f in files:
            if not f.endswith(AUDIO_EXTS):
                continue
            rel = os.path.relpath(os.path.join(dirpath, f), AUDIO_DIR)
            rel = rel.replace("\\", "/")
            if rel.startswith("sfx/"):
                continue  # generated set: blanket-covered by LICENSES.md
            if f not in licenses:
                problems.append(
                    f"assets/audio/{rel} has no entry in LICENSES.md "
                    "(license + attribution required in the same commit)")

    # (c) generator ids == SFX ids
    gen = read("tools/gen_audio.py")
    gen_block = re.search(r"SOUNDS = \{(.*?)\n\}", gen, re.S).group(1)
    gen_ids = set(re.findall(r'"([\w]+)":', gen_block))
    sfx_ids = set(sfx)
    for missing in sorted(sfx_ids - gen_ids):
        problems.append(f"audio.gd SFX id '{missing}' has no gen_audio.py recipe")
    for orphan in sorted(gen_ids - sfx_ids):
        problems.append(f"gen_audio.py generates '{orphan}' but audio.gd never registers it")

    if problems:
        print("check_audio FAIL:\n  - " + "\n  - ".join(problems))
        sys.exit(1)
    print(f"audio: {len(sfx)} sfx + {len(tracks)} tracks registered, "
          "all files present, licensing covered, generator in sync.")


if __name__ == "__main__":
    main()
