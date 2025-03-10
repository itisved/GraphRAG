import os
from arango import ArangoClient
from langchain_openai import ChatOpenAI
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain
from langchain_community.graphs.arangodb_graph import ArangoGraph
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph
from db_arangodb import query_db, get_networkx_graph
from graph_networkx import apply_networkx_algorithm
from graph_cugraph import apply_cugraph_algorithm
from visualization_graph import visualize_result

# ✅ Set up ArangoDB connection
ARANGO_HOST = "https://14c3433deb43.arangodb.cloud:8529"
USERNAME = "root"
PASSWORD = "8evufUJ4rbSVeiZbAIHZ"
GRAPH_NAME = "NTX"

try:
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(username=USERNAME, password=PASSWORD, verify=True)
    print("✅ Connected to ArangoDB!")
except Exception as e:
    print(f"❌ Failed to connect to ArangoDB: {e}")
    exit(1)

# ✅ Set OpenAI API Key
# os.environ["OPENAI_API_KEY"] = ""

# ✅ Initialize ArangoGraph
graph = None

if db.has_graph(GRAPH_NAME):
    try:
        graph = ArangoGraph(db=db)
        print(f"✅ Graph '{GRAPH_NAME}' connected successfully!")
    except Exception as e:
        print(f"❌ Error initializing graph: {e}")
        exit(1)
else:
    print(f"⚠️ Graph '{GRAPH_NAME}' not found in ArangoDB.")
    exit(1)

# ✅ LangChain Setup for ArangoDB QA
chain = ArangoGraphQAChain.from_llm(
    ChatOpenAI(temperature=0),
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True
)

# ✅ Query Function for ArangoDB
def query_arangodb(question):
    """
    Queries the ArangoDB graph using LangChain.
    """
    try:
        result = chain.invoke(question)
        return result
    except Exception as e:
        return {"error": f"❌ Error executing AQL query: {e}"}

# ✅ Prompt Templates for Classification & Code Generation
classify_prompt = PromptTemplate.from_template(
    "Determine if this query requires an ArangoDB AQL query, a NetworkX graph algorithm, or a cuGraph algorithm. "
    "Respond with one of: 'AQL', 'Nx', or 'Nx-Cu'. Query: {query}"
)

generate_prompt = PromptTemplate.from_template(
    "Generate {category} code for the following user query: {query}. Ensure the code is complete and valid."
)

# ✅ Function to call ChatGPT
def call_chatgpt(prompt):
    response = ChatOpenAI(temperature=0).invoke(prompt)  # Use LangChain’s `invoke`
    return response.content.strip()

# ✅ Classify Query Function
def classify_query(user_query):
    classify_runnable = RunnableLambda(lambda x: call_chatgpt(classify_prompt.format(query=x)))
    return classify_runnable.invoke(user_query)

# ✅ Generate Code Function
def generate_code(user_query, category):
    generate_runnable = RunnableLambda(lambda x: call_chatgpt(generate_prompt.format(query=x, category=category)))
    return generate_runnable.invoke(user_query)

# ✅ Handle User Query and Execute Workflow
def handle_user_query(user_query):
    """
    Classifies the query, routes it appropriately, and returns the response.
    """
    category = classify_query(user_query)

    if category == "AQL":
        # Query ArangoDB if classified as AQL
        response = query_arangodb(user_query)
    else:
        # Generate code for Nx or Nx-Cu categories
        response = generate_code(user_query, category)

    return response  # ✅ Return output

# ✅ Define LangGraph Workflow
workflow = StateGraph(dict)

def parse_algorithm_code(code):
    """
    Parses the code to extract algorithm name and parameters.
    """
    parts = code.split('(')
    algorithm_name = parts[0].strip()
    params_str = parts[1].rstrip(')')
    params = {}

    # Assuming parameters are in the form key=value
    for param in params_str.split(','):
        key, value = param.split('=')
        params[key.strip()] = value.strip()

    return algorithm_name, params

def execute_workflow(state):
    """
    Executes the appropriate workflow based on category.
    Dynamically determines which module should process the generated code.
    """
    category = state["category"]
    code = state["code"]

    # Process AQL Queries with ArangoDB
    if category == "AQL":
        result = query_db(code)

    # Process NetworkX Algorithms
    elif category == "Nx":
        algorithm_name, params = parse_algorithm_code(code)
        result = apply_networkx_algorithm(algorithm_name, **params)

    # Process cuGraph Algorithms
    elif category == "Nx-Cu":
        result = apply_cugraph_algorithm(code)

    # Handle Visualization
    elif category == "Viz":
        result = visualize_result(code)

    else:
        result = {"error": "Invalid category"}

    # Send result to visualization module if it's not a visualization query
    if category in ["AQL", "Nx", "Nx-Cu"]:
        visualization_output = visualize_result(result)
        return {"result": result, "visualization": visualization_output}

    return {"result": result}

# Adding nodes to LangGraph
workflow.add_node("execute", execute_workflow)
workflow.set_entry_point("execute")
app = workflow.compile()

# Example usage
# if __name__ == "__main__":
#     user_query = "Find the most influential patent in the network using centrality measures."
#     response = handle_user_query(user_query)
#     inputs = {"category": response["category"], "code": response["code"]}
#     final_output = app.stream(inputs)
#     print("Final Output:", final_output)
if __name__ == "__main__":
    user_query = "Retrieve the node with most citated patents"
    response = handle_user_query(user_query)

    # Debugging: Inspect the response format
    print("Response from handle_user_query:", response)

    # Ensure response is a dictionary before accessing keys
    if isinstance(response, dict):
        inputs = {"category": response["category"], "code": response["code"]}
        final_output = app.stream(inputs)
        print("Final Output:", final_output)
    else:
        print("Error: Response is not in the expected dictionary format.")
