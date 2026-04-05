## Mosquito AI - Flies randomly, detects player, chases, bites.
## Types: Normal, Fast, Tanky, Stealth.
extends CharacterBody3D

enum State { IDLE, CHASE, ATTACK, FLEE, DEAD }
enum MosquitoType { NORMAL, FAST, TANKY, STEALTH }

@export var mosquito_type: MosquitoType = MosquitoType.NORMAL
@export var base_speed: float = 3.0
@export var detection_radius: float = 8.0
@export var attack_radius: float = 1.2
@export var bite_cooldown: float = 2.0
@export var hp: int = 1

var state: State = State.IDLE
var player: CharacterBody3D = null
var idle_target: Vector3 = Vector3.ZERO
var idle_timer: float = 0.0
var bite_timer: float = 0.0
var bob_offset: float = 0.0  # Wing bobbing
var room_bounds: AABB = AABB(Vector3(-8, 0.5, -8), Vector3(16, 4, 16))

# Stealth
var is_visible_to_player: bool = true
var stealth_alpha: float = 1.0

var mesh: MeshInstance3D = null
var wing_left: Node3D = null
var wing_right: Node3D = null

func _ready() -> void:
	add_to_group("mosquitoes")
	# Find child nodes safely
	mesh = get_node_or_null("MeshInstance3D") as MeshInstance3D
	wing_left = get_node_or_null("WingLeft")
	wing_right = get_node_or_null("WingRight")
	_apply_type_stats()
	_pick_idle_target()
	bob_offset = randf() * TAU

func _physics_process(delta: float) -> void:
	if state == State.DEAD:
		return

	bob_offset += delta * 15.0  # Wing flutter speed
	_animate_wings(delta)
	_animate_bob(delta)

	# Bite cooldown
	if bite_timer > 0:
		bite_timer -= delta

	match state:
		State.IDLE:
			_process_idle(delta)
		State.CHASE:
			_process_chase(delta)
		State.ATTACK:
			_process_attack(delta)

	move_and_slide()

	# Stealth fade
	if mosquito_type == MosquitoType.STEALTH:
		_update_stealth(delta)

func _process_idle(delta: float) -> void:
	idle_timer -= delta
	if idle_timer <= 0:
		_pick_idle_target()

	# Move towards idle target
	var direction = (idle_target - global_position).normalized()
	velocity = direction * base_speed * 0.5 * GameManager.mosquito_speed_mult

	# Check for player
	if player and global_position.distance_to(player.global_position) < detection_radius:
		state = State.CHASE

func _process_chase(delta: float) -> void:
	if not player or not is_instance_valid(player):
		state = State.IDLE
		return

	var to_player = player.global_position + Vector3(0, 1, 0) - global_position
	var distance = to_player.length()

	if distance > detection_radius * 1.5:
		state = State.IDLE
		return

	if distance < attack_radius:
		state = State.ATTACK
		return

	# Chase with slight wobble for organic feel
	var wobble = Vector3(sin(bob_offset * 0.7) * 0.3, 0, cos(bob_offset * 0.5) * 0.3)
	var direction = (to_player.normalized() + wobble).normalized()
	var speed = base_speed * GameManager.mosquito_speed_mult

	velocity = direction * speed

	# Look at player
	if to_player.length() > 0.1:
		look_at(player.global_position + Vector3(0, 1, 0), Vector3.UP)

func _process_attack(delta: float) -> void:
	if not player or not is_instance_valid(player):
		state = State.IDLE
		return

	var distance = global_position.distance_to(player.global_position + Vector3(0, 1, 0))
	if distance > attack_radius * 1.5:
		state = State.CHASE
		return

	# Attempt bite
	if bite_timer <= 0:
		_bite_player()
		bite_timer = bite_cooldown

func _bite_player() -> void:
	GameManager.register_bite()
	# Brief retreat after bite
	var flee_dir = (global_position - player.global_position).normalized()
	velocity = flee_dir * base_speed * 2.0
	state = State.CHASE

func die() -> void:
	if state == State.DEAD:
		return

	hp -= 1
	if hp > 0:
		# Tanky mosquito takes multiple hits
		_flash_hit()
		return

	state = State.DEAD
	set_physics_process(false)

	# Death animation: shrink + spin
	var tween = create_tween()
	tween.set_parallel(true)
	tween.tween_property(self, "scale", Vector3.ZERO, 0.3).set_ease(Tween.EASE_IN)
	tween.tween_property(self, "rotation_degrees:y", rotation_degrees.y + 720, 0.3)
	tween.chain().tween_callback(queue_free)

func _flash_hit() -> void:
	if mesh:
		var mat = mesh.get_surface_override_material(0)
		if mat is StandardMaterial3D:
			var orig = mat.albedo_color
			mat.albedo_color = Color.WHITE
			await get_tree().create_timer(0.1).timeout
			mat.albedo_color = orig

func _pick_idle_target() -> void:
	idle_target = Vector3(
		randf_range(room_bounds.position.x, room_bounds.end.x),
		randf_range(1.0, 3.0),
		randf_range(room_bounds.position.z, room_bounds.end.z)
	)
	idle_timer = randf_range(2.0, 5.0)

func _animate_wings(delta: float) -> void:
	# Simple wing flap using sine wave
	var flap = sin(bob_offset) * 45.0
	if wing_left:
		wing_left.rotation_degrees.z = flap
	if wing_right:
		wing_right.rotation_degrees.z = -flap

func _animate_bob(delta: float) -> void:
	# Gentle vertical bobbing
	position.y += sin(bob_offset * 0.5) * delta * 0.3

func _apply_type_stats() -> void:
	match mosquito_type:
		MosquitoType.NORMAL:
			base_speed = 3.0
			hp = 1
			detection_radius = 8.0
		MosquitoType.FAST:
			base_speed = 5.5
			hp = 1
			detection_radius = 10.0
			if mesh:
				var mat = StandardMaterial3D.new()
				mat.albedo_color = Color(0.2, 0.8, 0.2)  # Green
				mesh.set_surface_override_material(0, mat)
		MosquitoType.TANKY:
			base_speed = 2.0
			hp = 3
			detection_radius = 6.0
			scale = Vector3.ONE * 1.5  # Bigger
			if mesh:
				var mat = StandardMaterial3D.new()
				mat.albedo_color = Color(0.8, 0.2, 0.2)  # Red
				mesh.set_surface_override_material(0, mat)
		MosquitoType.STEALTH:
			base_speed = 3.5
			hp = 1
			detection_radius = 12.0

func _update_stealth(delta: float) -> void:
	if state == State.CHASE or state == State.ATTACK:
		stealth_alpha = move_toward(stealth_alpha, 0.3, delta * 2.0)
	else:
		stealth_alpha = move_toward(stealth_alpha, 0.05, delta * 1.0)
	if mesh:
		var mat = mesh.get_surface_override_material(0)
		if mat is StandardMaterial3D:
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mat.albedo_color.a = stealth_alpha

func set_player_ref(p: CharacterBody3D) -> void:
	player = p
