# Asset catalog — the full Cute Fantasy arsenal

Everything we own, mapped so we can build **this** game (Norfolk Path) *and*
reach for a sprite fast in any future one. This is the "arsenal" reference:
open the named contact sheet, find the row, follow the path.

- **Library root:** `assets/cute_fantasy/packs/<Pack>/…` — a raw art *library*,
  `.gdignore`'d so Godot doesn't import all 1,220 files. We copy the specific
  sprites we use into the game as we build.
- **Main pack root** (referenced below as `B/`):
  `assets/cute_fantasy/packs/Cute_Fantasy/Cute_Fantasy/` (the vendor
  double-nests it).
- **Contact sheets:** `docs/asset-previews/*.png` — one montage per category
  (`.gdignore`'d). Every heading names its sheet.
- **Full file list:** `docs/asset-index.md` — all 1,220 PNGs with dimensions.
- **Frame sizes:** characters/animals = **64×64** per frame (multi-row sheets:
  idle + walk × 4 directions, plus action rows). Tiles = **16×16**. Buildings/
  props vary (whole-image sprites).

---

## ⚡ Quick "where is…" index

| Looking for… | Sheet | Path under `B/` (or pack) |
|---|---|---|
| A **duck** (Ariana) | `animals` | `Animals/Duck/` |
| A **horse** (6 colors) | `animals` | `Animals/Horse/` + rideable `Player/Player_Mounts/Horse/` |
| A **cozy human NPC** (bartender, chef, farmer, fisher…) | `cast` | `B/NPCs (Premade)/` |
| A **custom human** (build from parts) | `player_hair`/`_outfits` | `B/Player/` |
| A **fantasy fighter** (knight, goblin, orc, angel) | `pack_characters` | `Cute_Fantasy_Characters/` |
| A **skeleton / slime** enemy | `enemies` | `B/Enemies/` |
| A **food stall / shop** building | `buildings` | `B/Buildings/…/Stalls/Market_Stalls.png` |
| A **big landmark** building (inn/church) | `buildings` | `B/Buildings/…/Unique_Buildings/` |
| **Water / grass / path** tiles (+ autotile edges) | `tiles` | `B/Tiles/` |
| A **bookshelf / bed / table** (interiors) | `interiors` | `B/Buildings/Houses_Interiors/`, `House_Decor/` |
| **HP bars / dialogue box / buttons / font** | `ui` | `Cute_Fantasy_UI/` |
| A **desert / dungeon / mushroom / lava / spooky / camp / xmas** biome | `pack_*` | `Cute_Fantasy_<Theme>/` |

---

## 1. The cozy cast — premade human NPCs  → `cast.png`

**8 ready-to-use 64×64 townsfolk** in `B/NPCs (Premade)/`. Each is a full
animated sheet (idle + walk × 4 dirs).

| File | Reads as | Norfolk Path fit |
|---|---|---|
| `Bartender_Bruno.png` | bald man, dark apron | **Evan** (deli/sandwich guy) |
| `Bartender_Katy.png` | dark-haired woman, apron | Evan or **Irene** |
| `Chef_Chloe.png` | white chef hat, orange hair | **Evan** (food service) |
| `Farmer_Bob.png` | straw hat, overalls | farmstead flavor NPC |
| `Farmer_Buba.png` | straw hat variant | farmstead flavor NPC |
| `Fisherman_Fin.png` | hat, waders | pond/dock NPC |
| `Lumberjack_Jack.png` | grey hair, rugged | flavor NPC |
| `Miner_Mike.png` | grey hair, work clothes | flavor NPC |

## 2. Build-a-character — the modular player  → `player_hair.png`, `player_outfits.png`, `player_tools_mounts.png`

A layered paper-doll in `B/Player/` — stack base + hair + shirt + legs + extras
to make **any** custom human (this is how we make a distinct **Irene the
librarian** without a premade sheet).

- **Player_Base** — nude body (skin-tone base).
- **Head** — `Hair_1`…`Hair_6` (each in ~8 colors) + `Plate_Helmet_1/2`.
- **Chest** — `Farmer_Shirt`, `Lumberjack_Shirt`, `OG_Shirt`, `Royal_Shirt`,
  `Plate_Chest` — each in the full colorway (blue/green/orange/pink/purple/
  red/white…).
- **Legs**, **Feet**, **Hands**, **Accessories** — same modular colorways.
- **Tools** — `Bow/`, `Fishing_Rod/`, `Iron/` (axe/pick/hoe/etc.), `Other/`.
- **Player_Mounts/Horse** — a **rideable** horse (distinct from the animal).

## 3. Fantasy fighters — the character pack  → `pack_characters.png`

`Cute_Fantasy_Characters/` — **14 combat-ready 64×64 characters**, great for a
boss, guards, or a future action game:

- **Angels** — `Angel_1` (winged, gold-haired), `Angel_2` (dark/fallen).
- **Goblins** — `Goblin_Archer`, `Goblin_Maceman`, `Goblin_Spearman`,
  `Goblin_Thief`.
- **Knights** — `Archer`, `Spearman`, `Swordman`, `Templar`.
- **Orcs** — `Orc_Archer`, `Orc_Chief` (wolf-pelt chief), `Orc_Grunt`,
  `Orc_Peon`.

> Norfolk Path's boss (Irene) is a *human*, so she's a modular build (§2) — but
> these are on hand if we ever want a real fight or path encounters.

## 4. Animals  → `animals.png`  (13 species, `B/Animals/`)

Each species is its own folder, most with several **colorways**:

| Species | Notes |
|---|---|
| **Duck** | 🦆 **= Ariana.** Yellow + mallard. |
| **Horse** | ~6 colors (brown/cream/dark/grey/black/chestnut) — pond life. |
| Chicken | many colors (Ariana's original stand-in critter). |
| Cow | many colors (spotted/brown/grey). |
| Pig | pink + variants. |
| Sheep | many colors incl. dyed. |
| Goose, Swan | white/grey waterfowl for the pond. |
| Frog | pond edge. |
| Capybara | sits in water — charming pond centerpiece. |
| Mouse, Bee, Butterfly | tiny ambient critters. |

## 5. Enemies  → `enemies.png`  (`B/Enemies/`)

- **Skeleton** — `Skeleton_Swordman`, `Skeleton_Bowman` (merged + separated
  bow), `Skeleton_Mage` (dark-robed caster) + `Skeleton_Mage_Projectile`
  (in `Other/`).
- **Slime** — `Big` / `Medium` / `Small`, each in **Blue/Green/Pink/Red/
  Yellow**.
- **Bombschroom** — red mushroom that pops + `Toxic_Gas_Cloud_VFX`.

## 6. Buildings  → `buildings.png`  (`B/Buildings/Buildings/`, 187 files w/ recolors)

**Houses** — `Wood` / `Stone` / `Limestone`, each with a `House_Base`
(construction/foundation stage) → finished `House`.

**Unique buildings** (each its own silhouette; the star of the roster):

| Building | Reads as | Story use |
|---|---|---|
| **Market_Stalls** | striped-awning food stalls | **Evan's shop** (the Subway gag) |
| **Inn** | big multi-gable landmark | **the library** (or Church) |
| **Church** | steeple landmark | alt library / town anchor |
| **Fisherman_House** | dockside cabin | pond-side character |
| **Blacksmith_House** | forge + chimney | flavor |
| **Barn**, **Coop**, **Silo**, **Windmill** (animated sail), **Greenhouse** (glass/metal), **Shed** | farmstead set | rural texture |
| **Tent** (Big/Small + Interior) | camp | wanderer/quest spot |

> `_Base` variants = build-in-progress stages (for a construction cutscene, if
> ever). Interiors are §9.

## 7. Tiles / terrain  → `tiles.png`  (`B/Tiles/`)

Much richer than the 3 we ship now. All with **autotile edge sets**:

`Grass` (several shades) · `Water` (+ grass transitions) · `Waterfall` ·
`Path` · `Cobble_Road` · `Beach` (sand) · `Cliff` (stone walls/faces) · `Cave`
(interior stone) · `FarmLand` (tilled soil) · `Bridge` (wood + stone) ·
`Hedge_Tiles` · `Pavement_Tiles` · `Wooden_Deck_Tiles` · `Picnic_Blankets`.

## 8. Nature & outdoor props  → `trees.png`, `crops.png`, `decor.png`, `decor_anim.png`, `weather.png`

- **Trees** (`B/Trees/`): `Birch` / `Oak` / `Spruce` / `Fruit`, each **Big /
  Medium / Small**, + falling-leaf particles.
- **Crops** (`B/Crops/`): `Apple/Cherry/Peach/Pear` fruit trees, `Berries`,
  `Grapes_Bower`, `Crops`/`Crops_2` (veg rows), `Fruit_Tree_Stages` (growth).
- **Decor** (`B/Outdoor decoration/`): `Benches`, `Boat`, `Fountain`, `Well`,
  `Fences`/`Fence_Big`/`White_Fence`/`Stone_Fence_Big`+`_Small`, `Flowers`,
  `Hay_Bales`, `Lantern`/`Lanter_Posts`, `Ores`, `Nests`, `Scarecrows`,
  `Signs`, `Water_Troughs`, `barrels`, `Minecrats`, `Camp_Decor`,
  `Cave_Decorations`, `Picnic_Basket`.
- **Animated decor** (`…/Outdoor_Decor_Animations/`, 113 frames): animated
  flowers, grass tufts, water, mushrooms, torches — life/motion for the world.
- **Weather** (`B/Weather effects/`): `Clouds`, `Rain_Drop`,
  `Rain_Drop_Impact`, `Wind_Anim`.

## 9. Interiors & icons  → `interiors.png`, `icons.png`

- **Interiors** (`B/Buildings/Houses_Interiors/` + `House_Decor/`): Beds (many
  colors), Tables, Chairs, Kitchen (stoves/sinks/counters), Fireplaces, Clocks,
  Cabinets, **BookShelves** (→ library interior), bottles/potions, barrels,
  brick/stone/wood/checkered **floors & walls**, doors, windows, animated
  chests. (For a later interior/indoor scene.)
- **Icons** (`B/Icons/`, Outline + No-Outline sets): `Food_Icons`,
  `Tool_Icons`, `Resources_Icons`, `Other_Icons` (+ `_2`) — inventory/menu
  glyphs.

## 10. UI kit  → `ui.png`  (`Cute_Fantasy_UI/`)

Covers every remaining v1 system — no hand-drawing needed:

- **Combat HUD:** `UI_Bars` (red/green/blue HP-style bars).
- **Dialogue:** `Book_UI`, `UI_Pop_Up` (speech panels), `UI_Frames`; fonts
  `Cute_Fantasy_Font_5x9` / `5x7` (+ `Fonts/CuteFantasy-5x9.ttf`).
- **Menus / player-select:** `UI_Buttons`, `UI_Button_Icons`, `UI_Selectors`
  (arrows), `UI_Ribbons` (title banners), `UI_Sliders`.
- **Misc:** `UI_Icons`, `UI_Crosshairs`, `UI_Premade` (pre-assembled), pointer.

## 11. Themed biome packs (future games, NOT the cozy island)  → `pack_*.png`

Full standalone biomes — committed as arsenal, not part of Norfolk Path:

| Pack | Files | What's inside |
|---|---|---|
| **Desert** | 92 | adobe/sandstone houses (multi-story), cacti, palm + dead trees, **mummy**, pyramid/obelisk/temple, oasis water, sand terrain, pottery. |
| **Dungeons** | 51 | stone walls, arched + **monster doors**, jail cells, stairs, **treasure/gold piles**, ladders, portal/void, slime pools, chains. |
| **ShroomLands** | 33 | giant **mushroom houses**, small mushrooms (6 colors), **snails** (4 colors), fungal terrain. |
| **MilitaryCamp** | 16 | wooden **watchtowers**, **catapult/ballista**, tents, palisades/barricades, banners (many colors), campfire, sandbags, spikes. |
| **Halloween** | 15 | **pumpkins**/jack-o-lanterns, **scarecrows**, bats, spooky house, dead trees. |
| **Volcano** | 13 | dark obsidian **temple**, lava tiles, fire, red/orange ashen plants. |
| **Christmas** | 9 | **Santa** + helper, **reindeer**, gingerbread house, snowmen (animated), snowy grass, chimney, decor. |

`Old_Sprites` (242) = **legacy** versions of main-pack art — ignore.

---

## Casting board — recommended picks (Chris + story chat confirm)

1. **Ariana = Duck** 🦆 (`Animals/Duck/`). ✅ Locks the long-standing stand-in.
2. **Evan** → sprite `Chef_Chloe` or `Bartender_Bruno`; building **Market_Stalls**.
3. **Library** → **Inn** (or Church), sited by the pond; **BookShelves** interior later.
4. **Irene (boss)** → **custom modular build** (§2: base + `Hair_*` + a shirt) for
   a warm-then-menacing librarian; fallback `Bartender_Katy`.
5. **Pond life** → **Horse** by the water + a **Capybara**/Goose/Swan/Frog for character.
6. **UI** → this pack's kit (bars, `UI_Pop_Up`, buttons, font) for player-select,
   dialogue, and the boss HP bar.

*All contact sheets referenced above are in `docs/asset-previews/`; every raw
file with dimensions is in `docs/asset-index.md`.*
