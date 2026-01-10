import os
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMBackend(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        pass

class OpenAIBackend(LLMBackend):
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini", base_url: str = None):
        import openai
        self.client = openai.OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL")
        )
        self.model = model

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        # Filter out tool_map form tool definition if present (not needed for API)
        # But here 'tools' is expected to be the list of schemas.
        
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
            
        return self.client.chat.completions.create(**kwargs)

class MockBackend(LLMBackend):
    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["I am a mock agent."]
        self.calls = []

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        self.calls.append({"messages": messages, "tools": tools})
        
        # Simple mock response object mimicking OpenAI's structure
        class MockChoice:
            def __init__(self, content):
                self.message = type('obj', (object,), {'content': content, 'tool_calls': None})

        class MockResponse:
            def __init__(self, content):
                self.choices = [MockChoice(content)]
        
        return MockResponse(self.responses.pop(0) if self.responses else "No more mock responses.")

class GeminiBackend(LLMBackend):
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        from google import genai
        self.client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        if not self.client.api_key:
             # The new SDK might pick it up from env automatically, but let's be safe
             if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
                  raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found.")
        self.model_name = model

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts OpenAI tool schemas to Gemini V2 tool definitions."""
        if not tools:
            return None
        
        # The new SDK supports providing a list of tool configurations.
        # It can accept raw function callables, or a Tool object.
        # For manual schema control, we define it as a list of 'function_declarations'.
        
        from google.genai import types
        
        function_declarations = []
        for tool in tools:
            fn = tool['function']
            # google-genai uses a simplified schema definition or standard OpenAPI-like dicts.
            # We can use the text-based definition or constructs.
            # Let's use the dict structure which is close to OpenAI's but structured under 'function_declarations'.
            
            function_declarations.append({
                "name": fn['name'],
                "description": fn.get('description'),
                "parameters": fn.get('parameters')
            })
            
        # The API expects: tools=[{'function_declarations': [...]}]
        return [{"function_declarations": function_declarations}]

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        gemini_tools = self._convert_tools(tools)
        
        # Convert History
        # The new SDK uses 'contents' with 'role' (user/model) and 'parts'.
        # 'system' instructions are passed separately to generate_content config.
        
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg['role']
            content = msg.get('content')
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                parts = []
                if content:
                    parts.append({"text": content})
                if "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        parts.append({
                            "function_call": {
                                "name": tc.function.name,
                                "args": json.loads(tc.function.arguments)
                            }
                        })
                contents.append({"role": "model", "parts": parts})
            elif role == "tool":
                # Find valid previous call or just append. 
                # The V2 SDK expects 'role': 'tool' (or 'function' depending on precise version parity).
                # Actually, standard Vertex/Gemini API V1beta uses 'function_response' inside 'function' role.
                # V2 SDK `types.Content` also supports role='tool'.
                
                # We need to match the function name.
                # Since we are iterating strictly, we can try to look up key by tool_call_id if we had a map.
                # Re-scanning messages for map:
                tool_map = {}
                for m in messages:
                    if m['role'] == 'assistant' and 'tool_calls' in m:
                        for tc in m['tool_calls']:
                            tool_map[tc.id] = tc.function.name
                
                fname = tool_map.get(msg.get('tool_call_id'), 'unknown')
                
                contents.append({
                    "role": "user", # In many google apis, function response is user-side.
                    # HOWEVER, verify SDK V2. 
                    # Docs say: function responses are part of the conversation.
                    # Let's try 'user' role with 'function_response' part.
                    "parts": [{
                        "function_response": {
                            "name": fname,
                            "response": {"result": content}
                        }
                    }]
                })

        from google.genai import types
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=gemini_tools,
            temperature=0.7, # Default setup
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )

        # Map response back to OpenAI format
        class OpenAICompatMessage:
            def __init__(self, content, tool_calls=None, role="assistant"):
                self.content = content
                self.tool_calls = tool_calls
                self.role = role

        class OpenAICompatChoice:
            def __init__(self, message):
                self.message = message

        class OpenAICompatResponse:
            def __init__(self, choices, usage=None):
                self.choices = choices
                self.usage = usage

        content_text = None
        tool_calls = []

        # Parse candidates
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.text:
                    content_text = (content_text or "") + part.text
                if part.function_call:
                    tool_calls.append(type('obj', (object,), {
                        'id': 'call_' + part.function_call.name, 
                        'function': type('obj', (object,), {
                            'name': part.function_call.name,
                            'arguments': json.dumps(part.function_call.args)
                        })
                    }))

        # Usage
        usage = None
        if response.usage_metadata:
             usage = type('obj', (object,), {
                'prompt_tokens': response.usage_metadata.prompt_token_count,
                'completion_tokens': response.usage_metadata.candidates_token_count,
                'total_tokens': response.usage_metadata.total_token_count,
                 # Check if cached content is exposed in usage_metadata in V2
                 # It's usually present if implicit caching happened.
                'prompt_tokens_details': type('obj', (object,), {
                    'cached_tokens': getattr(response.usage_metadata, 'cached_content_token_count', 0)
                })
            })

        return OpenAICompatResponse(
            choices=[OpenAICompatChoice(OpenAICompatMessage(content_text, tool_calls if tool_calls else None))],
            usage=usage
        )
