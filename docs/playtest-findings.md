# Playtest findings — round 1

Local playtest on Chris's Windows machine, Godot 4.7-stable (Chris's exact build),
branch `playtest/round-1` = `origin/main` @ 41188ea. The engine ran natively
(windowed); input was driven programmatically via Win32 `PostMessage` key events
(real editor F5 window, not the web build — see Methodology at the bottom). The
web export was also built locally and checked in a browser for boot, fonts and
save-gating. Screenshots live in `docs/playtest/round-1/`.

**TL;DR:** the game is playable end-to-end (creator → slimes → skeletons →
camp → Irene → win screen). Creator, persistence, checkpoints, co-op revive and
the full HUD all work. The two most user-visible problems are the **missing
space glyph in the pixel font (tofu boxes on every menu line of the web build —
including the live site)** and a cluster of **sticky collision spots** (bridge
parapet corners, tent rock pocket) that can pin a player in place. Several
smaller polish items below.

## Checklist status

| Item | Status |
|---|---|
| A. Creator 1P — all 7 rows cycle + wrap | PASS |
| A. Creator — Randomize / Confirm / Back | PASS |
| A. Creator 2P — P1→P2 handoff, Back semantics | PASS |
| A. Creator — live preview layers stay aligned (idle) | PASS |
| B. Idle + walk all 8 directions | PASS |
| B. Left-facing flip | PASS (indirect — sword/arc render on left when facing west; per-pixel sprite inspection not done at 640×360) |
| B. Sword swing each facing | PASS, with one visual anomaly (see "Swing arc direction") |
| B. Actual hit + impact FX | PASS (slime killed; debris + spark dashes captured) |
| B. Max-range hit | PARTIAL (hits landed and killed, but a controlled max-range-only hit wasn't isolated) |
| B. Dodge roll movement + animation | PASS |
| B. Roll i-frame flash | NOT VERIFIED (no flash distinguishable in stills) |
| B. Well-timed roll passes through a hit | NOT RUN (needs human timing; scripted input couldn't time reliably) |
| B. Damage → hurt flash → downed | PASS (red tint, collapse pose captured) |
| B. 1P downed → checkpoint respawn + area rearm | PASS |
| B. 2P co-op revive in place | PASS (P1 downed, P2 cleared skeleton, P1 back up while P2 stayed at low HP) |
| B. 2P all-down → checkpoint respawn | PASS (verified repeatedly, incl. boss reset) |
| C. Persistence — desktop save/Continue | PASS (save.json matches created look exactly; Continue restores count + appearances + checkpoint) |
| C. Persistence — web (localStorage) | PARTIAL (load path PASS via injected save → CONTINUE gates correctly; write path not drivable — see Methodology) |
| D. Pause / Save Now | PASS ("Saved HH:MM" toast) |
| D. Skeletons | PASS |
| D. Bombschroom | PARTIAL (camp + enemy engaged; its blast wiped the party — windup flash and gas cloud not captured in stills) |
| D. Irene boss | PASS (activation, HP bar, book projectiles, taunt line, damage to ~55%); **kill performed manually by Chris** |
| D. Win screen | Reached (by Chris, manually); not screenshotted. Post-win reset behavior observed via save file — see finding below |
| E. Map polish pass west/middle/east | DONE — traversal screenshots `map-east-run-*.png`; issues below |
| Live URL reachable | PASS (https://norfolk-path.vercel.app boots; same font bug as local web build) |
| Engine smoke test | PASS (headless `--import` clean; native boot clean, no script errors) |

## Findings

### Pixel font is missing the space glyph — tofu boxes across all web menus
- Area: hud / flow (web build, including LIVE site)
- Severity: bug (worst user-visible issue; first thing a visitor sees)
- Observed: on the web build every UI line renders a boxed glyph (hex `0020`)
  wherever a space should be: "NORFOLK⬚PATH", "1⬚PLAYER", "NEW⬚GAME", and the
  hint lines are almost entirely boxes. Confirmed on the locally exported web
  build AND on https://norfolk-path.vercel.app (CI build). Native Windows build
  renders spaces fine — `allow_system_fallback=true` silently substitutes a
  system font on desktop, but web has no system fonts, so the .notdef box shows.
  Root cause is in the font file itself: `assets/game/CuteFantasy-5x9.ttf`
  appears to have no glyph for U+0020.
- Expected: spaces render as spaces on every platform.
- Screenshot: docs/playtest/round-1/boot-title.png (local web),
  docs/playtest/round-1/live-vercel-title.png (live site),
  docs/playtest/round-1/native-count-stage.png (native — correct).

### Committed font .import was hand-authored; editor regenerates it (dirty tree)
- Area: flow (repo hygiene)
- Severity: bug
- Observed: `assets/game/CuteFantasy-5x9.ttf.import` in git contains a
  hand-written UID (`uid://cnorfolkctf5x9font`) and a fake dest hash
  (`...-cf5x9norfolkpathfont000000000.fontdata`). The first time the real
  editor imports the project it regenerates a genuine UID/hash and adds
  Godot-4.7 param keys (`modulate_color_glyphs`, etc.), so every local machine
  immediately has a modified tracked file. Dozens of asset `.png.import` files
  are also untracked locally (never committed), so a fresh editor open makes a
  noisy working tree.
- Expected: commit editor-generated `.import` files (open project once, commit
  the result), or gitignore them consistently — one policy, applied to all.
- Screenshot: n/a (see `git status` / `git diff` on any machine after opening
  the editor).

### Sticky collision at stone-bridge parapet corners
- Area: map-middle
- Severity: bug
- Observed: approaching the river bridge from the northwest (the natural line
  from the road), both players got pinned against the bridge's west parapet
  corner — holding east for 4+ seconds produced zero movement, twice, in two
  different spots (NW corner outside the deck, and mid-deck against the north
  parapet). Stepping south first, then east, always freed them. Repro: walk the
  road east to the bridge, hug the north edge, hold east.
- Expected: colliders beveled/positioned so sliding along the wall funnels the
  player onto the deck instead of wedging them.
- Screenshot: docs/playtest/round-1/map-bridge-cross-1.png (pinned; identical
  frame repeated over 2.5s of held input), docs/playtest/round-1/diag-stuck-south.png
  (after stepping south, both free and crossing).

### Prop pocket at the camp tent wedges players
- Area: map-middle (bombschroom camp)
- Severity: bug
- Observed: the rock cluster + tree trunk immediately west of the tent forms a
  pocket; P1 got wedged there twice and S/D inputs didn't free them (had to go
  north). Blind repro: from the camp, walk into the gap between the tree and
  the rocks next to the tent's left pole.
- Expected: prop colliders spaced so there's no dead pocket, or the gap closed
  entirely.
- Screenshot: docs/playtest/round-1/bombschroom-leg2.png (P1's hat visible
  wedged between rock and tree; same position across three consecutive
  captures).

### Swing arc occasionally renders opposite to the direction that lands the hit
- Area: combat
- Severity: bug (needs code-side verification)
- Observed: in several captures the white swing arc + sword sprite render on
  the player's WEST side while the hit lands on a slime to the EAST (slime
  deformed with debris in the same frame). A controlled test (long walk to set
  facing, then swing) matched arc-to-facing for west and south, so the anomaly
  appears when direction changes rapidly or after respawns — possibly facing
  updates a frame late, or the attack uses stale facing.
- Expected: swing visual and hitbox always match current facing.
- Screenshot: docs/playtest/round-1/combat-1p-hit-seq2.png (arc west, slime
  east mid-death), docs/playtest/round-1/combat-1p-facing-west.png +
  combat-1p-facing-south.png (controlled, correct).

### Post-win reset silently discards the created characters
- Area: persistence / flow
- Severity: bug (design-level)
- Observed: after Chris beat Irene and pressed through the win screen, the
  saved file became `checkpoint 0, boss_defeated false, player_count 2` with
  DEFAULT appearances (P1's custom blonde/hat look was replaced by the seed
  default). The title screen then offers CONTINUE, which resumes a fresh run
  with default-looking characters — surprising after having customized them.
- Expected: either keep appearances through the reset (players' identities
  persist across runs), or don't offer CONTINUE for a just-reset run.
- Screenshot: docs/playtest/round-1/post-irene-state.png (title after win);
  save.json contents captured in the session log.

### Boss resets to full HP on every party wipe
- Area: combat (boss)
- Severity: polish (design feedback)
- Observed: each all-down respawn (players revive at the adjacent checkpoint-3
  beacon) resets Irene to full HP. With 6-HP players and 1-2 books being
  enough to chip them down, uncoordinated play bounces off her indefinitely —
  scripted play got her to ~55% repeatedly but never further; a human (Chris)
  beat her fine. Worth a deliberate decision: keep as intended difficulty, or
  persist partial boss damage / shorten her range.
- Expected: intentional, documented difficulty rather than accidental wall.
- Screenshot: docs/playtest/round-1/boss-assault12.png (~55%),
  docs/playtest/round-1/boss-tight-end.png (bar back to ~full right after a
  wipe, players respawned at the beacon).

### Bombschroom is nearly identical to decorative mushrooms
- Area: map-middle (camp)
- Severity: polish
- Observed: the bombschroom enemy and the decorative red amanita props are both
  small red-capped mushrooms; at 640×360 they're effectively indistinguishable
  until the enemy detonates (its blast wiped the party before any tell was
  visible in stills). Several decor amanitas sit near the camp specifically.
- Expected: a visual tell on the enemy (idle pulse/bob, different cap color,
  eyes) so players can read the threat before stepping on it.
- Screenshot: docs/playtest/round-1/bombschroom-approach2.png (enemy alive near
  the campfire, decor mushrooms in the same shot),
  docs/playtest/round-1/bomb2-southroute.png.

### Road terminates in a blunt dead-end near the boss arena
- Area: map-east
- Severity: polish
- Observed: the dirt road just stops in a rectangular stub in the grass short
  of the boss/lake area (and the library that per design lives at the far east
  wasn't seen anywhere around the arena — the fight happens on open road/lake
  shore). Feels unfinished / AI-generated-tell.
- Expected: road tapers into a clearing, gate, or the library frontage it's
  leading to.
- Screenshot: docs/playtest/round-1/boss-seq3.png (road stub, book projectile
  in flight).

### Creator hint line is barely legible
- Area: creator
- Severity: polish
- Observed: the input-hints line at the bottom of the creator panel is tiny and
  very low contrast (pale grey on tan). At the default window size it's
  unreadable; at 4× it's still faint. The title-screen hint rows have the same
  problem (compounded by the tofu boxes on web).
- Expected: readable hint text (darker color or larger font).
- Screenshot: docs/playtest/round-1/2p-creator-p2.png (bottom of panel).

### Dialogue/taunt font doesn't match the pixel aesthetic
- Area: hud
- Severity: polish
- Observed: Irene's taunt line ("Oh — you're here about the DVD. I really am
  sorry it came to this.") renders in a smooth antialiased font (Godot default),
  while every other UI element uses the 5×9 pixel font. Possibly intentional
  for readability, but it visibly breaks style.
- Expected: pixel font (or a deliberate, consistent "subtitle" style).
- Screenshot: docs/playtest/round-1/boss-assault6.png.

### HP bar fill is hard to read against the HUD
- Area: hud
- Severity: polish
- Observed: the missing-HP portion of the P1/P2 bars is near-black on a dark
  edge, so at a glance "nearly dead" and "full but dim" are easy to confuse
  (this repeatedly confused the playtest itself). P2's bar fills right-to-left
  (mirrored), which is fine once noticed but adds to the ambiguity.
- Expected: lighter empty-fill or an outlined empty state; consistent fill
  direction is a taste call.
- Screenshot: docs/playtest/round-1/2p-simul-move.png (both bars read as
  "empty" mid-fight), docs/playtest/round-1/boss-long24.png.

### Boss arena flag/checkpoint props confusable with NPCs
- Area: map-east / map-west
- Severity: polish (minor)
- Observed: the checkpoint beacons are scarecrow figures (straw hat + blue
  overalls, arms out) with a lamp. West village also has decorative scarecrows
  by the wheat fields, and during play the beacon was repeatedly mistaken for
  an NPC/player at a glance (same silhouette + palette as a hatted player).
- Expected: beacon silhouette more distinct from player/NPC (e.g. taller pole,
  distinct color, animated glow).
- Screenshot: docs/playtest/round-1/2p-p2-attack.png (beacon scarecrow beside
  the players at the lamp), docs/playtest/round-1/bombschroom-spawn.png.

## Positive observations (no action needed)

- Creator handoff logic is exactly to spec: P1 confirm → P2; Esc from P2 → P1
  with confirmed look intact (2p-back-to-p1.png); Esc from P1 → count screen.
- Randomize produces varied, valid combos; live preview matches labels on
  every row change (creator-1p-*.png series).
- Checkpoint toast ("CHECKPOINT SAVED", map-east-run-15.png), pause Save Now
  toast, and autosave-on-creation all fired as designed.
- Co-op revive works and reads clearly in motion (2p-revive2-fight2.png shows
  P1 back up beside the dying skeleton while P2 stayed at ~15% — a checkpoint
  respawn would have refilled both).
- Ambient life (chickens, ducks, goose, frog, capybara in the lake, floating
  logs, boat) is charming and dense; boss-long24.png accidentally captured a
  duck inspecting a downed player, which is honestly a feature.
- Desktop persistence round-trip is byte-exact for appearances.
- Web export boots clean (no console errors), and the live Vercel deployment is
  publicly reachable — the PROJECT.md "verify from another machine" item can be
  considered half-done (loads fine from this machine's browser; still worth one
  check from a truly external network).

## Methodology + honest limitations

- The Claude-driven browser couldn't deliver keyboard input to the Godot web
  canvas (CDP events never reached the page in this session; untrusted JS
  events reach Godot's handler but the engine ignores them — separately
  interesting but not a game bug). So all gameplay was driven on the NATIVE
  Windows build via Win32 `PostMessage` scan-code events, with `PrintWindow`
  screen captures. This gives real engine input but blind, latency-heavy
  "hands" — timing-sensitive tests (roll i-frames, max-range spacing) were
  attempted but couldn't be timed reliably, and are marked NOT VERIFIED rather
  than guessed.
- The Irene kill and win screen were completed manually by Chris mid-session
  (the scripted fighter kept trading wipes with the boss-reset mechanic); every
  other result above was observed directly from the scripted run.
- The bombschroom's blast is inferred (mushroom present → party wipe → mushroom
  gone); its windup flash and gas cloud were never caught in a still frame.
