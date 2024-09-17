from copy import deepcopy
from mcts.random_data import *
from mcts.mcts_node_local_search import *
from mcts.utils import *

EXPANSION_LIMIT = 5 # adjust if necessary

#TODO remove prints

class MCTS:

    def __init__(self, current_timetable):
        calculate_event_durations(current_timetable["events"])
        self.root = MCTSNodeLocalSearch(current_timetable)
        self.current_node = self.root


    def evaluate_timetable(self, timetable): #TODO Add students and soft constraints
        penalty = 0
        for event in timetable["events"]:
            room = event["RoomId"]
            start_time = event["StartTime"]
            end_time = event["EndTime"]
            weekday = event["WeekDay"]
            lecturer = event["LecturerId"]

            if start_time and end_time and weekday:
                for other_event in timetable["events"]:
                    if other_event["Id"] != event["Id"]:
                        if room and check_conflict(other_event, start_time, end_time, weekday, room, self.current_node.timetable["rooms"]):
                            penalty += 1
                        if lecturer and other_event["LecturerId"] == lecturer and check_conflict_time(start_time, other_event, end_time, weekday):
                            penalty += 1
                for occupation in timetable["occupations"]:
                    if room and check_conflict(occupation, start_time, end_time, weekday, room, self.current_node.timetable["rooms"]):
                            penalty += 1
                if lecturer:
                    for restriction in timetable["restrictions"]:
                        if (restriction["Type"] == 1 and
                            restriction["LecturerId"] == lecturer and 
                            check_conflict_time(start_time, restriction, end_time, weekday)):
                            penalty += 1
        return -penalty
    

    # MCTS steps:


    def selection(self):
        #print("Starting selection...")
        current_node = self.root
        while current_node.is_fully_expanded() and len(current_node.children)+1 > EXPANSION_LIMIT:
            #print(f"\tCurrent node visits: {current_node.visits}, score: {current_node.score}")
            current_node = current_node.best_child()
        #print(f"\tSelected node: visits: {current_node.visits}, score: {current_node.score}")
        self.current_node = current_node


    def expansion(self, timetable):
        #print("Starting expansion...")
        event = random_event(timetable["events"])
        #print(f"\tExpanding event: {event}")
        new_start_time, new_end_time, new_weekday = random_time(event["Duration"])
        new_room = random_room(timetable["occupations"], timetable["events"], new_start_time, new_end_time, timetable["rooms"])
        new_timetable = deepcopy(self.current_node.timetable)
        for e in new_timetable["events"]:
            if e["Id"] == event["Id"]:
                e["StartTime"] = new_start_time
                e["EndTime"] = new_end_time
                e["RoomId"] = new_room["Id"]
                e["WeekDay"] = new_weekday
                new_change = e
                #print(f"\tEvent updated: {e}")
                break

        new_changed_events = deepcopy(self.current_node.changedEvents) + [new_change]

        child_node = MCTSNodeLocalSearch(new_timetable, changedEvents=new_changed_events, parent=self.current_node)
        self.current_node.children.append(child_node)
        self.current_node = child_node
        #print(f"\tCreated child node with visits: {child_node.visits}, score: {child_node.score}")


    def simulation(self):
        #print("Starting simulation...")
        result = self.evaluate_timetable(self.current_node.timetable)
        #print(f"\tSimulation result: {result}")
        return result


    def backpropagation(self, simulation_result):
        #print("Starting backpropagation...")
        node = self.current_node
        while node is not None:
            #print(f"\tUpdating node: visits {node.visits} + 1, score {node.score} + {simulation_result}")
            node.visits += 1
            node.score += simulation_result
            node = node.parent


    def run_mcts(self, iterations=1000):
        for _ in range(iterations):
            self.selection()
            self.expansion(self.current_node.timetable)
            simulation_result = self.simulation()
            self.backpropagation(simulation_result)
        return self.get_best_solution()


    def get_best_solution(self):
        def select_best_terminal_node(node):
            if not node.children:
                return node
            best_child = max(node.children, key=lambda child: child.score / child.visits if child.visits > 0 else float('-inf'))
            return select_best_terminal_node(best_child)

        print_node_scores(self.root)
        best_terminal_node = select_best_terminal_node(self.root)

        #print(f"Best terminal node: visits {best_terminal_node.visits}, score {best_terminal_node.score}, ratio {best_terminal_node.score / best_terminal_node.visits:.2f}")
        print(f"Changes: {best_terminal_node.changedEvents}")

        return best_terminal_node.changedEvents
