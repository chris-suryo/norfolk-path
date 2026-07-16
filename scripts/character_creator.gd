class_name CharacterCreator
extends Control

signal accepted(profile: Dictionary)
signal backed

const ROWS := [
	"Hair",
	"Hair color",
	"Top",
	"Top color",
	"Pants",
	"Shoes",
	"Hat",
	"Randomize",
	"Confirm",
	"Back",
]

var _slot := 1
var _profile: Dictionary = AppearanceCatalog.default_profile()
var _row := 0

@onready var _slot_label: Label = $Frame/Slot
@onready var _preview: AppearanceRenderer = $Frame/Preview
@onready var _rows: Array[Label] = [
	$Frame/Options/Hair,
	$Frame/Options/HairColor,
	$Frame/Options/Top,
	$Frame/Options/TopColor,
	$Frame/Options/Pants,
	$Frame/Options/Shoes,
	$Frame/Options/Hat,
	$Frame/Options/Randomize,
	$Frame/Options/Confirm,
	$Frame/Options/Back,
]


func begin(slot: int, initial_profile: Dictionary) -> void:
	_slot = slot
	_profile = AppearanceCatalog.normalized(initial_profile)
	_row = 0
	visible = true
	_slot_label.text = "CREATE PLAYER %d" % _slot
	_preview.apply_profile(_profile)
	_refresh()


func close() -> void:
	visible = false


func handle_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_up"):
		_row = posmod(_row - 1, ROWS.size())
		_refresh()
	elif event.is_action_pressed("ui_down"):
		_row = posmod(_row + 1, ROWS.size())
		_refresh()
	elif event.is_action_pressed("ui_left"):
		_adjust(-1)
	elif event.is_action_pressed("ui_right"):
		_adjust(1)
	elif event.is_action_pressed("ui_cancel"):
		backed.emit()
	elif _is_confirm(event):
		_activate()


func _process(delta: float) -> void:
	if visible:
		_preview.animate_idle(delta)


func _is_confirm(event: InputEvent) -> bool:
	if event.is_action_pressed("ui_accept") or event.is_action_pressed("p1_attack"):
		return true
	if event.is_action_pressed("p2_attack"):
		return true
	return (
		event is InputEventKey
		and event.pressed
		and not event.echo
		and event.physical_keycode == KEY_SPACE
	)


func _adjust(direction: int) -> void:
	match _row:
		0:
			_profile.hair_style = posmod(int(_profile.hair_style) - 1 + direction, 6) + 1
		1:
			_profile.hair_color = _cycle(
				AppearanceCatalog.HAIR_COLORS, _profile.hair_color, direction
			)
		2:
			_profile.shirt_style = _cycle(
				AppearanceCatalog.SHIRT_STYLES, _profile.shirt_style, direction
			)
			var colors := AppearanceCatalog.shirt_colors(_profile.shirt_style)
			if _profile.shirt_color not in colors:
				_profile.shirt_color = colors[0]
		3:
			_profile.shirt_color = _cycle(
				AppearanceCatalog.shirt_colors(_profile.shirt_style),
				_profile.shirt_color,
				direction
			)
		4:
			_profile.pants_color = _cycle(
				AppearanceCatalog.PANTS_COLORS, _profile.pants_color, direction
			)
		5:
			_profile.shoes_color = _cycle(
				AppearanceCatalog.SHOES_COLORS, _profile.shoes_color, direction
			)
		6:
			_profile.hat = not _profile.hat
	_profile = AppearanceCatalog.normalized(_profile)
	_preview.apply_profile(_profile)
	_refresh()


func _activate() -> void:
	match _row:
		7:
			_randomize()
		8:
			accepted.emit(_profile.duplicate())
		9:
			backed.emit()


func _randomize() -> void:
	_profile = {
		"hair_style": randi_range(1, 6),
		"hair_color": AppearanceCatalog.HAIR_COLORS.pick_random(),
		"shirt_style": AppearanceCatalog.SHIRT_STYLES.pick_random(),
		"pants_color": AppearanceCatalog.PANTS_COLORS.pick_random(),
		"shoes_color": AppearanceCatalog.SHOES_COLORS.pick_random(),
		"hat": randi_range(0, 1) == 1,
	}
	_profile.shirt_color = AppearanceCatalog.shirt_colors(_profile.shirt_style).pick_random()
	_profile = AppearanceCatalog.normalized(_profile)
	_preview.apply_profile(_profile)
	_refresh()


func _cycle(options: Array, value: Variant, direction: int) -> Variant:
	var index := options.find(value)
	return options[posmod(index + direction, options.size())]


func _refresh() -> void:
	var values := [
		"HAIR: %d" % _profile.hair_style,
		"HAIR COLOR: %s" % _profile.hair_color.to_upper(),
		"TOP: %s" % _profile.shirt_style.replace("_", " ").to_upper(),
		"TOP COLOR: %s" % _profile.shirt_color.replace("_", " ").to_upper(),
		"PANTS: %s" % _profile.pants_color.to_upper(),
		"SHOES: %s" % _profile.shoes_color.to_upper(),
		"HAT: %s" % ("ON" if _profile.hat else "OFF"),
		"RANDOMIZE",
		"CONFIRM",
		"BACK",
	]
	for index in _rows.size():
		_rows[index].text = ("> " if index == _row else "  ") + values[index]
		_rows[index].modulate = Color(1.0, 0.88, 0.3) if index == _row else Color(0.9, 0.82, 0.67)
