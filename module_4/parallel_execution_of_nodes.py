import asyncio
import getpass
import os
import operator
from dotenv import load_dotenv
from typing import Any, TypedDict, Annotated

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
_set_env("TAVILY_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

###########################################################
# class State(TypedDict):
#     # The operator.add reducer fn makes this append-only
#     state: str

# class ReturnNodeValue:
#     def __init__(self, node_secret: str):
#         self._value = node_secret

#     def __call__(self, state: State) -> Any:
#         print(f"Adding {self._value} to {state['state']}")
#         return {"state": [self._value]}

# # Add nodes
# builder = StateGraph(State)

# # Initialize each node with node_secret 
# builder.add_node("a", ReturnNodeValue("I'm A"))
# builder.add_node("b", ReturnNodeValue("I'm B"))
# builder.add_node("c", ReturnNodeValue("I'm C"))
# builder.add_node("d", ReturnNodeValue("I'm D"))

# # Flow
# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("b", "c")
# builder.add_edge("c", "d")
# builder.add_edge("d", END)
# graph = builder.compile()

# final_state = graph.invoke({"state": []})
# print(final_state)

# ###############
# # Now, let's run b and c in parallel.
# #################
# builder = StateGraph(State)

# # Initialize each node with node_secret 
# builder.add_node("a", ReturnNodeValue("I'm A"))
# builder.add_node("b", ReturnNodeValue("I'm B"))
# builder.add_node("c", ReturnNodeValue("I'm C"))
# builder.add_node("d", ReturnNodeValue("I'm D"))

# # Flow
# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("a", "c")
# builder.add_edge("b", "d")
# builder.add_edge("c", "d")
# builder.add_edge("d", END)
# graph = builder.compile()

# #This is because both b and c are writing to the same state key / channel in the same step.
# from langgraph.errors import InvalidUpdateError
# try:
#     graph.invoke({"state": []})
# except InvalidUpdateError as e:
#     print(f"An error occurred: {e}")

# # When using fan out, we need to be sure that we are using a reducer
# ## if steps are writing to the same the channel / key.
# class State(TypedDict):
#     # The operator.add reducer fn makes this append-only
#     state: Annotated[list, operator.add]

# # Add nodes
# builder = StateGraph(State)

# # Initialize each node with node_secret 
# builder.add_node("a", ReturnNodeValue("I'm A"))
# builder.add_node("b", ReturnNodeValue("I'm B"))
# builder.add_node("c", ReturnNodeValue("I'm C"))
# builder.add_node("d", ReturnNodeValue("I'm D"))

# # Flow
# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("a", "c")
# builder.add_edge("b", "d")
# builder.add_edge("c", "d")
# builder.add_edge("d", END)
# graph = builder.compile()
# graph.invoke({"state": []})

# #Now, lets consider a case where one parallel path has more steps than the other one.
# builder = StateGraph(State)

# # Initialize each node with node_secret 
# builder.add_node("a", ReturnNodeValue("I'm A"))
# builder.add_node("b", ReturnNodeValue("I'm B"))
# builder.add_node("b2", ReturnNodeValue("I'm B2"))
# builder.add_node("c", ReturnNodeValue("I'm C"))
# builder.add_node("d", ReturnNodeValue("I'm D"))

# # Flow
# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("a", "c")
# builder.add_edge("b", "b2")
# builder.add_edge(["b2", "c"], "d")
# builder.add_edge("d", END)
# graph = builder.compile()
# # In this case, b, b2, and c are all part of the same step.
# # The graph will wait for all of these to be completed before proceeding to step d.
# graph.invoke({"state": []})

# # However, within each step we don't have specific control over the order of the state updates!
# # In simple terms, it is a deterministic order determined by LangGraph based upon graph topology
# ## that we do not control.
# # Above, we see that c is added before b2.
# # However, we can use a custom reducer to customize this e.g., sort state updates.
# def sorting_reducer(left, right):
#     """ Combines and sorts the values in a list"""
#     if not isinstance(left, list):
#         left = [left]

#     if not isinstance(right, list):
#         right = [right]
    
#     return sorted(left + right, reverse=False)

# class State(TypedDict):
#     # sorting_reducer will sort the values in state
#     state: Annotated[list, sorting_reducer]

# # Add nodes
# builder = StateGraph(State)

# # Initialize each node with node_secret 
# builder.add_node("a", ReturnNodeValue("I'm A"))
# builder.add_node("b", ReturnNodeValue("I'm B"))
# builder.add_node("b2", ReturnNodeValue("I'm B2"))
# builder.add_node("c", ReturnNodeValue("I'm C"))
# builder.add_node("d", ReturnNodeValue("I'm D"))

# # Flow
# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("a", "c")
# builder.add_edge("b", "b2")
# builder.add_edge(["b2", "c"], "d")
# builder.add_edge("d", END)
# graph = builder.compile()
# graph.invoke({"state": []})
###########################################################

class State(TypedDict):
    question: str
    answer: str
    context: Annotated[list, operator.add]

from langchain_community.document_loaders import WikipediaLoader
from langchain_tavily import TavilySearch


def search_web(state):
    
    """ Retrieve docs from web search """

    # Search
    tavily_search = TavilySearch(max_results=3)
    search_docs = tavily_search.invoke({"query":state['question']})

     # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document href="{doc["url"]}">\n{doc["content"]}\n</Document>'
            for doc in search_docs["results"]
        ]
    )

    return {"context": [formatted_search_docs]}

def search_wikipedia(state):
    
    """ Retrieve docs from wikipedia """

    # Search
    search_docs = WikipediaLoader(query=state['question'], 
                                  load_max_docs=2).load()

     # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document source="{doc.metadata["source"]}" page="{doc.metadata.get("page", "")}">\n{doc.page_content}\n</Document>'
            for doc in search_docs
        ]
    )

    return {"context": [formatted_search_docs]} 

def generate_answer(state):
    
    """ Node to answer a question """

    # Get state
    context = state["context"]
    question = state["question"]

    # Template
    answer_template = """Answer the question {question} using this context: {context}"""
    answer_instructions = answer_template.format(question=question, 
                                                       context=context)    
    
    # Answer
    answer = llm.invoke([SystemMessage(content=answer_instructions)]+[HumanMessage(content=f"Answer the question.")])
      
    # Append it to state
    return {"answer": answer}

# Add nodes
builder = StateGraph(State)

# Initialize each node with node_secret 
builder.add_node("search_web",search_web)
builder.add_node("search_wikipedia", search_wikipedia)
builder.add_node("generate_answer", generate_answer)

# Flow
builder.add_edge(START, "search_wikipedia")
builder.add_edge(START, "search_web")
builder.add_edge("search_wikipedia", "generate_answer")
builder.add_edge("search_web", "generate_answer")
builder.add_edge("generate_answer", END)
graph = builder.compile()

# result = graph.invoke({"question": "How were IBM's Q2 2025 earnings"})
# result['answer'].content

