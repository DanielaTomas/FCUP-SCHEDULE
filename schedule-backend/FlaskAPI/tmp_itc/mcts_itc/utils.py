from copy import deepcopy

weekday_range = 5
period_range = 4

def add_event_ids(events):
    events_to_visit = []
    unique_id = 0
    for event in events:
        for _ in range(event["Lectures"]):
            new_event = deepcopy(event)
            new_event["Id"] = unique_id
            events_to_visit.append(new_event)
            unique_id += 1
    return events_to_visit


def get_events_by_name(event_name, events):
    evs = []
    for event in events:
        if event["Name"] == event_name:
            evs.append(event)
    return evs


def update_event(event_id, timetable_events, room, weekday, period):
    for event in timetable_events:
        if event["Id"] == event_id:
            event["RoomId"] = room
            event["WeekDay"] = weekday
            event["Period"] = period
            return event
    return None
 

def get_valid_slots(event, constraints):
    all_slots = set((weekday, period) for weekday in range(weekday_range) for period in range(period_range))
    available_slots = set(all_slots)

    for constraint in constraints:
        for weekday in range(weekday_range):
            for period in range(period_range):
                if constraint["Id"] == event["Name"] and constraint["WeekDay"] == weekday and constraint["Period"] == period:
                    available_slots.discard((weekday,period))

    return list(available_slots) if available_slots else list(all_slots)


def print_node_scores(node, depth=0):
    if node.visits > 0:
        if not node.path:
            score_visits = f"score {node.score}, visits {node.visits}, ratio {node.score / node.visits:.2f}"
        else:
            score_visits = f"{node.path[-1]['Id']} {node.path[-1]['Name']} D{node.path[-1]['WeekDay']} P{node.path[-1]['Period']} R{node.path[-1]['RoomId']} score {node.score}, visits {node.visits}, ratio {node.score / node.visits:.2f}"
    else:
        score_visits = "score {node.score}, visits {node.visits}, ratio -inf"
    print("   " * depth + f"Node: {score_visits}")
    for child in node.children:
        print_node_scores(child, depth + 1)