- One save-file injection was used to jump back to checkpoint 2 after the
  post-win reset (documented format, `user://save.json`) — used for travel
  only, not to fake any result.

## Combined triage — round 1 (cloud audit + live findings, post-decisions)

Cloud session cross-checked every live finding against the code and the
scale-2 map composites (west/middle/east), then applied Chris's four decisions
(post-win identity: KEEP; .import policy: COMMIT generated; boss wipe-reset:
INTENDED; map polish: data-level only, layout frozen). Status of every item:

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | Font missing space glyph (web tofu) | CONFIRMED — U+0020 absent from cmap; also `_`, `–`, `—` | **FIXED**: fontTools patch adds empty space glyph (advance 250) + maps both dashes to hyphen; verified by before/after Pillow render of every UI string |
| 2 | Hand-authored font .import dirties tree | CONFIRMED | Decision: commit editor-generated .import/.uid files — needs one commit from a Godot-editor machine AFTER the font fix merges (regenerates for the patched .ttf). Not in this slice's diff |
| 3 | Bridge parapet corner pins | CONFIRMED — classic rect-vs-tile-seam catch: player used a 12×12 RectangleShape2D against per-tile water colliders | **FIXED (needs live re-verify)**: player body is now a radius-6 CircleShape2D — circles slide over seams and around corners; no frozen-map edits |
| 4 | Camp tent rock pocket | Same mechanism as #3 | Same fix; if the pocket still wedges live, next step is a collider tweak on the camp-decor prop (data-level) |
| 5 | Swing arc opposite the hit | NOT A DEFECT (verdict from code + frames): hitbox is 24×20 at facing×18px — physically cannot hit behind; the anomaly frame shows impact sparks NE with arc W, consistent with swing N−1's persistent FX + slime death anim overlapping swing N's capture. Controlled tests passed | No code change; round-2 live re-test listed to falsify if wrong |
| 6 | Post-win reset wipes characters, still offers Continue | CONFIRMED — win_screen called reset_run() which reset appearances | **FIXED**: reset_run() now clears run progress only; appearances persist as identity. Continue after a win = fresh run, same characters |
| 7 | Boss full-HP reset on wipe | Decision: INTENDED difficulty | **DOCUMENTED** in docs/combat-slice.md; revisit only if humans also bounce |
| 8 | Bombschroom identical to decor amanitas | CONFIRMED | **FIXED**: idle breathe (±10% scale) + faint warm flush — decor mushrooms hold still; needs live look |
| 9 | Road dead-end near arena / "library missing" | PARTLY CORRECTED: the manor (library) EXISTS north of the road end — composites show it; the playtest never looked north. The blunt stub is real | DEFERRED to the cove/layout decision: routing the road to the manor entrance is an island_map.gd layout edit (frozen) |
| 10 | Creator + title hints barely legible | CONFIRMED (pale grey on tan) | **FIXED**: hint/legend labels now dark brown (0.45,0.32,0.22) @ size 8 — high contrast on the tan panel |
| 11 | Dialogue font mismatch | CONFIRMED — boss NameLabel had the pixel font, Dialogue/Line did not | **FIXED**: Line gets the pixel font @ 9 (em-dash/apostrophe coverage secured by fix #1) |
| 12 | HP bar empty-state unreadable | CONFIRMED (tint_under 0.22,0.24,0.2 ≈ black) | **FIXED**: tint_under lightened to 0.45,0.49,0.42 — empty track reads as a pale pill. P2's mirrored fill left as-is (taste) |
| 13 | Beacon confusable with NPC/scarecrow | Mechanism confirmed: beacon is a lamp post; decor scarecrows stand nearby and read as figures | DEFERRED: prop placement lives in the frozen map; revisit in the cove pass (candidate: move/swap the two checkpoint-adjacent scarecrows) |
| — | West quadrant (cloud audit) | No new blockers; minor: floating cobble patches, two similar red-roof houses | Noted only |

Round-2 live checklist (next Godot session): bridge + tent un-stick with the
circle body; web build spaces render everywhere (title, hints, creator); post-win
Continue keeps the created look; bombschroom breathe reads as a tell; arc-vs-hit
one deliberate rapid-turn swing test; roll i-frames + roll-through-hit (human
timing); bombschroom windup flash + gas visuals; win screen screenshot.

---

# Playtest findings — round 3

Chris's first real playthrough of the beta build (live web build at
norfolk-path.vercel.app, post world-alive + combat slices, PR #13-#16
merged). Findings arrived as annotated feedback with 5 screenshots. This
round also produced explicit direction decisions: **bugs first**, then combat
feel, then UI (new CC0 font + dark panels approved), then the library
interior. Keys: G = sword, H = bow (Space and "/" stay as legacy aliases
until the remap screen ships); P2 ranged on numpad 1/2/3. Difficulty
selector: backlog, not now.

