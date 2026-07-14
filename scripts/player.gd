class_name Player
extends CharacterBody2D

## Free 8-directional movement with a deliberately weighty feel.
##
## Velocity eases toward a target rather than snapping to it, so the character
## accelerates on start and slides to a stop on release. The three exported
## constants below are the tuning surface: movement feel is a human-in-editor
## call on Windows, not something the headless build can verify. An early
## prototype felt too fast/precise because it snapped straight to max speed with
## no ramp; these defaults start slower and heavier on purpose.

## 1 = player one (WASD, "p1_*" actions), 2 = player two (arrow keys, "p2_*").
## Only P1 is instanced in Slice 1; P2 reuses this exact scene later by flipping
## this index — no per-player script needed.
@export var player_index: int = 1

## Top movement speed, in pixels per second.
@export var max_speed: float = 60.0
## Rate (px/s^2) at which velocity ramps toward the target while a key is held.
@export var acceleration: float = 500.0
## Rate (px/s^2) at which velocity bleeds back to zero when no key is held.
@export var friction: float = 800.0

var _action_prefix: String


func _ready() -> void:
	_action_prefix = "p%d_" % player_index


func _physics_process(delta: float) -> void:
	var input_vector := Vector2(
		(
			Input.get_action_strength(_action_prefix + "right")
			- Input.get_action_strength(_action_prefix + "left")
		),
		(
			Input.get_action_strength(_action_prefix + "down")
			- Input.get_action_strength(_action_prefix + "up")
		)
	)

	if input_vector != Vector2.ZERO:
		# Normalize so diagonal movement isn't faster than moving straight.
		input_vector = input_vector.normalized()
		velocity = velocity.move_toward(input_vector * max_speed, acceleration * delta)
	else:
		velocity = velocity.move_toward(Vector2.ZERO, friction * delta)

	move_and_slide()
