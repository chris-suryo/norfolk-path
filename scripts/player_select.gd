extends Control

## Title screen. Two stages, driven by whether a save exists:
##   MODE  (only shown when Game.has_save()): Continue / New Game.
##   COUNT (always): 1 Player / 2 Players.
## Continue resumes the saved checkpoint (Game.resume_requested = true, player
## count comes from the save). New Game wipes the run (reset_run) and asks for a
## player count, starting fresh in the village. With no save we skip straight to
## COUNT (an implicit New Game).
##
## Deliberately plain — Labels + a highlight; dressing it with the pack UI kit is
## a later polish pass. Confirm is intentionally broad: ui_accept AND the game's
## own attack keys AND a raw Enter/Space check, so a quirk in one binding can't
## make "start" dead. A failed scene load is reported loudly, not silent.

enum Stage { MODE, COUNT, CREATOR }

const MAIN_SCENE := "res://scenes/main.tscn"
const SELECTED := Color(1, 0.9, 0.3)
const DIMMED := Color(0.84, 0.74, 0.60)

const APPEARANCE_SCENE := preload("res://scenes/appearance_preview.tscn")
const BUTTERFLY_SHEET := "res://assets/cute_fantasy/packs/Cute_Fantasy/Cute_Fantasy/Animals/Butterfly/Butterfly.png"

## Title diversity (playtest ask: "more interesting and diverse"): the backdrop,
## the character by the fire, and the tagline are all rolled fresh on each launch,
## so the intro never reads the same twice. Backdrops are regions of the already-
## baked outdoor grounds — no new art, no new imports.
const TITLE_BACKDROPS := [
	{"tex": "res://assets/generated/valley-1-ground.png", "region": Rect2(1400, 260, 640, 360)},
	{"tex": "res://assets/generated/valley-1-ground.png", "region": Rect2(600, 380, 640, 360)},
	{"tex": "res://assets/generated/valley-1-ground.png", "region": Rect2(2300, 300, 640, 360)},
	{"tex": "res://assets/generated/cove-s11-ground.png", "region": Rect2(700, 380, 640, 360)},
]

## PLACEHOLDER flavor taglines (Chris curates the tone/copy). The late-fee line is
## the anchor; the rest keep the same dry register. One is picked per launch.
const TAGLINES := [
	"THE LATE FEE HAS ESCALATED.",
	"SHE RENTED A DVD. SHE NEVER RETURNED IT.",
	"THE LIBRARIAN DOES NOT FORGIVE.",
	"A GOOSE IS INVOLVED. IT USUALLY IS.",
	"OVERDUE. ESCALATING. UNRESOLVED.",
	"RETURN THE DVD. HOW HARD CAN IT BE?",
]

var _stage: int = Stage.COUNT
var _selected := 1
var _creator_slot := 1
var _pending_appearances: Array[Dictionary] = []
var _character: AppearanceRenderer = null

@onready var _title: Label = $Frame/Box/Title
@onready var _subtitle: Label = $Frame/Box/Subtitle
@onready var _option1: Label = $Frame/Box/Option1
@onready var _option2: Label = $Frame/Box/Option2
@onready var _build_version: Label = $Frame/BuildVersion
@onready var _backdrop: TextureRect = $Backdrop
@onready var _scene: Node2D = $Scene
@onready var _creator: CharacterCreator = $Creator


func _ready() -> void:
	_build_version.text = (
		"v%s - %s" % [ProjectSettings.get_setting("application/config/version", "?"), BuildInfo.SHA]
	)
	_roll_backdrop()
	_subtitle.text = TAGLINES.pick_random()
	_spawn_title_scene()
	_creator.close()
	_creator.accepted.connect(_on_creator_accepted)
	_creator.backed.connect(_on_creator_backed)
	if Game.has_save():
		_stage = Stage.MODE
	_wire_mouse()
	_show_stage()


## Mouse as a second input path (keyboard stays): hovering an option highlights
## it, clicking the highlighted option confirms it (so one click on a hovered
## option activates; on a no-hover device, first click selects, second confirms).
func _wire_mouse() -> void:
	var options := {1: _option1, 2: _option2}
	for index in options:
		var label: Label = options[index]
		label.mouse_filter = Control.MOUSE_FILTER_STOP
		label.mouse_entered.connect(_on_option_hover.bind(index))
		label.gui_input.connect(_on_option_click.bind(index))


func _on_option_hover(index: int) -> void:
	_selected = index
	_refresh()


func _on_option_click(event: InputEvent, index: int) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if _selected == index:
			_confirm()
		else:
			_selected = index
			_refresh()


func _unhandled_input(event: InputEvent) -> void:
	if _stage == Stage.CREATOR:
		_creator.handle_input(event)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_up") or event.is_action_pressed("ui_down"):
		_selected = 3 - _selected
		_refresh()
	elif _is_confirm(event):
		_confirm()


