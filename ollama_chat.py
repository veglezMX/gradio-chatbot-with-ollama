import json
import logging
import time
from typing import Generator, Optional, Union

import gradio as gr
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with the Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 30

    def fetch_models(self) -> list[str]:
        """Retrieve available models from Ollama."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout
            )
            response.raise_for_status()
            return [model["name"] for model in response.json().get("models", [])]
        except Exception as e:
            logger.error(f"Failed to fetch models: {str(e)}")
            return []

    def stream_response(self, model: str, prompt: str) -> requests.Response:
        """Stream response from the Ollama generate API."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": True},
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise


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




def chatbot_response(
    message: str,
    history: Optional[list[Union[gr.ChatMessage, dict, list]]],
    selected_model: str
) -> Generator[gr.ChatMessage, None, None]:
    """Handle chat responses with streaming and thinking indicators."""
    client = OllamaClient()
    history = history or []
    
    try:
        # Prepare chat history
        chat_history = []
        for msg in history:
            converted = convert_to_chat_message(msg)
            if isinstance(converted, list):
                chat_history.extend(converted)
            else:
                chat_history.append(converted)
        
        chat_history.append(gr.ChatMessage(content=message, role="user"))
        
        # Generate prompt from conversation history
        prompt = "\n".join(
            f"{msg.role}: {msg.content}" 
            for msg in chat_history 
            if not msg.metadata
        )
        
        # Stream response from Ollama
        response = client.stream_response(selected_model, prompt)
        accumulated_text = ""
        thinking_message = None
        end_thinking = False

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    chunk = data.get("response", "")
                    accumulated_text += chunk
                    
                    if accumulated_text.startswith("<think>") and "</think>" not in accumulated_text:
                        if thinking_message is None:
                            thinking_start_time = time.time()
                            thinking_message = gr.ChatMessage(
                                content="",
                                metadata={"title": "Thinking...", "id": 0, "status": "pending"},
                            )
                        thinking_content = accumulated_text.split("<think>", 1)[1].strip()
                        thinking_message.content = thinking_content
                        yield thinking_message

                    elif "</think>" in accumulated_text:
                        end_thinking = True
                        thinking_message.metadata["status"] = "done"
                        thinking_message.metadata["time"] = time.time() - thinking_start_time
                        if end_thinking:
                            yield [thinking_message, gr.ChatMessage(content=accumulated_text.split("</think>")[1].strip(), role="assistant")]
                    else:
                        yield gr.ChatMessage(content=accumulated_text.strip(), role="assistant")

                   
                        
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error processing response: {str(e)}")

        if thinking_message is not None:
            yield [thinking_message, gr.ChatMessage(content=accumulated_text.split("</think>")[1].strip(), role="assistant")]
        else:
            yield gr.ChatMessage(content=accumulated_text.strip(), role="assistant")

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        yield gr.ChatMessage(content=error_msg, role="assistant")


def create_interface() -> gr.Blocks:
    """Create Gradio interface with dynamic model loading."""
    with gr.Blocks(title="Ollama Chat") as demo:
        with gr.Row():
            model_dropdown = gr.Dropdown(
                label="Select Model",
                interactive=True,
                scale=4
            )
            refresh_btn = gr.Button("Refresh Models", scale=1)

        gr.ChatInterface(
            fn=chatbot_response,
            additional_inputs=[model_dropdown],
            chatbot=gr.Chatbot(
                height=600,
                render_markdown=True,
                placeholder="Your AI Assistant Ready to Help!",
                layout="panel"
            ),
            type="messages",
            title="Local Ollama Chat",
            description="Chat with locally running Ollama models",
            example_labels=["Introduction", "Poetry"],
            examples=[
                ["Who are you? What is your name?"],
                ["Write a poem about artificial intelligence"]
            ],
            cache_examples=False,
            analytics_enabled=False
        )

        def load_models():
            """Refresh available models in dropdown."""
            models = OllamaClient().fetch_models()
            return gr.Dropdown(
                choices=models,
                value=models[0] if models else None
            )

        demo.load(load_models, outputs=model_dropdown)
        refresh_btn.click(load_models, outputs=model_dropdown)

    return demo


if __name__ == "__main__":
    interface = create_interface()
    interface.launch(server_port=7860, share=False)