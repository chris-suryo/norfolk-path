extends CanvasLayer

## In-world health HUD: P1's bar hugs the top-left, P2's the top-right. Both are
## TextureProgressBars skinned from the Cute Fantasy UI_Bars pill (a full green
## pill as texture_progress, the same pill darkened via tint_under as the empty
## track), so the fill depletes on hit and refills on revive.
##
## Anchoring is the boss-bar lesson applied: P2 anchors to the RIGHT edge (anchor
## 1.0), not an absolute offset, so it stays glued to the corner when the
## expand-aspect viewport is wider than the 640 design width.
##
## main.gd calls bind_player() for each live player after positioning them (the
## players' own _ready fires health_changed before this HUD is connected, so the
## bind reads hp() once to seed the bar, then rides the signal after that). P2's
## widgets are hidden in 1-player, where Player2 is freed.

var _bars := {}
var _hp_labels := {}

@onready var _p2_name: Label = $P2Name
@onready var _p2_bar: TextureProgressBar = $P2Bar
@onready var _p2_hp: Label = $P2HP
@onready var _checkpoint_toast: Label = $CheckpointToast
@onready var _move_hint: Label = $MoveHint


func _ready() -> void:
	_bars = {1: $P1Bar, 2: _p2_bar}
	# A number beside each bar — the bar alone (far corner, no digits) was the only
	# health readout (R4-21).
	_hp_labels = {1: $P1HP, 2: _p2_hp}
	if Game.player_count < 2:
		_p2_name.visible = false
		_p2_bar.visible = false
		_p2_hp.visible = false


## Wire one player's health to its bar and seed the current value immediately.
func bind_player(player: Node) -> void:
	var idx: int = player.player_index
	if not _bars.has(idx):
		return
	player.health_changed.connect(_on_health_changed.bind(idx))
	_on_health_changed(player.hp(), player.max_hp, idx)


func _on_health_changed(current: int, maximum: int, idx: int) -> void:
	var bar: TextureProgressBar = _bars[idx]
	bar.max_value = maximum
	bar.value = current
	_hp_labels[idx].text = "%d/%d" % [current, maximum]


func show_checkpoint_saved() -> void:
	_checkpoint_toast.modulate.a = 1.0
	_checkpoint_toast.visible = true
	var tween := create_tween()
	# Hold longer so it isn't lost in motion (R4-22).
	tween.tween_interval(1.6)
	tween.tween_property(_checkpoint_toast, "modulate:a", 0.0, 0.35)
	tween.tween_callback(func(): _checkpoint_toast.visible = false)


## The one-time "here's how to move" hint at the start of a fresh run — cued by
## the intro cutscene when it hands control back. Fades on its own after a beat.
func show_move_hint() -> void:
	_move_hint.modulate.a = 1.0
	_move_hint.visible = true
	var tween := create_tween()
	tween.tween_interval(4.0)
	tween.tween_property(_move_hint, "modulate:a", 0.0, 0.4)
	tween.tween_callback(func(): _move_hint.visible = false)
