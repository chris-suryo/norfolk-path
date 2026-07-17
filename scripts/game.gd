extends Node

## Global run state + persistence (autoload "Game").
##
## Tiny save: the current checkpoint, player count, whether the boss is down,
## the current level id (v4), and both appearance profiles. On web the payload
## goes to localStorage
## via JavaScriptBridge (synchronous, survives a refresh with threads off); on
## desktop it is a user:// JSON file. Stored strings all come from the curated
## AppearanceCatalog IDs — none contain a single quote or backslash, so wrapping
## the JSON in a single-quoted JS string for localStorage stays safe.

const SAVE_KEY := "norfolk_path"
const SAVE_PATH := "user://save.json"
# v4 adds the current level id (the connected-world position). v3 saves remain
# valid and default to the valley on load — same forward-compatible migration as
# v2 -> v3, and appearances are kept (only the level field is new).
const SAVE_VERSION := 4
const PREVIOUS_SAVE_VERSION := 3
## How long each half of the scene-change fade takes (out, then back in).
const FADE_HALF := 0.22
## The quest-complete screen, and the beat that precedes it (lets the boss's
## defeat line + fade play before the swap). Both live here — not on the
## EncounterManager — so the win coroutine runs on a node the scene swap can't free.
const WIN_SCENE := "res://scenes/win_screen.tscn"
const WIN_DELAY := 3.0

var player_count := 1
var checkpoint := 0
## Persisted only in begin_win_sequence, after the win screen is guaranteed to
## load — never in BossIrene._die, or a mid-win-delay refresh strands the run
## (B-03/B-04).
var boss_defeated := false
## The level the players are on (LevelRegistry id). Saved, so Continue returns to
## it; New Game / reset starts in the valley.
var current_level_id := "valley"
var appearances: Array[Dictionary] = [
	AppearanceCatalog.default_profile(1),
	AppearanceCatalog.default_profile(2),
]

## Set by player-select: true when the player chose "Continue" (resume the saved
## checkpoint), false for "New Game" (fresh village start). The EncounterManager
## only resumes a saved position when this is true, so a stale save never drops a
## new game next to a late-game checkpoint.
var resume_requested := false

## Runtime-only: the named entry the players arrived through (set by
## LevelTransition before a scene reload). main.gd picks the spawn cell from it;
## not persisted — a Continue uses the level's own spawn/checkpoint.
var current_entry := ""

## Runtime-only "HH:MM" of the last save this session (autosave or manual). NOT
## persisted — it is display-state for the pause menu's "Save Now" confirmation,
## and keeping it out of the saved dict preserves the ints/bools-only JSON note
## above. Empty until the first save.
var last_saved := ""

## Runtime-only: true while a dialogue box is open. The pause menu ignores Esc
## during dialogue so the two overlays can't fight over the paused tree.
var dialogue_active := false

## Runtime-only: the answer the player gave Irene at the library door ("dvd" or
## "friend"), which picks the win-screen closing line. Empty if the door was
## never engaged. Not saved (like dialogue_active); cleared on reset_run.
var irene_choice := ""

## Runtime-only: true between the boss falling and the win screen loading.
## Level transitions no-op while pending — walking into a door during the win
## delay must not swallow the quest-complete screen. The win beat itself lives on
## this autoload (begin_win_sequence) so a freed EncounterManager can't strand it.
var win_pending := false

## Runtime-only: the encounter-area ids the party has already cleared this run.
## NOT persisted (keeps the ints/bools-only save note above): it exists to survive
## change_scene, which frees the EncounterManager and its per-area `cleared` flags.
## Without it a door round-trip respawns every beaten area (R4-43). A cold Continue
## (fresh launch) rebuilds clears from the saved checkpoint instead — see
## EncounterManager._apply_resume.
var cleared_areas: Array[int] = []

var _fading := false
var _fade_rect: ColorRect


## The autoload survives scene changes, so it hosts the fade overlay: a
## full-screen black rect on a top CanvasLayer, alpha-tweened around every
## change_scene() call (the abrupt-cut fix for doors and map edges).
func _ready() -> void:
	# Saved key remaps apply before any scene reads input (defaults otherwise).
	Controls.apply_saved()
	# Fades must run even when the tree is paused (pause menu, dialogue).
	process_mode = Node.PROCESS_MODE_ALWAYS
	var layer := CanvasLayer.new()
	layer.layer = 100
	_fade_rect = ColorRect.new()
	_fade_rect.color = Color.BLACK
	_fade_rect.modulate.a = 0.0
	_fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_fade_rect)
	add_child(layer)


## True while a change_scene fade is in flight. LevelTransition polls this so a
## crossing requested mid-fade is retried next frame instead of being swallowed
## (the round-3 "walked out of the house into the void" bug: the exit mat is one
## tile from the arrival spawn, reachable before the arrival fade finishes).
func is_fading() -> bool:
	return _fading


## Every scene change goes through here: fade to black, swap, fade back in.
## Re-entrant calls during the fade are dropped (a second door touched
## mid-crossing must not queue a second swap).
func change_scene(path: String) -> void:
	if _fading:
		return
	# Every freeze in the win/pause cluster is "pause state outlived the scene that
	# could clear it": the only paused=false sites live in main.tscn, which the swap
	# frees. Clearing it here — on EVERY change — means no scene ever loads frozen
	# (Esc/dialogue during the win delay or any fade). Cheapest fix in the cluster.
	get_tree().paused = false
	_fading = true
	var out_tween := create_tween()
	out_tween.tween_property(_fade_rect, "modulate:a", 1.0, FADE_HALF)
	await out_tween.finished
	var err := get_tree().change_scene_to_file(path)
	if err != OK:
		push_error("Game.change_scene: could not load %s (error %d)" % [path, err])
	var in_tween := create_tween()
	in_tween.tween_property(_fade_rect, "modulate:a", 0.0, FADE_HALF)
	await in_tween.finished
	_fading = false


