# Map rulebook — the constitution for world generation

Every rule here exists because a real playtest or audit finding created it (provenance
column). Rules are **[HARD]** (machine-checked in `tools/check_map_rules.py` /
`tools/check_assets.py` — CI fails on violation) or **[SOFT]** (judged by the vision review
against rendered composites — see the checklist below). New findings that reveal a bug
CLASS get promoted into this file and, when mechanically checkable, into the checkers —
that is how the loop improves itself (`docs/testing-loop.md`).

The generator (`tools/worldgen/`) must produce maps that pass every HARD rule at
generation time and are reviewed against every SOFT rule before a human ever looks.

## HARD rules (CI-enforced)

| # | Rule | Checker | Provenance |
|---|---|---|---|
| H1 | Water / path / farm regions are >= 2 tiles wide everywhere | preview_map validate | edge sheets have no 1-wide strips (slice 1) |
| H2 | Every map symbol has a handler (prop table / terrain / fence) | check_symbols + main.gd assert | blank-grass bug (apply-live) |
| H3 | Every referenced asset exists and is exportable | check_assets | web-build trim guard |
| H4 | ANIMAL_ANIM frame indices fit their sheet (frame_size honored) | check_assets | chicken 6-frame walk on a 4-frame sheet (bot log, round 1); butterfly 2x2 block (round 2) |
| H5 | Every beehive hangs from an adjacent tree | check_map_rules | floating hives (map audit M3) |
| H6 | Small cobble groups (<=4 cells) sit within 2 cells of a building | check_map_rules | orphan doorsteps (M2) — vacuous since round-2 removal, armed against regressions |
| H7 | Singleton props stay singleton (chest, well, windmill, tent, library, stall, spawn) | check_map_rules | census (map audit) |
| H8 | No floating fence fragments (every F/\| touches its family) | check_map_rules | picket fragments (M4) + 4 strays the checker itself caught |
| H9 | Decor mushrooms keep Manhattan >= 10 from the bombschroom spawn | check_map_rules | enemy-tell ambiguity (round 1) |
| H10 | Every connected path region contacts >= 2 distinct POIs (a road goes from somewhere TO somewhere) | check_map_rules (new) | road dead-end / unpathed library (M1) |
| H11 | No straight line of >= 5 identical decor symbols (grid artifacts) | check_map_rules (new) | flower-column artifact (M13 class) |

## SOFT rules (vision-review checklist — applied to composites before any human look)

| # | Rule | Provenance |
|---|---|---|
| S1 | Density gradient: dense dressing at POIs, sparse in transit; no uniform carpet | map audits |
| S2 | Variety: groves mix species; repeated sprites vary via flips/palette (oak flips M12, villager clones M10) | round 1+2 |
| S3 | Negative-space budget: breathing room is fine, DEAD space is not — no unreachable or purposeless bands inside the play area | Chris round 2 ("top/bottom never seen") |
| S4 | A landmark or draw is visible roughly every 1.5 screens along the golden path | pacing (combat-slice) |
| S5 | Clustering with purpose: props tell mini-stories (trough+hay+animals; campfire+tent+stumps), never random salt | audits |
| S6 | Paths curve like desire lines; long straights only with framing that makes them read intentional (the lamp-lined library avenue) | M1 + avenue design |
| S7 | Shores/banks meander organically; no square notches or perfect arcs | M9 |
| S8 | Every building reads inhabited: door faces sensibly, yard tells a story, no floating steps | M2 |
| S9 | Palette cohesion per biome; accent colors used sparingly | pack design |
| S10 | Nothing overlaps illegibly at gameplay zoom (640x360): enemy tells, beacons, NPCs distinct | beacon/scarecrow + bombschroom findings |

## Biome asset tables (the pluggable part)

A biome = a symbol->sheet table + terrain palette + dressing vocabulary. The generator is
biome-agnostic; only the table changes.

- **valley** (live): the `island_map.gd` legend — grass/path/water autotiles (free pack),
  oak/birch/spruce/fruit trees, village buildings A/G/J/E/Y/L/H, farm D/Q, fences F/|,
  decor w/f/m/&/r/u, cast N/$/C/^/d/U/R/j/y/h/o/p/e, water-set O/k/@/a/l.
- **beach-cove** (next): Beach_Tile + main `Tiles/Beach` (complete), cliffs
  (`Cliff_Tile`), water/waterfall, boat/chest/reeds; palms absent in temperate pack —
  dressing comes from rocks/driftwood/reeds/fishing props. Cast: waterfowl, capybara, crab
  (check sheet), Fisherman Fin NPC.
- **interior-home** (prototype LIVE — the cottage): `Buildings/Houses_Interiors`
  walls/floors + `House_Decor` (~28 furniture sheets: beds, tables, chairs,
  bookshelves, kitchen, fireplaces, carpets, windows, doors, lamps). Not gdignored.
  Small fixed-size rooms; furniture placed as mini-stories (bed+rug+fireplace).
  Baked by `tools/bake_interior.py` (emits the collision map `.gd` + the ground
  PNG together). **Interior maps are EXEMPT from the outdoor HARD rules** (H1
  ≥2-wide, shoreline/beehive/fence/path-POI rules): 1-tile walls and furniture
  stories are the norm, not violations. They are NOT run through
  `check_map_rules.py` / `preview_map.py` (see `ci.yml`); `check_symbols.py`
  still covers them (every registered level). Walls collide by reusing the water
  tile source (`level.gd.terrain_of`, "X"); the baked PNG carries all visuals.
- **library-interior** (later): dungeon/stone walls + bookshelves — Irene's library inside.
- Full standalone libraries on disk (gdignored, copy-out per `docs/pack-arrival.md`):
  desert, dungeon x2, shroomlands, cave, volcano, autumn. NOT buildable: winter,
  military camp (props only, no ground tiles).

## Generation pipeline (who checks what, when)

```
brief (JSON: zones/POIs/paths/water/density, seed)
  -> worldgen passes (layout -> terrain -> paths -> POI stamps -> Poisson/noise scatter)
  -> inline HARD-rule validation (fail = candidate discarded before render)
  -> composite render (preview_map.py, unchanged)
  -> vision review against SOFT rules (scored)
  -> gallery of the best 3-5 -> Chris picks
  -> bake + register + CI + playtest bot (the standard loop)
```

Established algorithms used deliberately (not reinvented): Bridson Poisson-disc sampling
for even-but-organic scatter; low-frequency value-noise density fields for meadows/groves;
constructive shapes + erosion cleanup (existing `fix_water`) for autotile-safe water;
jittered control-point paths for desire lines. WFC noted as a later option for terrain
texture only — our constraints are semantic and live in validators, which WFC cannot express.
