from arango import ArangoClient
from langchain_community.graphs.arangodb_graph import ArangoGraph
import nx_arangodb as nx_db

# Load ArangoDB credentials from environment variables
ARANGO_HOST = os.getenv("ARANGO_HOST", "http://localhost:8529")
USERNAME = os.getenv("ARANGO_USERNAME", "root")
PASSWORD = os.getenv("ARANGO_PASSWORD", "")
GRAPH_NAME = os.getenv("GRAPH_NAME", "default_graph")

print(f"🔗 Connecting to ArangoDB at {ARANGO_HOST} as {USERNAME}")

# Initialize ArangoDB Connection
try:
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(username=USERNAME, password=PASSWORD, verify=True)
    print("Connected to ArangoDB!")
except Exception as e:
    print(f"Connection Failed: {e}")
    exit(1)

# Initialize NetworkX-ArangoDB Graph
graph = None

if db.has_graph(GRAPH_NAME):
    try:
        graph = ArangoGraph(db=db)
        print(f"Graph '{GRAPH_NAME}' connected successfully!")
    except Exception as e:
        print(f"Error initializing graph: {e}")
        exit(1)
else:
    print(f"Graph '{GRAPH_NAME}' not found in ArangoDB.")
    exit(1)

# Function to query ArangoDB using AQL
def query_db(aql_query: str):
    """
    Executes an AQL query and returns the result.
    Args:
        aql_query (str): The AQL query string.
    Returns:
        list | dict: Query results or error message.
    """
    try:
        result = db.aql.execute(aql_query)
        return list(result)
    except Exception as e:
        return {"error": str(e)}

# Function to store graph data
def store_graph_in_db(edges):
    """
    Stores edges in ArangoDB.
    Args:
        edges (list): A list of edge dictionaries with 'source' and 'target' keys.
    """
    if not db.has_collection("edges"):
        db.create_collection("edges")
    for edge in edges:
        db.collection("edges").insert({
            "_from": f"nodes/{edge['source']}",
            "_to": f"nodes/{edge['target']}"
        })

# Function to retrieve graph as NetworkX graph
def get_networkx_graph():
    """
    Retrieves the graph from ArangoDB and converts it to a NetworkX graph.
    Returns:
        networkx.Graph | None: The NetworkX graph if available, else None.
    """
    if "nx_db" in globals():
        return nx_db.get_graph()
    else:
        print("NetworkX-ArangoDB Graph not initialized.")
        return None
