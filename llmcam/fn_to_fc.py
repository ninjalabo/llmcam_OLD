"""python module to convert a given Fn into FC automatically"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/06_fn_to_fc.ipynb.

# %% auto 0
__all__ = ['YTLiveTools', 'capture_youtube_live_frame_and_save', 'ask_gpt4v_about_image_file', 'extract_parameter_comments',
           'param_converter', 'tool_schema', 'fn_name', 'fn_args', 'fn_exec', 'fn_result_content', 'form_msg',
           'complete']

# %% ../nbs/06_fn_to_fc.ipynb 3
# Importing openai and our custom functions
import openai
import json
import ast
import inspect

from typing import Optional, Union, Callable, Literal,  Tuple
from types import NoneType
from .ytlive import YTLive, NHsta
from .gpt4v import ask_gpt4v

# %% ../nbs/06_fn_to_fc.ipynb 7
def capture_youtube_live_frame_and_save(
        link: Optional[str] = None,  # YouTube Live link
        place: Optional[str] = None,  # Location of live image
    ) -> str:  # Path to the saved image
    """Capture a jpeg file from YouTube Live and save in data directory"""
    if link is not None:
        live = YTLive(url=link, place=place)
    
    else:
        live = NHsta()
    return str(live())

# %% ../nbs/06_fn_to_fc.ipynb 9
def ask_gpt4v_about_image_file(
        path:str  # Path to the image file
    ) -> str:  # JSON string with quantitative information
    """Tell all about quantitative information from a given image file"""
    info = ask_gpt4v(path)
    return json.dumps(info)

# %% ../nbs/06_fn_to_fc.ipynb 13
# Extract parameter comments from the function
def extract_parameter_comments(
        func: Callable  # Function to extract comments from
    ) -> dict[str, str]:  # Dictionary with parameter comments
    """Extract comments for function arguments"""
    # Get the source code of the function
    source = inspect.getsource(func)
    # Parse the source code into an AST
    tree = ast.parse(source)
    
    # Extract comments for function arguments
    comments = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func.__name__:
            # Get arguments and comments in the function
            for arg in node.args.args:
                arg_name = arg.arg
                # Check if there's an inline comment associated with the argument
                if arg.end_lineno and arg.col_offset:
                    # Loop through the source code lines to find the comment
                    lines = source.splitlines()
                    for line in lines:
                        if line.strip().startswith(f"{arg_name}:") and "#" in line:
                            comment = line.split("#")[1].strip()
                            comments[arg_name] = comment
    return comments

# %% ../nbs/06_fn_to_fc.ipynb 19
def param_converter(
        param_type,  # The type of the parameter
        description  # The description of the parameter
    ) -> dict:  # The converted parameter
    """Convert Python parameter types to acceptable types for tool schema"""
    simple_types = {
        str: "string",
        int: "number",
        float: "number",
        bool: "boolean",
    }
    if param_type in simple_types:
        return { "type": simple_types[param_type], "description": description }
    elif param_type == NoneType:
        return { "type": "null", "description": "A default value will be automatically used." }
    
    if hasattr(param_type, '__origin__') and param_type.__origin__ == Union:
        # Recursively convert the types
        descriptions = description.split(" or ")
        subtypes = param_type.__args__
        if len(subtypes) > len(descriptions):
            descriptions = descriptions + ["A description is not provided"] * (len(subtypes) - len(descriptions))

        return {
            "anyOf": [param_converter(subtype, desc) for subtype, desc in zip(subtypes, descriptions)]
        }
    return { "type": "string", "description": description }

# %% ../nbs/06_fn_to_fc.ipynb 24
def tool_schema(
        func: Callable  # The function to generate the schema for
    ) -> dict:  # The generated tool schema
    """Automatically generate a schema from its parameters and docstring"""
    # Extract function name, docstring, and parameters
    func_name = func.__name__
    func_description = func.__doc__ or "No description provided."
    signature = inspect.signature(func)
    
    # Create parameters schema
    parameters_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    # Populate properties and required fields
    param_comments = extract_parameter_comments(func)
    for param_name, param in signature.parameters.items():
        param_type = param.annotation if param.annotation != inspect._empty else str
        
        # Add parameter to schema
        parameters_schema["properties"][param_name] = param_converter(
            param_type, 
            param_comments.get(param_name, "No description provided.")
        )
        
        # Mark as required if no default
        if param.default == inspect.Parameter.empty:
            parameters_schema["required"].append(param_name)
    
    # Build final tool schema
    tool_schema = {
        "type": "function",
        "function": {
            "name": func_name,
            "description": func_description,
            "parameters": parameters_schema,
        }
    }
    
    return tool_schema

# %% ../nbs/06_fn_to_fc.ipynb 26
# Environmental setting up
YTLiveTools = [tool_schema(fn) for fn in (capture_youtube_live_frame_and_save, ask_gpt4v_about_image_file)]

# %% ../nbs/06_fn_to_fc.ipynb 30
# Support functions to handle tool response,where call == response.choices[0].message.tool_calls[i]
def fn_name(call): return call["function"]["name"]
def fn_args(call): return json.loads(call["function"]["arguments"])    
def fn_exec(call, aux_fn, tools = []):
    fn = globals().get(fn_name(call))
    if fn: return fn(**fn_args(call))
    return aux_fn(fn_name(call), **fn_args(call), tools = tools)
    
def fn_result_content(call, aux_fn, tools = []):
    """Create a content containing the result of the function call"""
    content = dict()
    content.update(fn_args(call))
    content.update({fn_name(call): fn_exec(call, aux_fn, tools)})
    return json.dumps(content)

# %% ../nbs/06_fn_to_fc.ipynb 31
def form_msg(
    role: Literal["system", "user", "assistant", "tool"],  # The role of the message sender
    content: str,  # The content of the message
    tool_call_id: Optional[str] = None,  # The ID of the tool call (if role == "tool")
):
    """Create a message for the conversation"""
    msg = {
        "role": role,
        "content": content
    }
    if role == "tool":
        msg["tool_call_id"] = tool_call_id
    return msg

# %% ../nbs/06_fn_to_fc.ipynb 32
def complete(
        messages: list[dict],  # The list of messages
        tools: list[dict] = [],  # The list of tools
        aux_fn: Optional[Callable] = None  # The auxiliary function to handle tool response
    ) -> Tuple[str, str]:  # The role and content of the last message
    """Complete the conversation with the given message"""
    # Generate the response from GPT-4
    response = openai.chat.completions.create(model="gpt-4o", messages=messages, tools=tools)
    res = response.choices[0].message
    messages.append(res.to_dict())

    # Handle the tool response
    for call in res.to_dict().get('tool_calls', []):
        # Append the tool response to the list
        messages.append(
            form_msg(
                role="tool",
                content=fn_result_content(call, aux_fn, tools=tools),
                tool_call_id=call["id"]
            )
        )
    
    if res.to_dict().get('tool_calls'):
        # Recursively call the complete function to handle the tool response
        complete(
            messages, 
            tools=tools, 
            aux_fn=aux_fn
        )

    # Return the last message
    return messages[-1]['role'], messages[-1]['content']
