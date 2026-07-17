class_name BossIrene
extends Enemy

## Phase 1 boss. Stays inactive until the player reaches the library area, then
## drifts slowly toward the nearest player while throwing books on a timer — the
## player rolls through the books and closes in to melee. A screen-top HP bar
## tracks her; hardcoded lines (from the story session) fire at fight start, at
## half HP, and on defeat. Extends Enemy for HP/take_damage; overrides movement
## so she casts instead of chasing, and overrides death for the defeat beat.
##
## Phase 2 (low-HP minion summons) is intentionally NOT here yet — ships only
## after Phase 1 is verified solid.

signal defeated

const BOOK_SCENE := preload("res://scenes/book_projectile.tscn")
const BAT_SCENE := preload("res://scenes/enemy_bat.tscn")
const LINE_DURATION := 3.5
const FADE_TIME := 1.2

@export var throw_interval: float = 1.7
@export var keep_distance: float = 44.0
## PHASE 2 (below half HP): she summons this many bats, once, and her book
## throws tighten by this factor. Both live-tunable.
@export var summon_count: int = 2
@export var phase2_interval_scale: float = 0.75
@export var start_line := "Oh — you're here about the DVD. I really am sorry it came to this."
@export var early_line := "You could have just returned it on time, you know."
@export var mid_line := "This is for your own good, I promise."
@export var late_line := "Fine, keep the disc — but the late fees are NON-NEGOTIABLE."
@export var defeat_line := "I suppose I'll waive the late fee."

var _active := false
var _throw_cd := 0.0
var _said_early := false
var _said_mid := false
var _said_late := false
var _line_time := 0.0

@onready var _hud: CanvasLayer = $HUD
@onready var _bar: TextureProgressBar = $HUD/Bar
@onready var _line: Label = $Dialogue/Line


func _ready() -> void:
	super()
	_bar.max_value = max_hp
	_bar.value = _hp
	_hud.visible = false
	_line.visible = false


func activate() -> void:
	if _active or _dead:
		return
	_active = true
	_hud.visible = true
	_throw_cd = throw_interval
	_show_line(start_line)


func _physics_process(delta: float) -> void:
	_tick_line(delta)
	if not _active or _dead:
		velocity = Vector2.ZERO
		move_and_slide()
		return

	_throw_cd -= delta
	if _throw_cd <= 0.0:
		_throw_book()
		_throw_cd = throw_interval
	# Staged taunts at 3/4, 1/2, 1/4 HP — one-shot each, highest unspoken threshold
	# first (elif so a big single hit can't flash two lines the same frame).
	if not _said_early and _hp <= int(max_hp * 3.0 / 4.0):
		_said_early = true
		_show_line(early_line)
	elif not _said_mid and _hp <= int(max_hp / 2.0):
		_said_mid = true
		_show_line(mid_line)
		_enter_phase2()
	elif not _said_late and _hp <= int(max_hp / 4.0):
		_said_late = true
		_show_line(late_line)

	var target := _nearest_player()
	if target != null:
		var to_target := target.global_position - global_position
		if to_target.length() > keep_distance:
			velocity = to_target.normalized() * move_speed
		else:
			velocity = Vector2.ZERO
	move_and_slide()
	_update_bar()
	_animate_idle(delta)


func _throw_book() -> void:
	var target := _nearest_player()
	if target == null:
		return
	var book := BOOK_SCENE.instantiate()
	get_parent().add_child(book)
	book.global_position = global_position + Vector2(0, -8)
	book.launch(target.global_position - book.global_position)


## PHASE 2 — the long-deferred capstone, kept minimal: a one-shot bat summon at
## her flanks plus a tighter throw rhythm. Summons join "boss_summons" so a
## wipe-retry can sweep them (EncounterManager._rearm_area).
func _enter_phase2() -> void:
	throw_interval *= phase2_interval_scale
	for i in summon_count:
		var bat := BAT_SCENE.instantiate()
		bat.add_to_group("boss_summons")
		var side := -1.0 if i % 2 == 0 else 1.0
		get_parent().add_child(bat)
		bat.global_position = global_position + Vector2(side * 26.0, -10.0)


func _update_bar() -> void:
	_bar.value = maxi(_hp, 0)


func _animate_idle(delta: float) -> void:
	_anim_time += delta
	_sprite.frame = int(_anim_time * anim_fps) % anim_frames


func _show_line(text: String) -> void:
	_line.text = text
	_line.visible = true
	_line_time = LINE_DURATION


func _tick_line(delta: float) -> void:
	if _line_time > 0.0:
		_line_time -= delta
		if _line_time <= 0.0:
			_line.visible = false


func _die() -> void:
	super()
	_active = false
	_hud.visible = false
	Game.boss_defeated = true
	Game.save()
	_show_line(defeat_line)
	defeated.emit()
	var tween := create_tween()
	tween.tween_property(_sprite, "modulate:a", 0.0, FADE_TIME)
	tween.tween_interval(LINE_DURATION - FADE_TIME)
	tween.tween_callback(queue_free)
