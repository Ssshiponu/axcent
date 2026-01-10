import os
import dotenv
from datetime import datetime
dotenv.load_dotenv()

from axcent import Agent

agent = Agent(system_prompt="You are a helpful assistant. respond very shortly in plain text.")

@agent.tool
def calculator(expression: str) -> str:
    """Calculate the result of a mathematical expression."""
    return eval(expression)

@agent.tool
def get_datetime() -> str:
    """Return the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

while True:
    prompt = input("User: ")    
    print(f"Agent: {agent.ask(prompt)}")
