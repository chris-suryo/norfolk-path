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
const SAVE_VERSION := 1

var player_count := 1
var checkpoint := 0
var boss_defeated := false


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
	if OS.has_feature("web"):
		JavaScriptBridge.eval("localStorage.setItem('%s', '%s');" % [SAVE_KEY, text], true)
	else:
		var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
		if file != null:
			file.store_string(text)
			file.close()


func load_state() -> bool:
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
	return _apply(text)


func _apply(text: String) -> bool:
	var parsed: Variant = JSON.parse_string(text) if text != "" else null
	var ok: bool = parsed is Dictionary and parsed.get("v") == SAVE_VERSION
	if ok:
		checkpoint = int(parsed.get("checkpoint", 0))
		player_count = clampi(int(parsed.get("player_count", 1)), 1, 2)
		boss_defeated = bool(parsed.get("boss_defeated", false))
	return ok
