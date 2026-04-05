## RoomBuilder - Procedurally generates the bedroom/living room environment.
## Creates floor, walls, and furniture using primitive meshes.
extends Node3D

const ROOM_WIDTH: float = 16.0
const ROOM_DEPTH: float = 16.0
const ROOM_HEIGHT: float = 4.0
const WALL_THICKNESS: float = 0.3

func _ready() -> void:
	_build_room()
	_add_furniture()
	_add_lighting()

func _build_room() -> void:
	var half_w = ROOM_WIDTH / 2.0
	var half_d = ROOM_DEPTH / 2.0

	# Floor
	_create_box(
		Vector3(0, -0.15, 0),
		Vector3(ROOM_WIDTH, WALL_THICKNESS, ROOM_DEPTH),
		Color(0.6, 0.5, 0.35),  # Wooden floor color
		true  # static body for collision
	)

	# Ceiling
	_create_box(
		Vector3(0, ROOM_HEIGHT, 0),
		Vector3(ROOM_WIDTH, WALL_THICKNESS, ROOM_DEPTH),
		Color(0.9, 0.9, 0.85),
		false
	)

	# Walls
	# Back wall
	_create_box(
		Vector3(0, ROOM_HEIGHT / 2.0, -half_d),
		Vector3(ROOM_WIDTH, ROOM_HEIGHT, WALL_THICKNESS),
		Color(0.75, 0.82, 0.88),
		true
	)
	# Front wall (with gap for visibility)
	_create_box(
		Vector3(-half_w + 2, ROOM_HEIGHT / 2.0, half_d),
		Vector3(4, ROOM_HEIGHT, WALL_THICKNESS),
		Color(0.75, 0.82, 0.88),
		true
	)
	_create_box(
		Vector3(half_w - 2, ROOM_HEIGHT / 2.0, half_d),
		Vector3(4, ROOM_HEIGHT, WALL_THICKNESS),
		Color(0.75, 0.82, 0.88),
		true
	)
	# Left wall
	_create_box(
		Vector3(-half_w, ROOM_HEIGHT / 2.0, 0),
		Vector3(WALL_THICKNESS, ROOM_HEIGHT, ROOM_DEPTH),
		Color(0.82, 0.78, 0.88),
		true
	)
	# Right wall
	_create_box(
		Vector3(half_w, ROOM_HEIGHT / 2.0, 0),
		Vector3(WALL_THICKNESS, ROOM_HEIGHT, ROOM_DEPTH),
		Color(0.82, 0.78, 0.88),
		true
	)

func _add_furniture() -> void:
	# Bed (large box + pillow)
	_create_box(Vector3(-4, 0.4, -5), Vector3(3, 0.8, 2.2), Color(0.3, 0.4, 0.7), true)
	_create_box(Vector3(-4, 0.9, -5.8), Vector3(2.5, 0.4, 0.5), Color(0.9, 0.9, 0.95), false) # Pillow

	# Table
	_create_box(Vector3(3, 0.5, -5), Vector3(2, 1.0, 1.2), Color(0.55, 0.35, 0.2), true)

	# Chairs (2)
	_create_box(Vector3(3, 0.3, -3.5), Vector3(0.7, 0.6, 0.7), Color(0.45, 0.3, 0.15), true)
	_create_box(Vector3(3, 0.7, -3.2), Vector3(0.7, 0.5, 0.1), Color(0.45, 0.3, 0.15), false) # Backrest
	_create_box(Vector3(4.5, 0.3, -5), Vector3(0.7, 0.6, 0.7), Color(0.45, 0.3, 0.15), true)

	# Wardrobe (tall box)
	_create_box(Vector3(-6.5, 1.2, -2), Vector3(1.5, 2.4, 1.0), Color(0.5, 0.35, 0.25), true)

	# Lamp (cylinder + sphere)
	_create_cylinder(Vector3(5, 0.5, -6), 0.1, 1.0, Color(0.3, 0.3, 0.3), true)
	_create_sphere(Vector3(5, 1.2, -6), 0.25, Color(1.0, 0.95, 0.7))

	# Small table / nightstand
	_create_box(Vector3(-5.8, 0.3, -3.5), Vector3(0.8, 0.6, 0.8), Color(0.5, 0.4, 0.3), true)

	# Rug (flat colored floor area)
	_create_box(Vector3(0, 0.01, 0), Vector3(4, 0.02, 3), Color(0.7, 0.2, 0.2), false)

func _add_lighting() -> void:
	# Main room light
	var light = OmniLight3D.new()
	light.position = Vector3(0, 3.5, 0)
	light.light_energy = 1.5
	light.omni_range = 12.0
	light.light_color = Color(1.0, 0.95, 0.85)
	light.shadow_enabled = true
	add_child(light)

	# Secondary fill light
	var fill = OmniLight3D.new()
	fill.position = Vector3(5, 2, 3)
	fill.light_energy = 0.5
	fill.omni_range = 8.0
	fill.light_color = Color(0.8, 0.85, 1.0)
	add_child(fill)

	# Environment
	var env = WorldEnvironment.new()
	var environment = Environment.new()
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.3, 0.3, 0.35)
	environment.ambient_light_energy = 0.5
	env.environment = environment
	add_child(env)

func _create_box(pos: Vector3, size: Vector3, color: Color, with_collision: bool) -> void:
	if with_collision:
		var body = StaticBody3D.new()
		body.position = pos
		body.collision_layer = 1  # Environment
		var mesh_inst = _make_box_mesh(size, color)
		body.add_child(mesh_inst)
		var col = CollisionShape3D.new()
		var shape = BoxShape3D.new()
		shape.size = size
		col.shape = shape
		body.add_child(col)
		add_child(body)
	else:
		var mesh_inst = _make_box_mesh(size, color)
		mesh_inst.position = pos
		add_child(mesh_inst)

func _make_box_mesh(size: Vector3, color: Color) -> MeshInstance3D:
	var mesh_inst = MeshInstance3D.new()
	var box = BoxMesh.new()
	box.size = size
	var mat = StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = 0.85
	box.material = mat
	mesh_inst.mesh = box
	return mesh_inst

func _create_cylinder(pos: Vector3, radius: float, height: float, color: Color, with_collision: bool) -> void:
	var mesh_inst = MeshInstance3D.new()
	var cyl = CylinderMesh.new()
	cyl.top_radius = radius
	cyl.bottom_radius = radius
	cyl.height = height
	var mat = StandardMaterial3D.new()
	mat.albedo_color = color
	cyl.material = mat
	mesh_inst.mesh = cyl
	mesh_inst.position = pos
	add_child(mesh_inst)

func _create_sphere(pos: Vector3, radius: float, color: Color) -> void:
	var mesh_inst = MeshInstance3D.new()
	var sphere = SphereMesh.new()
	sphere.radius = radius
	sphere.height = radius * 2.0
	var mat = StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 1.5
	sphere.material = mat
	mesh_inst.mesh = sphere
	mesh_inst.position = pos
	add_child(mesh_inst)
