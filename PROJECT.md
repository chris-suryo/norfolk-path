# norfolk-path

A personal learning-project: a top-down **pixel-art fantasy RPG** built in
**Godot 4.7**, playable solo or **local 2-player on a shared screen** (WASD +
arrow keys), exported to **HTML5** so it runs from a browser link. Ultrawide
monitors are a first-class target (stretch viewport, not letterbox). The point
is learning the engine end-to-end, not shipping commercially.

## Status

- next: **Playtest Slice 2 (world pipeline) on Windows.** The art pass is
  browser-verified. Slice 2 adds the level-design pipeline: the island is now
  an ASCII map (`scripts/island_map.gd` — edit the string, reshape the world),
  shorelines/path edges autotile from the pack's edge sheets, trees/fences/
  bridge spawn from map symbols with collision, the chicken pecks, zoom is an
  Inspector-tunable export (default 2.5), and **both players now spawn** (WASD
  + arrows) with the camera tracking their midpoint — deliberately no leash
  yet, so walking apart is expected to break framing; that playtest feedback
  drives the camera design. Chris: pull → first-time import → Web export →
  serve → hard-refresh, then walk it (and feel the 2P camera problem).

### v1 scope (the whole build — nothing beyond this without asking)

- Player-select screen: 1 Player or 2 Players (Mario-style)
- ONE hand-built top-down level leading to ONE boss fight
- Simple combat: HP + Attack only (no elemental types, no special moves)
- A few NPCs based on real friends — some allies, some comic villains
- Art: *Cute Fantasy RPG – 16×16* tileset pack (itch.io, free tier)
- Local browser save only (no login, no backend)
- Movement tuned a bit **weightier/slower** than default (an early prototype felt
  too fast/too precise — caused by snapping to max speed with no acceleration ramp)

**Explicitly NOT in v1:** login/cloud saves, type-chart combat, creature-catching,
true split-screen cameras, mobile port, custom hand-drawn art, special moves / skill
trees.

**SHIPPED means:** two people open a browser link, pick 1P or 2P, walk the level,
fight the NPCs (including the friend-based ones) and the boss, see a "quest complete"
screen, and their progress survives a refresh.

## Locations

| Piece | Where |
|---|---|
| Repo | `E:\code\norfolk-path` |
| Engine | Godot **4.7 stable** (June 2026) — from godotengine.org; pin matches the repo |
| Art pack | *Cute Fantasy RPG – 16×16* (free tier), committed at `assets/cute_fantasy/Cute_Fantasy_Free/` |
| Build plan | `docs/slice-1-plan.md` |
| Web build | (HTML5 export → `export/web/` once Slice 1 lands; browser link TBD) |

**On-disk standard:** code repos live under the code root `E:\code\<name>`.

## Project specifics — commands

This is a **Godot / GDScript** project, so the global CLAUDE.md "standard scaffold"
(uv / pytest / ruff) does **not** apply here. Use these instead (Godot 4.7 binary
assumed on PATH as `godot`):

| Task | Command |
|---|---|
| Open in editor (Windows) | `godot --path . --editor` |
| Run the game | `godot --path .` (runs the main scene, `scenes/main.tscn`) |
| **First-time import** (run once per fresh clone, before anything else) | `godot --headless --editor --path . --quit` |
| Headless sanity-check (after the import cache exists) | `godot --headless --path . --quit` |
| Web export (headless) | `godot --headless --path . --export-release "Web" export/web/index.html` |
| Serve the web build locally (PowerShell) | `py -m http.server 8000 --directory export/web` → open `http://localhost:8000` |
| Lint GDScript (what CI runs) | `pip install gdtoolkit==4.5.0`, then `gdformat --check scripts/` and `gdlint scripts/` |
| **Edit the level** | change the ASCII grid in `scripts/island_map.gd` (legend at top of file) — terrain, props, and spawns all follow it; no editor painting needed |

**Playtesting the movement feel is a human-in-editor task on Windows**, not something
the cloud build session can verify — movement lives in exported constants
(`max_speed` / `acceleration` / `friction` on the player) for tuning.

