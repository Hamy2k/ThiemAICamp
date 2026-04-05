## MosquitoSpawner - Manages spawning waves of mosquitoes with type variety.
extends Node3D

var player: CharacterBody3D = null
var spawn_timer: float = 0.0
var active_mosquitoes: int = 0
var room_bounds: AABB = AABB(Vector3(-7, 1, -7), Vector3(14, 3, 14))

func _ready() -> void:
	await get_tree().create_timer(0.5).timeout
	player = get_tree().get_first_node_in_group("player") as CharacterBody3D

func _process(delta: float) -> void:
	if GameManager.is_game_over:
		return

	active_mosquitoes = get_tree().get_nodes_in_group("mosquitoes").size()

	spawn_timer -= delta
	if spawn_timer <= 0 and active_mosquitoes < GameManager.max_mosquitoes:
		_spawn_mosquito()
		spawn_timer = GameManager.spawn_interval

func _spawn_mosquito() -> void:
	var mosquito = _build_mosquito()

	# Random spawn position at room edges
	var edge = randi() % 4
	var pos: Vector3
	match edge:
		0: pos = Vector3(room_bounds.position.x, randf_range(1.5, 3.0), randf_range(room_bounds.position.z, room_bounds.end.z))
		1: pos = Vector3(room_bounds.end.x, randf_range(1.5, 3.0), randf_range(room_bounds.position.z, room_bounds.end.z))
		2: pos = Vector3(randf_range(room_bounds.position.x, room_bounds.end.x), randf_range(1.5, 3.0), room_bounds.position.z)
		3: pos = Vector3(randf_range(room_bounds.position.x, room_bounds.end.x), randf_range(1.5, 3.0), room_bounds.end.z)

	# Add to tree FIRST, then set position
	add_child(mosquito)
	mosquito.global_position = pos

	# Assign type based on difficulty
	var type_roll = randf()
	if GameManager.difficulty > 2.0 and type_roll < 0.15:
		mosquito.mosquito_type = mosquito.MosquitoType.STEALTH
	elif GameManager.difficulty > 1.5 and type_roll < 0.3:
		mosquito.mosquito_type = mosquito.MosquitoType.TANKY
	elif GameManager.difficulty > 1.2 and type_roll < 0.5:
		mosquito.mosquito_type = mosquito.MosquitoType.FAST

	# Apply type stats after setting type
	if mosquito.has_method("_apply_type_stats"):
		mosquito._apply_type_stats()

	if player and mosquito.has_method("set_player_ref"):
		mosquito.set_player_ref(player)

func _build_mosquito() -> CharacterBody3D:
	"""Build mosquito node tree procedurally (no PackedScene/owner needed)."""
	var body = CharacterBody3D.new()
	body.name = "Mosquito"
	body.collision_layer = 4  # Mosquitoes layer
	body.collision_mask = 1   # Environment

	# Collision shape
	var col = CollisionShape3D.new()
	var shape = SphereShape3D.new()
	shape.radius = 0.3
	col.shape = shape
	body.add_child(col)

	# Body mesh (dark capsule)
	var mesh_inst = MeshInstance3D.new()
	mesh_inst.name = "MeshInstance3D"
	var capsule = CapsuleMesh.new()
	capsule.radius = 0.12
	capsule.height = 0.4
	var mat = StandardMaterial3D.new()
	mat.albedo_color = Color(0.15, 0.1, 0.1)
	mat.roughness = 0.9
	capsule.material = mat
	mesh_inst.mesh = capsule
	mesh_inst.rotation_degrees.x = 90
	body.add_child(mesh_inst)

	# Left wing
	var wing_l = MeshInstance3D.new()
	wing_l.name = "WingLeft"
	var wing_mesh = PlaneMesh.new()
	wing_mesh.size = Vector2(0.3, 0.15)
	var wing_mat = StandardMaterial3D.new()
	wing_mat.albedo_color = Color(0.8, 0.8, 0.9, 0.5)
	wing_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	wing_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	wing_mesh.material = wing_mat
	wing_l.mesh = wing_mesh
	wing_l.position = Vector3(-0.15, 0.08, 0)
	wing_l.rotation_degrees = Vector3(0, 0, 30)
	body.add_child(wing_l)

	# Right wing
	var wing_r = MeshInstance3D.new()
	wing_r.name = "WingRight"
	wing_r.mesh = wing_mesh
	wing_r.position = Vector3(0.15, 0.08, 0)
	wing_r.rotation_degrees = Vector3(0, 0, -30)
	body.add_child(wing_r)

	# Attach script BEFORE adding to tree
	body.set_script(load("res://scripts/mosquito.gd"))

	return body
