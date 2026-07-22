# Norfolk Path — one-click local playtest launcher (Windows)

Double-click a desktop icon → it pulls the latest, launches the game, and tells
you exactly which build you're on. No manual git/import steps per session.

## First-time setup (once)

From the repo root in PowerShell:

```powershell
cd E:\code\norfolk-path
git fetch origin
git checkout -B playtest/beta origin/playtest/beta   # the combined test build
powershell -ExecutionPolicy Bypass -File launcher\Install-Shortcut.ps1
```

That makes **Norfolk Path (playtest)** on your Desktop. (Godot is found
automatically on first run; if it can't, it asks once and remembers.)

## Every session after

Double-click **Norfolk Path (playtest)**. It fetches, force-syncs to the exact
pinned version, imports new assets, and launches — printing a green
`RUNNING: playtest/beta @ <sha>` banner so you always know what you're testing.
Pair that sha with `docs/chris-walkthrough.md` as your test script.

## Tuning

The playtest branch is **read-only** — the launcher force-syncs it, so it
stashes any local edits (recover with `git stash list`). To change tuning
(zoom/speed presets, enemy HP, etc.), tell the build session the values and it
bakes them into the real PRs.

## Test one thing in isolation

```powershell
launcher\play-norfolk-path.ps1 fix/coop-projectiles   # or any branch, or main
```

## Files

- `play-norfolk-path.ps1` — the launcher (find Godot → sync → import → run).
- `Install-Shortcut.ps1` — makes the Desktop shortcut.
- `norfolk-path.ico` — the icon (Irene).
- `.godot-path` — created on first run, caches your Godot exe path (gitignored).
