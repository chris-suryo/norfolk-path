class_name Enemy
extends CharacterBody2D

## A simple melee enemy: walk toward the nearest live player and deal contact
## damage on a cooldown. No pathfinding (the level is open); on death it plays a
## collapse frame, leaves the tracking groups so an area reads as "cleared," then
## frees itself.
##
## Animation is data-driven so one script serves several sheets. Two layouts:
## - non-directional (slime, 8-col sheet): idle_row / move_row / death_row,
##   cycling anim_frames columns, no flip.
## - directional (skeleton, Player-layout 6-col sheet): idle rows 0/1/2 and walk
##   rows 3/4/5 chosen by facing (down/side/up, side flips), death on row 9.

# Directional (Player-layout) sheets share row semantics but not width: the
# skeleton/bowman are 6 columns, the mage 8 — so the stride comes from the
# exported sheet_columns, not a constant.
const DIR_IDLE_DOWN := 0
const DIR_WALK_DOWN := 3
const DIR_DEATH_ROW := 9
const DIR_FRAMES := 4

@export var max_hp: int = 3
@export var move_speed: float = 30.0
@export var contact_damage: int = 1
@export var contact_cooldown: float = 0.8
@export var knockback_speed: float = 90.0

## Ambush gate. 0 = always-on: the enemy chases from spawn (slimes, as before).
## When > 0, it idles until a live player comes within this radius, then latches
## awake and chases forever — so a camp/cluster wakes when you enter the clearing
## instead of marching at you from level load. Set per-scene (~110 px on the
## skeleton). Being hit doesn't wake it; only proximity does.
@export var aggro_radius: float = 0.0

## Corner steering (round-3 "enemies get stuck on corners"): a chaser whose
## straight line to the player is blocked by a prop commits to sliding along
## the obstacle's surface for this long before re-aiming — long enough to clear
## a fence post or table corner, short enough to stay dumb. 0 disables. No
## pathfinding; feel knob, tune live.
@export var steer_duration: float = 0.35

## Animation layout.
@export var directional: bool = false
@export var idle_row: int = 0
@export var move_row: int = 1
@export var death_row: int = 2
@export var sheet_columns: int = 8
@export var anim_frames: int = 4
@export var anim_fps: float = 6.0
@export var death_duration: float = 0.6

var _hp: int = 3
var _dead := false
var _aggro := false
var _home := Vector2.ZERO
var _anim_time := 0.0
var _death_time := 0.0
var _contact_cd := 0.0
var _knockback := Vector2.ZERO
var _facing := Vector2.DOWN
var _steer_dir := Vector2.ZERO
var _steer_time := 0.0

@onready var _sprite: Sprite2D = $Sprite2D
@onready var _contact: Area2D = $ContactHitbox


func _ready() -> void:
	_hp = max_hp
	# Position is set before add_child in EncounterManager._spawn_area, so this is
	# the spawn post — where return_home() sends a survivor on a checkpoint retry.
	_home = position
	add_to_group("enemies")


## Send a surviving enemy back to its spawn post and re-idle it (clears the ambush
## latch) — used when the player wipes and retries a checkpoint, so survivors
## don't stay parked where the death happened. A dying enemy is left alone.
func return_home() -> void:
	if _dead:
		return
	position = _home
	velocity = Vector2.ZERO
	_knockback = Vector2.ZERO
	_aggro = false
	_steer_time = 0.0


