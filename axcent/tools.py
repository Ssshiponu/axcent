import inspect
import typing
from typing import get_origin, get_args

def python_type_to_json_schema(t: typing.Any) -> dict:
    """Recursively maps Python types to JSON Schema definitions."""
    origin = get_origin(t)
    args = get_args(t)

    if t == str or origin == str:
        return {"type": "string"}
    elif t == int or origin == int:
        return {"type": "integer"}
    elif t == float or origin == float:
        return {"type": "number"}
    elif t == bool or origin == bool:
        return {"type": "boolean"}
    elif t == type(None) or t is None:
        return {"type": "null"}
    
    # Handle List/Sequence: List[str], list[int], etc.
    elif t == list or origin == list or origin == typing.List:
        item_schema = python_type_to_json_schema(args[0]) if args else {}
        return {
            "type": "array",
            "items": item_schema
        }
    
    # Handle Dict/Mapping: Dict[str, Any]
    elif t == dict or origin == dict or origin == typing.Dict:
        # JSON objects technically have string keys. 
        # We can try to map the value type if provided.
        # Dict[str, int] -> additionalProperties: {"type": "integer"}
        value_schema = python_type_to_json_schema(args[1]) if len(args) > 1 else {}
        return {
            "type": "object",
            "additionalProperties": value_schema
        }

    # Handle Optional (Union[T, NoneType])
    elif origin == typing.Union:
        # Check if it's strictly Optional (T | None)
        non_none_types = [arg for arg in args if arg != type(None)]
        if len(non_none_types) == 1:
            # It's effectively Optional[T]
            # In JSON schema, "optionality" is usually handled by the 'required' list in the parent.
            # However, the field itself can be nullable.
            # OpenAI prefers simple types. Let's return the schema of the inner type.
            # The 'required' logic in function_to_schema handles the optionality.
            return python_type_to_json_schema(non_none_types[0])
            
    # Handle Literal
    elif origin == typing.Literal:
         # Map Literal['a', 'b'] to enum
         return {
             "type": "string", # Assuming literals are strings/ints
             "enum": list(args)
         }

    return {"type": "string"}  # Default fallback

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
        
        # Determine schema for this parameter
        if param.annotation != inspect.Parameter.empty:
            param_schema = python_type_to_json_schema(param.annotation)
        else:
            param_schema = {"type": "string"}
        
        parameters["properties"][param_name] = param_schema
        
        # Determine if required
        # If default is empty, it's required.
        # Note: Optional[T] = None usually implies default=None, so it won't be required.
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
