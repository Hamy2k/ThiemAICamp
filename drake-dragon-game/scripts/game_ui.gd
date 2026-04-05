## GameUI - HUD displaying bites, health, score, combo, and game over screen.
extends CanvasLayer

@onready var bite_label: Label = $HUD/BiteLabel
@onready var score_label: Label = $HUD/ScoreLabel
@onready var health_bar: ProgressBar = $HUD/HealthBar
@onready var combo_label: Label = $HUD/ComboLabel
@onready var powerup_label: Label = $HUD/PowerUpLabel
@onready var game_over_panel: PanelContainer = $GameOverPanel
@onready var final_score_label: Label = $GameOverPanel/VBox/FinalScoreLabel
@onready var restart_button: Button = $GameOverPanel/VBox/RestartButton
@onready var swing_button: Button = $HUD/SwingButton

var player: CharacterBody3D = null

func _ready() -> void:
	game_over_panel.visible = false
	combo_label.visible = false
	powerup_label.visible = false

	GameManager.bite_received.connect(_on_bite)
	GameManager.mosquito_killed.connect(_on_kill)
	GameManager.combo_updated.connect(_on_combo)
	GameManager.game_over_triggered.connect(_on_game_over)
	GameManager.powerup_activated.connect(_on_powerup)

	restart_button.pressed.connect(_on_restart)
	swing_button.pressed.connect(_on_swing_pressed)

	_update_display()

func _process(_delta: float) -> void:
	health_bar.value = GameManager.get_player_health_percent() * 100.0

func _on_bite(total: int) -> void:
	bite_label.text = "Bites: %d / %d" % [total, GameManager.max_bites]
	_flash_label(bite_label, Color.RED)

func _on_kill(total: int, combo: int) -> void:
	score_label.text = "Score: %d" % GameManager.score
	_flash_label(score_label, Color.YELLOW)

func _on_combo(combo: int) -> void:
	if combo >= 2:
		combo_label.visible = true
		combo_label.text = "COMBO x%d!" % combo
		combo_label.modulate = Color.YELLOW
		var tween = create_tween()
		tween.tween_property(combo_label, "scale", Vector2.ONE * 1.3, 0.1)
		tween.tween_property(combo_label, "scale", Vector2.ONE, 0.2)
	else:
		combo_label.visible = false

func _on_powerup(type: String) -> void:
	powerup_label.visible = true
	match type:
		"shield":
			powerup_label.text = "SHIELD ACTIVE!"
			powerup_label.modulate = Color(0.3, 0.6, 1.0)
		"strong_racket":
			powerup_label.text = "POWER RACKET!"
			powerup_label.modulate = Color(1.0, 0.8, 0.0)

	# Hide after duration
	await get_tree().create_timer(8.0).timeout
	powerup_label.visible = false

func _on_game_over(final_score: int) -> void:
	game_over_panel.visible = true
	final_score_label.text = "Final Score: %d\nMosquitoes Killed: %d\nMax Combo: x%d" % [
		final_score, GameManager.kills, GameManager.combo
	]

func _on_restart() -> void:
	GameManager.reset_game()
	get_tree().reload_current_scene()

func _on_swing_pressed() -> void:
	if not player:
		player = get_tree().get_first_node_in_group("player")
	if player and player.has_method("swing_racket"):
		player.swing_racket()

func _flash_label(label: Label, color: Color) -> void:
	label.modulate = color
	var tween = create_tween()
	tween.tween_property(label, "modulate", Color.WHITE, 0.3)

func _update_display() -> void:
	bite_label.text = "Bites: 0 / %d" % GameManager.max_bites
	score_label.text = "Score: 0"
	health_bar.value = 100.0
