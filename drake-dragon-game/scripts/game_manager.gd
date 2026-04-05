## GameManager - Autoload singleton managing global game state.
## Tracks score, bites, combos, difficulty, and game flow.
extends Node

signal bite_received(total_bites: int)
signal mosquito_killed(total_kills: int, combo: int)
signal game_over_triggered(final_score: int)
signal combo_updated(combo: int)
signal powerup_activated(type: String)

# ── Game State ─────────────────────────────────────────────────
var score: int = 0
var bites: int = 0
var max_bites: int = 100
var kills: int = 0
var combo: int = 0
var combo_timer: float = 0.0
var combo_window: float = 1.5  # seconds to chain kills

var is_game_over: bool = false
var is_paused: bool = false
var game_time: float = 0.0

# ── Difficulty Scaling ─────────────────────────────────────────
var difficulty: float = 1.0
var max_mosquitoes: int = 5
var spawn_interval: float = 3.0
var mosquito_speed_mult: float = 1.0

# ── Power-ups ──────────────────────────────────────────────────
var shield_active: bool = false
var strong_racket: bool = false
var powerup_duration: float = 0.0

func _ready() -> void:
	reset_game()

func _process(delta: float) -> void:
	if is_game_over or is_paused:
		return

	game_time += delta

	# Combo decay
	if combo > 0:
		combo_timer -= delta
		if combo_timer <= 0:
			combo = 0
			combo_updated.emit(combo)

	# Power-up timer
	if powerup_duration > 0:
		powerup_duration -= delta
		if powerup_duration <= 0:
			shield_active = false
			strong_racket = false

	# Difficulty scaling over time
	difficulty = 1.0 + (game_time / 60.0) * 0.5  # +50% per minute
	max_mosquitoes = mini(5 + int(game_time / 20.0), 15)
	spawn_interval = maxf(3.0 - (game_time / 60.0), 0.8)
	mosquito_speed_mult = 1.0 + (game_time / 120.0)

func register_bite() -> void:
	if shield_active:
		return
	bites += 1
	bite_received.emit(bites)
	if bites >= max_bites:
		trigger_game_over()

func register_kill() -> void:
	kills += 1
	combo += 1
	combo_timer = combo_window

	# Score: base + combo bonus
	var points = 10 + (combo - 1) * 5
	if strong_racket:
		points = int(points * 1.5)
	score += points

	mosquito_killed.emit(kills, combo)
	combo_updated.emit(combo)

func activate_powerup(type: String) -> void:
	match type:
		"shield":
			shield_active = true
			powerup_duration = 8.0
		"strong_racket":
			strong_racket = true
			powerup_duration = 10.0
	powerup_activated.emit(type)

func get_player_speed_multiplier() -> float:
	# Movement slows as bites increase
	return maxf(1.0 - (float(bites) / float(max_bites)) * 0.6, 0.4)

func get_player_health_percent() -> float:
	return 1.0 - (float(bites) / float(max_bites))

func trigger_game_over() -> void:
	is_game_over = true
	game_over_triggered.emit(score)

func reset_game() -> void:
	score = 0
	bites = 0
	kills = 0
	combo = 0
	combo_timer = 0.0
	is_game_over = false
	is_paused = false
	game_time = 0.0
	difficulty = 1.0
	max_mosquitoes = 5
	spawn_interval = 3.0
	mosquito_speed_mult = 1.0
	shield_active = false
	strong_racket = false
	powerup_duration = 0.0