### Slice 1 decisions recorded by the build session

- **Web threads OFF** (`variant/thread_support=false` in `export_presets.cfg`):
  the export uses no SharedArrayBuffer, so it needs **no COOP/COEP headers** and
  runs from any plain static server (hence the simple `http.server` command
  above). Flip threads on later only behind a header-setting host.
- **Renderer = GL Compatibility** (WebGL 2), not Forward+ — the well-supported
  web path in Godot 4 and the safe choice for an HTML5-first project.
- **The level is an ASCII map** (`scripts/island_map.gd`), painted at runtime
  by `level.gd` and decorated by `main.gd` — the map string is the single
  source of truth for terrain, props (trees/fences/bridge), and spawn points.
  Shorelines and path borders autotile in code from the pack's 3×6 edge
  sheets via a neighbor bitmask (no editor terrain sets), with collision on
  water only (`B` bridge cells use a collision-free water source). Design
  rule the art imposes: keep water/path regions ≥ 2 tiles wide (the sheets
  have no strip tiles). The cloud session verifies layouts with a real-art
  preview renderer (scratchpad tool) before pushing.
- **Camera zoom is an exported var** (`zoom_level` on Camera2D, default 2.5)
  — 3× felt too tight in the first browser test; tune it live in the
  Inspector.
- **Both players spawn as of Slice 2** (2P shared-screen test): camera tracks
  a midpoint node, deliberately WITHOUT leash/clamp logic — the "players walk
  apart" problem is meant to be felt in playtest before the camera rule is
  designed. Player-select (1P vs 2P) remains a later slice.
- **CI = gdtoolkit lint only** (see comment in `.github/workflows/ci.yml`): a
  headless-Godot import/export job couldn't be validated from the cloud session
  (egress blocked the engine download), so CI gates on `gdformat --check` +
  `gdlint`, which was proven green before commit. Promote a real import/export
  job once someone validates it locally.
- **Toolchain spike (plan Step 0) failed in the cloud** — github.com and
  godotengine.org are blocked by the session's egress policy, and no allowed
  mirror carries the engine. All engine-side checks (headless import, Web
  export, movement feel) are therefore local, human steps for now.
- **`.gitattributes` marks image/audio/font extensions `binary`** (good
  hygiene, kept) — but this was **not** the cause of the first Windows import
  failure. That was a real misdiagnosis: `git hash-object` on the Windows
  working copy matched `git rev-parse HEAD:...` exactly for both PNGs, proving
  the files were byte-identical to what's committed the whole time.
- **The chicken at the pond is a TEMPORARY stand-in for Ariana, who should be
  a DUCK.** A duck sprite download was attempted but didn't extract correctly;
  the pack's `Animals/Chicken/Chicken.png` fills the spot visually until a duck
  is sourced. Swap = replace the `Chicken` Sprite2D texture in
  `scenes/main.tscn` (frames are 2×2 of 32×32; adjust `hframes`/`vframes` to
  the duck sheet).
- **Art pack license caution:** the Cute Fantasy free tier allows
  non-commercial use and modification but **forbids redistribution, even
  modified**. The pack is committed to this repo — fine while the repo is
  private, but making the repo public would arguably be redistribution.
  Chris's call to revisit before any public hosting of the repo itself (the
  exported game build is a different question from redistributing the raw
  pack).
- **Real cause of "No loader found for resource" on first Windows import:**
  the project had *never* been imported (`.godot/` didn't exist yet), and the
  documented sanity command, `godot --headless --path . --quit` (no
  `--editor`), runs in runtime/game mode — which only loads *already-imported*
  resources and has no import pipeline. A brand-new headless checkout needs
  one `godot --headless --editor --path . --quit` pass first to build the
  `.godot/imported/` cache; only after that does the plain `--quit` sanity
  command work. Documented as a separate "first-time import" row above so
  this doesn't trip the next fresh clone (including CI, if a headless Godot
  job is ever promoted there).

---
kit: 364605cbbd6bbff3e9ed81ee4fe49035120c7ff0 · stamped by dos new
