class_name GuideNpc
extends Node2D

## The onboarding/task-giver who greets the player at the village spawn — the first
## person you meet, there to hand you the quest (Ariana's a goose; get to the
## library east; mind Irene) and point you at the basics. Like Evan, there's no
## premade NPC sheet: the guide is built from the SAME modular player layers the
## creator uses, so the look is pure data (PROFILE). Full player scale so they read
## as an adult, unlike Evan's kid scale.
##
## SCAFFOLD: the exact look here is a placeholder to dial in-editor; the dialogue
## lives in DialogueData under "guide" (Chris's locked copy replaces it). Invalid
## PROFILE values normalize to catalog defaults, so it can never crash.

const PROFILE := {
	"hair_style": 1,
	"hair_color": "Grey",
	"shirt_style": "Classic",
	"shirt_color": "Red",
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
