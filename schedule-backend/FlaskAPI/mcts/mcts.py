from copy import deepcopy
from mcts.random_data import *
from mcts.mcts_node import *
from mcts.utils import *

#TODO remove prints
class MCTS:

    def __init__(self, current_timetable):
        self.timetable = deepcopy(current_timetable)
        self.events_to_visit = events_to_visit(self.timetable["events"])
        if self.events_to_visit == []: Exception("All the events are allocated. There are no events to visit.")
        self.root = MCTSNode(current_timetable)
        self.current_node = self.root


    def evaluate_timetable(self, timetable): #TODO Add students and soft constraints
        penalty = 0
        for i, event in enumerate(timetable["events"]):
            room = event["RoomId"]
            start_time = event["StartTime"]
            end_time = event["EndTime"]
            weekday = event["WeekDay"]
            lecturer = event["LecturerId"]

            if start_time and end_time and weekday:
                for other_event in timetable["events"][i+1:]:
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
        if self.current_node.parent is None: return
        event_index = self.current_node.parent.depth
        event = self.events_to_visit[event_index]
        start_of_day, lunch_end, latest_start_morning, latest_start_afternoon = calculate_time_bounds(event["Duration"])

        valid_start_slots = get_valid_start_slots(
            start_of_day, lunch_end, latest_start_morning, latest_start_afternoon
        )
        current_node = self.root
        while current_node.is_fully_expanded(len(valid_start_slots)*5):
            current_node = current_node.best_child()
        self.current_node = current_node


    def expansion(self):
        event = self.events_to_visit[self.current_node.depth]

        start_of_day, lunch_end, latest_start_morning, latest_start_afternoon = calculate_time_bounds(event["Duration"])
        valid_start_slots = get_valid_start_slots(
            start_of_day, lunch_end, latest_start_morning, latest_start_afternoon
        )

        slot = len(self.current_node.children)
        slot_index = slot % len(valid_start_slots)
        new_weekday = (slot // len(valid_start_slots)) + 2
        start_time = valid_start_slots[slot_index]
        end_time = start_time + timedelta(minutes=event["Duration"])

        new_start_time = timedelta(hours=start_time.hour, minutes=start_time.minute)
        new_end_time = timedelta(hours=end_time.hour, minutes=end_time.minute)
        
        new_timetable = deepcopy(self.current_node.timetable)
        for e in new_timetable["events"]:
            if e["Id"] == event["Id"]:
                e["StartTime"] = new_start_time
                e["EndTime"] = new_end_time
                if event["RoomId"] is None : 
                    new_room = random_room(self.timetable["occupations"], self.timetable["events"], new_start_time, new_end_time, self.timetable["rooms"])
                    e["RoomId"] = new_room["Id"]
                else: 
                    e["RoomId"] = event["RoomId"]
                e["WeekDay"] = new_weekday
                new_event = e

        child_node = MCTSNode(timetable=new_timetable, parent=self.current_node, depth=self.current_node.depth+1)
        child_node.path = self.current_node.path + [new_event]
        self.current_node.children.append(child_node)
        self.current_node = child_node


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
            if self.current_node.depth == len(self.events_to_visit): break
            self.expansion()
            simulation_result = self.simulation()
            self.backpropagation(simulation_result)
        return self.get_best_solution()


    def get_best_solution1(self):
        if self.root.children:
            print_node_scores(self.root)
            best_node = max(self.root.children, key=lambda node: (node.score / node.visits if node.visits > 0 else float('-inf'), node.visits))
            #if best_node: print(f"Best solution: visits {best_node.visits}, score {best_node.score}, ratio {best_node.score / best_node.visits:.2f}")
            return best_node.path if best_node else self.root.path
        return self.root.path
    

    def get_best_solution(self):
        def select_best_terminal_node(node):
            if not node.children:
                return node
            best_child = max(node.children, key=lambda child: (child.score / child.visits if child.visits > 0 else float('-inf'), child.visits))
            return select_best_terminal_node(best_child)

        print_node_scores(self.root)
        best_terminal_node = select_best_terminal_node(self.root)

        #print(f"Best terminal node: visits {best_terminal_node.visits}, score {best_terminal_node.score}, ratio {best_terminal_node.score / best_terminal_node.visits:.2f}")
        #print(f"Changes: {best_terminal_node.changedEvents}")

        return best_terminal_node.path