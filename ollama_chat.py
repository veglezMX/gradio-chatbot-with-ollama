import json
import logging
import queue
import threading
import time
from typing import Generator, Optional, Union, List

import gradio as gr
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 30

    def fetch_models(self) -> list[str]:
        try:
            resp = self.session.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return []

    def stream_response(self, model: str, prompt: str) -> requests.Response:
        resp = self.session.post(
            f"{self.base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": True},
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp



def convert_to_chat_message(
    msg: Union[gr.ChatMessage, dict, list]
) -> Union[gr.ChatMessage, list[gr.ChatMessage]]:
    """Convert various message formats to gr.ChatMessage."""
    if isinstance(msg, gr.ChatMessage):
        return msg
    if isinstance(msg, dict):
        return gr.ChatMessage(
            content=msg.get("content", ""),
            role=msg.get("role", "user"),
            metadata=msg.get("metadata", {}),
        )
    if isinstance(msg, list):
        return [convert_to_chat_message(m) for m in msg]
    raise ValueError(f"Unsupported message type: {type(msg)}")



class ChatStreamer:
    THINK_START = "<think>"
    THINK_END = "</think>"

    def __init__(self, client: OllamaClient, model: str, prompt: str):
        self.client = client
        self.model = model
        self.prompt = prompt
        self.text = ""
        self.thinking_msg = None
        self.start_time = None

    def stream(self) -> Generator[gr.ChatMessage, None, None]:
        try:
            resp = self.client.stream_response(self.model, self.prompt)
            for line in resp.iter_lines():
                if not line: continue
                data = json.loads(line.decode())
                chunk = data.get("response", "")
                self.text += chunk
                # Simplest: yield assistant chunk by chunk
                yield gr.ChatMessage(content=f"[{self.model}] {self.text}", role="assistant")
        except Exception as e:
            yield gr.ChatMessage(content=f"Error on {self.model}: {e}", role="assistant")

    def _process_accumulated_text(self) -> List[Union[gr.ChatMessage, List[gr.ChatMessage]]]:
        """Process the accumulated text and return messages based on thinking markers."""
        messages: List[Union[gr.ChatMessage, List[gr.ChatMessage]]] = []

        if self.accumulated_text.startswith(self.THINK_START_TAG) and self.THINK_END_TAG not in self.accumulated_text:
            if self.thinking_message is None:
                self.thinking_start_time = time.time()
                self.thinking_message = gr.ChatMessage(
                    content="",
                    metadata={"title": "Thinking...", "id": 0, "status": "pending"},
                )
            thinking_content = self.accumulated_text.split(self.THINK_START_TAG, 1)[1].strip()
            self.thinking_message.content = thinking_content
            messages.append(self.thinking_message)

        elif self.THINK_END_TAG in self.accumulated_text:
            if self.thinking_message is not None:
                self.thinking_message.metadata["status"] = "done"
                if self.thinking_start_time:
                    self.thinking_message.metadata["time"] = time.time() - self.thinking_start_time
            assistant_text = self.accumulated_text.split(self.THINK_END_TAG, 1)[1].strip()
            messages.append([self.thinking_message, gr.ChatMessage(content=assistant_text, role="assistant")])
        else:
            messages.append(gr.ChatMessage(content=self.accumulated_text.strip(), role="assistant"))

        return messages

    def _finalize_messages(self) -> List[Union[gr.ChatMessage, List[gr.ChatMessage]]]:
        """
        At the end of the streaming response, ensure that if a thinking message was used,
        we yield both the final thinking message (with updated metadata) and the assistant's final response.
        """
        if self.thinking_message is not None and self.THINK_END_TAG in self.accumulated_text:
            self.thinking_message.metadata["status"] = "done"
            if self.thinking_start_time:
                self.thinking_message.metadata["time"] = time.time() - self.thinking_start_time
            assistant_text = self.accumulated_text.split(self.THINK_END_TAG, 1)[1].strip()
            return [[self.thinking_message, gr.ChatMessage(content=assistant_text, role="assistant")]]
        else:
            return [gr.ChatMessage(content=self.accumulated_text.strip(), role="assistant")]

