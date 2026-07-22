# Walkthrough: what changed in PRs #37–#43 (all merged, none playtested)

One continuous in-editor route through everything that landed while you were
away. Each stop: **what changed → where to stand / what to press → expected →
flag if**. Order is optimized so one session covers everything without
backtracking. Tuning knobs are named so a "feels off" is a one-line fix, not a
re-review.

Everything here passed the headless gate (lint + all checkers + determinism +
render eyeballs). What it has NOT had is human eyes in the engine — that's
this checklist.

---

## 0 · Setup

- Pull `main`, open in Godot 4.7. Fresh clone? Run the first-time import once:
  `godot --headless --editor --path . --quit`.
- Optional: keep an old save around (any pre-#38 save) — stop 7 tests that it
  still loads.

## 1 · Pause-menu shakedown — zoom persist (#39) + speed toggle (#40)

**What changed:** camera zoom now survives entering/exiting buildings (it used
to snap back to 2.5 on every door); the pause menu has a new **Speed** row
(Slow 0.8 / Normal 1.0 / Fast 1.25 via `Engine.time_scale`).

- Start a game. Esc → the menu should now read: Resume / Zoom / **Speed** /
  Save Now / Controls / How to Play / Return to Title.
- On **Zoom**, press ←/→ to set **Far**. On **Speed**, ←/→ to **Fast**. Esc out.
- Walk into any cottage, walk back out.
- **Expected:** zoom is still Far after both transitions (the old bug: it reset
  at every door). Game speed is still Fast. Re-open the pause menu — both rows'
  labels show the live values (they used to go stale after a mouse-wheel zoom).
- Mouse-wheel to some in-between zoom, enter/exit a house — the wheel zoom
  carries too. Pause menu snaps the label to the *nearest* preset (by design).
- Play ~2 min at Slow and Fast. **Flag if:** either preset feels like the wrong
  value (knob: `SPEED_PRESETS` in `pause_menu.gd`); fades/cutscene pacing feel
  weird when speed ≠ Normal (`Engine.time_scale` scales those too — known,
  judged acceptable, your veto); a small interior at Far zoom shows too much
  void around the room (pre-existing centering behavior, now reachable).
- **Regression check:** let the intro cutscene play (New Game) with a non-default
  zoom set — when the cutscene ends it should restore YOUR zoom, not 2.5.

## 2 · Village pass — fence fix (#41) + North Overlook (#43)

**What changed:** the fence behind house J no longer juts ~5 cells past the
animal pen; the empty north field above the houses is now "The North Overlook"
— a golden-birch rest spot with the game's first unguarded exploration chest.

- Walk to the SW cow pen (behind the stone house J, west side).
- **Expected:** the pen is a clean closed rectangle; no fence bar reaching
  toward the house. **Flag if:** the pen's top-left corner looks odd in-engine
  (the neighbour-aware fence renderer picks sprites headlessly unverifiable).
- Head north from behind cottage E (the one at the village's NE edge), following
  the lamp pairs uphill.
- **Expected:** a signpost, then a birch-framed clearing with a bench, lamp,
  flowers, butterflies — and a chest by the bench. Open it → **Swift Boots**
  message, and your walk speed visibly rises immediately.
- **Flag if:** the golden birches don't read as a landmark from the road (the
  in-engine density is sparser than the preview render — known caveat from that
  PR); the chest feels too easy this close to spawn (its cell/reward: 
  `loot_data.gd`, `Vector2i(35, 8): "swift"`).

## 3 · The windmill (#42) — **test the door first, it's the risk item**

**What changed:** the windmill (east of the wheat field) is now enterable — a
doorway collision gap + a baked mill-storeroom interior.

- Walk to the windmill and press into the **center of its base** (the door art).
- **Expected:** you slide into a 16px gap and the screen fades into an 11×9
  storeroom — barrels along the walls, work table center, two windows. Step on
  the bottom mat → back outside, just south of the door, no re-trigger bounce.
- **Flag if — most likely failure on this list:** you wedge on the door flanks
  and can't enter (the gap is 16px vs. the player's circle collider — exactly
  the tuning the house doors needed). Knob: the `z` entry's `collision_segments`
  in `prop_table.gd` — widen the flank offsets. Also flag: sails stopped
  animating (they shouldn't have — same StaticBody path), interior size/dressing
  feels wrong (`windmill` spec in `tools/bake_interior.py`, re-bake).

## 4 · Procgen interiors (#37) — bedroom, parlor, library

**What changed:** three rooms are now furnished by the deterministic procedural
furnisher instead of hand lists: house J's bedroom, house G's parlor, and the
library.

- Enter each and walk the walls: house J (bedroom: bed/rug/lamp/plants),
  house G (parlor: table+chairs on rug, fireplace, clock), the library
  (shelf bank, grandfather clock, two reading desks).
- **Expected:** furniture collides where it looks solid, rugs walk-over, the
  exit mat is reachable, nothing overlaps a window.
- **Flag if:** any layout reads worse than the old hand version — each room's
  hand list is still in `bake_interior.py` as a fallback; delete its
  `"furnish"` key + re-bake to revert that room alone. On your OK, phase 2
  converts the remaining rooms.

## 5 · Reward loop (#38) — chests, upgrades, persistence, aggro

**What changed:** permanent power-up system + openable chests; enemies now
aggro when hit from range.

- **Aggro:** bow-shoot an idle enemy from beyond its notice radius →
  **expected:** it chases immediately (used to ignore ranged hits).
- Clear the forest camp, open the camp chest → **Fletching Kit**, arrows hit
  harder after.
- Library approach chest → **Heart Locket**, max HP up AND heals the gain.
- Quit to title → Continue → **expected:** both chests stay looted-dim, both
  upgrades still active. New Game → **expected:** chests reset, upgrades gone.
- **Flag if:** any message/timing feels wrong mid-combat, or a chest's
  StaticBody blocks a path you care about.

## 6 · Overlook ↔ upgrade interaction (one deliberate check)

With Swift Boots collected, the pause-menu **Speed: Fast** stacks on top
(boots = +max_speed, Fast = time_scale). **Expected:** fast but controllable.
**Flag if:** combined it's absurd — that's the argument for retuning the Fast
preset, not the boots.

## 7 · Save-compat spot-check

Load your **pre-#38 save** (if you kept one). **Expected:** loads clean, empty
chest/upgrade state, everything else intact (fields are additive; verified
headlessly against synthetic old saves — this is the belt-and-suspenders human
check).

## 8 · Known items already on the radar (don't re-report)

- Latent, unarmed: two chests sharing one upgrade id would double-apply on live
  players (all three shipped chests use distinct ids). Design call parked
  with you.
- Preview renders are denser than engine reality (preview layers ambient tufts
  the engine doesn't spawn) — judge meadows in-engine.
- `.import`/`.uid` housekeeping commit still owed from a Godot-editor machine.

---

*Maintained by the build session. New merged PRs each carry a
`## Playtest checklist` section in their PR body; those get harvested into
this doc at the end of the current push, ordered as one route.*
