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

var _lines: PackedStringArray = []
var _index := 0
var _prompt_requests := 0

@onready var _panel: Panel = $Panel
@onready var _name_label: Label = $Panel/Name
@onready var _text_label: Label = $Panel/Text
@onready var _prompt: Label = $Prompt


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_panel.visible = false
	_prompt.visible = false


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
	_name_label.text = data.name
	_text_label.text = _lines[0] if _lines.size() > 0 else "..."
	_panel.visible = true
	_prompt.visible = false
	Game.dialogue_active = true
	get_tree().paused = true


func _unhandled_input(event: InputEvent) -> void:
	if not _panel.visible:
		return
	var advance := (
		event.is_action_pressed("p1_interact")
		or event.is_action_pressed("p2_interact")
		or event.is_action_pressed("ui_accept")
	)
	if not advance:
		return
	# Consume the press so the Interactable that opened us can't instantly
	# re-open on the same key event after we close.
	get_viewport().set_input_as_handled()
	_index += 1
	if _index < _lines.size():
		_text_label.text = _lines[_index]
	else:
		_close()


func _close() -> void:
	_panel.visible = false
	Game.dialogue_active = false
	get_tree().paused = false
	_prompt.visible = _prompt_requests > 0
