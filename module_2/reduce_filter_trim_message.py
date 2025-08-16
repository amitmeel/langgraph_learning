from pprint import pprint
from typing import TypedDict
from langchain_core.messages import HumanMessage, AnyMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage

from langgraph.graph import START, StateGraph, MessagesState
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


from pprint import pprint
from langchain_core.messages import AIMessage, HumanMessage
messages = [AIMessage(f"So you said you were researching ocean mammals?", name="Bot")]
messages.append(HumanMessage(f"Yes, I know about whales. But what others should I learn about?", name="Lance"))

for m in messages:
    m.pretty_print()
# print(llm.invoke(messages))

from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END
# # Node
# def chat_model_node(state: MessagesState):
#     return {"messages": llm.invoke(state["messages"])}

# # Build graph
# builder = StateGraph(MessagesState)
# builder.add_node("chat_model", chat_model_node)
# builder.add_edge(START, "chat_model")
# builder.add_edge("chat_model", END)
# graph = builder.compile()
# output = graph.invoke({'messages': messages})
# for m in output['messages']:
#     m.pretty_print()
#######################################################
#    REDUCER
#######################################################
# from langchain_core.messages import RemoveMessage

# # Nodes
# def filter_messages(state: MessagesState):
#     # Delete all but the 2 most recent messages
#     delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
#     return {"messages": delete_messages}

# def chat_model_node(state: MessagesState):    
#     return {"messages": [llm.invoke(state["messages"])]}

# # Build graph
# builder = StateGraph(MessagesState)
# builder.add_node("filter", filter_messages)
# builder.add_node("chat_model", chat_model_node)
# builder.add_edge(START, "filter")
# builder.add_edge("filter", "chat_model")
# builder.add_edge("chat_model", END)
# graph = builder.compile()

# # Message list with a preamble
# messages = [AIMessage("Hi.", name="Bot", id="1")]
# messages.append(HumanMessage("Hi.", name="Lance", id="2"))
# messages.append(AIMessage("So you said you were researching ocean mammals?", name="Bot", id="3"))
# messages.append(HumanMessage("Yes, I know about whales. But what others should I learn about?", name="Lance", id="4"))

# # Invoke
# output = graph.invoke({'messages': messages})
# for m in output['messages']:
#     m.pretty_print()

###############################################
# filter
###############################################
# Node
# def chat_model_node(state: MessagesState):
#     return {"messages": [llm.invoke(state["messages"][-1:])]}

# # Build graph
# builder = StateGraph(MessagesState)
# builder.add_node("chat_model", chat_model_node)
# builder.add_edge(START, "chat_model")
# builder.add_edge("chat_model", END)
# graph = builder.compile()
# messages.append(output['messages'][-1])  ## this output is from reducer
# messages.append(HumanMessage(f"Tell me more about Narwhals!", name="Lance"))
# for m in messages:
#     m.pretty_print()
# # Invoke, using message filtering
# output = graph.invoke({'messages': messages})
# ## so here state wil have all the messages but
# ### if you look at tracing we are only sending the last message to the model
# for m in output['messages']:
#     m.pretty_print()

#############################################################################
# TRIM MESSAGES (Trim messages to be below a token count.)
###############################################################
from langchain_core.messages import trim_messages

# Node
def chat_model_node(state: MessagesState):
    messages = trim_messages(
            state["messages"],
            max_tokens=100,
            strategy="last",
            token_counter=ChatGoogleGenerativeAI(model="gemini-2.5-flash"),
            allow_partial=False,
        )
    return {"messages": [llm.invoke(messages)]}

# Build graph
builder = StateGraph(MessagesState)
builder.add_node("chat_model", chat_model_node)
builder.add_edge(START, "chat_model")
builder.add_edge("chat_model", END)
graph = builder.compile()

messages.append(output['messages'][-1])
messages.append(HumanMessage(f"Tell me where Orcas live!", name="Lance"))

# Example of trimming messages
trim_messages(
            messages,
            max_tokens=100,
            strategy="last",
            token_counter=ChatGoogleGenerativeAI(model="gemini-2.5-flash"),
            allow_partial=False
        )

# Invoke, using message trimming in the chat_model_node 
messages_out_trim = graph.invoke({'messages': messages})