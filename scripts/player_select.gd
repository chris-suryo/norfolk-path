extends Control

## Mario-style 1P/2P pick. Sets Game.player_count, then loads the level (which
## resumes at the saved checkpoint). Deliberately plain — Labels + a highlight;
## dressing it with the pack UI kit is a later polish pass.
##
## Confirm is intentionally broad: ui_accept AND the game's own attack keys AND a
## raw Enter/Space check, so a quirk in one binding can't make "start" dead. If
## the scene ever fails to load, that is reported loudly rather than looking like
## a dead key.

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
	elif _is_confirm(event):
		_start()


func _is_confirm(event: InputEvent) -> bool:
	if event.is_action_pressed("ui_accept") or event.is_action_pressed("p1_attack"):
		return true
	if event.is_action_pressed("p2_attack"):
		return true
	if event is InputEventKey and event.pressed and not event.echo:
		var code: int = event.physical_keycode
		return code == KEY_ENTER or code == KEY_KP_ENTER or code == KEY_SPACE
	return false


func _start() -> void:
	Game.set_player_count(_selected)
	var err: int = get_tree().change_scene_to_file(MAIN_SCENE)
	if err != OK:
		push_error("player_select: could not load %s (error %d)" % [MAIN_SCENE, err])


func _refresh() -> void:
	_option1.modulate = SELECTED if _selected == 1 else DIMMED
	_option2.modulate = SELECTED if _selected == 2 else DIMMED
