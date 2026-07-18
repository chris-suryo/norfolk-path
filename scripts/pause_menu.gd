extends CanvasLayer

## Esc pause/settings overlay. The node runs with PROCESS_MODE_ALWAYS (set in the
## scene) so it keeps handling input while the rest of the tree is frozen by
## get_tree().paused — that is how Esc can both open the menu (unpaused) and close
## it (paused).
##
## Options, navigated with up/down + confirm (the project's Label-list +
## _selected + modulate idiom, same as player_select):
##   Resume        -> unpause, hide.
##   Zoom          -> cycle Far / Normal / Close camera presets live; the value
##                    row also steps with Left/Right, like the character creator.
##   Speed         -> cycle Slow / Normal / Fast game speed (Engine.time_scale),
##                    a pace experiment knob; steps with Left/Right like Zoom.
##   Save Now      -> Game.save(), then show the "Saved HH:MM" confirmation.
##   Controls      -> open the key-remap overlay.
##   How to Play   -> open the read-only control reference.
##   Return to Title-> unpause and go to player-select, KEEPING the checkpoint
##                     (no reset_run), so the run resumes where it left off.
##
## The camera is reached via an explicit exported NodePath (set in main.tscn),
## mirroring FollowCamera's own fail-loud path resolution.

const SELECT_SCENE := "res://scenes/player_select.tscn"
const SELECTED := Color(1, 0.9, 0.3)
const DIMMED := Color(0.72, 0.66, 0.56)

## label shown / camera magnification for each Zoom preset (higher = closer).
const ZOOM_PRESETS := [
	{"label": "Far", "value": 2.0},
	{"label": "Normal", "value": 2.5},
	{"label": "Close", "value": 3.0},
]

## label shown / Engine.time_scale multiplier for each Speed preset. Modest spread
## on purpose — a pace experiment, not a slow-mo toy; tune the values live.
const SPEED_PRESETS := [
	{"label": "Slow", "value": 0.8},
	{"label": "Normal", "value": 1.0},
	{"label": "Fast", "value": 1.25},
]

## Path to the FollowCamera whose zoom the presets drive.
@export var camera_path: NodePath

var _open := false
var _selected := 0
var _zoom_idx := 1
var _speed_idx := 1
## True while an overlay (Controls or How to Play) is on top — the pause menu goes
## inert (its panel hidden, its input ignored) until the overlay reports closed.
var _overlay_open := false

@onready var _panel: Control = $Panel
@onready var _zoom_label: Label = $Panel/Frame/Box/Zoom
@onready var _speed_label: Label = $Panel/Frame/Box/Speed
@onready var _status: Label = $Panel/Frame/Box/Status
@onready var _camera: Node = get_node_or_null(camera_path)
@onready var _controls: ControlsMenu = $ControlsMenu
@onready var _how_to_play: HowToPlay = $HowToPlayMenu
@onready var _options: Array = [
	$Panel/Frame/Box/Resume,
	$Panel/Frame/Box/Zoom,
	$Panel/Frame/Box/Speed,
	$Panel/Frame/Box/Save,
	$Panel/Frame/Box/Controls,
	$Panel/Frame/Box/HowToPlay,
	$Panel/Frame/Box/ToTitle,
]


func _ready() -> void:
	_panel.visible = false
	if camera_path.is_empty() or _camera == null:
		push_error("PauseMenu: camera_path did not resolve — Zoom presets will be inert.")
	_controls.closed.connect(_on_overlay_closed)
	_how_to_play.closed.connect(_on_overlay_closed)
	_wire_mouse()
	_sync_zoom_label()
	_sync_speed_from_game()


## Mouse as a second input path (keyboard stays): hover highlights, a click on the
## highlighted option activates it (same _activate() as the keyboard confirm).
func _wire_mouse() -> void:
	for index in _options.size():
		var label: Label = _options[index]
		label.mouse_filter = Control.MOUSE_FILTER_STOP
		label.mouse_entered.connect(_on_option_hover.bind(index))
		label.gui_input.connect(_on_option_click.bind(index))


func _on_option_hover(index: int) -> void:
	if not _open:
		return
	_selected = index
	_refresh()


func _on_option_click(event: InputEvent, index: int) -> void:
	if not _open:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if _selected == index:
			_activate()
		else:
			_selected = index
			_refresh()


