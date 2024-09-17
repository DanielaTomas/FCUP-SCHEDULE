from copy import deepcopy
from mcts.random_data import *
from mcts.mcts_node import *
from mcts.utils import *

#TODO remove prints

class MCTS:

    def __init__(self, current_timetable):
        self.timetable = deepcopy(current_timetable)
        self.num_events = len(self.timetable["events"])
        calculate_event_durations(self.timetable["events"])

        event = random_event(self.timetable["events"])
        new_start_time, new_end_time, new_weekday = random_time(event["Duration"])
        new_room = random_room(self.timetable["occupations"], [event], new_start_time, new_end_time, self.timetable["rooms"])
        event["StartTime"] = new_start_time
        event["EndTime"] = new_end_time
        event["RoomId"] = new_room["Id"]
        event["WeekDay"] = new_weekday

        self.root = MCTSNode([event])
        self.current_node = self.root


    def evaluate_timetable(self, visited_events): #TODO Add students and soft constraints
        penalty = 0
        for event in visited_events:
            room = event["RoomId"]
            start_time = event["StartTime"]
            end_time = event["EndTime"]
            weekday = event["WeekDay"]
            lecturer = event["LecturerId"]

            if start_time and end_time and weekday:
                for other_event in visited_events:
                    if other_event["Id"] != event["Id"]:
                        if room and check_conflict(other_event, start_time, end_time, weekday, room, self.timetable["rooms"]):
                            penalty += 1
                        if lecturer and other_event["LecturerId"] == lecturer and check_conflict_time(start_time, other_event, end_time, weekday):
                            penalty += 1
                for occupation in self.timetable["occupations"]:
                    if room and check_conflict(occupation, start_time, end_time, weekday, room, self.timetable["rooms"]):
                            penalty += 1
                if lecturer:
                    for restriction in self.timetable["restrictions"]:
                        if (restriction["Type"] == 1 and
                            restriction["LecturerId"] == lecturer and 
                            check_conflict_time(start_time, restriction, end_time, weekday)):
                            penalty += 1
        return -penalty
    

    # MCTS steps:


    def selection(self):
        #print("Starting selection...")
        current_node = self.root
        while current_node.is_fully_expanded() and len(current_node.visited_events) <= self.num_events:
            #print(f"\tCurrent node visits: {current_node.visits}, score: {current_node.score}")
            current_node = current_node.best_child()
        #print(f"\tSelected node: visits: {current_node.visits}, score: {current_node.score}")
        self.current_node = current_node


    def expansion(self, unvisited_events):
        #print("Starting expansion...")
        event = random_event(unvisited_events)
        #print(f"\tExpanding event: {event}")
        new_start_time, new_end_time, new_weekday = random_time(event["Duration"])
        new_room = random_room(self.timetable["occupations"], unvisited_events, new_start_time, new_end_time, self.timetable["rooms"])
        event["StartTime"] = new_start_time
        event["EndTime"] = new_end_time
        event["RoomId"] = new_room["Id"]
        event["WeekDay"] = new_weekday

        new_visited_events = deepcopy(self.current_node.visited_events) + [event]

        child_node = MCTSNode(events=new_visited_events, parent=self.current_node)
        self.current_node.children.append(child_node)
        self.current_node = child_node
        #print(f"\tCreated child node with visits: {child_node.visits}, score: {child_node.score}")


    def simulation(self):
        #print("Starting simulation...")
        result = self.evaluate_timetable(self.current_node.visited_events)
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


    def get_unvisited_events(self, visited_events):
        visited_event_ids = {event["Id"] for event in visited_events}
        unvisited_events = [event for event in self.timetable["events"] if event["Id"] not in visited_event_ids]
        return unvisited_events
    
    def run_mcts(self, iterations=1000):
        for _ in range(iterations):
            self.selection()
            unvisited_nodes = self.get_unvisited_events(self.current_node.visited_events)
            if (unvisited_nodes) : self.expansion(unvisited_nodes)
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

        #print(f"Best solution: visits {best_terminal_node.visits}, score {best_terminal_node.score}, ratio {best_terminal_node.score / best_terminal_node.visits:.2f}")
        #print(f"Visited Events: {best_terminal_node.visited_events}")

        return best_terminal_node.visited_events
