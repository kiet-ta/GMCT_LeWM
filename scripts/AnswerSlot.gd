extends Area3D

signal block_placed(slot_index: int, value: int)
signal block_removed(slot_index: int)

@export var slot_index: int = 0
var current_block: RigidBody3D = null

func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)

func _on_body_entered(body: Node3D) -> void:
	if body.is_in_group("number_block") and current_block == null:
		# If a block enters, snap it and register
		# We should probably only do this if it's dropped, but for MVP, entering is enough or we check if grabbed.
		# Let's assume the player drops it, and it enters the slot.
		current_block = body
		# Snap to center
		body.global_position = global_position
		body.linear_velocity = Vector3.ZERO
		body.angular_velocity = Vector3.ZERO
		
		if body.has_method("get_value"):
			block_placed.emit(slot_index, body.value)
		else:
			# fallback if no get_value but has property
			block_placed.emit(slot_index, body.get("value"))
			
		EventLogger.log_event("block_placed", {"slot_index": slot_index, "block_value": body.get("value")})

func _on_body_exited(body: Node3D) -> void:
	if body == current_block:
		current_block = null
		block_removed.emit(slot_index)
		EventLogger.log_event("block_removed", {"slot_index": slot_index})