def prepare_prompt(history, user_msg, custom="") -> str:
    hist = history or []
    if custom:
        hist.insert(0, {"role": "system", "content": custom})
    parts = []
    for m in hist:
        r = m.role if isinstance(m, gr.ChatMessage) else m.get("role", "user")
        c = m.content if isinstance(m, gr.ChatMessage) else m.get("content", "")
        parts.append(f"{r}: {c}")
    parts.append(f"user: {user_msg}")
    return "\n".join(parts)


def chatbot_response(
    message: str,
    history: Optional[List[Union[gr.ChatMessage, dict, list]]],
    selected_models: List[str],
    custom_instructions=""
) -> List[Union[gr.ChatMessage, List[gr.ChatMessage]]]:
    """
    Handle chat responses without returning a raw generator.
    Collect all streamed messages into a list to satisfy ChatInterface.
    """
    client = OllamaClient()
    prompt = prepare_prompt(history, message, custom_instructions)
    if not selected_models:
        return [gr.ChatMessage(content="Error: No model selected", role="assistant")]
    streamer = ChatStreamer(client, selected_models[0], prompt)
    # Fully consume generator into list
    messages = []
    for msg in streamer.stream():
        messages.append(msg)
    return messages

def chatbot_parallel(
    message: str,
    history: Optional[List[Union[gr.ChatMessage, dict]]],
    selected_models: List[str],
    custom_instructions=""
) -> Generator[gr.ChatMessage, None, None]:
    if not selected_models:
        yield gr.ChatMessage(content="Error: No model selected", role="assistant")
        return

    client = OllamaClient()
    prompt = prepare_prompt(history, message, custom_instructions)
    q: "queue.Queue[gr.ChatMessage]" = queue.Queue()

    def run_model(model: str):
        streamer = ChatStreamer(client, model, prompt)
        for msg in streamer.stream():
            q.put(msg)
    threads: List[threading.Thread] = []
    for m in selected_models:
        t = threading.Thread(target=run_model, args=(m,))
        t.start()
        threads.append(t)

    # While any thread is alive or queue has items, yield messages
    while any(t.is_alive() for t in threads) or not q.empty():
        try:
            msg = q.get(timeout=0.1)
            yield msg
        except queue.Empty:
            continue

    for t in threads:
        t.join()

