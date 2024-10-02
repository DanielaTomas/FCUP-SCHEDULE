import random
from datetime import datetime, timedelta
from mcts.utils import get_room_name_by_id
from mcts.check_conflicts import check_conflict_time


def calculate_time_bounds(duration, start_hour=8, end_hour=20, launch_start_hour=13, launch_end_hour=14):
    start_of_day = datetime(2025, 1, 1, start_hour, 0)
    end_of_day = datetime(2025, 1, 1, end_hour, 0)
    lunch_start = datetime(2025, 1, 1, launch_start_hour, 0)
    lunch_end = datetime(2025, 1, 1, launch_end_hour, 0)

    latest_start_morning = lunch_start - timedelta(minutes=duration)
    latest_start_afternoon = end_of_day - timedelta(minutes=duration)

    if latest_start_morning < start_of_day and latest_start_afternoon < lunch_end:
        raise ValueError(f"Duration is too long to fit in the available time range.")

    return start_of_day, lunch_end, latest_start_morning, latest_start_afternoon


def get_valid_start_slots(start_of_day, lunch_end, latest_start_morning, latest_start_afternoon):
    valid_start_slots = []
    current_time = start_of_day
    while current_time <= latest_start_afternoon:
        if (current_time <= latest_start_morning) or (current_time >= lunch_end):
            valid_start_slots.append(current_time)
        current_time += timedelta(minutes=30)  # 30-minute slots
    return valid_start_slots


def random_time(duration, start_hour = 8, end_hour = 20, launch_start_hour = 13, launch_end_hour = 14):
    start_of_day, lunch_end, latest_start_morning, latest_start_afternoon = calculate_time_bounds(duration, start_hour, end_hour, launch_start_hour, launch_end_hour)
    
    valid_start_slots = get_valid_start_slots(start_of_day, lunch_end, latest_start_morning, latest_start_afternoon)

    start_time = random.choice(valid_start_slots)
    end_time = start_time + timedelta(minutes=duration)
    start_time = timedelta(hours=start_time.hour, minutes=start_time.minute)
    end_time = timedelta(hours=end_time.hour, minutes=end_time.minute)

    weekday = random.randint(2, 6)
    
    return start_time, end_time, weekday


def empty_rooms(occupations, events, event, rooms):
    empty_rooms = {room["Id"] for room in rooms if room["Id"] is not None}
    online = []
    
    for e in events:
        if get_room_name_by_id(e["RoomId"], rooms) == "DCC online": 
            online.append(e["RoomId"])
            if e["RoomId"] in empty_rooms: 
                empty_rooms.remove(e["RoomId"])
        elif e['RoomId'] in empty_rooms and (get_room_name_by_id(e["RoomId"], rooms) == "__________" or check_conflict_time(event["StartTime"], e, event["EndTime"], event["WeekDay"])):
            empty_rooms.remove(e["RoomId"])

    for occupation in occupations:
        room = occupation['RoomId']
        if room in empty_rooms and check_conflict_time(event["StartTime"], occupation, event["EndTime"], event["WeekDay"]):
            empty_rooms.remove(room)

    return online if not empty_rooms else list(empty_rooms)


def random_room(occupations, events, event, rooms):
    return random.choice(empty_rooms(occupations, events, event, rooms))


def random_event(events):
    return random.choice(events)