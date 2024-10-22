from mcts_itc.mcts import *

db = {
    "events": [],
    "blocks": [],
    "rooms": [],
    "constraints": []
}

def parse_input_data(input_data):
    lines = input_data.strip().split('\n')
    
    current_section = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("Name:") or line.startswith("Courses:") or line.startswith("Rooms:") or line.startswith("Days:") or line.startswith("Periods_per_day:") or line.startswith("Curricula:") or line.startswith("Constraints:"):
            continue
        if line.startswith("COURSES:"):
            current_section = "courses"
            continue
        elif line.startswith("ROOMS:"):
            current_section = "rooms"
            continue
        elif line.startswith("CURRICULA:"):
            current_section = "curricula"
            continue
        elif line.startswith("UNAVAILABILITY_CONSTRAINTS:"):
            current_section = "unavailability_constraints"
            continue
        elif line == "END.":
            break
        
        if current_section == "courses":
            parts = line.split()
            if len(parts) != 5:
                print(f"Skipping invalid course line: {line}")
                continue
            course_id, teacher, num_lectures, min_days, num_students = parts[0], parts[1], int(parts[2]), int(parts[3]), int(parts[4])
            db["events"].append({"Name": course_id, "Teacher": teacher, "Lectures": num_lectures, "MinWorkingDays": min_days, "Capacity": num_students, "Timeslot": None, "WeekDay": None, "RoomId": None})

        elif current_section == "rooms":
            parts = line.split()
            if len(parts) != 2:
                print(f"Skipping invalid room line: {line}")
                continue
            room_id, capacity = parts[0], int(parts[1])
            db["rooms"].append({"Id": room_id, "Capacity": capacity})

        elif current_section == "curricula":
            parts = line.split()
            if len(parts) < 3:
                print(f"Skipping invalid curriculum line: {line}")
                continue
            curriculum_id, num_courses = parts[0], int(parts[1])
            member_ids = parts[2:2 + num_courses]
            db["blocks"].append({"Id": curriculum_id, "Events": member_ids})

        elif current_section == "unavailability_constraints":
            parts = line.split()
            if len(parts) != 3:
                print(f"Skipping invalid unavailability constraint line: {line}")
                continue
            course_id, day, day_timeslot = parts[0], int(parts[1]), int(parts[2])
            db["constraints"].append({"Id": course_id, "WeekDay": day, "Timeslot": day_timeslot})


def write_best_solution_to_file(best_solution, file):
    for solution in best_solution:
        file.write(f"{solution['Name']} {solution['RoomId']} {solution['WeekDay']} {solution['Timeslot']}\n")


f = open("input_itc.ctt", "r")
parse_input_data(f.read())
f.close()

mcts = MCTS(db)
best_solution = mcts.run_mcts(40000)
file = open('final_output.txt', 'w')
write_best_solution_to_file(best_solution, file)
file.close()
