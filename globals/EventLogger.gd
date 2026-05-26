extends Node

var events_log: Array[Dictionary] = []

func log_event(event_name: String, details: Dictionary = {}) -> void:
	var event_dict := {
		"event_name": event_name,
		"timestamp": Time.get_unix_time_from_system(),
		"details": details
	}
	events_log.append(event_dict)
	print("EventLogger: Logged event - ", event_name, " | Details: ", details)
	
	# Send to backend client
	BackendClient.send_event(event_dict)

func get_all_events() -> Array[Dictionary]:
	return events_log
