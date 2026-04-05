## SceneBuilder - Auto-constructs the entire game scene procedurally.
## Run this script once to generate the scene, or use it as the main scene.
## This avoids needing a complex .tscn file - everything is built in code.
extends Node3D

func _ready() -> void:
	name = "Main"

	_build_player()
	_build_room()
	_build_camera()
	_build_spawners()
	_build_ui()

	print("Drake Dragon: Mosquito Hunt - Scene built!")

func _build_player() -> void:
	var player = CharacterBody3D.new()
	player.name = "Player"
	player.add_to_group("player")
	player.position = Vector3(0, 0, 0)
	player.collision_layer = 2  # Player layer
	player.collision_mask = 1 | 4  # Environment + Mosquitoes

	# Player collision
	var col = CollisionShape3D.new()
	var shape = CapsuleShape3D.new()
	shape.radius = 0.4
	shape.height = 1.6
	col.shape = shape
	col.position.y = 0.8
	player.add_child(col)

	# Model container
	var model = Node3D.new()
	model.name = "Model"
	player.add_child(model)

	# Body mesh (cute rounded character)
	var body_mesh = MeshInstance3D.new()
	var capsule = CapsuleMesh.new()
	capsule.radius = 0.35
	capsule.height = 1.2
	var body_mat = StandardMaterial3D.new()
	body_mat.albedo_color = Color(0.95, 0.8, 0.65)  # Skin color
	body_mat.roughness = 0.7
	capsule.material = body_mat
	body_mesh.mesh = capsule
	body_mesh.position.y = 0.7
	model.add_child(body_mesh)

	# Head (sphere on top)
	var head = MeshInstance3D.new()
	var head_sphere = SphereMesh.new()
	head_sphere.radius = 0.3
	head_sphere.height = 0.6
	head_sphere.material = body_mat
	head.mesh = head_sphere
	head.position.y = 1.5
	model.add_child(head)

	# Eyes (two small dark spheres)
	for side in [-1, 1]:
		var eye = MeshInstance3D.new()
		var eye_mesh = SphereMesh.new()
		eye_mesh.radius = 0.06
		eye_mesh.height = 0.12
		var eye_mat = StandardMaterial3D.new()
		eye_mat.albedo_color = Color(0.1, 0.1, 0.1)
		eye_mesh.material = eye_mat
		eye.mesh = eye_mesh
		eye.position = Vector3(side * 0.12, 1.55, 0.25)
		model.add_child(eye)

	# Mouth (small red sphere for comical look)
	var mouth = MeshInstance3D.new()
	var mouth_mesh = SphereMesh.new()
	mouth_mesh.radius = 0.08
	mouth_mesh.height = 0.06
	var mouth_mat = StandardMaterial3D.new()
	mouth_mat.albedo_color = Color(0.9, 0.3, 0.3)
	mouth_mesh.material = mouth_mat
	mouth.mesh = mouth_mesh
	mouth.position = Vector3(0, 1.42, 0.27)
	model.add_child(mouth)

	# Racket pivot + area
	var racket_pivot = Node3D.new()
	racket_pivot.name = "RacketPivot"
	racket_pivot.position = Vector3(0.5, 1.0, 0.3)
	model.add_child(racket_pivot)

	# Racket handle
	var handle = MeshInstance3D.new()
	var handle_mesh = CylinderMesh.new()
	handle_mesh.top_radius = 0.03
	handle_mesh.bottom_radius = 0.03
	handle_mesh.height = 0.6
	var handle_mat = StandardMaterial3D.new()
	handle_mat.albedo_color = Color(0.3, 0.3, 0.3)
	handle_mesh.material = handle_mat
	handle.mesh = handle_mesh
	handle.position.y = -0.1
	racket_pivot.add_child(handle)

	# Racket head (flat cylinder = the electrified part)
	var racket_head = MeshInstance3D.new()
	var rh_mesh = CylinderMesh.new()
	rh_mesh.top_radius = 0.25
	rh_mesh.bottom_radius = 0.25
	rh_mesh.height = 0.03
	var rh_mat = StandardMaterial3D.new()
	rh_mat.albedo_color = Color(0.2, 0.6, 1.0)
	rh_mat.emission_enabled = true
	rh_mat.emission = Color(0.1, 0.3, 0.8)
	rh_mat.emission_energy_multiplier = 0.5
	rh_mesh.material = rh_mat
	racket_head.mesh = rh_mesh
	racket_head.position.y = 0.35
	racket_head.rotation_degrees.x = 90
	racket_pivot.add_child(racket_head)

	# Racket hit area
	var racket_area = Area3D.new()
	racket_area.name = "RacketArea"
	racket_area.collision_layer = 8  # Racket layer
	racket_area.collision_mask = 4   # Mosquito layer
	racket_area.monitoring = false
	var ra_col = CollisionShape3D.new()
	var ra_shape = SphereShape3D.new()
	ra_shape.radius = 0.8
	ra_col.shape = ra_shape
	ra_col.position.y = 0.3
	racket_area.add_child(ra_col)
	racket_pivot.add_child(racket_area)

	# Zap particles
	var zap = GPUParticles3D.new()
	zap.name = "ZapParticles"
	zap.emitting = false
	zap.one_shot = true
	zap.amount = 20
	zap.lifetime = 0.3
	zap.explosiveness = 1.0
	var zap_mat = ParticleProcessMaterial.new()
	zap_mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	zap_mat.emission_sphere_radius = 0.3
	zap_mat.direction = Vector3(0, 1, 0)
	zap_mat.spread = 180.0
	zap_mat.initial_velocity_min = 2.0
	zap_mat.initial_velocity_max = 5.0
	zap_mat.gravity = Vector3(0, -5, 0)
	zap_mat.scale_min = 0.05
	zap_mat.scale_max = 0.15
	zap_mat.color = Color(0.3, 0.7, 1.0)
	zap.process_material = zap_mat
	# Simple sphere mesh for particles
	var spark_mesh = SphereMesh.new()
	spark_mesh.radius = 0.05
	spark_mesh.height = 0.1
	var spark_mat = StandardMaterial3D.new()
	spark_mat.albedo_color = Color(0.5, 0.8, 1.0)
	spark_mat.emission_enabled = true
	spark_mat.emission = Color(0.3, 0.6, 1.0)
	spark_mat.emission_energy_multiplier = 3.0
	spark_mesh.material = spark_mat
	zap.draw_pass_1 = spark_mesh
	racket_pivot.add_child(zap)

	# Bite bumps container
	var bumps = Node3D.new()
	bumps.name = "BiteBumps"
	model.add_child(bumps)

	# AnimationPlayer (placeholder)
	var anim = AnimationPlayer.new()
	anim.name = "AnimationPlayer"
	player.add_child(anim)

	# Attach player script
	player.set_script(load("res://scripts/player.gd"))

	add_child(player)

