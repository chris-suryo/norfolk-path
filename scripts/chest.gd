class_name Chest
extends Area2D

## A one-time reward chest. Stand close, press interact: it grants its upgrade
## (Game.open_chest — recorded + saved), boosts the live players immediately, shows
## a pickup message, and dims to a looted state. The opened flag lives on the Game
## autoload (saved), so a re-entered scene shows it already looted and it can never
## re-grant. main.gd places one per `x` map cell; the loot comes from LootData keyed
## by the cell id. Mirrors Interactable's proximity-prompt + interact pattern.

const RADIUS := 18.0
const CHEST_TEX := preload(
	"res://assets/cute_fantasy/Cute_Fantasy_Free/Outdoor decoration/Chest.png"
)
const LOOTED_TINT := Color(0.55, 0.5, 0.45)

var chest_id := ""
var upgrade_id := ""

var _sprite: Sprite2D
var _box: DialogueBox
var _near_bodies: Array[Node] = []
var _opened := false


func _ready() -> void:
	collision_layer = 0
	collision_mask = 2  # detect the players physics layer
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = RADIUS
	shape.shape = circle
	add_child(shape)
	# A small solid body so the chest blocks like the old decor prop did.
	var body := StaticBody2D.new()
	var body_shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(12, 8)
	body_shape.shape = rect
	body_shape.position = Vector2(0, -2)
	body.add_child(body_shape)
	add_child(body)
	_sprite = Sprite2D.new()
	_sprite.texture = CHEST_TEX
	_sprite.offset = Vector2(0, -4)
	body.add_child(_sprite)
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	_box = get_tree().get_first_node_in_group("dialogue_box")
	if chest_id in Game.opened_chests:
		_mark_looted()


func _on_body_entered(body: Node) -> void:
	if body is Player:
		_near_bodies.append(body)
		if _near_bodies.size() == 1 and not _opened and _box != null:
			_box.request_prompt(true)


func _on_body_exited(body: Node) -> void:
	if body is Player:
		_near_bodies.erase(body)
		if _near_bodies.is_empty() and _box != null:
			_box.request_prompt(false)


## Same downed-state gate as Interactable: a downed co-op body next to the chest
## must not open it (and pop its message box) mid-fight.
func _any_near_targetable() -> bool:
	for body in _near_bodies:
		if is_instance_valid(body) and body.is_targetable():
			return true
	return false


func _unhandled_input(event: InputEvent) -> void:
	if _near_bodies.is_empty() or _opened or Game.dialogue_active:
		return
	if not _any_near_targetable():
		return
	if event.is_action_pressed("p1_interact") or event.is_action_pressed("p2_interact"):
		get_viewport().set_input_as_handled()
		_open()


func _open() -> void:
	var granted := Game.open_chest(chest_id, upgrade_id)
	_mark_looted()
	if _box != null:
		_box.request_prompt(false)
	if granted.is_empty():
		# Already opened earlier (or an empty chest) — nothing to give.
		return
	for p in get_tree().get_nodes_in_group("players"):
		if p.has_method("apply_upgrade"):
			p.apply_upgrade(upgrade_id)
	if _box != null and _box.has_method("show_message"):
		_box.show_message(str(granted.get("name", "Found")), [str(granted.get("line", "..."))])


func _mark_looted() -> void:
	_opened = true
	if _sprite != null:
		_sprite.modulate = LOOTED_TINT
