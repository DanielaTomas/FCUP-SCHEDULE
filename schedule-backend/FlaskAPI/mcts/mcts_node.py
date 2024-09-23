from copy import deepcopy
import math
from mcts.random_data import *

class MCTSNode:

    def __init__(self, timetable, parent = None, depth = 0):
        self.timetable = deepcopy(timetable)
        self.parent = parent
        self.depth = depth
        self.children = []
        self.visits = 0
        self.score = 0
        

    def is_fully_expanded(self, num_slots):
        return len(self.children) == num_slots
    

    def best_child(self, c_param = 1.4):
        choices_weights = [
            (child.score / child.visits) + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]