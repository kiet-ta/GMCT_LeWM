extends OmniLight3D

@export var min_energy: float = 2.5
@export var max_energy: float = 4.5
@export var flicker_speed: float = 15.0

var time: float = 0.0
var base_energy: float = 3.5

func _ready() -> void:
	base_energy = light_energy
	# Seed randomness
	randomize()
	time = randf() * 100.0

func _process(delta: float) -> void:
	time += delta * flicker_speed
	# Combine multiple sine waves for pseudo-noise flickering
	var flicker = sin(time) * 0.4 + cos(time * 2.3) * 0.3 + sin(time * 5.7) * 0.15
	light_energy = clamp(base_energy + flicker, min_energy, max_energy)
