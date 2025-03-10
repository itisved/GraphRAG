import networkx as nx
import matplotlib.pyplot as plt
from db_arangodb import get_networkx_graph
from graph_networkx import apply_networkx_algorithm
from graph_cugraph import apply_cugraph_algorithm

def visualize_graph(source, algorithm_code=None):
    """
    Visualizes the graph from ArangoDB, NetworkX, or cuGraph.

    Args:
        source (str): 'arangodb', 'networkx', or 'cugraph'.
        algorithm_code (str, optional): Dynamically generated code for processing.
    Returns:
        dict: Message confirming visualization.
    """
    try:
        # Load graph from the selected source
        if source == "arangodb":
            G = get_networkx_graph()  # Load graph from ArangoDB using nx-arangodb
        elif source == "networkx":
            G = apply_networkx_algorithm(algorithm_code) if algorithm_code else get_networkx_graph()
        elif source == "cugraph":
            if algorithm_code:
                G = apply_cugraph_algorithm(algorithm_code)
            else:
                raise ValueError("cuGraph requires algorithm execution first.")
        else:
            raise ValueError("Invalid source. Choose 'arangodb', 'networkx', or 'cugraph'.")

        # Draw the graph
        plt.figure(figsize=(10, 6))
        pos = nx.spring_layout(G, seed=42)  # Position nodes for visualization
        nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='gray', node_size=1000, font_size=10)

        plt.title(f"Graph Visualization from {source}")
        plt.show()

        return {"message": f"Graph visualization generated from {source}"}
    except Exception as e:
        return {"error": str(e)}

def visualize_result(data):
    print("Visualization function not implemented yet.")
    return {"message": "Visualization not implemented"}
