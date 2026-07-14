# Candidate island layouts

**Round 3b (current): more textures, fewer trees/rocks.** The `cove3-rich-*`
renders now use the pack's fuller texture set — **plowed farmland fields**, a
grass pasture with animals, **signs**, wheat, mushrooms, lamp-lit path — with
tree/rock density dialed back so the island reads as varied, not just wooded.
For BUILDINGS and a HORSE (not in the free pack), see
[`../asset-sourcing.md`](../asset-sourcing.md) — short version: the $2.99 full
Cute Fantasy pack has a horse, stables, a barn, and ~52 buildings in this exact
style.

**Round 3 (below): cove-3 enriched — variety, density, animals, character.**
Chris picked cove-3 and asked to fill it with detail aligned to the story. These
build on cove-3's geography (lagoon, library peninsula, fenced garden campus,
single 2-wide crescent path) and add the pack's wider art set — animals, lamp
posts, rocks, stumps, wildflowers, garden flowers, a veg patch, a chest. Pick
one (or mix). NOTE: making the winner *live* is a bigger build step than before
— `main.gd`/`level.gd` must learn every new prop symbol (sprite + collision).

## cove3-rich-1 — Balanced (recommended) (`cove3-rich-1.png`)

Every zone dressed without tipping into clutter: a calm, lamp-lit spawn; one
tidy fenced farmstead (cow, sheep, pig, a carrot patch) giving the "old-world
village" the Subway joke plays against; lamp posts lining the path east toward
the library; a lush reading garden (flowers, corner lamps, a chest) at the
climax; rocks along the shore, stumps and wildflowers breaking up the woods.

## cove3-rich-2 — Pastoral Village (`cove3-rich-2.png`)

Leans into settled farmland: **two** fenced plots near the start — a livestock
pen (cows, sheep, pigs) and a carrot field — so the island reads as a small
working homestead. Lamp-lit path, modest library garden. The most
"people-live-here" of the three.

## cove3-rich-3 — Wild Garden (`cove3-rich-3.png`)

No farm pens — a quiet, overgrown, naturalistic island: dense trees, heavy
rocks/stumps/wildflowers everywhere, and the richest, most flower-filled reading
garden at the library. Ariana's pond feels like a secret clearing at the end of
a wild path. The calmest and most atmospheric; least "villagey."

---

# Round 2 (history): cove refinements.

** Chris picked the **Option C / lakeside**
direction, with notes: make the cove *bigger + smoother + pushed further east*,
and *populate the island more*. Three refined variants below — review
`cove-1/2/3.png` and pick (or send more notes for another round). Round 1
(`option-a/b/c`) is kept below for history.

## cove-1 — Open Smooth Bay (`cove-1.png`)

A large, clean-edged bay biting in from the east; the library sits on a point at
the water with a small reading-garden fence. Balanced, evenly-wooded island —
the calmest read, the cove itself doing the "you've arrived" work. Smoothest
shoreline of the three.

## cove-2 — Enclosed Cove (`cove-2.png`)

The biggest, most *enclosed* cove — a south land-arm wraps under the water so it
reads as a sheltered curve rather than open sea, and the island is heavily
forested throughout. The path threads a denser wood to the library point; the
most lush and secluded feel.

## cove-3 — Lagoon & Garden Campus (`cove-3.png`)

A lagoon with the library on a broad peninsula ringed by a fenced "reading
garden campus" (two garden plots) — the most *populated*, settlement-like
climax. Densest decoration; the library area reads as a real place, not just a
building. (Trade-off: the busiest, so the calm-spawn contrast is a touch weaker
than cove-1.)

---

# Round 1 (history) — pick one

Three full-island layouts for the Norfolk Path quest (`docs/world-brief.md`),
each rendered from its own ASCII source. All are the same fixed story: calm
west **spawn** → Evan's **shop** mid-path → the path continues east to the
**library** beside the **pond**, with Ariana (chicken stand-in) at the water's
edge. All are single, non-branching, 2-tile-wide paths and validate clean.

Review the three `.png`s and pick one. They differ in *how* they apply the five
design principles (landmark-before-arrival, readable walkable/not, pond
foreshadowing, calm→climax density gradient, one clear path).

## Option A — Straight Pilgrimage (`option-a.png`)

A dead-straight east–west avenue with the library as the vanishing point at the
far end — the **landmark is a clear sightline**: stand at spawn and the path
runs unbroken to the library's door, trees kept off the corridor so the rooftop
is always visible ahead. Density is a formal, near-symmetrical scatter that fills
the whole island, with a fenced "cloister" garden framing the library and pond.
Reads as processional and deliberate — you can always see exactly where you're
going.

## Option B — Winding Approach (`option-b.png`)

A chunky S-bend that **hides and reveals**: the path leaves the calm, sparse
spawn, dives south through a dense middle woods (where the library is out of
sight), then climbs back north to reveal the library at the pond clearing. The
landmark works by *absence then arrival*, and the density gradient is the
strongest of the three — empty west, thick forest core, open climax. The most
dramatic and exploratory-feeling, while still being one fixed route.

## Option C — Lakeside Crescent (`option-c.png`)

Water-forward: a lake bites into the east and the path **hugs the shore in a
crescent**, curving south and back up so the library sits on a point jutting
into the water — the **landmark is the water itself** opening up as you head
east, with the library framed against it. Inland west is dry and sparse; a grove
thickens around the lakeside library. The calmest, most scenic of the three, and
the one where the pond reads as the emotional focal point the brief asks for.

## Applying the pick

Each `.png` has a matching `.txt` (its exact ASCII map). To make the chosen one
live, its `.txt` becomes the `MAP` const in `scripts/island_map.gd`. Note: the
maps use a new `L` symbol for the library (a second building) — a small build
follow-up will add `L` handling to `scripts/level.gd` and `scripts/main.gd`
(they currently know only `H`). Regenerate any preview with
`python tools/preview_map.py --map <file> --out <file>`.
