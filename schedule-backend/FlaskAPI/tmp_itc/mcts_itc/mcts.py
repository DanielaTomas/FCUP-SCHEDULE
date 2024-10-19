from copy import deepcopy
from mcts_itc.random_data import *
from mcts_itc.mcts_node import *
from mcts_itc.utils import *
from mcts_itc.check_conflicts import *
import time

#TODO remove prints

class MCTS:

    def __init__(self, current_timetable):
        current_timetable["events"] = add_event_ids(current_timetable["events"])
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

        available_slots = get_valid_slots(event,self.current_node.timetable["constraints"])
        slot = len(self.current_node.children)
        slot_index = slot % len(available_slots)
        new_weekday, new_period = available_slots[slot_index]

        available_rooms = empty_rooms(self.current_node.timetable["events"], event, self.current_node.timetable["rooms"])
        new_room = available_rooms[(slot // len(available_slots)) % len(available_rooms)]
        
        new_timetable = deepcopy(self.current_node.timetable)
        new_event = update_event(event["Id"], new_timetable["events"], new_room, new_weekday, new_period)

        child_node = MCTSNode(timetable=new_timetable, parent=self.current_node, depth=self.current_node.depth+1)
        child_node.path = self.current_node.path + [new_event]
        self.current_node.children.append(child_node)
        self.current_node = child_node


    def simulation(self):

        def find_best_room_and_slot(event):
            best_slot = None
            best_penalty = float('inf')
            available_rooms = empty_rooms(simulated_timetable["events"][:self.current_node.depth], event, simulated_timetable["rooms"])
            for weekday in range(weekday_range):
                for period in range(period_range):
                    for room in available_rooms:
                        if check_event_hard_constraints(event, simulated_timetable["constraints"], simulated_timetable["blocks"], simulated_timetable["events"][:self.current_node.depth], room, period, weekday) == 0:
                            soft_penalty = check_event_soft_constraints(event, simulated_timetable["blocks"], simulated_timetable["rooms"], simulated_timetable["events"][:self.current_node.depth], room, period, weekday)
                            if soft_penalty < best_penalty:
                                best_penalty = soft_penalty
                                best_slot = (room, weekday, period)
                                if best_penalty == 0:
                                    return best_slot
            return best_slot
        

        def evaluate_timetable(simulated_timetable):
            penalty = 0
            for i, event in enumerate(simulated_timetable["events"]):
                penalty += check_event_hard_constraints(event, simulated_timetable["constraints"], simulated_timetable["blocks"], simulated_timetable["events"][i+1:], event["RoomId"], event["Period"], event["WeekDay"])
                penalty += check_event_soft_constraints(event, simulated_timetable["blocks"], simulated_timetable["rooms"], simulated_timetable["events"][i+1:], event["RoomId"], event["Period"], event["WeekDay"])
            return -penalty
        
        simulated_timetable = deepcopy(self.current_node.timetable)
        for event in self.current_node.timetable["events"][self.current_node.depth:]:
            best_room_and_slot = find_best_room_and_slot(event)                   
            if best_room_and_slot:
                update_event(event["Id"], simulated_timetable["events"], best_room_and_slot[0], best_room_and_slot[1], best_room_and_slot[2])
            else:
                random_period, random_weekday = random_time()
                rand_room = random_room()
                update_event(event["Id"], simulated_timetable["events"], rand_room, random_weekday, random_period)

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

        for _ in range(iterations):
            self.selection()
            if self.current_node.depth == len(self.current_node.timetable["events"]) or time.time() - start_time > time_limit: break
            self.expansion()
            simulation_result = self.simulation()
            self.backpropagation(simulation_result)
        
        return self.get_best_solution(time.time() - start_time)
    

    def get_best_solution(self, time):
        def select_best_terminal_node(node):
            if not node.children:
                return node
            best_child = max(node.children, key=lambda child: (child.score / child.visits if child.visits > 0 else float('-inf'), child.visits))
            return select_best_terminal_node(best_child)

        file = open('tree.txt', 'w')
        file.write(f"Time: ~{time}\n")
        write_node_scores_to_file(self.root, file)
        file.close()
        #print_node_scores(self.root)
        best_terminal_node = select_best_terminal_node(self.root)

        return best_terminal_node.path