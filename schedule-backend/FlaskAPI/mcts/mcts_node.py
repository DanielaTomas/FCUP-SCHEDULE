from copy import deepcopy
import math
from mcts.random_data import *

class MCTSNode:

    def __init__(self, timetable, parent = None, depth = 0):
        self.timetable = deepcopy(timetable)
        self.parent = parent
        self.depth = depth
        self.children = []
        self.path = []
        self.visits = 0
        self.score = 0
    
    
    def is_fully_expanded(self,events_to_visit):
        event = events_to_visit[self.depth]
        
        start_of_day, lunch_end, latest_start_morning, latest_start_afternoon = calculate_time_bounds(event["Duration"])
        valid_start_slots = get_valid_start_slots(
            start_of_day, lunch_end, latest_start_morning, latest_start_afternoon
        )

        if event["RoomId"] is None:
            available_rooms = empty_rooms(self.timetable["occupations"], self.timetable["events"], event, self.timetable["rooms"])
            num_rooms = len(available_rooms)
        else:
            num_rooms = 1

        return len(self.children) >= len(valid_start_slots)*5*num_rooms
        

    def best_child(self, c_param = 1.4):
        choices_weights = [
            (child.score / child.visits) + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]