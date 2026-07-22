extends Node

## Audio autoload ("Audio"): one place for every sound the game makes.
##
## Call sites are one-liners — `Audio.sfx("sword_swing")`,
## `Audio.play_music("overworld")` — and EVERY level knob lives in the MIX
## table below, so post-playtest tuning is one block, not a hunt across
## scripts. NOTHING calls this yet: the hooks land as their own slice once the
## currently-open PRs merge (this file + its assets are deliberately
## conflict-free).
##
## SFX come from tools/gen_audio.py (deterministic, project-original — no
## third-party license; see assets/audio/LICENSES.md). Music slots are wired
## but EMPTY on purpose: looping music is a taste call — drop .ogg files in
## assets/audio/music/ and register them in TRACKS.
##
## Web note: browsers gate audio behind the first user input. The title
## screen's first keypress unlocks the context automatically in Godot 4; if
## the first sound ever plays silent on web, that gate is the first suspect.

## Every playable effect -> its generated file. Ids match gen_audio.py.
const SFX := {
	"sword_swing": "res://assets/audio/sfx/sword_swing.wav",
	"hit_connect": "res://assets/audio/sfx/hit_connect.wav",
	"bow_shoot": "res://assets/audio/sfx/bow_shoot.wav",
	"player_hurt": "res://assets/audio/sfx/player_hurt.wav",
	"enemy_die": "res://assets/audio/sfx/enemy_die.wav",
	"chest_open": "res://assets/audio/sfx/chest_open.wav",
	"door": "res://assets/audio/sfx/door.wav",
	"ui_select": "res://assets/audio/sfx/ui_select.wav",
	"dialogue_blip": "res://assets/audio/sfx/dialogue_blip.wav",
	"checkpoint": "res://assets/audio/sfx/checkpoint.wav",
	"boss_sting": "res://assets/audio/sfx/boss_sting.wav",
	"win_fanfare": "res://assets/audio/sfx/win_fanfare.wav",
}

## Music slots — EMPTY until Chris picks loops (e.g. "overworld", "boss",
## "cove"). play_music() no-ops gracefully on an unknown id, so hook code can
## land before the tracks exist.
const TRACKS := {}

## THE tuning block. Master levels in dB, then per-id offsets — a sound that's
## too loud in playtest gets one line here, not a regenerated file.
const MIX := {
	"sfx_db": -8.0,
	"music_db": -10.0,
	"per":
	{
		"dialogue_blip": -6.0,
		"ui_select": -4.0,
		"hit_connect": 2.0,
		"boss_sting": 2.0,
	},
}

## How many SFX can overlap before the oldest is stolen. 8 covers a busy
## co-op camp fight (2 swords + hits + deaths + bolts) comfortably.
const POOL_SIZE := 8

## Small random pitch spread per SFX play so repeated hits don't machine-gun
## the identical sample.
const PITCH_JITTER := 0.06

const MUSIC_FADE := 1.2

var muted := false

var _streams := {}
var _pool: Array[AudioStreamPlayer] = []
var _pool_idx := 0
var _music_a: AudioStreamPlayer
var _music_b: AudioStreamPlayer
var _music_active: AudioStreamPlayer
var _current_track := ""


func _ready() -> void:
	# Sounds must survive the paused tree (menus blip while paused).
	process_mode = Node.PROCESS_MODE_ALWAYS
	for id: String in SFX:
		var stream := load(SFX[id])
		if stream != null:
			_streams[id] = stream
	for id: String in TRACKS:
		var stream := load(TRACKS[id])
		if stream != null:
			_streams[id] = stream
	for _i in POOL_SIZE:
		var player := AudioStreamPlayer.new()
		add_child(player)
		_pool.append(player)
	_music_a = AudioStreamPlayer.new()
	_music_b = AudioStreamPlayer.new()
	add_child(_music_a)
	add_child(_music_b)
	_music_active = _music_a


## Fire-and-forget one-shot. Unknown/missing ids no-op (fail-quiet is right
## for audio: a missing sound must never crash or spam errors mid-combat).
func sfx(id: String) -> void:
	if muted or not _streams.has(id):
		return
	var player := _pool[_pool_idx]
	_pool_idx = (_pool_idx + 1) % POOL_SIZE
	player.stream = _streams[id]
	player.volume_db = MIX.sfx_db + float(MIX.per.get(id, 0.0))
	player.pitch_scale = randf_range(1.0 - PITCH_JITTER, 1.0 + PITCH_JITTER)
	player.play()


## Crossfade to a registered track; "" fades music out. Re-requesting the
## playing track is a no-op, so per-level hooks can call this unconditionally.
func play_music(id: String) -> void:
	if id == _current_track:
		return
	_current_track = id
	var incoming := _music_b if _music_active == _music_a else _music_a
	var outgoing := _music_active
	_music_active = incoming
	if outgoing.playing:
		var fade_out := create_tween()
		fade_out.tween_property(outgoing, "volume_db", -60.0, MUSIC_FADE)
		fade_out.tween_callback(outgoing.stop)
	if muted or id == "" or not _streams.has(id):
		return
	incoming.stream = _streams[id]
	incoming.volume_db = -60.0
	incoming.play()
	var fade_in := create_tween()
	fade_in.tween_property(incoming, "volume_db", MIX.music_db, MUSIC_FADE)


## Kill switch (a future settings row can flip this): stops music, silences
## future sfx() calls.
func set_muted(value: bool) -> void:
	muted = value
	if muted:
		play_music("")
