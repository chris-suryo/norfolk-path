# Combat slice — real-time sword combat + co-op game loop

Built headlessly across 6 commits (Stages 0–5). This is the **beatable loop**:
player-select → walk the path → fight three encounters → beat Irene → win screen
→ progress persists. Authored lint-clean; **not yet run in-engine** — Chris
verifies on Windows. `scripts/island_map.gd` was untouched the whole slice.

## Controls

| | Move | Attack (sword) | Roll (dodge, i-frames) |
|---|---|---|---|
| **P1** | WASD | Space | C |
| **P2** | Arrow keys | `/` | `.` |

Roll gives brief invulnerability — the intended way to dodge Irene's books.
Keys are exported in `project.godot` `[input]`, easy to rebind.

## First run on Windows (fresh assets need one import pass)

New sprites live in `assets/game/` **without** `.import` siblings (the cloud
session can't run Godot to generate them). So:

1. `godot --headless --editor --path . --quit`  ← generates `.import` for
   `Duck.png`, `Chef_Chloe.png`, `Irene.png` (and imports everything).
2. `godot --path .` — you land on the **player-select** screen (1P/2P).
3. Walk east: 2 slimes near spawn, a skeleton by the shop, then Irene at the
   pond/library. Roll through her books, sword her down.
4. Win screen → Enter → back to player-select.
5. **Save test (do this on a real Web export, not the editor):**
   `godot --headless --path . --export-release "Web" export/web/index.html` →
   serve → reach a checkpoint → refresh → you should resume there. Local save is
   `localStorage` on web, `user://save.json` on desktop.

Commit the generated `assets/game/*.import` files afterward so CI / a fresh
clone doesn't have to regenerate them.

## What to tune (all exported / one file)

- **Player feel:** `max_speed` / `acceleration` / `friction` / `max_hp` /
  `attack_damage` on `scenes/player.tscn` (Inspector).
- **Enemies:** `max_hp` / `move_speed` / `contact_damage` on
  `scenes/enemy_slime.tscn`, `enemy_skeleton.tscn`.
- **Boss:** `max_hp` (36) / `throw_interval` (1.7) / `move_speed` on
  `scenes/boss_irene.tscn`; her three lines are exported strings there too.
- **Encounter + checkpoint positions:** the cell coordinates in
  `scripts/encounter_manager.gd` `_build_areas()` — first-pass placements on
  real walkable cells; nudge in playtest.

## First-pass guesses most likely to need a nudge

- Enemy / checkpoint / boss **positions** (picked by reading the ASCII map, not
  seen in-engine).
- Sprite **offsets**: the Duck (Ariana) and Irene are 64px sheets on a 16px
  world — `offset` may need tweaking so feet sit on the ground.
- Irene's **frame layout**: her stand-in sheet (Bartender_Katy, 6×7) is animated
  as idle row 0; if a row looks wrong, adjust `anim_frames` / `anim_fps`.
- **HP balance** — first cut; make the fight feel right.

## Deferred / gated (NOT in this slice, by design)

- **Boss Phase 2** (low-HP minion summons) — gated: verify Phase 1 feels good
  first, then say the word.
- **The cove world swap + pack buildings/terrain** (distinct shop/library
  buildings, richer tiles) — still gated on your cove-variant pick
  (`docs/pack-arrival.md`). Combat was built world-agnostically on the current
  placeholder map; the library is a zone by the pond, not a building yet.
- **Distinct modular Chris/Erin/Irene sprites** — both players use `Player.png`
  for now; Irene is the Bartender_Katy stand-in. Real characters come from
  Kenmi's Player Generator (an art step).
- **Real roll / 3-stage combo animations** — the free sheet has neither, so roll
  is a dash+flash and attack is a single swing; both arrive with the premium
  player sheet.
- **UI-kit dressing** (bars/buttons/font) and a **book sprite** — placeholders
  (ColorRect bar, Polygon2D book, plain Labels) for now.
