class_name Player
extends CharacterBody2D

## Free 8-directional movement with a deliberately weighty feel, plus real-time
## combat: a facing-direction sword swing, a dodge roll with i-frames, and HP
## with hurt/death handling.
##
## Velocity eases toward a target rather than snapping to it, so the character
## accelerates on start and slides to a stop on release. The movement-feel
## constants (max_speed/acceleration/friction) are the tuning surface: a
## human-in-editor call on Windows, not something the headless build verifies.
##
## Player visuals use the Cute Fantasy modular 64px sheets: aligned body, hair,
## shirt, pants, shoes, and an optional hat. Gameplay collision stays at the
## original footprint; the visual layers are selected from Game appearances.

## Emitted once when HP hits 0 and the collapse animation finishes. The
## EncounterManager decides what happens next (solo respawn, or co-op wait for a
## revive) — the player does not respawn itself.
signal downed

## Fired whenever HP changes (spawn, hit, revive) so the HUD can track it without
## polling. Carries current + max so a listener needs no other reference.
signal health_changed(current: int, maximum: int)

enum State { NORMAL, ATTACK, ROLL, HURT, DOWN, FIRE, DRAW }

const ARROW_SCENE := preload("res://scenes/arrow_projectile.tscn")

const IDLE_ROW_DOWN := 0
const IDLE_ROW_SIDE := 1
const IDLE_ROW_UP := 2
const WALK_ROW_DOWN := 3
const WALK_ROW_SIDE := 4
const WALK_ROW_UP := 5
const ATTACK_ROW_DOWN := 6
const ATTACK_ROW_SIDE := 9
const ATTACK_ROW_UP := 12
const ROLL_ROW_DOWN := 17
const ROLL_ROW_SIDE := 18
const ROLL_ROW_UP := 19
const DEATH_ROW := 53
const SHEET_COLUMNS := 9
const WALK_FPS := 8.0
const MOVE_FRAMES := 6

const ATTACK_FRAMES := 4
const ROLL_FRAMES := 8
const DEATH_FRAMES := 6
const ATTACK_DURATION := 0.4
const ATTACK_ACTIVE_START := 0.1
const ATTACK_ACTIVE_END := 0.28
const SWORD_REACH := 18.0
## You keep a slow shuffle during the swing (playtest feedback: the dead stop
## felt stiff) — this fraction of walk speed, mirroring the bow's draw_move_factor.
const ATTACK_MOVE_FACTOR := 0.5

## The bow is hold-to-charge (round-3 direction): DRAW steps through these
## frames while the key is held, releasing looses the arrow and holds the
## final pose for RELEASE_TIME. Power scales with the hold (see the exports).
const DRAW_FRAMES := 3
const RELEASE_TIME := 0.15

## A brisk ~32px evasive step. The immunity window is deliberately shorter than
## the travel so a roll must be timed through a hit rather than held as safety.
## Distance = ROLL_SPEED x ROLL_DURATION; nudged +10% (playtest: "a touch
## further") via SPEED alone, which leaves the 8-frame roll animation timing
## (driven by _state_time/ROLL_DURATION) untouched.
const ROLL_DURATION := 0.24
const ROLL_IFRAME_DURATION := 0.16
const ROLL_SPEED := 132.0
const ROLL_COOLDOWN := 0.4

const HURT_DURATION := 0.25
const KNOCKBACK_SPEED := 120.0
const INVULN_AFTER_HURT := 0.6
const DEATH_DURATION := 0.7

## 1 = player one (WASD, "p1_*" actions), 2 = player two (arrow keys, "p2_*").
## Identity is purely this index -> action-name prefix; both share one keyboard.
@export var player_index: int = 1

## Top movement speed, in pixels per second.
@export var max_speed: float = 60.0
## Rate (px/s^2) at which velocity ramps toward the target while a key is held.
@export var acceleration: float = 500.0
## Rate (px/s^2) at which velocity bleeds back to zero when no key is held.
@export var friction: float = 800.0

@export var max_hp: int = 6
@export var attack_damage: int = 4
## Charge-bow tuning (all feel knobs — tune live). A bare tap fires the min
## arrow; holding for full_draw_time fires the max. Damage and arrow speed
## scale together, so a full draw both hits harder and flies flatter.
@export var ranged_damage_min: int = 1
@export var ranged_damage_max: int = 3
@export var arrow_speed_min: float = 120.0
@export var arrow_speed_max: float = 200.0
## Seconds of held draw for a max-power shot.
@export var full_draw_time: float = 0.9
## You can keep moving while drawing, at this fraction of max_speed.
@export var draw_move_factor: float = 0.5
## Seconds between shots (starts when the arrow is loosed).
@export var fire_cooldown: float = 0.7

