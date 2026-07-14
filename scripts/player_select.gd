extends Control

## Mario-style 1P/2P pick. Sets Game.player_count, then loads the level (which
## resumes at the saved checkpoint). Deliberately plain — Labels + a highlight;
## dressing it with the pack UI kit is a later polish pass.

const MAIN_SCENE := "res://scenes/main.tscn"
const SELECTED := Color(1, 0.9, 0.3)
const DIMMED := Color(0.6, 0.6, 0.6)

var _selected := 1

@onready var _option1: Label = $Center/Box/Option1
@onready var _option2: Label = $Center/Box/Option2


func _ready() -> void:
	_refresh()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_up") or event.is_action_pressed("ui_down"):
		_selected = 3 - _selected
		_refresh()
	elif event.is_action_pressed("ui_accept"):
		Game.set_player_count(_selected)
		get_tree().change_scene_to_file(MAIN_SCENE)


func _refresh() -> void:
	_option1.modulate = SELECTED if _selected == 1 else DIMMED
	_option2.modulate = SELECTED if _selected == 2 else DIMMED
