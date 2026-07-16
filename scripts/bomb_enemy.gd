class_name BombEnemy
extends Enemy

## A stationary "bombschroom": it never chases. It idles until a live player comes
## within detonate_radius, then runs a short flashing wind-up and explodes — a
## one-shot area hit to everyone within blast_radius, plus a gas puff. The player
## can defuse it by killing it during the wind-up (one solid sword hit), which is
## the risk/reward: get close enough to hit it and you're inside the blast unless
## you're quick or roll clear.
##
## Extends Enemy purely for HP / take_damage / death / the "enemies" group so the
## EncounterManager counts it like any other camp enemy. Movement, contact, and
## animation are fully overridden here (the base chase/contact never runs).

const GAS_SCENE := preload("res://scenes/gas_cloud.tscn")

## Player proximity that starts the wind-up (px).
@export var detonate_radius := 22.0
## Radius of the actual blast damage when it goes off (px) — larger than the
## trigger, so you must move/roll clear during the wind-up, not just stand.
@export var blast_radius := 30.0
## Seconds of flashing wind-up between trigger and blast.
@export var windup := 0.6
## Frames per second for the idle bob (sheet row 0, frames 0-1).
@export var idle_fps := 2.0

var _detonating := false
var _windup_time := 0.0


func _physics_process(delta: float) -> void:
	if _dead:
		return
	velocity = Vector2.ZERO
	move_and_slide()
	if _detonating:
		_windup_time += delta
		var flash := int(_windup_time * 20.0) % 2 == 0
		_sprite.modulate = Color(1.0, 0.5, 0.5) if flash else Color.WHITE
		_sprite.scale = Vector2.ONE * (1.0 + 0.4 * (_windup_time / windup))
		if _windup_time >= windup:
			_explode()
		return
	_idle_anim(delta)
	var target := _nearest_player()
	if target != null and global_position.distance_to(target.global_position) <= detonate_radius:
		_detonating = true


## Defused before it pops (killed during idle or wind-up): fade out, no blast.
func _die() -> void:
	if _dead:
		return
	super()
	var tween := create_tween()
	tween.tween_property(_sprite, "modulate:a", 0.0, 0.2)
	tween.tween_callback(queue_free)


## Reset for a checkpoint retry (EncounterManager rearm) — also cancels a wind-up.
func return_home() -> void:
	super()
	_detonating = false
	_windup_time = 0.0
	_sprite.scale = Vector2.ONE
	_sprite.modulate = Color.WHITE


func _explode() -> void:
	_dead = true
	remove_from_group("enemies")
	for player in get_tree().get_nodes_in_group("players"):
		if not player.has_method("take_damage") or not player.is_targetable():
			continue
		if global_position.distance_to(player.global_position) <= blast_radius:
			player.take_damage(contact_damage, global_position)
	var gas := GAS_SCENE.instantiate()
	gas.global_position = global_position
	get_parent().add_child(gas)
	queue_free()


func _idle_anim(delta: float) -> void:
	_anim_time += delta
	_sprite.frame = int(_anim_time * idle_fps) % 2
	# Threat tell (playtest round-1): decor amanitas hold perfectly still, so a
	# visible breathe + faint warm flush marks this one as alive and dangerous
	# before the player is inside detonate_radius.
	var breathe := 0.5 + 0.5 * sin(_anim_time * 3.5)
	_sprite.scale = Vector2.ONE * (1.0 + 0.1 * breathe)
	_sprite.modulate = Color(1.0, 1.0 - 0.12 * breathe, 1.0 - 0.12 * breathe)
