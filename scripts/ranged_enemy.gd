class_name RangedEnemy
extends Enemy

## A shooter: closes to keep_distance, then stands off and fires bolts at the
## nearest player on a timer (Irene's throw loop, generalized). Everything else
## — HP, knockback, aggro latch, contact damage, data-driven animation — is the
## Enemy base. Bolt speed/damage/interval are per-scene knobs, so one script
## serves the bowman (fast, frequent, weak) and the mage (slow, rare, mean).

const BOLT_SCENE := preload("res://scenes/enemy_bolt.tscn")

## Seconds between shots once awake.
@export var shoot_interval: float = 1.8
## Preferred stand-off range: advances beyond it, holds inside it.
@export var keep_distance: float = 90.0
@export var bolt_speed: float = 90.0
@export var bolt_damage: int = 1

var _shoot_cd := 0.0


func _physics_process(delta: float) -> void:
	_contact_cd = maxf(0.0, _contact_cd - delta)
	_knockback = _knockback.move_toward(Vector2.ZERO, 400.0 * delta)

	if _dead:
		velocity = _knockback
		move_and_slide()
		_animate_death(delta)
		return

	var target := _nearest_player()
	var moving := false
	if target != null and _awake(target):
		var to_target := target.global_position - global_position
		_facing = to_target.normalized()
		_shoot_cd -= delta
		if _shoot_cd <= 0.0:
			_shoot(target)
			_shoot_cd = shoot_interval
		if to_target.length() > keep_distance:
			velocity = _facing * move_speed + _knockback
			moving = true
		else:
			velocity = _knockback
	else:
		velocity = _knockback

	move_and_slide()
	_try_contact_damage()
	_animate(moving, delta)


func return_home() -> void:
	super()
	_shoot_cd = 0.0


func _shoot(target: Node2D) -> void:
	var bolt := BOLT_SCENE.instantiate()
	bolt.speed = bolt_speed
	bolt.damage = bolt_damage
	get_parent().add_child(bolt)
	bolt.global_position = global_position + Vector2(0, -8)
	bolt.launch(target.global_position - bolt.global_position)
