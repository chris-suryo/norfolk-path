#!/usr/bin/env python3
"""Headless-browser playtest driver for the exported Web build (CI).

Drives the real exported game in Chromium via Playwright: boots it, proves the
canvas is actually rendering (fail-loud, never vacuous), walks title -> creator
-> in-game movement/sword/roll, and screenshots every checkpoint. Runs inside
GitHub Actions (see .github/workflows/playtest.yml) where the build is served
from localhost — no external network involved.

Design notes:
- Assertions are pixel-level only (non-blank frames + menu highlight movement).
  There is deliberately NO game-state introspection: the window.np_debug hook
  idea is a recorded deferral (docs/playtest-findings.md triage).
- Input goes through Playwright's keyboard API -> CDP -> trusted browser input.
  Godot's JS glue ignores untrusted synthetic JS events (round-1 finding), but
  CDP input is trusted — the first assertion (highlight moves) proves the whole
  input path before anything else runs.
- Timing-sensitive tests (roll i-frames, max-range spacing) stay human/local —
  a blind scripted driver can't time 0.16s windows honestly.

The run drives TWO browser contexts:
  1. Fresh context — the original title -> creator -> movement/sword/roll run,
     then the DOOR LOOP: walk into cottage A's doorway, screenshot the interior,
     walk out the exit mat, screenshot the valley again (level transitions +
     fade, live).
  2. Seeded context — localStorage carries a hand-written v3 save (checkpoint 3,
     boss defeated, Ginger hair). Continue must migrate it to v4 in place
     (asserted by re-reading localStorage), resume into a CLEARED east valley,
     and the bot then talks to the library-avenue villager (dialogue open /
     advance / close, asserted from the textbox pixels).

Usage: ci_driver.py [output_dir] [base_url]
"""

import io
import json
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/playtest")
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8060"

# Viewport is exactly 2x the 640x360 design resolution, so design coords map
# to screen coords by doubling. The menu-option region of the title panel
# (below the campfire + title, above the hint rows) in screen pixels:
VIEWPORT = {"width": 1280, "height": 720}
MENU_CROP = (380, 380, 900, 510)
# The dialogue textbox panel + prompt region (design x140-500, y282-350, x2):
DIALOG_CROP = (280, 540, 1000, 710)

BOOT_TIMEOUT_S = 120
MIN_COLORS_FRAME = 40  # a rendered scene has hundreds; a blank/splash has few
MIN_COLORS_MENU = 8  # panel + text + highlight inside the crop
MIN_CHANGED_PIXELS = 50  # highlight recolor changes far more than this
MIN_SCENE_DELTA = 15000  # thumbnail pixels that change on a level swap (of 57k)
MIN_DIALOG_DELTA = 5000  # crop pixels that change when the textbox opens

# A hand-written SAVE v3 blob (no "level" field — that's what v4 adds). The
# Ginger hair is the keeps-appearances marker: it must survive migration.
V3_SAVE = {
    "v": 3,
    "checkpoint": 3,
    "player_count": 1,
    "boss_defeated": True,
    "appearances": [
        {
            "hair_style": 3,
            "hair_color": "Ginger",
            "shirt_style": "Classic",
            "shirt_color": "Green",
            "pants_color": "Red",
            "shoes_color": "Brown",
            "hat": False,
        }
    ],
}


def img_of(png_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(png_bytes)).convert("RGB")


def distinct_colors(png_bytes: bytes, crop=None) -> int:
    img = img_of(png_bytes)
    if crop:
        img = img.crop(crop)
    img.thumbnail((320, 320))
    return len(set(img.getdata()))


def changed_pixels(a: bytes, b: bytes, crop) -> int:
    diff = ImageChops.difference(img_of(a).crop(crop), img_of(b).crop(crop))
    return sum(1 for px in diff.getdata() if max(px) > 10)


def frame_delta(a: bytes, b: bytes) -> int:
    """Changed pixels across the whole frame, on 320px thumbnails (fast) —
    a level swap changes most of the ~57k thumbnail pixels."""
    ia, ib = img_of(a), img_of(b)
    ia.thumbnail((320, 320))
    ib.thumbnail((320, 320))
    diff = ImageChops.difference(ia, ib)
    return sum(1 for px in diff.getdata() if max(px) > 10)


