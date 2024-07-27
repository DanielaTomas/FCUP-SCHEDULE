import random
from datetime import datetime, timedelta

def random_time(duration, start_hour = 8, end_hour = 20, launch_start_hour = 13, launch_end_hour = 14):
    start_of_day = datetime(2025, 1, 1, start_hour, 0)
    end_of_day = datetime(2025, 1, 1, end_hour, 0)
    lunch_start = datetime(2025, 1, 1, launch_start_hour, 0)
    lunch_end = datetime(2025, 1, 1, launch_end_hour, 0) # earliest start afternoon
    
    latest_start_morning = lunch_start - timedelta(minutes=duration)
    latest_start_afternoon = end_of_day - timedelta(minutes=duration)

    if latest_start_morning <= start_of_day and latest_start_afternoon <= lunch_end:
        raise ValueError("Duration is too long to fit in the available time range.")

    valid_start_slots = []

    current_time = start_of_day
    while current_time <= latest_start_afternoon:
        if (current_time <= latest_start_morning) or (current_time >= lunch_start):
            valid_start_slots.append(current_time)
        current_time += timedelta(minutes=30) # 30-minute slots

    start_time = random.choice(valid_start_slots)
    end_time = start_time + timedelta(minutes=duration)

    start_timedelta = start_time - start_of_day
    end_timedelta = end_time - start_of_day

    start_timedelta = start_time - start_of_day
    end_timedelta = end_time - start_of_day

    return start_timedelta, end_timedelta, random.randint(2, 6)


def random_room(occupations, events, start_time, end_time, rooms):
    occupied_rooms = set()
    for event in events:
        room = event['RoomId']
        if room is not None:
            occupied_rooms.add(room)
    
    empty_rooms = [room for room in rooms if room["Id"] not in occupied_rooms]
    
    for occupation in occupations:
        room = occupation['RoomId']
        if room not in empty_rooms and start_time < occupation["EndTime"] and end_time > occupation["StartTime"]:
            empty_rooms.add(room)

    return random.choice(rooms) if not empty_rooms else random.choice(empty_rooms)


def random_event(events):
    return random.choice(events)