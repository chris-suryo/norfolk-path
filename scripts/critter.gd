class_name Critter
extends Sprite2D

## Cycles a couple of spritesheet frames so a critter reads as alive.
## Not an animation system — one accumulator, no states.

## Frames per second for the idle cycle.
@export var fps := 2.0
## How many frames to cycle through, starting at first_frame.
@export var frame_count := 2
## First frame of the cycle within the sheet.
@export var first_frame := 0

var _time := 0.0


func _process(delta: float) -> void:
	_time += delta
	frame = first_frame + int(_time * fps) % frame_count
