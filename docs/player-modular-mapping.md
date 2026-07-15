# Distinct P1/P2 player sprites — modular sheet mapping (prep, not yet wired)

**Status:** investigation complete, ready for Chris's approval. **Nothing here is
wired into the game** — per the standing rule, the modular player animations must
be verified live (each animation, in-engine) with Chris present, so this is a
mapping + plan for a future focused slice, not a build.

## Why this was previously deferred, and what changed

The distinct-players work was parked because the 64×64 modular sheet had "56
undocumented animation rows" that couldn't be confidently mapped, and recoloring
hair looked unsafe (browns shared with belt/boots). Both blockers are now
resolved:

- The row order was reverse-engineered by pixel occupancy + pose inspection and
  cross-referenced against the pack's dedicated tool overlays (sword/bow/tools/
  fishing-rod sheets have known frame-count signatures that line up with the
  base sheet's blocks). The game-driven animations map cleanly.
- **No recoloring is needed at all** — the pack ships pre-authored per-color hair
  sheets that are frame-for-frame aligned with the body. P1 vs P2 = same body,
  different hair overlay.

## The sheet

- Base body: `assets/cute_fantasy/packs/Cute_Fantasy/Cute_Fantasy/Player/Player_Base/Player_Base_animations.png`
- **576×3584 = 9 columns × 56 rows of 64×64 frames.**
- Direction order within each animation block is **down / side / up**; the side
  row faces RIGHT and flips for left — same convention as the current 32×32
  player (`scripts/player.gd`).
- Frame of (row `r`, col `c`) = `r*9 + c`.

## Row map

Confident (everything the game actually drives):

| Animation | Rows (down / side / up) | Frames | Confidence |
|---|---|---|---|
| Idle | 0 / 1 / 2 | 6 | HIGH |
| Walk | 3 / 4 / 5 | 6 | HIGH |
| Sword attack | 6 / 9 / 12 | 4 | HIGH (block); it's the down/side/up of the first of 3 sword-swing variants — rows 7/10/13 and 8/11/14 are the other two variants |
| Roll / dodge | 17 / 18 / 19 | 8 | HIGH — a *real* roll, replacing the current dash + alpha-flash hack |

Soft (not blocking — the game already fakes both):

| Animation | Candidate rows | Note |
|---|---|---|
| Hurt | — | keep the existing modulate-flash; no dedicated row needed |
| Death | 53–55 (6-frame) or 50–52 (short) | pick live; today it reuses the free-sheet collapse |

Other blocks on the sheet (not game-relevant): rows 26–43 tool/farming + bow,
rows 44–49 fishing, 20–25 misc/jump/pickup.

## P1 vs P2 — hair overlay (no recolor)

Same base body, composited with a different pre-authored hair sheet (each
576×3584, frame-aligned with the body):

- **P1 (black hair):** `…/Player/Head/Hair_1/Hair_1_Black.png`
- **P2 (brown hair):** `…/Player/Head/Hair_1/Hair_1_Brown.png`
- (Hair_1…Hair_6 styles exist, each in Black/Blonde/Brown/Ginger/Grey. Shirts/
  pants/shoes are also aligned layers in many colors if we want extra P1/P2
  contrast beyond hair.)

## Proposed wiring (for approval — a future slice)

- `scenes/player.tscn`: body Sprite2D switches to the 64×64 sheet
  (`hframes=9, vframes=56`); add a child hair-overlay Sprite2D using the same
  frame index, tinted/selected per `player_index` (Black for P1, Brown for P2).
- `scripts/player.gd`: `SHEET_COLUMNS 6 → 9`; remap the row constants to the
  table above; drive the hair overlay's `frame`/`flip_h` in lockstep with the
  body; add a real ROLL animation (rows 17/18/19) in place of the dash+flash.
  Frame size, attack-frame count, and collision/hitbox offsets all shift with
  the larger 64×64 art and need a live pass.
- The player is currently ~32px; going to 64×64 art changes on-screen scale and
  sword/contact offsets — this is exactly why it needs Chris verifying each
  animation and the combat feel live, not a headless wire-up.

## Verification (when built)

Chris drives each animation in-engine per player: idle/walk (all 8 directions),
sword swing (down/side/up + left-flip), roll (i-frames + the new tumble),
hurt-flash, death; confirms P1 shows black hair and P2 brown, aligned to the
body across every frame; and re-checks the sword hitbox/contact offsets at the
new sprite scale.
