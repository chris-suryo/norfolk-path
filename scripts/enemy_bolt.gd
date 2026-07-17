class_name EnemyBolt
extends Area2D

## An enemy's ranged shot: straight line toward where the player was, damages
## the first player it touches. The book_projectile pattern with a real sprite;
## rotation faces travel. Roll through it or sidestep — it does not track.

@export var speed: float = 90.0
@export var damage: int = 1
@export var lifetime: float = 3.0

var _dir := Vector2.RIGHT
var _age := 0.0


func launch(direction: Vector2) -> void:
	_dir = direction.normalized()
	rotation = _dir.angle()


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _physics_process(delta: float) -> void:
	position += _dir * speed * delta
	_age += delta
	if _age >= lifetime:
		queue_free()


func _on_body_entered(body: Node) -> void:
	if body.is_in_group("players") and body.has_method("take_damage"):
		body.take_damage(damage, global_position)
		queue_free()
