def events_to_visit(events):
    events_to_visit = []
    for event in events:
        if event["StartTime"] is None and event["EndTime"] is None:
            events_to_visit.append(event)
    return events_to_visit


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