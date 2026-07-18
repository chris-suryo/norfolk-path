extends Node2D

## Intro-cutscene director (SCAFFOLD). Plays a scripted, skippable 5-shot sequence
## through the LIVE valley on a fresh New Game, then hands control to the player.
##
## Staged entirely inside main.tscn — no scene change. Shots 1-3 play at the
## library's outdoor footprint (camera parked + zoomed), shot 2's hard cut-to-black
## covers the human-Ariana -> goose swap, shot 4 is one long camera pan west to the
## spawn. Players are frozen via process_mode (NOT get_tree().paused), so ambient
## life keeps moving during the pan. The camera is DRIVEN, not edited: detach the
## follow with set_physics_process(false), tween global_position, re-attach.
##
## Every camera move / zoom / pan / caption timing here is engine-only — none of it
## can be verified headlessly. The constants below are meant to be tuned in-editor.

## PLACEHOLDER intro captions — Chris's locked round-5 copy replaces this whole
## array (story brief: exposition -> confrontation -> transformation -> bridge).
## Beats auto-play at CAPTION_SECONDS each; the panel fits ~3 short lines, so keep
## each beat short. "" speaker = a narrator caption.
const SHOT1 := [
	["", "Ariana rented a film from the library. She never brought it back."],
	["IRENE", "You still have my copy. The late fee has escalated."],
	["ARIANA", "I'm not going to return it."],
	["IRENE", "Then it's the usual arrangement, I'm afraid."],
	["", "(Irene is the librarian. This is, apparently, what she does.)"],
]
## PLACEHOLDER landing/bridge caption — replaced with Chris's locked line.
const LANDING := "Find Ariana. The library's east. Bring her home."

const IRENE_TEX := preload("res://assets/game/Irene.png")
const GOOSE_TEX := preload(
	"res://assets/cute_fantasy/packs/Cute_Fantasy/Cute_Fantasy/Animals/Goose/Goose_01.png"
)

## Shot timings (seconds) and zooms — tune in-engine. The pan is deliberately slow
## and pulled-back (Chris's playtest: the old 6s/zoom-2.6 sweep was too fast and
## too tight — hard on the eyes). Lower zoom = wider view; higher PAN_SECONDS = slower.
const CAPTION_SECONDS := 2.6
const GOOSE_SECONDS := 2.2
const PAN_SECONDS := 11.0
const LIBRARY_ZOOM := 3.2
const PULLBACK_ZOOM := 1.8
const FOLLOW_ZOOM := 2.5

## Shot 2 is a burst of magic light (not a plain cut-to-black) so the
## transformation reads as a spell: snap to light, swap under the peak, bloom away
## to reveal the goose. Asset-free (a warm-white flash + a textureless sparkle) so
## the headless asset gate stays green. Tune in-engine.
const FLASH_RISE := 0.18
const FLASH_HOLD := 0.22
const FLASH_FALL := 0.7

## Resolution (reverse) cutscene — played after the boss falls, before the win
## card: the goose changes back into human Ariana where the fight ended, with a
## closing line branched on the library-door choice. A short held beat frames the
## transform on each side.
const RESOLUTION_BEAT := 1.4
## PLACEHOLDER resolution captions — Chris's locked round-5 payoff replaces both
## branches (story brief section C). "dvd" = returned the DVD; else (friend / the
## door skipped) = came for her.
const RESOLUTION_DVD := [
	["ARIANA", "You actually brought it back. Hm."],
	["", "(She's a person again. Somehow that's the smaller shock.)"],
]
const RESOLUTION_FRIEND := [
	["ARIANA", "You came all this way. For me."],
	["", "(She's a person again. You did that.)"],
]

@export var camera_path: NodePath
@export var world_path: NodePath

var _running := false
var _res_running := false
var _released := false
var _active_tween: Tween
var _landing: Node2D
var _irene: Node2D
var _ariana: Node2D
var _goose: Node2D
var _human: Node2D

@onready var _camera: Camera2D = get_node_or_null(camera_path)
@onready var _world: Node2D = get_node_or_null(world_path)
@onready var _cap_layer: CanvasLayer = $Captions
@onready var _cap_name: Label = $Captions/Panel/Name
@onready var _cap_text: Label = $Captions/Panel/Text
@onready var _flash: ColorRect = $Flash/Rect


func _ready() -> void:
	_cap_layer.visible = false
	_flash.modulate.a = 0.0
	if _camera == null or _world == null:
		push_error("CutsceneDirector: camera_path/world_path did not resolve.")


