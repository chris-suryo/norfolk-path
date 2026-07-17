class_name AppearanceRenderer
extends Node2D

## A visual-only layered player. Gameplay stays on the owning CharacterBody2D;
## this node only keeps modular art locked to one animation frame and flip.

const SHEET_COLUMNS := 9
const SHEET_ROWS := 56

var profile: Dictionary = AppearanceCatalog.default_profile()
var _idle_time := 0.0

@onready var _body: Sprite2D = $Body
@onready var _pants: Sprite2D = $Pants
@onready var _shoes: Sprite2D = $Shoes
@onready var _shirt: Sprite2D = $Shirt
@onready var _sword: Sprite2D = $Sword
@onready var _bow: Sprite2D = $Bow
@onready var _hair: Sprite2D = $Hair
@onready var _hat: Sprite2D = $Hat


func _ready() -> void:
	apply_profile(profile)
	set_frame(0, 0, false)


func apply_profile(next_profile: Dictionary) -> void:
	profile = AppearanceCatalog.normalized(next_profile)
	_body.texture = load(AppearanceCatalog.BASE_PATH)
	_hair.texture = load(AppearanceCatalog.hair_path(profile))
	_shirt.texture = load(AppearanceCatalog.shirt_path(profile))
	_sword.texture = load(AppearanceCatalog.SWORD_PATH)
	_bow.texture = load(AppearanceCatalog.BOW_PATH)
	_pants.texture = load(AppearanceCatalog.pants_path(profile))
	_shoes.texture = load(AppearanceCatalog.shoes_path(profile))
	_hat.texture = load(AppearanceCatalog.HAT_PATH)
	_hat.visible = profile.hat
	_sword.visible = false
	_bow.visible = false


func set_frame(row: int, column: int, flip: bool) -> void:
	var frame := (
		clampi(row, 0, SHEET_ROWS - 1) * SHEET_COLUMNS + clampi(column, 0, SHEET_COLUMNS - 1)
	)
	for layer in [_body, _pants, _shoes, _shirt, _hair, _hat]:
		layer.frame = frame
		layer.flip_h = flip
	# The weapon overlays key off the attack rows (6 down / 9 side / 12 up):
	# sword sheet is 4 frames per row, bow sheet 6 (draw + release).
	var weapon_row := -1
	if row == 6:
		weapon_row = 0
	elif row == 9:
		weapon_row = 1
	elif row == 12:
		weapon_row = 2
	if weapon_row >= 0:
		_sword.frame = weapon_row * 4 + mini(column, 3)
		_sword.flip_h = flip
		_bow.frame = weapon_row * 6 + mini(column, 5)
		_bow.flip_h = flip


func set_sword_visible(value: bool) -> void:
	_sword.visible = value


func set_bow_visible(value: bool) -> void:
	_bow.visible = value


func animate_idle(delta: float) -> void:
	_idle_time += delta
	set_frame(0, int(_idle_time * 4.0) % 6, false)
