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
			message = "Tráng sĩ còn thiếu vài chữ số. Hãy đặt đủ khối số vào ô đáp án."
		"likely_correct_path":
			message = "Đường tính đã thuận. Tráng sĩ cứ theo phép ấy mà tiến."
		"wrong_direction":
			message = "Phép này chưa hợp. Tráng sĩ thử xét lại hàng chục, hàng đơn vị."
		"near_correct":
			message = "Gần đúng rồi. Chỉ còn một chữ số chưa thuận."
		"correct":
			message = "Khéo lắm, tráng sĩ! Cổng câu đố đã mở đường."
		_:
			message = "Hãy cùng ta giải câu đố để chứng minh lòng trung thực của chàng."

	speech_bubble.text = message
	EventLogger.log_event("buddy_speech", {"state": state, "message": message})

	# Update the bottom dialogue UI in SettingsUI
	var ui = get_tree().current_scene.get_node_or_null("SettingsUI")
	if ui and ui.has_method("show_dialogue"):
		ui.show_dialogue(message)
