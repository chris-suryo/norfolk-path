extends Control

## Quest-complete screen shown after Irene is defeated. Pressing accept clears
## the run and returns to player-select so the game can be played again.

const SELECT_SCENE := "res://scenes/player_select.tscn"


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		Game.reset_run()
		Game.save()
		get_tree().change_scene_to_file(SELECT_SCENE)
