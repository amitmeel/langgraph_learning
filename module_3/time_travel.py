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

# System message
sys_msg = SystemMessage(content="You are a helpful assistant tasked with performing arithmetic on a set of inputs.")

# Node
def assistant(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# Graph
builder = StateGraph(MessagesState)

# Define nodes: these do the work
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

# Define edges: these determine the control flow
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")

memory = MemorySaver()
graph = builder.compile(checkpointer=MemorySaver())


# Input
initial_input = {"messages": HumanMessage(content="Multiply 2 and 3")}

# Thread
thread = {"configurable": {"thread_id": "1"}}

# Run the graph until the first interruption
for event in graph.stream(initial_input, thread, stream_mode="values"):
    event['messages'][-1].pretty_print()

# We can use get_state to look at the current state of our graph, given the thread_id!
print(graph.get_state({'configurable': {'thread_id': '1'}}))
#We can also browse the state history of our agent.
# get_state_history lets us get the state at all prior steps.
all_states = [s for s in graph.get_state_history(thread)]
#The first element is the current state, just as we got from get_state.


###########################
#  REPLAYING
###########################
## lets look back the human input
to_replay = all_states[-2]
print(to_replay.values)
print(to_replay.config)
# to replay from here , we simply pass the config back to the agent
# The graph knows that this checkpoint has aleady been executed.
# It just re-plays from this checkpoint!
for event in graph.stream(None, to_replay.config, stream_mode="values"):
    event['messages'][-1].pretty_print()


##############################
# FORKING
##############################
# forking:What if we want to run from that same step, but with a different input.
to_fork = all_states[-2]
print(f"config of step which we are forking: {to_fork.config}")
# Let's modify the state at this checkpoint.
# We can just run update_state with the checkpoint_id supplied.
# Remember how our reducer on messages works:
# It will append, unless we supply a message ID.
# We supply the message ID to overwrite the message, rather than appending to state!
# So, to overwrite the the message, we just supply the message ID,
## which we have to_fork.values["messages"].id.

fork_config = graph.update_state(
    to_fork.config,
    {"messages": [HumanMessage(content='Multiply 5 and 3', 
                               id=to_fork.values["messages"][0].id)]},
)
# above creates a new, forked checkpoint.
# We can see the current state of our agent has been updated with our fork.
all_states = [state for state in graph.get_state_history(thread) ]
all_states[0].values["messages"]
# Now, when we stream, the graph knows this checkpoint has never been executed.
# So, the graph runs, rather than simply re-playing.
for event in graph.stream(None, fork_config, stream_mode="values"):
    event['messages'][-1].pretty_print()

