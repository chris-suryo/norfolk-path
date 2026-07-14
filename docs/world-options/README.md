# Candidate island layouts — pick one

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
