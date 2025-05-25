import math

class MCTSNode:
    """
    Represents a node in the Monte Carlo Tree Search (MCTS) for solving
    scheduling or planning problems with hard and soft constraints.
    """

    def __init__(self, expansion_limit, assignment = None, path = {}, parent = None):
        """
        Initializes an MCTSNode.

        Args:
            expansion_limit (int): The number of children a node can expand to.
            assignment (any, optional): The current assignment or decision at this node.
            path (dict, optional): A dictionary representing the sequence of assignments.
            parent (MCTSNode, optional): Reference to the parent node.
        """
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
        """
        Returns:
            int: Depth of the current node (number of decisions made).
        """
        return len(self.path)
    

    def is_fully_expanded(self):
        """
        Checks if the node has reached its expansion limit.

        Returns:
            bool: True if no more children can be added.
        """
        return self.expansion_limit == 0 or len(self.children) == self.expansion_limit


    def is_terminal_node(self, num_events):
        """
        Determines if the node is a terminal node (i.e., full assignment path).

        Args:
            num_events (int): Total number of decisions to be made in the problem.

        Returns:
            bool: True if node is terminal (end of a full path).
        """
        return self.expansion_limit == 0 or self.depth() == num_events
    

    def best_child(self, unflagged_children, c_param):
        """
        Selects the best child node using UCT.

        Args:
            unflagged_children (list of MCTSNode): Candidate child nodes.
            c_param (float): Exploration-exploitation trade-off parameter.

        Returns:
            MCTSNode: The best child node to explore.
        """
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
