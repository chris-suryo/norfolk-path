# Playtest checklist — one clean pass

Everything built while Chris was away, ordered as a single playthrough so you can
run top-to-bottom in one sitting. All of it is pushed on
`claude/slice-1-godot-toolchain-ij6e9w` and lint/asset-checked, but none of it
has been seen in-engine — the sandbox has no Godot. Each item notes the **tuning
knob** if it plays wrong, so you can adjust without a round-trip.

Import the project fresh (re-import so the font change takes) before starting.

---

## 0. Font sanity (cross-cutting — glance at every screen)
- [ ] All UI text is crisp, no smeared/overlapping glyphs (the boss "Icene" bug).
      Applies to the title, pause menu, boss name, HUD.
- **If any text still smears:** the fix is a committed `assets/game/
  CuteFantasy-5x9.ttf.import` (subpixel positioning disabled). If Godot didn't
  honour it, toggle it by hand: select the font → Import dock → **Subpixel
  Positioning: Disabled** → Reimport. (Worst case is cosmetic; nothing breaks.)

## 1. Title screen
- [ ] Dimmed world-slice **backdrop** (a path through meadow) behind a framed
      panel; a **campfire** loops at the top of the panel.
- [ ] Title "NORFOLK PATH" reads cleanly (see font check above).
- [ ] **Keyboard:** up/down highlights, Enter/Space selects — unchanged.
- [ ] **Mouse:** hovering an option highlights it; clicking it activates.
- [ ] **New Game / Continue:** if you have an OLD save it should be auto-
      invalidated (SAVE_VERSION bumped) — you go straight to 1P/2P, i.e. a clean
      New Game. Make a fresh save (below) and confirm **Continue** then appears
      and resumes.
- **Knobs:** backdrop slice = the AtlasTexture region in `player_select.tscn`;
  campfire size/speed = the `Campfire` node scale / `fps`.

## 2. New Game → the world
- [ ] You spawn in the **west village**, nowhere near the forest camp.
- [ ] **Dash** (Space/C roll) feels shorter now (~2 tiles, was ~3). Knob:
      `ROLL_SPEED` in `player.gd` (currently 105).
- [ ] **Animals are alive:** farm animals bob in place; ducks/goose/rooster/
      horse/frog/mouse **idle then slowly wander** a small radius and settle.
      Water fowl + capybaras **bob but never walk onto land**.
- [ ] **Ariana** (pond) is a **single** animated duck — not a static duplicate,
      and not a 2×2 block of four ducks (both were bugs). Knob: her node in
      `main.tscn` / per-animal values in `main.gd` `ANIMAL_ANIM` (radius/speed).

## 3. Collision (walk into things)
- [ ] **No walk-through rocks** anywhere, and **no duplicated/overlapping rock
      clusters** next to houses (both were the removed ore scatter).
- [ ] **Berry bushes** and the **camp keg/barrel** now block you.
- [ ] **Buildings block their whole footprint** — you can't walk through the
      sides of the **inn**, **cottages**, or the **barn** (the façade wings used
      to be passable). Doors are walls too (buildings aren't enterable).
- **Knob:** any collider that's too tight/loose = its `(w,h)` in
  `tools/gen_prop_table.py` SPEC/BUILDINGS → regenerate `prop_table.gd`.

## 4. Forest camp (combat)
- [ ] Camp holds **3 skeletons + 1 bombschroom** (a mushroom).
- [ ] Skeletons wake on approach (not from across the map).
- [ ] **Bombschroom:** sits idle; when you get close it **flashes/swells (~0.6s
      wind-up) then explodes** in an area. You can **defuse it with one sword hit
      during the wind-up**, or **roll clear** of the blast.
- **Knobs (all exported on `enemy_bombschroom.tscn`):** `detonate_radius` (22),
  `blast_radius` (30), `windup` (0.6), `max_hp` (3), `contact_damage` (3).
  Camp mix / skeleton count = `encounter_manager.gd` `_build_areas`.

## 5. Checkpoints & respawn (Slice A — already confirmed; spot-check)
- [ ] Die at the camp → you respawn **on the road just west of it**, not inside
      the fight; skeletons you already killed **stay dead**; survivors reset to
      idle until you re-approach.
- [ ] Reaching a new area auto-saves (progress-based checkpoint).

## 6. Pause menu (Esc — try mid-game)
- [ ] Esc opens the panel and **freezes** the game; Esc/Resume closes + unfreezes.
- [ ] **Keyboard and mouse** both drive it (hover-highlight + click).
- [ ] **Zoom** cycles Far / Normal / Close live; **Save Now** shows "Saved HH:MM";
      **Return to Title** goes to the title (keeps your checkpoint).
- [ ] Panel text is crisp (font check).

## 7. Boss — Irene (library, east)
- [ ] Her **name label reads "Irene"** (was "Icene") and the **HP bar is
      centered**.
- [ ] **Four staged taunts** fire once each: at fight start, **¾ HP**, **½ HP**,
      **¼ HP**; plus the defeat line. Knob: the `*_line` exports on
      `boss_irene.gd`.
- [ ] Dying to her resets her to full HP for the retry.

## 8. Web build (optional — load-time sanity)
- [ ] Export size is smaller than before: the unused base-pack `Player/`,
      `Tiles/`, `Icons/` dirs are now `.gdignore`d (asset payload 4.7 → 2.0 MB;
      the seasonal packs were already excluded). Confirm the game still loads and
      no sprite is missing (the new `tools/check_assets.py` guards this, but a
      real export is the final word).

---

## Not done (need you live — deliberately untouched)
- **Distinct P1/P2 sprites** — mapping ready in `docs/player-modular-mapping.md`,
  assets staged in `assets/game/` (`Player_Modular_Base` + hair overlays), NOT
  wired. Approve the doc and it's a fast slice with you verifying each animation.
- **Boss Phase 2**, and any further feel/tuning — all need you watching.
