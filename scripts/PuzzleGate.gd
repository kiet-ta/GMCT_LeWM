extends StaticBody3D

@onready var display_label: Label3D = $DisplayLabel
@onready var slots_container: Node3D = $SlotsContainer

var is_open: bool = false

func update_display(expression: String) -> void:
	display_label.text = expression

func sink_gate(duration: float = 2.0) -> Signal:
	EventLogger.log_event("gate_sinking")
	var tween = create_tween()
	tween.tween_property(self, "global_position:y", -4.0, duration).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	return tween.finished

func rise_gate(duration: float = 2.0) -> Signal:
	EventLogger.log_event("gate_rising")
	var tween = create_tween()
	tween.tween_property(self, "global_position:y", 0.0, duration).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	return tween.finished

func open_gate() -> void:
	if is_open: return
	is_open = true
	EventLogger.log_event("gate_opened")
	sink_gate(2.0)

