class_name ArrowProjectile
extends Area2D

## The player's bow shot: a straight arrow that damages the first enemy it
## touches. The book_projectile pattern with the collision mask flipped to the
## enemies layer; rotation faces travel so the bolt sprite reads as an arrow.

@export var speed: float = 140.0
@export var damage: int = 2
@export var lifetime: float = 1.2

var _dir := Vector2.RIGHT
var _age := 0.0
var _consumed := false


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
	# One arrow, one hit: queue_free is deferred, so without this guard an arrow
	# passing through stacked enemies damaged every one in the same physics tick.
	if _consumed:
		return
	if body.is_in_group("enemies") and body.has_method("take_damage"):
		_consumed = true
		body.take_damage(damage, global_position)
		queue_free()