## Called (gated) from main.gd at the end of _ready. library_world = the outdoor
## cell to stage shots 1-3 at; landing = the node the pan ends on (the Midpoint).
## Each shot is its own coroutine returning whether the cutscene is still running
## (false = a skip fired), so the chain stops cleanly without a pile of returns.
func play(library_world: Vector2, landing: Node2D) -> void:
	if _running or _camera == null or _world == null:
		return
	_running = true
	_landing = landing
	Game.cutscene_active = true
	_freeze_players()
	_camera.set_physics_process(false)
	_camera.global_position = library_world
	_camera.zoom = Vector2(LIBRARY_ZOOM, LIBRARY_ZOOM)
	_stage_shot1(library_world)
	var ok := await _play_captions()
	if ok:
		ok = await _play_cut(library_world)
	if ok:
		ok = await _play_pullback_and_pan()
	if ok:
		await _play_landing()


## Shot 1 — alternating captions, timed (not click-advanced).
func _play_captions() -> bool:
	for pair in SHOT1:
		_show_caption(pair[0], pair[1])
		if not await _wait(CAPTION_SECONDS):
			return false
	_hide_caption()
	return true


## Shot 2 — a burst of magic light covers the human-Ariana -> goose swap: snap to
## light, swap + spray a sparkle at the peak, then bloom away to reveal the goose.
func _play_cut(library_world: Vector2) -> bool:
	_tween_prop(_flash, "modulate:a", 1.0, FLASH_RISE)
	if not await _wait(FLASH_RISE):
		return false
	_swap_to_goose(library_world)
	_spawn_sparkle(library_world)
	if not await _wait(FLASH_HOLD):
		return false
	_tween_prop(_flash, "modulate:a", 0.0, FLASH_FALL)
	return await _wait(FLASH_FALL)


## A one-shot magic sparkle at the transform point — textureless CPUParticles2D
## (small bright motes, no art asset) that frees itself once the burst is done.
## A placeholder VFX; the exact look is Chris's to dial in-engine.
func _spawn_sparkle(at: Vector2) -> void:
	var burst := CPUParticles2D.new()
	burst.position = at + Vector2(0, -6)
	burst.one_shot = true
	burst.explosiveness = 0.9
	burst.amount = 28
	burst.lifetime = 0.9
	burst.direction = Vector2.UP
	burst.spread = 180.0
	burst.gravity = Vector2.ZERO
	burst.initial_velocity_min = 24.0
	burst.initial_velocity_max = 70.0
	burst.scale_amount_min = 1.0
	burst.scale_amount_max = 2.5
	burst.color = Color(1.0, 0.95, 0.6)
	burst.emitting = true
	_world.add_child(burst)
	get_tree().create_timer(burst.lifetime + 0.4).timeout.connect(burst.queue_free)


## Shot 3 — goose runs while the camera pulls back; shot 4 — the long pan west.
func _play_pullback_and_pan() -> bool:
	_tween_prop(_camera, "zoom", Vector2(PULLBACK_ZOOM, PULLBACK_ZOOM), GOOSE_SECONDS)
	if not await _wait(GOOSE_SECONDS):
		return false
	_tween_prop(_camera, "global_position", _landing.global_position, PAN_SECONDS)
	return await _wait(PAN_SECONDS)


## Shot 5 — land, caption, hand control back.
func _play_landing() -> void:
	_show_caption("", LANDING)
	if await _wait(CAPTION_SECONDS):
		_hide_caption()
		_release()


## The reverse cutscene: the goose changes back into human Ariana where the fight
## ended, then a closing branched line, then control returns to Game to load the
## win card. Awaited by Game.begin_win_sequence — it MUST always finish (never
## hang), or the win screen never loads. Teardown is minimal: the win-screen swap
## frees this whole scene, so we don't restore player control here. Skippable via
## ui_accept (fast-forwards to the end).
func play_resolution() -> void:
	if _running or _res_running or _camera == null or _world == null:
		return
	_res_running = true
	Game.cutscene_active = true
	_freeze_players()
	# Stage beside the camera centre (where the party beat her), not on top of the
	# frozen player sprite.
	var at := _camera.global_position + Vector2(22, 0)
	_goose = _make_goose(at, false)
	_world.add_child(_goose)
	var ok := await _res_wait(RESOLUTION_BEAT)
	if ok:
		_tween_prop(_flash, "modulate:a", 1.0, FLASH_RISE)
		ok = await _res_wait(FLASH_RISE)
	if ok:
		_swap_goose_to_human(at)
		_spawn_sparkle(at)
		ok = await _res_wait(FLASH_HOLD)
	if ok:
		_tween_prop(_flash, "modulate:a", 0.0, FLASH_FALL)
		ok = await _res_wait(FLASH_FALL)
	if ok:
		ok = await _res_wait(RESOLUTION_BEAT)
	if ok:
		for pair in _resolution_lines():
			_show_caption(pair[0], pair[1])
			if not await _res_wait(CAPTION_SECONDS):
				break
	_hide_caption()
	_flash.modulate.a = 0.0
	_res_running = false


