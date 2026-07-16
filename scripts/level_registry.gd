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

const LEVELS := {
	"valley":
	{
		"map": VALLEY_MAP,
		"ground": "res://assets/generated/valley-1-ground.png",
		"biome": "outdoor",
		"has_shop": true,
		"has_ariana": true,
		"encounters": "valley",
		# Arrive back from the cove just inside the east-edge path stub.
		"entries": {"from_cove": Vector2i(186, 25)},
		# East-edge crossing to the cove (a path stub runs east past the boss).
		"transitions": [{"cells": Rect2i(190, 24, 2, 5), "to": "cove", "entry": "from_valley"}],
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
}


## The level definition for an id, falling back to the valley if unknown so a
## stale save can never strand the player in a nonexistent level.
static func get_def(id: String) -> Dictionary:
	return LEVELS.get(id, LEVELS["valley"])


## A fresh MapData for the level's ASCII layout.
static func make_map(id: String) -> MapData:
	return MapData.new(get_def(id).map.MAP)
