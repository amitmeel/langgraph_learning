from typing import TypedDict

class State(TypedDict):
    graph_state: str

## Nodes are just python function
## Nodes operate on states
## By default each node state will override the prior state value
def node_1(state):
    print("Node 1")
    return {"graph_state": state["graph_state"] + " I'm"}

def node_2(state):
    print("Node 2")
    return {"graph_state": state["graph_state"] + " Happy"}

def node_3(state):
    print("Node 3")
    return {"graph_state": state["graph_state"] + " Sad"}

## Edges 
### Edges simply connect the nodes
### Normal edges are sued if you want to go from node1 to node2
### conditional edges are used to optionally route between nodes
### the conditional edge is implemented as a function that returns the next node based on some logic

import random
from typing import Literal

def decide_mood(state) -> Literal["node_2", "node_3"]:
    # often we will use node state to decide on the next node to visit
    user_input = state["graph_state"]

    # let's do 50/50 split between node_2 and node_3
    if random.random() < 0.5: 
        return "node_2"
    return "node_3"


## GRAPH CONSTRUCTION
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END

# build graph
builder = StateGraph(State)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

#logic
builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_mood)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

#compile the graph
graph = builder.compile()

# Generate and save Graph PNG (requires graphviz)
# try:
#     # This will save the graph as a PNG file
#     png_data = graph.get_graph().draw_mermaid_png()
#     with open("langgraph_visualization.png", "wb") as f:
#         f.write(png_data)
#     print("Graph saved as 'langgraph_visualization.png'")
# except Exception as e:
#     print(f"PNG generation failed: {e}")
#     print("Make sure you have graphviz installed: pip install graphviz")

## GRAPH INVOCATION
### compiled graph implements the runnable protocol
### this provides a standard way to execute langchain components
### `invoke` is one of the standard method in this interface


#### here input is a dictionary {"graph_state": "Hi, this is amit"}
#### which sets the initial value for our graph state dict
#### when invoke is called, the graph starts execution from the `START` node.
#### The execution continues until it reaches the `END` node.
## NOTE: `invoke` runs the graph synchrounously meaning this waits for each step to complete 
### before moving to next. it returns the final state of the graph after all nodes have executed

# final_state = graph.invoke({"graph_state": "Hi, this is amit"})
# print(final_state)
# print("Final graph_state value:", final_state["graph_state"])


# --------------------------
# DEBUG EXECUTION FUNCTION
# --------------------------
def debug_invoke(graph, initial_state):
    state = initial_state
    print("\n=== Graph Execution Trace ===")
    print("START:", state)

    for event in graph.stream(initial_state):
        for node, node_state in event.items():
            print(f"\nNode executed: {node}")
            print("Updated State:", node_state)
            state = node_state

    print("\n=== Final State ===")
    print(state)
    return state


# --------------------------
# RUN GRAPH WITH DEBUG
# --------------------------
final_state = debug_invoke(graph, {"graph_state": "Hi, this is amit"})


