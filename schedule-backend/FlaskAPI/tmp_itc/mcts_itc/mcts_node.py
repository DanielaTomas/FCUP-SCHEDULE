from copy import deepcopy
import math
from mcts_itc.utils import get_valid_periods, find_available_rooms

class MCTSNode:

    def __init__(self, timetable, expansion_limit = None, parent = None, depth = 0):
        self.timetable = deepcopy(timetable)
        self.parent = parent
        self.depth = depth
        self.children = []
        self.path = []
        self.visits = 0
        self.score = 0
        self.expansion_limit = expansion_limit
    
    
    def is_fully_expanded(self):
        if self.depth >= len(self.timetable["events"]):
            return True
        
        if self.expansion_limit == None: #root
            event = self.timetable["events"][self.depth]
            available_periods = get_valid_periods(event, self.timetable["constraints"])
            available_rooms = find_available_rooms(event, self.timetable["rooms"], self.timetable["events"][:self.depth], available_periods)
            available_rooms_list = list(list(available_rooms.values())[0])
            self.expansion_limit = len(available_periods) * len(available_rooms_list)

        return len(self.children) < self.expansion_limit
        

    def best_child(self, c_param = 1.4):
        choices_weights = [
            (child.score / child.visits) + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]