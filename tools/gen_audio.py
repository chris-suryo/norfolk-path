#!/usr/bin/env python3
"""Deterministic retro SFX generator — the audio sibling of bake_interior.py.

Generates every sound effect the Audio autoload references, as 16-bit mono
WAVs under assets/audio/sfx/. Pure stdlib (wave/struct/math/random), fully
seeded: the same script always emits byte-identical files, so a re-run in CI
or a fresh clone proves nothing drifted (same discipline as the interior
baker).

Why generated, not downloaded: curated CC0 packs (kenney.nl, OpenGameArt)
are unreachable from the build sandbox's egress, and generated chiptune-style
SFX carry NO third-party license at all — they are project-original output of
this script. Each sound is a tiny recipe below; retuning a sound is editing
its recipe and re-running:

    python tools/gen_audio.py

The music slots in scripts/audio.gd are deliberately NOT generated — looping
music is a taste call; drop .ogg files in assets/audio/music/ and register
them in Audio.TRACKS.
"""
import math
import os
import random
import struct
import wave

RATE = 22050
PEAK = 0.55  # headroom: well under full scale so stacked SFX don't clip
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "audio", "sfx")


def env(i, n, attack=0.01, release=0.25):
    """Linear attack, exponential-ish release — clickless start and tail."""
    t = i / n
    a = min(1.0, t / attack) if attack > 0 else 1.0
    r = (1.0 - t) ** (1.0 / release) if release > 0 else 1.0
    return a * r


def sine(t, freq):
    return math.sin(2 * math.pi * freq * t)


def square(t, freq, duty=0.5):
    return 1.0 if (t * freq) % 1.0 < duty else -1.0


def triangle(t, freq):
    p = (t * freq) % 1.0
    return 4 * p - 1 if p < 0.5 else 3 - 4 * p


def render(duration, fn, release=0.25, attack=0.01):
    n = int(duration * RATE)
    return [fn(i / RATE, i, n) * env(i, n, attack, release) for i in range(n)]


def sweep(t, f0, f1, duration):
    """Phase-correct linear frequency sweep."""
    k = (f1 - f0) / duration
    return math.sin(2 * math.pi * (f0 * t + 0.5 * k * t * t))


def noise_fn(seed):
    rng = random.Random(seed)
    state = {"v": 0.0}

    def fn(_t, _i, _n):
        # Soft brown-ish noise: integrate white noise, leak toward zero.
        state["v"] = state["v"] * 0.97 + rng.uniform(-1, 1) * 0.3
        return state["v"]

    return fn


def notes(seq, wave_fn=square, gap=0.0):
    """seq = [(freq, dur), ...] -> one list of samples, per-note envelopes."""
    out = []
    for freq, dur in seq:
        out += render(dur, lambda t, i, n, f=freq: wave_fn(t, f), release=0.3)
        out += [0.0] * int(gap * RATE)
    return out


def sfx_sword_swing():
    # A fast whoosh: noise through a rising-then-falling amplitude arc.
    base = noise_fn("sword")
    return render(0.18, lambda t, i, n: base(t, i, n) * math.sin(math.pi * (i / n)),
                  release=0.5, attack=0.15)


def sfx_hit_connect():
    # A low thud with a tiny click transient.
    return render(0.15, lambda t, i, n: 0.9 * sweep(t, 160, 60, 0.15)
                  + (0.4 if i < 40 else 0.0), release=0.18)


def sfx_bow_shoot():
    # String pluck: sharp triangle that drops an octave fast.
    return render(0.16, lambda t, i, n: triangle(t, 440 * (2 ** (-t * 6))),
                  release=0.15)


def sfx_player_hurt():
    # Two descending square blips.
    return notes([(392, 0.07), (262, 0.10)], gap=0.015)


def sfx_enemy_die():
    # Downward sweep into a noise poof.
    body = render(0.22, lambda t, i, n: sweep(t, 330, 70, 0.22), release=0.3)
    poof = noise_fn("die")
    return body + render(0.12, lambda t, i, n: 0.5 * poof(t, i, n), release=0.4)


def sfx_chest_open():
    # Rising major arpeggio — the classic "got something" chime.
    return notes([(523, 0.09), (659, 0.09), (784, 0.16)], wave_fn=square, gap=0.01)


def sfx_door():
    # A low slide up: wooden door swinging.
    return render(0.20, lambda t, i, n: 0.8 * sweep(t, 90, 180, 0.20), release=0.3)


def sfx_ui_select():
    return notes([(660, 0.06)])


def sfx_dialogue_blip():
    return notes([(880, 0.035)], wave_fn=triangle)


def sfx_checkpoint():
    # Two-note affirming chime.
    return notes([(659, 0.10), (880, 0.18)], wave_fn=sine, gap=0.02)


def sfx_boss_sting():
    # A low minor dyad swelling in — trouble.
    return render(0.7, lambda t, i, n: 0.5 * (sine(t, 110) + sine(t, 131)),
                  attack=0.5, release=0.25)


def sfx_win_fanfare():
    # Four-note major fanfare with a held top.
    return notes([(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.42)],
                 wave_fn=square, gap=0.015)


SOUNDS = {
    "sword_swing": sfx_sword_swing,
    "hit_connect": sfx_hit_connect,
    "bow_shoot": sfx_bow_shoot,
    "player_hurt": sfx_player_hurt,
    "enemy_die": sfx_enemy_die,
    "chest_open": sfx_chest_open,
    "door": sfx_door,
    "ui_select": sfx_ui_select,
    "dialogue_blip": sfx_dialogue_blip,
    "checkpoint": sfx_checkpoint,
    "boss_sting": sfx_boss_sting,
    "win_fanfare": sfx_win_fanfare,
}


def write_wav(name, samples):
    peak = max(1e-9, max(abs(s) for s in samples))
    scale = PEAK / peak * 32767
    path = os.path.join(OUT, name + ".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(
            struct.pack("<h", int(max(-32767, min(32767, s * scale))))
            for s in samples))
    return path, len(samples) / RATE


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in sorted(SOUNDS.items()):
        path, secs = write_wav(name, fn())
        print(f"wrote {os.path.relpath(path)}  ({secs:.2f}s)")


if __name__ == "__main__":
    main()
