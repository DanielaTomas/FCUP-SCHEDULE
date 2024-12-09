from copy import deepcopy
from mcts_itc.mcts_node import *
from mcts_itc.utils import *
from mcts_itc.check_conflicts import ConflictsChecker
import time

#TODO remove prints

class MCTS:

    def __init__(self, current_timetable, days, periods_per_day, output_filename = "output\output.txt"):
        current_timetable["events"] = add_event_ids(current_timetable["events"], days, periods_per_day, current_timetable["blocks"], current_timetable["constraints"])
        self.conflicts_checker = ConflictsChecker(current_timetable["constraints"], current_timetable["blocks"], current_timetable["rooms"])
        self.root = MCTSNode(current_timetable, root_expansion_limit(current_timetable["events"][0], current_timetable["rooms"], current_timetable["events"][:0]))
        self.current_node = self.root
        self.best_result_hard= float('-inf')
        self.best_result_soft = float('-inf')

        self.best_hard_penalty = float('-inf')
        self.worst_hard_penalty = float('inf')
        self.best_soft_penalty = float('-inf')
        self.worst_soft_penalty = float('inf')

        self.unassigned_events = []
        self.output_filename = output_filename


    def normalize_hard(self, result):
        if self.best_hard_penalty == self.worst_hard_penalty: return 0.5
        a = (result - self.worst_hard_penalty)/(self.best_hard_penalty - self.worst_hard_penalty)
        #return ((math.exp(a) - 1) / (math.e - 1))*0.5 + 0.5
        return (math.exp(a) - 1) / (math.e - 1)


    def normalize_soft(self, result):
        if self.best_soft_penalty == self.worst_soft_penalty: return 0.5
        a = (result - self.worst_soft_penalty)/(self.best_soft_penalty - self.worst_soft_penalty)
        #return ((math.exp(a) - 1) / (math.e - 1))*0.5
        return (math.exp(a) - 1) / (math.e - 1)
    
    
    # MCTS steps:


    def selection(self):
        current_node = self.root
        while not current_node.is_fully_expanded():
            best_child = current_node.best_child()
            current_node = best_child
        self.current_node = current_node


    def expansion(self):
        event = self.current_node.timetable["events"][self.current_node.depth()]

        available_periods = event["Available_Periods"]
        if not available_periods: return
        period = len(self.current_node.children)
        period_index = period % len(available_periods)
        new_weekday, new_timeslot = available_periods[period_index]

        available_rooms = find_available_rooms(event, self.current_node.timetable["rooms"], self.current_node.timetable["events"][:self.current_node.depth()], [available_periods[period_index]])
        if not available_rooms: return
        available_rooms_list = list(list(available_rooms.values())[0])
        new_room_index = period // len(available_periods) % len(available_rooms_list)
        new_room = available_rooms_list[new_room_index]
        
        new_timetable = deepcopy(self.current_node.timetable)
        new_event = update_event(event["Id"], new_timetable["events"], new_room, new_weekday, new_timeslot)
        next_event = self.current_node.timetable["events"][self.current_node.depth()+1] if self.current_node.depth()+1 < len(self.current_node.timetable["events"]) else None
        if next_event is None:
            expansion_limit = 0
        else:
            expansion_limit = sum(
                len(rooms) for rooms in find_available_rooms(next_event, self.current_node.timetable["rooms"], self.current_node.timetable["events"][:self.current_node.depth()], next_event["Available_Periods"]
                ).values()
            )
            
        child_node = MCTSNode(timetable=new_timetable, expansion_limit=(expansion_limit), parent=self.current_node)
        child_node.path = self.current_node.path + [new_event]
        self.current_node.children.append(child_node)
        self.current_node = child_node


    def simulation(self):

        def find_best_room_and_period(event, i, simulated_timetable):
            if not event["Available_Periods"]: return None

            min_soft_penalty = float('inf')
            candidates = []

            compactness_weight = min(1, i / (len(simulated_timetable["events"])-1))

            for available_period in event["Available_Periods"]:
                weekday, timeslot = available_period
                available_rooms = find_available_rooms(event, simulated_timetable["rooms"], simulated_timetable["events"][:i], [available_period])
                if available_rooms:
                    for room in list(list(available_rooms.values())[0]):
                        hard_penalty = self.conflicts_checker.check_event_hard_constraints(event, simulated_timetable["events"][:i], room, timeslot, weekday)
                        if hard_penalty == 0:
                            soft_penalty = (
                                self.conflicts_checker.check_room_capacity(event, room)
                                + compactness_weight * self.conflicts_checker.check_block_compactness(event, simulated_timetable["events"][:i], timeslot, weekday)
                                + self.conflicts_checker.check_min_working_days(event, simulated_timetable["events"][:i], weekday)
                                + self.conflicts_checker.check_room_stability(event, simulated_timetable["events"][:i], room)
                            )
                            if soft_penalty < min_soft_penalty:
                                min_soft_penalty = soft_penalty
                                candidates = [(room, weekday, timeslot)]
                            elif soft_penalty == min_soft_penalty:
                                candidates.append((room, weekday, timeslot))
            return random.choice(candidates) if candidates else None
        

        def evaluate_timetable(simulated_timetable):
            hard_penalty = 0
            soft_penalty = 0
            event_names = []
            room_conflicts = {}

            for i, event in enumerate(simulated_timetable["events"]):
                hard_penalty += self.conflicts_checker.check_event_hard_constraints(event, simulated_timetable["events"][i+1:], event["RoomId"], event["Timeslot"], event["WeekDay"], room_conflicts)   
                soft_penalty += (self.conflicts_checker.check_room_capacity(event, event["RoomId"])
                             + self.conflicts_checker.check_block_compactness(event, simulated_timetable["events"], event["Timeslot"], event["WeekDay"]))
                if event["Name"] not in event_names: 
                    soft_penalty += (self.conflicts_checker.check_min_working_days(event, simulated_timetable["events"][i+1:], event["WeekDay"])
                                 + self.conflicts_checker.check_room_stability(event, simulated_timetable["events"][i+1:], event["RoomId"]))
                event_names.append(event["Name"])
            hard_penalty += self.conflicts_checker.check_room_conflicts(room_conflicts)
            return -hard_penalty, -soft_penalty
        
        
        def update_penalties(hard_penalty, soft_penalty):
            self.best_hard_penalty = max(hard_penalty, self.best_hard_penalty)
            self.worst_hard_penalty = min(hard_penalty, self.worst_hard_penalty)
            self.best_soft_penalty = max(soft_penalty, self.best_soft_penalty)
            self.worst_soft_penalty = min(soft_penalty, self.worst_soft_penalty)

            self.current_node.best_hard_penalty_result = max(hard_penalty, self.current_node.best_hard_penalty_result)
            self.current_node.best_soft_penalty_result = max(soft_penalty, self.current_node.best_soft_penalty_result)


        simulated_timetable = deepcopy(self.current_node.timetable)
        simulated_timetable["events"][self.current_node.depth():] = sorted(simulated_timetable["events"][self.current_node.depth():], key=lambda event: (event["Id"] in self.unassigned_events, event["Priority"], random.random()), reverse=True)
        for i, event in enumerate(simulated_timetable["events"][self.current_node.depth():]):
            best_room_and_period = find_best_room_and_period(event, i+self.current_node.depth(), simulated_timetable)
            if best_room_and_period:
                room, weekday, timeslot = best_room_and_period              
                update_event(event["Id"], simulated_timetable["events"], room, weekday, timeslot)
            elif event["Id"] not in self.unassigned_events: 
                self.unassigned_events.append(event["Id"])

        hard_penalty_result, soft_penalty_result = evaluate_timetable(simulated_timetable)
        update_penalties(hard_penalty_result, soft_penalty_result)
        
        print(f"{hard_penalty_result} {soft_penalty_result} {self.normalize_hard(self.current_node.best_hard_penalty_result)} {self.normalize_soft(self.current_node.best_soft_penalty_result)}")

        if (hard_penalty_result > self.best_result_hard) or (hard_penalty_result == self.best_result_hard and soft_penalty_result > self.best_result_soft):
            self.best_result_hard = hard_penalty_result
            self.best_result_soft = soft_penalty_result
            with open(self.output_filename, 'w') as file:
                write_best_simulation_result_to_file(simulated_timetable["events"], file)

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
                best_child = max(node.children, key=lambda child: (child.score_hard, child.score_soft))
                return select_best_terminal_node(best_child)

            """ file = open('tree.txt', 'w')
            file.write(f"Time: ~{time}\n")
            write_node_scores_to_file(self.root, file)
            file.close() """
            best_terminal_node = select_best_terminal_node(self.root)

            return best_terminal_node.path

        start_time = time.time()
        try:
            for _ in range(iterations):
                self.selection()
                duration = time.time() - start_time
                if self.current_node.depth() == len(self.current_node.timetable["events"]) or duration > time_limit: break
                self.expansion()
                simulation_hard, simulation_soft = self.simulation()
                self.backpropagation(simulation_hard, simulation_soft)
        except KeyboardInterrupt:
            print("Execution interrupted by user. Returning the best solution found so far...")
            duration = time.time() - start_time
        
        return get_best_solution(duration)
