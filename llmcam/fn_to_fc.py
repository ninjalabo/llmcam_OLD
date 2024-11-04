"""python module to convert a given Fn into FC automatically"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/06_fn_to_fc.ipynb.

# %% auto 0
__all__ = ['tools', 'initial_messages', 'capture_youtube_live_frame_and_save', 'ask_gpt4v_about_image_file',
           'extract_parameter_comments', 'param_converter', 'tool_schema', 'fn_name', 'fn_args', 'fn_exec',
           'fn_result_content', 'generate_messages']

# %% ../nbs/06_fn_to_fc.ipynb 3
# Importing openai and our custom functions
import openai
import json
import ast
import inspect

from typing import Optional, Union, Callable, Literal
from types import NoneType
from .ytlive import capture_youtube_live_frame
from .gpt4v import ask_gpt4v

# %% ../nbs/06_fn_to_fc.ipynb 7
def capture_youtube_live_frame_and_save(
        link: Optional[str] = None,  # YouTube Live link
    ) -> str:  # Path to the saved image
    """Capture a jpeg file from YouTube Live and save in data directory"""
    if link is not None:
        return str(capture_youtube_live_frame(link))
    return str(capture_youtube_live_frame())

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
tools = [tool_schema(fn) for fn in (capture_youtube_live_frame_and_save, ask_gpt4v_about_image_file)]
initial_messages = [{"role":"system", "content":"You are a helpful system administrator. Use the supplied tools to assist the user."}]

# %% ../nbs/06_fn_to_fc.ipynb 30
# Support functions to handle tool response,where res == response.choices[0].message
def fn_name(res): return res.tool_calls[0].function.name
def fn_args(res): return json.loads(res.tool_calls[0].function.arguments)    
def fn_exec(res): return globals().get(fn_name(res))(**fn_args(res))
def fn_result_content(res):
    """Create a content containing the result of the function call"""
    content = dict()
    content.update(fn_args(res))
    content.update({fn_name(res): fn_exec(res)})
    return json.dumps(content)

# %% ../nbs/06_fn_to_fc.ipynb 31
def generate_messages(
    message: str,  # New message frorm the user
    history : list[dict] = []  # Previous messages
) -> list[dict]:  # List of messages
    """Generate messages from the user and the system"""
    # Copy the history to avoid modifying the original list
    messages = history.copy()
    if len(messages) == 0:
        # Add initial system message if no history
        messages.append({
            "role":"system", 
            "content":"You are a helpful system administrator. Use the supplied tools to assist the user."
        })

    def complete(
            role: Literal["system", "user", "tool", "assistant"],  # The role of the message sender
            content: str,  # The content of the message
            tool_call_id=None):
        """Send completion request with messages, and save the response in messages again"""
        messages.append({"role":role, "content":content, "tool_call_id":tool_call_id})
        response = openai.chat.completions.create(
            model="gpt-4o", 
            messages=messages, 
            tools=tools
        )
        res = response.choices[0].message
        messages.append(res.to_dict())
        if res.to_dict().get('tool_calls'):
            complete(role="tool", content=fn_result_content(res), tool_call_id=res.tool_calls[0].id)
        return messages[-1]['role'], messages[-1]['content']
    
    complete("user", message)
    return messages
