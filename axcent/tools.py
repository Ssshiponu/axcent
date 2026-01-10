import inspect
import typing

def type_to_json_type(t: typing.Any) -> str:
    """Maps Python types to JSON Safe types."""
    if t == str:
        return "string"
    elif t == int:
        return "integer"
    elif t == float:
        return "number"
    elif t == bool:
        return "boolean"
    elif t == list or typing.get_origin(t) == list:
        return "array"
    elif t == dict or typing.get_origin(t) == dict:
        return "object"
    else:
        return "string"  # Default fallback

def function_to_schema(func: typing.Callable) -> dict:
    """
    Converts a Python function into an OpenAI tool schema.
    Uses type hints and docstrings.
    """
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or "No description provided."
    name = func.__name__

    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        
        param_type = type_to_json_type(param.annotation) if param.annotation != inspect.Parameter.empty else "string"
        
        parameters["properties"][param_name] = {
            "type": param_type
        }
        
        if param.default == inspect.Parameter.empty:
            parameters["required"].append(param_name)

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": doc,
            "parameters": parameters,
        }
    }
