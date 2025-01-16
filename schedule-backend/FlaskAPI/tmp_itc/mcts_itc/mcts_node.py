from copy import deepcopy
import math

class MCTSNode:

    def __init__(self, timetable, expansion_limit, parent = None):
        self.timetable = deepcopy(timetable)
        self.parent = parent
        self.children = []
        self.path = []
        self.visits = 0
        self.score_hard = 0
        self.score_soft = 0
        self.discrepancy = 0
        self.best_hard_penalty_result = float("-inf")
        self.best_soft_penalty_result = float("-inf")
        self.expansion_limit = expansion_limit
    

    def depth(self):
        return len(self.path)
    

    def is_fully_expanded(self):
        if self.depth() >= len(self.timetable["events"]): return True
        return len(self.children) < self.expansion_limit
        

    def best_child(self, c_param=1.4):
        choices_weights = [
            child.score_hard + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]

        max_weight = max(choices_weights)
        best_children = [self.children[i] for i, weight in enumerate(choices_weights) if weight == max_weight]

        choices_weights = [
            child.score_soft + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in best_children
        ]

        return best_children[choices_weights.index(max(choices_weights))]


    """
    def best_child(self, c_param=1.4, hard_weight=0.7, soft_weight=0.3):
        choices_weights = [
            (hard_weight*child.score_hard + soft_weight*child.score_soft) + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]
    """