extends Node

## Global run state + persistence (autoload "Game").
##
## Tiny save: the current checkpoint, player count, and whether the boss is down.
## On web the payload goes to localStorage via JavaScriptBridge (synchronous,
## survives a refresh with threads off); on desktop it is a user:// JSON file.
## Only ints/bools are stored, so wrapping the JSON in a single-quoted JS string
## for localStorage is safe (no inner single quotes to escape).

const SAVE_KEY := "norfolk_path"
const SAVE_PATH := "user://save.json"
# Bumped to 2 to invalidate pre-respawn-fix saves (their checkpoint ids point at
# renumbered areas): has_save() now returns false for a v1 save, so the title
# starts a clean New Game in the village instead of resuming a stale checkpoint.
const SAVE_VERSION := 2

var player_count := 1
var checkpoint := 0
var boss_defeated := false

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


func reset_run() -> void:
	checkpoint = 0
	boss_defeated = false


func save() -> void:
	var data := {
		"v": SAVE_VERSION,
		"checkpoint": checkpoint,
		"player_count": player_count,
		"boss_defeated": boss_defeated,
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
	return parsed is Dictionary and parsed.get("v") == SAVE_VERSION


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
	var ok: bool = parsed is Dictionary and parsed.get("v") == SAVE_VERSION
	if ok:
		checkpoint = int(parsed.get("checkpoint", 0))
		player_count = clampi(int(parsed.get("player_count", 1)), 1, 2)
		boss_defeated = bool(parsed.get("boss_defeated", false))
	return ok
