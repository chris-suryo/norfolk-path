class_name Level
extends TileMapLayer

## Grass-island level, painted in code at runtime.
##
## The layout is generated with set_cell() rather than hand-painted in the
## editor because this project was authored headlessly (no editor available,
## and a TileMapLayer's binary tile data isn't safe to hand-write). Theme:
## a grass island ringed by impassable water, a path winding from the west
## spawn toward a pond at the east end. Uses the Cute Fantasy "middle" fill
## tiles only — edge/corner autotiling is a later polish pass.
##
## Layout map (tile coords, 60x40):
##   - water ring: 2 tiles thick around the border
##   - pond: x 46..59, y 10..26 (merges into the east ring, reads as a bay)
##   - path leg 1: x 2..31, y 20..21 (west spawn -> bend)
##   - path leg 2: x 30..31, y 12..21 (the bend, heading north)
##   - path leg 3: x 30..45, y 12..13 (east to the pond edge)
##   - Evan's shop sits just north of leg 1 (placed in main.tscn)

const SOURCE_GRASS := 0
const SOURCE_PATH := 1
const SOURCE_WATER := 2
const ATLAS_ORIGIN := Vector2i(0, 0)

## Level size in tiles. 60x40 @ 16px = 960x640 px, well past the 640x360 view.
const WIDTH := 60
const HEIGHT := 40

## Water ring thickness in tiles.
const RING := 2


func _ready() -> void:
	_paint()


func _paint() -> void:
	# Grass everywhere, water ring around the outer edge.
	for y in HEIGHT:
		for x in WIDTH:
			var in_ring := x < RING or y < RING or x >= WIDTH - RING or y >= HEIGHT - RING
			var source := SOURCE_WATER if in_ring else SOURCE_GRASS
			set_cell(Vector2i(x, y), source, ATLAS_ORIGIN)

	# Pond at the east end, connected to the ring so it reads as a bay.
	_fill_rect(46, 10, WIDTH - 46, 17, SOURCE_WATER)

	# Path from the west spawn to the pond edge: two horizontal legs joined
	# by a vertical bend.
	_fill_rect(2, 20, 30, 2, SOURCE_PATH)
	_fill_rect(30, 12, 2, 10, SOURCE_PATH)
	_fill_rect(30, 12, 16, 2, SOURCE_PATH)


func _fill_rect(x: int, y: int, w: int, h: int, source: int) -> void:
	for dy in h:
		for dx in w:
			set_cell(Vector2i(x + dx, y + dy), source, ATLAS_ORIGIN)
