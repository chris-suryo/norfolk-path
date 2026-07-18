class_name LootData
extends RefCounted

## Every reward chest: its valley cell -> the Game.UPGRADES id it grants. Chests are
## code-placed from THIS table, NOT from map symbols: `x` (chest) is a singleton in
## the map rules, so the map's one decorative `x` is suppressed (main._spawn_props)
## and the real, openable chests live here. Placing a reward is a one-line edit.

const CHESTS := {
	# The library-approach chest — the map's lone `x`, once purely decorative. A
	# Heart Locket to tank up right before Irene.
	Vector2i(165, 19): "max_hp",
	# The forest camp's stash, earned by clearing the camp — a bow boost for the road
	# ahead and the boss.
	Vector2i(120, 32): "bow_power",
}


## Stable id for a chest cell (also the save key in Game.opened_chests).
static func chest_id(cell: Vector2i) -> String:
	return "chest_%d_%d" % [cell.x, cell.y]
