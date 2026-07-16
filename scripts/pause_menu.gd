extends CanvasLayer

## Esc pause/settings overlay. The node runs with PROCESS_MODE_ALWAYS (set in the
## scene) so it keeps handling input while the rest of the tree is frozen by
## get_tree().paused — that is how Esc can both open the menu (unpaused) and close
## it (paused).
##
## Four options, navigated with up/down + confirm (the project's Label-list +
## _selected + modulate idiom, same as player_select):
##   Resume        -> unpause, hide.
##   Zoom          -> cycle Far / Normal / Close camera presets live.
##   Save Now      -> Game.save(), then show the "Saved HH:MM" confirmation.
##   Return to Title-> unpause and go to player-select, KEEPING the checkpoint
##                     (no reset_run), so the run resumes where it left off.
##
## The camera is reached via an explicit exported NodePath (set in main.tscn),
## mirroring FollowCamera's own fail-loud path resolution.

const SELECT_SCENE := "res://scenes/player_select.tscn"
const SELECTED := Color(1, 0.9, 0.3)
const DIMMED := Color(0.45, 0.32, 0.22)

## label shown / camera magnification for each Zoom preset (higher = closer).
const ZOOM_PRESETS := [
	{"label": "Far", "value": 2.0},
	{"label": "Normal", "value": 2.5},
	{"label": "Close", "value": 3.0},
]

## Path to the FollowCamera whose zoom the presets drive.
@export var camera_path: NodePath

var _open := false
var _selected := 0
var _zoom_idx := 1

@onready var _panel: Control = $Panel
@onready var _zoom_label: Label = $Panel/Frame/Box/Zoom
@onready var _status: Label = $Panel/Frame/Box/Status
@onready var _camera: Node = get_node_or_null(camera_path)
@onready var _options: Array = [
	$Panel/Frame/Box/Resume,
	$Panel/Frame/Box/Zoom,
	$Panel/Frame/Box/Save,
	$Panel/Frame/Box/ToTitle,
]


func _ready() -> void:
	_panel.visible = false
	if camera_path.is_empty() or _camera == null:
		push_error("PauseMenu: camera_path did not resolve — Zoom presets will be inert.")
	_wire_mouse()
	_sync_zoom_label()


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
	if event.is_action_pressed("ui_cancel"):
		# The dialogue box owns the paused tree while a conversation is open —
		# Esc must not stack the pause menu on top of it.
		if Game.dialogue_active:
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
			_save_now()
		3:
			_return_to_title()


func _cycle_zoom() -> void:
	_zoom_idx = (_zoom_idx + 1) % ZOOM_PRESETS.size()
	if _camera != null and _camera.has_method("set_zoom_preset"):
		_camera.set_zoom_preset(ZOOM_PRESETS[_zoom_idx]["value"])
	_sync_zoom_label()


func _save_now() -> void:
	Game.save()
	_status.text = "Saved %s" % Game.last_saved


func _return_to_title() -> void:
	get_tree().paused = false
	Game.change_scene(SELECT_SCENE)


func _sync_zoom_label() -> void:
	_zoom_label.text = "Zoom: %s" % ZOOM_PRESETS[_zoom_idx]["label"]


func _refresh() -> void:
	for i in _options.size():
		_options[i].modulate = SELECTED if i == _selected else DIMMED