## Like _wait, but for the resolution's own run flag so a skip drops its chain.
func _res_wait(seconds: float) -> bool:
	await get_tree().create_timer(seconds).timeout
	return _res_running


func _resolution_lines() -> Array:
	return RESOLUTION_DVD if Game.irene_choice == "dvd" else RESOLUTION_FRIEND


func _swap_goose_to_human(at: Vector2) -> void:
	if is_instance_valid(_goose):
		_goose.queue_free()
		_goose = null
	_human = ArianaHumanNpc.new()
	_human.position = at
	_world.add_child(_human)


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed("ui_accept"):
		return
	if _running:
		get_viewport().set_input_as_handled()
		_release()
	elif _res_running:
		# Fast-forward the resolution; its coroutine finishes and Game loads the win card.
		get_viewport().set_input_as_handled()
		_res_running = false


## All pacing goes through a SceneTreeTimer (which always fires, even after a skip
## kills the visual tween) and returns whether the cutscene is still running — so
## `if not await _wait(...): return` drops the coroutine cleanly on a skip.
func _wait(seconds: float) -> bool:
	await get_tree().create_timer(seconds).timeout
	return _running


## Fire-and-forget visual tween (killed on skip); pacing is the paired _wait.
func _tween_prop(obj: Object, prop: String, to: Variant, dur: float) -> void:
	if _active_tween != null and _active_tween.is_valid():
		_active_tween.kill()
	_active_tween = create_tween()
	_active_tween.tween_property(obj, prop, to, dur)


func _show_caption(speaker: String, text: String) -> void:
	_cap_name.text = speaker
	_cap_text.text = text
	_cap_layer.visible = true


func _hide_caption() -> void:
	_cap_layer.visible = false


func _stage_shot1(library_world: Vector2) -> void:
	_irene = Critter.new()
	_irene.texture = IRENE_TEX
	_irene.hframes = 6
	_irene.vframes = 7
	_irene.fps = 4.0
	_irene.frame_count = 4
	_irene.first_frame = 0
	_irene.position = library_world + Vector2(-14, 0)
	_world.add_child(_irene)
	_ariana = ArianaHumanNpc.new()
	_ariana.position = library_world + Vector2(14, 0)
	_world.add_child(_ariana)


func _swap_to_goose(library_world: Vector2) -> void:
	if is_instance_valid(_ariana):
		_ariana.queue_free()
		_ariana = null
	_goose = _make_goose(library_world, true)
	_world.add_child(_goose)


## A goose from the shared sheet at `at`. Wander is on for the intro (she bolts
## off after the change) and off for the resolution (she's about to change back).
func _make_goose(at: Vector2, wander: bool) -> AmbientAnimal:
	var goose := AmbientAnimal.new()
	goose.texture = GOOSE_TEX
	goose.hframes = 12
	goose.vframes = 16
	goose.idle_row = 0
	goose.idle_count = 2
	goose.walk_row = 1
	goose.walk_count = 6
	goose.position = at
	if wander:
		goose.can_wander = true
		goose.wander_radius = 40.0
		goose.move_speed = 52.0
	return goose


func _freeze_players() -> void:
	for p in get_tree().get_nodes_in_group("players"):
		p.process_mode = Node.PROCESS_MODE_DISABLED


func _restore_players() -> void:
	for p in get_tree().get_nodes_in_group("players"):
		p.process_mode = Node.PROCESS_MODE_INHERIT


## Idempotent teardown — runs on natural end and on skip: stop the coroutine, free
## the staged actors, reset zoom + re-attach the follow camera, unfreeze players,
## and cue the spawn hint. The director node itself stays resident but inert.
func _release() -> void:
	if _released:
		return
	_released = true
	_running = false
	if _active_tween != null and _active_tween.is_valid():
		_active_tween.kill()
	_hide_caption()
	_flash.modulate.a = 0.0
	for actor in [_irene, _ariana, _goose, _human]:
		if is_instance_valid(actor):
			actor.queue_free()
	if _camera != null:
		# Restore the player's chosen zoom, not a hardcoded default: set_zoom_preset
		# persists to Game.camera_zoom, so passing FOLLOW_ZOOM here would overwrite
		# a player's preset every time a cutscene ends. Game.camera_zoom defaults to
		# FOLLOW_ZOOM's 2.5 on a fresh launch, so the intro pan is unaffected.
		if _camera.has_method("set_zoom_preset"):
			_camera.set_zoom_preset(Game.camera_zoom)
		else:
			_camera.zoom = Vector2(Game.camera_zoom, Game.camera_zoom)
		if _landing != null:
			_camera.global_position = _landing.global_position
		_camera.set_physics_process(true)
	_restore_players()
	Game.cutscene_active = false
	var hud := get_node_or_null("../HUD")
	if hud != null and hud.has_method("show_move_hint"):
		hud.show_move_hint()
