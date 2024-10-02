from copy import deepcopy
from mcts.random_data import *
from mcts.mcts_node import *
from mcts.utils import *
from mcts.check_conflicts import *

#TODO remove prints
class MCTS:

    def __init__(self, current_timetable):
        self.timetable = deepcopy(current_timetable)
        self.events_to_visit = events_to_visit(self.timetable["events"])
        if not self.events_to_visit: raise Exception("All the events are allocated. There are no events to visit.")
        self.root = MCTSNode(current_timetable)
        self.current_node = self.root


    def evaluate_timetable(self, timetable): #TODO Add soft constraints
        penalty = 0
        for i, event in enumerate(timetable["events"]):
            if event["StartTime"] and event["EndTime"] and event["WeekDay"]:
                penalty += check_event_conflicts(event, timetable["events"][i+1:], self.timetable["rooms"], event["LecturerId"], event["StartTime"], event["EndTime"], event["WeekDay"])
                penalty += check_room_occupations(event, self.timetable["occupations"], self.timetable["rooms"], event["StartTime"], event["EndTime"], event["WeekDay"])
                penalty += check_lecturer_restrictions(event["LecturerId"], self.timetable["restrictions"], event["StartTime"], event["EndTime"], event["WeekDay"])
                penalty += check_student_conflicts(event, timetable["students_events"], timetable["events"], event["StartTime"], event["EndTime"], event["WeekDay"])
        return -penalty
    

    # MCTS steps:

    
    def selection(self):
        current_node = self.root
        while current_node.is_fully_expanded(self.events_to_visit):
            current_node = current_node.best_child()
        self.current_node = current_node


    def expansion(self):
        event = self.events_to_visit[self.current_node.depth]

        start_of_day, lunch_end, latest_start_morning, latest_start_afternoon = calculate_time_bounds(event["Duration"])
        valid_start_slots = get_valid_start_slots(start_of_day, lunch_end, latest_start_morning, latest_start_afternoon)

        slot = len(self.current_node.children)
        slot_index = slot % len(valid_start_slots)
        new_weekday = (slot // len(valid_start_slots)) % 5 + 2

        start_time = valid_start_slots[slot_index]
        new_start_time = timedelta(hours=start_time.hour, minutes=start_time.minute)
        new_end_time = new_start_time + timedelta(minutes=event["Duration"])

        if event["RoomId"] is not None: print(f"Room {event['RoomId']} Weekday {new_weekday} StartTime {new_start_time} Event {event['Id']} Depth {self.current_node.depth}")
        
        new_timetable = deepcopy(self.current_node.timetable)
        new_event = update_event(event["Id"], new_timetable["events"], new_weekday, new_start_time, new_end_time)
        if event["RoomId"] is None:
            rooms = self.timetable["rooms"]
            available_rooms = empty_rooms(self.timetable["occupations"], self.current_node.timetable["events"], event, rooms)
            new_event["RoomId"] = rooms[(slot // (len(valid_start_slots) * 5)) % len(available_rooms)]["Id"]
            print(f"Room {(slot // (len(valid_start_slots) * 5)) % len(available_rooms)}:{new_event['RoomId']} Weekday {new_weekday} StartTime {new_start_time} Event {event['Id']} Depth {self.current_node.depth}")

        child_node = MCTSNode(timetable=new_timetable, parent=self.current_node, depth=self.current_node.depth+1)
        child_node.path = self.current_node.path + [new_event]
        self.current_node.children.append(child_node)
        self.current_node = child_node

    
    def simulation(self):
        random_timetable = deepcopy(self.current_node.timetable)
        for event in self.events_to_visit[self.current_node.depth:]:
            random_start_time, random_end_time, random_weekday = random_time(event["Duration"])
            new_event = update_event(event, random_timetable["events"], random_weekday, random_start_time, random_end_time)
            if event["RoomId"] is None:
                new_event["RoomId"] = random_room(self.timetable["occupations"],self.current_node.timetable["events"],event,self.timetable["rooms"])["Id"]

        result = self.evaluate_timetable(random_timetable)
        return result


    def backpropagation(self, simulation_result):
        node = self.current_node
        while node is not None:
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
    

    def get_best_solution(self):
        def select_best_terminal_node(node):
            if not node.children:
                return node
            best_child = max(node.children, key=lambda child: (child.score / child.visits if child.visits > 0 else float('-inf'), child.visits))
            return select_best_terminal_node(best_child)

        print_node_scores(self.root)
        best_terminal_node = select_best_terminal_node(self.root)

        return best_terminal_node.path