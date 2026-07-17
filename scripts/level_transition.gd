class_name LevelTransition
extends Area2D

## The ONE travel mechanism: a proximity volume that sends the party to another
## level. Serves both map-edge crossings (valley <-> cove) and building doors
## (valley <-> cottage interior) — an interior is just a small level. main.gd
## builds these from each level's `transitions` registry data, so travel is map
## data, not new map symbols.
##
## Any player entering triggers travel for BOTH players: the scene reloads with
## the target level set, so nobody is stranded (co-op friendly).
##
## Arm-on-exit: the arriving player usually spawns ON the return volume (a door
## you just walked through). The trigger starts DISARMED and only arms once no
## player overlaps it — so you can step off without bouncing straight back.

@export var target_level: String
@export var target_entry: String

var _armed := false


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	# Arm on the next physics frame if nothing is already standing in the volume
	# (e.g. an edge exit the player did not spawn on).
	_arm_if_clear.call_deferred()


func _on_body_entered(body: Node) -> void:
	if _armed and body is Player:
		_travel()


func _on_body_exited(_body: Node) -> void:
	_arm_if_clear()


## Arm only when no player is inside — the arrival bounce-guard.
func _arm_if_clear() -> void:
	if _armed:
		return
	for body in get_overlapping_bodies():
		if body is Player:
			return
	_armed = true


func _travel() -> void:
	# The quest-complete screen is queued — don't let a door swallow it.
	if Game.win_pending:
		return
	_armed = false
	Game.current_level_id = target_level
	Game.current_entry = target_entry
	# A door/edge crossing is not a save resume — spawn at the entry, not at a
	# valley checkpoint.
	Game.resume_requested = false
	Game.change_scene("res://scenes/main.tscn")
