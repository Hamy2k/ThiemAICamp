## VirtualJoystick - Touch joystick for mobile movement.
## Drag to move, release to stop. Works with mouse for testing.
extends Control

signal joystick_input(direction: Vector2)

@export var max_distance: float = 80.0
@export var deadzone: float = 10.0

@onready var base: TextureRect = $Base
@onready var knob: TextureRect = $Base/Knob

var is_pressed: bool = false
var touch_index: int = -1
var center: Vector2 = Vector2.ZERO

func _ready() -> void:
	center = base.size / 2.0
	knob.position = center - knob.size / 2.0

	# Create placeholder textures if none assigned
	if not base.texture:
		_create_placeholder_textures()

func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		var touch = event as InputEventScreenTouch
		if touch.pressed and _is_in_joystick_area(touch.position):
			is_pressed = true
			touch_index = touch.index
			_update_knob(touch.position)
		elif not touch.pressed and touch.index == touch_index:
			_reset()

	elif event is InputEventScreenDrag:
		var drag = event as InputEventScreenDrag
		if drag.index == touch_index and is_pressed:
			_update_knob(drag.position)

	# Mouse support for desktop testing
	elif event is InputEventMouseButton:
		var mouse = event as InputEventMouseButton
		if mouse.pressed and mouse.button_index == MOUSE_BUTTON_LEFT and _is_in_joystick_area(mouse.position):
			is_pressed = true
			_update_knob(mouse.position)
		elif not mouse.pressed:
			_reset()

	elif event is InputEventMouseMotion and is_pressed:
		_update_knob((event as InputEventMouseMotion).position)

func _update_knob(touch_pos: Vector2) -> void:
	var base_center = base.global_position + center
	var direction = touch_pos - base_center
	var distance = direction.length()

	if distance > max_distance:
		direction = direction.normalized() * max_distance

	knob.global_position = base_center + direction - knob.size / 2.0

	# Emit normalized direction
	if distance > deadzone:
		var normalized = direction / max_distance
		joystick_input.emit(normalized)
	else:
		joystick_input.emit(Vector2.ZERO)

func _reset() -> void:
	is_pressed = false
	touch_index = -1
	knob.position = center - knob.size / 2.0
	joystick_input.emit(Vector2.ZERO)

func _is_in_joystick_area(pos: Vector2) -> bool:
	var rect = base.get_global_rect()
	rect = rect.grow(30)  # Slightly larger touch area
	return rect.has_point(pos)

func _create_placeholder_textures() -> void:
	# Create circular textures procedurally
	var base_img = Image.create(160, 160, false, Image.FORMAT_RGBA8)
	var knob_img = Image.create(60, 60, false, Image.FORMAT_RGBA8)

	# Draw base circle
	var bc = Vector2(80, 80)
	for x in range(160):
		for y in range(160):
			var dist = Vector2(x, y).distance_to(bc)
			if dist < 78:
				base_img.set_pixel(x, y, Color(1, 1, 1, 0.15))
			elif dist < 80:
				base_img.set_pixel(x, y, Color(1, 1, 1, 0.4))

	# Draw knob circle
	var kc = Vector2(30, 30)
	for x in range(60):
		for y in range(60):
			var dist = Vector2(x, y).distance_to(kc)
			if dist < 28:
				knob_img.set_pixel(x, y, Color(1, 1, 1, 0.6))
			elif dist < 30:
				knob_img.set_pixel(x, y, Color(1, 1, 1, 0.8))

	var base_tex = ImageTexture.create_from_image(base_img)
	var knob_tex = ImageTexture.create_from_image(knob_img)
	base.texture = base_tex
	knob.texture = knob_tex
