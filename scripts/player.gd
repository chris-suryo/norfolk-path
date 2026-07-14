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
##
## Sprite frames come straight from the Cute Fantasy Player.png sheet (32x32
## frames, 6 columns x 10 rows): rows 0/1/2 are idle down/side/up, rows 3/4/5
## are walk down/side/up, rows 6+ are action rows (unused here). Side rows face
## RIGHT in the sheet, so moving left flips the sprite. This is deliberately
## just row/column math on one Sprite2D — no animation state machine yet.

const IDLE_ROW_DOWN := 0
const IDLE_ROW_SIDE := 1
const IDLE_ROW_UP := 2
const WALK_ROW_DOWN := 3
const WALK_ROW_SIDE := 4
const WALK_ROW_UP := 5
const SHEET_COLUMNS := 6
const WALK_FPS := 8.0

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
var _facing := Vector2.DOWN
var _anim_time := 0.0

@onready var _sprite: Sprite2D = $Sprite2D


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
		_facing = input_vector
	else:
		velocity = velocity.move_toward(Vector2.ZERO, friction * delta)

	move_and_slide()
	_update_sprite(input_vector != Vector2.ZERO, delta)


func _update_sprite(moving: bool, delta: float) -> void:
	# Horizontal facing wins ties on diagonals so side-walking reads clearly.
	var row: int
	var flip := false
	if absf(_facing.x) >= absf(_facing.y):
		row = WALK_ROW_SIDE if moving else IDLE_ROW_SIDE
		flip = _facing.x < 0.0
	elif _facing.y < 0.0:
		row = WALK_ROW_UP if moving else IDLE_ROW_UP
	else:
		row = WALK_ROW_DOWN if moving else IDLE_ROW_DOWN

	var column := 0
	if moving:
		_anim_time += delta
		column = int(_anim_time * WALK_FPS) % SHEET_COLUMNS
	else:
		_anim_time = 0.0

	_sprite.flip_h = flip
	_sprite.frame = row * SHEET_COLUMNS + column