func take_damage(amount: int, from: Vector2) -> void:
	if _dead:
		return
	_hp -= amount
	_knockback = (global_position - from).normalized() * knockback_speed
	if _hp <= 0:
		_die()
	else:
		_sprite.modulate = Color(1.0, 0.4, 0.4)


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
	var chasing := false
	if target != null and _awake(target):
		var to_target := target.global_position - global_position
		if to_target.length() > 6.0:
			chasing = true
			moving = true
			_steer_time = maxf(0.0, _steer_time - delta)
			# Committed steer: keep sliding along the obstacle instead of
			# re-aiming at the player every frame (which just pins the enemy
			# back into the corner it is stuck on).
			_facing = _steer_dir if _steer_time > 0.0 else to_target.normalized()
			velocity = _facing * move_speed + _knockback
		else:
			velocity = _knockback
	else:
		velocity = _knockback

	var before := global_position
	move_and_slide()
	if chasing and _steer_time <= 0.0:
		_maybe_steer(before, delta, target)
	_try_contact_damage()
	_animate(moving, delta)


## Blocked-chaser detection, run after move_and_slide: intent to move but almost
## no ground covered against something collidable. Picks the collision tangent
## that points toward the player and commits to it for steer_duration.
func _maybe_steer(before: Vector2, delta: float, target: Node2D) -> void:
	if steer_duration <= 0.0 or get_slide_collision_count() == 0:
		return
	var progress := global_position.distance_to(before)
	if progress >= move_speed * delta * 0.3:
		return
	var tangent := get_slide_collision(0).get_normal().orthogonal()
	var to_target := target.global_position - global_position
	if tangent.dot(to_target) < 0.0:
		tangent = -tangent
	_steer_dir = tangent
	_steer_time = steer_duration


## Ambush latch: always awake when aggro_radius is 0 (default) or once triggered;
## otherwise wakes — permanently — the first frame a live player is within range.
func _awake(target: Node2D) -> bool:
	if aggro_radius <= 0.0 or _aggro:
		return true
	if global_position.distance_to(target.global_position) <= aggro_radius:
		_aggro = true
	return _aggro


func _nearest_player() -> Node2D:
	var best: Node2D = null
	var best_dist := INF
	for player in get_tree().get_nodes_in_group("players"):
		if not (player is Node2D):
			continue
		if player.has_method("is_targetable") and not player.is_targetable():
			continue
		var dist: float = global_position.distance_squared_to(player.global_position)
		if dist < best_dist:
			best_dist = dist
			best = player
	return best


func _try_contact_damage() -> void:
	if _contact_cd > 0.0:
		return
	for body in _contact.get_overlapping_bodies():
		if body.has_method("take_damage") and body.is_in_group("players"):
			body.take_damage(contact_damage, global_position)
			_contact_cd = contact_cooldown
			return


func _die() -> void:
	_dead = true
	_death_time = 0.0
	_sprite.modulate = Color.WHITE
	_contact.monitoring = false
	remove_from_group("enemies")
	if is_in_group("area_enemies"):
		remove_from_group("area_enemies")
	$CollisionShape2D.set_deferred("disabled", true)


func _animate(moving: bool, delta: float) -> void:
	_sprite.modulate = _sprite.modulate.lerp(Color.WHITE, 0.2)
	_anim_time += delta
	var column := int(_anim_time * anim_fps)
	if directional:
		_animate_directional(moving, column)
	else:
		var row := move_row if moving else idle_row
		_sprite.frame = row * sheet_columns + column % anim_frames


func _animate_directional(moving: bool, column: int) -> void:
	var base := DIR_WALK_DOWN if moving else DIR_IDLE_DOWN
	var flip := false
	var row := base
	if absf(_facing.x) >= absf(_facing.y):
		row = base + 1
		flip = _facing.x < 0.0
	elif _facing.y < 0.0:
		row = base + 2
	_sprite.flip_h = flip
	_sprite.frame = row * sheet_columns + column % DIR_FRAMES


func _animate_death(delta: float) -> void:
	_death_time += delta
	if directional:
		var col := mini(DIR_FRAMES - 1, int(_death_time / death_duration * DIR_FRAMES))
		_sprite.frame = DIR_DEATH_ROW * sheet_columns + col
	else:
		var col := mini(anim_frames - 1, int(_death_time / death_duration * anim_frames))
		_sprite.frame = death_row * sheet_columns + col
	if _death_time >= death_duration:
		queue_free()
