from mcts_itc.utils import get_events_by_name

def check_conflict_time(other, period, weekday):
    if other["Period"] is None or other["WeekDay"] is None: return False
    return other["WeekDay"] == weekday and other["Period"] == period


def check_conflict(other, period, weekday, room):
    return (other['RoomId'] == room and
            check_conflict_time(other, period, weekday))


def check_event_hard_constraints(event, constraints, blocks, other_events, period, weekday):
    penalty = 0
    penalty += check_event_constraints(event, constraints, period, weekday)
    penalty += check_block_constraints(event, blocks, other_events, period, weekday)

    for other_event in other_events:
        if other_event["Id"] != event["Id"]:
            if event["RoomId"] and check_conflict(other_event, period, weekday, event["RoomId"]):
                penalty += 2
            if event["Teacher"] and other_event["Teacher"] == event["Teacher"] and check_conflict_time(other_event, period, weekday):
                penalty += 2
    return penalty


def check_event_soft_constraints(event, blocks, other_events, period, weekday):
    penalty = 0
    penalty += check_min_working_days(event, other_events, weekday)
    penalty += check_block_compactness(event,blocks,other_events, period, weekday)
    penalty += check_room_stability(event, other_events)
    return penalty


def check_event_constraints(event, constraints, period, weekday):
    penalty = 0
    for constraint in constraints:
        if constraint["Id"] == event["Name"] and check_conflict_time(constraint, period, weekday):
            penalty += 2
    return penalty


def check_block_constraints(event, blocks, other_events, period, weekday):
    penalty = 0
    for block in blocks:
        if event["Name"] in block["Events"]:
            for e_name in block["Events"]:
                evs = get_events_by_name(e_name,other_events)
                for ev in evs:
                    if ev["Id"] != event["Id"] and check_conflict_time(ev, period, weekday):
                        penalty += 2
    return penalty


def check_min_working_days(event, events, weekday):
    penalty = 0

    event_days = {ev["WeekDay"] for ev in events if ev["Name"] == event["Name"] and ev["Id"] != event["Id"]}
    
    event_days.add(weekday)
    
    if len(event_days) < event["MinWorkingDays"]:
        penalty += 1
    
    return penalty


def check_block_compactness(event, blocks, other_events, period, weekday):
    penalty = 0

    for block in blocks:

        if event["Name"] in block["Events"]:
            adjacent_found = False

            for e_name in block["Events"]:
                evs = get_events_by_name(e_name, other_events)

                for ev in evs:
                    if ev["Id"] != event["Id"] and ev["WeekDay"] == weekday:
                        if period == (ev["Period"]+1) or period == (ev["Period"]-1):
                            adjacent_found = True
                            break

                if adjacent_found:
                    break
            
            if not adjacent_found:
                penalty += 1

    return penalty


def check_room_stability(event, other_events):
    penalty = 0

    for other_event in other_events:
        if other_event["Id"] != event["Id"] and other_event["Name"] == event["Name"] and other_event["RoomId"] != event["RoomId"]:
            penalty += 1

    return penalty
