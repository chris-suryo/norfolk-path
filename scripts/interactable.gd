class_name Interactable
extends Area2D

## A talk trigger: stand close, press interact, the DialogueBox opens with this
## npc's lines. The generalized shop-sign pattern (docs/roadmap.md step 3) —
## main.gd spawns one per talkable map symbol (villagers, Ariana, the sealed
## library door), so adding a conversation is a DialogueData edit, not code.
##
## Input runs through _unhandled_input: the DialogueBox consumes the interact
## press while it is open, so closing a conversation can't instantly reopen it.
## While the tree is paused (box open), this node is PAUSABLE and hears nothing.

const RADIUS := 18.0

var npc_id := ""

var _box: DialogueBox
var _near_bodies: Array[Node] = []


func _ready() -> void:
	collision_layer = 0
	collision_mask = 2  # the players physics layer
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = RADIUS
	shape.shape = circle
	add_child(shape)
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	_box = get_tree().get_first_node_in_group("dialogue_box")


func _on_body_entered(body: Node) -> void:
	if body is Player:
		_near_bodies.append(body)
		if _near_bodies.size() == 1 and _box != null:
			_box.request_prompt(true)


func _on_body_exited(body: Node) -> void:
	if body is Player:
		_near_bodies.erase(body)
		if _near_bodies.is_empty() and _box != null:
			_box.request_prompt(false)


## True when a player who can actually act is in range. A downed co-op body
## lying next to an NPC must not be able to open dialogue and pause the whole
## fight (R4 finding — there was no state gate here).
func _any_near_targetable() -> bool:
	for body in _near_bodies:
		if is_instance_valid(body) and body.is_targetable():
			return true
	return false


func _unhandled_input(event: InputEvent) -> void:
	if _near_bodies.is_empty() or _box == null or Game.dialogue_active:
		return
	if not _any_near_targetable():
		return
	if event.is_action_pressed("p1_interact") or event.is_action_pressed("p2_interact"):
		get_viewport().set_input_as_handled()
		_box.open(npc_id)
