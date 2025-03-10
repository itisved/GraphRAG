import networkx as nx
from db_arangodb import get_networkx_graph

def apply_networkx_algorithm(algorithm_name: str, **kwargs):
    """
    Dynamically applies any NetworkX algorithm to the graph.

    :param algorithm_name: Name of the NetworkX algorithm to execute.
    :param kwargs: Additional parameters for the algorithm.
    :return: Result of the algorithm execution.
    """
    G = get_networkx_graph()  # Fetch graph from ArangoDB

    # Ensure the algorithm exists in NetworkX
    if hasattr(nx, algorithm_name):
        algorithm = getattr(nx, algorithm_name)
        try:
            return algorithm(G, **kwargs)  # Dynamically execute the function
        except TypeError as e:
            return {"error": f"Algorithm parameters error: {str(e)}"}
    else:
        return f"Unsupported NetworkX algorithm: {algorithm_name}"