def create_interface() -> gr.Blocks:
    """Create Gradio interface with dynamic model loading."""
    with gr.Blocks(title="Ollama Chat") as demo:
        # State variables
        available_models_state = gr.State([])
        selected_models_state = gr.State([])
        num_dropdowns_state = gr.State(0)

        with gr.Row():
            refresh_btn = gr.Button("Refresh Models", scale=1)

        # Container for model dropdowns
        with gr.Column() as model_container:
            # Create empty markdown as placeholder - we'll update this with render_models_ui
            model_ui = gr.Markdown("")

        with gr.Row():
            add_model_btn = gr.Button("Add Another Model", scale=1)

        with gr.Row():
            custom_instructions = gr.Textbox(
                label="Instructions",
                placeholder="Provide any custom instructions here...",
                lines=3,
                scale=4
            )

        with gr.Row():
            chatbot = gr.ChatInterface(
            fn=chatbot_response,
            additional_inputs=[selected_models_state, custom_instructions],
            chatbot=gr.Chatbot(
                render_markdown=True,
                placeholder="Your AI Assistant Ready to Help!",
                layout="panel",
                type="messages"
            ),
            type="messages",
            title="Local Ollama Chat",
            description="Chat with locally running Ollama models"
        )

        def load_models():
            """Refresh available models and reset the dropdowns."""
            client = OllamaClient()
            models = client.fetch_models()
            return models, [], 0  # Reset selected models and dropdown count
        
        def render_models_ui(available_models, selected_models, num_dropdowns):
            """Generate HTML for model dropdowns instead of dynamic components."""
            if not available_models:
                return "<div>No models available. Please refresh.</div>", selected_models
            
            # Initialize selected_models if needed
            new_selected = selected_models.copy()
            
            # Generate HTML for dropdowns
            html = "<div class='model-selection'>"
            
            # Create appropriate number of dropdown entries
            for i in range(min(num_dropdowns, len(available_models))):
                # Get current value and choices
                if i < len(new_selected):
                    current = new_selected[i]
                else:
                    # Find models not yet selected
                    available = [m for m in available_models if m not in new_selected]
                    if not available:
                        break
                    current = available[0]
                    new_selected.append(current)
                
                # Create dropdown HTML with data attributes to identify it
                html += f"""
                <div class='model-dropdown' id='model-{i}'>
                    <label>Model {i + 1}</label>
                    <select 
                        id='model-select-{i}' 
                        onchange='handleModelChange(this, {i})'
                        class='model-select'
                    >
                """
                
                # Add selected model first
                html += f"<option value='{current}' selected>{current}</option>"
                
                # Add other available models
                for model in available_models:
                    if model != current and model not in new_selected:
                        html += f"<option value='{model}'>{model}</option>"
                
                html += "</select></div>"
            
            # Add message if all models selected
            if num_dropdowns >= len(available_models):
                html += "<div><em>All available models have been added</em></div>"
                
            html += "</div>"
            
            # Add JavaScript to handle selection changes
            html += """
            <script>
            function handleModelChange(select, index) {
                // Create a custom event to notify Python code about the change
                const event = new CustomEvent('model-selected', {
                    detail: {
                        index: index,
                        value: select.value
                    }
                });
                document.dispatchEvent(event);
                
                // Use Gradio's API to update the state
                const options = {
                    fn_index: 'update_model_fn'
                };
                // We'll handle this server-side
            }
            </script>
            """
            
            return html, new_selected
        
        def update_model_selection(index, value, selected_models):
            """Update the selected model at the given index."""
            if index < len(selected_models):
                selected_models[index] = value
            return selected_models
        
        def increment_dropdowns(num, available_models, selected_models):
            """Increment the number of dropdowns if there are remaining models."""
            remaining = [m for m in available_models if m not in selected_models]
            if remaining and num < len(available_models):
                return num + 1
            return num

        # Define the dropdown components separately
        dropdown_components = []
        max_models = 10  # Set a reasonable maximum
        
        # Create hidden model selection dropdowns that we'll control via JavaScript
        with gr.Column(visible=False) as dropdown_container:
            for i in range(max_models):
                dropdown = gr.Dropdown(
                    choices=[],
                    label=f"Model {i+1}",
                    interactive=True, 
                    visible=False,
                    elem_id=f"model-dropdown-{i}"
                )
                dropdown_components.append(dropdown)
                # Register the event handler during the Blocks context
                dropdown.change(
                    fn=update_model_selection,
                    inputs=[gr.Number(value=i, visible=False), dropdown, selected_models_state],
                    outputs=[selected_models_state]
                )

        # Register the function that handles model selection updates
        demo.load(
            fn=None,
            inputs=None,
            outputs=None,
            js="""
            function() {
                document.addEventListener('model-selected', function(e) {
                    // Find the corresponding dropdown component
                    const dropdown = document.getElementById('model-dropdown-' + e.detail.index);
                    if (dropdown) {
                        // Trigger Gradio's change event on the dropdown
                        const event = new Event('change');
                        dropdown.value = e.detail.value;
                        dropdown.dispatchEvent(event);
                    }
                });
                return [];
            }
            """
        )
        
        # Load models on startup and refresh
        refresh_result = refresh_btn.click(
            load_models, 
            outputs=[available_models_state, selected_models_state, num_dropdowns_state]
        )
        
        # After loading models or changing dropdown count, re-render the UI
        def setup_initial_dropdown(models, selected, count):
            # Always start with at least one dropdown if models are available
            if models and count == 0:
                count = 1
            return count
        
        refresh_result.then(
            setup_initial_dropdown,
            inputs=[available_models_state, selected_models_state, num_dropdowns_state],
            outputs=[num_dropdowns_state]
        ).then(
            render_models_ui,
            inputs=[available_models_state, selected_models_state, num_dropdowns_state],
            outputs=[model_ui, selected_models_state]
        )
        
        # Add dropdown when button is clicked
        add_model_btn.click(
            increment_dropdowns,
            inputs=[num_dropdowns_state, available_models_state, selected_models_state],
            outputs=[num_dropdowns_state]
        ).then(
            render_models_ui,
            inputs=[available_models_state, selected_models_state, num_dropdowns_state],
            outputs=[model_ui, selected_models_state]
        )

    demo.queue()
    return demo


if __name__ == "__main__":
    interface = create_interface()
    interface.launch(inbrowser=False, server_port=7860, share=False)