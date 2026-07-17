class_name EncounterManager
extends Node

## Drives the path areas west->east: village slimes, a lone forest skeleton, the
## forest camp cluster, then the library boss. Each area has a checkpoint (an
## x-position on the road), a set of enemies, and a cleared flag.
##
## Checkpoints are recorded by PROGRESS, not by a trigger volume: _process tracks
## the furthest area a player has walked past (by world-x) and advances
## Game.checkpoint monotonically + autosaves. This is reliable regardless of road
## width or which edge the player hugs — the old 40px Area2D triggers could be
## missed while a camp skeleton (110px aggro) still reached and killed you,
## stranding the checkpoint behind you.
##
## On a wipe, players revive at the current checkpoint's road spot and the area is
## REARMED, not re-spawned: enemies the player already killed stay dead, survivors
## just reset to their post and idle again. The boss area is the exception — a
## boss retry re-spawns her to full HP. A cleared area never comes back.
##
## setup() is called by main.gd AFTER it positions the players, so a Continue
## resume overrides the default village spawn rather than being clobbered by
## main._ready running last.

const SLIME_SCENE := preload("res://scenes/enemy_slime.tscn")
const SKELETON_SCENE := preload("res://scenes/enemy_skeleton.tscn")
const BOMB_SCENE := preload("res://scenes/enemy_bombschroom.tscn")
const BOWMAN_SCENE := preload("res://scenes/enemy_bowman.tscn")
const MAGE_SCENE := preload("res://scenes/enemy_mage.tscn")
const BAT_SCENE := preload("res://scenes/enemy_bat.tscn")
const BIG_SLIME_SCENE := preload("res://scenes/enemy_slime_big.tscn")
const BOSS_SCENE := preload("res://scenes/boss_irene.tscn")
# The boss moved to id 4 when the mid-road area landed at 3. An old save with
# checkpoint 3 now resumes one beat earlier (the new area) and simply walks
# forward — the checkpoint re-advances monotonically.
const BOSS_ID := 4

## Co-op: a downed teammate revives once no live enemy is within this radius of
## any player (the fight around them is cleared).
const REVIVE_RADIUS := 130.0

var _areas: Array = []
var _world: Node2D
var _hud: Node
var _map: MapData
var _beacons := {}


func setup(hud: Node, encounters_id: String, map_data: MapData) -> void:
	_world = get_parent()
	_hud = hud
	_map = map_data
	_build_areas(encounters_id)
	# Peaceful level (no areas): nothing to spawn, and _apply_resume would index
	# an empty list. The checkpoint/respawn system is valley-internal.
	if _areas.is_empty():
		return
	_spawn_beacons()
	for area in _areas:
		_spawn_area(area)
	for player in get_tree().get_nodes_in_group("players"):
		player.downed.connect(_on_downed)
	_apply_resume()


func _spawn_beacons() -> void:
	for area in _areas:
		var beacon := CheckpointBeacon.new()
		beacon.position = area.beacon_center
		_world.add_child(beacon)
		_beacons[area.id] = beacon
		beacon.set_active(area.id <= Game.checkpoint)


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
			# Record on the autoload so this clear survives a change_scene: a door
			# round-trip must not respawn a beaten area (R4-43).
			Game.mark_area_cleared(area.id)
	_update_checkpoint()
	if Game.player_count >= 2:
		_update_coop_revive()