class Driver:
    def __init__(self, page):
        self.page = page
        self.failures = []

    def shot(self, name: str, min_colors: int = MIN_COLORS_FRAME) -> bytes:
        data = self.page.screenshot()
        (OUT / f"{name}.png").write_bytes(data)
        n = distinct_colors(data)
        status = "ok" if n >= min_colors else "BLANK?"
        print(f"[shot] {name}: {n} distinct colors ({status})")
        if n < min_colors:
            self.failures.append(f"{name}: only {n} distinct colors — frame looks blank")
        return data

    def press(self, key: str, settle: float = 0.45):
        self.page.keyboard.press(key)
        time.sleep(settle)

    def hold(self, key: str, seconds: float, settle: float = 0.3):
        self.page.keyboard.down(key)
        time.sleep(seconds)
        self.page.keyboard.up(key)
        time.sleep(settle)


def wait_for_title(page) -> None:
    """Poll until the title screen is actually rendered (not splash, not blank)."""
    page.wait_for_selector("canvas", timeout=60_000)
    deadline = time.time() + BOOT_TIMEOUT_S
    while time.time() < deadline:
        data = page.screenshot()
        frame_c = distinct_colors(data)
        menu_c = distinct_colors(data, MENU_CROP)
        if frame_c >= MIN_COLORS_FRAME and menu_c >= MIN_COLORS_MENU:
            print(f"[boot] title rendered: frame={frame_c} menu={menu_c} colors")
            time.sleep(1.5)  # let animations settle into steady state
            return
        print(f"[boot] waiting… frame={frame_c} menu={menu_c} colors")
        time.sleep(2.5)
    raise SystemExit("FAIL: title screen never rendered — canvas blank after boot timeout")


def run_fresh(page) -> list:
    """Original run: title -> creator -> movement/sword/roll, then the door
    loop into cottage A and back. Returns accumulated soft failures."""
    d = Driver(page)
    # Focus the canvas without clicking a menu label (labels confirm on
    # click): the top-left corner is backdrop only.
    page.mouse.click(60, 60)
    time.sleep(0.3)

    before = d.shot("01-title")

    # INPUT PROOF — the load-bearing assertion. ArrowDown flips the
    # player-count selection; if the highlight doesn't move, no other
    # result in this run can be trusted, so fail immediately.
    d.press("ArrowDown")
    after = d.shot("02-title-selection-moved")
    moved = changed_pixels(before, after, MENU_CROP)
    print(f"[assert] menu highlight: {moved} pixels changed in menu region")
    if moved < MIN_CHANGED_PIXELS:
        raise SystemExit(
            f"FAIL: keyboard input not reaching the game "
            f"(only {moved} pixels changed after ArrowDown)"
        )
    d.press("ArrowUp")  # back to 1 PLAYER

    # Title -> creator (fresh context has no save, so this is COUNT stage).
    d.press("Enter", settle=1.0)
    d.shot("03-creator")

    # Cycle two options with live preview, then jump to Confirm (row 8).
    d.press("ArrowRight")
    d.shot("04-creator-hair2")
    d.press("ArrowDown")
    d.press("ArrowRight")
    d.shot("05-creator-haircolor")
    for _ in range(7):
        d.press("ArrowDown", settle=0.15)
    d.press("Enter", settle=2.5)  # confirm -> scene change -> spawn
    d.shot("06-ingame-spawn")

    # P1 movement (WASD): one shot per direction.
    d.hold("d", 0.7)
    d.shot("07-walk-east")
    d.hold("s", 0.5)
    d.shot("08-walk-south")
    d.hold("a", 0.7)
    d.shot("09-walk-west-flip")
    d.hold("w", 0.5)
    d.shot("10-walk-north")

    # Sword swing (Space) — capture mid-swing (0.4s total, arc from 0.1s).
    page.keyboard.press(" ")
    time.sleep(0.18)
    d.shot("11-sword-swing")
    time.sleep(0.5)

    # Dodge roll (C) — capture mid-roll (0.24s total).
    page.keyboard.press("c")
    time.sleep(0.12)
    d.shot("12-roll")
    time.sleep(0.8)
    outside = d.shot("13-after-roll")

    # DOOR LOOP — walk into cottage A's doorway and back out. The door ART is
    # left of sprite center (door_dx -17): gap center sits at col ~9.4, trigger
    # cells (8..10,19), flanking lamps at (7,20)/(11,20). Post-roll the player
    # sits ~cell (6.5, 23.7) facing north. Route: north to ~row 22, east along
    # row 22 to the walkway stub (cols 8-9), then north through the collision
    # door gap; the transition fires mid-hold. Every crossing hides ~0.44s of
    # black fade — sleep it out before screenshotting.
    d.hold("w", 0.47)
    d.hold("d", 0.80)
    d.hold("w", 0.9, settle=0.2)
    time.sleep(1.6)
    interior = d.shot("14-interior")
    delta_in = frame_delta(outside, interior)
    print(f"[assert] door crossing: {delta_in} thumbnail pixels changed")
    if delta_in < MIN_SCENE_DELTA:
        d.failures.append(
            f"14-interior: only {delta_in} pixels changed after the door walk — "
            f"the transition into home_a1 did not happen"
        )
    # Interior spawn (5,7); the exit mat is directly south at (5,8).
    d.hold("s", 0.6, settle=0.2)
    time.sleep(1.6)
    back = d.shot("15-back-outside")
    delta_out = frame_delta(interior, back)
    print(f"[assert] exit mat: {delta_out} thumbnail pixels changed")
    if delta_out < MIN_SCENE_DELTA:
        d.failures.append(
            f"15-back-outside: only {delta_out} pixels changed after the exit "
            f"mat — the return transition did not happen"
        )
    return d.failures


