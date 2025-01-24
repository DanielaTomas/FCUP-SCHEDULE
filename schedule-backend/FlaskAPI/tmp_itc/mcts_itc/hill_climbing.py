from copy import copy, deepcopy
import random, time
from mcts_itc.utils import find_available_rooms, write_best_simulation_result_to_file, get_events_by_name

class HillClimbing:

    def __init__(self, conflicts_checker, blocks, rooms, days, output_filename="output/output.txt"):
        self.blocks = blocks
        self.rooms = rooms
        self.conflicts_checker = conflicts_checker
        self.days = days
        self.output_filename = output_filename
        self.best_result_soft = float('-inf')
        

    def evaluate_timetable(self, simulated_events):
        soft_penalty = 0
        event_names = []

        for i, event in enumerate(simulated_events):
            soft_penalty += (
                self.conflicts_checker.check_room_capacity(event, event["RoomId"]) +
                self.conflicts_checker.check_block_compactness(event, simulated_events, event["Timeslot"], event["WeekDay"])
            )
            if event["Name"] not in event_names:
                soft_penalty += (
                    self.conflicts_checker.check_min_working_days(event, simulated_events[i+1:], event["WeekDay"]) +
                    self.conflicts_checker.check_room_stability(event, simulated_events[i+1:], event["RoomId"])
                )
            if -soft_penalty <= self.best_result_soft: return None
            event_names.append(event["Name"])
        return -soft_penalty
    


    def period_move(self, timetable, i):
        random_event = random.choice(timetable[i:])
        for new_period in random_event["Available_Periods"]:
            new_weekday, new_timeslot = new_period
            if new_period != (random_event["WeekDay"], random_event["Timeslot"]) and self.conflicts_checker.check_event_hard_constraints(random_event, timetable, random_event["RoomId"], new_timeslot, new_weekday) == 0:
                random_event["WeekDay"], random_event["Timeslot"] = new_weekday, new_timeslot
                return timetable
        return None


    def room_move(self, timetable, i):
        random_event = random.choice(timetable[i:])
        available_rooms = find_available_rooms(random_event["Capacity"], self.rooms, timetable, [(random_event["WeekDay"], random_event["Timeslot"])])
        if available_rooms.values() != [set()]:
            for new_room in list(list(available_rooms.values())[0]):
                if new_room != random_event["RoomId"] and self.conflicts_checker.check_event_hard_constraints(random_event, timetable, new_room, random_event["Timeslot"], random_event["WeekDay"]) == 0:
                    random_event["RoomId"] = new_room
                    return timetable
        return None


    def event_move(self, timetable, i):
        random_event = random.choice(timetable[i:])

        for new_weekday, new_timeslot in random_event["Available_Periods"]:
            if (new_weekday, new_timeslot) == (random_event["WeekDay"], random_event["Timeslot"]): continue
            available_rooms = find_available_rooms(random_event["Capacity"], self.rooms, timetable, [(new_weekday, new_timeslot)])
            if available_rooms.values() == [set()]: continue

            for new_room in list(list(available_rooms.values())[0]):
                if new_room == random_event["RoomId"]: continue
                elif self.conflicts_checker.check_event_hard_constraints(random_event, timetable, new_room, new_timeslot, new_weekday) == 0:
                    original_weekday, original_timeslot, original_room = random_event["WeekDay"], random_event["Timeslot"], random_event["RoomId"]
                    random_event["WeekDay"], random_event["Timeslot"], random_event["RoomId"] = new_weekday, new_timeslot, new_room

                conflict_event = None
                for event in timetable:
                    if event["Id"] != random_event["Id"] and (event["WeekDay"] == random_event["WeekDay"] and event["Timeslot"] == random_event["Timeslot"] and (event["RoomId"] == random_event["RoomId"] or event["Teacher"] == random_event["Teacher"])):
                        conflict_event = event
                        break

                if not conflict_event:
                    return timetable

                random_event["RoomId"], random_event["Timeslot"], random_event["WeekDay"] = conflict_event["RoomId"], conflict_event["Timeslot"], conflict_event["WeekDay"]
                conflict_event["RoomId"], conflict_event["Timeslot"], conflict_event["WeekDay"] = original_room, original_timeslot, original_weekday

                if (self.conflicts_checker.check_event_hard_constraints(random_event, timetable, random_event["RoomId"], random_event["Timeslot"], random_event["WeekDay"]) == 0 and 
                    self.conflicts_checker.check_event_hard_constraints(conflict_event, timetable, conflict_event["RoomId"], conflict_event["Timeslot"], conflict_event["WeekDay"]) == 0):
                    return timetable
        return None
    

    def room_stability_move(self, timetable, i):
        course_events = []
        random_event = random.choice(timetable[i:])

        course_events = get_events_by_name(random_event["Name"], timetable[i:])

        if len(course_events) < random_event["Lectures"]: return None

        target_room = random.choice(self.rooms)

        for e in course_events:
            if e["RoomId"] != target_room["Id"]:
                if self.conflicts_checker.check_event_hard_constraints(e, timetable, target_room["Id"], e["Timeslot"], e["WeekDay"]) == 0:
                    e["RoomId"] = target_room["Id"]
                else:
                    return None

        return timetable
    

    def curriculum_compactness_move(self, timetable, i):
        random_block = random.choice(self.blocks)

        isolated_events = []
        block_events = []
        for event_name in random_block["Events"]:
            for ev in get_events_by_name(event_name, timetable):
                block_events.append(ev)
                if ev in timetable[i:]:
                    isolated_events.append(ev)
        
        for j, event in enumerate(block_events):
            if j+1 < len(block_events) and event["WeekDay"] == block_events[j+1]["WeekDay"] and abs(ev["Timeslot"] - block_events[j+1]["Timeslot"]) == 1:
                if event in isolated_events:
                    isolated_events.remove(event)

        if not isolated_events: return None

        event_to_move = random.choice(isolated_events)

        available_periods = []
        for weekday, timeslot in event_to_move["Available_Periods"]:
            if (weekday, timeslot) != (event_to_move["WeekDay"], event_to_move["Timeslot"]):
                adjacent_events = [e for e in block_events if e["Id"] != event_to_move["Id"] and e["WeekDay"] == weekday and abs(e["Timeslot"] - timeslot) == 1]
                if adjacent_events:
                    available_periods.append((weekday, timeslot))

        if not available_periods: return None

        new_weekday, new_timeslot = random.choice(available_periods)
        available_rooms = find_available_rooms(event_to_move["Capacity"], self.rooms, timetable, [(new_weekday, new_timeslot)])

        if available_rooms.values() == [set()]: return None
        
        for new_room in list(list(available_rooms.values())[0]):
            if self.conflicts_checker.check_event_hard_constraints(event_to_move, timetable, new_room, new_timeslot, new_weekday) == 0:
                event_to_move["WeekDay"], event_to_move["Timeslot"], event_to_move["RoomId"] = new_weekday, new_timeslot, new_room
                return timetable
        return None

    
    def min_working_days_move(self, timetable, i):
        penalized_events = [
            event for event in timetable[i:]
            if self.conflicts_checker.check_min_working_days(event, timetable, event["WeekDay"]) > 0
        ]

        if not penalized_events: return None

        event_to_move = random.choice(penalized_events)

        taught_days = {day for event in timetable if event["Name"] == event_to_move["Name"] for day in [event["WeekDay"]]}

        available_days = set(range(self.days)) - taught_days

        if not available_days:
            return None

        for new_weekday, new_timeslot in event_to_move["Available_Periods"]:
            if new_weekday in available_days:
                available_rooms = find_available_rooms(event_to_move["Capacity"], self.rooms, timetable, [(new_weekday,new_timeslot)])
                if available_rooms.values() == [set()]: return None
                for new_room in list(list(available_rooms.values())[0]):
                    if self.conflicts_checker.check_event_hard_constraints(event_to_move, timetable, new_room, new_timeslot, new_weekday) == 0:
                        event_to_move["WeekDay"], event_to_move["Timeslot"], event_to_move["RoomId"] = new_weekday, new_timeslot, new_room
                        return timetable
        return None


    def run_hill_climbing(self, best_timetable, i, best_result_soft, start_time, time_limit, max_idle_iterations):
        self.best_result_soft = best_result_soft

        neighborhoods = [self.period_move, self.room_move, self.event_move, self.room_stability_move, self.min_working_days_move, self.curriculum_compactness_move]
        idle_iterations = 0

        while idle_iterations < max_idle_iterations and (time.time() - start_time <= time_limit):
            current_neighborhood = random.choice(neighborhoods)
            """ new_timetable = []
            new_timetable[:i] = copy(best_timetable[:i])
            new_timetable[i:] = deepcopy(best_timetable[i:]) """
            modified_timetable = current_neighborhood(deepcopy(best_timetable), i)

            if not modified_timetable:
                idle_iterations += 1
                continue

            result = self.evaluate_timetable(modified_timetable)

            if result is not None: 
                if result > self.best_result_soft:
                    print(f"({current_neighborhood.__name__}): {self.best_result_soft} -> {result}") # ------- DEBUG
                    self.best_result_soft = result
                    best_timetable = modified_timetable
                    with open(self.output_filename, 'w') as file:
                        write_best_simulation_result_to_file(best_timetable, file)
                    idle_iterations = 0
                else:
                    idle_iterations += 1
            else:
                idle_iterations += 1

        return self.best_result_soft
