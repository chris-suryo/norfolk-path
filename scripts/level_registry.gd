class_name LevelRegistry
extends RefCounted

## The connected-world map: every level keyed by id, with the data main.gd needs
## to build it. Adding a level = adding an entry here (its map script, baked
## ground, and any door/edge transitions) — no engine changes.
##
## Fields per level:
##   map        - a script exposing `const MAP` (the ASCII layout, packed into
##                the Web export as a Godot resource)
##   ground     - the baked below-player composite (tools/preview_map.py
##                --ground-only); the Level tilemap is collision-only
##   biome      - "outdoor" (grass/water autotiles) or "interior" (wall/floor)
##   has_shop   - keep/free the $World/Shop node (valley-only building)
##   has_ariana - keep/free the $World/Ariana critter (valley-only NPC)
##   encounters - encounter_manager builder key ("valley"); "" = peaceful
##   entries    - named arrival cells {entry_id: Vector2i}; the fallback is the
##                map's own "S" spawn cell
##   transitions- edge/door travel volumes:
##                {cells: Rect2i (in map cells), to: level_id, entry: entry_id}

const VALLEY_MAP := preload("res://scripts/island_map.gd")
const COVE_MAP := preload("res://scripts/cove_map.gd")
const COTTAGE_MAP := preload("res://scripts/cottage_map.gd")
const HOME_A1_MAP := preload("res://scripts/home_a1_map.gd")
const HOME_A2_MAP := preload("res://scripts/home_a2_map.gd")
const HOME_G2_MAP := preload("res://scripts/home_g2_map.gd")
const HOME_J1_MAP := preload("res://scripts/home_j1_map.gd")
const HOME_E1_MAP := preload("res://scripts/home_e1_map.gd")
const BARN_INT_MAP := preload("res://scripts/barn_int_map.gd")

