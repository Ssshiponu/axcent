import os
import dotenv
from datetime import datetime

from axcent.llm import GeminiBackend
dotenv.load_dotenv()

from axcent import Agent, Transcriber

agent = Agent(
    system_prompt="You are a helpful assistant. respond very shortly in plain text.",
    persist_history=True,
    max_history=20,
)

@agent.tool
def calculator(expression: str) -> str:
    """Calculate the result of a mathematical expression."""
    return eval(expression)

@agent.tool
def get_datetime() -> str:
    """Return the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@agent.tool
def see_media(url: str) -> str:
    """See media to text."""
    transcriber = Transcriber(system_prompt="you are a media transcriber. transcribe the media to very short and plain text.",
    backend=GeminiBackend(),
    model="gemini-2.5-flash")
    return transcriber.transcribe(url)

while True:
    prompt = input("User: ")
    if prompt == "exit":
        break
    elif prompt == "print_using":
        print(agent.get_total_usage())
    else:
        print(f"Agent: {agent.ask(prompt)}")