var _action_prefix: String
var _facing := Vector2.DOWN
var _anim_time := 0.0
var _state: int = State.NORMAL
var _state_time := 0.0
var _invuln_time := 0.0
var _roll_cd := 0.0
var _fire_cd := 0.0
var _hp: int = 6
var _hit_this_swing: Array = []
var _downed_emitted := false

@onready var _appearance: AppearanceRenderer = $Appearance
@onready var _sword: Area2D = $SwordHitbox
@onready var _sword_shape: CollisionShape2D = $SwordHitbox/CollisionShape2D


func _ready() -> void:
	_action_prefix = "p%d_" % player_index
	_appearance.apply_profile(Game.appearance_for_player(player_index))
	_apply_all_upgrades()  # before _hp = max_hp, so a Heart Locket spawns you full
	_hp = max_hp
	add_to_group("players")
	_sword.monitoring = true
	_sword_shape.disabled = true
	health_changed.emit(_hp, max_hp)


## Re-apply every collected power-up onto the base exports. Players are recreated on
## each scene reload, so upgrades live on the Game autoload and are re-summed here.
func _apply_all_upgrades() -> void:
	for uid in Game.upgrades:
		_add_upgrade(uid)


## Grant one upgrade to a LIVE player (called by a Chest on open) so it's felt now,
## not only after the next reload. A max-HP bump also heals by the gained amount so
## the new capacity isn't left empty.
func apply_upgrade(upgrade_id: String) -> void:
	var gained_hp := _add_upgrade(upgrade_id)
	if gained_hp > 0:
		_hp = mini(_hp + gained_hp, max_hp)
		health_changed.emit(_hp, max_hp)


## Add one upgrade's stat deltas onto the exports. Returns the max-HP delta so a live
## grant can heal to match; zero for non-HP upgrades.
func _add_upgrade(upgrade_id: String) -> int:
	var up: Dictionary = Game.UPGRADES.get(upgrade_id, {})
	var hp_gain := int(up.get("max_hp", 0))
	max_hp += hp_gain
	attack_damage += int(up.get("attack_damage", 0))
	ranged_damage_min += int(up.get("ranged_damage", 0))
	ranged_damage_max += int(up.get("ranged_damage", 0))
	max_speed += float(up.get("max_speed", 0))
	return hp_gain


## Current HP (the HUD reads this on connect; _hp itself stays private).
func hp() -> int:
	return _hp


func is_targetable() -> bool:
	return _state != State.DOWN


func take_damage(amount: int, from: Vector2) -> void:
	if _invuln_time > 0.0 or _state == State.DOWN:
		return
	_hp -= amount
	health_changed.emit(maxi(_hp, 0), max_hp)
	if _hp <= 0:
		_enter_down()
	else:
		_enter_hurt(from)


func _physics_process(delta: float) -> void:
	_invuln_time = maxf(0.0, _invuln_time - delta)
	_roll_cd = maxf(0.0, _roll_cd - delta)
	_fire_cd = maxf(0.0, _fire_cd - delta)
	_state_time += delta

	match _state:
		State.NORMAL:
			_process_normal(delta)
		State.ATTACK:
			_process_attack(delta)
		State.ROLL:
			_process_roll(delta)
		State.HURT:
			_process_hurt(delta)
		State.DOWN:
			_process_down(delta)
		State.FIRE:
			_process_fire(delta)
		State.DRAW:
			_process_draw(delta)

	move_and_slide()


func _process_normal(delta: float) -> void:
	var input_vector := _move_input()
	if Input.is_action_just_pressed(_action_prefix + "attack"):
		_enter_attack(input_vector)
		return
	if Input.is_action_just_pressed(_action_prefix + "action2") and _roll_cd <= 0.0:
		_enter_roll(input_vector)
		return
	if Input.is_action_pressed(_action_prefix + "fire") and _fire_cd <= 0.0:
		_enter_draw(input_vector)
		return

	if input_vector != Vector2.ZERO:
		input_vector = input_vector.normalized()
		velocity = velocity.move_toward(input_vector * max_speed, acceleration * delta)
		_facing = input_vector
	else:
		velocity = velocity.move_toward(Vector2.ZERO, friction * delta)
	_animate_move(input_vector != Vector2.ZERO, delta)


