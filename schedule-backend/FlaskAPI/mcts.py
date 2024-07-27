from copy import deepcopy
from random_data import *

class MCTS:

    def __init__(self, current_timetable):

        self.timetable = deepcopy(current_timetable)

        self.events = self.timetable["events"]
        self.rooms = self.timetable["rooms"]
        self.lecturers = self.timetable["lecturers"]
        self.restrictions = self.timetable["restrictions"]
        self.occupations = self.timetable["occupations"]

        self.calculate_event_durations()
        
        self.scores = []
        self.best_score = float('-inf')
        self.best_timetable = None


    def calculate_event_durations(self):
        for event in self.events:
            start_time = event["StartTime"]
            end_of_day = event["EndTime"]
            if start_time is not None and end_of_day is not None:
                duration = (end_of_day - start_time).total_seconds() / 60.0
                event["Duration"] = duration
            else:
                event["Duration"] = 60 #TODO adjust default duration if necessary


    def get_room_name_by_id(self, room_id):
        for room in self.rooms:
            if room["Id"] == room_id:
                return room["Name"]
        return "Room Not Found"
    

    def evaluate_timetable(self): # conflitos
        penalty = 0
        for event in self.events:
            room = event["RoomId"]
            start_time = event["StartTime"]
            end_time = event["EndTime"]
            weekday = event["WeekDay"]

            if room and start_time and end_time and weekday:
                for other_event in self.events:
                    if (self.get_room_name_by_id(room) != "DCC online" and 
                        other_event["Id"] != event["Id"] and 
                        other_event["RoomId"] == room and 
                        other_event["WeekDay"] == weekday and 
                        start_time < other_event["EndTime"] and end_time > other_event["StartTime"]):
                            penalty += 1
                lecturer = event["LecturerId"]
                if lecturer:
                    for restriction in self.restrictions:
                        if (restriction["Type"] == 1 and
                            restriction["LecturerId"] == lecturer and 
                            restriction["WeekDay"] == weekday and
                            start_time < restriction["EndTime"] and end_time > restriction["StartTime"]):
                            penalty += 1
        print(penalty)
        return -penalty
    

    #MCTS steps:

    #def selection(self):
        #pass

    def expansion(self):
        event = random_event(self.events)
        #print("old event: ", event)
        new_start_time, new_end_time, new_weekday = random_time(event["Duration"])
        new_room = random_room(self.occupations, self.events, new_start_time, new_end_time, self.rooms)
        event["StartTime"] = new_start_time
        event["EndTime"] = new_end_time
        event["RoomId"] = new_room["Id"]
        event["WeekDay"] = new_weekday
        #print("new event: ", event)

    def simulation(self):
        return self.evaluate_timetable()

    def backpropagation(self, simulation_result):
        self.scores.append(simulation_result)
        pass

    def run_mcts(self, iterations=10):
        for _ in range(iterations):
            #self.selection()
            self.expansion()
            simulation_result = self.simulation()
            self.backpropagation(simulation_result)
        return self.get_best_solution()

    def get_best_solution(self):
        if self.scores:
            best_score_index = self.scores.index(max(self.scores))
            #TODO tree structure
            return self.timetable
        else:
            return self.timetable
