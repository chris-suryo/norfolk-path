# Story-session handoff — the full arsenal + the decisions we need

**How to use this file:** paste everything under the `═══ PROMPT ═══` line into
the story/planning chat. Then **upload the contact-sheet PNGs** from
`docs/asset-previews/` so that session (if it's vision-capable) can *see* the
sprites — or so you can eyeball them while it writes. Filenames in the prompt
match the sheet names exactly, so the mapping is unambiguous even without upload.

**Which images to attach** (priority order):
`cast.png`, `animals.png`, `buildings.png`, `player_hair.png`, `ui.png`,
`enemies.png`, `tiles.png` — those cover every casting/world decision below.
The rest (`trees`, `crops`, `decor`, `interiors`, themed `pack_*`) are optional
texture references.

---

═══ PROMPT ═══

You're the story/design lead for **Norfolk Path**, a cozy top-down pixel-art
RPG (Godot, HTML5, solo or local 2-player). The build session has finished
cataloging our full art library — the paid **Cute Fantasy** pack plus
companions, ~1,220 sprites. Below is the **complete inventory of what we can
actually put on screen.** I need you to design the v1 world and cast against
**only** what exists here (no "we'll need an asset for X" — if it's not listed,
it's not available). Where I attach contact-sheet images, they're named to
match the categories below.

## The story we've locked
- **Setting:** a small cozy lakeside cove — grass, a pond, paths, a few
  buildings. Norfolk Path.
- **Evan** runs a modern **Subway-style sandwich shop** (the anachronism is the
  joke) on the island.
- **Irene the librarian** is the antagonist/boss: she turned **Ariana into a
  duck** over an unreturned *"Peep and the Big Wide World"* DVD. She's a human.
- **Ariana** is now a **duck** living at the pond.
- **v1 scope (hard limit — do not exceed):** player-select (1 or 2 players) →
  walk through ONE hand-built level → talk to a few NPCs → beat ONE boss
  (Irene) → win screen → save. That's the whole game.

## Scope rules (the build session will hold you to these)
- **~5 total dialogue lines**, hardcoded — NOT a dialogue system, NOT branching
  trees. Write the actual handful of lines.
- Combat = **HP + one attack, real-time**. No turn queue, menus, skills, or
  items. One fight.
- One level, one boss, one win screen. Anything past that is v2 — name it as
  v2, don't design it into v1.

## THE ARSENAL — everything we own

### Humans, ready-made (sheet: `cast.png`) — folder `NPCs (Premade)/`
8 finished 64×64 townsfolk (idle + walk, 4 directions):
`Bartender_Bruno` (bald, apron), `Bartender_Katy` (dark hair, apron),
`Chef_Chloe` (chef hat, orange hair), `Farmer_Bob`, `Farmer_Buba`,
`Fisherman_Fin`, `Lumberjack_Jack`, `Miner_Mike`.

### Custom humans, build-a-character (sheets: `player_hair.png`, `player_outfits.png`)
A modular paper-doll — stack base + hair + shirt + legs to make ANY human
(this is how we'd make a distinct **Irene**): body base, **Hair_1–6** (~8 colors
each) + plate helmets, shirts (**Farmer / Lumberjack / OG / Royal / Plate**, full
colorways), legs/feet/hands/accessories, tools (bow, fishing rod, axe/pick/hoe),
and a **rideable horse**.

### Fantasy fighters (sheet: `pack_characters.png`) — for a real fight/guards
14 combat 64×64 chars: **Angels** (light + dark), **Goblins** (archer/maceman/
spearman/thief), **Knights** (archer/spearman/swordman/templar), **Orcs**
(archer/chief/grunt/peon). Irene's a human so probably not the boss — but here
if you want an escort, minion, or a different fight.

### Enemies (sheet: `enemies.png`)
**Skeleton** (swordman / bowman / mage), **Slime** (big/medium/small × blue,
green, pink, red, yellow), **Bombschroom** (exploding mushroom).

### Animals (sheet: `animals.png`) — 13 species, most in several colors
**Duck** (= Ariana; yellow + mallard), **Horse** (~6 colors), Chicken, Cow,
Pig, Sheep, **Goose**, **Swan**, **Frog**, **Capybara** (sits in water — great
pond centerpiece), Mouse, Bee, Butterfly.

### Buildings (sheet: `buildings.png`)
Houses (wood/stone/limestone). Unique silhouettes: **Market_Stalls**
(striped-awning food stalls — the obvious Evan's-shop), **Inn** (big landmark),
**Church** (steeple landmark), **Fisherman_House**, **Blacksmith_House**,
**Barn**, **Coop**, **Silo**, **Windmill** (animated), **Greenhouse**, **Shed**,
**Tent**. (Interiors like bookshelves/beds exist too, for a later indoor scene.)

### Terrain (sheet: `tiles.png`) — all auto-tiling
Grass (several shades), Water (+ shore edges), Waterfall, Path, Cobble road,
Beach/sand, Cliff (stone walls), Cave, Farmland (tilled soil), Bridges (wood +
stone), hedges, pavement, wooden deck.

### Nature & props (sheets: `trees`, `crops`, `decor`, `decor_anim`, `weather`)
Trees (birch/oak/spruce/fruit × big/med/small), fruit trees + berries + grapes +
veg rows, fences (wood/white/stone), flowers (many colors), fountain, well,
benches, boat, hay bales, lanterns/posts, signs, scarecrows, barrels, ores,
nests; animated flowers/grass/water/torches; rain, clouds, wind.

### UI kit (sheet: `ui.png`) — covers every menu/HUD we need
HP-style **bars** (boss health), **speech/pop-up panels** + **book UI**
(dialogue), **buttons + selector arrows** (player-select menu), a pixel **font**,
icons (food/tools/resources).

### Themed biome packs (probably NOT this cozy island — flag if you want one)
Desert, Dungeons, ShroomLands, MilitaryCamp, Halloween, Volcano, Christmas —
full alternate biomes. Available, but Norfolk Path is the cozy cove.

## WHAT I NEED BACK FROM YOU

Design v1 against the list above and answer these concretely:

1. **Ariana = the Duck sprite** — confirm (yes/which color).
2. **Evan** — pick his sprite (`Chef_Chloe`, `Bartender_Bruno`, or
   `Bartender_Katy`) and confirm his building is **Market_Stalls** (or name an
   alternative from the buildings list).
3. **The library** — **Inn** or **Church**? And roughly where it sits relative
   to the pond and Evan's shop.
4. **Irene (the boss)** — describe her look so the build session can assemble
   her from parts: hair (1–6 + color), shirt (Farmer/Lumberjack/OG/Royal/Plate
   + color), any accessory/tool. Aim for "warm librarian who turns menacing."
   (Or just pick `Bartender_Katy` if you'd rather use a ready sheet.)
5. **Supporting cast** — which of the 8 townsfolk (if any) to place as flavor,
   and one line of dialogue each.
6. **The ~5 dialogue lines, written out** — e.g. Evan's hook that points the
   player toward the library, Ariana-as-a-duck's line, Irene's pre-fight taunt,
   and the win-screen text. Keep it to a handful; the build session hardcodes
   exactly what you write.
7. **The boss fight** — HP + one attack, real-time. Give it thematic flavor
   that fits a librarian (thrown books? a "SHUSH" shockwave? overdue-fine
   projectiles?). One mechanic.
8. **Pond life** — how much: just the Horse + Ariana, or add
   Capybara/Goose/Swan/Frog for character?
9. **The player's path** — the critical route through the one level (spawn →
   who they meet → how they reach Irene → the fight → the win).
10. **Tone words** — 3–5 adjectives so the build session picks trees, flowers,
    weather, and palette to match.

Design only within the arsenal above. If you want something not on the list,
call it out explicitly as "not available — here's the closest substitute."

═══ END PROMPT ═══
