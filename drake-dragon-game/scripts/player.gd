## Player Controller - Cute character with electric mosquito racket.
## Handles movement, racket swing, bite effects, and animations.
extends CharacterBody3D

@export var base_speed: float = 5.0
@export var rotation_speed: float = 10.0
@export var swing_cooldown: float = 0.4

@onready var model: Node3D = $Model
@onready var racket_area: Area3D = $Model/RacketPivot/RacketArea
@onready var racket_pivot: Node3D = $Model/RacketPivot
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var bite_bumps_container: Node3D = $Model/BiteBumps
@onready var zap_particles: GPUParticles3D = $Model/RacketPivot/ZapParticles

var can_swing: bool = true
var swing_timer: float = 0.0
var is_swinging: bool = false
var move_input: Vector2 = Vector2.ZERO  # From virtual joystick

# Bump tracking for visual comedy
var bump_positions: Array[Vector3] = []
var bump_scene: PackedScene = null

func _ready() -> void:
	GameManager.bite_received.connect(_on_bite_received)
	racket_area.monitoring = false
	if zap_particles:
		zap_particles.emitting = false

	# Create simple bump mesh for bites
	bump_scene = _create_bump_scene()

func _physics_process(delta: float) -> void:
	if GameManager.is_game_over:
		return

	# Handle movement
	var speed = base_speed * GameManager.get_player_speed_multiplier()
	var direction = Vector3(move_input.x, 0, move_input.y).normalized()

	if direction.length() > 0.1:
		# Rotate towards movement direction
		var target_rotation = atan2(direction.x, direction.z)
		model.rotation.y = lerp_angle(model.rotation.y, target_rotation, delta * rotation_speed)
		velocity = direction * speed
	else:
		velocity = velocity.move_toward(Vector3.ZERO, speed * delta * 10.0)

	velocity.y -= 9.8 * delta  # Gravity
	move_and_slide()

	# Swing cooldown
	if not can_swing:
		swing_timer -= delta
		if swing_timer <= 0:
			can_swing = true
			is_swinging = false
			racket_area.monitoring = false

func set_move_input(input: Vector2) -> void:
	move_input = input

func swing_racket() -> void:
	if not can_swing or GameManager.is_game_over:
		return

	can_swing = false
	is_swinging = true
	swing_timer = swing_cooldown
	racket_area.monitoring = true

	# Swing animation
	_play_swing_animation()

	# Check for mosquitoes in racket area
	await get_tree().create_timer(0.05).timeout
	var bodies = racket_area.get_overlapping_bodies()
	for body in bodies:
		if body.is_in_group("mosquitoes"):
			_zap_mosquito(body)

func _play_swing_animation() -> void:
	# Procedural swing: rotate racket pivot
	var tween = create_tween()
	tween.tween_property(racket_pivot, "rotation_degrees:x", -120.0, 0.1)
	tween.tween_property(racket_pivot, "rotation_degrees:x", 0.0, 0.3).set_ease(Tween.EASE_OUT)

func _zap_mosquito(mosquito: Node3D) -> void:
	if mosquito.has_method("die"):
		# Zap effect
		if zap_particles:
			zap_particles.global_position = mosquito.global_position
			zap_particles.emitting = true
			zap_particles.restart()

		mosquito.die()
		GameManager.register_kill()

func _on_bite_received(total_bites: int) -> void:
	_add_bite_bump()
	# Flash red briefly
	_flash_damage()

func _add_bite_bump() -> void:
	if not bump_scene:
		return
	var bump = bump_scene.instantiate()
	# Random position on character body
	var random_offset = Vector3(
		randf_range(-0.3, 0.3),
		randf_range(0.2, 1.5),
		randf_range(-0.2, 0.2)
	)
	bump.position = random_offset
	bite_bumps_container.add_child(bump)

	# Pop-in animation
	bump.scale = Vector3.ZERO
	var tween = create_tween()
	tween.tween_property(bump, "scale", Vector3.ONE * 0.15, 0.2).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)

func _flash_damage() -> void:
	# Brief red flash on model
	if model.get_child_count() > 0:
		var mesh = _find_mesh_instance(model)
		if mesh and mesh.get_surface_override_material(0):
			var mat = mesh.get_surface_override_material(0) as StandardMaterial3D
			if mat:
				var orig_color = mat.albedo_color
				mat.albedo_color = Color.RED
				await get_tree().create_timer(0.1).timeout
				mat.albedo_color = orig_color

func _find_mesh_instance(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node
	for child in node.get_children():
		var found = _find_mesh_instance(child)
		if found:
			return found
	return null

func _create_bump_scene() -> PackedScene:
	# Create a red sphere bump procedurally
	var scene = PackedScene.new()
	var mesh_inst = MeshInstance3D.new()
	var sphere = SphereMesh.new()
	sphere.radius = 0.5
	sphere.height = 0.8
	var mat = StandardMaterial3D.new()
	mat.albedo_color = Color(0.9, 0.2, 0.2)
	mat.roughness = 0.8
	sphere.material = mat
	mesh_inst.mesh = sphere
	scene.pack(mesh_inst)
	return scene
