class_name ArianaHumanNpc
extends Node2D

## Human stand-in for Ariana, used ONLY in the intro cutscene (pre-transformation).
## No dedicated human-Ariana sprite exists, so she is built from the same modular
## appearance layers as Evan and the creator — her look is pure data (PROFILE).
## SCAFFOLD: the exact PROFILE is a placeholder to dial in-engine; invalid values
## normalize to catalog defaults, so it can never crash.

const PROFILE := {
	"hair_style": 4,
	"hair_color": "Blonde",
	"shirt_style": "Classic",
	"shirt_color": "Purple",
	"pants_color": "Brown",
	"shoes_color": "Brown",
	"hat": false,
}

const APPEARANCE_SCENE := preload("res://scenes/appearance_preview.tscn")

var _appearance: AppearanceRenderer


func _ready() -> void:
	_appearance = APPEARANCE_SCENE.instantiate()
	add_child(_appearance)
	_appearance.apply_profile(AppearanceCatalog.normalized(PROFILE))


func _process(delta: float) -> void:
	_appearance.animate_idle(delta)
