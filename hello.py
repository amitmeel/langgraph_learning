from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os, getpass

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

# Load environment variables from .env file
load_dotenv()

_set_env("GOOGLE_API_KEY")

# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# # Simple text invocation
# result = llm.invoke("Sing a ballad of LangChain.")
# print(result.content)



