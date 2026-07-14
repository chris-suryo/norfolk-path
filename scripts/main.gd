extends Node2D

## Scene orchestrator: places entities and spawns props from IslandMap.
##
## level.gd paints terrain; this script handles everything that must Y-sort
## against the players (trees, fences, the shop, the chicken) plus the
## bridge, which always draws under everyone (GroundProps, unsorted).
## The map is the single source of truth for all positions.

const DECOR_DIR := "res://assets/cute_fantasy/Cute_Fantasy_Free/Outdoor decoration/"

## Exact opaque box of the E-W walkway sprite inside Bridge_Wood.png
## (found by scanning the sheet's alpha channel — it is not 16px-aligned).
const BRIDGE_REGION := Rect2(5, 0, 38, 54)

var _rows := IslandMap.rows()
var _oak: Texture2D = load(DECOR_DIR + "Oak_Tree.png")
var _oak_small: Texture2D = load(DECOR_DIR + "Oak_Tree_Small.png")
var _fences: Texture2D = load(DECOR_DIR + "Fences.png")
var _bridge: Texture2D = load(DECOR_DIR + "Bridge_Wood.png")

@onready var _world: Node2D = $World
@onready var _ground_props: Node2D = $GroundProps


func _ready() -> void:
	var spawn := IslandMap.cell_center(IslandMap.find_one("S"))
	$World/Player.position = spawn
	$World/Player.respawn_point = spawn
	$World/Player2.position = spawn + Vector2(18, 0)
	$World/Player2.respawn_point = spawn + Vector2(18, 0)
	$World/Shop.position = IslandMap.cell_center(IslandMap.find_one("H"))
	$World/Ariana.position = IslandMap.cell_center(IslandMap.find_one("C"))
	_spawn_trees()
	_spawn_fences()
	_spawn_bridge()
	# Encounters, checkpoints, and death/respawn. Called AFTER players are
	# positioned so a saved-checkpoint resume overrides the default spawn.
	$World/EncounterManager.setup()


func _symbol(x: int, y: int) -> String:
	if y < 0 or y >= _rows.size() or x < 0 or x >= _rows[y].length():
		return "~"
	return _rows[y][x]


func _spawn_trees() -> void:
	for cell in IslandMap.find_all("T"):
		# Sprite offset puts the trunk base at the node origin (for Y-sort).
		_add_prop(_oak, Rect2(), Vector2(0, -30), cell, Vector2(0, -2), Vector2(12, 8))
	for cell in IslandMap.find_all("t"):
		# Middle sprite of the 3 in Oak_Tree_Small.png.
		_add_prop(
			_oak_small, Rect2(32, 0, 32, 48), Vector2(0, -16), cell, Vector2(0, -2), Vector2(10, 6)
		)


func _spawn_fences() -> void:
	for cell in IslandMap.find_all("F"):
		var left := _symbol(cell.x - 1, cell.y) == "F"
		var right := _symbol(cell.x + 1, cell.y) == "F"
		var up := _symbol(cell.x, cell.y - 1) == "F"
		var down := _symbol(cell.x, cell.y + 1) == "F"
		var piece: Vector2i
		var col_size: Vector2
		if left or right:
			piece = (
				Vector2i(2, 0) if left and right else (Vector2i(1, 0) if right else Vector2i(3, 0))
			)
			col_size = Vector2(16, 6)
		elif up or down:
			piece = Vector2i(0, 1) if up and down else (Vector2i(0, 0) if down else Vector2i(0, 2))
			col_size = Vector2(6, 16)
		else:
			piece = Vector2i(0, 3)
			col_size = Vector2(6, 6)
		var region := Rect2(piece.x * 16, piece.y * 16, 16, 16)
		_add_prop(_fences, region, Vector2.ZERO, cell, Vector2.ZERO, col_size)


func _spawn_bridge() -> void:
	var cells := IslandMap.find_all("B")
	if cells.is_empty():
		return
	var center := Vector2.ZERO
	for cell in cells:
		center += IslandMap.cell_center(cell)
	center /= cells.size()
	var sprite := Sprite2D.new()
	sprite.texture = _bridge
	sprite.region_enabled = true
	sprite.region_rect = BRIDGE_REGION
	sprite.position = center
	_ground_props.add_child(sprite)


func _add_prop(
	texture: Texture2D,
	region: Rect2,
	sprite_offset: Vector2,
	cell: Vector2i,
	collider_offset: Vector2,
	collider_size: Vector2
) -> void:
	var body := StaticBody2D.new()
	body.position = IslandMap.cell_center(cell)
	var sprite := Sprite2D.new()
	sprite.texture = texture
	if region.size != Vector2.ZERO:
		sprite.region_enabled = true
		sprite.region_rect = region
	sprite.offset = sprite_offset
	body.add_child(sprite)
	var collider := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = collider_size
	collider.shape = shape
	collider.position = collider_offset
	body.add_child(collider)
	_world.add_child(body)
