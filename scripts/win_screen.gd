extends Control

## Quest-complete screen shown after Irene is defeated. Pressing accept clears
## the run and returns to player-select so the game can be played again. The
## closing line branches on the answer the player gave Irene at the door
## (Game.irene_choice); a skipped door falls back to the "friend" line.

const SELECT_SCENE := "res://scenes/player_select.tscn"

@onready var _ariana: Label = $Frame/Box/Ariana


func _ready() -> void:
	match Game.irene_choice:
		"dvd":
			_ariana.text = "Did you bring it?"
		_:
			_ariana.text = "I didn't need saving."


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		Game.reset_run()
		Game.save()
		Game.change_scene(SELECT_SCENE)