## What's working (keep, don't touch)

- Movement + dodge roll: "really solid, you really honestly nailed that."
- Door entry flow and the interior vibe ("the interior looks great").
- The cove (second area): "no notes."
- The harder difficulty curve after the rebalance — likes it.
- Character creator options are fun (input is the problem, not content).
- Subtle animations (mushroom breathe etc.) land well.

## Triage

| # | Finding | Root cause (verified in code/art) | Resolution |
|---|---|---|---|
| 1 | Walked out through the bottom of a house into the void | `Game.change_scene()` silently dropped a crossing requested during the 0.44s arrival fade; the interior exit mat is 1 tile from the spawn and the trigger's arm was already consumed. Off-map cells have no collision | **FIXED (Slice C1)**: `Game.is_fading()` exposed; LevelTransition polls in `_physics_process` and never consumes its arm on a refused crossing — the mat retries the frame the fade clears |
| 2 | Clock sitting on the floor | Interior top wall was 1 tile tall, so wall-mounted decor anchored at row 1 hung at floor level | **FIXED (C2)**: baker renders a 2-row hanging band; windows/clock/pans sit ON the wall |
| 3 | Rug drawn over the bed ("make sure that never happens") | Baker had no overlap rule; home_j1's rug was stamped after the bed | **FIXED (C2)**: fail-loud overlap validator — solid-over-solid and rug-over-solid abort the bake (rug-under stays legal). Caught a real error (chair on spawn cell) on its first run |
| 4 | No furniture collision | Baked furniture was deliberately decor-only v1 | **FIXED (C2)**: furniture footprints emit collision cells (X) into the interior maps; big pieces solid, rugs/wall decor walkable |
| 5 | "Not able to enter every house right — door entrance not where it's supposed to be" | Door ART is off-center on 4/6 building sprites (house_a −17px, house_g −43px, house_j −26px, house_e +12px) while the collision gap, trigger and lamps sat at sprite center | **FIXED (C3)**: per-building `door_dx` measured from the art drives the collision gap (gen_prop_table), the trigger cells and entries (registry), and the lamp/walkway placement (map). Valley re-baked, diff confined |
| 6 | Two flanking lamps "don't make sense" | Lamps flanked the sprite center, not the drawn door | **FIXED (C3)**: lamps moved to flank the real doors |
| 7 | Redo walkways | Paths led to sprite-center doors | **FIXED (C3)**: cottage G's walkway shifted to the door column; house A got a walkway stub; the rest of the walkway network is a level-design-session item |
| 8 | Chicken standing on a player's face | Animal Y-sort origin at cell center while visual feet sat up to 11px higher — outside the +9px feet-below-origin convention player/props share | **FIXED (C4)**: measured per-animal `foot` shift moves the sort origin onto the visual feet; sprite offset compensated, pixels unchanged |
| 9 | Enemies stuck on corners, "more intelligent in how they move" | Straight-line chase re-aimed every frame, pinning enemies into props | **FIXED (C5)**: blocked chasers commit to a collision-tangent slide (exported 0.35s knob) before re-aiming. No pathfinding — live-verify the feel |
| 10 | Sword keys: G sword / H bow; P2 numpad | Decision, not a defect | **Slice D** (keys + aliases until remap ships) |
| 11 | Bow should be hold-to-charge with damage by hold time | Current bow is tap-fire | **Slice D** (charge draw, half-speed while drawing, damage/speed scale with hold) |
| 12 | Sword swing "has fireballs" — wants a white swipe matching the hit region | Orange `_draw()` crescent reads as a projectile | **Slice D** (white/pale swipe arc matched to the real SwordHitbox sweep) |
| 13 | Menus tan + hard to read; text/font "impossible to read" | Small pixel font + tan-on-tan panels | **Slice E** (new CC0/OFL font + dark panel theme, approved) |
| 14 | Creator is arrow-keys-only | No gui_input hookup in character_creator.gd | **Slice E** (mouse hover/click, title/pause pattern) |
| 15 | Key remapping should be the menu focus | — | **Slice E** (Controls screen, InputMap + user://controls.json) |
| 16 | Change Evan's character to a boy that looks like him | Fruit-stand NPC uses a premade sprite | **Slice E** |
| 17 | Irene's house (library) should be enterable | Library door is dialogue-locked flavor | **Slice F** (baker-generated study interior via the inn's centered arch) |
| 18 | Use the top/bottom of the map | Dead bands are a layout property | **DEFERRED (named)**: dedicated level-design session |
| 19 | Maybe difficulty settings later | — | **BACKLOG** by Chris's call |
| 20 | Agree on audio | No audio exists yet | **DEFERRED (named)**: no audio track scheduled this epic |
| 21 | Wants a full-feedback prompt for a fable-model review session | — | **Deliverable G**: docs/review-prompt-round3.md |

## Live-verify list for round 4 (can't be proven headless)

- Enemy corner steering FEEL (the 0.35s knob) around fence posts + camp props.
- Door-loop walk into every relocated door (bot only proves cottage A).
- Lamp/walkway look at all 7 doors on the real render.
- Y-sort: stand directly below/above chicken, cow, capybara.
- Furniture collision in all 7 interiors; exit mats still reachable.
- Fade retry: sprint straight down from an interior spawn — must re-exit, never void.
