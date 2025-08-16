from pprint import pprint
from typing import TypedDict
from langchain_core.messages import HumanMessage, AnyMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
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


def multiply(a: int, b: int) -> int:
    """Multiply a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b

def addition(a: int, b: int) -> int:
    """addition of  a and b

    Args:
        a: first int
        b: second int
    """
    return a + b


llm_with_tools = llm.bind_tools([multiply, addition])


from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langgraph.graph.message import add_messages, AnyMessage
from typing import TypedDict, Annotated

class MessageState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# Node
def tool_calling_llm(state:MessageState):
    return {"messages": llm_with_tools.invoke(state["messages"])}

# build the graph
builder = StateGraph(MessageState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([multiply, addition]))
builder.add_edge(START,"tool_calling_llm")
builder.add_conditional_edges(
    "tool_calling_llm",
    # if the latest message (result) from assistant is a tool call -> tool_condition routes to tools
    # if the latest message(results) from assistant is not a tool call -> tool_condition routes to END
    tools_condition,
    # Optional mapping of paths to node names.
    {"tools": "tools", "__end__": "__end__"}
)
builder.add_edge("tools", END)
graph = builder.compile()

# final_state = graph.invoke({"messages":"add 2 and 3"}, print_mode="debug")
# print(final_state)
