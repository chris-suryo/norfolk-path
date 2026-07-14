# Asset catalog — the full Cute Fantasy library, mapped to our game

What we actually own now (paid pack + companions), organized so we can plan the
world, the cast, combat, and menus against real sprites. Companion doc:
`asset-index.md` (every one of the 1,220 files with dimensions). Visual contact
sheets live in `docs/asset-previews/` and are referenced below.

- **Where it lives:** `assets/cute_fantasy/packs/<Pack>/…` — a raw *library*
  (`.gdignore`'d so Godot doesn't import all of it). We copy the specific
  sprites we use into the game when we build.
- **Frame size:** characters/animals are **64×64** per frame, multi-row sheets
  (idle/walk × 4 directions, plus actions). Tiles are 16×16.

---

## 1. The cast — characters  → `asset-previews/cast.png`

**8 premade NPC characters** (`Cute_Fantasy/…/NPCs (Premade)/`), each a full
64×64 animated sheet:

| Sprite | Reads as | Good fit for |
|---|---|---|
| **Bartender_Bruno** | bald man, dark apron | **Evan** (deli/sandwich guy) |
| **Bartender_Katy** | dark-haired woman, apron | Evan or Irene |
| **Chef_Chloe** | white chef hat, orange hair | **Evan** (food service) |
| **Farmer_Bob / Buba** | straw hat, overalls | farmstead flavor NPC |
| **Fisherman_Fin** | hat, waders | a pond/dock NPC |
| **Lumberjack_Jack** | grey hair, rugged | flavor NPC |
| **Miner_Mike** | grey hair, work clothes | flavor NPC |

Plus a **fully modular player** (`Player/`): a nude `Player_Base` + swappable
**Head** (Hair_1–6, helmets), **Chest** (Farmer/Lumberjack/OG/Royal/Plate shirts
in many colors), **Legs**, **Feet**, **Hands**, **Accessories**, **Tools** (bow,
fishing rod, etc.), and **Mounts/Horse**. → We can **build custom characters**
(e.g. a distinct **Irene the librarian**) by layering base + hair + outfit.

**Casting recommendation:** Evan = **Chef_Chloe** or **Bartender_Bruno**
(food-service read); Irene = a **custom modular character** (warm librarian look)
or **Bartender_Katy**; Ariana = the **Duck** (below). Story chat to confirm.

## 2. Animals  (13, `Cute_Fantasy/…/Animals/`)

Bee, Butterfly, Chicken, Cow, **Duck**, Frog, **Goose**, **Horse**, Kapybara,
Mouse, Pig, Sheep, **Swan**. → **Ariana becomes a real Duck** 🦆; **Horse**,
Goose, Swan, Frog add pond/island life. (Cast sheet shows Duck/Horse/Goose/Frog.)

## 3. Buildings  → `asset-previews/buildings.png`  (187 files, mostly recolors)

Distinct types (each in several materials/roof colors):
- **Houses** — 5 designs × Wood / Stone / Limestone.
- **Unique:** **Inn** (big, grand), **Church**, **Fisherman_House**,
  **Blacksmith_House**, **Barn**, **Coop**, **Greenhouse**, **Windmill**,
  **Silo**, **Market_Stalls** (striped-awning stalls), **Shed**, **Tent**.
- **Interiors** (for later): Beds, **BookShelves**, Chairs, Tables, Kitchen,
  Fireplaces, Clocks, Doors, windows, wall/floor tiles, chests (animated).

**Building recommendation for our story:**
- **Evan's shop (modern Subway gag)** → **Market_Stalls** — a striped-awning
  food stall is the perfect anachronistic "sandwich stand," and it's visually
  distinct from a house. (Backup: Blacksmith_House or a plain House.)
- **The library** → **Inn** (big multi-gable, reads as an important destination)
  or **Church**. Site it by the pond. Later, a **BookShelves** interior sells
  "library."
- **Fisherman_House** by the pond adds character if we want a third structure.

## 4. UI kit  → `asset-previews/ui.png`  (`Cute_Fantasy_UI/`, + a font .ttf)

Everything the remaining v1 systems need:
- **Combat HUD:** `UI_Bars` (red/green/blue HP-style bars).
- **Dialogue:** `Book_UI`, `UI_Pop_Up` (speech panels), `UI_Frames`, `Font` /
  `Cute_Fantasy_Font_5x9` / `5x7` (+ `Fonts/CuteFantasy-5x9.ttf`).
- **Menus / player-select:** `UI_Buttons`, `UI_Button_Icons`, `UI_Selectors`
  (arrows), `UI_Ribbons` (title banners), `UI_Sliders`.
- **Misc:** `UI_Icons`, `UI_Crosshairs`, `UI_Premade` (pre-assembled), pointer.

→ This fully covers the roadmap's remaining systems (combat bars, dialogue box,
1P/2P menu). No need to hand-draw any UI.

## 5. Enemies  (`Cute_Fantasy/…/Enemies/`)

**Skeleton** (+ Skeleton_Bowman, merged/separated), **Slime** (Big / Medium /
Small), **Bombschroom**. → Boss (Irene) is a human character, but these are here
for optional path encounters / atmosphere (roadmap keeps combat minimal for v1).

## 6. Tiles / terrain  (`Cute_Fantasy/…/Tiles/`)

Grass, Water, **Waterfall**, Path, **Cobble_Road**, **Beach**, **Cliff**,
**Cave**, **FarmLand**, **Bridge** — a much richer terrain set than the 3 we use
now (we can add cobble paths, beaches, waterfalls when we migrate).

## 7. Trees, Crops, Decor, Weather  (main pack)

Full tree set, Crops, an expanded Outdoor decoration set (with **animations** —
flowers, water, grass, mushrooms), and **Weather effects**. Plenty for the
richer island.

## 8. Themed companion packs (available, NOT for v1's cozy island)

`Desert` (92), `Dungeons` (51), `ShroomLands` (33), `MilitaryCamp` (16),
`Halloween` (15), `Volcano` (13), `Christmas` (9) — different biomes/seasons.
Committed as a library for future use; not part of the Norfolk Path island.
`Old_Sprites` (242) = legacy versions, ignore.

---

## Recommended next decisions (for Chris + the story chat)

1. **Ariana = Duck** (locks the long-standing stand-in). ✅ obvious.
2. **Evan's building = Market_Stalls**, **Evan's sprite = Chef_Chloe or
   Bartender_Bruno**.
3. **Library building = Inn** (or Church), sited by the pond.
4. **Irene = a custom modular character** (or Bartender_Katy) — story chat to
   describe the look; build session assembles it.
5. Combat/menu **UI = this pack's UI kit** (bars, pop-ups, buttons, font).

Visual follow-up still to render: enemies, tiles, trees, crops, decor, and the
themed packs (all listed in `asset-index.md`; contact sheets on request).
