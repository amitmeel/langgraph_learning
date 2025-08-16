from pprint import pprint
from typing import TypedDict
from langchain_core.messages import HumanMessage, AnyMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

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

messages = [AIMessage(content="so you were saying youn were working deep research agents" , name="gemini")]
messages.append(HumanMessage(content="yeah! that's right.", name="amit"))
messages.append(AIMessage(content="Great, do you want to learn anything specific", nbame="gemini"))
messages.append(HumanMessage(content="I wan to learn about common archtecture of deep research agent which has to procvess the invoice again Purchase order.explain it in details"))

# result = llm.invoke(messages)
# print(result)
# print(result.response_metadata)

def multiply(a: int, b: int) -> int:
    """Multiply a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b

llm_with_tools = llm.bind_tools([multiply])
tool_call = llm_with_tools.invoke([HumanMessage(content=f"What is 2 multiplied by 3", name="Lance")])
print(tool_call)
print(tool_call.tool_calls)

from typing import Annotated
from langgraph.graph.message import add_messages

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

from langgraph.graph import MessagesState

# below is exactly similar to above Messagestate class
class MessagesState(MessagesState):
    # Add any keys needed beyond messages, which is pre-built 
    pass

from langgraph.graph import StateGraph, START, END

# nODE
def tool_calling_llm(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_edge(START, "tool_calling_llm")
builder.add_edge("tool_calling_llm", END)
graph = builder.compile()

messages = graph.invoke({"messages": HumanMessage(content="Hello!")})
for m in messages['messages']:
    m.pretty_print()

messages = graph.invoke({"messages": HumanMessage(content="Multiply 2 and 3")})
for m in messages['messages']:
    m.pretty_print()

