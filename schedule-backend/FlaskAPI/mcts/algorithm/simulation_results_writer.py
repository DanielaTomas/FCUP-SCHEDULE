import os
import time
from datetime import datetime
from algorithm.macros import DEBUG_LOG

def write_simulation_results(output_filename, assigned_events, start_time, hard_penalty_result, soft_penalty_result):
    """
    Writes the best simulation results to both a log file (if DEBUG_LOG is enabled) and the output file.

    Args:
        output_filename (str): Path to the file where best assignments are saved.
        assigned_events (list): List of scheduled events with assignment information.
        start_time (float): Start time of the simulation (as a Unix timestamp).
        hard_penalty_result (int): Best hard constraint penalty score.
        soft_penalty_result (int): Best soft constraint penalty score.
    """
    if DEBUG_LOG:
        _, tail = os.path.split(output_filename)
        input_file_name = tail.split('_')[0]
        log_file_name = os.path.join("log", f"{input_file_name}_log.txt")
        
        start_dt = datetime.fromtimestamp(start_time)
        current_dt = datetime.fromtimestamp(time.time())

        with open(log_file_name, 'a') as file:
            file.write(f"Time: {current_dt - start_dt}, Hard: {hard_penalty_result}, Soft: {soft_penalty_result}\n")
    
    with open(output_filename, 'w') as file:
        for event in assigned_events:
            if event['RoomId'] is not None or event['WeekDay'] is not None or event['Timeslot'] is not None:
                file.write(f"{event['Name']} {event['RoomId']} {event['WeekDay']} {event['Timeslot']}\n")


def directory_exists(directory):
    """
    Ensures that the given directory exists, creating it if necessary.

    Args:
        directory (str): The path of the directory to check or create.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


""" def write_best_final_solution_to_file(best_solution, file):
    for solution in best_solution.values():
        file.write(f"{solution['Name']} {solution['RoomId']} {solution['WeekDay']} {solution['Timeslot']}\n") """