extends Node

@export var puzzle_gate: Node3D
@export var ai_buddy: Node3D
@export var puzzle_paths: Array[String] = ["res://data/puzzle_1.json", "res://data/puzzle_2.json"]

var current_puzzle_index: int = 0
var trust_points: int = 0
var max_trust: int = 100

var expected_answer: String = ""
var current_input: Array = []
var num_slots: int = 0

func _ready() -> void:
	_load_puzzle()
	_scatter_blocks()
	
func _scatter_blocks() -> void:
	var block_scene = preload("res://scenes/NumberBlock.tscn")
	var blocks_container = get_node("../Blocks")
	if not block_scene or not blocks_container: return
	
	for child in blocks_container.get_children():
		child.queue_free()
		
	for i in range(10):
		var block = block_scene.instantiate()
		block.value = i
		var rand_x = randf_range(-15, 15)
		var rand_z = randf_range(-5, 15)
		block.position = Vector3(rand_x, 2, rand_z)
		blocks_container.add_child(block)

func _load_puzzle() -> void:
	if current_puzzle_index >= puzzle_paths.size():
		return
		
	var path = puzzle_paths[current_puzzle_index]
	if not FileAccess.file_exists(path):
		print("Puzzle file not found: ", path)
		return
		
	var file = FileAccess.open(path, FileAccess.READ)
	var content = file.get_as_text()
	var data = JSON.parse_string(content)
	
	if data and typeof(data) == TYPE_DICTIONARY:
		expected_answer = data.get("expected_answer", "")
		var expression = data.get("expression", "")
		num_slots = data.get("slots", 0)
		
		current_input.resize(num_slots)
		for i in range(num_slots):
			current_input[i] = -1 # -1 means empty
		
		if puzzle_gate:
			puzzle_gate.update_display(expression)
			_spawn_slots()

func _spawn_slots() -> void:
	var slot_scene = preload("res://scenes/AnswerSlot.tscn")
	var container = puzzle_gate.get_node("SlotsContainer")
	if container and slot_scene:
		# Clear existing
		for child in container.get_children():
			child.queue_free()
			
		for i in range(num_slots):
			var slot = slot_scene.instantiate()
			slot.slot_index = i
			slot.position = Vector3(i * 1.5 - (num_slots * 1.5) / 2.0 + 0.75, 0, 0)
			container.add_child(slot)
			slot.block_placed.connect(_on_block_placed)
			slot.block_removed.connect(_on_block_removed)

func _on_block_placed(index: int, value: int) -> void:
	current_input[index] = value
	_evaluate_state()

func _on_block_removed(index: int) -> void:
	current_input[index] = -1
	_evaluate_state()

func _evaluate_state() -> void:
	# Build string
	var input_str = ""
	for val in current_input:
		if val == -1:
			input_str += "_"
		else:
			input_str += str(val)
	
	var state = "not_enough_info"
	var is_full = not "_" in input_str
	
	if is_full:
		if input_str == expected_answer:
			state = "correct"
		else:
			var match_count = 0
			for i in range(min(input_str.length(), expected_answer.length())):
				if input_str[i] == expected_answer[i]:
					match_count += 1
			if match_count >= expected_answer.length() - 1 and match_count > 0:
				state = "near_correct"
			else:
				state = "wrong_direction"
	else:
		var matching_so_far = true
		var has_input = false
		for i in range(input_str.length()):
			if input_str[i] != "_":
				has_input = true
				if i >= expected_answer.length() or input_str[i] != expected_answer[i]:
					matching_so_far = false
					break
		
		if not has_input:
			state = "not_enough_info"
		elif matching_so_far:
			state = "likely_correct_path"
		else:
			state = "wrong_direction"

	if ai_buddy and ai_buddy.has_method("update_feedback"):
		ai_buddy.update_feedback(state)
		
	if state == "correct":
		trust_points += 50
		var ui = get_tree().current_scene.get_node_or_null("SettingsUI")
		if ui and ui.has_method("update_trust"):
			ui.update_trust(trust_points)
			
		if trust_points >= max_trust:
			if ui and ui.has_method("trigger_victory"):
				ui.trigger_victory()
			if puzzle_gate and puzzle_gate.has_method("open_gate"):
				puzzle_gate.open_gate()
		else:
			_transition_to_next_puzzle()

func _transition_to_next_puzzle() -> void:
	# Let player drop any grabbed block
	var player = get_node_or_null("../Player")
	if player and player.has_method("drop_block"):
		player.drop_block()
		
	# Sink the gate
	if puzzle_gate and puzzle_gate.has_method("sink_gate"):
		await puzzle_gate.sink_gate(2.0)
		
	# Increment index and check
	current_puzzle_index += 1
	if current_puzzle_index < puzzle_paths.size():
		_load_puzzle()
		_scatter_blocks()
		
		# Show transition dialogue via Buddy
		if ai_buddy and ai_buddy.has_method("update_feedback"):
			ai_buddy.update_feedback("not_enough_info") # reset buddy message
			
		# Rise the gate with the new puzzle
		if puzzle_gate and puzzle_gate.has_method("rise_gate"):
			await puzzle_gate.rise_gate(2.0)

