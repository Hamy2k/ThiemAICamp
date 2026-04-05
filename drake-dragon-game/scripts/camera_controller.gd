## CameraController - Third-person camera following player.
## Smooth follow with slight tilt for better room visibility.
extends Camera3D

@export var target_path: NodePath
@export var offset: Vector3 = Vector3(0, 8, 6)
@export var look_offset: Vector3 = Vector3(0, 1, 0)
@export var smooth_speed: float = 5.0

var target: Node3D = null

func _ready() -> void:
	if target_path:
		target = get_node(target_path)
	else:
		await get_tree().create_timer(0.1).timeout
		target = get_tree().get_first_node_in_group("player")

func _process(delta: float) -> void:
	if not target or not is_instance_valid(target):
		return

	# Smooth follow
	var desired_pos = target.global_position + offset
	global_position = global_position.lerp(desired_pos, delta * smooth_speed)

	# Look at player with offset
	look_at(target.global_position + look_offset, Vector3.UP)
