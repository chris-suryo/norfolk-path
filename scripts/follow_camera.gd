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

## Free-zoom (mouse wheel) bounds. The pause-menu presets stay Far 2.0 / Normal
## 2.5 / Close 3.0; the wheel goes wider than "Far" (down to ZOOM_MIN) so you can
## pull back to see the whole area — Chris's "zoom out as much as I want" ask.
const ZOOM_STEP := 0.15
const ZOOM_MIN := 0.6
const ZOOM_MAX := 6.0

## Path to the node this camera tracks (the players' midpoint node).
@export var target_path: NodePath

## Camera magnification: higher = closer. 3.0 felt too tight in the first
## browser test; tune live in the Inspector while the game runs.
@export var zoom_level := 2.5

## Path to the TileMapLayer whose painted bounds clamp the camera. Empty path
## = no clamping.
@export var bounds_source_path: NodePath

var _target: Node2D
var _bounds_source: TileMapLayer


func _ready() -> void:
	# Restore the zoom the player last chose: this node is rebuilt on every scene
	# reload (doors/edges reload main.tscn), so without this it snaps back to the
	# export default. Set before `zoom` so the deferred _apply_bounds below sizes
	# interior clamps against the restored zoom, not the default.
	zoom_level = Game.camera_zoom
	zoom = Vector2(zoom_level, zoom_level)

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


## Mouse wheel = free zoom (scroll up in / down out), past the pause-menu presets,
## clamped to [ZOOM_MIN, ZOOM_MAX]. Reuses set_zoom_preset so bounds recompute. Held
## off during the intro/resolution cutscene, whose camera is script-driven; a
## paused tree (pause menu, dialogue) already stops this from firing.
func _unhandled_input(event: InputEvent) -> void:
	if Game.cutscene_active:
		return
	if not (event is InputEventMouseButton and event.pressed):
		return
	if event.button_index == MOUSE_BUTTON_WHEEL_UP:
		set_zoom_preset(clampf(zoom_level + ZOOM_STEP, ZOOM_MIN, ZOOM_MAX))
		get_viewport().set_input_as_handled()
	elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
		set_zoom_preset(clampf(zoom_level - ZOOM_STEP, ZOOM_MIN, ZOOM_MAX))
		get_viewport().set_input_as_handled()


## Live zoom change from the pause menu's Zoom presets. Recompute the limits:
## on a level smaller than the view they are a view-sized centred window, and
## the view size just changed with the zoom.
func set_zoom_preset(value: float) -> void:
	zoom_level = value
	zoom = Vector2(value, value)
	# Persist so the choice survives the next scene reload. Covers both the
	# pause-menu presets and the mouse-wheel free-zoom (both route through here).
	Game.camera_zoom = value
	if _bounds_source != null and _bounds_source.tile_set != null:
		_apply_bounds()


func _apply_bounds() -> void:
	var used := _bounds_source.get_used_rect()
	var tile := _bounds_source.tile_set.tile_size
	# Convert the tilemap's used-cell rect into world-space pixel limits.
	var top_left := _bounds_source.to_global(Vector2(used.position * tile))
	var bottom_right := _bounds_source.to_global(Vector2(used.end * tile))
	# A level smaller than the view (an interior room) would jam the camera to a
	# corner; instead lock that axis to a view-sized window centred on the room.
	# Outdoor levels are far larger than the view, so they clamp normally.
	var view := get_viewport_rect().size / zoom
	var x := _axis_limits(top_left.x, bottom_right.x, view.x)
	var y := _axis_limits(top_left.y, bottom_right.y, view.y)
	limit_left = x[0]
	limit_right = x[1]
	limit_top = y[0]
	limit_bottom = y[1]


func _axis_limits(lo: float, hi: float, view: float) -> Array:
	if hi - lo >= view:
		return [int(lo), int(hi)]
	var mid := (lo + hi) / 2.0
	return [int(mid - view / 2.0), int(mid + view / 2.0)]
