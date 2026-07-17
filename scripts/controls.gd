class_name Controls
extends RefCounted

## Key remapping persistence (round-3: remapping is the menu focus).
##
## The InputMap starts from project.godot's defaults (which include the legacy
## aliases — Space sword, F bow, "/" and "," and "." for P2). A remap REPLACES
## an action's bindings with the one chosen key; the whole live map is then saved
## to user://controls.json (IndexedDB on web) as {action: [physical_keycode, ...]}
## — the full key set per action, so unremapped actions keep their aliases across
## a reboot. Game._ready applies the file at boot; reset deletes it and restores
## the project defaults. (Legacy files that stored a bare int per action still
## load.)

const PATH := "user://controls.json"

## Every rebindable action, in display order. Movement first, then combat.
const ACTIONS := [
	"p1_up",
	"p1_down",
	"p1_left",
	"p1_right",
	"p1_attack",
	"p1_fire",
	"p1_action2",
	"p1_interact",
	"p2_up",
	"p2_down",
	"p2_left",
	"p2_right",
	"p2_attack",
	"p2_fire",
	"p2_action2",
	"p2_interact",
]

## Short human names for the menu ("p1_action2" means nothing to a player).
const LABELS := {
	"up": "UP",
	"down": "DOWN",
	"left": "LEFT",
	"right": "RIGHT",
	"attack": "SWORD",
	"fire": "BOW",
	"action2": "ROLL",
	"interact": "TALK",
}


static func label_for(action: String) -> String:
	return LABELS.get(action.trim_prefix("p1_").trim_prefix("p2_"), action)


## The key currently bound to an action, for display. Shows the FIRST binding
## (the primary; legacy aliases stay silent so the menu reads clean).
static func key_text(action: String) -> String:
	for event in InputMap.action_get_events(action):
		if event is InputEventKey:
			var code: Key = (
				event.physical_keycode if event.physical_keycode != KEY_NONE else event.keycode
			)
			return OS.get_keycode_string(code)
	return "-"


## Bind an action to exactly one physical key (replacing defaults + aliases —
## a remap is an explicit choice) and persist the full override set.
static func rebind(action: String, physical_keycode: Key) -> void:
	InputMap.action_erase_events(action)
	var event := InputEventKey.new()
	event.physical_keycode = physical_keycode
	InputMap.action_add_event(action, event)
	_save()


## Restore project defaults and forget the saved overrides.
static func reset() -> void:
	if FileAccess.file_exists(PATH):
		DirAccess.remove_absolute(PATH)
	InputMap.load_from_project_settings()


## Apply saved overrides at boot. Unknown actions or bad values are skipped —
## a stale/corrupt file must never brick input.
static func apply_saved() -> void:
	if not FileAccess.file_exists(PATH):
		return
	var file := FileAccess.open(PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	file.close()
	if not parsed is Dictionary:
		return
	for action in parsed:
		if action not in ACTIONS:
			continue
		# Accept the current list-of-keys form and the legacy single-int form
		# (files written before B-07's fix) so old saves still load.
		var raw: Variant = parsed[action]
		var source: Array = raw if raw is Array else [raw]
		var valid: Array[Key] = []
		for entry in source:
			var code := int(entry)
			if code > 0:
				valid.append(code as Key)
		# Only replace the defaults when we have at least one usable key — a
		# stale/corrupt entry must never leave an action with no binding.
		if valid.is_empty():
			continue
		InputMap.action_erase_events(action)
		for code in valid:
			var event := InputEventKey.new()
			event.physical_keycode = code
			InputMap.action_add_event(action, event)


## Persist the FULL key set of every action — all bindings, not just the first.
## (B-07: saving only the first key silently dropped every legacy alias on the
## next boot, since apply_saved re-applies exactly what was written.)
static func _save() -> void:
	var data := {}
	for action in ACTIONS:
		var codes := []
		for event in InputMap.action_get_events(action):
			if event is InputEventKey:
				var code: Key = (
					event.physical_keycode if event.physical_keycode != KEY_NONE else event.keycode
				)
				codes.append(int(code))
		data[action] = codes
	var file := FileAccess.open(PATH, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(data))
		file.close()