## The boss is down: hold doors (win_pending) through a short beat so a wandering
## player can't swallow the quest-complete screen, then load it. Runs on this
## always-alive autoload so returning to title or racing a door during the delay
## can't drop the coroutine — the win screen still loads and win_pending never
## sticks true for the session (B-02). Cleared before the swap since the win
## screen has no doors to guard. The boss_defeated record is also persisted here,
## at the END of the delay, so the ending never hits disk before it is guaranteed
## to display (B-03/B-04) — see below.
func begin_win_sequence() -> void:
	if win_pending:
		return
	win_pending = true
	await get_tree().create_timer(WIN_DELAY).timeout
	win_pending = false
	# Persist the ending only now that the win screen is guaranteed to load (moved out
	# of BossIrene._die — B-03/B-04). Setting boss_defeated in memory AND on disk at the
	# same instant keeps "in-memory true iff on-disk true", so no save() reachable during
	# the win delay can ever record a premature boss clear.
	boss_defeated = true
	save()
	change_scene(WIN_SCENE)


## Records that an encounter area was cleared this run. Idempotent. Runtime-only;
## see cleared_areas above.
func mark_area_cleared(id: int) -> void:
	if id not in cleared_areas:
		cleared_areas.append(id)


func set_player_count(count: int) -> void:
	player_count = clampi(count, 1, 2)


## Clears RUN progress only. Appearances are identity, not run state: they
## survive a post-win reset so Continue never silently swaps a customized
## character for the seed default (playtest round-1 finding). New Game still
## re-creates from scratch — player_select seeds its own creator defaults.
func reset_run() -> void:
	checkpoint = 0
	boss_defeated = false
	current_level_id = "valley"
	current_entry = ""
	win_pending = false
	irene_choice = ""
	cleared_areas.clear()


func appearance_for_player(player_index: int) -> Dictionary:
	var index := clampi(player_index - 1, 0, 1)
	while appearances.size() < 2:
		appearances.append(AppearanceCatalog.default_profile(appearances.size() + 1))
	appearances[index] = AppearanceCatalog.normalized(appearances[index])
	return appearances[index].duplicate()


func set_appearances(next_appearances: Array[Dictionary]) -> void:
	appearances = []
	for index in 2:
		var fallback := AppearanceCatalog.default_profile(index + 1)
		var value := next_appearances[index] if index < next_appearances.size() else fallback
		appearances.append(AppearanceCatalog.normalized(value))


func save() -> void:
	var data := {
		"v": SAVE_VERSION,
		"checkpoint": checkpoint,
		"player_count": player_count,
		"boss_defeated": boss_defeated,
		"level": current_level_id,
		"appearances": appearances,
	}
	var text := JSON.stringify(data)
	last_saved = Time.get_time_string_from_system().substr(0, 5)
	if OS.has_feature("web"):
		JavaScriptBridge.eval("localStorage.setItem('%s', '%s');" % [SAVE_KEY, text], true)
	else:
		var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
		if file != null:
			file.store_string(text)
			file.close()


func load_state() -> bool:
	return _apply(_read_raw())


## True when a valid save exists, so player-select can offer "Continue". Reads
## without applying (no side effects on the current run state).
func has_save() -> bool:
	var text := _read_raw()
	var parsed: Variant = JSON.parse_string(text) if text != "" else null
	if not parsed is Dictionary:
		return false
	var version := int(parsed.get("v", 0))
	return version == SAVE_VERSION or version == PREVIOUS_SAVE_VERSION


func _read_raw() -> String:
	var text := ""
	if OS.has_feature("web"):
		var raw: Variant = JavaScriptBridge.eval("localStorage.getItem('%s');" % SAVE_KEY, true)
		if raw is String:
			text = raw
	elif FileAccess.file_exists(SAVE_PATH):
		var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
		if file != null:
			text = file.get_as_text()
			file.close()
	return text


func _apply(text: String) -> bool:
	var parsed: Variant = JSON.parse_string(text) if text != "" else null
	var version := int(parsed.get("v", 0)) if parsed is Dictionary else 0
	var ok := parsed is Dictionary and (version == SAVE_VERSION or version == PREVIOUS_SAVE_VERSION)
	if ok:
		checkpoint = int(parsed.get("checkpoint", 0))
		player_count = clampi(int(parsed.get("player_count", 1)), 1, 2)
		boss_defeated = bool(parsed.get("boss_defeated", false))
		# Missing "level" (a v3 save) defaults to the valley.
		current_level_id = str(parsed.get("level", "valley"))
		var loaded: Array[Dictionary] = []
		# Appearances exist in v3 AND v4 (only "level" is new this bump), so read
		# them for either version — dropping them would reset a customized look.
		if parsed.get("appearances") is Array:
			for item in parsed.appearances:
				if item is Dictionary:
					loaded.append(item)
		set_appearances(loaded)
		if version == PREVIOUS_SAVE_VERSION:
			save()
	return ok
