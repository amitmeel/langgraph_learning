from typing_extensions import TypedDict
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END

# class OverallState(TypedDict):
#     foo: int

# class PrivateState(TypedDict):
#     baz: int

# def node_1(state: OverallState) -> PrivateState:
#     print("---Node 1---")
#     return {"baz": state['foo'] + 1}

# def node_2(state: PrivateState) -> OverallState:
#     print("---Node 2---")
#     return {"foo": state['baz'] + 1}

# # Build graph
# builder = StateGraph(OverallState)
# builder.add_node("node_1", node_1)
# builder.add_node("node_2", node_2)

# # Logic
# builder.add_edge(START, "node_1")
# builder.add_edge("node_1", "node_2")
# builder.add_edge("node_2", END)

# # Add
# graph = builder.compile()

# graph.invoke({"foo" : 1})
###############################################################
# By default, StateGraph takes in a single schema and
# ##  all nodes are expected to communicate with that schema.
# However, it is also possible to define explicit input and output schemas for a graph.
# Often, in these cases, we define an "internal" schema that contains all keys 
## relevant to graph operations.
# But, we use specific input and output schemas to constrain the input and output.

# class OverallState(TypedDict):
#     question: str
#     answer: str
#     notes: str

# def thinking_node(state: OverallState):
#     return {"answer": "bye", "notes": "... his name is Lance"}

# def answer_node(state: OverallState):
#     return {"answer": "bye Lance"}

# graph = StateGraph(OverallState)
# graph.add_node("answer_node", answer_node)
# graph.add_node("thinking_node", thinking_node)
# graph.add_edge(START, "thinking_node")
# graph.add_edge("thinking_node", "answer_node")
# graph.add_edge("answer_node", END)

# graph = graph.compile()
# graph.invoke({"question":"hi"})

#################################################################0000000000000000000000000000000000000000000000000
# Here, input / output schemas perform filtering on what keys are permitted on the input
## and output of the graph.
# In addition, we can use a type hint state: InputState to specify the input schema of
## each of our nodes.
# This is important when the graph is using multiple schemas.
# We use type hints below to, for example, show that the output of answer_node will be
## filtered to OutputState.
class InputState(TypedDict):
    question: str

class OutputState(TypedDict):
    answer: str

class OverallState(TypedDict):
    question: str
    answer: str
    notes: str

def thinking_node(state: InputState):
    return {"answer": "bye", "notes": "... his is name is Lance"}

def answer_node(state: OverallState) -> OutputState:
    return {"answer": "bye Lance"}

graph = StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)
graph.add_node("answer_node", answer_node)
graph.add_node("thinking_node", thinking_node)
graph.add_edge(START, "thinking_node")
graph.add_edge("thinking_node", "answer_node")
graph.add_edge("answer_node", END)

graph = graph.compile()
graph.invoke({"question":"hi"})
########################################################




