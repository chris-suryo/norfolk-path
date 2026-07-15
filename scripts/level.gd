class_name Level
extends TileMapLayer

## Terrain painter: renders IslandMap.MAP into tiles at runtime.
##
## Painting happens in code because this project is authored headlessly
## (TileMapLayer's packed tile data isn't safe to hand-write), and the map
## itself lives in scripts/island_map.gd as ASCII. Edge tiles (shorelines,
## path borders) are picked per-cell from the pack's 3x6 edge sheets by
## looking at the 8 neighbors — no editor terrain sets needed, and the same
## algorithm is mirrored in the scratchpad preview renderer, so layouts are
## verified visually before they ever reach the engine.
##
## Props and entities are NOT painted here — main.gd places those (they need
## Y-sorting against the players, which a tile layer can't provide).

enum Terrain { GRASS, PATH, WATER, WATER_WALKABLE }

const SOURCE_GRASS := 0
const SOURCE_PATH := 1
const SOURCE_WATER := 2
const SOURCE_WATER_WALKABLE := 3

const CENTER := Vector2i(1, 1)

## Edge-sheet atlas cell keyed by a land-neighbor bitmask (N=1, S=2, E=4,
## W=8). Sheet layout (verified by decoding the PNGs): rows 0-2 = 3x3 blob
## (corners/edges/center), rows 3-4 = inner corners, row 5 = decorative
## center variants. Unmapped combos fall back to the plain center — the map
## design keeps regions >= 2 tiles wide so those never occur.
const EDGE_BY_LAND_MASK := {
	1: Vector2i(1, 0),
	2: Vector2i(1, 2),
	4: Vector2i(2, 1),
	8: Vector2i(0, 1),
	5: Vector2i(2, 0),
	9: Vector2i(0, 0),
	6: Vector2i(2, 2),
	10: Vector2i(0, 2),
}

var _rows: PackedStringArray


func _ready() -> void:
	_rows = IslandMap.rows()
	_paint()


static func terrain_of(symbol: String) -> Terrain:
	match symbol:
		# open water + everything that floats ON the lake (boat, capybaras,
		# swimming duck/swan) — all solid so the player can't walk into the lake.
		"~", "O", "k", "a", "l", "@":
			return Terrain.WATER
		"B":
			return Terrain.WATER_WALKABLE
		# path, spawn, and the grape-bower arch (walk underneath it).
		"#", "S", "g":
			return Terrain.PATH
		_:
			# grass catch-all — also farm (D/Q) and cobble (c): all walkable,
			# their look comes from the baked ground image, not the tilemap.
			return Terrain.GRASS


func _paint() -> void:
	for y in _rows.size():
		var row := _rows[y]
		for x in row.length():
			var cell := Vector2i(x, y)
			match terrain_of(row[x]):
				Terrain.GRASS:
					set_cell(cell, SOURCE_GRASS, Vector2i.ZERO)
				Terrain.PATH:
					set_cell(cell, SOURCE_PATH, _edge_cell(x, y, false))
				Terrain.WATER:
					set_cell(cell, SOURCE_WATER, _edge_cell(x, y, true))
				Terrain.WATER_WALKABLE:
					# Same water art, collision-free source — the bridge
					# sprite (main.gd) draws on top.
					set_cell(cell, SOURCE_WATER_WALKABLE, _edge_cell(x, y, true))


func _is_same(x: int, y: int, water: bool) -> bool:
	# Off-map counts as water: the map edge is open ocean.
	if y < 0 or y >= _rows.size() or x < 0 or x >= _rows[y].length():
		return water
	var t := terrain_of(_rows[y][x])
	if water:
		return t == Terrain.WATER or t == Terrain.WATER_WALKABLE
	return t == Terrain.PATH


## Picks the atlas cell in a 3x6 edge sheet for the material cell at (x, y).
func _edge_cell(x: int, y: int, water: bool) -> Vector2i:
	var mask := 0
	if not _is_same(x, y - 1, water):
		mask |= 1
	if not _is_same(x, y + 1, water):
		mask |= 2
	if not _is_same(x + 1, y, water):
		mask |= 4
	if not _is_same(x - 1, y, water):
		mask |= 8
	if mask == 0:
		return _interior_cell(x, y, water)
	return EDGE_BY_LAND_MASK.get(mask, CENTER)


## No land on any cardinal: inner corners for diagonal land, else the plain
## center with deterministic decorative variants sprinkled in.
func _interior_cell(x: int, y: int, water: bool) -> Vector2i:
	var result := CENTER
	if not _is_same(x + 1, y + 1, water):
		result = Vector2i(0, 3)
	elif not _is_same(x - 1, y + 1, water):
		result = Vector2i(1, 3)
	elif not _is_same(x + 1, y - 1, water):
		result = Vector2i(0, 4)
	elif not _is_same(x - 1, y - 1, water):
		result = Vector2i(1, 4)
	elif (x * 7 + y * 13) % 17 == 0:
		result = Vector2i((x + y) % 3, 5)
	return result
