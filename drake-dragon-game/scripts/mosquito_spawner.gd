## MosquitoSpawner - Manages spawning waves of mosquitoes with type variety.
## Spawns at random positions along room edges, respects max count.
extends Node3D

@export var mosquito_scene: PackedScene
var player: CharacterBody3D = null
var spawn_timer: float = 0.0
var active_mosquitoes: int = 0
var room_bounds: AABB = AABB(Vector3(-7, 1, -7), Vector3(14, 3, 14))

func _ready() -> void:
	# Find player
	await get_tree().create_timer(0.1).timeout
	player = get_tree().get_first_node_in_group("player") as CharacterBody3D

func _process(delta: float) -> void:
	if GameManager.is_game_over:
		return

	# Count active mosquitoes
	active_mosquitoes = get_tree().get_nodes_in_group("mosquitoes").size()

	spawn_timer -= delta
	if spawn_timer <= 0 and active_mosquitoes < GameManager.max_mosquitoes:
		_spawn_mosquito()
		spawn_timer = GameManager.spawn_interval

func _spawn_mosquito() -> void:
	if not mosquito_scene:
		mosquito_scene = _create_mosquito_scene()
	if not mosquito_scene:
		return

	var mosquito = mosquito_scene.instantiate()

	# Random spawn position at room edges
	var edge = randi() % 4
	var pos: Vector3
	match edge:
		0: pos = Vector3(room_bounds.position.x, randf_range(1.5, 3.0), randf_range(room_bounds.position.z, room_bounds.end.z))
		1: pos = Vector3(room_bounds.end.x, randf_range(1.5, 3.0), randf_range(room_bounds.position.z, room_bounds.end.z))
		2: pos = Vector3(randf_range(room_bounds.position.x, room_bounds.end.x), randf_range(1.5, 3.0), room_bounds.position.z)
		3: pos = Vector3(randf_range(room_bounds.position.x, room_bounds.end.x), randf_range(1.5, 3.0), room_bounds.end.z)

	mosquito.global_position = pos

	# Assign type based on difficulty
	var type_roll = randf()
	if GameManager.difficulty > 2.0 and type_roll < 0.15:
		mosquito.mosquito_type = mosquito.MosquitoType.STEALTH
	elif GameManager.difficulty > 1.5 and type_roll < 0.3:
		mosquito.mosquito_type = mosquito.MosquitoType.TANKY
	elif GameManager.difficulty > 1.2 and type_roll < 0.5:
		mosquito.mosquito_type = mosquito.MosquitoType.FAST

	add_child(mosquito)

	if player and mosquito.has_method("set_player_ref"):
		mosquito.set_player_ref(player)

func _create_mosquito_scene() -> PackedScene:
	# Procedural mosquito: body (dark ellipsoid) + wings
	var scene = PackedScene.new()
	var body = CharacterBody3D.new()
	body.name = "Mosquito"

	# Collision shape
	var col = CollisionShape3D.new()
	var shape = SphereShape3D.new()
	shape.radius = 0.3
	col.shape = shape
	body.add_child(col)
	col.owner = body

	# Body mesh (dark elongated sphere)
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
	mesh_inst.rotation_degrees.x = 90  # Horizontal body
	body.add_child(mesh_inst)
	mesh_inst.owner = body

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
	wing_l.owner = body

	# Right wing
	var wing_r = MeshInstance3D.new()
	wing_r.name = "WingRight"
	wing_r.mesh = wing_mesh
	wing_r.position = Vector3(0.15, 0.08, 0)
	wing_r.rotation_degrees = Vector3(0, 0, -30)
	body.add_child(wing_r)
	wing_r.owner = body

	# Detection area
	var det_area = Area3D.new()
	det_area.name = "DetectionArea"
	var det_col = CollisionShape3D.new()
	var det_shape = SphereShape3D.new()
	det_shape.radius = 8.0
	det_col.shape = det_shape
	det_area.add_child(det_col)
	det_col.owner = body
	det_area.owner = body
	body.add_child(det_area)

	# Attach script
	body.set_script(load("res://scripts/mosquito.gd"))

	# Set collision layers: layer 3 (Mosquitoes)
	body.collision_layer = 4  # bit 3
	body.collision_mask = 1   # collide with environment

	scene.pack(body)
	return scene
