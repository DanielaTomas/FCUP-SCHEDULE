from copy import deepcopy
import math
from mcts_itc.random_data import *

valid_start_slots = [0,1,2,3]

class MCTSNode:

    def __init__(self, timetable, parent = None, depth = 0):
        self.timetable = deepcopy(timetable)
        self.parent = parent
        self.depth = depth
        self.children = []
        self.path = []
        self.visits = 0
        self.score = 0
    
    
    def is_fully_expanded(self):

        if self.depth >= len(self.timetable["events"]):
            return True

        event = self.timetable["events"][self.depth]

        if event["RoomId"] is None:
            available_rooms = empty_rooms(self.timetable["events"], event, self.timetable["rooms"])
            num_rooms = len(available_rooms)
        else:
            num_rooms = 1
        return len(self.children) < len(valid_start_slots)*5*num_rooms
        

    def best_child(self, c_param = 1.4):
        choices_weights = [
            (child.score / child.visits) + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]