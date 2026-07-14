class_name EncounterManager
extends Node

## Drives the three path areas: spawn, shop, library-approach. Each area has a
## checkpoint (an Area2D trigger that sets Game.checkpoint + autosaves), a set of
## enemies, and a cleared flag. On a player's death the current checkpoint's area
## resets (its enemies respawn) unless it was already cleared; a cleared area
## never respawns. Positions come from the map anchors (S/H/C) + hand-picked
## on-path cells, so nothing here edits the frozen island_map.gd.
##
## setup() is called by main.gd AFTER it positions the players, so a resume (load
## a saved checkpoint) overrides the default spawn placement rather than being
## clobbered by main._ready running last.

const SLIME_SCENE := preload("res://scenes/enemy_slime.tscn")
const SKELETON_SCENE := preload("res://scenes/enemy_skeleton.tscn")
const TRIGGER_RADIUS := 40.0

var _areas: Array = []
var _world: Node2D


func setup() -> void:
	_world = get_parent()
	_build_areas()
	for area in _areas:
		_spawn_area(area)
	_make_triggers()
	for player in get_tree().get_nodes_in_group("players"):
		player.downed.connect(_on_player_downed.bind(player))
	_apply_resume()


func _process(_delta: float) -> void:
	for area in _areas:
		if area.cleared or area.specs.is_empty() or not area.spawned:
			continue
		var alive: Array = []
		for enemy in area.instances:
			if is_instance_valid(enemy):
				alive.append(enemy)
		area.instances = alive
		if alive.is_empty():
			area.cleared = true


func _build_areas() -> void:
	# center cell (checkpoint) + [scene, cell] enemy specs — all on walkable tiles.
	_areas = [
		_make_area(
			0, Vector2i(9, 20), [[SLIME_SCENE, Vector2i(14, 20)], [SLIME_SCENE, Vector2i(17, 21)]]
		),
		_make_area(1, Vector2i(24, 20), [[SKELETON_SCENE, Vector2i(31, 20)]]),
		_make_area(2, Vector2i(44, 22), []),
	]


func _make_area(id: int, center_cell: Vector2i, specs: Array) -> Dictionary:
	var built: Array = []
	for spec in specs:
		built.append({"scene": spec[0], "pos": IslandMap.cell_center(spec[1])})
	return {
		"id": id,
		"center": IslandMap.cell_center(center_cell),
		"specs": built,
		"instances": [],
		"cleared": false,
		"spawned": false,
	}


func _spawn_area(area: Dictionary) -> void:
	for spec in area.specs:
		var enemy := (spec.scene as PackedScene).instantiate()
		enemy.position = spec.pos
		_world.add_child(enemy)
		area.instances.append(enemy)
	area.spawned = true


func _make_triggers() -> void:
	for area in _areas:
		var trigger := Area2D.new()
		trigger.position = area.center
		trigger.collision_layer = 0
		trigger.collision_mask = 2
		var collider := CollisionShape2D.new()
		var shape := CircleShape2D.new()
		shape.radius = TRIGGER_RADIUS
		collider.shape = shape
		trigger.add_child(collider)
		add_child(trigger)
		trigger.body_entered.connect(_on_area_entered.bind(area))


func _apply_resume() -> void:
	Game.load_state()
	if Game.checkpoint <= 0:
		return
	var area := _area_by_id(Game.checkpoint)
	for prior in _areas:
		if prior.id < Game.checkpoint and not prior.cleared:
			_clear_area(prior)
	for player in get_tree().get_nodes_in_group("players"):
		player.global_position = area.center
		player.respawn_point = area.center


func _on_area_entered(body: Node, area: Dictionary) -> void:
	if not body.is_in_group("players"):
		return
	if area.id > Game.checkpoint:
		Game.checkpoint = area.id
		Game.save()
	for player in get_tree().get_nodes_in_group("players"):
		player.respawn_point = area.center


func _on_player_downed(player: Node) -> void:
	var area := _area_by_id(Game.checkpoint)
	player.respawn_at(area.center)
	_reset_area(area)


func _reset_area(area: Dictionary) -> void:
	if area.cleared:
		return
	for enemy in area.instances:
		if is_instance_valid(enemy):
			enemy.queue_free()
	area.instances = []
	area.spawned = false
	_spawn_area(area)


func _clear_area(area: Dictionary) -> void:
	for enemy in area.instances:
		if is_instance_valid(enemy):
			enemy.queue_free()
	area.instances = []
	area.cleared = true


func _area_by_id(id: int) -> Dictionary:
	for area in _areas:
		if area.id == id:
			return area
	return _areas[0]
