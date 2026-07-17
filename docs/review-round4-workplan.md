# Round-4 work plan — how to split the fixes across sessions

Companion to [review-round4.md](review-round4.md). This maps the review's
findings onto **parallel tracks that don't collide**, so multiple sessions
(or agents, or Chris offline) can work at once and merge cleanly.

## Status — round-4 close (2026-07-17)

The single source of truth for what's actually done, so nobody has to reconstruct
it from memory.

| Item | State |
|---|---|
| Review round-4 (all 8 sections, 44 findings, appendices, finalized top-5) | **DONE** — merged (PR #20). §3 map-forensics independently re-verified. |
| Actions-usage cuts (paths filters, dispatch-only playtest) | **DONE** — merged (PR #21) |
| CORE — scene-state ownership (R4-43/44, B-01…B-06) | **DONE** — merged + verified (PR #23) |
| QUICKFIX — integrity one-liners (R4-01, B-27/B-11/B-10, B-16/R4-10, B-07) | **DONE** — merged + verified (PR #22) |
| B-03/B-04 — defer `boss_defeated` save until win is guaranteed | **PR OPEN** (#24), branch `claude/norfolk-round4-playtest-km5bvj` |
| STORY — dialogue pass (`dialogue_data.gd` + 2 labels) | **IN PROGRESS** — Chris, offline, from [story-brief-round4.md](story-brief-round4.md) |
| FEEL / WORLD / UI tracks | **NOT STARTED** — each wants its own grill+plan |
| Native Windows playtest of all merged fixes | **NOT DONE** — the human gate before "confirmed playable" |

**Blockers / notes:** GitHub Actions is over its monthly free-minutes cap (resets
~15 days from close), so the auto-deploy did **not** run on these merges —
`norfolk-path.vercel.app` is **stale**; playtest the native build, not the live
link. When PR #24 merges, flip B-03/B-04 to fixed in
[review-round4-bugs.json](review-round4-bugs.json) and correct its stale line refs
(147-148 → 165-166). Recommended next track: **FEEL** (top-5 #2 — heal + hit/death
feedback + audio).

## The collision rule (from PROJECT.md's parallel-work map)

Two files are shared hotspots — **only one open PR may touch each at a time:**
`scripts/main.gd` and `scripts/level_registry.gd`. This review adds two more to
treat the same way, because they're the coupling core:
`scripts/game.gd` and `scripts/encounter_manager.gd`.

Everything below is grouped so that **tracks in the same wave own disjoint
files.** A track "owns" its files for the duration of its PR; nobody else
touches them until it merges.

## Sequencing at a glance

```
WAVE 1 (start now, in parallel — all disjoint):
  CORE ......... scene-state ownership      [gating; game/encounter/transition/pause]
  QUICKFIX ..... integrity one-liners       [boss + enemy scenes + controls]
  CI ........... debug-smoke job            [new files only]
  STORY ........ the writing pass           [dialogue_data + 2 labels]  <- Chris, offline

WAVE 2 (after CORE merges — they rebase on it):
  FEEL ......... combat tuning + heal + audio [player/enemy/encounter + new Audio autoload]
  WORLD ........ off-road reward + interiors   [main/registry/maps/baker]  (parallel w/ FEEL)
  UI ........... menu polish                   [pause/hud/controls_menu/player_select]
```

Why CORE gates: it rewrites how `change_scene` and checkpoints work, which
FEEL (encounter areas) and UI (pause menu) both build on. WORLD touches
`main.gd`/`level_registry.gd` — a *different* hotspot from CORE's
`game.gd`/`encounter_manager.gd` — so WORLD can safely run alongside CORE.

## The tracks

### CORE — scene-state ownership  ·  **do first, solo, gating**
- **Branch:** `fix/scene-state-ownership`
- **Owns:** `game.gd`, `encounter_manager.gd`, `level_transition.gd`, `pause_menu.gd` (win/pause gating only)
- **Findings:** R4-43 (gauntlet resurrects on every door), R4-44 (boss goes inert after a library round-trip), B-01…B-06 (win-delay freeze cluster)
- **Shape:** give `win_pending` / `resume_requested` / `area.cleared` / boss `_active` an owner that survives `change_scene`. Start with the free line — `get_tree().paused = false` at the top of `Game.change_scene` — then move the win timer + cleared/active state out of the freed scene, and stop `_apply_resume` early-returning before it clears beaten areas.
- **Fresh-conversation friendly?** No — hand the next session the review's §7 + R4-43/44 + Appendix C cluster A. It's judgment-heavy.
- **Done when:** beat the camp, enter a cottage, leave → camp stays dead. Enter the library mid-approach, leave → boss still activates. Esc/refresh/return-to-title during the 3s win delay never freezes or strands.

### QUICKFIX — integrity one-liners  ·  **parallel, fast, high value**
- **Branch:** `fix/integrity-oneliners`
- **Owns:** `dialogue_box.gd`, `boss_irene.gd`, `controls.gd`, `enemy_slime_big.tscn`, `enemy_mage.tscn`, `enemy_bowman.tscn`
- **Findings:** R4-01 (dialogue type `NinePatchRect`→`Panel`), B-27 (boss calls `_try_contact_damage()` in its loop), B-11 (reset boss modulate), B-10 (gate boss damage on `_active` — do it as a `boss_irene` override to stay out of `enemy.gd`), B-07 (remap saves/erases only the first key per action), B-16/R4-39 (big slime `aggro_radius`), R4-10 (pull mage/bowman aggro inside the 128px half-view or give `_shoot_cd` a starting wind-up)
- **Fresh-conversation friendly?** Yes — every item is one edit with an exact line in the review. Good cold-start agent task.
- **Done when:** NPCs talk in an editor run; Irene hurts you and flashes correctly; a remap survives a reboot with aliases intact; no enemy wakes off-screen or from level load.

### CI — debug-smoke guard  ·  **parallel, fully isolated**
- **Branch:** `ci/debug-smoke`
- **Owns:** `tools/ci_smoke.gd` (new), `.github/workflows/ci.yml`
- **Findings:** R4-27 / §7's "one check": a headless **debug** job that instantiates every `scenes/*.tscn`, parses all registered levels, and greps stderr for `SCRIPT ERROR` (Godot exits 0 regardless — the grep is the assertion). Would have caught R4-01 on its first run.
- **Fresh-conversation friendly?** Yes — §7 specs it in enough detail to implement cold. Blocked only by the Actions billing pause (see below).
- **Done when:** the job fails on a deliberately-broken `@onready` cast and passes on clean main.

### STORY — the writing pass  ·  **Chris, offline, zero code collision**
- **Branch:** `story/dialogue-pass`
- **Owns:** `dialogue_data.gd`, `win_screen.tscn` (the "Ariana" label text), `player_select.tscn` (subtitle)
- **Findings:** R4-31 (premise undiscoverable), R4-32 (no resolution + the mislabeled win screen), R4-25 (Evan's double-fired joke), R4-24/34 (thin cast, silent id fallback), R4-26 (stale handoff)
- **Everything you need is in [story-brief-round4.md](story-brief-round4.md).** Pure data — it can't break the build.

### FEEL — combat tuning + heal + audio  ·  **wave 2, rebase on CORE**
- **Branch:** `feat/combat-feel`
- **Owns:** `player.gd`, `enemy.gd`, `encounter_manager.gd` (area tables), a new `Audio` autoload + sound assets, `hud.gd`
- **Findings:** R4-05 (a non-death heal), R4-38 (buff the full-draw bow or slow the sword), the area-2 difficulty cliff, R4-06/07 (audio + make the existing flash readable, hit-stop)
- **Note:** keep the audio *autoload* self-contained; the per-event hook calls live in these same files, so do them here rather than as a separate track that fights over `player.gd`/`enemy.gd`.
- **Fresh-conversation friendly?** Partly — hand it §2 with the numbers. Tuning wants the review's math.

### WORLD — off-road reward + interior contents  ·  **wave 2, parallel with FEEL**
- **Branch:** `feat/world-rewards`
- **Owns:** `main.gd` (`_spawn_talkers`), `island_map.gd`, `cove_map.gd`, `level_registry.gd`, `bake_interior.py`
- **Findings:** R4-42 (make the chest a talker + move it and the windmill into the 76-tile void), R4-13/14/33 (one findable thing in the library; differentiate the duplicate rooms), R4-15 (give the cove a purpose or cut it from the beta)
- **Note:** this is the `main.gd`/`level_registry.gd` hotspot — solo on those files, but disjoint from CORE, so it may run in Wave 1 if you'd rather. The `bake_interior.py` baker needs a new cell type to place a talker/item indoors (the plumbing gap behind all 8 empty rooms).
- **Fresh-conversation friendly?** No — needs §3's map forensics.

### UI — menu polish  ·  **wave 2, rebase on CORE (shares `pause_menu.gd`)**
- **Branch:** `fix/ui-polish`
- **Owns:** `pause_menu.gd` (zoom rows), `hud.gd`, `controls_menu.gd`, `player_select.gd`
- **Findings:** R4-20 (pause value-rows ignore Left/Right), R4-19 (show alias bindings), R4-22 (checkpoint toast), R4-04 (subtitle legibility at 640×360)
- **Fresh-conversation friendly?** Yes.

## Recommended first move

Kick off **CORE, QUICKFIX, CI, and STORY together** — they're four disjoint
branches. QUICKFIX + CI + STORY are cold-start friendly (hand a fresh session
the branch's row above); CORE wants a session with the review loaded. When CORE
merges, fan out FEEL + WORLD + UI.

## Known blocker: GitHub Actions billing pause

Per the last session handoff, Actions jobs were failing at 0ms (runner never
starts) — an account minutes/spending cap, not a code fault. Until that's
lifted, CI/playtest/deploy won't run on these PRs, and the CI track can't be
verified in the cloud (build it locally against the pinned Godot). Bump the
spending limit before relying on green checks again.

## The `.import` housekeeping commit (separate, needs a Godot editor)

The working tree carries ~586 editor-generated `.import`/`.uid` changes
(PROJECT.md's long-standing "outstanding `.import` commit"). Keep them OUT of
these feature PRs — commit them once, on their own, from a Godot-editor machine,
so the feature diffs stay readable.
