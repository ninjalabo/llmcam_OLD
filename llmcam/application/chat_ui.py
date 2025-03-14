"""Python module for implementing chat UI in fastHTML"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/application/02_chat_ui.ipynb.

# %% auto 0
__all__ = ['hdrs', 'app', 'noti_script', 'scroll_script', 'title_script', 'ChatMessage', 'ChatInput', 'ActionButton',
           'ActionPanel', 'ToolPanel', 'NotiMessage', 'NotiButton', 'index', 'noti_disconnect', 'wsnoti',
           'chat_disconnect', 'wschat', 'get_file']

# %% ../../nbs/application/02_chat_ui.ipynb 4
import os
import asyncio
from fasthtml.common import *
from ..core.fc import *
from .session import *

# %% ../../nbs/application/02_chat_ui.ipynb 5
# Set up the app, including daisyui and tailwind for the chat component
hdrs = (picolink,
        Link(rel="icon", href=f"""{os.getenv("LLMCAM_DATA", "../data").split("/")[-1]}/favicon.ico""", type="image/png"),
        Script(src="https://cdn.tailwindcss.com"),
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css"),
        # Link(rel="preconnect", href="https://fonts.googleapis.com"),
        # Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        # Link(href="https://fonts.googleapis.com/css2?family=Patrick+Hand", rel="stylesheet"),
        Script(src="https://unpkg.com/htmx.org"),
        Style("p {color: black; font-family: 'Georgia', Times, serif;}"),
        Style("li {color: black; font-family: 'Georgia', Times, serif;}"),
        Style("main {font-family: 'Georgia', Times, serif;}"),
        MarkdownJS(), HighlightJS(langs=['python', 'javascript', 'html', 'css']))
app = FastHTML(hdrs=hdrs, exts="ws")

# %% ../../nbs/application/02_chat_ui.ipynb 10
# Chat message component (renders a chat bubble)
def ChatMessage(
        msg: str,  # Message to display
        user: bool  # Whether the message is from the user or assistant
    ):  # Returns a Div containing the chat bubble
    # Set class to change displayed style of bubble
    content_class = "chat-bubble chat-bubble-primary" if user else ""
    content_class += " marked py-2"
    return  Div(cls=f"chat chat-end py-4" if user else "py-4")(
                Div('User' if user else 'Assistant', cls="chat-header"),
                Div(
                    msg,
                    cls=content_class,
                )
            )

# %% ../../nbs/application/02_chat_ui.ipynb 13
# The input field for the user message. Also used to clear the
# input field after sending a message via an OOB swap
def ChatInput():  # Returns an input field for the user message
    return Input(name='msg', id='msg-input', placeholder="Type a message",
                 cls="input input-bordered w-full rounded-l-2xl", 
                 hx_swap_oob='true'  # Re-render the element to remove submitted message
                )

# %% ../../nbs/application/02_chat_ui.ipynb 16
def ActionButton(
        session_id: str,  # Session ID to use
        content: str,  # Text to display on the button
        message: str = None  # Message to send when the button is clicked
    ):  # Returns a button with the given content

    return Form(
        ws_send=True,
        hx_ext='ws', ws_connect='/wschat',
    )(
        Hidden(session_id, name="session_id"),
        Hidden(content if message is None else message, name="msg"),
        Button(
            content, 
            cls="btn btn-secondary rounded-2 h-fit",
            style="font-family: 'Georgia', Times, serif;" 
        )
    )

def ActionPanel(
        session_id: str  # Session ID to use
    ):  # Returns a panel of action buttons
    return Div(
        P("Quick actions", cls="text-lg text-black"),
        ActionButton(session_id, "Introduce your model GPT-4o"),
        ActionButton(session_id,
            "Extract information from a YouTube Live", 
            "Capture and extract information from a YouTube Live. Use the default link."),
        A('YouTube Playlist (Examples)', href='https://www.youtube.com/watch?v=BuyqWfyhvgE&list=PLNzPo4P4-KZOJEwDrywdUt8IryV06viqg&index=8', target='_blank'),

        cls="flex flex-col h-fit gap-4 py-4 px-4"
    )

# %% ../../nbs/application/02_chat_ui.ipynb 20
def ToolPanel(
        session_id: str  # Session ID to use
    ):  # Returns a panel of usable tools

    available_services = retrieve_session_tools(session_id)

    # Generate list items for each available tool
    items = []
    if available_services:
        for service in available_services:
            service_desc = service['function']['description']
            items.append(Li(f"{service_desc}", cls="text-sm text-black"))
    else:
        items.append(Li("No services available", cls="text-sm italic text-gray-500"))

    return Div(
        P("Available Tools", cls="text-lg text-black"),
        Ul(*items, cls="list-disc list-inside px-6", style="max-height: 60vh; overflow-y:auto;"),
        id="toollist",
        cls="flex flex-col h-fit gap-4 py-4 px-4"
    )

# %% ../../nbs/application/02_chat_ui.ipynb 23
def NotiMessage(
        message: str = "No message"  # Message to display
    ):  # Returns a notification message hidden from the UI view
    return Hidden(message, id="notification", cls="text-black")

def NotiButton(
        session_id: str  # Session ID to use
    ):  # Returns a hidden button to trigger notification websocket connection
    return Form(
        ws_send=True,
        hx_ext='ws', ws_connect='/wsnoti',
        style="display: none;"
    )(
        Hidden(session_id, name="session_id"),
        Button(
            "Notification", 
            id="connect-btn", 
            cls="btn btn-primary rounded-2 h-fit", 
            style="display: none;"
        )
    )

# %% ../../nbs/application/02_chat_ui.ipynb 24
# Event listener to handle notifications when the element #notification is loaded
noti_script = Script("""
    // Automatically click the hidden button to connect to the notification websocket
    window.addEventListener('load', function() {
        let connectButton = document.querySelector('#connect-btn');
        if (connectButton) {
            connectButton.click();
            console.log("Hidden button clicked on page load!");
        }
    });
                     
    // Listen for the htmx:load event on the document body
    document.body.addEventListener('htmx:load', function(event) {
        if (event.target.id === "notification") {
            let htDivElement = event.detail.elt; // Extract the HtDiv element

            // Find the input element inside the HtDiv and extract its value
            let inputElement = htDivElement.querySelector('input');
            if (inputElement) {
                let inputValue = inputElement.value;
                alert(inputValue);
            } else {
                console.log("Input element not found.");
            }
        }
    });
