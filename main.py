import json
import os
import logging
import time
from typing import Generator, Optional, Union, List

import gradio as gr
import requests
 
from fastapi import FastAPI, Response, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class OllamaClient:
    """Client for interacting with the Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        # Allow overriding the base URL via environment variable
        base_url = os.getenv("OLLAMA_BASE_URL", base_url)
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


class ChatStreamer:
    """
    Encapsulates the logic for streaming and processing responses from Ollama.
    """
    THINK_START_TAG = "<think>"
    THINK_END_TAG = "</think>"

    def __init__(self, client: OllamaClient, selected_model: str, prompt: str):
        self.client = client
        self.selected_model = selected_model
        self.prompt = prompt
        self.accumulated_text = ""
        self.thinking_message: Optional[gr.ChatMessage] = None
        self.thinking_start_time: Optional[float] = None

    def stream(self) -> Generator[Union[gr.ChatMessage, List[gr.ChatMessage]], None, None]:
        """Streams and yields chat messages as they are processed."""
        response = self.client.stream_response(self.selected_model, self.prompt)

        for line in response.iter_lines():
            if not line:
                continue

            try:
                data = json.loads(line.decode("utf-8"))
                chunk = data.get("response", "")
                self.accumulated_text += chunk

                messages = self._process_accumulated_text()
                for message in messages:
                    yield message

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error processing response: {str(e)}")

        for message in self._finalize_messages():
            yield message

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

def prepare_prompt(
        history: Optional[List[Union[gr.ChatMessage, dict, list]]], 
        user_message: str, 
        custom_instructions="",
        thinking_enabled: bool = True
        ) -> str:
    """Prepare a prompt from chat history and the new user message."""
    history = history or []
    thinking_instruction = "/think" if thinking_enabled else "/no_think"

    if custom_instructions:
        custom_instructions = f"{custom_instructions}\n{thinking_instruction}"
    else:
        custom_instructions = thinking_instruction
    
    if custom_instructions:
        history.insert(0, gr.ChatMessage(content=custom_instructions, role="system"))
    
    chat_history: List[gr.ChatMessage] = []

    for msg in history:
        converted = convert_to_chat_message(msg)
        if isinstance(converted, list):
            chat_history.extend(converted)
        else:
            chat_history.append(converted)

    user_message_with_thinking = f"{user_message} {thinking_instruction}"
    chat_history.append(gr.ChatMessage(content=user_message_with_thinking, role="user"))

    prompt = "\n".join(
        f"{msg.role}: {msg.content}"
        for msg in chat_history
        if not msg.metadata  
    )
    return prompt


def chatbot_response(
    message: str,
    history: Optional[List[Union[gr.ChatMessage, dict, list]]],
    selected_model: str,
    custom_instructions="",
    thinking_enabled: bool = True
) -> Generator[Union[gr.ChatMessage, List[gr.ChatMessage]], None, None]:
    """Handle chat responses with streaming and thinking indicators."""
    try:
        client = OllamaClient()
        prompt = prepare_prompt(history, message, custom_instructions,thinking_enabled)

        streamer = ChatStreamer(client, selected_model, prompt)
        yield from streamer.stream()

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
            thinking_toggle = gr.Checkbox(
                label="Enable Thinking Mode",
                value=True,
                scale=1,
                info="Show model's reasoning process"
            )

        custom_instructions = gr.Textbox(
            label="Instructions",
            placeholder="Provide any custom instructions here...",
            lines=3,
            scale=4
        )

        with gr.Row():
            gr.ChatInterface(
                fn=chatbot_response,
                additional_inputs=[model_dropdown, custom_instructions,thinking_toggle],
                chatbot=gr.Chatbot(
                    render_markdown=True,
                    placeholder="Your AI Assistant Ready to Help!",
                    layout="bubble"
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
    interface.launch(
        inbrowser=True,
        server_port=7860,
        share=False
    )
