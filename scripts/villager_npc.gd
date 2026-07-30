class_name VillagerNpc
extends Node2D

## A background villager, built from the SAME modular layers as the player and
## the guide/Evan NPCs — so every villager can look like a different person
## instead of the pack's one premade sheet cloned four times (map audit M10).
##
## The look is DETERMINISTIC per map cell (profile_for): the same cell always
## yields the same villager, so runs, saves, and the review composites agree,
## and no wall-clock/RNG is involved. Dialogue still lives in DialogueData under
## "villager_<x>_<y>"; this node is purely the body you walk up to.
##
## SCAFFOLD look, like the guide: the exact palette spread is a placeholder to
## judge in-editor. Invalid profile values normalize to catalog defaults, so a
## bad pick can never crash.

const APPEARANCE_SCENE := preload("res://scenes/appearance_preview.tscn")

# Villager-only rural sub-pools. These are curated SUBSETS of AppearanceCatalog
# (every value is still a valid catalog id, so normalized() never rewrites them)
# that read as farm folk: earth-tone clothes, no bright pinks/purples/oranges,
# work shirts only, and a straw hat half the time. The shared catalog consts stay
# untouched, so the player and character-creator keep the full palette — this
# only narrows what background villagers draw from (playtest feedback: they
# looked like "creative characters", not villagers).
const V_HAIR := ["Black", "Brown", "Grey"]
const V_SHIRT_STYLES := ["Farmer_Shirt", "Lumberjack_Shirt"]
const V_SHIRT_COLORS := {
	"Farmer_Shirt": ["Green", "Blue", "Black", "White_and_Brown"],
	"Lumberjack_Shirt": ["Brown", "Green", "Blue", "Red", "Black"],
}
const V_PANTS := ["Brown", "Black", "Blue", "Green"]
const V_SHOES := ["Brown", "Black"]

var profile: Dictionary = {}

var _appearance: AppearanceRenderer


## Deterministic per-cell villager profile. Each attribute is drawn from a
## different slice of one spatial hash, so neighbouring villagers don't share a
## look and the four valley villagers all differ. Values come from the rural
## sub-pools above. The arithmetic is mirrored by
## tools/capture_character_review.py --villagers (parses this file, composites
## the looks headlessly) — run it to preview without the engine.
static func profile_for(x: int, y: int) -> Dictionary:
	var seed := (x * 2654435761 + y * 40503) & 0x7FFFFFFF
	var shirt_style: String = V_SHIRT_STYLES[(seed / 30) % V_SHIRT_STYLES.size()]
	var shirt_opts: Array = V_SHIRT_COLORS[shirt_style]
	return {
		"hair_style": (seed % 6) + 1,
		"hair_color": V_HAIR[(seed / 6) % V_HAIR.size()],
		"shirt_style": shirt_style,
		"shirt_color": shirt_opts[(seed / 90) % shirt_opts.size()],
		"pants_color": V_PANTS[(seed / 900) % V_PANTS.size()],
		"shoes_color": V_SHOES[(seed / 7200) % V_SHOES.size()],
		"hat": (seed / 65000) % 2 == 0,
	}


func _ready() -> void:
	_appearance = APPEARANCE_SCENE.instantiate()
	add_child(_appearance)
	_appearance.apply_profile(AppearanceCatalog.normalized(profile))


func _process(delta: float) -> void:
	_appearance.animate_idle(delta)