func _build_areas(encounters_id: String) -> void:
	if encounters_id != "valley":
		_areas = []
		return
	# center cell (checkpoint road spot) + [scene, cell] enemy specs — all on
	# walkable tiles of the valley-1 (192x48) map, west -> east along the road:
	# spawn/west village (slimes) -> lone forest skeleton (a taste) -> the forest
	# CAMP (3 skeletons + 1 stationary bombschroom guarding the western entry at
	# (117,33)) -> library approach (boss). The camp skeletons are aggro-gated
	# (enemy_skeleton.tscn) so they wake on approach, not at load.
	# The camp checkpoint (108,24) sits on the road WEST of the camp's ~110px
	# aggro edge (~x1818), so it records before the skeletons wake and a wipe
	# respawns you on the road, not inside the clearing.
	_areas = [
		_make_area(
			0,
			Vector2i(45, 28),
			Vector2i(45, 30),
			[[SLIME_SCENE, Vector2i(50, 28)], [SLIME_SCENE, Vector2i(55, 28)]]
		),
		# The lone skeleton gains a bowman on the ridge north of the road bend —
		# the player's first taste of dodging projectiles (and of shooting back).
		_make_area(
			1,
			Vector2i(70, 26),
			Vector2i(70, 28),
			[[SKELETON_SCENE, Vector2i(95, 21)], [BOWMAN_SCENE, Vector2i(101, 18)]]
		),
		# The forest camp: melee wall up front, a mage lobbing bolts from the
		# clearing's north lip, bats harrying the flanks.
		_make_area(
			2,
			Vector2i(108, 24),
			Vector2i(108, 26),
			[
				[BOMB_SCENE, Vector2i(117, 33)],
				[SKELETON_SCENE, Vector2i(124, 32)],
				[SKELETON_SCENE, Vector2i(120, 35)],
				[SKELETON_SCENE, Vector2i(124, 35)],
				[MAGE_SCENE, Vector2i(122, 30)],
				[BAT_SCENE, Vector2i(118, 31)],
				[BAT_SCENE, Vector2i(126, 34)],
			]
		),
		# Mid-road pacing beat before the library: a tank slime astride the road
		# with bat escorts.
		_make_area(
			3,
			Vector2i(132, 26),
			Vector2i(132, 28),
			[
				[BIG_SLIME_SCENE, Vector2i(138, 26)],
				[BAT_SCENE, Vector2i(135, 25)],
				[BAT_SCENE, Vector2i(141, 27)],
			]
		),
		_make_area(
			BOSS_ID, Vector2i(156, 26), Vector2i(156, 28), [[BOSS_SCENE, Vector2i(162, 26)]]
		),
	]


func _make_area(id: int, center_cell: Vector2i, beacon_cell: Vector2i, specs: Array) -> Dictionary:
	var built: Array = []
	for spec in specs:
		built.append({"scene": spec[0], "pos": _map.cell_center(spec[1])})
	return {
		"id": id,
		"center": _map.cell_center(center_cell),
		"beacon_center": _map.cell_center(beacon_cell),
		"specs": built,
		"instances": [],
		"cleared": false,
		"spawned": false,
	}


func _spawn_area(area: Dictionary) -> void:
	for spec in area.specs:
		var enemy := (spec.scene as PackedScene).instantiate()
		enemy.position = spec.pos
		if enemy.has_signal("defeated"):
			enemy.defeated.connect(_on_boss_defeated)
		_world.add_child(enemy)
		area.instances.append(enemy)
	area.spawned = true


## Re-derive persistent run state after setup() rebuilt every area from scratch:
## re-clear beaten areas (Game.cleared_areas + the saved checkpoint) and re-wake
## the boss if the run reached her — on EVERY entry, so a door round-trip doesn't
## resurrect the gauntlet (R4-43/44). Only the final party-reposition is Continue-
## specific; a New Game (checkpoint 0, empty cleared_areas) is left untouched.
func _apply_resume() -> void:
	# A defeated boss stays defeated on ANY re-entry — a Continue, or walking back
	# into the valley from the cove (which is not a checkpoint resume). Otherwise
	# she would respawn at full HP in her already-cleared library.
	if Game.boss_defeated:
		_clear_area(_area_by_id(BOSS_ID))
	# Cleared + boss-awake state is re-derived on EVERY entry, not just a Continue:
	# every door/edge crossing sets resume_requested false, and this manager (with
	# its per-area `cleared` flags) was just freed and rebuilt by the scene swap.
	# Only the party-reposition at the end is Continue-specific.
	#
	# Areas the party already beat stay beaten — Game.cleared_areas survived the
	# swap. This is what stops a door round-trip resurrecting the camp (R4-43),
	# regardless of where the checkpoint happens to sit.
	for area in _areas:
		if area.id in Game.cleared_areas and not area.cleared:
			_clear_area(area)
	# A saved checkpoint also implies the earlier areas are done — clear them too.
	# Covers a cold Continue (fresh launch) where cleared_areas is empty but the
	# checkpoint was loaded from disk.
	for prior in _areas:
		if prior.id < Game.checkpoint and not prior.cleared:
			_clear_area(prior)
	# Wake the boss whenever the run has reached her checkpoint, however the party
	# arrived. Reaching the library (its door is east of her x-only checkpoint)
	# wakes her on approach; this re-wakes her after a library round-trip respawns
	# her inert — which _update_checkpoint cannot, since `reached` can't exceed the
	# max checkpoint once you're there (R4-44).
	if Game.checkpoint >= BOSS_ID:
		_activate_area(_area_by_id(BOSS_ID))
	# Continue only: drop the party onto the saved checkpoint spot. A door/edge
	# entry keeps main.gd's entry-cell spawn instead.
	if Game.resume_requested and Game.checkpoint > 0:
		var target := _area_by_id(Game.checkpoint)
		for player in get_tree().get_nodes_in_group("players"):
			player.global_position = target.center


