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
const BOSS_SCENE := preload("res://scenes/boss_irene.tscn")
const TRIGGER_RADIUS := 40.0

## Co-op: a downed teammate revives once no live enemy is within this radius of
## any player (the fight around them is cleared).
const REVIVE_RADIUS := 130.0

var _areas: Array = []
var _world: Node2D


func setup() -> void:
	_world = get_parent()
	_build_areas()
	for area in _areas:
		_spawn_area(area)
	_make_triggers()
	for player in get_tree().get_nodes_in_group("players"):
		player.downed.connect(_on_downed)
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
	if Game.player_count >= 2:
		_update_coop_revive()


func _build_areas() -> void:
	# center cell (checkpoint) + [scene, cell] enemy specs — all on walkable tiles.
	_areas = [
		_make_area(
			0, Vector2i(9, 20), [[SLIME_SCENE, Vector2i(14, 20)], [SLIME_SCENE, Vector2i(17, 21)]]
		),
		_make_area(1, Vector2i(24, 20), [[SKELETON_SCENE, Vector2i(31, 20)]]),
		_make_area(2, Vector2i(44, 22), [[BOSS_SCENE, Vector2i(45, 22)]]),
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
	# The player-select choice wins over the saved player_count; the rest of the
	# save (checkpoint / boss_defeated) is what we resume from.
	var chosen := Game.player_count
	Game.load_state()
	Game.player_count = chosen
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
	_activate_area(area)


func _on_downed() -> void:
	# Solo, or co-op with everyone down: respawn all at the checkpoint + reset
	# the area. Co-op with a survivor: the downed player waits for a clear-revive.
	if not _all_players_down():
		return
	var area := _area_by_id(Game.checkpoint)
	for player in get_tree().get_nodes_in_group("players"):
		player.respawn_at(area.center)
	_reset_area(area)


func _update_coop_revive() -> void:
	var downed: Array = []
	var any_up := false
	for player in get_tree().get_nodes_in_group("players"):
		if player.is_targetable():
			any_up = true
		else:
			downed.append(player)
	if not any_up or downed.is_empty() or _enemies_near_players(REVIVE_RADIUS):
		return
	for player in downed:
		player.respawn_at(player.global_position)


func _all_players_down() -> bool:
	for player in get_tree().get_nodes_in_group("players"):
		if player.is_targetable():
			return false
	return true


func _enemies_near_players(radius: float) -> bool:
	var players := get_tree().get_nodes_in_group("players")
	for enemy in get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(enemy):
			continue
		for player in players:
			if enemy.global_position.distance_to(player.global_position) <= radius:
				return true
	return false


func _reset_area(area: Dictionary) -> void:
	if area.cleared:
		return
	for enemy in area.instances:
		if is_instance_valid(enemy):
			enemy.queue_free()
	area.instances = []
	area.spawned = false
	_spawn_area(area)
	# On a retry the player is already standing in the area, so re-activate any
	# boss immediately (a fresh boss would otherwise wait for a re-entry that
	# never fires while the body already overlaps the trigger).
	_activate_area(area)


func _activate_area(area: Dictionary) -> void:
	for enemy in area.instances:
		if is_instance_valid(enemy) and enemy.has_method("activate"):
			enemy.activate()


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
