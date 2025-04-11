import random
from copy import copy
from itertools import dropwhile

def add_event_ids_and_priority(events, days, periods_per_day, blocks, constraints):
    events_to_visit = []
    name_to_event_ids = {}
    unique_id = 0

    for event in events:
        for _ in range(event["Lectures"]):
            new_event = copy(event)
            new_event["Id"] = unique_id
            new_event["Available_Periods"] = get_valid_periods(event, constraints, days, periods_per_day)
            new_event["Priority"] = ((new_event["Lectures"] - new_event["MinWorkingDays"]) * 4
                                    - len(new_event["Available_Periods"]) * 3
                                    + new_event["Capacity"] * 2
                                    + sum(1 for block in blocks.values() if event["Name"] in block["Events"])
                                    )
            events_to_visit.append(new_event)

            if event["Name"] not in name_to_event_ids:
                name_to_event_ids[event["Name"]] = set()
            name_to_event_ids[event["Name"]].add(unique_id)
            
            unique_id += 1

    for event in events_to_visit:
        event["Available_Periods"] = sort_periods(event, events_to_visit)
        
    sorted_events = sorted(events_to_visit, key=lambda event: (event["Priority"], random.random()), reverse=True)

    return sorted_events, name_to_event_ids


def sort_periods(event, events): # periods that are less frequently available across events get higher priority
    period_conflict_count = {}
    for period in event["Available_Periods"]:
        period_conflict_count[period] = sum(period in other["Available_Periods"] for other in events if other["Id"] != event["Id"])
    return sorted(event["Available_Periods"], key=lambda p: (period_conflict_count[p], p[0], p[1]))
    

def root_expansion_limit(event, rooms):
        available_rooms = find_available_rooms(event["Capacity"], rooms, [], event["Available_Periods"])
        expansion_limit = sum(len(rooms) for rooms in available_rooms.values())
        return expansion_limit


def find_available_rooms(event_capacity, rooms, events, available_periods):
    period_room_availability = {period: set(rooms.keys()) for period in available_periods}
    for other_event in events:
        occupied_period = (other_event["WeekDay"], other_event["Timeslot"])
        if occupied_period in period_room_availability:
            period_room_availability[occupied_period].discard(other_event["RoomId"])

    suitable_rooms = {room_id for room_id, room in rooms.items() if room["Capacity"] >= event_capacity}
    for period in available_periods:
        if period_room_availability[period]:
            intersected = period_room_availability[period] & suitable_rooms
            if intersected: 
                sorted_rooms = sorted(list(intersected), key=lambda room_id: (rooms[room_id]["Capacity"] - event_capacity))
            else:
                sorted_rooms = sorted(list(period_room_availability[period]), key=lambda room_id: abs(rooms[room_id]["Capacity"] - event_capacity))
            period_room_availability[period] = sorted_rooms 

    return period_room_availability


def get_valid_periods(event, constraints, days, periods_per_day):
    available_periods = set((weekday, timeslot) for weekday in range(days) for timeslot in range(periods_per_day))

    event_constraints = constraints.get(event["Name"], [])
    restricted_slots = set((constraint["WeekDay"], constraint["Timeslot"]) for constraint in event_constraints)
    available_periods -= restricted_slots
    
    if available_periods:
        available_periods_list = list(available_periods)
        random.shuffle(available_periods_list)
        return available_periods_list
    
    return list()


def dict_slice(d, start_key, next_iteration = False):
    iterator = dropwhile(lambda x: x[0] != start_key, d.items())
    if next_iteration: next(iterator, None)
    return dict(iterator)


def evaluate_timetable(conflicts_checker, timetable, unassigned_events = [], full_evaluation = True):
    hard_penalty = 0
    soft_penalty = 0
    room_conflicts = {}
    event_names = []

    for event in timetable.values():
        events_to_check = dict_slice(timetable, event["Id"], True)
        hard_penalty += conflicts_checker.check_event_hard_constraints(event, events_to_check, event["RoomId"], event["Timeslot"], event["WeekDay"], room_conflicts)
        
        if full_evaluation:
            soft_penalty += (conflicts_checker.check_room_capacity(event, event["RoomId"])
                            + conflicts_checker.check_block_compactness(
                                event, timetable, event["Timeslot"], event["WeekDay"]
                            ))
            if event["Name"] not in event_names:
                soft_penalty += (conflicts_checker.check_min_working_days(event, events_to_check, event["WeekDay"])
                                + conflicts_checker.check_room_stability(event, events_to_check, event["RoomId"]))
                event_names.append(event["Name"])
    
    hard_penalty += conflicts_checker.check_room_conflicts(room_conflicts)
    
    if full_evaluation:
        hard_penalty += len(unassigned_events)
        return -hard_penalty, -soft_penalty
    return -hard_penalty