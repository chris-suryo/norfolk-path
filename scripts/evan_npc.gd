class_name EvanNpc
extends Node2D

## Evan at his stand (round-3: "change Evan's character to a boy that looks
## like him"). Instead of a premade adult NPC sheet, Evan is built from the
## SAME modular player layers the creator uses — a boy-sized villager whose
## look is pure data. To change how he looks, edit PROFILE below (values come
## from AppearanceCatalog; invalid ones normalize to defaults).

const PROFILE := {
	"hair_style": 2,
	"hair_color": "Brown",
	"shirt_style": "Classic",
	"shirt_color": "Green",
	"pants_color": "Blue",
	"shoes_color": "Brown",
	"hat": false,
}

const APPEARANCE_SCENE := preload("res://scenes/appearance_preview.tscn")

## Slightly under player scale so he reads as a kid next to the stall.
const BOY_SCALE := 0.85

var _appearance: AppearanceRenderer


func _ready() -> void:
	_appearance = APPEARANCE_SCENE.instantiate()
	_appearance.scale = Vector2(BOY_SCALE, BOY_SCALE)
	add_child(_appearance)
	_appearance.apply_profile(AppearanceCatalog.normalized(PROFILE))


func _process(delta: float) -> void:
	_appearance.animate_idle(delta)
