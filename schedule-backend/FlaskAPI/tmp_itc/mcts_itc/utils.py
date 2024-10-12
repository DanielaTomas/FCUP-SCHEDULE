import copy

def add_event_ids(events):
    events_to_visit = []
    unique_id = 0
    for event in events:
        for _ in range(event["Lectures"]):
            new_event = copy.deepcopy(event)
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


def update_event(event_id, timetable_events, weekday, period):
    for event in timetable_events:
        if event["Id"] == event_id:
            event["WeekDay"] = weekday
            event["Period"] = period
            return event
    return None
 

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