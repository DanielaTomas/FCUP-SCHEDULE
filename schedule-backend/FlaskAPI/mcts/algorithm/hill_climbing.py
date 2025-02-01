from copy import deepcopy
import random, time
from algorithm.utils import find_available_rooms, write_best_simulation_result_to_file, get_events_by_name, dict_slice
from algorithm.macros import HC_IDLE

class HillClimbing:

    def __init__(self, conflicts_checker, blocks, rooms, days, name_to_event_ids, output_filename="output/output.txt"):
        self.blocks = blocks.values()
        self.rooms = rooms
        self.conflicts_checker = conflicts_checker
        self.days = days
        self.name_to_event_ids = name_to_event_ids
        self.output_filename = output_filename
        self.best_result_soft = float('-inf')
        

    def evaluate_timetable(self, simulated_events):
        soft_penalty = 0
        event_names = []

        for event in simulated_events.values():
            soft_penalty += (
                self.conflicts_checker.check_room_capacity(event, event["RoomId"]) +
                self.conflicts_checker.check_block_compactness(event, simulated_events, event["Timeslot"], event["WeekDay"])
            )
            if event["Name"] not in event_names:
                events_to_check = dict_slice(simulated_events, event["Id"], True)
                soft_penalty += (
                    self.conflicts_checker.check_min_working_days(event, events_to_check, event["WeekDay"]) +
                    self.conflicts_checker.check_room_stability(event, events_to_check, event["RoomId"])
                )
            if -soft_penalty <= self.best_result_soft: return None
            event_names.append(event["Name"])
        return -soft_penalty
    

    def period_move(self, timetable, unscheduled_events):
        random_event = random.choice(list(unscheduled_events.values()))

        for new_period in random_event["Available_Periods"]:
            new_weekday, new_timeslot = new_period
            if new_period != (random_event["WeekDay"], random_event["Timeslot"]) and self.conflicts_checker.check_event_hard_constraints(random_event, timetable, random_event["RoomId"], new_timeslot, new_weekday) == 0:
                random_event["WeekDay"], random_event["Timeslot"] = new_weekday, new_timeslot
                return timetable
        return None


    def room_move(self, timetable, unscheduled_events):
        random_event = random.choice(list(unscheduled_events.values()))

        available_rooms = find_available_rooms(random_event["Capacity"], self.rooms, timetable.values(), [(random_event["WeekDay"], random_event["Timeslot"])])
        if available_rooms.values() != [set()]:
            for new_room in list(list(available_rooms.values())[0]):
                if new_room != random_event["RoomId"] and self.conflicts_checker.check_event_hard_constraints(random_event, timetable, new_room, random_event["Timeslot"], random_event["WeekDay"]) == 0:
                    random_event["RoomId"] = new_room
                    return timetable
        return None


    def event_move(self, timetable, unscheduled_events):
        random_event = random.choice(list(unscheduled_events.values()))

        for new_weekday, new_timeslot in random_event["Available_Periods"]:
            if (new_weekday, new_timeslot) == (random_event["WeekDay"], random_event["Timeslot"]): continue
            available_rooms = find_available_rooms(random_event["Capacity"], self.rooms, timetable.values(), [(new_weekday, new_timeslot)])
            if available_rooms.values() == [set()]: continue

            for new_room in list(list(available_rooms.values())[0]):
                if new_room == random_event["RoomId"]: continue
                elif self.conflicts_checker.check_event_hard_constraints(random_event, timetable, new_room, new_timeslot, new_weekday) == 0:
                    original_weekday, original_timeslot, original_room = random_event["WeekDay"], random_event["Timeslot"], random_event["RoomId"]
                    random_event["WeekDay"], random_event["Timeslot"], random_event["RoomId"] = new_weekday, new_timeslot, new_room

                conflict_event = None
                for event in timetable.values():
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
    

    def room_stability_move(self, timetable, unscheduled_events):
        random_event = random.choice(list(unscheduled_events.values()))

        course_events = self.name_to_event_ids.get(random_event["Name"])
        course_events = [unscheduled_events.get(event_id) for event_id in course_events if event_id in unscheduled_events]

        if len(course_events) < random_event["Lectures"]: return None

        target_room_id = random.choice(list(self.rooms.keys()))

        for e in course_events:
            if e["RoomId"] != target_room_id:
                if self.conflicts_checker.check_event_hard_constraints(e, timetable, target_room_id, e["Timeslot"], e["WeekDay"]) == 0:
                    e["RoomId"] = target_room_id
                else:
                    return None

        return timetable


    def curriculum_compactness_move(self, timetable, unscheduled_events):
        random_block = random.choice(list(self.blocks))

        isolated_events = []
        block_events = []
        for event_name in random_block["Events"]:
            evs = self.name_to_event_ids.get(event_name)
            for ev in evs:
                ev = timetable.get(ev)
                block_events.append(ev)
                if ev["Id"] in unscheduled_events:
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
        available_rooms = find_available_rooms(event_to_move["Capacity"], self.rooms, timetable.values(), [(new_weekday, new_timeslot)])

        if available_rooms.values() == [set()]: return None
        
        for new_room in list(list(available_rooms.values())[0]):
            if self.conflicts_checker.check_event_hard_constraints(event_to_move, timetable, new_room, new_timeslot, new_weekday) == 0:
                event_to_move["WeekDay"], event_to_move["Timeslot"], event_to_move["RoomId"] = new_weekday, new_timeslot, new_room
                return timetable
        return None

    
    def min_working_days_move(self, timetable, unscheduled_events):
        penalized_events = [
            event for event in unscheduled_events.values()
            if self.conflicts_checker.check_min_working_days(event, timetable, event["WeekDay"]) > 0
        ]

        if not penalized_events: return None

        event_to_move = random.choice(penalized_events)

        course = self.name_to_event_ids.get(event_to_move["Name"])
        taught_days = {timetable.get(event_id)["WeekDay"] for event_id in course}

        available_days = set(range(self.days)) - taught_days

        if not available_days:
            return None

        for new_weekday, new_timeslot in event_to_move["Available_Periods"]:
            if new_weekday in available_days:
                available_rooms = find_available_rooms(event_to_move["Capacity"], self.rooms, timetable.values(), [(new_weekday,new_timeslot)])
                if available_rooms.values() == [set()]: return None
                for new_room in list(list(available_rooms.values())[0]):
                    if self.conflicts_checker.check_event_hard_constraints(event_to_move, timetable, new_room, new_timeslot, new_weekday) == 0:
                        event_to_move["WeekDay"], event_to_move["Timeslot"], event_to_move["RoomId"] = new_weekday, new_timeslot, new_room
                        return timetable
        return None


    def run_hill_climbing(self, best_timetable, start_key, best_result_soft, start_time, time_limit):
        self.best_result_soft = best_result_soft

        neighborhoods = [(self.period_move,1), (self.room_move,1), (self.event_move,1), (self.room_stability_move,0.7), (self.min_working_days_move,0.3), (self.curriculum_compactness_move,0.7)]

        idle_iterations = 0

        while idle_iterations < HC_IDLE and (time.time() - start_time <= time_limit):
            current_neighborhood, _ = random.choices(neighborhoods, weights=[weight for _, weight in neighborhoods], k=1)[0]
            timetable = deepcopy(best_timetable)
            unscheduled_events = dict_slice(timetable, start_key)
            modified_timetable = current_neighborhood(timetable, unscheduled_events)

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
                        write_best_simulation_result_to_file(best_timetable.values(), file)
                    idle_iterations = 0
                else:
                    idle_iterations += 1
            else:
                idle_iterations += 1

        return self.best_result_soft
