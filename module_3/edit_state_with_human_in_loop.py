import asyncio
import getpass
import os
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage,SystemMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

# Load environment variables from .env file
load_dotenv()

_set_env("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def multiply(a: int, b: int) -> int:
    """Multiply a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b

# This will be a tool
def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b

def divide(a: int, b: int) -> float:
    """Divide a by b.

    Args:
        a: first int
        b: second int
    """
    return a / b

tools = [add, multiply, divide]
llm_with_tools = llm.bind_tools(tools)


# motivations for human-in-the-loop:

# (1) Approval - We can interrupt our agent, surface state to a user, and allow the user to accept an action
# (2) Debugging - We can rewind the graph to reproduce or avoid issues
# (3) Editing - You can modify the state


# System message
# sys_msg = SystemMessage(content="You are a helpful assistant tasked with performing arithmetic on a set of inputs.")

# # Node
# def assistant(state: MessagesState):
#    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# # Graph
# builder = StateGraph(MessagesState)

# # Define nodes: these do the work
# builder.add_node("assistant", assistant)
# builder.add_node("tools", ToolNode(tools))

# # Define edges: these determine the control flow
# builder.add_edge(START, "assistant")
# builder.add_conditional_edges(
#     "assistant",
#     # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
#     # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
#     tools_condition,
# )
# builder.add_edge("tools", "assistant")

# memory = MemorySaver()
# graph = builder.compile(interrupt_before=["assistant"], checkpointer=memory)
# # We can see in above line the graph is interrupted before the chat model responds
# ## (assistant reponds).
# # Input
# initial_input = {"messages": "Multiply 2 and 3"}

# # Thread
# thread = {"configurable": {"thread_id": "1"}}

# # Run the graph until the first interruption
# for event in graph.stream(initial_input, thread, stream_mode="values"):
#     event['messages'][-1].pretty_print()

# state = graph.get_state(thread)
# print(f"{'#'*10} CURRENT STATE {'#'*10}")
# print(state)
# # print(state.values['messages'][-1].content)
# # print(state.values['messages'][-1].id)


# # now, we can directly apply a state update.
# # Remember, updates to the messages key will use the add_messages reducer:

# # If we want to over-write the existing message, we can supply the message id.
# # If we simply want to append to our list of messages, 
# ## then we can pass a message without an id specified, as shown below.
# graph.update_state(
#     thread,
#     {"messages": [HumanMessage(content="No, actually multiply 3 and 3!")]},
# )
# # We called update_state with a new message.
# # The add_messages reducer appends it to our state key, messages.
# new_state = graph.get_state(thread).values
# for m in new_state['messages']:
#     m.pretty_print()

# # let's proceed with our agent, simply by passing None and allowing it proceed 
# ## from the current state.
# # We emit the current and then proceed to execute the remaining nodes.
# for event in graph.stream(None, thread, stream_mode="values"):
#     event['messages'][-1].pretty_print()

# # we're back at the assistant, which has our breakpoint.
# # We can again pass None to proceed.
# for event in graph.stream(None, thread, stream_mode="values"):
#     event['messages'][-1].pretty_print()


# Now, what if we want to allow for human feedback to perform this state update?
# We'll add a node that serves as a placeholder for human feedback within our agent.
# This human_feedback node allow the user to add feedback directly to state.
# We specify the breakpoint using interrupt_before our human_feedback node.
# We set up a checkpointer to save the state of the graph up until this node.

# System message
sys_msg = SystemMessage(content="You are a helpful assistant tasked with performing arithmetic on a set of inputs.")

# no-op node that should be interrupted on
def human_feedback(state: MessagesState):
    pass

# Assistant node
def assistant(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# Graph
builder = StateGraph(MessagesState)

# Define nodes: these do the work
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_node("human_feedback", human_feedback)

# Define edges: these determine the control flow
builder.add_edge(START, "human_feedback")
builder.add_edge("human_feedback", "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "human_feedback")

memory = MemorySaver()
graph = builder.compile(interrupt_before=["human_feedback"], checkpointer=memory)

#We will get feedback from the user.
# We use .update_state to update the state of the graph with the human response we get, as before.
# We use the as_node="human_feedback" parameter to apply this state update as the specified node,
## human_feedback.
# Input
initial_input = {"messages": "Multiply 2 and 3"}

# Thread
thread = {"configurable": {"thread_id": "6"}}

# Run the graph until the first interruption
for event in graph.stream(initial_input, thread, stream_mode="values"):
    event["messages"][-1].pretty_print()
    
# Get user input
user_input = input("Tell me how you want to update the state: ")

# We now update the state as if we are the human_feedback node
graph.update_state(thread, {"messages": user_input}, as_node="human_feedback")

# Continue the graph execution
for event in graph.stream(None, thread, stream_mode="values"):
    event["messages"][-1].pretty_print()

# Continue the graph execution
for event in graph.stream(None, thread, stream_mode="values"):
    event["messages"][-1].pretty_print()