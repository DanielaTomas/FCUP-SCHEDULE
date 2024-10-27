from mcts_itc.utils import get_events_by_name
from mcts_itc.macros import HARD_PENALTY, MIN_WORKING_DAYS_PENALTY, CURRICULUM_COMPACTNESS_PENALTY, ROOM_STABILITY_PENALTY, ROOM_CAPACITY_PENALTY

class ConflictsChecker:

    def __init__(self, constraints, blocks, rooms):
        self.constraints = constraints
        self.blocks = blocks
        self.rooms = rooms


    @staticmethod
    def check_conflict_time(other, timeslot, weekday):
        if other["Timeslot"] is None or other["WeekDay"] is None:
            return False
        return other["WeekDay"] == weekday and other["Timeslot"] == timeslot


    def check_event_hard_constraints(self, event, other_events, room_id, timeslot, weekday):
        penalty = 0
        penalty += self.check_event_unavailability_constraints(event, timeslot, weekday)
        penalty += self.check_block_constraints(event, other_events, timeslot, weekday)
        
        for other_event in other_events:
            if other_event["Id"] != event["Id"] and self.check_conflict_time(other_event, timeslot, weekday):
                if other_event['Name'] == event["Name"]:
                    penalty += HARD_PENALTY
                if other_event['RoomId'] == room_id:
                    penalty += HARD_PENALTY
                if other_event["Teacher"] == event["Teacher"]:
                    penalty += HARD_PENALTY
        return penalty


    def check_event_unavailability_constraints(self, event, timeslot, weekday):
        penalty = 0
        for constraint in self.constraints:
            if constraint["Id"] == event["Name"] and self.check_conflict_time(constraint, timeslot, weekday):
                penalty += HARD_PENALTY
        return penalty


    def check_block_constraints(self, event, other_events, timeslot, weekday):
        penalty = 0
        for block in self.blocks:
            if event["Name"] in block["Events"]:
                for e_name in block["Events"]:
                    evs = get_events_by_name(e_name, other_events)
                    for ev in evs:
                        if ev["Id"] != event["Id"] and self.check_conflict_time(ev, timeslot, weekday):
                            penalty += HARD_PENALTY
        return penalty


    # Soft Constraints:


    def check_min_working_days(self, event, events, weekday):
        penalty = 0
        event_days = {ev["WeekDay"] for ev in events if ev["Name"] == event["Name"] and ev["Id"] != event["Id"]}
        event_days.add(weekday)
        if len(event_days) < event["MinWorkingDays"]:
            penalty += (event["MinWorkingDays"] - len(event_days)) * MIN_WORKING_DAYS_PENALTY
        return penalty


    def check_block_compactness(self, event, other_events, timeslot, weekday):
        penalty = 0
        for block in self.blocks:
            if event["Name"] in block["Events"]:
                adjacent_found = False

                for e_name in block["Events"]:
                    evs = get_events_by_name(e_name, other_events)
                    for ev in evs:
                        if ev["Id"] != event["Id"] and ev["WeekDay"] == weekday and abs(timeslot - ev["Timeslot"]) == 1:
                            adjacent_found = True
                            break
                    
                    if adjacent_found:
                        break
                
                if not adjacent_found:
                    penalty += CURRICULUM_COMPACTNESS_PENALTY
        return penalty


    def check_room_stability(self, event, other_events, room_id):
        different_rooms = set()
        for other_event in other_events:
            if other_event["Id"] != event["Id"] and other_event["Name"] == event["Name"] and other_event["RoomId"] != room_id:
                different_rooms.add(other_event["RoomId"])
        return len(different_rooms)
    
    
    def check_room_capacity(self, event, room_id):
        penalty = 0
        for room in self.rooms:
            if room["Id"] == room_id and room["Capacity"] < event["Capacity"]:
                penalty += (event["Capacity"]-room["Capacity"])
                break
        return penalty

'''
    def get_max_penalies(self, events): #FIXME

        def max_conflict_violations(events): #Lectures, RoomOccupancy, SameTeacher
            return ((len(events)) + (len(events) - 1)*2) * HARD_PENALTY

        def max_curriculum_violations(blocks):
            return (sum(len(block["Events"]) - 1 for block in blocks)) * HARD_PENALTY
        
        def max_unavailability_violations(constraints):
            return len(constraints) * HARD_PENALTY
        
        def max_room_capacity_violations(events):
            smallest_room_capacity = min(room["Capacity"] for room in self.rooms)
            return sum(max(0, event["Capacity"] - smallest_room_capacity) * ROOM_CAPACITY_PENALTY for event in events)
        
        def max_room_stability_violations(blocks):
            return sum((len(block["Events"]) - 1) * ROOM_STABILITY_PENALTY for block in blocks)
    
        def max_curriculum_compactness_violations(blocks):
            return sum((len(block["Events"]) - 1) * CURRICULUM_COMPACTNESS_PENALTY for block in blocks)
        
        def max_min_working_days_violations(events):
            return sum((event["MinWorkingDays"]) * MIN_WORKING_DAYS_PENALTY for event in events)
        
        max_hard_penalty = 0
        max_hard_penalty += max_conflict_violations(events)
        max_hard_penalty += max_curriculum_violations(self.blocks)
        max_hard_penalty += max_unavailability_violations(self.constraints)

        max_soft_penalty = 0
        max_soft_penalty += max_room_capacity_violations(events)
        max_soft_penalty += max_room_stability_violations(self.blocks)
        max_soft_penalty += max_curriculum_compactness_violations(self.blocks)
        max_soft_penalty += max_min_working_days_violations(events)

        print(f"{max_hard_penalty} {max_soft_penalty}")

        return max_hard_penalty, max_soft_penalty
'''