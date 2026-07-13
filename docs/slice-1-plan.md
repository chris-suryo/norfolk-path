# norfolk-path — Slice 1: the walking skeleton

> Approved build plan for the first slice. Authored in a planning session
> (grill → plan). The build itself is executed by a separate session ("Vela").
> This is the source of truth for what Slice 1 is; PROJECT.md points here.

## Context

`norfolk-path` is a personal learning-project: a top-down pixel-art fantasy RPG
in **Godot 4**, playable solo or local 2-player (shared screen), exported to
**HTML5** so it runs from a browser link. The v1 scope (player-select → one
hand-built level → one boss, HP+Attack combat, friend-based NPCs, local save,
*Cute Fantasy 16×16* art) is already locked from a prior ideation session.

The repo began as a fresh `dos new` scaffold — and critically, it was a **Python
CLI** scaffold (typer/pydantic, `uv`/`pytest`/`ruff`, Python-matrix CI) that does
not fit a Godot game. Slice 1 replaces that scaffold with a clean Godot project.

First concrete step (from the handoff): *"set up the Godot project structure, get
a player character walking around a placeholder level with correct movement feel,
before touching art or combat."*

## Goal

A runnable Godot 4.7 project where **one player walks around a placeholder level
with the right movement feel**, and the **HTML5 export pipeline is proven** while
the project is still tiny. No art, no combat, no NPCs, no save, no player-select.

## Decisions locked (via /grill)

1. **Scaffold:** rip out the Python scaffold entirely; clean Godot project at repo
   root. Keep `.claude/`, `CLAUDE.md`, `PROJECT.md`, the session hook.
2. **Build/verify split:** the build session (cloud) authors project files + does a
   headless sanity-check (project imports clean, Web export succeeds). Chris pulls to
   Windows, opens in Godot 4.7, and owns the movement-feel tuning. Movement lives in
   labeled exported constants.
3. **Godot version:** pin **4.7 stable** (June 2026). The build session installs 4.7
   headless + Web export templates to match what Chris opens locally.
4. **First-slice scope:** walking skeleton (details below). Player-select, combat,
   NPCs, save, real art are OUT.
5. **Movement model:** free 8-directional `CharacterBody2D`, normalized diagonals,
   weight via acceleration + friction (velocity lerps toward target, no snap).
6. **Camera:** target-agnostic follow `Camera2D`, bounds-clamped, **3× zoom**,
   **640×360** base viewport, pixel snapping. Target = player now, midpoint of both
   players later — no restructure.
7. **Placeholder level:** `TileMapLayer` + a 2-tile programmer-art set (floor +
   wall-with-collision), so real art drops in by tileset swap, not a rebuild.

## Approach

### 0. Prove the toolchain FIRST (before authoring anything)
This is the real risky unknown, so de-risk it in the first five minutes rather than
after a slice is authored:
- Download + install **Godot 4.7 stable headless** and the matching **Web export
  templates** (`.tpz`) through the agent proxy.
- Create a throwaway one-scene project (or minimal `project.godot` + empty main
  scene) and run a **trivial Web export** end-to-end:
  `godot --headless --path . --export-release "Web" <out>/index.html`.
- Confirm the export produces artifacts (`index.html`, `.wasm`, `.pck`).
- **If the install or export fails, STOP and surface it loudly** — do not proceed to
  author the real project. The whole delivery model depends on this working.
- Once confirmed, discard the throwaway and proceed to Step 1 as written.

### 1. Clean the scaffold
- Delete: `src/`, `tests/`, `pyproject.toml`.
- Replace `.gitignore` with Godot's essentials: `.godot/`, `export/` (or chosen
  export dir), `*.tmp`, `.env`. (Godot re-imports `.godot/` on open.)
- Rewrite `.github/workflows/ci.yml` to a Godot-shaped check (see Verification) or,
  if headless-Godot-in-CI proves flaky, reduce it to a lint/no-op and note the
  decision explicitly. Do **not** leave the Python CI in place.
- Do **not** hand-edit the CLAUDE.md global block. Record Godot run/export commands
  in PROJECT.md's project-specifics section instead.

### 2. Godot project skeleton (repo root)
- `project.godot` pinned to Godot 4.7, with:
  - Display: viewport width/height `640`/`360`; **stretch mode `canvas_items`,
    aspect `expand`** (ultrawide-aware, no letterbox); pixel snap on
    (`rendering/2d/snap/snap_2d_transforms_to_pixel` etc.); default texture filter
    `Nearest` for crisp pixels.
  - **Input map** with both players defined now:
    `p1_up/down/left/right` = W/A/S/D, `p2_up/down/left/right` = arrow keys.