def run_seeded(browser, page_errors) -> list:
    """Seeded-save context: a v3 blob in localStorage must surface CONTINUE,
    migrate to v4 (keeping the Ginger hair), resume a CLEARED east valley at
    the boss checkpoint, and let the bot hold a conversation."""
    page = browser.new_page(viewport=VIEWPORT)
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.on("console", lambda m: print(f"[console2:{m.type}] {m.text[:240]}"))
    blob = json.dumps(V3_SAVE, separators=(",", ":"))
    page.add_init_script(f"localStorage.setItem('norfolk_path', {json.dumps(blob)});")

    print(f"[nav2] {BASE} (seeded v3 save)")
    page.goto(BASE, wait_until="load", timeout=60_000)
    wait_for_title(page)

    d = Driver(page)
    page.mouse.click(60, 60)
    time.sleep(0.3)
    # With a save present the title opens on MODE with CONTINUE selected.
    d.press("Enter", settle=2.5)
    d.shot("16-continue-resume")

    # SAVE MIGRATION PROOF: Continue ran load_state() -> _apply() which must
    # have rewritten the blob as v4 with the level field, keeping appearances.
    stored = page.evaluate("() => localStorage.getItem('norfolk_path')") or ""
    checks = {
        '"v":4': "version bumped to 4",
        '"level":"valley"': "level field written",
        '"Ginger"': "custom appearance kept",
        '"boss_defeated":true': "boss flag kept",
    }
    for needle, meaning in checks.items():
        ok = needle in stored
        print(f"[assert] migration {needle}: {'ok' if ok else 'MISSING'} ({meaning})")
        if not ok:
            d.failures.append(f"save migration: {needle} missing from stored blob ({meaning})")

    # DIALOGUE — resume placed us at the boss checkpoint (156,26) in a cleared
    # world. Road east to col 166, then straight north up clear grass to the
    # villager at (166,20) (no collider, 18px talk radius).
    d.hold("d", 2.69)
    d.hold("w", 1.62)
    quiet = d.shot("17-before-talk")
    d.press("e", settle=0.6)
    talking = d.shot("18-dialogue-open")
    delta_open = changed_pixels(quiet, talking, DIALOG_CROP)
    print(f"[assert] dialogue open: {delta_open} pixels changed in textbox region")
    if delta_open < MIN_DIALOG_DELTA:
        d.failures.append(
            f"18-dialogue-open: only {delta_open} pixels changed — textbox did not open"
        )
    # Advance through the villager's two lines; the second press closes it.
    d.press("e", settle=0.4)
    d.press("e", settle=0.6)
    closed = d.shot("19-dialogue-closed")
    delta_close = changed_pixels(talking, closed, DIALOG_CROP)
    print(f"[assert] dialogue close: {delta_close} pixels changed in textbox region")
    if delta_close < MIN_DIALOG_DELTA:
        d.failures.append(
            f"19-dialogue-closed: only {delta_close} pixels changed — textbox did not close"
        )
    page.close()
    return d.failures


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                # GPU-less runner: software WebGL2 via SwiftShader/ANGLE.
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
            ]
        )
        page = browser.new_page(viewport=VIEWPORT)
        page_errors = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: print(f"[console:{m.type}] {m.text[:240]}"))

        print(f"[nav] {BASE}")
        page.goto(BASE, wait_until="load", timeout=60_000)
        wait_for_title(page)

        failures += run_fresh(page)
        page.close()
        failures += run_seeded(browser, page_errors)
        browser.close()

    if page_errors:
        print(f"[page errors] {len(page_errors)} JS error(s) — logged, not fatal:")
        for e in page_errors[:10]:
            print(f"  {e[:300]}")

    if failures:
        print("RESULT: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"RESULT: PASS — {len(list(OUT.glob('*.png')))} screenshots in {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
