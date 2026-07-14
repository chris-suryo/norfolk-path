class_name FollowCamera
extends Camera2D

## Camera that follows a target node and clamps to the level's painted bounds.
##
## In Slice 1 the target is the player, but it's a plain Node2D reference on
## purpose: in 2-player mode the target becomes a "midpoint" node sitting between
## both players, with no changes needed here. Clamping is derived from a
## TileMapLayer's used rect, so the camera never scrolls past the level edge.

## Node this camera tracks (assigned in the scene — the player in Slice 1).
@export var target: Node2D

## TileMapLayer whose painted bounds clamp the camera. If unset, no clamping.
@export var bounds_source: TileMapLayer


func _ready() -> void:
	# zoom > 1 magnifies: 3x makes the 16px pixel art read big and crisp.
	zoom = Vector2(3, 3)
	if bounds_source != null and bounds_source.tile_set != null:
		# Deferred so it runs after the level has painted its cells this frame,
		# regardless of node _ready() order.
		_apply_bounds.call_deferred()
	if target != null:
		global_position = target.global_position


func _physics_process(_delta: float) -> void:
	if target != null:
		global_position = target.global_position


func _apply_bounds() -> void:
	var used := bounds_source.get_used_rect()
	var tile := bounds_source.tile_set.tile_size
	# Convert the tilemap's used-cell rect into world-space pixel limits.
	var top_left := bounds_source.to_global(Vector2(used.position * tile))
	var bottom_right := bounds_source.to_global(Vector2(used.end * tile))
	limit_left = int(top_left.x)
	limit_top = int(top_left.y)
	limit_right = int(bottom_right.x)
	limit_bottom = int(bottom_right.y)
