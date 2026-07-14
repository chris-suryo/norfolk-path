class_name Midpoint
extends Node2D

## Sits at the midpoint of two nodes — the camera target for shared-screen
## 2-player. Deliberately has NO leash/clamp logic yet: the players can walk
## apart until both leave the view. That's intentional for the co-op test —
## feel the problem in playtest first, then decide the camera rule.

## The two nodes to average (the two players).
@export var target_a_path: NodePath
@export var target_b_path: NodePath

var _a: Node2D
var _b: Node2D


func _ready() -> void:
	_a = get_node_or_null(target_a_path) as Node2D
	_b = get_node_or_null(target_b_path) as Node2D
	if _a == null or _b == null:
		push_error("Midpoint: target paths did not resolve; camera will not track properly.")
	_update_position()


func _physics_process(_delta: float) -> void:
	_update_position()


func _update_position() -> void:
	if _a != null and _b != null:
		global_position = (_a.global_position + _b.global_position) / 2.0
	elif _a != null:
		global_position = _a.global_position
