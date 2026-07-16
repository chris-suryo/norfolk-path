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

Usage: ci_driver.py [output_dir] [base_url]
"""

import io
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

BOOT_TIMEOUT_S = 120
MIN_COLORS_FRAME = 40  # a rendered scene has hundreds; a blank/splash has few
MIN_COLORS_MENU = 8  # panel + text + highlight inside the crop
MIN_CHANGED_PIXELS = 50  # highlight recolor changes far more than this


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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
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
        d.shot("13-after-roll")

        browser.close()

    if page_errors:
        print(f"[page errors] {len(page_errors)} JS error(s) — logged, not fatal:")
        for e in page_errors[:10]:
            print(f"  {e[:300]}")

    if d.failures:
        print("RESULT: FAIL")
        for f in d.failures:
            print(f"  - {f}")
        return 1
    print(f"RESULT: PASS — {len(list(OUT.glob('*.png')))} screenshots in {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
