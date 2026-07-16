# Map visual audit — round 1 (side-channel)

Companion to `docs/playtest-findings.md` (PR #5), produced by the local session while
the fix slice is in flight. Method: `tools/preview_map.py` rendered at scale 3 into
14 overlapping inspection tiles (7 columns × 2 rows, 4-tile overlap), each inspected
closely; plus a mechanical pass over the `island_map.gd` ASCII grid (symbol census,
adjacency checks); plus cross-reference against the round-1 in-game screenshots.
Evidence tiles are in `docs/playtest/map-audit/` — coordinates below are **map cells**
(192×48 grid, 16px tiles), so they can be found in `island_map.gd` directly.

This is observation only. No map data was touched. Ranked worst-first within each
section. Items already in PR #5 (bridge parapet stickiness, tent rock pocket, road
dead-end, bombschroom readability, beacon/NPC confusion) are not repeated here except
where this audit adds new information.

## Corrections to PR #5 findings (important)

1. **The library EXISTS.** PR #5 said no library was observed near the boss arena. It
   is there — a large manor at cells ~(150–170, 6–15), symbol `L` anchor at (162,17),
   north of the boss arena, off-camera during the fight. See `tile-r0-c5.png`.
   The real issue is different: **nothing connects it** (finding M1).
2. **"Twin cloned villagers" at the west road end — retracted.** The pair at ~(6,25)
   in composites is `preview_map.py` rendering the player spawn `S` as two villager
   sprites. In-game the players spawn there; no NPC clones exist at that spot.
   (Tool nit: spawn could render as a distinct marker to avoid this misread.)

## New findings — layout / composition

### M1 — Road dead-ends pointing at nothing; library is unpathed
- Cells: road terminus ~(168–174, 24–27); second stub ~(145–147, 27–29); library door
  ~(160,15) with its orphan doorstep at ~(163,17).
- Observed: the main road's eastern end is a blunt rectangle in open grass ~15 tiles
  short of the map edge, and ~10 tiles SOUTH of the library the entire road exists to
  reach. A second stub ends mid-grass near the boss checkpoint. The library's entrance
  opens onto bare grass; its stone doorstep is a floating patch offset SE of the door.
- Suggested fix: turn the road terminus north into a short approach that meets the
  library doorstep (data-level path tiles only, no layout reshaping); alternatively
  end the road at a deliberate terminus prop (gate/plaza). This one change resolves
  the PR #5 "road stub" finding, the library disconnect, and gives the boss arena a
  reason to be where it is.
- Evidence: `tile-r0-c5.png` (library + doorstep), `tile-r1-c6.png` (terminus),
  `tile-r1-c5.png` (second stub) + in-game `docs/playtest/round-1/boss-seq3.png`.

### M2 — Doorstep/walkway stubs are systematically disconnected from doors and road
- Cells (all `cc` cobble pairs): (21,18-ish) green cottage, (44,18) cottage E,
  (31,21) cottage A annex, (163,17) library, plus barn (66-67,?) — every building
  except Evan's shop (which has a proper step under its door).
- Observed: 2×1 stone patches sit 1–2 tiles south or south-east of the actual door
  tile, floating in grass, connecting to nothing. They read as random stone litter
  rather than steps; no building has a path from door to road.
- Suggested fix: align each `cc` pair directly under its door tile and (where cheap)
  run 2-wide path tiles from doorstep to the road. Pattern-level fix in
  `tools/gen_valley.py`'s building stamping, or hand-adjust the few sites in
  `island_map.gd` if the generator stays frozen.
- Evidence: `tile-r0-c0.png`, `tile-r0-c1.png`, `tile-r0-c5.png`.

### M3 — Both beehives hang in mid-air (mechanically confirmed)
- Cells: (11,7) and (52,33). Neighbor scan shows **no tree within 1 tile of either**
  (neighbors: hay bale + butterflies; butterflies only).
- Observed: the hive sprite is drawn dangling from a branch that isn't there.
- Suggested fix: move each `%` one tile so it overlaps a tree canopy/trunk cell, or
  swap sprite to the ground `Bee_Nest` variant.
- Evidence: `tile-r0-c0.png` (11,7 — top-centre), `tile-r1-c1.png` (52,33 — right of
  the red-roof house).

### M4 — Fenced pens don't visually enclose; fence fragments float
- Cells: cow/pig pen ~(24–39, 34–40) — south run hidden/absent behind the border tree
  canopies; horse pen ~(40–47, 36–42) — west side open toward the sheep pen and south
  side relies on trees; decorative picket runs at ~(31–37, 27) stand alone in grass
  with a gap between segments, attached to nothing.
- Observed: every animal pen reads as open on at least one side. Gameplay-wise the
  animals stay put, so this is visual, but it's one of the strongest
  "generated, not gardened" tells in the west village.
- Suggested fix: close the pen rectangles (fence symbols where trees currently imply
  the edge), and either extend the floating picket runs into an actual yard around
  the flowerpots/dog or delete them.
- Evidence: `tile-r1-c0.png`, `tile-r1-c1.png`, plus PR #5's west-village shots.

### M5 — Well plaza is a large empty cobble slab
- Cells: cobble rectangle ~(14–23, 24–27) with well `W`(16,24), bench `b`(19,24),
  lamp, and a stone slab prop; the remaining ~30 cobble tiles are bare.
- Observed: the village's central plaza has its furniture crowded into the top edge
  and two-thirds empty stone — looks like a placeholder awaiting a centerpiece.
- Suggested fix: either shrink the cobble to hug the well/bench, or dress the space
  (market crates/barrels — `3` symbol already exists, flower pots, a second bench
  facing the well).
- Evidence: `tile-r1-c0.png`.