func _build_room() -> void:
	var room = Node3D.new()
	room.name = "Room"
	room.set_script(load("res://scripts/room_builder.gd"))
	add_child(room)

func _build_camera() -> void:
	var camera = Camera3D.new()
	camera.name = "Camera"
	camera.set_script(load("res://scripts/camera_controller.gd"))
	camera.position = Vector3(0, 8, 6)
	camera.current = true
	add_child(camera)

func _build_spawners() -> void:
	var mosquito_spawner = Node3D.new()
	mosquito_spawner.name = "MosquitoSpawner"
	mosquito_spawner.set_script(load("res://scripts/mosquito_spawner.gd"))
	add_child(mosquito_spawner)

	var powerup_spawner = Node3D.new()
	powerup_spawner.name = "PowerUpSpawner"
	powerup_spawner.set_script(load("res://scripts/powerup_spawner.gd"))
	add_child(powerup_spawner)

func _build_ui() -> void:
	var ui = CanvasLayer.new()
	ui.name = "UI"
	ui.set_script(load("res://scripts/game_ui.gd"))

	# HUD
	var hud = Control.new()
	hud.name = "HUD"
	hud.set_anchors_preset(Control.PRESET_FULL_RECT)

	# Bite counter
	var bite_label = Label.new()
	bite_label.name = "BiteLabel"
	bite_label.text = "Bites: 0 / 100"
	bite_label.position = Vector2(20, 20)
	bite_label.add_theme_font_size_override("font_size", 28)
	hud.add_child(bite_label)

	# Score
	var score_label = Label.new()
	score_label.name = "ScoreLabel"
	score_label.text = "Score: 0"
	score_label.position = Vector2(20, 60)
	score_label.add_theme_font_size_override("font_size", 28)
	hud.add_child(score_label)

	# Health bar
	var health = ProgressBar.new()
	health.name = "HealthBar"
	health.position = Vector2(20, 100)
	health.size = Vector2(300, 30)
	health.value = 100
	health.show_percentage = false
	var hb_style = StyleBoxFlat.new()
	hb_style.bg_color = Color(0.2, 0.8, 0.2)
	hb_style.corner_radius_top_left = 8
	hb_style.corner_radius_top_right = 8
	hb_style.corner_radius_bottom_left = 8
	hb_style.corner_radius_bottom_right = 8
	health.add_theme_stylebox_override("fill", hb_style)
	hud.add_child(health)

	# Combo label
	var combo = Label.new()
	combo.name = "ComboLabel"
	combo.text = ""
	combo.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	combo.position = Vector2(400, 20)
	combo.add_theme_font_size_override("font_size", 36)
	combo.visible = false
	hud.add_child(combo)

	# PowerUp label
	var powerup = Label.new()
	powerup.name = "PowerUpLabel"
	powerup.text = ""
	powerup.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	powerup.position = Vector2(400, 70)
	powerup.add_theme_font_size_override("font_size", 24)
	powerup.visible = false
	hud.add_child(powerup)

	# Swing button (bottom right)
	var swing_btn = Button.new()
	swing_btn.name = "SwingButton"
	swing_btn.text = "ZAP!"
	swing_btn.position = Vector2(850, 1600)
	swing_btn.size = Vector2(180, 180)
	swing_btn.add_theme_font_size_override("font_size", 32)
	var btn_style = StyleBoxFlat.new()
	btn_style.bg_color = Color(0.2, 0.5, 1.0, 0.8)
	btn_style.corner_radius_top_left = 90
	btn_style.corner_radius_top_right = 90
	btn_style.corner_radius_bottom_left = 90
	btn_style.corner_radius_bottom_right = 90
	swing_btn.add_theme_stylebox_override("normal", btn_style)
	var btn_hover = btn_style.duplicate()
	btn_hover.bg_color = Color(0.3, 0.6, 1.0, 0.9)
	swing_btn.add_theme_stylebox_override("hover", btn_hover)
	var btn_press = btn_style.duplicate()
	btn_press.bg_color = Color(0.1, 0.3, 0.8, 1.0)
	swing_btn.add_theme_stylebox_override("pressed", btn_press)
	hud.add_child(swing_btn)

	ui.add_child(hud)

	# Virtual Joystick
	var joystick = Control.new()
	joystick.name = "VirtualJoystick"
	joystick.set_script(load("res://scripts/virtual_joystick.gd"))
	joystick.set_anchors_preset(Control.PRESET_FULL_RECT)

	var js_base = TextureRect.new()
	js_base.name = "Base"
	js_base.position = Vector2(50, 1550)
	js_base.size = Vector2(200, 200)
	joystick.add_child(js_base)

	var js_knob = TextureRect.new()
	js_knob.name = "Knob"
	js_knob.size = Vector2(80, 80)
	js_knob.position = Vector2(60, 60)  # Centered in base
	js_base.add_child(js_knob)

	ui.add_child(joystick)

	# Game Over Panel
	var go_panel = PanelContainer.new()
	go_panel.name = "GameOverPanel"
	go_panel.set_anchors_preset(Control.PRESET_CENTER)
	go_panel.position = Vector2(240, 700)
	go_panel.size = Vector2(600, 400)
	go_panel.visible = false
	var go_style = StyleBoxFlat.new()
	go_style.bg_color = Color(0.1, 0.1, 0.15, 0.9)
	go_style.corner_radius_top_left = 20
	go_style.corner_radius_top_right = 20
	go_style.corner_radius_bottom_left = 20
	go_style.corner_radius_bottom_right = 20
	go_style.border_width_top = 3
	go_style.border_width_bottom = 3
	go_style.border_width_left = 3
	go_style.border_width_right = 3
	go_style.border_color = Color(0.8, 0.2, 0.2)
	go_panel.add_theme_stylebox_override("panel", go_style)

	var vbox = VBoxContainer.new()
	vbox.name = "VBox"
	vbox.alignment = BoxContainer.ALIGNMENT_CENTER

	var go_title = Label.new()
	go_title.text = "GAME OVER!"
	go_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	go_title.add_theme_font_size_override("font_size", 48)
	go_title.add_theme_color_override("font_color", Color.RED)
	vbox.add_child(go_title)

	var spacer = Control.new()
	spacer.custom_minimum_size.y = 20
	vbox.add_child(spacer)

	var final_score = Label.new()
	final_score.name = "FinalScoreLabel"
	final_score.text = "Score: 0"
	final_score.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	final_score.add_theme_font_size_override("font_size", 28)
	vbox.add_child(final_score)

	var spacer2 = Control.new()
	spacer2.custom_minimum_size.y = 30
	vbox.add_child(spacer2)

	var restart = Button.new()
	restart.name = "RestartButton"
	restart.text = "PLAY AGAIN"
	restart.custom_minimum_size = Vector2(250, 60)
	restart.add_theme_font_size_override("font_size", 28)
	var restart_style = StyleBoxFlat.new()
	restart_style.bg_color = Color(0.2, 0.7, 0.3)
	restart_style.corner_radius_top_left = 15
	restart_style.corner_radius_top_right = 15
	restart_style.corner_radius_bottom_left = 15
	restart_style.corner_radius_bottom_right = 15
	restart.add_theme_stylebox_override("normal", restart_style)
	vbox.add_child(restart)

	go_panel.add_child(vbox)
	ui.add_child(go_panel)

	add_child(ui)

	# Connect joystick to player after scene is ready
	await get_tree().create_timer(0.2).timeout
	var player_node = get_tree().get_first_node_in_group("player")
	if player_node and joystick.has_signal("joystick_input"):
		joystick.joystick_input.connect(player_node.set_move_input)