func _is_confirm(event: InputEvent) -> bool:
	if event.is_action_pressed("ui_accept") or event.is_action_pressed("p1_attack"):
		return true
	if event.is_action_pressed("p2_attack"):
		return true
	if event is InputEventKey and event.pressed and not event.echo:
		var code: int = event.physical_keycode
		return code == KEY_ENTER or code == KEY_KP_ENTER or code == KEY_SPACE
	return false


func _show_stage() -> void:
	_selected = 1
	if _stage == Stage.MODE:
		_option1.text = "CONTINUE"
		_option2.text = "NEW GAME"
	else:
		_option1.text = "1 PLAYER"
		_option2.text = "2 PLAYERS"
	_refresh()


func _confirm() -> void:
	if _stage == Stage.MODE:
		if _selected == 1:
			# Continue: load the saved state now (so main._ready sees the right
			# player_count) and let the EncounterManager resume the checkpoint.
			Game.resume_requested = true
			Game.load_state()
			_go()
		else:
			# New Game: wipe the run, then ask for a player count. Re-arm the intro
			# so it replays on EVERY New Game (reset_run deliberately leaves the
			# once-per-session latch alone; Continue never reaches here).
			Game.resume_requested = false
			Game.reset_run()
			Game.intro_played = false
			_stage = Stage.COUNT
			_show_stage()
	else:
		Game.set_player_count(_selected)
		Game.resume_requested = false
		_pending_appearances = [
			AppearanceCatalog.default_profile(1), AppearanceCatalog.default_profile(2)
		]
		_creator_slot = 1
		_stage = Stage.CREATOR
		_creator.begin(_creator_slot, _pending_appearances[_creator_slot - 1])


func _on_creator_accepted(profile: Dictionary) -> void:
	_pending_appearances[_creator_slot - 1] = AppearanceCatalog.normalized(profile)
	if _creator_slot < Game.player_count:
		_creator_slot += 1
		_creator.begin(_creator_slot, _pending_appearances[_creator_slot - 1])
		return
	Game.set_appearances(_pending_appearances)
	Game.save()
	_creator.close()
	_go()


func _on_creator_backed() -> void:
	if _creator_slot > 1:
		_creator_slot -= 1
		_creator.begin(_creator_slot, _pending_appearances[_creator_slot - 1])
		return
	_creator.close()
	_stage = Stage.COUNT
	_show_stage()


func _go() -> void:
	# Fade + error handling live in Game.change_scene.
	Game.change_scene(MAIN_SCENE)


func _refresh() -> void:
	_option1.modulate = SELECTED if _selected == 1 else DIMMED
	_option2.modulate = SELECTED if _selected == 2 else DIMMED


func _process(delta: float) -> void:
	# The butterflies self-animate (AmbientAnimal._process); the modular character
	# needs its idle cycle driven, like VillagerNpc/the creator preview do.
	if _character != null:
		_character.animate_idle(delta)


func _roll_backdrop() -> void:
	var pick: Dictionary = TITLE_BACKDROPS.pick_random()
	var at := AtlasTexture.new()
	at.atlas = load(pick["tex"])
	at.region = pick["region"]
	_backdrop.texture = at


## An idle villager standing off to the side of the menu (random look each launch)
## plus a few drifting butterflies — all reused, already-imported art, spawned into
## the "Scene" layer that draws over the dimmed backdrop and behind the menu panel.
func _spawn_title_scene() -> void:
	_character = APPEARANCE_SCENE.instantiate()
	_character.position = Vector2(92, 250)
	_character.scale = Vector2(2.0, 2.0)
	_scene.add_child(_character)
	_character.apply_profile(_random_look())
	for pos in [Vector2(70, 90), Vector2(560, 120), Vector2(590, 244)]:
		_scene.add_child(_make_butterfly(pos))


func _random_look() -> Dictionary:
	var style: String = AppearanceCatalog.SHIRT_STYLES.pick_random()
	return (
		AppearanceCatalog
		. normalized(
			{
				"hair_style": randi_range(1, 6),
				"hair_color": AppearanceCatalog.HAIR_COLORS.pick_random(),
				"shirt_style": style,
				"shirt_color": AppearanceCatalog.SHIRT_COLORS[style].pick_random(),
				"pants_color": AppearanceCatalog.PANTS_COLORS.pick_random(),
				"shoes_color": AppearanceCatalog.SHOES_COLORS.pick_random(),
				"hat": randf() < 0.4,
			}
		)
	)


## A drifting butterfly (8px frames, 2 flaps x 8 colour rows — AmbientAnimal picks
## a random colour + flight path itself). Same config main.gd uses for the "y" cell.
func _make_butterfly(pos: Vector2) -> AmbientAnimal:
	var tex: Texture2D = load(BUTTERFLY_SHEET)
	var b := AmbientAnimal.new()
	b.texture = tex
	b.hframes = int(tex.get_width() / 8)
	b.vframes = int(tex.get_height() / 8)
	b.idle_row = 0
	b.idle_count = 2
	b.idle_fps = 6.0
	b.can_fly = true
	b.flight_radius = 10.0
	b.flight_period = 2.8
	b.scale = Vector2(1.5, 1.5)
	b.position = pos
	return b