### M6 — East-of-library region is conspicuously empty
- Cells: roughly (168–192, 4–24) — the entire NE quadrant beyond the library.
- Observed: after the densest set piece on the map (library manor), the map just
  peters out: sparse single trees, a handful of flowers, thin top border. Every other
  region is generously dressed; this corner reads unfinished, and it's where the
  player lingers after beating the boss.
- Suggested fix: thicken the forest border to match the rest of the map edge and add
  a modest vignette (this is the natural site for the deferred cove/dock idea —
  recorded as compatible with, not blocked by, that decision).
- Evidence: `tile-r0-c6.png`.

## New findings — smaller polish

### M7 — Windmill reads broken/unfinished
- Cell: `z`(56,39). The tower renders with slat-like sails on one side only; at a
  glance it looks like a damaged sprite rather than a mill. If the source sheet has
  an animated/complete sail frame, prefer it; otherwise consider swapping the prop.
- Evidence: `tile-r1-c1.png` (right edge).

### M8 — Camp props overlap: stump on the tent pole
- Cells: tent `s`(118,34) with camp-prop/stump cluster at (119,33)–(120,34).
- Observed: a stump sprite overlaps the tent's right pole; with the rock pile on the
  left pole this is also the collision pocket from PR #5. One prop-shuffle fixes the
  visual overlap and the wedge trap together.
- Evidence: `tile-r1-c4.png`, in-game `docs/playtest/round-1/bombschroom-leg2.png`.

### M9 — Riverbank/lakeshore meanders have squared "machine" notches
- Cells: river bulges around (73–76, 10–13) and (72–75, 30–33); lake NW corner
  ~(146–150, 31–33); lake south shore has zero reed dressing while the north shore
  is fully reeded.
- Observed: rectangular single-tile notches in an otherwise organic bank, and
  asymmetric shore dressing, are mild generator tells.
- Suggested fix: knock the 1-tile notches off (2-wide rule still satisfied); scatter
  a few reed clumps on the south shore.
- Evidence: `tile-r0-c2.png`, `tile-r1-c6.png`.

### M10 — One villager sprite plays four different people
- Cells: `N` at (63,19) stall vendor, (166,20) library chest attendant, (156,29)
  boss-lake bystander, (46,30) west-road walker. All render identically (straw hat,
  blue overalls) — and the checkpoint-beacon scarecrow shares the same silhouette,
  which is exactly why PR #5 kept mistaking beacons for NPCs.
- Suggested fix: the pack ships other villager palettes (Chef Chloe et al. are
  already imported as assets) — differentiating even 2 of the 4 breaks the clone
  effect. Pairs well with the planned beacon-distinction fix.
- Evidence: `tile-r0-c2.png`, `tile-r0-c6.png`, `tile-r1-c5.png`.

### M11 — Boss-arena bystanders undercut the fight
- Cells: villager `N`(156,29), frog `R`(157,29), Ariana `$`(163,29), goose/ducks —
  all inside the boss activation zone, calmly loitering while Irene throws books.
- Observed: during the round-1 fight these NPCs were repeatedly mistaken for
  players/enemies at 640×360, and tonally they're picnicking in a boss arena.
- Suggested fix: either move the vignette a few tiles east past the arena bounds, or
  lean into it (they're spectators — fine, but then it's a decision, not an accident).
- Evidence: `tile-r1-c5.png`, in-game `docs/playtest/round-1/boss-fight8.png`.

### M12 — Forest texture relies on two oak sprites
- Mechanical check found NO long same-symbol runs (the generator mixes T/t/4/5/6/7
  properly), yet the forest walls still read repetitive because the two oak sprites
  dominate and tile in stair-step diagonals. Data is fine; art variety is the lever.
- Suggested fix (cheap): random horizontal flip on oak instances at spawn, and/or
  sprinkle the birch/spruce ratio up in the densest oak bands (e.g. rows 33–46
  between x 84–140).
- Evidence: `tile-r0-c3.png`, `tile-r1-c3.png`.

### M13 — Flower placement occasionally forms grid artifacts
- Example cells: vertical flower column at ~(176–177, 8–12); similar short columns
  elsewhere. Purely cosmetic, low priority — worth a jitter pass in the generator's
  flower scatter only if it's touched anyway.
- Evidence: `tile-r0-c6.png`.

## Mechanical census (for the fix session's reference)

- Singletons verified unique: chest(165,19), stall(62,16), well(16,24),
  windmill(56,39), tent(118,34), library(162,17). Grape arches ×2 (84,22)/(55,28)
  frame the road properly.
- Decor mushrooms `m` ×4: (106,19), (92,33), (142,34), (122,35) — the last is
  **7 tiles from the bombschroom spawn (117,33)**, same screen at gameplay zoom;
  reinforces the PR #5 readability fix (enemy tell), and/or relocate (122,35).
- Scarecrows `K` ×2 (5,6)/(43,38), both inside crop plots — legitimately decorative;
  the beacon-confusion issue is about the *checkpoint* scarecrow visual, not these.
- Beehives `%` ×2 — both fail tree-adjacency (M3).
- Tool nits found while auditing: `preview_map.py` crashes after writing the PNG when
  `--out` is on a different drive than the repo (`os.path.relpath` cross-drive on
  Windows) — output is fine, exit code isn't; and the spawn marker renders as two
  villager sprites (see correction #2).

## Suggested fix order (if the fix session adopts these)

M1 (road→library) and M2 (doorsteps) are the highest-leverage: they fix the two
"world feels unfinished" tells every player walks past. M3/M4/M7/M8 are one-line prop
moves. M5/M6 are small dressing passes. M9–M13 are taste-level.
