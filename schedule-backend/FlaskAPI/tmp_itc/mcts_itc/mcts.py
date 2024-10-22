from copy import deepcopy
from mcts_itc.mcts_node import *
from mcts_itc.utils import *
from mcts_itc.check_conflicts import ConflictsChecker
from mcts_itc.macros import HARD_WEIGHT
import time

#TODO remove prints

class MCTS:

    def __init__(self, current_timetable):
        current_timetable["events"] = add_event_ids(current_timetable["events"], current_timetable["blocks"], current_timetable["constraints"])
        self.conflicts_checker = ConflictsChecker(current_timetable["constraints"], current_timetable["blocks"], current_timetable["rooms"])
        self.root = MCTSNode(current_timetable)
        self.current_node = self.root
        self.best_result = float('-inf')
    

    # MCTS steps:

    
    def selection(self):
        current_node = self.root
        while not current_node.is_fully_expanded():
            current_node = current_node.best_child()
        self.current_node = current_node


    def expansion(self):
        event = self.current_node.timetable["events"][self.current_node.depth]

        available_periods = get_valid_periods(event,self.current_node.timetable["constraints"])
        period = len(self.current_node.children)
        period_index = period % len(available_periods)
        new_weekday, new_timeslot = available_periods[period_index]

        available_rooms = find_available_rooms(event, self.current_node.timetable["rooms"], self.current_node.timetable["events"][:self.current_node.depth], [available_periods[period_index]])
        available_rooms_list = list(list(available_rooms.values())[0])
        new_room_index = period // len(available_periods) % len(available_rooms_list)
        new_room = available_rooms_list[new_room_index]
        
        new_timetable = deepcopy(self.current_node.timetable)
        new_event = update_event(event["Id"], new_timetable["events"], new_room, new_weekday, new_timeslot)

        child_node = MCTSNode(timetable=new_timetable, expansion_limit=(len(available_periods)*len(available_rooms_list)), parent=self.current_node, depth=self.current_node.depth+1)
        child_node.path = self.current_node.path + [new_event]
        self.current_node.children.append(child_node)
        self.current_node = child_node


    def simulation(self):

        def find_best_room_and_slot(event,i):
            best_room_and_slot = None
            least_conflict_slot = None
            best_soft_penalty = float('inf')
            least_conflict_penalty = float('inf')
            available_periods = get_valid_periods(event,self.current_node.timetable["constraints"])
            
            for available_period in available_periods:
                weekday, timeslot = available_period
                available_rooms = find_available_rooms(event, simulated_timetable["rooms"], simulated_timetable["events"][:i], [available_period])
                available_rooms_list = list(list(available_rooms.values())[0])
                for room in available_rooms_list:
                    hard_penalty = self.conflicts_checker.check_event_hard_constraints(event, simulated_timetable["events"][:i], room, timeslot, weekday)
                    soft_penalty = self.conflicts_checker.check_event_soft_constraints(event, simulated_timetable["events"][:i], room, timeslot, weekday)
                    total_penalty = HARD_WEIGHT*hard_penalty + soft_penalty

                    if hard_penalty == 0 and soft_penalty < best_soft_penalty:
                        best_soft_penalty = soft_penalty
                        best_room_and_slot = (room, weekday, timeslot)
                        if best_soft_penalty == 0:
                            return best_room_and_slot
                    elif best_room_and_slot is None and total_penalty < least_conflict_penalty:
                        least_conflict_penalty = total_penalty
                        least_conflict_slot = (room, weekday, timeslot)
                            
            return best_room_and_slot if best_room_and_slot else least_conflict_slot
        

        def evaluate_timetable(simulated_timetable):
            hard_penalty = 0
            soft_penalty = 0
            for i, event in enumerate(simulated_timetable["events"]):
                hard_penalty += self.conflicts_checker.check_event_hard_constraints(event, simulated_timetable["events"][i+1:], event["RoomId"], event["Timeslot"], event["WeekDay"])
                soft_penalty += self.conflicts_checker.check_event_soft_constraints(event, simulated_timetable["events"][i+1:], event["RoomId"], event["Timeslot"], event["WeekDay"])
            return -hard_penalty, -soft_penalty
        
        
        simulated_timetable = deepcopy(self.current_node.timetable)
        for i, event in enumerate(self.current_node.timetable["events"][self.current_node.depth:]):
            best_room_and_slot = find_best_room_and_slot(event,i+self.current_node.depth)                   
            update_event(event["Id"], simulated_timetable["events"], best_room_and_slot[0], best_room_and_slot[1], best_room_and_slot[2])

        hard_penalty_result, soft_penalty_result = evaluate_timetable(simulated_timetable)
        result = HARD_WEIGHT*hard_penalty_result + soft_penalty_result
        if result > self.best_result:
            self.best_result = result
            file = open('output.txt', 'w')
            write_best_simulation_result_to_file(simulated_timetable["events"], file)
            file.close()

        return result
    

    def backpropagation(self, simulation_result):
        node = self.current_node
        while node is not None:
            node.visits += 1
            node.score += simulation_result
            node = node.parent


    def run_mcts(self, iterations=1500, time_limit=600):

        def get_best_solution(time):
            def select_best_terminal_node(node):
                if not node.children:
                    return node
                best_child = max(node.children, key=lambda child: (child.score / child.visits if child.visits > 0 else float('-inf'), child.visits))
                return select_best_terminal_node(best_child)

            file = open('tree.txt', 'w')
            file.write(f"Time: ~{time}\n")
            write_node_scores_to_file(self.root, file)
            file.close()
            best_terminal_node = select_best_terminal_node(self.root)

            return best_terminal_node.path

        start_time = time.time()
        for _ in range(iterations):
            self.selection()
            duration = time.time() - start_time
            if self.current_node.depth == len(self.current_node.timetable["events"]) or duration > time_limit: break
            self.expansion()
            simulation_result = self.simulation()
            self.backpropagation(simulation_result)
        
        return get_best_solution(duration)