const LEVELS := {
	"valley":
	{
		"map": VALLEY_MAP,
		"ground": "res://assets/generated/valley-1-ground.png",
		"biome": "outdoor",
		"has_shop": true,
		"has_ariana": true,
		"encounters": "valley",
		# Arrivals: back from the cove (east stub), or stepping out of a building
		# (the cell in front of its door).
		"entries":
		{
			"from_cove": Vector2i(186, 25),
			"from_cottage": Vector2i(21, 18),
			"from_home_a1": Vector2i(10, 20),
			"from_home_a2": Vector2i(27, 35),
			"from_home_g2": Vector2i(38, 37),
			"from_home_j1": Vector2i(14, 36),
			"from_home_e1": Vector2i(33, 21),
			"from_barn": Vector2i(43, 18),
		},
		# East-edge crossing to the cove + one door per building. Every building
		# sprite has a centered door gap in its collision, so the trigger is the
		# door-mouth cell ITSELF (the anchor): you must step INTO the doorway to
		# travel. (The old trigger sat on the path row in front of cottage G, so
		# just walking the village path yanked you inside — the "abrupt" bug.)
		"transitions":
		[
			{"cells": Rect2i(190, 24, 2, 5), "to": "cove", "entry": "from_valley"},
			{"cells": Rect2i(21, 17, 1, 1), "to": "cottage", "entry": "from_valley"},
			{"cells": Rect2i(10, 19, 1, 1), "to": "home_a1", "entry": "from_valley"},
			{"cells": Rect2i(27, 34, 1, 1), "to": "home_a2", "entry": "from_valley"},
			{"cells": Rect2i(38, 36, 1, 1), "to": "home_g2", "entry": "from_valley"},
			{"cells": Rect2i(14, 35, 1, 1), "to": "home_j1", "entry": "from_valley"},
			{"cells": Rect2i(33, 20, 1, 1), "to": "home_e1", "entry": "from_valley"},
			{"cells": Rect2i(43, 17, 1, 1), "to": "barn_int", "entry": "from_valley"},
		],
	},
	"cove":
	{
		"map": COVE_MAP,
		"ground": "res://assets/generated/cove-s11-ground.png",
		"biome": "outdoor",
		"has_shop": false,
		"has_ariana": false,
		# Peaceful for now — the plumbing ships; encounters are a later data add.
		"encounters": "",
		# Arrive from the valley a few tiles east of the west-edge return volume.
		"entries": {"from_valley": Vector2i(7, 24)},
		"transitions": [{"cells": Rect2i(2, 21, 3, 6), "to": "valley", "entry": "from_cove"}],
	},
	# --- interiors: one per enterable building. No named entries (arriving via
	# the door spawns on each map's own "S" just inside the doorway); the exit
	# mat at the bottom doorway returns you to the cell in front of the door.
	# All are baked by tools/bake_interior.py.
	"cottage":
	{
		"map": COTTAGE_MAP,
		"ground": "res://assets/generated/cottage-ground.png",
		"biome": "interior",
		"has_shop": false,
		"has_ariana": false,
		"encounters": "",
		"entries": {},
		"transitions": [{"cells": Rect2i(6, 9, 1, 1), "to": "valley", "entry": "from_cottage"}],
	},
	"home_a1":
	{
		"map": HOME_A1_MAP,
		"ground": "res://assets/generated/home_a1-ground.png",
		"biome": "interior",
		"has_shop": false,
		"has_ariana": false,
		"encounters": "",
		"entries": {},
		"transitions": [{"cells": Rect2i(5, 8, 1, 1), "to": "valley", "entry": "from_home_a1"}],
	},
	"home_a2":
	{
		"map": HOME_A2_MAP,
		"ground": "res://assets/generated/home_a2-ground.png",
		"biome": "interior",
		"has_shop": false,
		"has_ariana": false,
		"encounters": "",
		"entries": {},
		"transitions": [{"cells": Rect2i(5, 8, 1, 1), "to": "valley", "entry": "from_home_a2"}],
	},
	"home_g2":
	{
		"map": HOME_G2_MAP,
		"ground": "res://assets/generated/home_g2-ground.png",
		"biome": "interior",
		"has_shop": false,
		"has_ariana": false,
		"encounters": "",
		"entries": {},
		"transitions": [{"cells": Rect2i(6, 9, 1, 1), "to": "valley", "entry": "from_home_g2"}],
	},
	"home_j1":
	{
		"map": HOME_J1_MAP,
		"ground": "res://assets/generated/home_j1-ground.png",
		"biome": "interior",
		"has_shop": false,
		"has_ariana": false,
		"encounters": "",
		"entries": {},
		"transitions": [{"cells": Rect2i(4, 7, 1, 1), "to": "valley", "entry": "from_home_j1"}],
	},
	"home_e1":
	{
		"map": HOME_E1_MAP,
		"ground": "res://assets/generated/home_e1-ground.png",
		"biome": "interior",
		"has_shop": false,
		"has_ariana": false,
		"encounters": "",
		"entries": {},
		"transitions": [{"cells": Rect2i(6, 9, 1, 1), "to": "valley", "entry": "from_home_e1"}],
	},
	"barn_int":
	{
		"map": BARN_INT_MAP,
		"ground": "res://assets/generated/barn_int-ground.png",
		"biome": "interior",
		"has_shop": false,
		"has_ariana": false,
		"encounters": "",
		"entries": {},
		"transitions": [{"cells": Rect2i(7, 10, 1, 1), "to": "valley", "entry": "from_barn"}],
	},
}


## The level definition for an id, falling back to the valley if unknown so a
## stale save can never strand the player in a nonexistent level.
static func get_def(id: String) -> Dictionary:
	return LEVELS.get(id, LEVELS["valley"])


## A fresh MapData for the level's ASCII layout.
static func make_map(id: String) -> MapData:
	return MapData.new(get_def(id).map.MAP)
