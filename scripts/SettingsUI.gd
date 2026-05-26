extends CanvasLayer

@onready var option_button: OptionButton = $Panel/OptionButton

func _ready() -> void:
	option_button.selected = Settings.current_input_mode
	option_button.item_selected.connect(_on_item_selected)

func _on_item_selected(index: int) -> void:
	Settings.set_input_mode(index as Settings.InputMode)