func _process_attack(_delta: float) -> void:
	# Move-while-attacking: a slow shuffle instead of a dead stop. Facing stays
	# locked (set in _enter_attack) so the sword hitbox keeps pointing where the
	# swing started — only the body translates.
	var input_vector := _move_input()
	if input_vector != Vector2.ZERO:
		velocity = velocity.move_toward(
			input_vector.normalized() * max_speed * ATTACK_MOVE_FACTOR, acceleration * _delta
		)
	else:
		velocity = velocity.move_toward(Vector2.ZERO, friction * _delta)
	var active := _state_time >= ATTACK_ACTIVE_START and _state_time <= ATTACK_ACTIVE_END
	_sword_shape.disabled = not active
	if active:
		_apply_sword_hits()
	var column := mini(ATTACK_FRAMES - 1, int(_state_time / ATTACK_DURATION * ATTACK_FRAMES))
	_set_frame(_attack_row(), column)
	queue_redraw()
	if _state_time >= ATTACK_DURATION:
		_sword_shape.disabled = true
		_enter_normal()


func _process_roll(_delta: float) -> void:
	# Only the early evasive part flashes; the recovery remains fully readable.
	_appearance.modulate.a = (
		0.55 if _state_time < ROLL_IFRAME_DURATION and int(_state_time * 24.0) % 2 == 0 else 1.0
	)
	_animate_roll()
	if _state_time >= ROLL_DURATION:
		_appearance.modulate.a = 1.0
		_enter_normal()


## Drawing: the string is held. Movement stays live at a fraction of walk
## speed (kiting is the bow's identity), the draw pose steps with the charge,
## and letting go of the key looses the arrow at the accumulated power.
func _process_draw(delta: float) -> void:
	var input_vector := _move_input()
	if input_vector != Vector2.ZERO:
		input_vector = input_vector.normalized()
		velocity = velocity.move_toward(
			input_vector * max_speed * draw_move_factor, acceleration * delta
		)
		_facing = input_vector
	else:
		velocity = velocity.move_toward(Vector2.ZERO, friction * delta)
	var column := mini(DRAW_FRAMES - 1, int(_state_time / full_draw_time * DRAW_FRAMES))
	_set_frame(_attack_row(), column)
	if not Input.is_action_pressed(_action_prefix + "fire"):
		_loose_arrow()


## Post-release: hold the final pose briefly so the shot reads as coming off
## the string. The arrow is already in flight.
func _process_fire(delta: float) -> void:
	velocity = velocity.move_toward(Vector2.ZERO, friction * delta)
	_set_frame(_attack_row(), DRAW_FRAMES)
	if _state_time >= RELEASE_TIME:
		_enter_normal()


func _process_hurt(delta: float) -> void:
	velocity = velocity.move_toward(Vector2.ZERO, friction * 0.5 * delta)
	_appearance.modulate = Color(1.0, 0.5, 0.5) if int(_state_time * 20.0) % 2 == 0 else Color.WHITE
	if _state_time >= HURT_DURATION:
		_appearance.modulate = Color.WHITE
		_enter_normal()


func _process_down(delta: float) -> void:
	velocity = velocity.move_toward(Vector2.ZERO, friction * delta)
	var column := mini(DEATH_FRAMES - 1, int(_state_time / DEATH_DURATION * DEATH_FRAMES))
	_set_frame(DEATH_ROW, column)
	if _state_time >= DEATH_DURATION and not _downed_emitted:
		_downed_emitted = true
		downed.emit()


func _move_input() -> Vector2:
	return Vector2(
		(
			Input.get_action_strength(_action_prefix + "right")
			- Input.get_action_strength(_action_prefix + "left")
		),
		(
			Input.get_action_strength(_action_prefix + "down")
			- Input.get_action_strength(_action_prefix + "up")
		)
	)


func _enter_normal() -> void:
	_state = State.NORMAL
	_state_time = 0.0
	_appearance.set_sword_visible(false)
	_appearance.set_bow_visible(false)
	queue_redraw()


func _enter_attack(input_vector: Vector2) -> void:
	if input_vector != Vector2.ZERO:
		_facing = input_vector.normalized()
	_state = State.ATTACK
	_state_time = 0.0
	velocity = Vector2.ZERO
	_hit_this_swing.clear()
	_sword.position = _facing * SWORD_REACH
	_appearance.set_sword_visible(true)


func _enter_draw(input_vector: Vector2) -> void:
	if input_vector != Vector2.ZERO:
		_facing = input_vector.normalized()
	_state = State.DRAW
	_state_time = 0.0
	_appearance.set_bow_visible(true)


## Fire at the accumulated charge: a tap is a weak lob, a full draw
## (>= full_draw_time held) is the hardest, fastest arrow. Cooldown starts
## here — you can't feather the string for a stream of taps.
func _loose_arrow() -> void:
	var charge := clampf(_state_time / full_draw_time, 0.0, 1.0)
	var arrow := ARROW_SCENE.instantiate()
	arrow.damage = int(roundf(lerpf(float(ranged_damage_min), float(ranged_damage_max), charge)))
	arrow.speed = lerpf(arrow_speed_min, arrow_speed_max, charge)
	arrow.global_position = global_position + _facing * 10.0 + Vector2(0, -6)
	arrow.launch(_facing)
	get_parent().add_child(arrow)
	_fire_cd = fire_cooldown
	_state = State.FIRE
	_state_time = 0.0


