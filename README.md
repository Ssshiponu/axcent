# Axcent

**The easiest way to build AI agents in Python.**

Axcent is a lightweight framework designed to let you build powerful AI agents with tool calling, context caching, and multi-backend support in just a few lines of code.

## Installation

```bash
pip install axcent
```

To use Gemini models:
```bash
pip install axcent[gemini]
```

## Quick Start (OpenAI)

```python
import os
from axcent import Agent

# Set your API Key
os.environ["OPENAI_API_KEY"] = "sk-..."

# Initialize Agent
agent = Agent(system_prompt="You are a helpful assistant.")

# Register a Tool
@agent.tool
def get_weather(city: str) -> str:
    """Returns weather info for a city."""
    return f"The weather in {city} is sunny!"

# Ask away!
response = agent.ask("What is the weather in Tokyo?")
print(response)
```

## Features

- **Simple Tool Registration**: Just use `@agent.tool`.
- **Automatic Context Caching**: Optimizes token usage by enforcing stable prompt structures.
- **Token Monitoring**: Track prompt, completion, and cached tokens via `agent.get_total_usage()`.
- **Backend Agnostic**:
    - **OpenAI**: First-class support.
    - **Google Gemini**: Support for all of the latest models.
    - **OpenRouter**: Use any model via OpenRouter API compatibility.

## Multi-Backend Usage

### Google Gemini

```python
from axcent import Agent, GeminiBackend
import os

# Set API Key (or GOOGLE_API_KEY)
os.environ["GEMINI_API_KEY"] = "AIza..."

# Use Gemini Backend (uses google-genai V2 SDK)
backend = GeminiBackend(model="gemini-3-flash")
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

## License

MIT