## Progress-based checkpoint: advance to the furthest area whose road spot a live
## player has walked past (by world-x). Monotonic — never moves backward — so a
## respawn (which teleports players west to the checkpoint) can't lower it.
func _update_checkpoint() -> void:
	var max_x := -INF
	for player in get_tree().get_nodes_in_group("players"):
		if player.is_targetable():
			max_x = maxf(max_x, player.global_position.x)
	if max_x == -INF:
		return
	var reached := Game.checkpoint
	for area in _areas:
		if area.center.x <= max_x and area.id > reached:
			reached = area.id
	if reached > Game.checkpoint:
		Game.checkpoint = reached
		Game.save()
		_activate_beacon(reached)
		_hud.show_checkpoint_saved()
		if reached >= BOSS_ID:
			_activate_area(_area_by_id(BOSS_ID))


func _activate_beacon(id: int) -> void:
	var beacon: CheckpointBeacon = _beacons.get(id)
	if beacon != null:
		beacon.set_active(true, true)


func _on_downed() -> void:
	# Solo, or co-op with everyone down: respawn all at the checkpoint + rearm the
	# area. Co-op with a survivor: the downed player waits for a clear-revive.
	if not _all_players_down():
		return
	var area := _area_by_id(Game.checkpoint)
	for player in get_tree().get_nodes_in_group("players"):
		player.respawn_at(area.center)
	_rearm_area(area)


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


func _on_boss_defeated() -> void:
	# The win beat lives on the Game autoload, not this freeable node: a
	# return-to-title or co-op door race during the delay must not drop the
	# coroutine and strand the ending (B-02). Doors stay disabled while it's
	# pending so a wandering player can't swallow the quest-complete screen.
	Game.begin_win_sequence()


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


## Retry handling. Normal areas: killed enemies stay dead — only survivors reset
## to their post and idle again (return_home), so a partial clear isn't undone.
## The boss area is the exception: a boss retry re-spawns her to full HP and
## re-activates (she's a single fight, not a clearable cluster).
func _rearm_area(area: Dictionary) -> void:
	if area.cleared:
		return
	if area.id == BOSS_ID:
		for enemy in area.instances:
			if is_instance_valid(enemy):
				enemy.queue_free()
		# A phase-2 wipe leaves her summons flying around — clear them too, so a
		# boss retry restarts the whole fight, not the fight plus leftovers.
		for summon in get_tree().get_nodes_in_group("boss_summons"):
			if is_instance_valid(summon):
				summon.queue_free()
		area.instances = []
		area.spawned = false
		_spawn_area(area)
		_activate_area(area)
		return
	var alive: Array = []
	for enemy in area.instances:
		if is_instance_valid(enemy):
			if enemy.has_method("return_home"):
				enemy.return_home()
			alive.append(enemy)
	area.instances = alive


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
	Game.mark_area_cleared(area.id)


func _area_by_id(id: int) -> Dictionary:
	for area in _areas:
		if area.id == id:
			return area
	return _areas[0]
