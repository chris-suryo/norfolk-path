class_name FollowCamera
extends Camera2D

## Camera that follows a target node and clamps to the level's painted bounds.
##
## In Slice 1 the target is the player, but it's resolved via a NodePath on
## purpose: in 2-player mode the target becomes a "midpoint" node sitting
## between both players — repoint the path, no script changes needed. Paths
## are resolved explicitly in _ready() (rather than via a typed @export Node
## reference) so a bad path fails loudly instead of leaving the camera
## silently parked at its own default (0, 0) position with no visible error.

## Path to the node this camera tracks (assigned in the scene — the player in
## Slice 1).
@export var target_path: NodePath

## Path to the TileMapLayer whose painted bounds clamp the camera. Empty path
## = no clamping.
@export var bounds_source_path: NodePath

var _target: Node2D
var _bounds_source: TileMapLayer


func _ready() -> void:
	# zoom > 1 magnifies: 3x makes the 16px pixel art read big and crisp.
	zoom = Vector2(3, 3)

	if target_path.is_empty():
		push_error("FollowCamera: target_path is unset — camera will not follow anything.")
	else:
		_target = get_node_or_null(target_path) as Node2D
		if _target == null:
			push_error("FollowCamera: target_path '%s' did not resolve to a Node2D." % target_path)

	if not bounds_source_path.is_empty():
		_bounds_source = get_node_or_null(bounds_source_path) as TileMapLayer
		if _bounds_source == null:
			push_error(
				(
					"FollowCamera: bounds_source_path '%s' did not resolve to a TileMapLayer."
					% bounds_source_path
				)
			)
		elif _bounds_source.tile_set != null:
			# Deferred so it runs after the level has painted its cells this
			# frame, regardless of node _ready() order.
			_apply_bounds.call_deferred()

	if _target != null:
		global_position = _target.global_position


func _physics_process(_delta: float) -> void:
	if _target != null:
		global_position = _target.global_position


func _apply_bounds() -> void:
	var used := _bounds_source.get_used_rect()
	var tile := _bounds_source.tile_set.tile_size
	# Convert the tilemap's used-cell rect into world-space pixel limits.
	var top_left := _bounds_source.to_global(Vector2(used.position * tile))
	var bottom_right := _bounds_source.to_global(Vector2(used.end * tile))
	limit_left = int(top_left.x)
	limit_top = int(top_left.y)
	limit_right = int(bottom_right.x)
	limit_bottom = int(bottom_right.y)
