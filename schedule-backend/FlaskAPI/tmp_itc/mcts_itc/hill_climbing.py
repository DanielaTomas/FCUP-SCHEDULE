from copy import deepcopy
import random
from mcts_itc.utils import find_available_rooms, write_best_simulation_result_to_file, get_events_by_name

class HillClimbing:

    def __init__(self, conflicts_checker, output_filename="output/output.txt"):
        self.conflicts_checker = conflicts_checker
        self.output_filename = output_filename
        self.best_result_hard= float('-inf')
        self.best_result_soft = float('-inf')
        

    def evaluate_timetable(self, simulated_timetable):
        hard_penalty = 0
        soft_penalty = 0
        event_names = []
        room_conflicts = {}

        for i, event in enumerate(simulated_timetable["events"]):
            hard_penalty += self.conflicts_checker.check_event_hard_constraints(event, simulated_timetable["events"][i+1:], event["RoomId"], event["Timeslot"], event["WeekDay"], room_conflicts)
            soft_penalty += (
                self.conflicts_checker.check_room_capacity(event, event["RoomId"]) +
                self.conflicts_checker.check_block_compactness(event, simulated_timetable["events"], event["Timeslot"], event["WeekDay"])
            )
            if event["Name"] not in event_names:
                soft_penalty += (
                    self.conflicts_checker.check_min_working_days(event, simulated_timetable["events"][i+1:], event["WeekDay"]) +
                    self.conflicts_checker.check_room_stability(event, simulated_timetable["events"][i+1:], event["RoomId"])
                )
            event_names.append(event["Name"])
            if -hard_penalty < self.best_result_hard or (-hard_penalty == self.best_result_hard and -soft_penalty < self.best_result_soft): return None
        hard_penalty += self.conflicts_checker.check_room_conflicts(room_conflicts)
        return -hard_penalty, -soft_penalty


    def period_move(self, timetable, i):
        event = random.choice(timetable["events"][i:])
        for new_period in event["Available_Periods"]:
            new_weekday, new_timeslot = new_period
            if new_period != (event["WeekDay"], event["Timeslot"]) and self.conflicts_checker.check_event_hard_constraints(event, timetable["events"], event["RoomId"], new_timeslot, new_weekday) <= -self.best_result_hard:
                event["WeekDay"], event["Timeslot"] = new_weekday, new_timeslot
                return timetable
        return None


    def room_move(self, timetable, i):
        event = random.choice(timetable["events"][i:])
        available_rooms = find_available_rooms(event, timetable["rooms"], timetable["events"], [(event["WeekDay"], event["Timeslot"])])
        if available_rooms.values() != [set()]:
            for new_room in list(list(available_rooms.values())[0]):
                if new_room != event["RoomId"] and self.conflicts_checker.check_event_hard_constraints(event, timetable["events"], new_room, event["Timeslot"], event["WeekDay"]) <= -self.best_result_hard:
                    event["RoomId"] = new_room
                    return timetable
        return None


    def event_move(self, timetable, i):
        event = random.choice(timetable["events"][i:])
        available_periods = event["Available_Periods"]

        for period in available_periods:
            new_weekday, new_timeslot = period

            if (new_weekday, new_timeslot) == (event["WeekDay"], event["Timeslot"]): continue

            available_rooms = find_available_rooms(event, timetable["rooms"], timetable["events"], [(new_weekday, new_timeslot)])
            if available_rooms.values() == [set()]: continue

            for new_room in list(list(available_rooms.values())[0]):
                if new_room != event["RoomId"] and self.conflicts_checker.check_event_hard_constraints(event, timetable["events"], new_room, new_timeslot, new_weekday) <= -self.best_result_hard:
                    event["WeekDay"], event["Timeslot"], event["RoomId"] = new_weekday, new_timeslot, new_room

                conflict_event = None
                for event in timetable["events"]:
                    if (event["WeekDay"] == new_weekday and event["Timeslot"] == new_timeslot and event["RoomId"] == new_room and event != event):
                        conflict_event = event
                        break

                if not conflict_event:
                    return timetable

                original_weekday, original_timeslot, original_room = conflict_event["WeekDay"], conflict_event["Timeslot"], conflict_event["RoomId"]

                conflict_event["WeekDay"], conflict_event["Timeslot"], conflict_event["RoomId"] = event["WeekDay"], event["Timeslot"], event["RoomId"]
                event["WeekDay"], event["Timeslot"], event["RoomId"] = original_weekday, original_timeslot, original_room

                if (self.conflicts_checker.check_event_hard_constraints(event, timetable["events"], event["RoomId"], event["Timeslot"], event["WeekDay"]) <= -self.best_result_hard and 
                    self.conflicts_checker.check_event_hard_constraints(conflict_event, timetable["events"], conflict_event["RoomId"], conflict_event["Timeslot"], conflict_event["WeekDay"]) <= -self.best_result_hard):
                    return timetable

                conflict_event["WeekDay"], conflict_event["Timeslot"], conflict_event["RoomId"] = original_weekday, original_timeslot, original_room
                event["WeekDay"], event["Timeslot"], event["RoomId"] = new_weekday, new_timeslot, new_room
        return None
    

    def room_stability_move(self, timetable, i):
        course_events = []
        event = random.choice(timetable["events"][i:])
        event_name = event["Name"]

        course_events = get_events_by_name(event_name, timetable["events"][i:])

        if len(course_events) < event["Lectures"]: return None

        target_room = random.choice(timetable["rooms"])
        original_assignments = []

        for e in course_events:
            if e["RoomId"] == target_room["Id"]: continue

            original_assignments.append((e, e["RoomId"]))

            if self.conflicts_checker.check_event_hard_constraints(e, timetable["events"], target_room["Id"], e["Timeslot"], e["WeekDay"]) <= -self.best_result_hard:
                e["RoomId"] = target_room["Id"]
            else:
                for orig_event, orig_room in original_assignments:
                    orig_event["RoomId"] = orig_room
                return None

        return timetable
    

    def curriculum_compactness_move(self, timetable, i):
        block = random.choice(timetable["blocks"])

        isolated_events = []
        events = []
        for event_name in block["Events"]:
            for ev in get_events_by_name(event_name, timetable["events"]):
                events.append(ev)
        
        for i, event in enumerate(events):
            if i+1 < len(events) and not(event["WeekDay"] == events[i+1]["WeekDay"] and abs(ev["Timeslot"] - events[i+1]["Timeslot"]) == 1):
                isolated_events.append(event)

        if not isolated_events: return None

        event_to_move = random.choice(isolated_events)

        available_periods = []
        for period in event_to_move["Available_Periods"]:
            weekday, timeslot = period
            if (weekday, timeslot) != (event_to_move["WeekDay"], event_to_move["Timeslot"]):
                adjacent_events = [e for e in events if e["Id"] != event["Id"] and e["WeekDay"] == weekday and abs(e["Timeslot"] - timeslot) == 1]
                if adjacent_events:
                    available_periods.append((weekday, timeslot))

        if not available_periods: return None

        new_weekday, new_timeslot = random.choice(available_periods)
        available_rooms = find_available_rooms(event_to_move, timetable["rooms"], timetable["events"], [(new_weekday, new_timeslot)])

        if available_rooms.values() == [set()]: return None
        
        for new_room in list(list(available_rooms.values())[0]):
            if self.conflicts_checker.check_event_hard_constraints(event_to_move, timetable["events"], new_room, new_timeslot, new_weekday) <= -self.best_result_hard:
                event_to_move["WeekDay"], event_to_move["Timeslot"], event_to_move["RoomId"] = new_weekday, new_timeslot, new_room
                return timetable
        return None


    def run_hill_climbing(self, timetable, i, best_result_hard, best_result_soft, max_idle_iterations):
        self.best_result_hard = best_result_hard
        self.best_result_soft = best_result_soft

        neighborhoods = [self.period_move, self.room_move, self.event_move, self.room_stability_move, self.curriculum_compactness_move]
        idle_iterations = 0
        best_timetable = deepcopy(timetable)

        while idle_iterations < max_idle_iterations:
            current_neighborhood = random.choice(neighborhoods)
            new_timetable = deepcopy(timetable)
            modified_timetable = current_neighborhood(new_timetable, i)

            if not modified_timetable:
                idle_iterations += 1
                continue

            result = self.evaluate_timetable(modified_timetable)

            if result is not None: 
                new_hard, new_soft = result
                if new_hard >= self.best_result_hard and new_soft > self.best_result_soft:
                    print(f"({current_neighborhood.__name__}): {self.best_result_hard} -> {new_hard} , {self.best_result_soft} -> {new_soft}") # ------- DEBUG
                    best_timetable = modified_timetable
                    self.best_result_hard = new_hard
                    self.best_result_soft = new_soft
                    with open(self.output_filename, 'w') as file:
                        write_best_simulation_result_to_file(best_timetable["events"], file)
                    idle_iterations = 0
                else:
                    idle_iterations += 1
            else:
                idle_iterations += 1

        return best_timetable, self.best_result_hard, self.best_result_soft
