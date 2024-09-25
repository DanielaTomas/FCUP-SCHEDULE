def events_to_visit(events):
    events_to_visit = []
    for event in events:
        if event["StartTime"] is None and event["EndTime"] is None:
            events_to_visit.append(event)
    return events_to_visit


def get_student_events(student_id, students_events, events):
    return [get_event_by_id(student_event["EventId"], events) for student_event in students_events if student_event["StudentId"] == student_id]


def get_event_by_id(event_id, events):
    for event in events:
        if event["Id"] == event_id:
            return event
    raise Exception("Event Not Found")


def get_room_name_by_id(room_id, rooms):
    for room in rooms:
        if room["Id"] == room_id:
            return room["Name"]
    raise Exception("Room Not Found")


# Check conflicts


def check_conflict_time(start_time, other, end_time, weekday):
    if not all([other["EndTime"], other["StartTime"], other["WeekDay"]]): 
        return False
    return other["WeekDay"] == weekday and start_time < other["EndTime"] and end_time > other["StartTime"]


def check_conflict(other, start_time, end_time, weekday, room, rooms):
    return (get_room_name_by_id(room, rooms) != "DCC online" and
            other['RoomId'] == room and
            check_conflict_time(start_time, other, end_time, weekday))


def check_event_conflicts(event, other_events, rooms, lecturer, start_time, end_time, weekday):
    penalty = 0
    for other_event in other_events:
        if other_event["Id"] != event["Id"]:
            if event["RoomId"] and check_conflict(other_event, start_time, end_time, weekday, event["RoomId"], rooms):
                penalty += 1
            if lecturer and other_event["LecturerId"] == lecturer and check_conflict_time(start_time, other_event, end_time, weekday):
                penalty += 1
    return penalty


def check_room_occupations(event, occupations, rooms, start_time, end_time, weekday):
    penalty = 0
    for occupation in occupations:
        if event["RoomId"] and check_conflict(occupation, start_time, end_time, weekday, event["RoomId"], rooms):
            penalty += 1
    return penalty


def check_lecturer_restrictions(lecturer, restrictions, start_time, end_time, weekday):
    penalty = 0
    if lecturer:
        for restriction in restrictions:
            if (restriction["Type"] == 1 and
                restriction["LecturerId"] == lecturer and 
                check_conflict_time(start_time, restriction, end_time, weekday)):
                penalty += 1
    return penalty


def check_student_conflicts(event, students_events, events, start_time, end_time, weekday):
    penalty = 0
    for student_event in students_events:
        events = get_student_events(student_event, students_events, events)
        for e in events:
            if e["Id"] != event["Id"] and check_conflict_time(start_time, e, end_time, weekday):
                penalty += 1
    return penalty


def print_node_scores(node, depth=0):
    if node.visits > 0:
        score_visits = f"score {node.score}, visits {node.visits}, ratio {node.score / node.visits:.2f}"
    else:
        score_visits = "score {node.score}, visits {node.visits}, ratio -inf"
    print("   " * depth + f"Node: {score_visits}")
    for child in node.children:
        print_node_scores(child, depth + 1)