func _unhandled_input(event: InputEvent) -> void:
	if _overlay_open:
		return
	if event.is_action_pressed("ui_cancel"):
		# The dialogue box owns the paused tree while a conversation is open —
		# Esc must not stack the pause menu on top of it. Likewise during the
		# post-boss win beat: don't let the pause menu stack over the incoming
		# win screen (change_scene already clears the paused tree either way).
		if Game.dialogue_active or Game.win_pending or Game.cutscene_active:
			return
		_toggle()
		get_viewport().set_input_as_handled()
		return
	if not _open:
		return
	if event.is_action_pressed("ui_up"):
		_move(-1)
	elif event.is_action_pressed("ui_down"):
		_move(1)
	elif event.is_action_pressed("ui_left") and _selected == 1:
		_cycle_zoom(-1)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_right") and _selected == 1:
		_cycle_zoom(1)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_left") and _selected == 2:
		_cycle_speed(-1)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_right") and _selected == 2:
		_cycle_speed(1)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_accept"):
		_activate()
		get_viewport().set_input_as_handled()


func _toggle() -> void:
	if _open:
		_close()
	else:
		_selected = 0
		_status.text = ""
		_open = true
		_panel.visible = true
		get_tree().paused = true
		# This node is rebuilt on every scene reload, so _speed_idx resets while
		# Engine.time_scale persists — re-sync the row to the live speed on open.
		_sync_speed_from_game()
		_refresh()


func _close() -> void:
	_open = false
	_panel.visible = false
	get_tree().paused = false


func _move(step: int) -> void:
	_selected = (_selected + step + _options.size()) % _options.size()
	_refresh()


func _activate() -> void:
	match _selected:
		0:
			_close()
		1:
			_cycle_zoom()
		2:
			_cycle_speed()
		3:
			_save_now()
		4:
			_open_controls()
		5:
			_open_how_to_play()
		6:
			_return_to_title()


func _open_controls() -> void:
	_overlay_open = true
	_panel.visible = false
	_controls.open()


func _open_how_to_play() -> void:
	_overlay_open = true
	_panel.visible = false
	_how_to_play.open()


func _on_overlay_closed() -> void:
	_overlay_open = false
	_panel.visible = true
	_refresh()


## Steps the zoom preset by dir (+1 forward on accept, -1/+1 on Left/Right so the
## value row behaves like the character creator's — R4-20). posmod wraps both ways.
func _cycle_zoom(dir: int = 1) -> void:
	_zoom_idx = posmod(_zoom_idx + dir, ZOOM_PRESETS.size())
	if _camera != null and _camera.has_method("set_zoom_preset"):
		_camera.set_zoom_preset(ZOOM_PRESETS[_zoom_idx]["value"])
	_sync_zoom_label()


## Steps the game-speed preset like the zoom row. set_game_speed pushes the value
## to Engine.time_scale, so every timed thing (player, enemies, tweens) scales with it.
func _cycle_speed(dir: int = 1) -> void:
	_speed_idx = posmod(_speed_idx + dir, SPEED_PRESETS.size())
	Game.set_game_speed(SPEED_PRESETS[_speed_idx]["value"])
	_sync_speed_label()


func _save_now() -> void:
	Game.save()
	_status.text = "Saved %s" % Game.last_saved


func _return_to_title() -> void:
	get_tree().paused = false
	Game.change_scene(SELECT_SCENE)


func _sync_zoom_label() -> void:
	_zoom_label.text = "Zoom: %s" % ZOOM_PRESETS[_zoom_idx]["label"]


## Point _speed_idx at the preset matching the live Engine.time_scale (mirrored on
## Game.game_speed) before showing the menu, so a speed carried across a scene
## reload doesn't leave the row stale. Falls back to the nearest preset if the live
## value ever drifts off the discrete set.
func _sync_speed_from_game() -> void:
	var best := 0
	var best_gap := INF
	for i in SPEED_PRESETS.size():
		var gap: float = absf(SPEED_PRESETS[i]["value"] - Game.game_speed)
		if gap < best_gap:
			best_gap = gap
			best = i
	_speed_idx = best
	_sync_speed_label()


func _sync_speed_label() -> void:
	_speed_label.text = "Speed: %s" % SPEED_PRESETS[_speed_idx]["label"]


func _refresh() -> void:
	for i in _options.size():
		_options[i].modulate = SELECTED if i == _selected else DIMMED
