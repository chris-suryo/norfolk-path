extends Sprite2D

## One-shot explosion puff: plays the Toxic_Gas_Cloud_VFX strip once, then frees
## itself. Spawned by BombEnemy at the moment it detonates — purely cosmetic, the
## damage is dealt separately by the bomb.

## Frames per second for the single play-through.
@export var fps := 14.0

var _time := 0.0


func _process(delta: float) -> void:
	_time += delta
	var f := int(_time * fps)
	if f >= hframes:
		queue_free()
		return
	frame = f
