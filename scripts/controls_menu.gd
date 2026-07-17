class_name ControlsMenu
extends CanvasLayer

## The key-remap screen (round-3: remapping is the menu focus). Opened from the
## pause menu; the tree stays paused underneath, so this node must run with
## PROCESS_MODE_ALWAYS (set in the scene).
##
## One row per action (P1 and P2 side by side), plus RESET TO DEFAULTS and
## BACK. Keyboard: arrows move, Enter starts a capture ("PRESS A KEY..."),
## the next key pressed becomes the action's ONLY binding (aliases are an
## un-remapped default, not a promise), Esc cancels the capture. Mouse: hover
## highlights, click captures/activates. Bindings persist via Controls
## (user://controls.json) and are re-applied at boot by Game.

signal closed

const SELECTED := Color(1, 0.9, 0.3)
const DIMMED := Color(0.72, 0.66, 0.56)
const CAPTURING := Color(0.4, 0.85, 0.5)

var _rows: Array = []  # {action: String, key_label: Label, name_label: Label}
var _selected := 0
var _capturing := false

@onready var _panel: Control = $Panel
@onready var _grid: GridContainer = $Panel/Frame/Box/Grid
@onready var _reset: Label = $Panel/Frame/Box/Reset
@onready var _back: Label = $Panel/Frame/Box/Back
@onready var _hint: Label = $Panel/Frame/Box/Hint


func _ready() -> void:
	_panel.visible = false
	_build_rows()


func open() -> void:
	_selected = 0
	_capturing = false
	_panel.visible = true
	_refresh()


func _close() -> void:
	_panel.visible = false
	closed.emit()


## The grid is built in code: 4 columns (P1 name, P1 key, P2 name, P2 key),
## walking the ACTIONS list which is ordered p1 block then p2 block.
func _build_rows() -> void:
	var half := Controls.ACTIONS.size() / 2
	for i in half:
		for action in [Controls.ACTIONS[i], Controls.ACTIONS[half + i]]:
			var name_label := Label.new()
			var prefix := "P1" if String(action).begins_with("p1") else "P2"
			name_label.text = "%s %s" % [prefix, Controls.label_for(action)]
			_grid.add_child(name_label)
			var key_label := Label.new()
			key_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			key_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			_grid.add_child(key_label)
			_rows.append({"action": action, "key_label": key_label, "name_label": name_label})
	# Rows read L->R but ACTIONS pairs them P1/P2 per line; selection order is
	# the visual order, so _rows is already in navigation order.
	for index in _rows.size():
		for label: Label in [_rows[index]["name_label"], _rows[index]["key_label"]]:
			label.mouse_filter = Control.MOUSE_FILTER_STOP
			label.mouse_entered.connect(_on_row_hover.bind(index))
			label.gui_input.connect(_on_row_click.bind(index))
	for extra_index in 2:
		var label := _reset if extra_index == 0 else _back
		label.mouse_filter = Control.MOUSE_FILTER_STOP
		label.mouse_entered.connect(_on_row_hover.bind(_rows.size() + extra_index))
		label.gui_input.connect(_on_row_click.bind(_rows.size() + extra_index))


func _on_row_hover(index: int) -> void:
	if not _panel.visible or _capturing:
		return
	_selected = index
	_refresh()


func _on_row_click(event: InputEvent, index: int) -> void:
	if not _panel.visible or _capturing:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_selected = index
		_activate()


## Capture runs in _input (not _unhandled_input) so the chosen key can be
## anything at all — including keys other actions already use.
func _input(event: InputEvent) -> void:
	if not _panel.visible:
		return
	if _capturing:
		if event is InputEventKey and event.pressed and not event.echo:
			get_viewport().set_input_as_handled()
			if event.physical_keycode == KEY_ESCAPE:
				_capturing = false
			else:
				Controls.rebind(_rows[_selected]["action"], event.physical_keycode)
				_capturing = false
			_refresh()
		return
	if event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		_close()
	elif event.is_action_pressed("ui_up"):
		get_viewport().set_input_as_handled()
		_move(-1)
	elif event.is_action_pressed("ui_down"):
		get_viewport().set_input_as_handled()
		_move(1)
	elif event.is_action_pressed("ui_accept"):
		get_viewport().set_input_as_handled()
		_activate()


func _move(step: int) -> void:
	var total := _rows.size() + 2
	_selected = posmod(_selected + step, total)
	_refresh()


func _activate() -> void:
	if _selected < _rows.size():
		_capturing = true
		_refresh()
	elif _selected == _rows.size():
		Controls.reset()
		_refresh()
	else:
		_close()


func _refresh() -> void:
	for index in _rows.size():
		var row: Dictionary = _rows[index]
		var color := SELECTED if index == _selected else DIMMED
		if _capturing and index == _selected:
			color = CAPTURING
			row["key_label"].text = "PRESS A KEY..."
		else:
			row["key_label"].text = Controls.key_text(row["action"])
		row["name_label"].modulate = color
		row["key_label"].modulate = color
	_reset.modulate = SELECTED if _selected == _rows.size() else DIMMED
	_back.modulate = SELECTED if _selected == _rows.size() + 1 else DIMMED
	_hint.text = (
		"PRESS THE NEW KEY - ESC CANCELS" if _capturing else "ENTER / CLICK: REBIND    ESC: BACK"
	)
