import graphviz
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import os

def visualize_tree(root, output_file_name = "mcts_tree"):
    dot = graphviz.Digraph(comment = 'MCTS Tree')

    def add_nodes_edges(node):
        label = f"H {node.hard_result:.2f} S {node.soft_result:.2f}, visits {node.visits}" #{node.score_hard:.2f} {node.score_soft:.2f}, visits {node.visits}"
        if node.path:
            last_event_id = max(node.path.keys())
            last_event = node.path[last_event_id]

            label += f"\n{last_event['Id']} {last_event.get('Name', 'Unnamed')} D{last_event.get('WeekDay', '?')} P{last_event.get('Timeslot', '?')} R{last_event.get('RoomId', '?')}"

        dot.node(str(id(node)), label=label)

        for child in node.children:
            dot.edge(str(id(node)), str(id(child)))
            add_nodes_edges(child)

    add_nodes_edges(root)

    output_dir = "mcts_tree"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file_name = os.path.join(output_dir, output_file_name)
    
    dot.render(output_file_name, format="pdf")


def plot_progress(iterations, current_hard, best_hard, current_soft, best_soft, output_file_name = "constraint_progress.html"):
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
    
    output_dir = "constraint_progress"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file_name = os.path.join(output_dir, output_file_name)

    fig.write_html(output_file_name)
    #fig.show()

