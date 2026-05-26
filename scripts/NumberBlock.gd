extends RigidBody3D

@export var value: int = 0 :
	set(new_val):
		value = new_val
		_update_label()

@onready var label: Label3D = $Label3D

func _ready() -> void:
	_update_label()

func _update_label() -> void:
	if label:
		label.text = str(value)

func interact(player: Node3D) -> void:
	# Called when player clicks on the block
	pass
