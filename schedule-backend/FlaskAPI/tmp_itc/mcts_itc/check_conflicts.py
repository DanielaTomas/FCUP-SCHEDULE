from mcts_itc.utils import get_events_by_name

def check_conflict_time(other, period, weekday):
    if other["Period"] is None or other["WeekDay"] is None: return False
    return other["WeekDay"] == weekday and other["Period"] == period


def check_conflict(other, period, weekday, room):
    return (other['RoomId'] == room and
            check_conflict_time(other, period, weekday))


def check_event_conflicts(event, constraints, blocks, other_events, lecturer, period, weekday):
    penalty = 0

    penalty += check_event_constraints(event, constraints, period, weekday)

    penalty += check_block_constraints(event, blocks, other_events, period, weekday)

    for other_event in other_events:
        if other_event["Id"] != event["Id"]:
            #print(f"{other_event['RoomId']} {event['RoomId']} {other_event['Id']} {other_event['Name']} {event['Id']} {event['Name']}")
            if event["RoomId"] and check_conflict(other_event, period, weekday, event["RoomId"]):
                penalty += 1
            if lecturer and other_event["Teacher"] == lecturer and check_conflict_time(other_event, period, weekday):
                penalty += 1
    return penalty


def check_event_constraints(event, constraints, period, weekday):
    penalty = 0
    for constraint in constraints:
        if constraint["Id"] == event["Name"] and check_conflict_time(event, period, weekday):
            penalty += 1
    return penalty


def check_block_constraints(event, blocks, events, period, weekday): #TODO events? other_events?
    penalty = 0
    for block in blocks:
        if event["Name"] in block["Events"]:
            for e_name in block["Events"]:
                evs = get_events_by_name(e_name,events)
                for ev in evs:
                    #print(f"{ev['Period']} {period} {ev['WeekDay']} {weekday} {ev['Id']} {ev['Name']} {event['Id']} {event['Name']} {check_conflict_time(ev, period, weekday)}")
                    if ev["Id"] != event["Id"] and check_conflict_time(ev, period, weekday):
                        penalty += 1
    return penalty