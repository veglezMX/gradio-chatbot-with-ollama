import json
import time
from typing import Generator, Optional, Union, List
import gradio as gr
from src.clients.ollama import OllamaClient
from src.config import config
from src.utils.logger import logger

class ChatStreamer:
    """Encapsulates the logic for streaming and processing responses from Ollama."""
    
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

        if (self.accumulated_text.startswith(config.THINK_START_TAG) and 
            config.THINK_END_TAG not in self.accumulated_text):
            if self.thinking_message is None:
                self.thinking_start_time = time.time()
                self.thinking_message = gr.ChatMessage(
                    content="",
                    metadata={"title": "Thinking...", "id": 0, "status": "pending"},
                )
            thinking_content = self.accumulated_text.split(config.THINK_START_TAG, 1)[1].strip()
            self.thinking_message.content = thinking_content
            messages.append(self.thinking_message)

        elif config.THINK_END_TAG in self.accumulated_text:
            if self.thinking_message is not None:
                self.thinking_message.metadata["status"] = "done"
                if self.thinking_start_time:
                    self.thinking_message.metadata["time"] = time.time() - self.thinking_start_time
            assistant_text = self.accumulated_text.split(config.THINK_END_TAG, 1)[1].strip()
            messages.append([self.thinking_message, gr.ChatMessage(content=assistant_text, role="assistant")])
        else:
            messages.append(gr.ChatMessage(content=self.accumulated_text.strip(), role="assistant"))

        return messages

    def _finalize_messages(self) -> List[Union[gr.ChatMessage, List[gr.ChatMessage]]]:
        """Finalize messages at the end of streaming."""
        if self.thinking_message is not None and config.THINK_END_TAG in self.accumulated_text:
            self.thinking_message.metadata["status"] = "done"
            if self.thinking_start_time:
                self.thinking_message.metadata["time"] = time.time() - self.thinking_start_time
            assistant_text = self.accumulated_text.split(config.THINK_END_TAG, 1)[1].strip()
            return [[self.thinking_message, gr.ChatMessage(content=assistant_text, role="assistant")]]
        else:
            return [gr.ChatMessage(content=self.accumulated_text.strip(), role="assistant")]