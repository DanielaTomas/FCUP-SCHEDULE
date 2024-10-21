import random
from mcts_itc.check_conflicts import check_conflict_time
from mcts_itc.macros import DAYS, PERIODS_PER_DAY

def random_time():
    period = random.randint(0, PERIODS_PER_DAY-1)
    weekday = random.randint(0, DAYS-1)
    return period, weekday


def empty_rooms(event, rooms, events = None, period = None, weekday = None):
    available_rooms = {room["Id"] for room in rooms if room["Capacity"] >= event["Capacity"]}

    if not available_rooms:
        available_rooms = {room["Id"] for room in rooms}

    available_rooms_backup = available_rooms.copy()

    if events and weekday and period:
        for e in events:
            if check_conflict_time(e, period, weekday):
                available_rooms.discard(e["RoomId"])
            if not available_rooms: 
                return list(available_rooms_backup)
    
    return list(available_rooms)


def random_room(event, rooms, events = None, period = None, weekday = None):
    return random.choice(empty_rooms(event, rooms, events, period, weekday))


def random_event(events):
    return random.choice(events)