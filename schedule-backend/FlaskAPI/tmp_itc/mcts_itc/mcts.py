from copy import deepcopy
from mcts_itc.random_data import *
from mcts_itc.mcts_node import *
from mcts_itc.utils import *
from mcts_itc.check_conflicts import *
import time

#TODO remove prints

valid_start_slots = [0,1,2,3]

class MCTS:

    def __init__(self, current_timetable):
        events_with_ids = add_event_ids(current_timetable["events"])
        current_timetable["events"] = events_with_ids
        self.root = MCTSNode(current_timetable)
        self.current_node = self.root
    

    # MCTS steps:

    
    def selection(self):
        current_node = self.root
        while not current_node.is_fully_expanded():
            current_node = current_node.best_child()
        self.current_node = current_node


    def expansion(self):
        event = self.current_node.timetable["events"][self.current_node.depth]

        slot = len(self.current_node.children)
        slot_index = slot % len(valid_start_slots)
        new_weekday = (slot // len(valid_start_slots)) % 5
        new_period = valid_start_slots[slot_index]

        new_timetable = deepcopy(self.current_node.timetable)
        new_event = update_event(event["Id"], new_timetable["events"], new_weekday, new_period)
        if event["RoomId"] is None:
            available_rooms = empty_rooms(self.current_node.timetable["events"], event, self.current_node.timetable["rooms"])
            new_event["RoomId"] = available_rooms[(slot // (len(valid_start_slots) * 5)) % len(available_rooms)]

        child_node = MCTSNode(timetable=new_timetable, parent=self.current_node, depth=self.current_node.depth+1)
        child_node.path = self.current_node.path + [new_event]
        self.current_node.children.append(child_node)
        self.current_node = child_node


    def simulation(self):
        simulated_timetable = deepcopy(self.current_node.timetable)

        def find_best_slot(event, valid_slots):
            best_slot = None
            best_penalty = float('inf')
            for weekday in range(5):
                for period in valid_slots:
                    if check_event_hard_constraints(event, simulated_timetable["constraints"], simulated_timetable["blocks"], simulated_timetable["events"][:self.current_node.depth], period, weekday) == 0:
                        soft_penalty = check_event_soft_constraints(event, simulated_timetable["blocks"], simulated_timetable["events"][:self.current_node.depth], period, weekday)
                        if soft_penalty < best_penalty:
                            best_penalty = soft_penalty
                            best_slot = (weekday, period)
                            if best_penalty == 0:
                                return best_slot
            return best_slot
        
        def evaluate_timetable(simulated_timetable):
            penalty = 0
            for i, event in enumerate(simulated_timetable["events"]):
                penalty += check_event_hard_constraints(event, simulated_timetable["constraints"], simulated_timetable["blocks"], simulated_timetable["events"][i+1:], event["Period"], event["WeekDay"])
                penalty += check_event_soft_constraints(event, simulated_timetable["blocks"], simulated_timetable["events"][i+1:], event["Period"], event["WeekDay"])
            return -penalty
        
        for event in self.current_node.timetable["events"][self.current_node.depth:]:
            best_slot = find_best_slot(event, valid_start_slots)                   
            if best_slot:
                new_event = update_event(event["Id"], simulated_timetable["events"], best_slot[0], best_slot[1])
            else:
                random_period, random_weekday = random_time()
                new_event = update_event(event["Id"], simulated_timetable["events"], random_weekday, random_period)

            if event["RoomId"] is None:
                new_event["RoomId"] = random_room(self.current_node.timetable["events"], event, self.current_node.timetable["rooms"])

        result = evaluate_timetable(simulated_timetable)

        return result
    

    def backpropagation(self, simulation_result):
        node = self.current_node
        while node is not None:
            node.visits += 1
            node.score += simulation_result
            node = node.parent


    def run_mcts(self, iterations=1500, time_limit=600):
        start_time = time.time()

        for i in range(iterations):
            self.selection()
            if self.current_node.depth == len(self.current_node.timetable["events"]) or time.time() - start_time > time_limit: break
            self.expansion()
            simulation_result = self.simulation()
            self.backpropagation(simulation_result)

        print(f"Iterations: {i} Time: ~{time.time() - start_time}")
        return self.get_best_solution()
    

    def get_best_solution(self):
        def select_best_terminal_node(node):
            if not node.children:
                return node
            best_child = max(node.children, key=lambda child: (child.score / child.visits if child.visits > 0 else float('-inf'), child.visits))
            return select_best_terminal_node(best_child)

        print_node_scores(self.root)
        best_terminal_node = select_best_terminal_node(self.root)

        return best_terminal_node.path