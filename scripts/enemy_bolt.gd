class_name EnemyBolt
extends Area2D

## An enemy's ranged shot: straight line toward where the player was, damages
## the first player it touches. The book_projectile pattern with a real sprite;
## rotation faces travel. Roll through it or sidestep — it does not track.
## Unlike Irene's books (magic, sail over everything), bolts are physical: the
## scene's mask includes the world layer, so terrain and buildings stop them —
## a mage can no longer snipe players through solid walls (R4 finding).

@export var speed: float = 90.0
@export var damage: int = 1
@export var lifetime: float = 3.0

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
	# One bolt, one hit: queue_free is deferred, so without this guard a bolt
	# overlapping both co-op players in the same physics tick damaged them both.
	if _consumed:
		return
	if body.is_in_group("players") and body.has_method("take_damage"):
		# A downed body must not soak the shot meant for the survivor.
		if body.has_method("is_targetable") and not body.is_targetable():
			return
		_consumed = true
		body.take_damage(damage, global_position)
		queue_free()
	else:
		# Anything else on the mask is terrain/buildings — the bolt splinters.
		_consumed = true
		queue_free()
