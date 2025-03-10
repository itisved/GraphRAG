import cugraph as cg
import networkx as nx
import cudf
from db_arangodb import get_networkx_graph

def apply_cugraph_algorithm(algorithm_name: str, **kwargs):
    """
    Dynamically applies a cuGraph algorithm to the graph.
    Args:
        algorithm_name (str): Name of the cuGraph algorithm to execute.
        **kwargs: Additional parameters for the algorithm.
    Returns:
        Result of the algorithm execution or an error message.
    """
    G_nx = get_networkx_graph()
    if G_nx is None:
        return {"error": "Graph is empty or not loaded"}
    
    df = nx.to_pandas_edgelist(G_nx)
    G_cu = cg.from_cudf_edgelist(cudf.DataFrame(df), source="source", destination="target")
    
    if hasattr(cg, algorithm_name):
        algorithm = getattr(cg, algorithm_name)
        return algorithm(G_cu, **kwargs)
    else:
        return {"error": f"Unsupported cuGraph algorithm: {algorithm_name}"}
