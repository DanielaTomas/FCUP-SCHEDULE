import csv
from mcts.mcts import *

db = {
    "events": [],
    "lecturers": [],
    "students": [],
    "students_events": [],
    "rooms": [],
    "restrictions": [],
    "occupations": [],
    "event_room_types": []
}


def generate_sample_data():
    load_csv_into_db('Events.csv', 'events')
    load_csv_into_db('Lecturers.csv', 'lecturers')
    load_csv_into_db('Students.csv', 'students')
    load_csv_into_db('StudentEvent.csv', 'students_events')
    load_csv_into_db('Rooms.csv', 'rooms')
    load_csv_into_db('Restrictions.csv', 'restrictions')
    load_csv_into_db('Event_Room_Type.csv', 'event_room_types')
    return db


def load_csv_into_db(csv_file, table_name):
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if table_name == "events":
                row["StartTime"] = parse_time(row["StartTime"])
                row["EndTime"] = parse_time(row["EndTime"])
                row["WeekDay"] = int(row["WeekDay"]) if row["WeekDay"] else None
                row["Duration"] = int(row["Duration"])
                row["Hide"] = bool(int(row["Hide"]))
                row["RoomId"] = row["RoomId"] if row["RoomId"] else None
                row["LecturerId"] = row["LecturerId"] if row["LecturerId"] else None
            elif table_name in ["lecturers", "students"]:
                row["Hide"] = bool(int(row["Hide"]))
            elif table_name == "rooms":
                row["RoomTypeId"] = int(row["RoomTypeId"])
                row["Hide"] = bool(int(row["Hide"]))
            elif table_name == "restrictions":
                row["StartTime"] = parse_time(row["StartTime"])
                row["EndTime"] = parse_time(row["EndTime"])
            elif table_name == "event_room_types":
                row["RoomTypeId"] = int(row["RoomTypeId"]) if row["RoomTypeId"] else None
            db[table_name].append(row)


def parse_time(time_str):
    if time_str:
        parts = time_str.split(':')
        if len(parts) == 2:
            h, m = map(int, parts)
            return timedelta(hours=h, minutes=m)
        elif len(parts) == 3:
            h, m, s = map(int, parts)
            return timedelta(hours=h, minutes=m, seconds=s)
    return None


def print_best_solution(best_solution):
    for solution in best_solution:
        print(f"Event {solution['Id']}, {solution['SubjectAbbr']}, Room {solution['RoomId']}, WeekDay {solution['WeekDay']}, {solution['StartTime']}-{solution['EndTime']}")


generate_sample_data()
#print(db)

mcts = MCTS(db)
best_solution = mcts.run_mcts(1500)
print_best_solution(best_solution)
