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

var profile: Dictionary = {}

var _appearance: AppearanceRenderer


## Deterministic per-cell villager profile. Each attribute is drawn from a
## different slice of one spatial hash, so neighbouring villagers don't share a
## look and the four valley villagers all differ. The arithmetic is mirrored by
## tools/capture_character_review.py --villagers (parses this catalog, composites
## the looks headlessly) — run it to preview without the engine.
static func profile_for(x: int, y: int) -> Dictionary:
	var seed := (x * 2654435761 + y * 40503) & 0x7FFFFFFF
	var shirt_style: String = AppearanceCatalog.SHIRT_STYLES[(seed / 30) % 3]
	var shirt_opts: Array = AppearanceCatalog.SHIRT_COLORS[shirt_style]
	return {
		"hair_style": (seed % 6) + 1,
		"hair_color": AppearanceCatalog.HAIR_COLORS[(seed / 6) % 5],
		"shirt_style": shirt_style,
		"shirt_color": shirt_opts[(seed / 90) % shirt_opts.size()],
		"pants_color": AppearanceCatalog.PANTS_COLORS[(seed / 900) % 8],
		"shoes_color": AppearanceCatalog.SHOES_COLORS[(seed / 7200) % 9],
		"hat": (seed / 65000) % 4 == 0,
	}


func _ready() -> void:
	_appearance = APPEARANCE_SCENE.instantiate()
	add_child(_appearance)
	_appearance.apply_profile(AppearanceCatalog.normalized(profile))


func _process(delta: float) -> void:
	_appearance.animate_idle(delta)
