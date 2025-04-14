from algorithm.mcts_node import *
from algorithm.utils import *
from algorithm.debug import *
from algorithm.check_conflicts import ConflictsChecker
from algorithm.hill_climbing import HillClimbing
from algorithm.simulation_results_writer import write_simulation_results
from algorithm.macros import DEFAULT_TIME_LIMIT, DEBUG_TREE, DEBUG_PROGRESS, DEBUG_PROFILER
from dataclasses import dataclass
import cProfile
import time

#TODO remove prints; remove debug ?
#TODO documentation
#TODO remove final_result ?

@dataclass
class Params:
    c_param: float = 1.4
    iterations: int = None
    time_limit: int = DEFAULT_TIME_LIMIT


@dataclass
class MCTSConfig:
    params: Params
    days: int
    periods_per_day: int
    output_filename: str = "output/output.txt"


class MCTS:

    def __init__(self, current_timetable, config: MCTSConfig):
        self.params = config.params
        self.rooms = current_timetable["rooms"]
        self.events, name_to_event_ids = add_event_ids_and_priority(current_timetable["events"], config.days, config.periods_per_day, current_timetable["blocks"], current_timetable["constraints"])
        self.root = MCTSNode(expansion_limit=root_expansion_limit(self.events[0], self.rooms))
        self.current_node = self.root
        
        self.conflicts_checker = ConflictsChecker(current_timetable["constraints"], current_timetable["blocks"], self.rooms, name_to_event_ids)
        self.hill_climber = HillClimbing(self.conflicts_checker, current_timetable["blocks"], self.rooms, config.days, name_to_event_ids, config.output_filename)
        
        self._initialize_penalties()

        self.previous_unassigned_events = set()
        self.output_filename = config.output_filename

        if DEBUG_PROGRESS:
            self.metrics = {'iterations': [], 'best_hard': [], 'best_soft': [], 'current_hard': [], 'current_soft': []}
    

    def _initialize_penalties(self):
        self.global_best_hard_penalty = float('-inf')
        self.global_best_soft_penalty = float('-inf')

        self.worst_hard_penalty = float('inf')
        self.worst_soft_penalty = float('inf')
        self.best_soft_penalty = float('-inf')


    def normalize(self, result, best, worst):
        if best == 0 and worst == 0: return 1.0
        if best == worst: return 0.5
        a = (result - worst) / (best - worst)
        return (math.exp(a) - 1) / (math.e - 1)
    

    def update_progress_metrics(self, iteration):
        self.metrics['iterations'].append(iteration)
        self.metrics['best_hard'].append(self.global_best_hard_penalty)
        self.metrics['best_soft'].append(self.global_best_soft_penalty)


    # MCTS steps:


    def selection(self):
        current_node = self.root
        while not current_node.is_terminal_node(len(self.events)):
            if not current_node.is_fully_expanded(): break
            
            unflagged_children = [child for child in current_node.children if child and not child.expansion_limit == 0]

            if not unflagged_children:
                if current_node.parent:
                    current_node.expansion_limit = 0
                    current_node = current_node.parent
                else:
                    return False
            else:
                current_node = current_node.best_child(unflagged_children, self.params.c_param)

        self.current_node = current_node
        return True


    def expansion(self):

        def calculate_expansion_limit(new_path):
            next_event = self.events[self.current_node.depth()+1] if self.current_node.depth()+1 < len(self.events) else None
            if next_event is None:
                return 0
            elif evaluate_timetable(self.conflicts_checker, new_path, full_evaluation=False) < self.global_best_hard_penalty:
                self.previous_unassigned_events.add(event["Id"])
                self.current_node.children.append(None)
                return None
            rooms_available = find_available_rooms(next_event["Capacity"], self.rooms, new_path.values(), next_event["Available_Periods"])
            return sum(len(rooms) for rooms in rooms_available.values())


        event = self.events[self.current_node.depth()]

        available_periods = event["Available_Periods"]
        if len(available_periods) == 0:
            self.current_node.expansion_limit = 0
            return False

        rooms_by_period = find_available_rooms(event["Capacity"], self.rooms, self.current_node.path.values(), available_periods)

        period_room_combinations = [(weekday, timeslot, room) for (weekday, timeslot), rooms in rooms_by_period.items() if rooms for room in rooms]

        if not period_room_combinations or len(self.current_node.children) >= len(period_room_combinations):
            self.current_node.expansion_limit = 0
            return False

        new_weekday, new_timeslot, new_room = period_room_combinations[len(self.current_node.children)]
        
        new_path = self.current_node.path.copy()
        new_path[event["Id"]] = {**event, "RoomId": new_room, "WeekDay": new_weekday, "Timeslot": new_timeslot}

        new_expansion_limit = calculate_expansion_limit(new_path)
        if new_expansion_limit is None: return False
        
        child_node = MCTSNode(expansion_limit=new_expansion_limit, assignment=(event["Id"], new_weekday, new_timeslot, new_room), parent=self.current_node, path=new_path)
        self.current_node.children.append(child_node)
        self.current_node = child_node
        return True


    def simulation(self, start_time, time_limit):

        def find_best_room_and_period():
            if not event["Available_Periods"]: return None

            min_soft_penalty = float('inf')
            candidates = []

            compactness_weight = min(1, (i+self.current_node.depth()) / (len(self.events)-1))

            for weekday, timeslot in event["Available_Periods"]:
                available_rooms = find_available_rooms(event["Capacity"], self.rooms, assigned_events.values(), [(weekday,timeslot)])
                if available_rooms.values() != [set()]:
                    for room in list(list(available_rooms.values())[0]):
                        hard_penalty = self.conflicts_checker.check_event_hard_constraints(event, assigned_events, room, timeslot, weekday)
                        if hard_penalty == 0:
                            soft_penalty = (
                                self.conflicts_checker.check_room_capacity(event, room)
                                + compactness_weight * self.conflicts_checker.check_block_compactness(event, assigned_events, timeslot, weekday)
                                + self.conflicts_checker.check_min_working_days(event, assigned_events, weekday)
                                + self.conflicts_checker.check_room_stability(event, assigned_events, room)
                            )
                            if soft_penalty < min_soft_penalty:
                                min_soft_penalty = soft_penalty
                                candidates = [(room, weekday, timeslot)]
                            elif soft_penalty == min_soft_penalty:
                                candidates.append((room, weekday, timeslot))
            return random.choice(candidates) if candidates else None
            

        def update_penalties(soft_penalty, hard_penalty = None):
            if hard_penalty is not None:
                self.worst_hard_penalty = min(hard_penalty, self.worst_hard_penalty)
                self.current_node.best_hard_penalty = max(hard_penalty, self.current_node.best_hard_penalty)
            self.best_soft_penalty = max(soft_penalty, self.best_soft_penalty)
            self.worst_soft_penalty = min(soft_penalty, self.worst_soft_penalty)
            self.current_node.best_soft_penalty = max(soft_penalty, self.current_node.best_soft_penalty)


        assigned_events = self.current_node.path.copy()
        unassigned_events = set()
        remaining_events = sorted(self.events[self.current_node.depth():], key=lambda event: (event["Id"] in self.previous_unassigned_events, event["Priority"], random.random()), reverse=True)

        for i, event in enumerate(remaining_events):
            best_room_and_period = find_best_room_and_period()
            if best_room_and_period:
                event["RoomId"], event["WeekDay"], event["Timeslot"] = best_room_and_period  
                assigned_events[event["Id"]] = event 
            else: 
                self.previous_unassigned_events.add(event["Id"])
                unassigned_events.add(event["Id"])
                event["Priority"] += 50

        hard_penalty_result, soft_penalty_result = evaluate_timetable(self.conflicts_checker, assigned_events, unassigned_events)
        
        if DEBUG_PROGRESS:
            self.metrics["current_hard"].append(hard_penalty_result)
            self.metrics["current_soft"].append(soft_penalty_result)

        update_penalties(soft_penalty_result, hard_penalty_result)
        
        if (hard_penalty_result > self.global_best_hard_penalty) or (hard_penalty_result == self.global_best_hard_penalty and soft_penalty_result > self.global_best_soft_penalty):
            self.global_best_hard_penalty, self.global_best_soft_penalty = hard_penalty_result, soft_penalty_result
            write_simulation_results(self.output_filename, list(assigned_events.values()), start_time, hard_penalty_result, soft_penalty_result)
            
            if len(unassigned_events) == 0 and hard_penalty_result == 0 and soft_penalty_result != 0:
                self.global_best_soft_penalty = self.hill_climber.run_hill_climbing(assigned_events, self.events[self.current_node.depth()]["Id"], self.global_best_soft_penalty, start_time, time_limit)
                update_penalties(self.global_best_soft_penalty)

        simulation_result_hard = self.normalize(self.current_node.best_hard_penalty, self.global_best_hard_penalty, self.worst_hard_penalty)
        simulation_result_soft = self.normalize(self.current_node.best_soft_penalty, self.best_soft_penalty, self.worst_soft_penalty)
        #if DEBUG_PRINT: print(f"{hard_penalty_result} {soft_penalty_result} {simulation_result_hard} {simulation_result_soft}")

        return simulation_result_hard, simulation_result_soft
    

    def backpropagation(self, simulation_result_hard, simulation_result_soft):
        node = self.current_node
        while node is not None:
            node.visits += 1
            node.score_hard += simulation_result_hard
            node.score_soft += simulation_result_soft
            node = node.parent


    def run_mcts(self):
        if DEBUG_PROFILER:
            profiler = cProfile.Profile()
            profiler.enable()

        try:
            start_time = time.time()
            duration = time.time() - start_time
            i = 0
            while (self.params.iterations is None or i < self.params.iterations) and (duration <= self.params.time_limit):
                if not self.selection():
                    print("Full tree!\n")
                    break
                if self.expansion():
                    simulation_hard, simulation_soft = self.simulation(start_time, self.params.time_limit)
                    if self.global_best_hard_penalty == 0 and self.global_best_soft_penalty == 0:
                        print("Optimal solution found!\n")
                        break
                    self.backpropagation(simulation_hard, simulation_soft)
                    duration = time.time() - start_time
                    if DEBUG_PROGRESS: self.update_progress_metrics(i+1)
                i += 1
        except KeyboardInterrupt:
            print("Execution interrupted by user.\n")
            duration = time.time() - start_time

        if DEBUG_TREE or DEBUG_PROGRESS or DEBUG_PROFILER:
            try:
                _, tail = os.path.split(self.output_filename)
                input_file_name = tail.split('_')[0]

                if DEBUG_PROFILER: profile_execution(profiler, f"{input_file_name}_profiler_outuput.txt")
                if DEBUG_PROGRESS: plot_progress(self.metrics, f"{input_file_name}_constraint_progress.html")
                if DEBUG_TREE: visualize_tree(self.root, f"{input_file_name}_tree")

            except KeyboardInterrupt:
                print("Execution interrupted by user.\n")

