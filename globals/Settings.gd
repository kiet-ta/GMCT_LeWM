extends Node

enum InputMode {
	CLICK_TO_PICK_UP,
	HOLD_TO_GRAB
}

var current_input_mode: InputMode = InputMode.CLICK_TO_PICK_UP

signal input_mode_changed(new_mode: InputMode)

func set_input_mode(mode: InputMode) -> void:
	if current_input_mode != mode:
		current_input_mode = mode
		input_mode_changed.emit(mode)
