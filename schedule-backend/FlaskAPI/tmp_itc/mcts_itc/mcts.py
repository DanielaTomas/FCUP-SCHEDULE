from copy import deepcopy
from mcts_itc.mcts_node import *
from mcts_itc.utils import *
from mcts_itc.check_conflicts import ConflictsChecker
import time

#TODO remove prints

class MCTS:

    def __init__(self, current_timetable):
        current_timetable["events"] = add_event_ids(current_timetable["events"], current_timetable["blocks"], current_timetable["constraints"])
        self.conflicts_checker = ConflictsChecker(current_timetable["constraints"], current_timetable["blocks"], current_timetable["rooms"])
        self.root = MCTSNode(current_timetable)
        self.current_node = self.root

        self.best_result_hard= float('-inf')
        self.best_result_soft = float('-inf')

        self.best_hard_penalty = float('-inf')
        self.worst_hard_penalty = float('inf')
        self.best_soft_penalty = float('-inf')
        self.worst_soft_penalty = float('inf')


    def normalize_hard(self, result):
        if self.best_hard_penalty == self.worst_hard_penalty: return 0.75
        a = (self.worst_hard_penalty - result)/(self.worst_hard_penalty - self.best_hard_penalty)
        return ((math.exp(a) - 1) / (math.e - 1))*0.5 + 0.5


    def normalize_soft(self, result):
        if self.best_soft_penalty == self.worst_soft_penalty: return 0.25
        a = (self.worst_soft_penalty - result)/(self.worst_soft_penalty - self.best_soft_penalty)
        return ((math.exp(a) - 1) / (math.e - 1))*0.5
    
    
    # MCTS steps:

    
    def selection(self):
        current_node = self.root
        while not current_node.is_fully_expanded():
            current_node = current_node.best_child()
        self.current_node = current_node


    def expansion(self):
        event = self.current_node.timetable["events"][self.current_node.depth()]

        available_periods = event["Available_Periods"]
        period = len(self.current_node.children)
        period_index = period % len(available_periods)
        new_weekday, new_timeslot = available_periods[period_index]

        available_rooms = find_available_rooms(event, self.current_node.timetable["rooms"], self.current_node.timetable["events"][:self.current_node.depth()], [available_periods[period_index]])
        available_rooms_list = list(list(available_rooms.values())[0])
        new_room_index = period // len(available_periods) % len(available_rooms_list)
        new_room = available_rooms_list[new_room_index]
        
        new_timetable = deepcopy(self.current_node.timetable)
        new_event = update_event(event["Id"], new_timetable["events"], new_room, new_weekday, new_timeslot)

        child_node = MCTSNode(timetable=new_timetable, expansion_limit=(len(available_periods)*len(available_rooms_list)), parent=self.current_node)
        child_node.path = self.current_node.path + [new_event]
        self.current_node.children.append(child_node)
        self.current_node = child_node


    def simulation(self):

        def find_best_room_and_period(event,i):
            best_room_and_period = None
            least_conflict_room_and_period = None
            min_soft_penalty = float('inf')
            least_conflict_hard_penalty = float('inf')
            least_conflict_soft_penalty = float('inf')

            for available_period in event["Available_Periods"]:
                weekday, timeslot = available_period
                available_rooms = find_available_rooms(event, simulated_timetable["rooms"], simulated_timetable["events"][:i], [available_period])
                
                for room in list(list(available_rooms.values())[0]):
                    hard_penalty = self.conflicts_checker.check_event_hard_constraints(event, simulated_timetable["events"][:i], room, timeslot, weekday)
                    soft_penalty = (
                        self.conflicts_checker.check_room_capacity(event, room) +
                        self.conflicts_checker.check_block_compactness(event, simulated_timetable["events"][:i], timeslot, weekday) +
                        self.conflicts_checker.check_min_working_days(event, simulated_timetable["events"][:i], weekday) +
                        self.conflicts_checker.check_room_stability(event, simulated_timetable["events"][:i], room)
                    )

                    if hard_penalty == 0 and soft_penalty < min_soft_penalty:
                        min_soft_penalty = soft_penalty
                        best_room_and_period = (room, weekday, timeslot)
                        if min_soft_penalty == 0:
                            return best_room_and_period
                    elif best_room_and_period is None:
                        if hard_penalty < least_conflict_hard_penalty:
                            least_conflict_hard_penalty = hard_penalty
                            least_conflict_soft_penalty = soft_penalty
                            least_conflict_room_and_period = (room, weekday, timeslot)
                        elif hard_penalty == least_conflict_hard_penalty and soft_penalty < least_conflict_soft_penalty:
                            least_conflict_soft_penalty = soft_penalty
                            least_conflict_room_and_period = (room, weekday, timeslot)
                            
            return best_room_and_period if best_room_and_period else least_conflict_room_and_period
        

        def evaluate_timetable(simulated_timetable):
            hard_penalty = 0
            soft_penalty = 0
            last_event_name = None
            for i, event in enumerate(simulated_timetable["events"]):
                hard_penalty += self.conflicts_checker.check_event_hard_constraints(event, simulated_timetable["events"][i+1:], event["RoomId"], event["Timeslot"], event["WeekDay"])   
                soft_penalty += self.conflicts_checker.check_room_capacity(event, event["RoomId"])
                soft_penalty += self.conflicts_checker.check_block_compactness(event,simulated_timetable["events"], event["Timeslot"], event["WeekDay"])
                if event["Name"] != last_event_name:
                    soft_penalty += self.conflicts_checker.check_min_working_days(event,simulated_timetable["events"][i+1:],event["WeekDay"])
                    soft_penalty += self.conflicts_checker.check_room_stability(event, simulated_timetable["events"][i+1:], event["RoomId"])
                last_event_name = event["Name"]

            #print(f"{hard_penalty} {soft_penalty}")

            return -hard_penalty, -soft_penalty
        
        
        def update_penalties(hard_penalty, soft_penalty):
            self.best_hard_penalty = max(hard_penalty, self.best_hard_penalty)
            self.worst_hard_penalty = min(hard_penalty, self.worst_hard_penalty)
            self.best_soft_penalty = max(soft_penalty, self.best_soft_penalty)
            self.worst_soft_penalty = min(soft_penalty, self.worst_soft_penalty)

            self.current_node.best_hard_penalty_result = max(hard_penalty, self.current_node.best_hard_penalty_result)
            self.current_node.best_soft_penalty_result = max(soft_penalty, self.current_node.best_soft_penalty_result)


        simulated_timetable = deepcopy(self.current_node.timetable)
        for i, event in enumerate(self.current_node.timetable["events"][self.current_node.depth():]):
            best_room_and_period = find_best_room_and_period(event,i+self.current_node.depth())    
            room, weekday, timeslot = best_room_and_period               
            update_event(event["Id"], simulated_timetable["events"], room, weekday, timeslot)

        hard_penalty_result, soft_penalty_result = evaluate_timetable(simulated_timetable)
        update_penalties(hard_penalty_result, soft_penalty_result)
        
        print(f"{hard_penalty_result} {soft_penalty_result} {self.normalize_hard(self.current_node.best_hard_penalty_result)} {self.normalize_soft(self.current_node.best_soft_penalty_result)}")

        if hard_penalty_result > self.best_result_hard:
            self.best_result_hard = hard_penalty_result
            self.best_result_soft = soft_penalty_result
            file = open('output.txt', 'w')
            write_best_simulation_result_to_file(simulated_timetable["events"], file)
            file.close()
        elif hard_penalty_result == self.best_result_hard and soft_penalty_result >= self.best_result_soft:
            self.best_result_soft = soft_penalty_result
            file = open('output.txt', 'w')
            write_best_simulation_result_to_file(simulated_timetable["events"], file)
            file.close()

        simulation_result_hard = self.normalize_hard(self.current_node.best_hard_penalty_result)
        simulation_result_soft = self.normalize_soft(self.current_node.best_soft_penalty_result)

        return simulation_result_hard, simulation_result_soft
    

    def backpropagation(self, simulation_result_hard, simulation_result_soft):
        node = self.current_node
        while node is not None:
            node.visits += 1
            node.score_hard += simulation_result_hard
            node.score_soft += simulation_result_soft
            node = node.parent


    def run_mcts(self, iterations=1500, time_limit=600):

        def get_best_solution(time):
            def select_best_terminal_node(node):
                if not node.children:
                    return node
                best_child = max(node.children, key=lambda child: child.score_hard + child.score_soft)
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
            if self.current_node.depth() == len(self.current_node.timetable["events"]) or duration > time_limit: break
            self.expansion()
            simulation_result_hard, simulation_result_soft = self.simulation()
            self.backpropagation(simulation_result_hard, simulation_result_soft)
        
        return get_best_solution(duration)
