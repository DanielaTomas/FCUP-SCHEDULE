from copy import deepcopy
from random_data import *
from mcts_node import *

EXPANSION_LIMIT = 5 # adjust if necessary

#TODO remove prints

class MCTS:

    def __init__(self, current_timetable):
        self.calculate_event_durations(current_timetable["events"])
        self.root = MCTSNode(current_timetable)
        self.current_node = self.root

    def calculate_event_durations(self, events):
        for event in events:
            start_time = event["StartTime"]
            end_of_day = event["EndTime"]
            if start_time is not None and end_of_day is not None:
                duration = (end_of_day - start_time).total_seconds() / 60.0
                event["Duration"] = duration
            else:
                event["Duration"] = 60 # adjust if necessary


    def get_room_name_by_id(self, room_id):
        for room in self.current_node.timetable["rooms"]:
            if room["Id"] == room_id:
                return room["Name"]
        return "Room Not Found"
    
    def check_conflict_time(self, start_time, other, end_time, weekday):
        if not all([other.get("EndTime"), other.get("StartTime"), other.get("WeekDay")]): 
            return False
        return other["WeekDay"] == weekday and start_time < other["EndTime"] and end_time > other["StartTime"]
    
    def check_conflict(self, other, start_time, end_time, weekday, room):
        return (self.get_room_name_by_id(room) != "DCC online" and
                other['RoomId'] == room and
                self.check_conflict_time(start_time, other, end_time, weekday))

    def evaluate_timetable(self, timetable):
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
                        if room and self.check_conflict(other_event, start_time, end_time, weekday, room):
                            penalty += 1
                        if lecturer and other_event["LecturerId"] == lecturer and self.check_conflict_time(start_time, other_event, end_time, weekday):
                            penalty += 1
                for occupation in timetable["occupations"]:
                    if room and self.check_conflict(occupation, start_time, end_time, weekday, room):
                            penalty += 1
                if lecturer:
                    for restriction in timetable["restrictions"]:
                        if (restriction["Type"] == 1 and
                            restriction["LecturerId"] == lecturer and 
                            self.check_conflict_time(start_time, restriction, end_time, weekday)):
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
                break
                #print(f"\tEvent updated: {e}")

        new_changed_events = deepcopy(self.current_node.changedEvents) + [new_change]

        child_node = MCTSNode(new_timetable, changedEvents=new_changed_events, parent=self.current_node)
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

    def print_node_scores(self, node, depth=0):
        if node.visits > 0:
            score_visits = f"score {node.score}, visits {node.visits}, ratio {node.score / node.visits:.2f}"
        else:
            score_visits = "score {node.score}, visits {node.visits}, ratio -inf"
        print("\t" * depth + f"Node: {score_visits}")
        for child in node.children:
            self.print_node_scores(child, depth + 1)

    def get_best_solution(self):
        def select_best_terminal_node(node):
            # If this node has no children, it is a terminal node
            if not node.children:
                return node
            
            # Select the best child based on score/visits ratio, then recursively continue
            best_child = max(node.children, key=lambda child: child.score / child.visits if child.visits > 0 else float('-inf'))
            # Recursively find the best terminal node from this child
            return select_best_terminal_node(best_child)

        self.print_node_scores(self.root)
        # Start from the root node and navigate to the best terminal node
        best_terminal_node = select_best_terminal_node(self.root)

        # Print the best terminal node's changed events and return them
        print(f"Best solution: visits {best_terminal_node.visits}, score {best_terminal_node.score}, ratio {best_terminal_node.score / best_terminal_node.visits:.2f}")
        print(f"Changes: {best_terminal_node.changedEvents}")

        # Return the changes (changedEvents) of the best terminal node
        return best_terminal_node.changedEvents
