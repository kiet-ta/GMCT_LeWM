extends CharacterBody3D

@export var target_player: Node3D

@onready var speech_bubble: Label3D = $SpeechBubble
var float_time: float = 0.0

func _process(delta: float) -> void:
	float_time += delta
	# Floating animation
	$MeshInstance3D.position.y = 0.4 + sin(float_time * 2.0) * 0.1
	
	if target_player:
		# Follow player smoothly
		var target_pos = target_player.global_position + Vector3(1.5, 1.5, -1.5)
		global_position = global_position.lerp(target_pos, delta * 3.0)
		look_at(target_player.global_position + Vector3(0, 1, 0), Vector3.UP)

func update_feedback(state: String) -> void:
	var message = ""
	match state:
		"not_enough_info":
			message = "Hmm, I need more numbers!"
		"likely_correct_path":
			message = "Looking good!"
		"wrong_direction":
			message = "Oops, try again!"
		"near_correct":
			message = "So close!"
		"correct":
			message = "You did it!"
		_:
			message = "Let's solve!"
			
	speech_bubble.text = message
	EventLogger.log_event("buddy_speech", {"state": state, "message": message})
