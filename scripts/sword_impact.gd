class_name SwordImpact
extends Node2D

## Brief, deterministic pixel sparks spawned once for each enemy hit in a swing.
## They communicate contact without altering damage, knockback, or enemy state.

const LIFETIME := 0.14

var direction := Vector2.RIGHT
var _age := 0.0


func _ready() -> void:
	if direction == Vector2.ZERO:
		direction = Vector2.RIGHT
	queue_redraw()


func _process(delta: float) -> void:
	_age += delta
	if _age >= LIFETIME:
		queue_free()
		return
	queue_redraw()


func _draw() -> void:
	var travel := lerpf(3.0, 14.0, _age / LIFETIME)
	var side := Vector2(-direction.y, direction.x)
	var sparks := [direction, side, -side, -direction * 0.55, (direction + side).normalized()]
	for index in sparks.size():
		var point: Vector2 = sparks[index] * travel
		var color := Color(1.0, 0.9, 0.45, 1.0) if index < 2 else Color(0.94, 0.46, 0.12, 0.9)
		draw_rect(Rect2(point - Vector2.ONE, Vector2(2, 2)), color)
