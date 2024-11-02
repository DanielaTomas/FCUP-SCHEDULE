from copy import deepcopy
import math
from mcts_itc.utils import find_available_rooms

class MCTSNode:

    def __init__(self, timetable, expansion_limit = None, parent = None):
        self.timetable = deepcopy(timetable)
        self.parent = parent
        self.children = []
        self.path = []
        self.visits = 0
        self.score_hard = 0
        self.score_soft = 0
        self.best_hard_penalty_result = float("-inf")
        self.best_soft_penalty_result = float("-inf")
        self.expansion_limit = expansion_limit
    

    def depth(self):
        return len(self.path)
    
    
    def is_fully_expanded(self):
        if self.depth() >= len(self.timetable["events"]):
            return True
        
        if self.expansion_limit == None: #root
            event = self.timetable["events"][self.depth()]
            available_rooms = find_available_rooms(event, self.timetable["rooms"], self.timetable["events"][:self.depth()], event["Available_Periods"])
            available_rooms_list = list(list(available_rooms.values())[0])
            self.expansion_limit = len(event["Available_Periods"]) * len(available_rooms_list)

        return len(self.children) < self.expansion_limit
        

    def best_child(self, c_param = 1.4):
        choices_weights = [
            (child.score_hard + child.score_soft) + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]