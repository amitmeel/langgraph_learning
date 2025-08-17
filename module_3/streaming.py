import asyncio
import getpass
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage,SystemMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langgraph.graph import END, START, StateGraph

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

# Load environment variables from .env file
load_dotenv()

_set_env("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

class State(MessagesState):
    summary: str

# Define the logic to call the model
def call_model(state: State):
    # Get summary if it exists
    summary = state.get("summary", "")

    # If there is summary, then we add it
    if summary:
        # Add summary to system message
        system_message = f"Summary of conversation earlier: {summary}"
        # Append summary to any newer messages
        messages = [SystemMessage(content=system_message)] + state["messages"]
    else:
        messages = state["messages"]
    
    response = llm.invoke(messages)
    return {"messages": response}

def summarize_conversation(state: State):
    # First, we get any existing summary
    summary = state.get("summary", "")
    # Create our summarization prompt 
    if summary:
        # A summary already exists
        summary_message = (
            f"This is summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = "Create a summary of the conversation above:"

    # Add prompt to our history
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = llm.invoke(messages)
    # Delete all but the 2 most recent messages
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}

# Determine whether to end or summarize the conversation
def should_continue(state: State):
    """Return the next node to execute."""
    messages = state["messages"]
    
    # If there are more than six messages, then we summarize the conversation
    if len(messages) > 6:
        return "summarize_conversation"
    
    # Otherwise we can just end
    return END

builder = StateGraph(MessagesState)
builder.add_node("conversation", call_model)
builder.add_node("summarize_conversation", summarize_conversation)

builder.add_edge(START, "conversation")
builder.add_conditional_edges("conversation", should_continue)
builder.add_edge("summarize_conversation", END)

memory = MemorySaver()
# COMPILE THE GRAPH
graph = builder.compile(checkpointer=memory)

# stream_mode:
## values: This streams the full state of the graph after each node is called.
## updates: This streams updates to the state of the graph after each node is called.

# Create a thread
# config = {"configurable": {"thread_id": "1"}}
# Start conversation
# for chunk in graph.stream({"messages": [HumanMessage(content="hi! I'm Lance")]}, config, stream_mode="updates"):
#     print(chunk)
# Start conversation
# for chunk in graph.stream({"messages": [HumanMessage(content="hi! I'm Lance")]}, config, stream_mode="updates"):
#     chunk['conversation']["messages"].pretty_print()


# Create a thread
# config = {"configurable": {"thread_id": "2"}}
# # Start conversation
# for chunk in graph.stream({"messages": [HumanMessage(content="hi! I'm Lance")]}, config, stream_mode="values"):
#     print(chunk)
# Start conversation
# input_message = HumanMessage(content="hi! I'm Lance")
# for event in graph.stream({"messages": [input_message]}, config, stream_mode="values"):
#     for m in event['messages']:
#         m.pretty_print()
#     print("---"*25)

# with chat model calls it is common to stream the tokens as they are generated.
## We can do this using the .astream_events method, which streams back events as
### they happen inside nodes!
## Each event is a dict with a few keys:
### event: This is the type of event that is being emitted.
### name: This is the name of event.
### data: This is the data associated with the event.
### metadata: Containslanggraph_node, the node emitting the event.
# Create a thread
config = {"configurable": {"thread_id": "4"}}
input_messages = [HumanMessage(content="tell me more about messi")]

async def run_graph(input_messages, config):
    # async for event in graph.astream_events({"messages": input_messages}, config=config, version="v2"):
    #     print(f"Node: {event['metadata'].get('langgraph_node','')}. Type: {event['event']}. Name: {event['name']}")
    
    node_to_stream = 'conversation'
    # async for event in graph.astream_events({"messages": [input_messages]}, config, version="v2"):
    #     # Get chat model tokens from a particular node 
    #     if event["event"] == "on_chat_model_stream" and event['metadata'].get('langgraph_node','') == node_to_stream:
    #         print(event["data"])

    async for event in graph.astream_events({"messages": [input_messages]}, config, version="v2"):
        # Get chat model tokens from a particular node 
        if event["event"] == "on_chat_model_stream" and event['metadata'].get('langgraph_node','') == node_to_stream:
            data = event["data"]
            print(data["chunk"].content, end="|")
asyncio.run(run_graph(input_messages, config))