""")

# %% ../../nbs/application/02_chat_ui.ipynb 27
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

# %% ../../nbs/application/02_chat_ui.ipynb 28
title_script = Script("""
    // Function to set the title of the page
    document.title = "LLMCAM";
""")

# %% ../../nbs/application/02_chat_ui.ipynb 30
@app.get('/')
async def index(session):
    # Initialize the session
    session_id = init_session(session_id=session.get('session_id'))
    
    # Set up the chat UI
    sidebar = Div(
        ActionPanel(session_id=session_id),
        ToolPanel(session_id=session_id),
        NotiButton(session_id=session_id),
        NotiMessage(),
        cls="w-[50vw] flex flex-col p-0",
        style="background-color: WhiteSmoke;"
    )
    page =  Div(cls="w-full flex flex-col p-0")(  # Main page
        Form(
            ws_send=True,
            hx_ext='ws', ws_connect='/wschat',
            cls="w-full flex flex-col px-24 h-[100vh]"
        )(
            Hidden(session_id, name="session_id"),
            # The chat list
            Div(id="chatlist", cls="chat-box overflow-y-auto flex-1 w-full mt-10 p-4")(
                # One initial message from AI assistant
                ChatMessage("Hello! I'm a chatbot. How can I help you today?", False),
            ),
            # Input form
            Div(cls="h-fit mb-5 mt-5 flex space-x-2 mt-2 p-4")(
                Group(
                    ChatInput(), 
                    Button("Send", cls="btn btn-primary rounded-r-2xl"),
                    style="font-family: 'Georgia', Times, serif;"
                )
            ),
            scroll_script
        ),
    )
    return Main(
        noti_script,
        title_script,
        sidebar,
        #a('Click here', href='https://example.com', target='_blank'),
        page, 
        title="Chatbot",
        data_theme="wireframe",
        cls="h-[100vh] w-full relative flex flex-row items-stretch overflow-hidden transition-colors z-0 p-0",)

# %% ../../nbs/application/02_chat_ui.ipynb 32
def noti_disconnect(ws):
    """Remove session ID from session notification sender on websocket disconnect"""
    session_id = ws.scope.get("session_id")
    remove_session(session_id)

# %% ../../nbs/application/02_chat_ui.ipynb 33
@app.ws('/wsnoti')
async def wsnoti(ws, send, session_id: str):
    # Initialize the session
    session_id = init_session(session_id=session_id)

    # Set the session ID in the websocket scope
    ws.scope["session_id"] = session_id

    # Set up the notification sender for the session
    def send_noti(message):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:  # No current event loop in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    
        if loop.is_running():
            # Schedule the task on the running loop
            asyncio.create_task(send(Div(NotiMessage(message), id="notification", hx_swap_oob="true")))
        else:
            # Create and run a new loop
            loop.run_until_complete(send(Div(NotiMessage(message), id="notification", hx_swap_oob="true")))
    
    set_noti_sender(session_id, send_noti)

    # Send a notification to the client
    send_noti("Notification service enabled.")

# %% ../../nbs/application/02_chat_ui.ipynb 37
# On websocket disconnect, remove the session ID from the session messages and tools
def chat_disconnect(ws):
    """Remove session ID from session messages and tools on websocket disconnect"""
    session_id = ws.scope.get("session_id")
    remove_session(session_id)

# %% ../../nbs/application/02_chat_ui.ipynb 38
# The chatbot websocket handler
@app.ws('/wschat', disconn=chat_disconnect)
async def wschat(ws, msg: str, send, session_id: str):
    # Initialize the session
    session_id = init_session(session_id=session_id)

    # Set the session ID in the websocket scope
    ws.scope["session_id"] = session_id
    
    # Create chat messages from the provided contents and roles
    messages = retrieve_session_message(session_id)
    if len(messages) == 0:
        messages.append(
            form_msg(
                "system", 
"You are a helpful assistant. Use the supplied tools to assist the user. \
If asked to show or display an image or plot, do it by embedding its path starting with \
`../data/<filename>` in Markdown syntax. \
When asked to monitor or notify about a process, start a detached notification stream and do not \
wait for it to stop in chat response.\
Use the available tools to stop stream or send notifications from the stream."))
    messages.append(form_msg("user", msg))
    await send(
        Div(ChatMessage(
            messages[-1]["content"],
            messages[-1]["role"] == "user"), 
        hx_swap_oob='beforeend', id="chatlist"))
    
    await send(ChatInput())  # Clear the input field
    
    # Add the user's message to the chat history
    await asyncio.to_thread(complete, messages, retrieve_session_tools(session_id))
    await send(Div(ChatMessage(
            messages[-1]["content"],
            messages[-1]["role"] == "user"), hx_swap_oob='beforeend', id="chatlist"))
    
    await send(Div(ToolPanel(session_id=session_id), hx_swap_oob='true', id='toollist'))
    return

# %% ../../nbs/application/02_chat_ui.ipynb 40
# Serve files from the 'data' directory
@app.get("/data/{file_name:path}")
async def get_file(file_name: str):
    """Serve files dynamically from the 'data' directory."""
    data_path = os.getenv("LLMCAM_DATA", "../data")
    file_path = Path(data_path) / file_name
    if file_path.exists():
        return FileResponse(file_path)
    return {"error": f"File '{file_name}' not found"}