func _enter_roll(input_vector: Vector2) -> void:
	var dir := input_vector.normalized() if input_vector != Vector2.ZERO else _facing
	_facing = dir
	_state = State.ROLL
	_state_time = 0.0
	_roll_cd = ROLL_COOLDOWN
	_invuln_time = ROLL_IFRAME_DURATION
	velocity = dir * ROLL_SPEED


func _enter_hurt(from: Vector2) -> void:
	_state = State.HURT
	_state_time = 0.0
	_invuln_time = INVULN_AFTER_HURT
	velocity = (position - from).normalized() * KNOCKBACK_SPEED
	_sword_shape.disabled = true
	_appearance.set_sword_visible(false)
	_appearance.set_bow_visible(false)


func _enter_down() -> void:
	_state = State.DOWN
	_state_time = 0.0
	velocity = Vector2.ZERO
	_sword_shape.disabled = true
	_appearance.set_sword_visible(false)
	_appearance.set_bow_visible(false)


## Full-HP revive at a position. Called by the EncounterManager for both a solo
## checkpoint respawn and a co-op in-place revive.
func respawn_at(pos: Vector2) -> void:
	position = pos
	_hp = max_hp
	_invuln_time = INVULN_AFTER_HURT
	_downed_emitted = false
	_appearance.modulate = Color.WHITE
	_appearance.set_sword_visible(false)
	_appearance.set_bow_visible(false)
	_sword_shape.disabled = true
	health_changed.emit(_hp, max_hp)
	_enter_normal()


func _apply_sword_hits() -> void:
	for body in _sword.get_overlapping_bodies():
		if body in _hit_this_swing:
			continue
		if body.has_method("take_damage"):
			_hit_this_swing.append(body)
			body.take_damage(attack_damage, global_position)
			_spawn_hit_impact(body)


func _spawn_hit_impact(body: Node2D) -> void:
	var impact := SwordImpact.new()
	impact.global_position = body.global_position
	impact.direction = (body.global_position - global_position).normalized()
	get_parent().add_child(impact)


func _attack_row() -> int:
	if absf(_facing.x) >= absf(_facing.y):
		return ATTACK_ROW_SIDE
	if _facing.y < 0.0:
		return ATTACK_ROW_UP
	return ATTACK_ROW_DOWN


func _animate_move(moving: bool, delta: float) -> void:
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
		column = int(_anim_time * WALK_FPS) % MOVE_FRAMES
	else:
		_anim_time = 0.0
	_appearance.set_frame(row, column, flip)


func _set_frame(row: int, column: int) -> void:
	_appearance.set_frame(row, column, absf(_facing.x) >= absf(_facing.y) and _facing.x < 0.0)


func _animate_roll() -> void:
	var row := ROLL_ROW_SIDE
	var flip := _facing.x < 0.0
	if absf(_facing.y) > absf(_facing.x):
		row = ROLL_ROW_UP if _facing.y < 0.0 else ROLL_ROW_DOWN
		flip = false
	var column := mini(ROLL_FRAMES - 1, int(_state_time / ROLL_DURATION * ROLL_FRAMES))
	_appearance.set_frame(row, column, flip)


## The free-sheet sword frames are compact, so a short stepped crescent makes
## the forward hit zone visible. White/pale (round-3: the old orange read as a
## fireball) to style-match the impact sparks, tracing the same reach as the
## SwordHitbox sweep.
func _draw() -> void:
	if (
		_state != State.ATTACK
		or _state_time < ATTACK_ACTIVE_START
		or _state_time > ATTACK_ACTIVE_END
	):
		return
	var progress := inverse_lerp(ATTACK_ACTIVE_START, ATTACK_ACTIVE_END, _state_time)
	var direction := _facing.normalized()
	var arc_head := lerpf(-0.95, 0.95, progress)
	var outer := Color(0.88, 0.93, 1.0, 0.45)
	var inner := Color(1.0, 1.0, 1.0, 0.95)
	for step in 5:
		var angle := arc_head - float(step) * 0.16
		var radius := 20.0 + float(step) * 1.5
		var point := direction.rotated(angle) * radius
		draw_rect(Rect2(point - Vector2(2, 2), Vector2(4, 4)), outer)
		draw_rect(Rect2(point - Vector2.ONE, Vector2(2, 2)), inner)
