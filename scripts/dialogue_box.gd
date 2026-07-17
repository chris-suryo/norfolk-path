class_name DialogueBox
extends CanvasLayer

## The one textbox: a bottom-screen panel that shows an NPC's name + lines,
## advanced with the interact key. Opening pauses the tree (both players hold
## still mid-conversation); PROCESS_MODE_ALWAYS keeps this box alive through
## the pause. Interactables open it; a screen-bottom prompt ("E - TALK") shows
## while any of them has a player in range.
##
## Kept deliberately tiny per docs/roadmap.md step 3: a home-rolled box beats a
## dialogue engine for a handful of lines. Content lives in DialogueData —
## the story session's file — never in here.
##
## An entry may carry an optional "choices" block ({at, options:[{label, reply,
## flag}]}): when the line at index `at` is dismissed, the box shows the options
## instead of advancing (reusing pause_menu's Label-list + select/confirm idiom),
## the pick writes `Game.irene_choice = flag` and plays the reply, then closes.
## Entries with no "choices" key behave exactly as before.

const SELECTED := Color(1, 0.9, 0.3)
const DIMMED := Color(0.72, 0.66, 0.56)
const FONT := preload("res://assets/game/fonts/PixelifySans.ttf")

var _lines: PackedStringArray = []
var _index := 0
var _prompt_requests := 0

var _choices: Dictionary = {}
var _choice_options: Array = []
var _choice_active := false
var _choice_sel := 0

@onready var _panel: Panel = $Panel
@onready var _name_label: Label = $Panel/Name
@onready var _text_label: Label = $Panel/Text
@onready var _choices_box: VBoxContainer = $Panel/Choices
@onready var _prompt: Label = $Prompt


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_panel.visible = false
	_prompt.visible = false
	_choices_box.visible = false


## Called by an Interactable when a player is in range (and left again) so the
## prompt reflects "someone here can talk right now".
func request_prompt(active: bool) -> void:
	_prompt_requests = maxi(0, _prompt_requests + (1 if active else -1))
	_prompt.visible = _prompt_requests > 0 and not _panel.visible


func open(npc_id: String) -> void:
	if _panel.visible:
		return
	var data := DialogueData.entry(npc_id)
	_lines = PackedStringArray(data.lines)
	_index = 0
	_choices = data.get("choices", {})
	_choice_active = false
	_choices_box.visible = false
	_text_label.visible = true
	_name_label.text = data.name
	_text_label.text = _lines[0] if _lines.size() > 0 else "..."
	_panel.visible = true
	_prompt.visible = false
	Game.dialogue_active = true
	get_tree().paused = true


func _unhandled_input(event: InputEvent) -> void:
	if not _panel.visible:
		return
	if _choice_active:
		_choice_input(event)
		return
	if not _is_confirm(event):
		return
	# Consume the press so the Interactable that opened us can't instantly
	# re-open on the same key event after we close.
	get_viewport().set_input_as_handled()
	# At the choice line, offer the options instead of advancing/closing.
	if not _choices.is_empty() and _index == int(_choices.get("at", -1)):
		_show_choices()
		return
	_index += 1
	if _index < _lines.size():
		_text_label.text = _lines[_index]
	else:
		_close()


func _choice_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_up"):
		get_viewport().set_input_as_handled()
		_move_choice(-1)
	elif event.is_action_pressed("ui_down"):
		get_viewport().set_input_as_handled()
		_move_choice(1)
	elif _is_confirm(event):
		get_viewport().set_input_as_handled()
		_pick()


## Build the option list (labels created here so an entry can carry any number),
## mirroring pause_menu's Label-list + modulate selection + mouse wiring.
func _show_choices() -> void:
	_choice_active = true
	_choice_sel = 0
	_choice_options = _choices.get("options", [])
	for child in _choices_box.get_children():
		child.queue_free()
	for i in _choice_options.size():
		var opt: Dictionary = _choice_options[i]
		var label := Label.new()
		label.text = str(opt.get("label", "..."))
		label.add_theme_font_override("font", FONT)
		label.add_theme_font_size_override("font_size", 11)
		label.mouse_filter = Control.MOUSE_FILTER_STOP
		label.mouse_entered.connect(_on_choice_hover.bind(i))
		label.gui_input.connect(_on_choice_click.bind(i))
		_choices_box.add_child(label)
	_text_label.visible = false
	_choices_box.visible = true
	_refresh_choices()


func _move_choice(step: int) -> void:
	var count := _choice_options.size()
	if count == 0:
		return
	_choice_sel = (_choice_sel + step + count) % count
	_refresh_choices()


func _refresh_choices() -> void:
	var kids := _choices_box.get_children()
	for i in kids.size():
		kids[i].modulate = SELECTED if i == _choice_sel else DIMMED


func _pick() -> void:
	if _choice_sel < 0 or _choice_sel >= _choice_options.size():
		return
	var opt: Dictionary = _choice_options[_choice_sel]
	Game.irene_choice = str(opt.get("flag", ""))
	_choice_active = false
	_choices_box.visible = false
	_text_label.visible = true
	_text_label.text = str(opt.get("reply", "..."))
	# The reply is the last beat; the next advance closes the box.
	_index = _lines.size()


func _on_choice_hover(index: int) -> void:
	if not _choice_active:
		return
	_choice_sel = index
	_refresh_choices()


func _on_choice_click(event: InputEvent, index: int) -> void:
	if not _choice_active:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if _choice_sel == index:
			_pick()
		else:
			_choice_sel = index
			_refresh_choices()


func _is_confirm(event: InputEvent) -> bool:
	return (
		event.is_action_pressed("p1_interact")
		or event.is_action_pressed("p2_interact")
		or event.is_action_pressed("ui_accept")
	)


func _close() -> void:
	_panel.visible = false
	_choice_active = false
	_choices_box.visible = false
	Game.dialogue_active = false
	get_tree().paused = false
	_prompt.visible = _prompt_requests > 0
