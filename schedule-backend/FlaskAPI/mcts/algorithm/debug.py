import graphviz
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def write_node_scores_to_file(node, file, depth=0):
    if node.visits > 0:
        if not node.path:
            score_visits = f"score {node.score_hard} {node.score_soft} , visits {node.visits}, ratio {node.score_hard / node.visits:.2f} {node.score_soft / node.visits:.2f}"
        else:
            score_visits = f"{node.path[-1]['Id']} {node.path[-1]['Name']} D{node.path[-1]['WeekDay']} P{node.path[-1]['Timeslot']} R{node.path[-1]['RoomId']} score {node.score_hard} {node.score_soft}, visits {node.visits}, ratio {node.score_hard / node.visits:.2f} {node.score_soft / node.visits:.2f}"
    else:
        score_visits = f"score {node.score_hard} {node.score_soft}, visits {node.visits}, ratio -inf"
    
    file.write("   " * depth + f"Node: {score_visits}\n")
    
    for child in node.children:
        write_node_scores_to_file(child, file, depth + 1)


def visualize_tree(root, filename="mcts_tree.png"):
    dot = graphviz.Digraph(comment='MCTS Tree')

    def add_nodes_edges(node):
        label = f"score {node.score_hard:.2f} {node.score_soft:.2f}, visits {node.visits}"
        if node.path:
            last_event = node.path[-1]
            label += f"\n{last_event['Id']} {last_event.get('Name', 'Unnamed')} D{last_event.get('WeekDay', '?')} P{last_event.get('Timeslot', '?')} R{last_event.get('RoomId', '?')}"
        dot.node(str(id(node)), label=label)

        for child in node.children:
            dot.edge(str(id(node)), str(id(child)))
            add_nodes_edges(child)

    add_nodes_edges(root)
    dot.render(filename, view=True)


def plot_progress(iterations, current_hard, best_hard, current_soft, best_soft):
    fig = make_subplots(rows=1, cols=2, 
                        subplot_titles=("Hard Constraint Progress", "Soft Constraint Progress"),
                        shared_xaxes=True)

    fig.add_trace(go.Scatter(x=iterations, y=current_hard, mode='lines+markers', name='Current Hard', line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=iterations, y=best_hard, mode='lines+markers', name='Best Hard', line=dict(color='green')), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=iterations, y=current_soft, mode='lines+markers', name='Current Soft', line=dict(color='red')), row=1, col=2)
    fig.add_trace(go.Scatter(x=iterations, y=best_soft, mode='lines+markers', name='Best Soft', line=dict(color='purple')), row=1, col=2)

    fig.update_layout(title="Constraint Progress (Current vs. Best)", showlegend=True)
    fig.update_xaxes(title_text="Iteration")
    fig.update_yaxes(title_text="Constraint Value")
    
    fig.show()
    #fig.write_html("constraint_progress.html")

