def calculate_event_durations(events): #TODO Add duration field to database
    for event in events:
        start_time = event["StartTime"]
        end_of_day = event["EndTime"]
        if start_time is not None and end_of_day is not None:
            duration = (end_of_day - start_time).total_seconds() / 60.0
            event["Duration"] = duration
        else:
            event["Duration"] = 60 # adjust if necessary


def get_room_name_by_id(room_id, rooms):
    for room in rooms:
        if room["Id"] == room_id:
            return room["Name"]
    return "Room Not Found"


def check_conflict_time(start_time, other, end_time, weekday):
    if not all([other.get("EndTime"), other.get("StartTime"), other.get("WeekDay")]): 
        return False
    return other["WeekDay"] == weekday and start_time < other["EndTime"] and end_time > other["StartTime"]


def check_conflict(other, start_time, end_time, weekday, room, rooms):
    return (get_room_name_by_id(room, rooms) != "DCC online" and
            other['RoomId'] == room and
            check_conflict_time(start_time, other, end_time, weekday))


def print_node_scores(node, depth=0):
    if node.visits > 0:
        score_visits = f"score {node.score}, visits {node.visits}, ratio {node.score / node.visits:.2f}"
    else:
        score_visits = "score {node.score}, visits {node.visits}, ratio -inf"
    print("   " * depth + f"Node: {score_visits}")
    for child in node.children:
        print_node_scores(child, depth + 1)