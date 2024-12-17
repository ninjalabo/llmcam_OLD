"""Python module to execute function calling from GPT messages"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/core/01_fc_exec.ipynb.

# %% auto 0
__all__ = ['form_msg', 'form_msgs', 'print_msg', 'print_msgs', 'fn_name', 'fn_args', 'fn_metadata', 'fn_exec',
           'fn_result_content', 'complete']

# %% ../../nbs/core/01_fc_exec.ipynb 26
import textwrap
from colorama import Fore, Back, Style
from typing import Literal, Optional

# %% ../../nbs/core/01_fc_exec.ipynb 27
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

def form_msgs(
    msgs: list[tuple[Literal["system", "user", "assistant"], str]]  # The list of messages to form in tuples of role and content
): 
    """Form a list of messages for the conversation"""
    return [{"role":m[0],"content":m[1]} for m in msgs]    

# %% ../../nbs/core/01_fc_exec.ipynb 30
def print_msg(
    msg: dict  # The message to print with role and content
):
    """Print a message with role and content"""
    who = msg['role'].capitalize()
    who = (Fore.RED if who in "System" else Fore.GREEN if who in "User" else Fore.BLUE if who in "Assistant" else Fore.CYAN) + who
    who = Back.YELLOW + who
    print(Style.BRIGHT + Fore.RED + f">> {who}:" + Style.RESET_ALL)
    try:
        print(textwrap.fill(msg["content"], 100))
    except:
        print(msg)

def print_msgs(
    msgs: list[dict],  # The list of messages to print with role and content
    with_tool: bool = False  # Whether to print tool messages
):
    for msg in msgs:
        if not with_tool and any(key in msg for key in ('tool_calls', 'tool_call_id')):
            continue
        print_msg(msg)    

# %% ../../nbs/core/01_fc_exec.ipynb 34
import importlib
import json
import openai

# %% ../../nbs/core/01_fc_exec.ipynb 35
# Support functions to handle tool response,where call == response.choices[0].message.tool_calls[i]
def fn_name(call): return call["function"]["name"]
def fn_args(call): return json.loads(call["function"]["arguments"])
def fn_metadata(tool): return tool["function"]["metadata"]

def fn_exec(call, tools=[]):
    """Execute the function call"""
    for tool in tools:
        # Check if the function name matches
        if call['function']['name'] != tool['function']['name']:
            continue

        # Execute the function by dynamically importing the module
        try:
            module_path = tool['function']['metadata']['module']
            module = importlib.import_module(module_path)
            fn = getattr(module, fn_name(call))
            return fn(**fn_args(call))
        
        # If the function is not found, try to fix it
        except Exception as e:
            if not 'fixup' in tool['function']:
                continue
            module_path, fn_path = tool['function']['fixup'].rsplit('.', 1)
            fn = getattr(importlib.import_module(module_path), fn_path)
            return fn(fn_name(call), **fn_metadata(tool), **fn_args(call))

def fn_result_content(call, tools=[]):
    """Create a content containing the result of the function call"""
    content = dict()
    content.update(fn_args(call))
    content.update({fn_name(call): fn_exec(call, tools)})
    return json.dumps(content)

# %% ../../nbs/core/01_fc_exec.ipynb 36
def complete(
        messages: list[dict],  # The list of messages
        tools: list[dict] = [],  # The list of tools
    ) -> tuple[str, str]:  # The role and content of the last message
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
                content=fn_result_content(call, tools=tools),
                tool_call_id=call["id"]
            )
        )

    if res.to_dict().get('tool_calls'):
        # Recursively call the complete function to handle the tool response
        complete(
            messages, 
            tools=tools
        )

    # Return the last message
    return messages[-1]['role'], messages[-1]['content']
