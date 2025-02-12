import random
from copy import copy
from itertools import dropwhile

def dict_slice(d, start_key, next_iteration = False):
    iterator = dropwhile(lambda x: x[0] != start_key, d.items())
    if next_iteration: next(iterator, None)
    return dict(iterator)


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

    sorted_events = sorted(events_to_visit, key=lambda event: (event["Priority"], random.random()), reverse=True)

    return sorted_events, name_to_event_ids


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
            period_room_availability[period] = period_room_availability[period] & suitable_rooms if period_room_availability[period] & suitable_rooms else period_room_availability[period] 
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
    
    return None


def write_best_simulation_result_to_file(events, file):
    for event in events:
        if event['RoomId'] is not None or event['WeekDay'] is not None or event['Timeslot'] is not None:
            file.write(f"{event['Name']} {event['RoomId']} {event['WeekDay']} {event['Timeslot']}\n")
