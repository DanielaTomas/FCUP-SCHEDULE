from copy import deepcopy
import math

class MCTSNodeLocalSearch:

    def __init__(self, timetable, changedEvents = [], parent = None):
        self.timetable = deepcopy(timetable) #TODO keeping deepcopy for now
        self.changedEvents = changedEvents
        self.parent = parent
        self.children = []
        self.visits = 0
        self.score = 0

    def is_fully_expanded(self):
        return len(self.children) > 0

    def best_child(self, c_param = 1.4):
        choices_weights = [
            (child.score / child.visits) + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]