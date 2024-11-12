"""chat UI implemented in fastHTML"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/05_chat_ui.ipynb.

# %% auto 0
__all__ = ['hdrs', 'app', 'scroll_script', 'ChatMessage', 'ChatInput', 'ActionButton', 'ActionPanel', 'index', 'send',
           'llmcam_chatbot']

# %% ../nbs/05_chat_ui.ipynb 4
import uvicorn
import importlib.util
from fasthtml.common import *
from .fn_to_fc import complete, form_msg, YTLiveTools

# %% ../nbs/05_chat_ui.ipynb 5
# Set up the app, including daisyui and tailwind for the chat component
hdrs = (picolink, Script(src="https://cdn.tailwindcss.com"),
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css"),
        MarkdownJS(), HighlightJS(langs=['python', 'javascript', 'html', 'css']))
app = FastHTML(hdrs=hdrs)

# %% ../nbs/05_chat_ui.ipynb 7
# Chat message component (renders a chat bubble)
def ChatMessage(
        msg: str,  # Message to display
        user: bool  # Whether the message is from the user or assistant
    ):  # Returns a Div containing the chat bubble
    # Set class to change displayed style of bubble
    bubble_class = "chat-bubble-primary" if user else 'chat-bubble-secondary'
    chat_class = "chat-end" if user else 'chat-start'
    return  Div(cls=f"chat {chat_class}")(
                Div('User' if user else 'Assistant', cls="chat-header"),
                Div(
                    msg,
                    cls=f"chat-bubble {bubble_class} marked px-6 py-4", 
                    style=f"background-color: {'#038a5e' if user else '#025238'}; color: {'black' if user else 'white'};"),
                Hidden(msg, name="contents"),  # Hidden field for submitting past contents to form
                Hidden("user" if user else "assistant", name="roles")  # Hidden field for submitting corresponding owners
            )

# %% ../nbs/05_chat_ui.ipynb 10
# The input field for the user message. Also used to clear the
# input field after sending a message via an OOB swap
def ChatInput():  # Returns an input field for the user message
    return Input(name='msg', id='msg-input', placeholder="Type a message",
                 cls="input input-bordered w-full rounded-l-2xl bg-stone-800", 
                 hx_swap_oob='true'  # Re-render the element to remove submitted message
                )

# %% ../nbs/05_chat_ui.ipynb 13
def ActionButton(
        content: str  # Text to display on the button
    ):  # Returns a button with the given content

    return Form(
        hx_post="/",
        hx_target="#chatlist",
        hx_swap="beforeend",  # Location: just before the end of element
    )(
        Hidden(content, name="msg"),
        Button(content, cls="btn btn-secondary")
    )

def ActionPanel():  # Returns a panel of action buttons
    return Div(
        ActionButton("Introduce your model GPT-4o"),
        ActionButton("Extract information from a YouTube Live"),
        cls="flex flex-row h-fit px-24 gap-4 pt-4"
    )

# %% ../nbs/05_chat_ui.ipynb 18
scroll_script = Script("""
  // Function to scroll to the bottom of an element
  function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
  }

  // Reference the expanding element
  const expandingElement = document.getElementById('chatlist');

  // Observe changes to the element's content and scroll down automatically
  const observer = new MutationObserver(() => {
    scrollToBottom(expandingElement);
  });

  // Start observing the expanding element for changes
  observer.observe(expandingElement, { childList: true, subtree: true });
""")

# %% ../nbs/05_chat_ui.ipynb 19
@app.get('/')
def index():
    sidebar = Div(
        H1("Conversations"),
        cls="w-[30vw] bg-stone-800"
    )
    page =  Div(cls="w-full flex flex-col p-0")(
        ActionPanel(),
        Form(
            hx_post="/",  # Operation: some POST endpoint with function `send` 
            hx_target="#chatlist",  # Target: element with ID 'chatlist'
            hx_swap="beforeend",  # Location: just before the end of element
            cls="w-full flex flex-col px-24 h-[90vh]"
        )(
            # The chat list
            Div(id="chatlist", cls="chat-box overflow-y-auto flex-1 w-full mt-10")(
                # One initial message from AI assistant
                ChatMessage("Hello! I'm a chatbot. How can I help you today?", False),
            ),
            # Input form
            Div(cls="h-fit mb-5 mt-5 flex space-x-2 mt-2")(
                Group(
                    ChatInput(), 
                    Button("Send", cls="btn btn-primary rounded-r-2xl", style="background-color: #03fcad;"))
            ),
            scroll_script
        )   
    )
    return Main(
        sidebar,
        page, 
        data_theme="forest", 
        cls="h-[100vh] w-full relative flex flex-row items-stretch overflow-hidden transition-colors z-0 p-0",)

# %% ../nbs/05_chat_ui.ipynb 21
# Handle the form submission
@app.post('/')
def send(msg: str, contents: list[str] = None, roles: list[str] = None):
    # If no contents or roles are provided, set them to empty lists
    if not contents: contents = []
    if not roles: roles = []

    # Create chat messages from the provided contents and roles
    messages = [ form_msg(role, content) for role, content in zip(roles, contents) ]
    nof_old_msgs = len(messages) # Number of old messages
    messages.append(form_msg("user", msg))
    
    # Add the user's message to the chat history
    complete(messages, YTLiveTools)
    responses = messages[nof_old_msgs:]  # Get only the new messages
    
    # Create chat messages from the responses
    chat_messages = [
        ChatMessage(res['content'], res['role'] == 'user') for res in responses if 'content' in res \
            if res['role'] in ['user', 'assistant'] and res['content'] is not None
    ]
    
    return (*chat_messages,
            ChatInput()) # And clear the input field via an OOB swap

# %% ../nbs/05_chat_ui.ipynb 23
def llmcam_chatbot(
        package_name="ninjalabo.llmcam",  # The installed package name
        module_name="chat_ui",  # The module containing the FastAPI app
        app_variable="app",  # The FastAPI app variable name
        host="0.0.0.0",  # The host to listen on
        port=5001,  # The port to listen on
        **uvicorn_kwargs  # Additional keyword arguments for uvicorn
    ):
    "Find and run the FastAPI app in the specified module within the given package."
    # Construct the full module path (e.g., 'llmcam.chat_ui')
    full_module_path = f"{package_name.split('.')[-1]}.{module_name}"

    # Check if the module exists in the installed package
    try:
        spec = importlib.util.find_spec(full_module_path)
        if spec is None:
            print(f"Module '{full_module_path}' not found in package '{package_name}'.")
            return
        # Dynamically run the Uvicorn server
        uvicorn.run(f"{full_module_path}:{app_variable}", host=host, port=port, **uvicorn_kwargs)
    except Exception as e:
        print(f"Error running the app: {e}")
