import math

class MCTSNode:

    def __init__(self, expansion_limit, assignment = None, path = {}, parent = None):
        self.parent = parent
        self.children = []
        self.path = path
        self.visits = 0
        self.score_hard = 0
        self.score_soft = 0
        self.best_hard_penalty = float("-inf")
        self.best_soft_penalty = float("-inf")
        self.expansion_limit = expansion_limit
        self.assignment = assignment
    

    def depth(self):
        return len(self.path)
    

    def is_fully_expanded(self):
        return self.expansion_limit == 0 or len(self.children) == self.expansion_limit


    def is_terminal_node(self, num_events):
        return self.expansion_limit == 0 or self.depth() == num_events
    

    def best_child(self, unflagged_children, c_param):
        choices_weights = [
            child.score_hard / child.visits + 2 * c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in unflagged_children
        ]

        max_weight = max(choices_weights)
        best_children = [unflagged_children[i] for i, weight in enumerate(choices_weights) if weight == max_weight]

        choices_weights = [
            child.score_soft / child.visits + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in best_children
        ]

        return best_children[choices_weights.index(max(choices_weights))]
