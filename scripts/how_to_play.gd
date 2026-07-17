class_name HowToPlay
extends CanvasLayer

## Read-only "how to play" card, opened from the pause menu. Lists every P1/P2
## control so a player never has to open the remap grid just to remember a key.
## Rows are generated from Controls.ACTIONS (+ Controls.key_text, which now shows
## the aliases too), so the card is always complete and correct — including ROLL
## and TALK, which the title legend omits. No rebinding here; that's the Controls
## screen. Runs with PROCESS_MODE_ALWAYS (set in the scene) since the tree is
## paused underneath, and sits on a layer above the pause menu like ControlsMenu.

signal closed

const NAME_TINT := Color(0.85, 0.79, 0.68)
const KEY_TINT := Color(1, 1, 1)
const BACK_TINT := Color(1, 0.9, 0.3)

@onready var _panel: Control = $Panel
@onready var _grid: GridContainer = $Panel/Frame/Box/Grid
@onready var _back: Label = $Panel/Frame/Box/Back


func _ready() -> void:
	_panel.visible = false
	_back.modulate = BACK_TINT
	_build_rows()


func open() -> void:
	_panel.visible = true


func _close() -> void:
	_panel.visible = false
	closed.emit()


## 4 columns (P1 name, P1 key, P2 name, P2 key), one line per action pair — the
## same walk ControlsMenu uses, but static text (no capture/rebind).
func _build_rows() -> void:
	var half := Controls.ACTIONS.size() / 2
	for i in half:
		for action in [Controls.ACTIONS[i], Controls.ACTIONS[half + i]]:
			var name_label := Label.new()
			var prefix := "P1" if String(action).begins_with("p1") else "P2"
			name_label.text = "%s %s" % [prefix, Controls.label_for(action)]
			name_label.modulate = NAME_TINT
			_grid.add_child(name_label)
			var key_label := Label.new()
			key_label.text = Controls.key_text(action)
			key_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			key_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			key_label.modulate = KEY_TINT
			_grid.add_child(key_label)
	_back.mouse_filter = Control.MOUSE_FILTER_STOP
	_back.gui_input.connect(_on_back_click)


func _on_back_click(event: InputEvent) -> void:
	if not _panel.visible:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_close()


## Any confirm/cancel closes the card. Runs in _input (not _unhandled_input) so it
## takes the key before the pause menu underneath can act on it.
func _input(event: InputEvent) -> void:
	if not _panel.visible:
		return
	if event.is_action_pressed("ui_cancel") or event.is_action_pressed("ui_accept"):
		get_viewport().set_input_as_handled()
		_close()
