from algorithm.macros import HARD_PENALTY, MIN_WORKING_DAYS_PENALTY, CURRICULUM_COMPACTNESS_PENALTY

class ConflictsChecker:

    def __init__(self, constraints, blocks, rooms, name_to_event_ids):
        self.constraints = constraints
        self.blocks = blocks.values()
        self.rooms = rooms
        self.name_to_event_ids = name_to_event_ids


    @staticmethod
    def check_conflict_time(other, timeslot, weekday):
        if other["Timeslot"] is None or other["WeekDay"] is None:
            return False
        return other["WeekDay"] == weekday and other["Timeslot"] == timeslot


    # Hard Constraints:
    
    def check_event_hard_constraints(self, event, other_events, timeslot, weekday, room_id = None, room_conflicts = None):
        if timeslot is None or weekday is None: return HARD_PENALTY

        penalty = (
            self.check_event_unavailability_constraints(event, timeslot, weekday)
            + self.check_block_constraints(event, other_events, timeslot, weekday)
        )
        
        for other_event in other_events.values():
            if other_event["Id"] != event["Id"] and self.check_conflict_time(other_event, timeslot, weekday):
                if other_event['Name'] == event["Name"]:
                    penalty += HARD_PENALTY
                else:
                    if room_id is not None and other_event.get("RoomId") is not None and other_event.get("RoomId") == room_id:
                        if room_conflicts is not None: self.room_conflicts(other_event, room_conflicts)
                        else: penalty += HARD_PENALTY
                    if other_event["Teacher"] == event["Teacher"]:
                        penalty += HARD_PENALTY
        return penalty
    

    def check_event_unavailability_constraints(self, event, timeslot, weekday):
        penalty = 0
        event_constraints = self.constraints.get(event["Name"], [])

        for constraint in event_constraints:
            if self.check_conflict_time(constraint, timeslot, weekday):
                penalty += HARD_PENALTY
        return penalty
    

    def check_block_constraints(self, event, other_events, timeslot, weekday):
        conflict = set()
        for block in self.blocks:
            if event["Name"] in block["Events"]:
                for e_name in block["Events"]:
                    evs = self.name_to_event_ids.get(e_name)
                    for ev in evs:
                        ev = other_events.get(ev)
                        if ev is not None and ev["Id"] != event["Id"] and self.check_conflict_time(ev, timeslot, weekday):
                            conflict.add((event["Id"], ev["Id"]))
        return len(conflict)
    

    def check_room_conflicts(self, room_conflicts):
        penalty = 0
        for room_penalty in room_conflicts.values():
            penalty += room_penalty
        return penalty
    

    def room_conflicts(self, other_event, room_conflicts):
            conflict_key = (other_event['Id'], other_event['RoomId'], other_event["WeekDay"], other_event["Timeslot"])
            if conflict_key not in room_conflicts:
                room_conflicts[conflict_key] = HARD_PENALTY


    # Soft Constraints:


    def check_min_working_days(self, event, events, weekday):
        evs = self.name_to_event_ids.get(event["Name"])
        event_days = set()
        for ev in evs:
            ev = events.get(ev, None)
            if ev is not None and ev["WeekDay"] is not None and ev["Id"] != event["Id"]:
                event_days.add(ev["WeekDay"])

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
                    evs = self.name_to_event_ids.get(e_name)
                    for ev in evs:
                        ev = other_events.get(ev)
                        if ev is not None and ev["Id"] != event["Id"]:
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
        evs = self.name_to_event_ids.get(event["Name"])

        for ev in evs:
            ev = other_events.get(ev)
            if ev is not None and ev.get("RoomId") is not None and ev["Id"] != event["Id"] and ev.get("RoomId") != room_id:
                different_rooms.add(ev["RoomId"])
        return len(different_rooms)
    
    
    def check_room_capacity(self, event, room_id):
        room = self.rooms.get(room_id)
        if room is None: return 0
        if room["Capacity"] < event["Capacity"]:
            return event["Capacity"] - room["Capacity"]
        return 0