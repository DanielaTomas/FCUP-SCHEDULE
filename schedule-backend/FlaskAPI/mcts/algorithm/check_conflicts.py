from algorithm.macros import HARD_PENALTY, MIN_WORKING_DAYS_PENALTY, CURRICULUM_COMPACTNESS_PENALTY

class ConflictsChecker:
    """
    Class responsible for checking hard and soft constraints for event scheduling.
    """

    def __init__(self, constraints, blocks, rooms, name_to_event_ids):
        """
        Initializes the ConflictsChecker.

        Args:
            constraints (dict): Mapping of event names to unavailable (WeekDay, Timeslot) constraints.
            blocks (dict): Curriculum blocks grouping related events.
            rooms (dict): Mapping of room IDs to room properties.
            name_to_event_ids (dict): Mapping of event names to assigned unique event IDs.
        """
        self.constraints = constraints
        self.blocks = blocks.values()
        self.rooms = rooms
        self.name_to_event_ids = name_to_event_ids


    @staticmethod
    def check_conflict_time(other, timeslot, weekday):
        """
        Checks if the given event conflicts with a certain period.

        Args:
            other (dict): The event to check.
            timeslot (int): The timeslot in question.
            weekday (int): The weekday in question.

        Returns:
            bool: True if there is a time conflict.
        """
        if other["Timeslot"] is None or other["WeekDay"] is None:
            return False
        return other["WeekDay"] == weekday and other["Timeslot"] == timeslot


    # Hard Constraints:
    
    def check_event_hard_constraints(self, event, other_events, room_id, timeslot, weekday, room_conflicts = None):
        """
        Checks all hard constraints for a given event.

        Args:
            event (dict): Event being evaluated.
            other_events (dict): All other scheduled events.
            room_id (str): Room ID for this event.
            timeslot (int): Timeslot being evaluated.
            weekday (int): Weekday being evaluated.
            room_conflicts (dict, optional): Dictionary to record room conflicts.

        Returns:
            int: Accumulated penalty for all violated hard constraints.
        """
        if timeslot is None or weekday is None or room_id is None: return HARD_PENALTY

        penalty = (
            self.check_event_unavailability_constraints(event, timeslot, weekday)
            + self.check_block_constraints(event, other_events, timeslot, weekday)
        )
        
        for other_event in other_events.values():
            if other_event["Id"] != event["Id"] and self.check_conflict_time(other_event, timeslot, weekday):
                if other_event['Name'] == event["Name"]:
                    penalty += HARD_PENALTY
                else:
                    if other_event['RoomId'] == room_id:
                        if room_conflicts is not None: self.room_conflicts(other_event, room_conflicts)
                        else: penalty += HARD_PENALTY
                    if other_event["Teacher"] == event["Teacher"]:
                        penalty += HARD_PENALTY
        return penalty
    

    def check_event_unavailability_constraints(self, event, timeslot, weekday):
        """
        Checks if the event is scheduled during an unavailable period.

        Args:
            event (dict): Event to check.
            timeslot (int): Timeslot being evaluated.
            weekday (int): Weekday being evaluated.

        Returns:
            int: Penalty if scheduled in restricted time.
        """
        penalty = 0
        event_constraints = self.constraints.get(event["Name"], [])

        for constraint in event_constraints:
            if self.check_conflict_time(constraint, timeslot, weekday):
                penalty += HARD_PENALTY
        return penalty
    

    def check_block_constraints(self, event, other_events, timeslot, weekday):
        """
        Ensures no two events from the same block are scheduled simultaneously.

        Args:
            event (dict): Event to check.
            other_events (dict): All scheduled events.
            timeslot (int): Timeslot being evaluated.
            weekday (int): Weekday being evaluated.

        Returns:
            int: Number of block conflicts.
        """
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
        """
        Sums penalties from detected room conflicts.

        Args:
            room_conflicts (dict): Recorded room conflicts.

        Returns:
            int: Total room conflict penalty.
        """
        penalty = 0
        for room_penalty in room_conflicts.values():
            penalty += room_penalty
        return penalty
    

    def room_conflicts(self, other_event, room_conflicts):
        """
        Registers a room conflict in the room_conflicts dictionary.

        Args:
            other_event (dict): Event already using the room.
            room_conflicts (dict): Dictionary to track room conflicts.
        """
        conflict_key = (other_event['Id'], other_event['RoomId'], other_event["WeekDay"], other_event["Timeslot"])
        if conflict_key not in room_conflicts:
            room_conflicts[conflict_key] = HARD_PENALTY


    # Soft Constraints:


    def check_min_working_days(self, event, events, weekday):
        """
        Ensures that an event is distributed across the required minimum number of working days.

        Args:
            event (dict): Event being evaluated.
            events (dict): All other events.
            weekday (int): Day of the current event.

        Returns:
            int: Penalty based on how many working days are missing.
        """
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
        """
        Encourages compact schedules by penalizing isolated events in a block.

        Args:
            event (dict): Event to evaluate.
            other_events (dict): All other events.
            timeslot (int): Timeslot for this event.
            weekday (int): Weekday for this event.

        Returns:
            int: Penalty if no adjacent block event is found.
        """
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
        """
        Encourages assigning the same room to all lectures of an event.

        Args:
            event (dict): Event to evaluate.
            other_events (dict): All other events.
            room_id (str): Current room ID.

        Returns:
            int: Number of different rooms used (acts as penalty).
        """
        if room_id is None: return 0
        different_rooms = set()
        evs = self.name_to_event_ids.get(event["Name"])

        for ev in evs:
            ev = other_events.get(ev)
            if ev is not None and ev["RoomId"] is not None and ev["Id"] != event["Id"] and ev["RoomId"] != room_id:
                different_rooms.add(ev["RoomId"])
        return len(different_rooms)
    
    
    def check_room_capacity(self, event, room_id):
        """
        Checks whether the room can accommodate the event.

        Args:
            event (dict): Event being evaluated.
            room_id (str): Room to check.

        Returns:
            int: Penalty for under-capacity rooms.
        """
        room = self.rooms.get(room_id)
        if room is None: return 0
        if room["Capacity"] < event["Capacity"]:
            return event["Capacity"] - room["Capacity"]
        return 0