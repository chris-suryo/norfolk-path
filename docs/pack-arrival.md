# When the full Cute Fantasy pack lands — morning checklist

Chris bought the **$2.99 full Cute Fantasy pack** (horse, stables, barn, ~52
buildings, same style). This is the concrete sequence for the build session once
the new art is committed. Nothing here needs guessing — it mirrors how we
decoded and wired the free pack's sheets.

## 0. Get the art into the repo (Chris, on Windows)
- Unzip the pack. **Delete any `__MACOSX/` folder and `._*` files** (macOS junk,
  like the duck download had).
- Commit the new art under `assets/` (e.g. `assets/cute_fantasy_full/…`), push.
- Tell the build session it's in and roughly where the buildings / horse live.

## 1. Decode the new sheets (build session)
- Grid-overlay the new building sheet(s) and the horse sheet with the scratchpad
  `pnglib` helper (same as we did for `Outdoor_Decor_Free.png` and the animals).
- Catalogue: which buildings we want (at minimum a **shop-ish** building and a
  **library-ish** building that read as *different* places), the horse frame
  layout, and any new decor worth using.

## 2. Add symbols to the preview tool
- `tools/preview_map.py`: give the new buildings their own symbols (e.g. keep
  `H` = Evan's shop building, make `L` = a *distinct* library building instead
  of reusing the house), and add a horse symbol (e.g. `k`). Regions from the
  decode. Update the legend in `docs/level-design.md`.
- This retires the brief's "reuse the same house for both" workaround — we can
  now differentiate the shop and the library by **building**, not just position.

## 3. Re-render the chosen cove variant
- Chris will have picked one of `cove3-rich-{1,2,3}`. Swap its `H`/`L` to the new
  building symbols, drop a **horse (`k`) near Ariana's pond / the reading
  garden**, re-run `python tools/preview_map.py --map … --out …`, and confirm it
  reads well. Iterate a touch if needed.

## 4. THEN apply it live (the real build slice — the big one)
This is the step that's been deferred all along; it's now unblocked once a
variant is chosen:
- Drop the chosen `.txt` into `scripts/island_map.gd`'s `MAP`.
- Teach `scripts/level.gd` the farmland terrain (`D`) autotiling (mirror the
  Python mask logic already proven).
- Teach `scripts/main.gd` to spawn every prop/entity symbol with a sprite +
  collision choice: buildings (collide), horse/cow/pig/sheep/chicken (decide —
  probably no collision, or a small one), lamp/sign/chest (collide, thin),
  trees/fences (already done), rocks (collide), stumps/flowers/wildflowers/
  wheat/mushrooms/veg (no collision, pure decoration).
- Keep it y-sorted under the `World` node so the player walks in front of/behind
  props correctly.
- Chris verifies: headless import clean → Web export → serve → hard-refresh →
  walk the real island in the browser.

## Note
Don't start step 4 until Chris has (a) picked a variant and (b) committed the
pack — doing it against the free pack's single building would just be redone.
See `docs/roadmap.md` for where this sits in the overall v1 plan.
