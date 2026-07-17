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

enum Stage { MODE, COUNT, CREATOR }

const MAIN_SCENE := "res://scenes/main.tscn"
const SELECTED := Color(1, 0.9, 0.3)
const DIMMED := Color(0.84, 0.74, 0.60)

var _stage: int = Stage.COUNT
var _selected := 1
var _creator_slot := 1
var _pending_appearances: Array[Dictionary] = []

@onready var _title: Label = $Frame/Box/Title
@onready var _option1: Label = $Frame/Box/Option1
@onready var _option2: Label = $Frame/Box/Option2
@onready var _build_version: Label = $Frame/BuildVersion
@onready var _creator: CharacterCreator = $Creator


func _ready() -> void:
	_build_version.text = (
		"v%s - %s" % [ProjectSettings.get_setting("application/config/version", "?"), BuildInfo.SHA]
	)
	_creator.close()
	_creator.accepted.connect(_on_creator_accepted)
	_creator.backed.connect(_on_creator_backed)
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
	if _stage == Stage.CREATOR:
		_creator.handle_input(event)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_up") or event.is_action_pressed("ui_down"):
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
			# New Game: wipe the run, then ask for a player count. Re-arm the intro
			# so it replays on EVERY New Game (reset_run deliberately leaves the
			# once-per-session latch alone; Continue never reaches here).
			Game.resume_requested = false
			Game.reset_run()
			Game.intro_played = false
			_stage = Stage.COUNT
			_show_stage()
	else:
		Game.set_player_count(_selected)
		Game.resume_requested = false
		_pending_appearances = [
			AppearanceCatalog.default_profile(1), AppearanceCatalog.default_profile(2)
		]
		_creator_slot = 1
		_stage = Stage.CREATOR
		_creator.begin(_creator_slot, _pending_appearances[_creator_slot - 1])


func _on_creator_accepted(profile: Dictionary) -> void:
	_pending_appearances[_creator_slot - 1] = AppearanceCatalog.normalized(profile)
	if _creator_slot < Game.player_count:
		_creator_slot += 1
		_creator.begin(_creator_slot, _pending_appearances[_creator_slot - 1])
		return
	Game.set_appearances(_pending_appearances)
	Game.save()
	_creator.close()
	_go()


func _on_creator_backed() -> void:
	if _creator_slot > 1:
		_creator_slot -= 1
		_creator.begin(_creator_slot, _pending_appearances[_creator_slot - 1])
		return
	_creator.close()
	_stage = Stage.COUNT
	_show_stage()


func _go() -> void:
	# Fade + error handling live in Game.change_scene.
	Game.change_scene(MAIN_SCENE)


func _refresh() -> void:
	_option1.modulate = SELECTED if _selected == 1 else DIMMED
	_option2.modulate = SELECTED if _selected == 2 else DIMMED
