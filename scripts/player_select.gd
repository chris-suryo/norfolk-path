extends Control

## Title screen. Two stages, driven by whether a save exists:
##   MODE  (only shown when Game.has_save()): Continue / New Game.
##   COUNT (always): 1 Player / 2 Players.
## Continue resumes the saved checkpoint (Game.resume_requested = true, player
## count comes from the save). New Game wipes the run (reset_run) and asks for a
## player count, starting fresh in the village. With no save we skip straight to
## COUNT (an implicit New Game).
##
## Deliberately plain — Labels + a highlight; dressing it with the pack UI kit is
## a later polish pass. Confirm is intentionally broad: ui_accept AND the game's
## own attack keys AND a raw Enter/Space check, so a quirk in one binding can't
## make "start" dead. A failed scene load is reported loudly, not silent.

enum Stage { MODE, COUNT }

const MAIN_SCENE := "res://scenes/main.tscn"
const SELECTED := Color(1, 0.9, 0.3)
const DIMMED := Color(0.84, 0.74, 0.60)

var _stage: int = Stage.COUNT
var _selected := 1

@onready var _title: Label = $Frame/Box/Title
@onready var _option1: Label = $Frame/Box/Option1
@onready var _option2: Label = $Frame/Box/Option2
@onready var _hint: Label = $Frame/Box/Hint


func _ready() -> void:
	if Game.has_save():
		_stage = Stage.MODE
	_wire_mouse()
	_show_stage()


## Mouse as a second input path (keyboard stays): hovering an option highlights
## it, clicking the highlighted option confirms it (so one click on a hovered
## option activates; on a no-hover device, first click selects, second confirms).
func _wire_mouse() -> void:
	var options := {1: _option1, 2: _option2}
	for index in options:
		var label: Label = options[index]
		label.mouse_filter = Control.MOUSE_FILTER_STOP
		label.mouse_entered.connect(_on_option_hover.bind(index))
		label.gui_input.connect(_on_option_click.bind(index))


func _on_option_hover(index: int) -> void:
	_selected = index
	_refresh()


func _on_option_click(event: InputEvent, index: int) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if _selected == index:
			_confirm()
		else:
			_selected = index
			_refresh()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_up") or event.is_action_pressed("ui_down"):
		_selected = 3 - _selected
		_refresh()
	elif _is_confirm(event):
		_confirm()


func _is_confirm(event: InputEvent) -> bool:
	if event.is_action_pressed("ui_accept") or event.is_action_pressed("p1_attack"):
		return true
	if event.is_action_pressed("p2_attack"):
		return true
	if event is InputEventKey and event.pressed and not event.echo:
		var code: int = event.physical_keycode
		return code == KEY_ENTER or code == KEY_KP_ENTER or code == KEY_SPACE
	return false


func _show_stage() -> void:
	_selected = 1
	if _stage == Stage.MODE:
		_option1.text = "CONTINUE"
		_option2.text = "NEW GAME"
	else:
		_option1.text = "1 PLAYER"
		_option2.text = "2 PLAYERS"
	_hint.text = "click or arrows + enter"
	_refresh()


func _confirm() -> void:
	if _stage == Stage.MODE:
		if _selected == 1:
			# Continue: load the saved state now (so main._ready sees the right
			# player_count) and let the EncounterManager resume the checkpoint.
			Game.resume_requested = true
			Game.load_state()
			_go()
		else:
			# New Game: wipe the run, then ask for a player count.
			Game.resume_requested = false
			Game.reset_run()
			_stage = Stage.COUNT
			_show_stage()
	else:
		Game.set_player_count(_selected)
		_go()


func _go() -> void:
	var err: int = get_tree().change_scene_to_file(MAIN_SCENE)
	if err != OK:
		push_error("player_select: could not load %s (error %d)" % [MAIN_SCENE, err])


func _refresh() -> void:
	_option1.modulate = SELECTED if _selected == 1 else DIMMED
	_option2.modulate = SELECTED if _selected == 2 else DIMMED
