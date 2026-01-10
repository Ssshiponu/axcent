import json
from typing import Callable, Dict, List, Any, Optional
from .tools import function_to_schema
from .llm import LLMBackend, OpenAIBackend

class Agent:
    def __init__(self, system_prompt: str = "You are a helpful assistant.", backend: LLMBackend = None, model: str = "gpt-4o-mini"):
        self.system_prompt = system_prompt
        self.backend = backend or OpenAIBackend(model=model)
        self.history: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        self.tools: Dict[str, Callable] = {}
        self.tool_schemas: List[Dict[str, Any]] = []
        self.usage_history: List[Dict[str, int]] = []

    def get_total_usage(self) -> Dict[str, int]:
        """Returns the total token usage across all requests."""
        total = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cached_tokens": 0}
        for usage in self.usage_history:
            total["prompt_tokens"] += usage.get("prompt_tokens", 0)
            total["completion_tokens"] += usage.get("completion_tokens", 0)
            total["total_tokens"] += usage.get("total_tokens", 0)
            total["cached_tokens"] += usage.get("cached_tokens", 0)
        return total

    def tool(self, func: Callable):
        """Decorator to register a tool."""
        schema = function_to_schema(func)
        self.tools[func.__name__] = func
        self.tool_schemas.append(schema)
        return func

    def ask(self, query: str) -> str:
        """
        Sends a query to the agent and returns the response.
        Handles tool calls automatically.
        """
        self.history.append({"role": "user", "content": query})
        
        while True:
            # Sort tools by name to ensure consistent order for OpenAI prompt caching
            current_tools = sorted(self.tool_schemas, key=lambda x: x['function']['name']) if self.tool_schemas else None
            response = self.backend.chat(self.history, tools=current_tools)
            message = response.choices[0].message
            
            # Track Usage
            if hasattr(response, 'usage') and response.usage:
                usage_data = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "cached_tokens": 0
                }
                # Check for cached tokens (OpenAI specific structure)
                if hasattr(response.usage, 'prompt_tokens_details') and response.usage.prompt_tokens_details:
                     if hasattr(response.usage.prompt_tokens_details, 'cached_tokens'):
                         usage_data["cached_tokens"] = response.usage.prompt_tokens_details.cached_tokens
                
                self.usage_history.append(usage_data)
            
            # Convert message to dict to ensure compatibility with next API call
            message_dict = {
                "role": message.role,
                "content": message.content,
            }
            if message.tool_calls:
                 message_dict["tool_calls"] = message.tool_calls
            
            self.history.append(message_dict)

            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    if function_name in self.tools:
                        func = self.tools[function_name]
                        try:
                            result = func(**arguments)
                            content = str(result)
                        except Exception as e:
                            content = f"Error executing tool: {e}"
                    else:
                        content = f"Error: Tool {function_name} not found."
                        
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": content
                    })
                # Continue loop to let LLM process tool outputs
            else:
                # No tool calls, return content
                return message.content
