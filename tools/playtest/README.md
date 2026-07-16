# Playtest driver scripts (round 1)

Helper scripts used by the local (Windows) playtest sessions — see
`docs/playtest-findings.md` for the round-1 results and
`docs/map-visual-audit.md` for the map audit these supported.

These are **machine-specific session tools**, not part of the game or CI. Paths
(Godot binary, repo location, screenshot output dir) are hardcoded near the top
of each script for Chris's machine — adjust before reuse.

## driver.ps1 (dot-source from PowerShell 5.1)

Drives the NATIVE Windows build with real engine input while the window is
unfocused/background:

- `Start-Game` / `Stop-Game` — launch/kill Godot 4.7 with `--path` at the repo.
- `Tap 'W'` / `Hold-Keys @('W','Up') 800` — key input via Win32
  `PostMessage(WM_KEYDOWN/WM_KEYUP)` with proper scan-code lParams. Supports true
  holds and simultaneous P1+P2 keys. Do NOT switch to SendInput/SetForegroundWindow:
  foreground focus is stolen between tool calls and input silently drops.
- `Shot 'name.png'` — window capture via `PrintWindow(PW_RENDERFULLCONTENT)`
  cropped to the client rect (CopyFromScreen breaks under 125 % DPI scaling).

Key map covers P1 (WASD/Space/C), P2 (arrows/Slash/Period), Enter/Esc.

## shot_server.py

Tiny localhost:8643 HTTP server that accepts POSTed base64 PNG data URLs and
writes them to the screenshot dir. Used for WEB-build captures: patch the
exported `index.html` to force `preserveDrawingBuffer: true` on the canvas
context, then `canvas.toDataURL('image/png')` → POST here. (Keyboard input to
the web canvas could NOT be delivered from the in-app browser in round 1 —
web checks are screenshot/JS-only; gameplay drives through driver.ps1.)

## map_audit.py

Mechanical audit over `scripts/island_map.gd`: symbol census (singleton props,
NPC placements), beehive tree-adjacency, same-symbol run detection, decor-
mushroom distance to the bombschroom spawn. Pure stdlib; prints cell coords.

## Fast travel during playtests

Desktop save lives at `%APPDATA%\Godot\app_userdata\norfolk-path\save.json`
(web: `localStorage['norfolk_path']`). Inject
`{"v":3,"checkpoint":N,"player_count":..,"boss_defeated":..,"appearances":[..]}`
and Continue to jump to checkpoint N (boss = 3). Wipes respawn at the checkpoint
and reset the boss to full HP.
