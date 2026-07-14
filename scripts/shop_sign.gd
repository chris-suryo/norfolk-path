class_name ShopSign
extends StaticBody2D

## Evan's shop: a house sprite with solid footing and a proximity one-liner.
##
## Walking into the Area2D around the door shows a single text line; walking
## away hides it. This is deliberately NOT a dialogue system — no interaction
## key, no branching, one Label on a CanvasLayer — just enough to prove
## proximity-triggered text before a real dialogue pass exists.

## The line shown when the player is near.
@export var line: String = "Toasted, or the old way?"

@onready var _label: Label = $CanvasLayer/Label
@onready var _area: Area2D = $Area2D


func _ready() -> void:
	_label.text = line
	_label.visible = false
	_area.body_entered.connect(_on_body_entered)
	_area.body_exited.connect(_on_body_exited)


func _on_body_entered(body: Node2D) -> void:
	if body is Player:
		_label.visible = true


func _on_body_exited(body: Node2D) -> void:
	if body is Player:
		_label.visible = false
