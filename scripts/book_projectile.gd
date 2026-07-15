class_name BookProjectile
extends Area2D

## Irene's thrown book: flies in a straight line toward where a player was, damages
## the first player it touches, and frees on hit or after a lifetime. Mask targets
## the players layer only, so books sail over terrain (they are, after all, magic).

@export var speed: float = 75.0
@export var damage: int = 1
@export var lifetime: float = 4.0
@export var spin: float = 6.0

var _dir := Vector2.RIGHT
var _life := 0.0


func launch(direction: Vector2) -> void:
	_dir = direction.normalized() if direction != Vector2.ZERO else Vector2.RIGHT


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _physics_process(delta: float) -> void:
	_life += delta
	position += _dir * speed * delta
	rotation += spin * delta
	if _life >= lifetime:
		queue_free()


func _on_body_entered(body: Node) -> void:
	if body.is_in_group("players") and body.has_method("take_damage"):
		body.take_damage(damage, global_position)
		queue_free()
