# Getting Started

## Basic Usage

The core of Axcent is the `Agent` class. 

```python
import os
from axcent import Agent

# 1. Set your API Key
os.environ["OPENAI_API_KEY"] = "sk-..."

# 2. Initialize Agent
agent = Agent(system_prompt="You are a helpful assistant.")

# 3. Ask a question
response = agent.ask("What is the capital of France?")
print(response)
```

## Using Tools

Axcent makes it incredibly easy to give your agent tools. Just define a python function and use the `@agent.tool` decorator.

```python
@agent.tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # In a real app, you'd call an API here
    return f"The weather in {city} is sunny!"

response = agent.ask("What's the weather in Tokyo?")
print(response)
```

The Docstring and Type Hints are automatically converted to the JSON schema required by the LLM.

## Multi-Backend Support

Axcent supports multiple LLM providers.

### Google Gemini

```python
from axcent import Agent, GeminiBackend
import os

os.environ["GEMINI_API_KEY"] = "AIza..."

# Use Gemini Backend (V2)
backend = GeminiBackend(model="gemini-2.0-flash-exp")
agent = Agent(system_prompt="You are a helper.", backend=backend)
```

### OpenRouter

```python
import os
from axcent import Agent

os.environ["OPENAI_API_KEY"] = "sk-or-..."
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

agent = Agent(system_prompt="You are a helper.")
```

## Multimodal: Images & Audio

Axcent supports multimodal inputs through the `Transcriber` class.

### Using Transcriber as a Tool

```python
from axcent import Agent, Transcriber
from axcent.llm import GeminiBackend

agent = Agent(system_prompt="You are a helpful assistant.")

@agent.tool
def see_media(path: str) -> str:
    """Analyze an image or audio file."""
    transcriber = Transcriber(
        system_prompt="Describe this media briefly.",
        backend=GeminiBackend()
    )
    return transcriber.transcribe_file(path)

response = agent.ask("What's in /home/user/photo.jpg?")
```

### Direct Media with ask()

```python
from axcent import Agent, Image

agent = Agent(model="gpt-4o")  # Vision model
img = Image(url="https://example.com/photo.jpg")
# Or from file: img = Image(path="/path/to/image.jpg")

response = agent.ask("What's in this image?", media=[img])
```
