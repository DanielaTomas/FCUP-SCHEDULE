def events_to_visit(events):
    events_to_visit = []
    for event in events:
        if event["StartTime"] is None or event["EndTime"] is None or event["WeekDay"] is None:
            events_to_visit.append(event)
    return events_to_visit


def get_student_events(student_id, students_events, events):
    return [get_event_by_id(student_event["EventId"], events) for student_event in students_events if student_event["StudentId"] == student_id]


def get_event_by_id(event_id, events):
    for event in events:
        if event["Id"] == event_id:
            return event
    return None


def get_room_name_by_id(room_id, rooms):
    for room in rooms:
        if room["Id"] == room_id:
            return room["Name"]
    return None


def update_event(event_id, timetable_events, weekday, start_time, end_time):
    for event in timetable_events:
        if event["Id"] == event_id:
            event["WeekDay"] = weekday
            event["StartTime"] = start_time
            event["EndTime"] = end_time
            return event
    return None


def check_room_use():
    #TODO
    return


def print_node_scores(node, depth=0):
    if node.visits > 0:
        score_visits = f"score {node.score}, visits {node.visits}, ratio {node.score / node.visits:.2f}"
    else:
        score_visits = "score {node.score}, visits {node.visits}, ratio -inf"
    print("   " * depth + f"Node: {score_visits}")
    for child in node.children:
        print_node_scores(child, depth + 1)