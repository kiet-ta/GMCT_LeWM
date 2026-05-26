extends CharacterBody3D

const SPEED = 5.0
const JUMP_VELOCITY = 4.5

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")

@onready var raycast: RayCast3D = $CameraPivot/Camera3D/RayCast3D
@onready var grab_position: Marker3D = $GrabPosition

var grabbed_block: RigidBody3D = null

func _ready() -> void:
	if not InputMap.has_action("move_forward"):
		InputMap.add_action("move_forward")
		var w = InputEventKey.new()
		w.physical_keycode = KEY_W
		InputMap.action_add_event("move_forward", w)
		
		InputMap.add_action("move_backward")
		var s = InputEventKey.new()
		s.physical_keycode = KEY_S
		InputMap.action_add_event("move_backward", s)
		
		InputMap.add_action("move_left")
		var a = InputEventKey.new()
		a.physical_keycode = KEY_A
		InputMap.action_add_event("move_left", a)
		
		InputMap.add_action("move_right")
		var d = InputEventKey.new()
		d.physical_keycode = KEY_D
		InputMap.action_add_event("move_right", d)

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= gravity * delta

	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Use the custom input map for WASD or arrow keys fallback
	var input_x := Input.get_axis("move_left", "move_right")
	if input_x == 0: input_x = Input.get_axis("ui_left", "ui_right")
	
	var input_y := Input.get_axis("move_forward", "move_backward")
	if input_y == 0: input_y = Input.get_axis("ui_up", "ui_down")
	
	var input_dir = Vector2(input_x, input_y).normalized()
	
	# Camera relative movement
	var cam_basis = $CameraPivot.global_transform.basis
	var forward = -cam_basis.z
	forward.y = 0
	forward = forward.normalized()
	
	var right = cam_basis.x
	right.y = 0
	right = right.normalized()
	
	var direction = (right * input_dir.x + forward * -input_dir.y).normalized()
	
	if direction:
		velocity.x = direction.x * SPEED
		velocity.z = direction.z * SPEED
		
		# Rotate mesh smoothly
		var target_angle = atan2(-direction.x, -direction.z)
		$MeshInstance3D.rotation.y = lerp_angle($MeshInstance3D.rotation.y, target_angle, 12.0 * delta)
		
		# Move grab position to be in front of the player
		$GrabPosition.position = Vector3(direction.x * 1.5, 1.0, direction.z * 1.5)
	else:
		velocity.x = move_toward(velocity.x, 0, SPEED)
		velocity.z = move_toward(velocity.z, 0, SPEED)

	move_and_slide()
	
	if grabbed_block:
		grabbed_block.global_position = grabbed_block.global_position.lerp(grab_position.global_position, 15.0 * delta)
		grabbed_block.linear_velocity = Vector3.ZERO

var was_mouse_pressed = false
var mouse_sensitivity: float = 0.005

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
		$CameraPivot.rotation.y -= event.relative.x * mouse_sensitivity
		$CameraPivot.rotation.x -= event.relative.y * mouse_sensitivity
		$CameraPivot.rotation.x = clamp($CameraPivot.rotation.x, -1.2, 0.2)

func _process(delta: float) -> void:
	var is_mouse_pressed = Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
	var mouse_just_pressed = is_mouse_pressed and not was_mouse_pressed
	var mouse_just_released = not is_mouse_pressed and was_mouse_pressed
	
	if Settings.current_input_mode == Settings.InputMode.CLICK_TO_PICK_UP:
		if mouse_just_pressed:
			if grabbed_block:
				drop_block()
			else:
				try_grab()
	elif Settings.current_input_mode == Settings.InputMode.HOLD_TO_GRAB:
		if mouse_just_pressed:
			try_grab()
		elif mouse_just_released and grabbed_block:
			drop_block()
			
	was_mouse_pressed = is_mouse_pressed

func try_grab() -> void:
	# Update raycast based on mouse position
	var viewport = get_viewport()
	var mouse_pos = viewport.get_mouse_position()
	var camera = $CameraPivot/Camera3D
	var from = camera.project_ray_origin(mouse_pos)
	var to = from + camera.project_ray_normal(mouse_pos) * 100.0
	
	var space_state = get_world_3d().direct_space_state
	var query = PhysicsRayQueryParameters3D.create(from, to, 2) # mask 2 is number block
	var result = space_state.intersect_ray(query)
	
	if result and result.collider is RigidBody3D and result.collider.is_in_group("number_block"):
		grabbed_block = result.collider
		grabbed_block.freeze = true
		grabbed_block.collision_layer = 0
		grabbed_block.collision_mask = 0
		if grabbed_block.has_method("get"):
			EventLogger.log_event("block_grabbed", {"block_value": grabbed_block.get("value")})

func drop_block() -> void:
	if grabbed_block:
		if grabbed_block.has_method("get"):
			EventLogger.log_event("block_dropped", {"block_value": grabbed_block.get("value")})
		grabbed_block.freeze = false
		grabbed_block.collision_layer = 2
		grabbed_block.collision_mask = 3
		grabbed_block.apply_central_impulse(Vector3.ZERO) # wake it up
		grabbed_block = null
