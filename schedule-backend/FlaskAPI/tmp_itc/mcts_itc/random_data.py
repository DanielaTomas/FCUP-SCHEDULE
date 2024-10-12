import random
from mcts_itc.check_conflicts import check_conflict_time

def random_time():
    period = random.randint(0, 3)
    weekday = random.randint(0, 4)
    return period, weekday


def empty_rooms(events, event, rooms):
    available_rooms = set()

    for room in rooms:
        if room["Id"] is not None and event["Capacity"] <= room["Capacity"]:
                available_rooms.add(room["Id"])

    for e in events:
        if check_conflict_time(e, event["Period"], event["WeekDay"]):
            available_rooms.discard(e["RoomId"])

    return list(available_rooms)


def random_room(events, event, rooms):
    return random.choice(empty_rooms(events, event, rooms))


def random_event(events):
    return random.choice(events)