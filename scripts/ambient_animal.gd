class_name AmbientAnimal
extends Sprite2D

## Ambient farm/wild animal: an idle frame-bob, plus — for land animals that have
## a walk row — a slow random wander within a small radius of its spawn spot, with
## pauses between strolls. No collider (these are decor), so the drifting never
## touches the physics or the player. main.gd configures one per animal symbol
## from the audited sheet layout (all 32x32 frames; idle/walk rows differ per
## animal). Water animals (swimming duck/swan, capybara) bob in place — can_wander
## stays false. hframes/vframes are set from the sheet before this enters the tree.

var idle_row := 0
var idle_count := 2
var idle_fps := 2.0
var walk_row := -1  # -1 = no walk frames -> idle-bob only
var walk_count := 6
var walk_fps := 6.0
var can_wander := false
var wander_radius := 16.0
var move_speed := 10.0
var can_fly := false
var flight_radius := 8.0
var flight_period := 3.0

var _home := Vector2.ZERO
var _target := Vector2.ZERO
var _moving := false
var _wait := 0.0
var _time := 0.0
var _flight_phase := 0.0


func _ready() -> void:
	_home = position
	_target = position
	_wait = randf_range(1.0, 3.0)
	# Offset each actor's cycle so nearby animals never animate in lockstep.
	_time = randf_range(0.0, 8.0)
	_flight_phase = randf_range(0.0, TAU)
	flip_h = randf() < 0.5
	frame = idle_row * hframes


func _process(delta: float) -> void:
	_time += delta
	if can_fly:
		_fly()
	elif can_wander and walk_row >= 0:
		_wander(delta)
	var fps := walk_fps if _moving else idle_fps
	var row := walk_row if _moving else idle_row
	var count := walk_count if _moving else idle_count
	frame = row * hframes + int(_time * fps) % count


func _wander(delta: float) -> void:
	if _moving:
		var to_target := _target - position
		if to_target.length() < 1.5:
			_moving = false
			_wait = randf_range(1.5, 4.0)
		else:
			var dir := to_target.normalized()
			position += dir * move_speed * delta
			flip_h = dir.x < 0.0
	else:
		_wait -= delta
		if _wait <= 0.0:
			_target = (
				_home
				+ Vector2(
					randf_range(-wander_radius, wander_radius),
					randf_range(-wander_radius, wander_radius)
				)
			)
			_moving = true


func _fly() -> void:
	# A small figure-eight feels alive without drifting away from its scene.
	var angle := _time * TAU / flight_period + _flight_phase
	position = _home + Vector2(cos(angle) * flight_radius, sin(angle * 2.0) * flight_radius * 0.45)
	flip_h = cos(angle) < 0.0
