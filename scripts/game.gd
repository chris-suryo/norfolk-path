extends Node

## Global run state + persistence (autoload "Game").
##
## Tiny save: the current checkpoint, player count, whether the boss is down,
## and both appearance profiles (v3). On web the payload goes to localStorage
## via JavaScriptBridge (synchronous, survives a refresh with threads off); on
## desktop it is a user:// JSON file. Stored strings all come from the curated
## AppearanceCatalog IDs — none contain a single quote or backslash, so wrapping
## the JSON in a single-quoted JS string for localStorage stays safe.

const SAVE_KEY := "norfolk_path"
const SAVE_PATH := "user://save.json"
# v3 adds two plain-JSON appearance profiles. v2 saves remain valid and gain
# defaults on load, so existing checkpoint progress is never discarded.
const SAVE_VERSION := 3
const PREVIOUS_SAVE_VERSION := 2

var player_count := 1
var checkpoint := 0
var boss_defeated := false
var appearances: Array[Dictionary] = [
	AppearanceCatalog.default_profile(1),
	AppearanceCatalog.default_profile(2),
]

## Set by player-select: true when the player chose "Continue" (resume the saved
## checkpoint), false for "New Game" (fresh village start). The EncounterManager
## only resumes a saved position when this is true, so a stale save never drops a
## new game next to a late-game checkpoint.
var resume_requested := false

## Runtime-only "HH:MM" of the last save this session (autosave or manual). NOT
## persisted — it is display-state for the pause menu's "Save Now" confirmation,
## and keeping it out of the saved dict preserves the ints/bools-only JSON note
## above. Empty until the first save.
var last_saved := ""


func set_player_count(count: int) -> void:
	player_count = clampi(count, 1, 2)


## Clears RUN progress only. Appearances are identity, not run state: they
## survive a post-win reset so Continue never silently swaps a customized
## character for the seed default (playtest round-1 finding). New Game still
## re-creates from scratch — player_select seeds its own creator defaults.
func reset_run() -> void:
	checkpoint = 0
	boss_defeated = false


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
		var loaded: Array[Dictionary] = []
		if version == SAVE_VERSION and parsed.get("appearances") is Array:
			for item in parsed.appearances:
				if item is Dictionary:
					loaded.append(item)
		set_appearances(loaded)
		if version == PREVIOUS_SAVE_VERSION:
			save()
	return ok
