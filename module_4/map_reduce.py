import getpass
import os
import operator
from dotenv import load_dotenv
from typing import TypedDict, Annotated

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

# Load environment variables from .env file
load_dotenv()

_set_env("GOOGLE_API_KEY")
_set_env("TAVILY_API_KEY")

# LLM
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# Map-reduce operations are essential for efficient task decomposition and parallel processing.

# It has two phases:
# (1) Map - Break a task into smaller sub-tasks, processing each sub-task in parallel.
# (2) Reduce - Aggregate the results across all of the completed, parallelized sub-tasks.

# Let's design a system that will do two things:
# (1) Map - Create a set of jokes about a topic.
# (2) Reduce - Pick the best joke from the list.
# We'll use an LLM to do the job generation and selection.
# Prompts we will use
subjects_prompt = """Generate a list of 3 sub-topics that are all related to this overall topic: {topic}."""
joke_prompt = """Generate a joke about {subject}"""
best_joke_prompt = """Below are a bunch of jokes about {topic}. Select the best one! Return the ID of the best one, starting 0 as the ID for the first joke. Jokes: \n\n  {jokes}"""

 
class Subjects(BaseModel):
    subjects: list[str]

class BestJoke(BaseModel):
    id: int

class overallState(TypedDict):
    topic: str
    subjects: list
    jokes: Annotated[list, operator.add]
    best_selected_joke: str


# node to generate the subjects for topic
def generate_topics(state: overallState):
    prompt = subjects_prompt.format(topic=state["topic"])
    response = model.with_structured_output(Subjects).invoke(prompt)
    return {"subjects": response.subjects}

# Here is the magic: we use the Send to create a joke for each subject.
# This is very useful! It can automatically parallelize joke generation for any number of subjects.
# generate_joke: the name of the node in the graph
# {"subject": s}: the state to send
# Send allow you to pass any state that you want to generate_joke! It does not have to align with OverallState.
# In this case, generate_joke is using its own internal state, and we can populate this via Send.
def continue_to_jokes(state: overallState):
    return [Send("generate_joke", {"subject":s}) for s in state["subjects"] ]

################
# Joke generation (map)
# Now, we just define a node that will create our jokes, generate_joke!
# We write them back out to jokes in OverallState!
# This key has a reducer that will combine lists.

class jokeState(TypedDict):
    subject: str

class Joke(BaseModel):
    joke: str

def generate_joke(state:jokeState):
    prompt = joke_prompt.format(subject=state["subject"])
    response = model.with_structured_output(Joke).invoke(prompt)
    return {"jokes": [response.joke]}

###############
# Best joke selection (reduce)
# Now, we add logic to pick the best joke.
def best_joke(state: overallState):
    jokes = "\n\n".join(state["jokes"])
    prompt = best_joke_prompt.format(topic=state["topic"], jokes=jokes)
    response = model.with_structured_output(BestJoke).invoke(prompt)
    return {"best_selected_joke": state["jokes"][response.id]}

# graph building and compiling
graph = StateGraph(overallState)
graph.add_node("generate_topics", generate_topics)
graph.add_node("generate_joke", generate_joke)
graph.add_node("best_joke", best_joke)

graph.add_edge(START, "generate_topics")
graph.add_conditional_edges("generate_topics", continue_to_jokes, ["generate_joke"])
graph.add_edge("generate_joke", "best_joke")
graph.add_edge("best_joke", END)

app=graph.compile()

# Call the graph: here we call it to generate a list of jokes
# if you are using this in langgraph studio , comment the below code lines.
# for s in app.stream({"topic": "animals"}):
#     print(s)