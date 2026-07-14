# Asset sourcing — getting more variety (buildings, a horse, NPCs)

**The short answer: pay $2.99 for the full Cute Fantasy pack.** Everything you
asked for — a horse and lots of varied buildings — is already in the *same pack
we're using*, in the *exact same art style*, just behind the paid unlock. That's
the zero-mismatch path.

> Sourcing note: itch.io pages are blocked from the cloud build session (403
> through the proxy), so the details below come from web-search snippets, not
> live page reads. **Re-verify prices and license wording on the live pages
> before buying.** Chris downloads on his Windows machine (as with the free pack
> + duck) and commits it; the build session then wires it into the map.

## 1. Cute Fantasy (full) — Kenmi  ⭐ recommended

- **URL:** https://kenmi-art.itch.io/cute-fantasy-rpg  (same page as the free tier)
- **Price:** pay-what-you-want; **$2.99 unlocks the full version.** Future updates
  free after purchase.
- **What it adds over the free tier:**
  - **Buildings — a lot:** ~52 houses (4 house types × 8 variants: different
    roofs / abandoned), plus **construction stages** (logs → frame → walls →
    finished), a **barn**, and **horse stables** (two roof variants). This fully
    solves "varied buildings" — Evan's shop and the library could finally be
    *different* buildings.
  - **A horse — confirmed.** Full animal set is ~7: **Horse**, Cow, Pig, Chicken,
    Sheep, Bee, Capybara. Directly fills the horse gap, same style.
  - More decoration (flowers, rocks, foliage, torches, lanterns, furniture) and
    reworked player/character animations.
- **NOT included:** townsfolk **NPC characters** — Kenmi sells those separately
  ("Cute Fantasy — Characters"). Budget a second pack later if Irene/Evan/Ariana
  want unique human sprites instead of recolored players.
- **License:** free tier = non-commercial; **the $2.99 version grants commercial
  use.** Redistributing/reselling the *raw art* is still forbidden (using it in
  the game is fine) — same as now.

**This is the move.** $2.99, no blending work, horse + stables + barn + 52
buildings in our exact palette.

## 2. Style-matching supplements (optional)

| Pack | URL | Price | Adds | License |
|---|---|---|---|---|
| **Sprout Lands** (Cup Nooble) | https://cupnooble.itch.io/sprout-lands-asset-pack | free non-comm / **$3.99+** comm | Cozy 16×16, very close style; more farm buildings + tiles + animals. **No horse.** | no resale/redistribution even if modified |
| **Mystic Woods** (Game Endeavor) | https://game-endeavor.itch.io/mystic-woods | PWYW (free demo + paid full) | Cute 16×16, buildings **+ interiors**, characters/slimes. **No horse.** | commercial on paid tier — verify the no-redistribution clause |
| **Horse Sprite w/ Rider** (Onfe) | https://onfe.itch.io/horse-sprite-with-rider-asset-pack | **free** | Dedicated horse + rider, 4-dir idle/walk/run | commercial OK, **credit required**. ⚠️ style/scale may not match Kenmi — likely needs recolor/downscale |

*Rejected:* **Tiny Swords** (Pixel Frog) — lovely but 64×64 RTS scale, no horse;
wrong tone for a cozy 16×16 RPG.

## How adding a pack works (the workflow)

1. Chris buys/downloads on Windows, unzips, and **commits the art** under
   `assets/` (watch for macOS `__MACOSX/._*` junk — delete it, like the duck).
2. Tell the build session what landed; it decodes the sheets (like we did for
   the decoration/animal sheets), adds symbols to `tools/preview_map.py` +
   `docs/level-design.md`, and can re-render options using the new buildings/
   horse.
3. When a final layout is chosen, those symbols also get wired into
   `scripts/level.gd` + `scripts/main.gd` to appear in the actual game.

## Recommendation

Buy the **$2.99 full Cute Fantasy** pack — it's the whole wishlist (horse,
stables, barn, 52 buildings) in-style with no reskin. Add **Sprout Lands** later
only if you want even more building variety. Skip the mismatched horse packs
unless you specifically want a different horse look.
