extends CanvasLayer

@onready var option_button: OptionButton = $Panel/OptionButton
@onready var settings_panel: Panel = $Panel
@onready var trust_label: Label = $TopHUD/Label
@onready var dialogue_panel: Panel = $DialoguePanel
@onready var dialogue_text: Label = $DialoguePanel/DialogueText
@onready var victory_overlay: Control = $VictoryOverlay
@onready var victory_banner: Panel = $VictoryOverlay/Banner

var dialogue_tween: Tween
var active_timer_id: int = 0
var dialogue_onscreen_y: float = 0.0
var dialogue_offscreen_y: float = 0.0
var is_dialogue_setup: bool = false

func _ready() -> void:
	option_button.selected = Settings.current_input_mode
	option_button.item_selected.connect(_on_item_selected)

	# Slide-in animation for settings drawer
	var final_pos = settings_panel.position
	settings_panel.position.x += 300
	var tween = create_tween()
	tween.tween_property(settings_panel, "position:x", final_pos.x, 1.2).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)

	# Delay coordinate calculations by one frame to allow anchors to resolve
	await get_tree().process_frame
	dialogue_onscreen_y = dialogue_panel.position.y
	dialogue_offscreen_y = get_viewport().size.y + 50.0
	dialogue_panel.position.y = dialogue_offscreen_y
	is_dialogue_setup = true

	# Initial dialogue typing animation
	show_dialogue(dialogue_text.text)

func _on_item_selected(index: int) -> void:
	Settings.set_input_mode(index as Settings.InputMode)

func update_trust(value: int) -> void:
	trust_label.text = "ĐỘ TIN CẬY CỦA NHÀ VUA: %d/100" % clampi(value, 0, 100)

func show_dialogue(text: String) -> void:
	if not is_dialogue_setup:
		dialogue_text.text = text
		return

	if dialogue_tween and dialogue_tween.is_running():
		dialogue_tween.kill()

	dialogue_text.text = text
	dialogue_text.visible_ratio = 0.0
	dialogue_panel.visible = true

	# Generate a new unique ID for this dialogue session
	var current_timer_id = randi()
	active_timer_id = current_timer_id

	# Animate dialogue panel sliding up and text typing
	var slide_tween = create_tween()
	slide_tween.tween_property(dialogue_panel, "position:y", dialogue_onscreen_y, 0.4).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)

	dialogue_tween = create_tween()
	dialogue_tween.tween_property(dialogue_text, "visible_ratio", 1.0, 1.5).set_trans(Tween.TRANS_LINEAR)

	# Start the 5-second auto-hide sequence
	_start_hide_timer(current_timer_id)

func _start_hide_timer(timer_id: int) -> void:
	if not is_inside_tree():
		return

	var tree = get_tree()
	if not tree:
		return

	await tree.create_timer(5.0).timeout
	if not is_inside_tree():
		return

	# If no new dialogue has been triggered, slide down and hide the panel
	if active_timer_id == timer_id:
		var slide_tween = create_tween()
		slide_tween.tween_property(dialogue_panel, "position:y", dialogue_offscreen_y, 0.6).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
		slide_tween.tween_callback(func(): dialogue_panel.visible = false)

func trigger_victory() -> void:
	victory_overlay.visible = true
	victory_banner.scale = Vector2.ZERO
	victory_banner.pivot_offset = victory_banner.size / 2.0

	var tween = create_tween()
	tween.tween_property(victory_banner, "scale", Vector2.ONE, 1.0).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
