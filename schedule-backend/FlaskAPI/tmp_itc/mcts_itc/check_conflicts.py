from mcts_itc.utils import get_events_by_name
from mcts_itc.macros import HARD_PENALTY, MIN_WORKING_DAYS_PENALTY, CURRICULUM_COMPACTNESS_PENALTY #, ROOM_STABILITY_PENALTY, ROOM_CAPACITY_PENALTY

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


    # Hard Constraints:

    
    def check_event_hard_constraints(self, event, other_events, room_id, timeslot, weekday):
        if timeslot is None or weekday is None or room_id is None: return HARD_PENALTY

        penalty = (
            self.check_event_unavailability_constraints(event, timeslot, weekday)
            + self.check_block_constraints(event, other_events, timeslot, weekday)
        )
        
        for other_event in other_events:
            if other_event["Id"] != event["Id"] and self.check_conflict_time(other_event, timeslot, weekday):
                if other_event['Name'] == event["Name"]:
                    penalty += HARD_PENALTY
                else:
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
        conflict = set()
        for block in self.blocks:
            if event["Name"] in block["Events"]:
                for e_name in block["Events"]:
                    evs = get_events_by_name(e_name, other_events)
                    for ev in evs:
                        if ev["Id"] != event["Id"] and self.check_conflict_time(ev, timeslot, weekday):
                            conflict.add((event["Id"], ev["Id"]))
        return len(conflict)


    # Soft Constraints:


    def check_min_working_days(self, event, events, weekday):
        event_days = {ev["WeekDay"] for ev in events if ev["Name"] == event["Name"] and ev["Id"] != event["Id"] and ev["WeekDay"] is not None}
        if weekday is not None:
            event_days.add(weekday)
        if len(event_days) < event["MinWorkingDays"]:
            return (event["MinWorkingDays"] - len(event_days)) * MIN_WORKING_DAYS_PENALTY
        return 0


    def check_block_compactness(self, event, other_events, timeslot, weekday):
        if weekday is None or timeslot is None: return 0
        penalty = 0
        for block in self.blocks:
            if event["Name"] in block["Events"]:
                adjacent_found = False

                for e_name in block["Events"]:
                    for ev in get_events_by_name(e_name, other_events):
                        if ev["Id"] != event["Id"]:
                            if ev["Id"] == event["Id"] or ev["WeekDay"] is None or ev["Timeslot"] is None:
                                continue
                            if ev["WeekDay"] == weekday and abs(timeslot - ev["Timeslot"]) == 1:
                                adjacent_found = True
                                break
                    
                    if adjacent_found:
                        break
                
                if not adjacent_found:
                    penalty += CURRICULUM_COMPACTNESS_PENALTY
        return penalty


    def check_room_stability(self, event, other_events, room_id):
        if room_id is None: return 0
        different_rooms = set()
        for other_event in other_events:
            if other_event["RoomId"] is not None and other_event["Id"] != event["Id"] and other_event["Name"] == event["Name"] and other_event["RoomId"] != room_id:
                different_rooms.add(other_event["RoomId"])
        return len(different_rooms)
    
    
    def check_room_capacity(self, event, room_id):
        for room in self.rooms:
            if room["Id"] == room_id: 
                if room["Capacity"] < event["Capacity"]:
                    return event["Capacity"] - room["Capacity"]
                break
        return 0
