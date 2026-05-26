extends StaticBody3D

@onready var display_label: Label3D = $DisplayLabel
@onready var slots_container: Node3D = $SlotsContainer

var is_open: bool = false

func update_display(expression: String) -> void:
	display_label.text = expression

func open_gate() -> void:
	if is_open: return
	is_open = true
	
	EventLogger.log_event("gate_opened")
	
	# Gentle opening animation
	var tween = create_tween()
	tween.tween_property(self, "position:y", position.y - 4.0, 2.0).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tween.tween_callback(func(): queue_free()) # Or just stay lowered
