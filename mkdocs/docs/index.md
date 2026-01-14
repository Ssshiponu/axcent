# Axcent - AI Agent Framework

**The easiest way to build AI agents in Python.**

Axcent is a lightweight framework designed to let you build powerful AI agents with tool calling, multimodal support (images & audio), context caching, and multi-backend support in just a few lines of code.


## Installation

```bash
pip install axcent
```

## Quick Start

```python
from axcent import Agent

agent = Agent(system_prompt="You are a helpful assistant.")
response = agent.ask("Hello!")
print(response)
```
