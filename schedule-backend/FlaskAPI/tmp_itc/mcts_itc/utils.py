from copy import deepcopy
from mcts_itc.macros import DAYS, PERIODS_PER_DAY, ALL_SLOTS

def add_event_ids(events, blocks = None, constraints = None):
    events_to_visit = []
    unique_id = 0
    for event in events:
        for _ in range(event["Lectures"]):
            new_event = deepcopy(event)
            new_event["Id"] = unique_id
            new_event["Priority"] =  event["MinWorkingDays"]*5 + event["Capacity"]*2
            new_event["Priority"] += sum(1 for block in blocks if new_event["Name"] in block["Events"])
            new_event["Priority"] += sum(1 for constraint in constraints if constraint["Id"] == event["Name"])
            events_to_visit.append(new_event)
            unique_id += 1
    
    return sorted(events_to_visit, key=lambda event: event["Priority"], reverse=True)


def find_available_rooms(event, rooms, events, available_periods):
    if not available_periods: return {period: {room["Id"] for room in rooms} for period in available_periods}

    period_room_availability = {period: {room["Id"] for room in rooms} for period in available_periods}

    for other_event in events:
        occupied_period = (other_event["WeekDay"], other_event["Timeslot"])
        if occupied_period in period_room_availability:
            period_room_availability[occupied_period].discard(other_event["RoomId"])

    suitable_rooms = {room["Id"] for room in rooms if room["Capacity"] >= event["Capacity"]}
    
    for period in available_periods:
        if period_room_availability[period]:
            period_room_availability[period] = period_room_availability[period] & suitable_rooms if period_room_availability[period] & suitable_rooms else period_room_availability[period]
        else:
            period_room_availability[period] = suitable_rooms if suitable_rooms else {room["Id"] for room in rooms}
    
    '''
    same_event_rooms = set()
    for other_event in events:
        if other_event["Name"] == event["Name"] and other_event["RoomId"] in period_room_availability:
            same_event_rooms.add(other_event["RoomId"])

    for period in available_periods:
        if period_room_availability[period]:
            period_room_availability[period] = period_room_availability[period] & suitable_rooms if period_room_availability[period] & suitable_rooms else period_room_availability[period]
        else:
            period_room_availability[period] = suitable_rooms if suitable_rooms else {room["Id"] for room in rooms}
    '''
    return period_room_availability
    
    
def get_events_by_name(event_name, events):
    evs = []
    for event in events:
        if event["Name"] == event_name:
            evs.append(event)
    return evs


def update_event(event_id, timetable_events, room, weekday, timeslot):
    for event in timetable_events:
        if event["Id"] == event_id:
            event["RoomId"] = room
            event["WeekDay"] = weekday
            event["Timeslot"] = timeslot
            return event
    return None
 

def get_valid_periods(event, constraints):
    available_periods = set(ALL_SLOTS)

    for constraint in constraints:
        for weekday in range(DAYS):
            for timeslot in range(PERIODS_PER_DAY):
                if constraint["Id"] == event["Name"] and constraint["WeekDay"] == weekday and constraint["Timeslot"] == timeslot:
                    available_periods.discard((weekday,timeslot))

    return list(available_periods) if available_periods else list(ALL_SLOTS)


def write_node_scores_to_file(node, file, depth=0):
    if node.visits > 0:
        if not node.path:
            score_visits = f"score {node.score}, visits {node.visits}, ratio {node.score / node.visits:.2f}"
        else:
            score_visits = f"{node.path[-1]['Id']} {node.path[-1]['Name']} D{node.path[-1]['WeekDay']} P{node.path[-1]['Timeslot']} R{node.path[-1]['RoomId']} score {node.score}, visits {node.visits}, ratio {node.score / node.visits:.2f}"
    else:
        score_visits = f"score {node.score}, visits {node.visits}, ratio -inf"
    
    file.write("   " * depth + f"Node: {score_visits}\n")
    
    for child in node.children:
        write_node_scores_to_file(child, file, depth + 1)


def write_best_simulation_result_to_file(events, file):
    for event in events:
        file.write(f"{event['Name']} {event['RoomId']} {event['WeekDay']} {event['Timeslot']}\n")
    
