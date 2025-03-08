from algorithm.mcts import *
import argparse
import os

def reset_db():
    return {
        "events": [],
        "blocks": {},
        "rooms": {},
        "constraints": {}
}

def parse_input_data(input_data, db):
    lines = input_data.strip().split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("Name:") or line.startswith("Courses:") or line.startswith("Rooms:") or line.startswith("Curricula:") or line.startswith("Constraints:"):
            continue
        if line.startswith("Days:"):
            parts = line.split()
            days = int(parts[1])
            continue
        if line.startswith("Periods_per_day:"):
            parts = line.split()
            periods_per_day = int(parts[1])
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
            db["events"].append({"Name": course_id, "Teacher": teacher, "Lectures": num_lectures, "MinWorkingDays": min_days, "Capacity": num_students})

        elif current_section == "rooms":
            parts = line.split()
            if len(parts) != 2:
                print(f"Skipping invalid room line: {line}")
                continue
            room_id, capacity = parts[0], int(parts[1])
            db["rooms"][room_id] = {"Capacity": capacity}

        elif current_section == "curricula":
            parts = line.split()
            if len(parts) < 3:
                print(f"Skipping invalid curriculum line: {line}")
                continue
            curriculum_id, num_courses = parts[0], int(parts[1])
            member_ids = parts[2:2 + num_courses]
            db["blocks"][curriculum_id] = {"Events": member_ids}

        elif current_section == "unavailability_constraints":
            parts = line.split()
            if len(parts) != 3:
                print(f"Skipping invalid unavailability constraint line: {line}")
                continue
            course_id, day, day_timeslot = parts[0], int(parts[1]), int(parts[2])
            if course_id not in db["constraints"]:
                db["constraints"][course_id] = []
            db["constraints"][course_id].append({"WeekDay": day, "Timeslot": day_timeslot})

    return days, periods_per_day


def process_file(input_file, input_dir, output_dir, log_dir, iterations, time_limit, params):
    input_file_path = os.path.join(input_dir, input_file)
    if not os.path.exists(input_file_path):
        print(f"Warning: The input file '{input_file_path}' does not exist. Skipping.")
        return

    print(f"Processing {input_file}...")
    with open(input_file_path, "r") as f:
        db = reset_db()
        days, periods_per_day = parse_input_data(f.read(), db)

    output_file = os.path.join(output_dir, f"{os.path.splitext(input_file)[0]}_output.txt")
    log_file = os.path.join(log_dir, f"{os.path.splitext(input_file)[0]}_log.txt")
    
    with open(log_file, "w") as file:
        file.write("")
    
    mcts = MCTS(params, db, days, periods_per_day, output_file)
    best_solution = mcts.run_mcts(iterations=iterations, time_limit=time_limit)

    if best_solution:
        final_output_dir = "final_output"
        directory_exists(final_output_dir)
        final_output_file = os.path.join(final_output_dir, f"{os.path.splitext(input_file)[0]}_final_output.txt")
        with open(final_output_file, 'w') as file:
            write_best_final_solution_to_file(best_solution, file)

    print(f"Finished processing {input_file}, output saved to {output_file}.")

class Params:
    pass


def main():
    parser = argparse.ArgumentParser(description="Run MCTS for timetabling.")
    parser.add_argument("--time_limit", type=int, default=300, help="Time limit in seconds for the MCTS run (default: 300 seconds)")
    parser.add_argument("--iterations", type=int, default=None, help="Number of iterations for the MCTS run")
    parser.add_argument("--c_param", type=float, default=1.4, help="C parameter for the MCTS run")
    parser.add_argument("--input_files", nargs="+", default=[f"comp{str(i+1).zfill(2)}.ctt" for i in range(21)], help="List of input files to process (default: comp01.ctt - comp21.ctt)")
    args = parser.parse_args()

    input_dir = "input"
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input folder '{input_dir}' does not exist. Please create it and add your input files.")

    output_dir = "output"
    log_dir = "log"
    directory_exists(output_dir)
    directory_exists(log_dir)

    for input_file in args.input_files:
        params = Params
        params.c_param = args.c_param
        process_file(input_file, input_dir, output_dir, log_dir, args.iterations, args.time_limit, params)

    log_line = {}
    for input_file in args.input_files:
        output_file = os.path.join(log_dir, f"{os.path.splitext(input_file)[0]}_log.txt")
        log_line[input_file] = get_last_log_line(output_file)

    save_results_to_excel(log_line, args.input_files)

if __name__ == "__main__":
    main()