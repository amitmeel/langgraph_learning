import asyncio
import getpass
import os
import operator
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, TypedDict, Annotated, List

from langchain_core.messages import AIMessage, HumanMessage,SystemMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.types import Send, Interrupt, Command
from pydantic import BaseModel, Field
# for tracing purpose
import mlflow

mlflow.langchain.autolog()

# this will create the mlruns in the the same folder as assistant.py. use mlflow ui in this
## folder to see the mlflow ui with tracing

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

# Load environment variables from .env file
load_dotenv()

_set_env("GOOGLE_API_KEY")
_set_env("TAVILY_API_KEY")

# LLM
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def read_prompt_file(filename: str) -> str:
    """
    Reads a .md file from the nearest 'prompt' folder by walking up directories.

    Args:
        filename (str): The name of the markdown file (with or without .md extension).

    Returns:
        str: The content of the markdown file.
    """
    if not filename.endswith(".md"):
        filename += ".md"

    # Start from current file's directory
    current_dir = Path(__file__).resolve().parent

    # Walk upwards until we find a 'prompt' folder
    for parent in [current_dir, *current_dir.parents]:
        prompt_dir = parent / "prompt"
        file_path = prompt_dir / filename
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")

    raise FileNotFoundError(f"No 'prompt' folder found upwards from {current_dir}, file: {filename}")


# Our goal is to build a lightweight, multi-agent system around chat models that customizes the research process.

# Source Selection

# Users can choose any set of input sources for their research.
# Planning

# Users provide a topic, and the system generates a team of AI analysts, each focusing on one sub-topic.
# Human-in-the-loop will be used to refine these sub-topics before research begins.
# LLM Utilization

# Each analyst will conduct in-depth interviews with an expert AI using the selected sources.
# The interview will be a multi-turn conversation to extract detailed insights as shown in the STORM paper(https://arxiv.org/abs/2402.14207).
# These interviews will be captured in a using sub-graphs with their internal state.
# Research Process

# Experts will gather information to answer analyst questions in parallel.
# And all interviews will be conducted simultaneously through map-reduce.
# Output Format

# The gathered insights from each interview will be synthesized into a final report.
# We'll use customizable prompts for the report, allowing for a flexible output format.


####################################
# Generate Analysts: Human-In-The-Loop
###################################
class Analyst(BaseModel):
    affiliation: str = Field(
        description="Primary affiliation of the analyst.",
    )
    name: str = Field(
        description="Name of the analyst."
    )
    role: str = Field(
        description="Role of the analyst in the context of the topic.",
    )
    description: str = Field(
        description="Description of the analyst focus, concerns, and motives.",
    )
    @property
    def persona(self) -> str:
        return f"Name: {self.name}\nRole: {self.role}\nAffiliation: {self.affiliation}\nDescription: {self.description}\n"

class Perspectives(BaseModel):
    analysts: List[Analyst] = Field(
        description="Comprehensive list of analysts with their roles and affiliations.",
    )

# print(Perspectives.model_json_schema())

class GenerateAnalystsState(TypedDict):
    topic: str # Research topic
    max_analysts: int # number of analysts
    human_analyst_feedback: str # Human feedback
    analysts: List[Analyst] # List of analyst who are going to ask questions to expert


# build the graph node to create the analyst
def create_analysts(state: GenerateAnalystsState):
    """ Create analyst based on the topic and human feedback"""
    topic = state["topic"]
    max_analysts = state["max_analysts"]
    human_analyst_feedback = state.get("human_analyst_feedback", "")

    # enforce structured output
    structured_llm = model.with_structured_output(Perspectives)

    # system message
    system_message = read_prompt_file("analyst_instructions").format(topic=topic,
                                                                      human_analyst_feedback=human_analyst_feedback,
                                                                      max_analysts=max_analysts
                                                                    )
    # generate analysts
    analysts = structured_llm.invoke([SystemMessage(content=system_message)]+[HumanMessage(content="Generate the set of analysts.")])

    return {"analysts": analysts.analysts}

