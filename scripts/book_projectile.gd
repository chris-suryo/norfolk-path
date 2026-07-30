class_name BookProjectile
extends Area2D

## Irene's thrown book: flies in a straight line toward where a player was, damages
## the first player it touches, and frees on hit or after a lifetime. Mask targets
## the players layer only, so books sail over terrain (they are, after all, magic).

@export var speed: float = 75.0
@export var damage: int = 1
@export var lifetime: float = 4.0
# A slow tumble reads as a thrown book; the old 6.0 spun it into an unreadable
# blur. The book is drawn flat (cover to camera) so it stays a recognizable book
# as it turns - no travel-facing, which in 2D would just point it edge-on.
@export var spin: float = 3.0

var _dir := Vector2.RIGHT
var _life := 0.0
var _consumed := false


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
	# One book, one hit: queue_free is deferred, so without this guard a book
	# overlapping both co-op players in the same physics tick damaged them both.
	if _consumed:
		return
	if body.is_in_group("players") and body.has_method("take_damage"):
		# A downed body must not soak the throw meant for the survivor.
		if body.has_method("is_targetable") and not body.is_targetable():
			return
		_consumed = true
		body.take_damage(damage, global_position)
		queue_free()
