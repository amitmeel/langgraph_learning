from pprint import pprint
from typing import TypedDict, Literal
from langchain_core.messages import HumanMessage, AnyMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, RemoveMessage

from langgraph.graph import START, StateGraph, MessagesState, END
from langgraph.prebuilt import tools_condition, ToolNode


# import mlflow

# mlflow.langchain.autolog()


from dotenv import load_dotenv
import os, getpass

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

# Load environment variables from .env file
load_dotenv()

# set the gemini keys if it is not avaialble in environment variable
_set_env("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

class State(MessagesState):
    summary: str

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# DEFINE THE NODE AND LOGIC TO CALL THE MODEL
def call_model(state: State):
    # get summary of list of messages if it exists
    summary = state.get("summary", "")

    if summary:
        # add summary to system message
        system_message = f" summary of earlier conversation: {summary}"

        # append the summary to newer message
        messages = [SystemMessage(content=system_message)] + state["messages"]
    
    else:
        messages = state["messages"]

    response = llm.invoke(messages)
    return {"messages": response}

# DEFINE THE NODE TO SUMMARIZE THE EXISTING MESSAGE HISTORY
def summarize_conversation(state: State):

    # first we get any existing summary
    summary = state.get("summary", "")

    # create our summarization prompt
    if summary:

        summary_message = (
            f"This is the summary of existing conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = "Create a summary of the conversation above:"

    # add prompt to our history 
    messages = state["messages"] + [HumanMessage(content=summary_message)]

    response = llm.invoke(messages)

    # delete all but the last 2 recent messages
    delete_messages = [RemoveMessage(id=m.id) for m in messages[:-2]]
    return {"summary": response.content, "messages": delete_messages}


#  add a conditional edge to determine whether
# ## to produce a summary based on the conversation length.
# Determine whether to end or summarize the conversation
def should_continue(state: State) -> Literal ["summarize_conversation",END]:
    
    """Return the next node to execute."""
    
    messages = state["messages"]
    
    # If there are more than six messages, then we summarize the conversation
    if len(messages) > 6:
        return "summarize_conversation"
    
    # Otherwise we can just end
    return END

# state is transient to a single graph execution.
# we can use persistence to address this
#LangGraph can use a checkpointer to automatically save the graph state after each step.
# This built-in persistence layer gives us memory, allowing LangGraph to pick up from 
## the last state update.
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START

# Define a new graph
workflow = StateGraph(State)
workflow.add_node("conversation", call_model)
workflow.add_node(summarize_conversation)

# Set the entrypoint as conversation
workflow.add_edge(START, "conversation")
workflow.add_conditional_edges("conversation", should_continue)
workflow.add_edge("summarize_conversation", END)

# Compile
memory = MemorySaver()
## uncomment it when running this as script
# graph = workflow.compile(checkpointer=memory)
# when you start the langgraph studio don't use the checkpointer
# as With LangGraph API, persistence is handled automatically by the platform,
# # so providing a custom checkpointer (type <class 'langgraph.checkpoint.memory.InMemorySaver'>)
# # here isn't necessary and will be ignored when deployed.
graph = workflow.compile()


# The checkpointer saves the state at each step as a checkpoint.
# These saved checkpoints can be grouped into a thread of conversation.
#Think about Slack as an analog: different channels carry different conversations.
# Threads are like Slack channels, capturing grouped collections of state 
# ## (e.g., conversation).
# Create a thread
# config = {"configurable": {"thread_id": "1"}}
# # Create a thread
# config = {"configurable": {"thread_id": "1"}}

# # Start conversation
# input_message = HumanMessage(content="hi! I'm AMIT")
# output = graph.invoke({"messages": [input_message]}, config) 
# for m in output['messages'][-1:]:
#     m.pretty_print()

# input_message = HumanMessage(content="what's my name?")
# output = graph.invoke({"messages": [input_message]}, config) 
# for m in output['messages'][-1:]:
#     m.pretty_print()

# input_message = HumanMessage(content="i like the 49ers!")
# output = graph.invoke({"messages": [input_message]}, config) 
# for m in output['messages'][-1:]:
#     m.pretty_print()

# print(graph.get_state(config).values.get("summary",""))

# #The config with thread ID allows us to proceed from the previously logged state!
# input_message = HumanMessage(content="i like Nick Bosa, isn't he the highest paid defensive player?")
# output = graph.invoke({"messages": [input_message]}, config) 
# for m in output['messages'][-1:]:
#     m.pretty_print()

# print(graph.get_state(config).values.get("summary",""))