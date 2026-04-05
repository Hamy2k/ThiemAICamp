## PowerUp - Collectible items that spawn randomly.
## Types: Shield (block bites), Strong Racket (more damage + score).
extends Area3D

enum PowerUpType { SHIELD, STRONG_RACKET }

@export var powerup_type: PowerUpType = PowerUpType.SHIELD
@export var lifetime: float = 15.0

var bob_offset: float = 0.0

@onready var mesh: MeshInstance3D = $MeshInstance3D

func _ready() -> void:
	body_entered.connect(_on_body_entered)
	bob_offset = randf() * TAU

	# Color based on type
	var mat = StandardMaterial3D.new()
	mat.emission_enabled = true
	match powerup_type:
		PowerUpType.SHIELD:
			mat.albedo_color = Color(0.2, 0.5, 1.0)
			mat.emission = Color(0.2, 0.5, 1.0)
		PowerUpType.STRONG_RACKET:
			mat.albedo_color = Color(1.0, 0.8, 0.0)
			mat.emission = Color(1.0, 0.8, 0.0)
	mat.emission_energy_multiplier = 2.0
	if mesh:
		mesh.set_surface_override_material(0, mat)

	# Auto-destroy after lifetime
	await get_tree().create_timer(lifetime).timeout
	if is_inside_tree():
		_fade_out()

func _process(delta: float) -> void:
	bob_offset += delta * 3.0
	position.y += sin(bob_offset) * delta * 0.5
	rotation_degrees.y += delta * 90.0  # Spin

func _on_body_entered(body: Node3D) -> void:
	if body.is_in_group("player"):
		match powerup_type:
			PowerUpType.SHIELD:
				GameManager.activate_powerup("shield")
			PowerUpType.STRONG_RACKET:
				GameManager.activate_powerup("strong_racket")
		queue_free()

func _fade_out() -> void:
	var tween = create_tween()
	tween.tween_property(self, "scale", Vector3.ZERO, 0.3)
	tween.tween_callback(queue_free)