- Folder layout: `scenes/`, `scripts/`, `assets/` (with `assets/placeholder/` for the
  temp tileset). Keep it flat and obvious.

### 3. Player
- `scenes/player.tscn`: `CharacterBody2D` + `Sprite2D` (placeholder colored square)
  + `CollisionShape2D`.
- `scripts/player.gd`: read `p1_*` actions → build input vector → **normalize** →
  lerp `velocity` toward `input_vector * max_speed` using `acceleration` (input) /
  `friction` (no input); `move_and_slide()`.
- Exported, clearly-labeled tuning constants (starting values, Chris tunes in-editor):
  `@export var max_speed := 60.0`, `@export var acceleration := 500.0`,
  `@export var friction := 800.0`.
- Player should read a `player_index` so P2 can reuse the same scene later with the
  `p2_*` action set — but only P1 is instanced in Slice 1.

### 4. Placeholder level + camera
- `scenes/level.tscn`: a `TileMapLayer` using a generated `TileSet` with two 16×16
  tiles (floor = walkable, wall = physics collision), painted into a level with real
  traversal (bigger than one screen).
- `scenes/main.tscn`: level + player instance + a `Camera2D`.
- `scripts/follow_camera.gd`: follow a `target` node (player in Slice 1), clamped via
  `limit_left/top/right/bottom` to the tilemap's used bounds; zoom `Vector2(3,3)`.
  Written so the target can later become a midpoint node.
- Set `main.tscn` as the run/main scene.

### 5. Web export
- Add a **"Web"** export preset; export to e.g. `export/web/index.html`.
- Confirm it runs in a browser. Note the **cross-origin isolation** requirement:
  Godot 4 Web with threads needs COOP/COEP headers; if serving locally, either use a
  header-setting static server or disable threads in the preset for Slice 1. Record
  the chosen approach + the exact "how to serve locally" command in PROJECT.md.

### 6. PROJECT.md
Finalize the project-specifics command block once the serve approach is chosen:
Godot 4.7 pin, how to open/run (`godot --path . --editor`, run main scene), headless
import (`godot --headless --path . --quit`), Web export command, and the local-serve
command with the COOP/COEP note.

## Critical files
- Delete: `src/`, `tests/`, `pyproject.toml`
- Rewrite: `.gitignore`, `.github/workflows/ci.yml`, `PROJECT.md`
- Create: `project.godot`, `scenes/{main,level,player}.tscn`,
  `scripts/{player,follow_camera}.gd`, placeholder `TileSet` + tiles under
  `assets/placeholder/`, `export_presets.cfg` (Web preset)

## Risks / things to watch
- **Godot-in-cloud dependency (biggest unknown — spiked in Step 0):** the build
  session must download+install Godot 4.7 headless and the 4.7 Web export templates
  (`.tpz`) through the agent proxy, and prove a trivial Web export *before* authoring
  the project. If that download or the headless export fails in the cloud env, stop
  and surface it loudly — a headless sanity-check is a stated deliverable, not optional.
- **Version match:** `.tscn`/`project.godot` are version-sensitive; 4.7 on both ends.
  If Chris ends up on a different 4.x, expect import churn.
- **Web cross-origin isolation:** the classic Godot-web gotcha. Decide threads-off vs
  header-serving in Slice 1 and document it.
- **Movement feel is Chris's call, not verifiable headless.** Don't claim the feel is
  "done" — only that it runs and exports.
- **CI feasibility:** headless Godot export in GitHub Actions may be heavy/flaky; if so,
  degrade the CI gracefully and record the decision (don't silently drop it).

## Verification
- **Build session (headless, cloud):**
  - `godot --headless --path . --quit` → project imports with no errors.
  - `godot --headless --path . --export-release "Web" export/web/index.html` →
    export succeeds, artifacts present (`index.html`, `.wasm`, `.pck`).
  - Report both outcomes honestly; if Godot can't be installed in the cloud env,
    stop and say so rather than faking a green check.
- **Chris (Windows, in-engine):**
  - Install Godot 4.7 stable from godotengine.org.
  - Pull the branch, open in Godot 4.7, run `main.tscn`: player walks 8-directionally,
    diagonals aren't faster, movement feels weighty (tune the 3 constants), camera
    follows and clamps to level edges, tiles are crisp at 3×.
  - Open the exported `index.html` in a browser (served with the documented command)
    and confirm the player walks in the tab.

## Out of scope for Slice 1 (do not build without asking)
Player-select screen, combat/HP, NPCs, save system, real *Cute Fantasy* art, 2-player
spawning (input maps are defined but only P1 is instanced).