def human_feedback(state: GenerateAnalystsState):
    """no-op node that should be interuppted on"""
    pass

def should_continue(state: GenerateAnalystsState):
    """Return the next node to execute"""

    # check if there is any humn feedback present
    human_analyst_feedback = state.get("human_analyst_feedback", None)
    # if present , send back to llm to incorporate humn feedback
    if human_analyst_feedback:
        return "create_analysts"
    
    #otherwise end
    return END

# # Add nodes and edges
# todo: instead of adding dummy humna feedback node, you can also use interrupt and command 

# builder = StateGraph(GenerateAnalystsState)
# builder.add_node("create_analysts", create_analysts)
# builder.add_node("human_feedback", human_feedback)
# builder.add_edge(START, "create_analysts")
# builder.add_edge("create_analysts", "human_feedback")
# builder.add_conditional_edges("human_feedback", should_continue, ["create_analysts", END])

# # Compile
# memory = MemorySaver()
# graph = builder.compile(interrupt_before=['human_feedback'], checkpointer=memory)

# # Input
# max_analysts = 3 
# topic = "The benefits of adopting LangGraph as an agent framework"
# thread = {"configurable": {"thread_id": "1"}}

# # Run the graph until the first interruption
# for event in graph.stream({"topic":topic,"max_analysts":max_analysts,}, thread, stream_mode="values"):
#     # Review
#     analysts = event.get('analysts', '')
#     if analysts:
#         for analyst in analysts:
#             print(f"Name: {analyst.name}")
#             print(f"Affiliation: {analyst.affiliation}")
#             print(f"Role: {analyst.role}")
#             print(f"Description: {analyst.description}")
#             print("-" * 50) 

# # Get state and look at next node
# state = graph.get_state(thread)
# print(f"state after analyst creation: {state.next}")
# # We now update the state as if we are the human_feedback node
# graph.update_state(thread, {"human_analyst_feedback": 
#                             "Add in someone from a startup to add an entrepreneur perspective"}, as_node="human_feedback")


# # Continue the graph execution
# for event in graph.stream(None, thread, stream_mode="values"):
#     # Review
#     analysts = event.get('analysts', '')
#     if analysts:
#         for analyst in analysts:
#             print(f"Name: {analyst.name}")
#             print(f"Affiliation: {analyst.affiliation}")
#             print(f"Role: {analyst.role}")
#             print(f"Description: {analyst.description}")
#             print("-" * 50) 

# # If we are satisfied, then we simply supply no feedback
# further_feedack = None
# graph.update_state(thread, {"human_analyst_feedback": 
#                             further_feedack}, as_node="human_feedback")
# # Continue the graph execution to end
# for event in graph.stream(None, thread, stream_mode="updates"):
#     print("--Node--")
#     node_name = next(iter(event.keys()))
#     print(node_name)

# final_state = graph.get_state(thread)
# analysts = final_state.values.get('analysts')
# print(final_state.next)
# for analyst in analysts:
#     print(f"Name: {analyst.name}")
#     print(f"Affiliation: {analyst.affiliation}")
#     print(f"Role: {analyst.role}")
#     print(f"Description: {analyst.description}")
#     print("-" * 50)


####################################################
# Conduct Interview
# Generate Question
###################################################
class InterviewState(MessagesState):
    max_num_turns: int # max numer of turns for conversation
    context: Annotated[list, operator.add] # source documents
    analyst: Analyst # Analyst who is going to ask question to expert
    interview: str # interview transcript between analyst and expert
    section: list # final key we duplicate in outer state for Send() API

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Search Query for retrieval.")

# build the graph node to generate the question related to topic
def generate_quetion(state: InterviewState):
    """Node to generate a question by analyst"""
    # get state
    analyst = state["analyst"]
    messages = state["messages"]

    # generate question
    system_message = read_prompt_file("question_instructions").format(
        goals=analyst.persona
    )
    question = model.invoke([SystemMessage(content=system_message)] + messages)

    # write question to state
    return {"messages": [question]}



