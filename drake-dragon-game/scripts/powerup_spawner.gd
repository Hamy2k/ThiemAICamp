## PowerUpSpawner - Spawns power-ups at random intervals in the room.
extends Node3D

@export var spawn_interval_min: float = 20.0
@export var spawn_interval_max: float = 40.0

var timer: float = 15.0  # First spawn after 15s
var room_bounds: AABB = AABB(Vector3(-5, 0, -5), Vector3(10, 0, 10))

func _process(delta: float) -> void:
	if GameManager.is_game_over:
		return

	timer -= delta
	if timer <= 0:
		_spawn_powerup()
		timer = randf_range(spawn_interval_min, spawn_interval_max)

func _spawn_powerup() -> void:
	var powerup = Area3D.new()
	powerup.name = "PowerUp"

	# Collision
	var col = CollisionShape3D.new()
	var shape = SphereShape3D.new()
	shape.radius = 0.5
	col.shape = shape
	powerup.add_child(col)
	col.owner = powerup

	# Mesh (glowing box)
	var mesh = MeshInstance3D.new()
	mesh.name = "MeshInstance3D"
	var box = BoxMesh.new()
	box.size = Vector3(0.4, 0.4, 0.4)
	mesh.mesh = box
	powerup.add_child(mesh)
	mesh.owner = powerup

	# Attach script
	powerup.set_script(load("res://scripts/powerup.gd"))

	# Random type
	if randf() < 0.5:
		powerup.set("powerup_type", 0)  # SHIELD
	else:
		powerup.set("powerup_type", 1)  # STRONG_RACKET

	# Random position
	powerup.position = Vector3(
		randf_range(room_bounds.position.x, room_bounds.end.x),
		1.2,
		randf_range(room_bounds.position.z, room_bounds.end.z)
	)

	# Collision layer for player pickup
	powerup.collision_layer = 0
	powerup.collision_mask = 2  # Player layer

	add_child(powerup)
