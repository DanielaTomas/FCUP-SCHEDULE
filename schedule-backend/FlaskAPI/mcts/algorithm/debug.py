import graphviz
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import os

def visualize_tree(root, output_file_name = "mcts_tree"):
    print("Processing the tree...")
    dot = graphviz.Digraph(comment = 'MCTS Tree')

    def add_nodes_edges(node):
        if not node: return
        label = ""
        dot.node(str(id(node)), label=label, shape="point", width="0.01", height="0.01")

        for child in node.children:
            dot.edge(str(id(node)), str(id(child)), dir="none", style="solid", penwidth="0.5")
            add_nodes_edges(child)

    try:
        add_nodes_edges(root)

        output_dir = "mcts_tree"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file_name)

        dot.render(output_path, format="pdf", cleanup=True)
        print(f"Tree successfully saved as {output_path}.pdf\n")

    except graphviz.ExecutableNotFound:
        print("Error: Graphviz is not installed or not in the system PATH.")
    except graphviz.CalledProcessError:
        print("Error: Graphviz failed to render the file. The tree may be too large.")
    except MemoryError:
        print("Error: Not enough memory to render the graph.")
    except Exception as e:
        print(f"Unexpected error: {e}")


def plot_progress(iterations, current_hard, best_hard, current_soft, best_soft, output_file_name = "constraint_progress.html"):
    print("Processing the constraint progress...")
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
    print(f"Plot saved successfully to {output_file_name}\n")

