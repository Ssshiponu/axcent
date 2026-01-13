# API Reference

## `axcent.core.Agent`

The main class for interacting with the LLM.

### `__init__`
```python
def __init__(self, system_prompt: str = "...", backend: LLMBackend = None, model: str = "gpt-4o-mini")
```
- **system_prompt**: The initial instruction for the agent.
- **backend**: An instance of `LLMBackend` (default: `OpenAIBackend`).
- **model**: The model name string (used if backend is default).

### `ask`
```python
def ask(self, query: str) -> str
```
Sends a user query to the agent. Handles the conversation loop including tool execution.

### `tool`
```python
@agent.tool
def my_function(): ...
```
Decorator to register a function as a tool.

### `get_total_usage`
```python
def get_total_usage(self) -> Dict[str, int]
```
Returns a dictionary containing token usage statistics (prompt, completion, total, cached).

---

## `axcent.llm`

### `OpenAIBackend`
Standard backend for OpenAI-compatible APIs.

### `GeminiBackend`
Backend for Google's Gemini models using `google-genai` SDK.

### `MockBackend`
Backend for testing without API calls.
