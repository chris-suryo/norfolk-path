class_name Level
extends TileMapLayer

## Placeholder level, painted in code at runtime.
##
## The layout is generated with set_cell() rather than hand-painted in the
## editor because this project was authored headlessly (no editor available, and
## a TileMapLayer's binary tile data isn't safe to hand-write). It uses the
## placeholder TileSet's two tiles — floor (walkable) and wall (collision) — so
## dropping in real Cute Fantasy art is a tileset swap, not a level rebuild.
## It's intentionally larger than one screen so the follow camera actually
## scrolls and clamps.

const SOURCE_ID := 0
const FLOOR_ATLAS := Vector2i(0, 0)
const WALL_ATLAS := Vector2i(1, 0)

## Level size in tiles. 60x40 @ 16px = 960x640 px, well past the 640x360 view.
const WIDTH := 60
const HEIGHT := 40


func _ready() -> void:
	_paint()


func _paint() -> void:
	# Floor everywhere, with a solid wall ring around the outer edge.
	for y in HEIGHT:
		for x in WIDTH:
			var is_border := x == 0 or y == 0 or x == WIDTH - 1 or y == HEIGHT - 1
			var atlas := WALL_ATLAS if is_border else FLOOR_ATLAS
			set_cell(Vector2i(x, y), SOURCE_ID, atlas)

	# A few interior walls so there's real geometry to navigate around.
	_wall_rect(10, 8, 6, 2)
	_wall_rect(40, 6, 2, 12)
	_wall_rect(18, 24, 14, 2)
	_wall_rect(30, 12, 2, 8)


func _wall_rect(x: int, y: int, w: int, h: int) -> void:
	for dy in h:
		for dx in w:
			set_cell(Vector2i(x + dx, y + dy), SOURCE_ID, WALL_ATLAS)
