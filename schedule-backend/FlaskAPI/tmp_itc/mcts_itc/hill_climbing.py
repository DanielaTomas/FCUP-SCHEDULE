from copy import copy, deepcopy
import random
from mcts_itc.utils import find_available_rooms, write_best_simulation_result_to_file, get_events_by_name

class HillClimbing:

    def __init__(self, conflicts_checker, blocks, rooms, output_filename="output/output.txt"):
        self.blocks = blocks
        self.rooms = rooms
        self.conflicts_checker = conflicts_checker
        self.output_filename = output_filename
        self.best_result_hard= float('-inf')
        self.best_result_soft = float('-inf')
        

    def evaluate_timetable(self, simulated_events):
        hard_penalty = 0
        soft_penalty = 0
        event_names = []
        room_conflicts = {}

        for i, event in enumerate(simulated_events):
            hard_penalty += self.conflicts_checker.check_event_hard_constraints(event, simulated_events[i+1:], event["RoomId"], event["Timeslot"], event["WeekDay"], room_conflicts)
            soft_penalty += (
                self.conflicts_checker.check_room_capacity(event, event["RoomId"]) +
                self.conflicts_checker.check_block_compactness(event, simulated_events, event["Timeslot"], event["WeekDay"])
            )
            if event["Name"] not in event_names:
                soft_penalty += (
                    self.conflicts_checker.check_min_working_days(event, simulated_events[i+1:], event["WeekDay"]) +
                    self.conflicts_checker.check_room_stability(event, simulated_events[i+1:], event["RoomId"])
                )
            event_names.append(event["Name"])
            if -hard_penalty < self.best_result_hard or (-hard_penalty == self.best_result_hard and -soft_penalty < self.best_result_soft): return None
        hard_penalty += self.conflicts_checker.check_room_conflicts(room_conflicts)
        return -hard_penalty, -soft_penalty


    def period_move(self, timetable, i):
        event = random.choice(timetable[i:])
        for new_period in event["Available_Periods"]:
            new_weekday, new_timeslot = new_period
            if new_period != (event["WeekDay"], event["Timeslot"]) and self.conflicts_checker.check_event_hard_constraints(event, timetable, event["RoomId"], new_timeslot, new_weekday) <= -self.best_result_hard:
                event["WeekDay"], event["Timeslot"] = new_weekday, new_timeslot
                return timetable
        return None


    def room_move(self, timetable, i):
        event = random.choice(timetable[i:])
        available_rooms = find_available_rooms(event["Capacity"], self.rooms, timetable, [(event["WeekDay"], event["Timeslot"])])
        if available_rooms.values() != [set()]:
            for new_room in list(list(available_rooms.values())[0]):
                if new_room != event["RoomId"] and self.conflicts_checker.check_event_hard_constraints(event, timetable, new_room, event["Timeslot"], event["WeekDay"]) <= -self.best_result_hard:
                    event["RoomId"] = new_room
                    return timetable
        return None


    def event_move(self, timetable, i):
        random_event = random.choice(timetable[i:])
        available_periods = random_event["Available_Periods"]

        for period in available_periods:
            new_weekday, new_timeslot = period

            if (new_weekday, new_timeslot) == (random_event["WeekDay"], random_event["Timeslot"]): continue
            available_rooms = find_available_rooms(random_event["Capacity"], self.rooms, timetable, [(new_weekday, new_timeslot)])
            if available_rooms.values() == [set()]: continue

            for new_room in list(list(available_rooms.values())[0]):
                if new_room == random_event["RoomId"]: continue
                elif self.conflicts_checker.check_event_hard_constraints(random_event, timetable, new_room, new_timeslot, new_weekday) <= -self.best_result_hard:
                    original_weekday, original_timeslot, original_room = random_event["WeekDay"], random_event["Timeslot"], random_event["RoomId"]
                    random_event["WeekDay"], random_event["Timeslot"], random_event["RoomId"] = new_weekday, new_timeslot, new_room

                conflict_event = None
                for event in timetable:
                    if event["Id"] != random_event["Id"] and (event["WeekDay"] == random_event["WeekDay"] and event["Timeslot"] == random_event["Timeslot"] and (event["RoomId"] == random_event["RoomId"] or event["Teacher"] == random_event["Teacher"])):
                        conflict_event = random_event
                        break

                if not conflict_event:
                    return timetable

                if (self.conflicts_checker.check_event_hard_constraints(random_event, timetable, conflict_event["RoomId"], conflict_event["Timeslot"], conflict_event["WeekDay"]) <= -self.best_result_hard and 
                    self.conflicts_checker.check_event_hard_constraints(conflict_event, timetable, original_room, original_timeslot, original_weekday) <= -self.best_result_hard):
                    random_event["RoomId"], random_event["Timeslot"], random_event["WeekDay"] = conflict_event["RoomId"], conflict_event["Timeslot"], conflict_event["WeekDay"]
                    conflict_event["RoomId"], conflict_event["Timeslot"], conflict_event["WeekDay"] = original_room, original_timeslot, original_weekday
                    return timetable
        return None
    

    def room_stability_move(self, timetable, i):
        course_events = []
        event = random.choice(timetable[i:])
        event_name = event["Name"]

        course_events = get_events_by_name(event_name, timetable[i:])

        if len(course_events) < event["Lectures"]: return None

        target_room = random.choice(self.rooms)
        original_assignments = []

        for e in course_events:
            if e["RoomId"] == target_room["Id"]: continue

            original_assignments.append((e, e["RoomId"]))

            if self.conflicts_checker.check_event_hard_constraints(e, timetable, target_room["Id"], e["Timeslot"], e["WeekDay"]) <= -self.best_result_hard:
                e["RoomId"] = target_room["Id"]
            else:
                for orig_event, orig_room in original_assignments:
                    orig_event["RoomId"] = orig_room
                return None

        return timetable
    

    def curriculum_compactness_move(self, timetable, i):
        block = random.choice(self.blocks)

        isolated_events = []
        events = []
        for event_name in block["Events"]:
            for ev in get_events_by_name(event_name, timetable):
                events.append(ev)
        
        for j, event in enumerate(events):
            if j+1 < len(events) and not(event["WeekDay"] == events[j+1]["WeekDay"] and abs(ev["Timeslot"] - events[j+1]["Timeslot"]) == 1):
                if event in timetable[i:]:
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
        available_rooms = find_available_rooms(event_to_move["Capacity"], self.rooms, timetable, [(new_weekday, new_timeslot)])

        if available_rooms.values() == [set()]: return None
        
        for new_room in list(list(available_rooms.values())[0]):
            if self.conflicts_checker.check_event_hard_constraints(event_to_move, timetable, new_room, new_timeslot, new_weekday) <= -self.best_result_hard:
                event_to_move["WeekDay"], event_to_move["Timeslot"], event_to_move["RoomId"] = new_weekday, new_timeslot, new_room
                return timetable
        return None

    
    """ def min_working_days_move(self, timetable, i):

        penalized_events = [
            event for event in timetable[i:]
            if self.conflicts_checker.check_min_working_days(event, timetable[i:], event["WeekDay"]) > 0
        ]

        if not penalized_events: return None

        event_to_move = random.choice(penalized_events)
        all_course = get_events_by_name(event_to_move["Name"], timetable)
        course = get_events_by_name(event_to_move["Name"], timetable[i:])

        events_by_day = {}
        for event in all_course:
            if event["WeekDay"] not in events_by_day:
                events_by_day[event["WeekDay"]] = []
            events_by_day[event["WeekDay"]].append(event)

        candidate_days = [day for day, events in events_by_day.items() if len(events) > 1]
        if not candidate_days:
            return None

        source_day = random.choice(candidate_days)
        events_to_move = [event for event in events_by_day[source_day] if event in course]

        if not events_to_move:
            return None
        
        event_to_move = random.choice(events_to_move)

        all_days = set(range(5))
        taught_days = set(events_by_day.keys())
        available_days = all_days - taught_days

        if not available_days:
            return None

        new_weekday = random.choice(list(available_days))

        if self.conflicts_checker.check_event_hard_constraints(event_to_move, timetable, event_to_move["RoomId"], event_to_move["Timeslot"], new_weekday) <= -self.best_result_hard:
            event_to_move["WeekDay"] = new_weekday
            return timetable

        return None """


    def run_hill_climbing(self, timetable, i, best_result_hard, best_result_soft, max_idle_iterations):
        self.best_result_hard = best_result_hard
        self.best_result_soft = best_result_soft

        neighborhoods = [self.period_move, self.room_move, self.event_move, self.room_stability_move, self.curriculum_compactness_move]
        idle_iterations = 0
        best_timetable = copy(timetable)

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
                        write_best_simulation_result_to_file(best_timetable, file)
                    idle_iterations = 0
                else:
                    idle_iterations += 1
            else:
                idle_iterations += 1

        return best_timetable, self.best_result_hard, self.best_result_soft
