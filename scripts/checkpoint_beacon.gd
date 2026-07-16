class_name CheckpointBeacon
extends Node2D

## A persistent road marker for each autosave point. It uses the supplied lantern
## art and a small code-drawn glow, so activation remains clear without another
## generated sprite asset.

const LANTERN := preload(
	"res://assets/cute_fantasy/packs/Cute_Fantasy/Cute_Fantasy/Outdoor decoration/Lantern.png"
)

var _active := false
var _pulse := 0.0
var _phase := randf() * TAU
var _sprite: Sprite2D


func _ready() -> void:
	_sprite = Sprite2D.new()
	_sprite.texture = LANTERN
	_sprite.position = Vector2(0, -12)
	add_child(_sprite)
	_refresh()


func set_active(value: bool, celebrate := false) -> void:
	_active = value
	if celebrate:
		_pulse = 0.85
	_refresh()


func _process(delta: float) -> void:
	_phase += delta * 2.4
	_pulse = maxf(0.0, _pulse - delta)
	_refresh()


func _refresh() -> void:
	if _sprite == null:
		return
	var flicker := 0.08 * sin(_phase)
	_sprite.modulate = (
		Color(1.0, 0.84 + flicker, 0.42, 1.0) if _active else Color(0.42, 0.45, 0.44, 0.8)
	)
	_sprite.scale = Vector2.ONE * (1.0 + _pulse * 0.18)
	queue_redraw()


func _draw() -> void:
	if not _active:
		return
	var radius := 11.0 + sin(_phase) * 1.5 + _pulse * 12.0
	draw_circle(Vector2(0, -12), radius, Color(1.0, 0.67, 0.18, 0.14 + _pulse * 0.16))
