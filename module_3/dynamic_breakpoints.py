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

from typing import TypedDict
import uuid

from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

# Define the graph state
class State(TypedDict):
    summary: str

# Simulate an LLM summary generation
def generate_summary(state: State) -> State:
    return {
        "summary": "The cat sat on the mat and looked at the stars."
    }

# Human editing node
def human_review_edit(state: State) -> State:
    result = interrupt({
        "task": "Please review and edit the generated summary if necessary.",
        "generated_summary": state["summary"]
    })
    return {
        "summary": result["edited_summary"]
    }

# Simulate downstream use of the edited summary
def downstream_use(state: State) -> State:
    print(f"✅ Using edited summary: {state['summary']}")
    return state

# Build the graph
builder = StateGraph(State)
builder.add_node("generate_summary", generate_summary)
builder.add_node("human_review_edit", human_review_edit)
builder.add_node("downstream_use", downstream_use)

builder.set_entry_point("generate_summary")
builder.add_edge("generate_summary", "human_review_edit")
builder.add_edge("human_review_edit", "downstream_use")
builder.add_edge("downstream_use", END)

# Set up in-memory checkpointing for interrupt support
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# Invoke the graph until it hits the interrupt
config = {"configurable": {"thread_id": uuid.uuid4()}}
result = graph.invoke({}, config=config)

# Output interrupt payload
print(result["__interrupt__"])
# Example output:
# > [
# >     Interrupt(
# >         value={
# >             'task': 'Please review and edit the generated summary if necessary.',
# >             'generated_summary': 'The cat sat on the mat and looked at the stars.'
# >         },
# >         id='...'
# >     )
# > ]

# Resume the graph with human-edited input
edited_summary = "The cat lay on the rug, gazing peacefully at the night sky."
resumed_result = graph.invoke(
    Command(resume={"edited_summary": edited_summary}),
    config=config
)
print(resumed_result)

##########################################################
# EXPLAINATION
# State vs. interrupt payload

# Your State (TypedDict) defines what the graph state should contain between nodes (in your case, only "summary").

# But when you call interrupt(...), the dict you get back from resuming does not go into the graph state automatically.
# It’s just the return value from interrupt(...).

# So for this node:

# def human_review_edit(state: State) -> State:
#     result = interrupt({
#         "task": "...",
#         "generated_summary": state["summary"]
#     })
#     return {"summary": result["edited_summary"]}


# 👉 The only thing you merge into the graph state is the "summary" key, because that’s what you return.

# 2. What’s in the state during execution?

# At the moment of interrupt, the state still looks like:

# {"summary": "The cat sat on the mat and looked at the stars."}


# When you resume with:

# Command(resume={"edited_summary": "The cat lay on the rug..."})


# inside human_review_edit, result will be:

# {"edited_summary": "The cat lay on the rug..."}


# But after your return, the state becomes:

# {"summary": "The cat lay on the rug..."}


# The edited_summary is not kept in the state unless you explicitly return it.