class_name MapData
extends RefCounted

## A parsed ASCII level map: the geometry + symbol-lookup helpers that used to
## live as statics on IslandMap, now per-instance so the game can hold more than
## one level at a time. Built from a map string — each level script exposes a
## `MAP` const (scripts/island_map.gd, scripts/cove_map.gd, ...), and
## LevelRegistry.make_map() wraps the active one in a MapData.

const TILE_SIZE := 16

var _rows: PackedStringArray


func _init(map_text: String) -> void:
	_rows = map_text.strip_edges().split("\n")


func rows() -> PackedStringArray:
	return _rows


func width() -> int:
	return _rows[0].length() if _rows.size() > 0 else 0


func height() -> int:
	return _rows.size()


## World-space center of a map cell.
func cell_center(cell: Vector2i) -> Vector2:
	return Vector2(cell) * TILE_SIZE + Vector2(TILE_SIZE, TILE_SIZE) / 2.0


## All cells carrying the given symbol.
func find_all(symbol: String) -> Array[Vector2i]:
	var found: Array[Vector2i] = []
	for y in _rows.size():
		var row := _rows[y]
		for x in row.length():
			if row[x] == symbol:
				found.append(Vector2i(x, y))
	return found


## The single cell carrying the given symbol; pushes an error if absent.
func find_one(symbol: String) -> Vector2i:
	var found := find_all(symbol)
	if found.is_empty():
		push_error("MapData: no '%s' symbol in map." % symbol)
		return Vector2i.ZERO
	return found[0]
