from copy import deepcopy
from mcts_itc.random_data import *
from mcts_itc.mcts_node import *
from mcts_itc.utils import *
from mcts_itc.check_conflicts import *

#TODO remove prints
class MCTS:

    def __init__(self, current_timetable):
        self.timetable = deepcopy(current_timetable)
        events_with_ids = add_event_ids(self.timetable["events"]) #TODO
        self.timetable["events"] = events_with_ids
        current_timetable["events"] = events_with_ids
        self.root = MCTSNode(current_timetable)
        self.current_node = self.root


    def evaluate_timetable(self, timetable):
        penalty = 0
        for i, event in enumerate(timetable["events"]):
            penalty += check_event_conflicts(event,self.timetable["constraints"],self.timetable["blocks"],timetable["events"][i+1:],event["Teacher"],event["Period"],event["WeekDay"])
            penalty += check_min_working_days(event,timetable["events"][i+1:],event["WeekDay"])
        return -penalty
    

    # MCTS steps:

    
    def selection(self):
        current_node = self.root
        while not current_node.is_fully_expanded(self.timetable["events"]):
            current_node = current_node.best_child()
        self.current_node = current_node


    def expansion(self):
        event = deepcopy(self.timetable["events"][self.current_node.depth])

        valid_start_slots = [0,1,2,3]

        slot = len(self.current_node.children)
        slot_index = slot % len(valid_start_slots)
        new_weekday = (slot // len(valid_start_slots)) % 5

        new_period = valid_start_slots[slot_index]

        new_timetable = deepcopy(self.current_node.timetable)
        new_event = update_event(event["Id"], new_timetable["events"], new_weekday, new_period)
        if event["RoomId"] is None:
            rooms = self.timetable["rooms"]
            available_rooms = empty_rooms(self.current_node.timetable["events"], event, rooms)
            new_event["RoomId"] = available_rooms[(slot // (len(valid_start_slots) * 5)) % len(available_rooms)]

        child_node = MCTSNode(timetable=new_timetable, parent=self.current_node, depth=self.current_node.depth+1)
        child_node.path = self.current_node.path + [new_event]
        self.current_node.children.append(child_node)
        self.current_node = child_node


    def simulation(self):
        simulated_timetable = deepcopy(self.current_node.timetable)
        
        valid_start_slots = [0,1,2,3]
        for event in self.timetable["events"][self.current_node.depth:]:
            assigned = False
            for weekday in range(5):
                for period in valid_start_slots:
                    if check_event_conflicts(event,simulated_timetable["constraints"],simulated_timetable["blocks"],simulated_timetable["events"][:(self.current_node.depth)],event["Teacher"],period,weekday) == 0:
                        new_event = update_event(event["Id"],simulated_timetable["events"],weekday,period)
                        assigned = True
                        break
                if assigned:
                    break
            if not assigned:
                random_period, random_weekday = random_time()
                new_event = update_event(event["Id"], simulated_timetable["events"], random_weekday, random_period)
            if event["RoomId"] is None:
                new_event["RoomId"] = random_room(self.current_node.timetable["events"], event, self.timetable["rooms"])
        result = self.evaluate_timetable(simulated_timetable)
        return result
    

    def backpropagation(self, simulation_result):
        node = self.current_node
        while node is not None:
            node.visits += 1
            node.score += simulation_result
            node = node.parent


    def run_mcts(self, iterations=1500):
        for _ in range(iterations):
            self.selection()
            if self.current_node.depth == len(self.timetable["events"]): break
            self.expansion()
            simulation_result = self.simulation()
            self.backpropagation(simulation_result)
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