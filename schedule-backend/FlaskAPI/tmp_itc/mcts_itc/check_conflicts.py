from mcts_itc.utils import get_events_by_name
from mcts_itc.macros import HARD_PENALTY

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


    def check_event_soft_constraints(self, event, other_events, room_id, timeslot, weekday):
        penalty = 0
        penalty += self.check_min_working_days(event, other_events, weekday)
        penalty += self.check_block_compactness(event, other_events, timeslot, weekday)
        penalty += self.check_room_stability(event, other_events, room_id)
        penalty += self.check_room_capacity(event, room_id)
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


    def check_min_working_days(self, event, events, weekday):
        penalty = 0
        event_days = {ev["WeekDay"] for ev in events if ev["Name"] == event["Name"] and ev["Id"] != event["Id"]}
        event_days.add(weekday)
        if len(event_days) < event["MinWorkingDays"]:
            penalty += (event["MinWorkingDays"] - len(event_days)) * 5
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
                    penalty += 2
        return penalty


    def check_room_stability(self, event, other_events, room_id):
        penalty = 0
        for other_event in other_events:
            if other_event["Id"] != event["Id"] and other_event["Name"] == event["Name"] and other_event["RoomId"] != room_id:
                penalty += 1
        return penalty
    
    
    def check_room_capacity(self, event, room_id):
        penalty = 0
        for room in self.rooms:
            if room["Id"] == room_id and room["Capacity"] < event["Capacity"]:
                penalty += (event["Capacity"]-room["Capacity"])
        return penalty
