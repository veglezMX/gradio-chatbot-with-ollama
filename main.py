import json
import os
import logging
import time
import re
from typing import Generator, Optional, Union, List

import gradio as gr
import requests
 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class OllamaClient:
    """Client for interacting with the Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        base_url = os.getenv("OLLOMA_BASE_URL", base_url)
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

    def get_model_info(self, model_name: str) -> dict:
        """Get detailed information about a specific model."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/show",
                json={"name": model_name},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.debug(f"Failed to fetch model info for {model_name}: {str(e)}")
            return {}

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


def extract_model_details(model_name: str) -> dict:
    """Extract available model details from Ollama API."""
    details = {}
    
    try:
        client = OllamaClient()
        model_info = client.get_model_info(model_name)
        if not model_info:
            return details
        
        if "details" in model_info:
            model_details = model_info["details"]
            if "parameter_size" in model_details:
                details["parameter_size"] = model_details["parameter_size"]
            if "quantization_level" in model_details:
                details["quantization"] = model_details["quantization_level"]
        
        context_found = False
        if "model_info" in model_info:
            for key, value in model_info["model_info"].items():
                if "context_length" in key.lower():
                    ctx_size = int(value)
                    if ctx_size >= 1000:
                        details["context_window"] = f"{ctx_size // 1000}K"
                    else:
                        details["context_window"] = str(ctx_size)
                    context_found = True
                    break
        
        if not context_found and "modelfile" in model_info:
            modelfile = model_info["modelfile"]
            
            # Try multiple patterns for context size
            patterns = [
                r'PARAMETER\s+num_ctx\s+(\d+)',
                r'num_ctx\s+(\d+)',
                r'context[_-]?length\s*[:=]\s*(\d+)',
                r'context[_-]?size\s*[:=]\s*(\d+)',
                r'ctx[_-]?len\s*[:=]\s*(\d+)'
            ]
            
            for pattern in patterns:
                ctx_match = re.search(pattern, modelfile, re.IGNORECASE)
                if ctx_match:
                    ctx_size = int(ctx_match.group(1))
                    if ctx_size >= 1000:
                        details["context_window"] = f"{ctx_size // 1000}K"
                    else:
                        details["context_window"] = str(ctx_size)
                    context_found = True
                    break
            
            # Look for temperature setting
            temp_match = re.search(r'PARAMETER\s+temperature\s+([\d.]+)', modelfile)
            if temp_match:
                details["temperature"] = temp_match.group(1)
        
        if not context_found and "template" in model_info:
            template = model_info["template"]
            ctx_match = re.search(r'(\d+)[kK]?\s*(?:tokens?|context)', template, re.IGNORECASE)
            if ctx_match:
                ctx_value = ctx_match.group(1)
                if 'k' in ctx_match.group(0).lower():
                    details["context_window"] = f"{ctx_value}K"
                else:
                    details["context_window"] = ctx_value
                context_found = True
        
        if "details" in model_info and "family" in model_info["details"]:
            details["family"] = model_info["details"]["family"]
        
        if "details" in model_info and "format" in model_info["details"]:
            details["format"] = model_info["details"]["format"]
        
            
    except Exception as e:
        logger.debug(f"Could not extract model details: {e}")
    
    return details


def format_model_info(model_name: str) -> str:
    """Format model information based on available data."""
    if not model_name:
        return "Select a model to see available information"
    
    # Check thinking capability
    has_thinking = has_thinking_capability(model_name)
    
    # Get dynamic model details
    details = extract_model_details(model_name)
    
    # Start building the info text
    info_parts = []
    
    # Model type based on thinking capability
    if "deepseek-r1" in model_name.lower():
        info_parts.append("**DeepSeek-R1** - Advanced reasoning model")
    elif "qwen3" in model_name.lower() or "qwq" in model_name.lower():
        info_parts.append("**Qwen** - Reasoning model")
    elif has_thinking:
        info_parts.append(f"**{model_name}** - Model with thinking capabilities")
    else:
        info_parts.append(f"**{model_name}**")
    
    # Add capabilities
    if has_thinking:
        info_parts.append("✅ Thinking mode supported")
    else:
        info_parts.append("💬 Direct response mode")
    
    # Add available details from API
    detail_lines = []
    
    if "context_window" in details:
        detail_lines.append(f"📏 Context: {details['context_window']} tokens")
    
    if "parameter_size" in details:
        detail_lines.append(f"💾 Parameters: {details['parameter_size']}")
    
    if "quantization" in details:
        detail_lines.append(f"🔢 Quantization: {details['quantization']}")
    
    if "family" in details:
        detail_lines.append(f"👨‍👩‍👧‍👦 Family: {details['family']}")
    
    if "format" in details:
        detail_lines.append(f"📦 Format: {details['format']}")
    
    if "temperature" in details:
        detail_lines.append(f"🌡️ Default temp: {details['temperature']}")
    
    # Combine all parts
    if detail_lines:
        info_parts.append("")  # Empty line for spacing
        info_parts.extend(detail_lines)
    
    return "\n".join(info_parts)

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
                    if message is not None:
                        yield message

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error processing response: {str(e)}")

        final_messages = self._finalize_messages()
        for message in final_messages:
            if message is not None:  
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
                # Handle case where thinking end tag appears without a proper thinking message
                assistant_text = self.accumulated_text.split(self.THINK_END_TAG, 1)[1].strip()
                if assistant_text:
                    messages.append(gr.ChatMessage(content=assistant_text, role="assistant"))
        elif self.accumulated_text.strip():
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
            if assistant_text:
                return [[self.thinking_message, gr.ChatMessage(content=assistant_text, role="assistant")]]
            else:
                # If there's no text after the thinking tag, just return the thinking message
                return [self.thinking_message]
        elif self.thinking_message is not None and self.THINK_START_TAG in self.accumulated_text:
            # Thinking started but never ended - finalize it
            self.thinking_message.metadata["status"] = "done"
            if self.thinking_start_time:
                self.thinking_message.metadata["time"] = time.time() - self.thinking_start_time
            return [self.thinking_message]
        elif self.accumulated_text.strip():
            return [gr.ChatMessage(content=self.accumulated_text.strip(), role="assistant")]
        else:
            return [gr.ChatMessage(content="I apologize, but I didn't generate a response.", role="assistant")]

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

def prepare_prompt_deepseek(
    history: Optional[List[Union[gr.ChatMessage, dict, list]]], 
    user_message: str, 
    custom_instructions: str = "",
    thinking_enabled: bool = True
) -> str:
    """Prepare a prompt from chat history for DeepSeek-R1 with thinking control."""
    history = history or []
    
    if custom_instructions:
        history.insert(0, gr.ChatMessage(content=custom_instructions, role="system"))
    
    chat_history: List[gr.ChatMessage] = []

    for msg in history:
        converted = convert_to_chat_message(msg)
        if isinstance(converted, list):
            chat_history.extend(converted)
        else:
            chat_history.append(converted)

    chat_history.append(gr.ChatMessage(content=user_message, role="user"))

    prompt_parts = []
    
    for msg in chat_history:
        if not msg.metadata:  
            if msg.role == "user":
                prompt_parts.append(f"<｜User｜>{msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"<｜Assistant｜>{msg.content}<｜end▁of▁sentence｜>")
            elif msg.role == "system":
                prompt_parts.append(msg.content)
    
    if thinking_enabled:
        prompt_parts.append("<｜Assistant｜>")
    else:
        prompt_parts.append("<｜Assistant｜><think>\n\n</think>\n\n")
    
    return "\n".join(prompt_parts)

def has_thinking_capability(model_name: str) -> bool:
    if not model_name or not isinstance(model_name, str):
        return False
    
    model_lower = model_name.lower().strip()
    
    thinking_patterns = [
        "qwen3", "qwq",
        "deepseek-r1", "deepseek-reasoner", 
        "reasoning", "think",
        "r1", "o1"
    ]
    
    return any(pattern in model_lower for pattern in thinking_patterns)

def chatbot_response(
    message: str,
    history: Optional[List[Union[gr.ChatMessage, dict, list]]],
    selected_model: str,
    custom_instructions="",
    thinking_enabled: Optional[bool] = None
) -> Generator[Union[gr.ChatMessage, List[gr.ChatMessage]], None, None]:
    """Handle chat responses with streaming and thinking indicators."""
    try:
        client = OllamaClient()
        if thinking_enabled is None:
            thinking_enabled = has_thinking_capability(selected_model)

        if "deepseek" in selected_model.lower():
            prompt = prepare_prompt_deepseek(history, message, custom_instructions, thinking_enabled)
        else:
            prompt = prepare_prompt(history, message, custom_instructions, thinking_enabled)

        streamer = ChatStreamer(client, selected_model, prompt)
        has_yielded = False
        for response in streamer.stream():
            if response is not None:
                if isinstance(response, list):
                    filtered_responses = [msg for msg in response if msg is not None]
                    if filtered_responses:
                        yield filtered_responses
                        has_yielded = True
                else:
                    yield response
                    has_yielded = True
        
        if not has_yielded:
            yield gr.ChatMessage(content="I apologize, but I couldn't generate a response.", role="assistant")

    except requests.exceptions.ConnectionError:
        error_msg = "Error: Cannot connect to Ollama server. Is it running?"
        logger.error(error_msg)
        yield gr.ChatMessage(content=error_msg, role="assistant")
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
                scale=3
            )
            refresh_btn = gr.Button("Refresh Models", scale=1)
        
        with gr.Row():
            thinking_toggle = gr.Checkbox(
                label="Enable Thinking Mode",
                value=True,
                visible=False,
                info="Show model's reasoning process"
            )

        model_info = gr.Markdown("Select a model to see thinking control method")

        custom_instructions = gr.Textbox(
            label="Instructions",
            placeholder="Provide any custom instructions here...",
            lines=3,
            scale=4
        )

        def update_model_interface(model_name):
            """Update UI based on selected model capabilities."""
            has_thinking = has_thinking_capability(model_name)
            info_text = format_model_info(model_name)
            
            # Return updated components: model_info, thinking_toggle visibility
            return info_text, gr.Checkbox(visible=has_thinking, value=has_thinking)

        model_dropdown.change(
            update_model_interface, 
            inputs=model_dropdown, 
            outputs=[model_info, thinking_toggle]
        )

        with gr.Row():
            gr.ChatInterface(
                fn=chatbot_response,
                additional_inputs=[model_dropdown, custom_instructions, thinking_toggle],
                chatbot=gr.Chatbot(
                    type="messages",
                    render_markdown=True,
                    placeholder="Your AI Assistant Ready to Help!",
                    layout="bubble"
                ),
                type="messages",
                title="Smart Multi-Model Chat",
                description="Automatically detects model capabilities and adjusts thinking controls.",
                example_labels=["Simple Question", "Complex Math", "Coding Problem"],
                examples=[
                    ["What is the capital of France?"],
                    ["Solve this step by step: What's the derivative of x^3 + 2x^2 - 5x + 1?"],
                    ["Write a Python function to calculate fibonacci numbers efficiently"]
                ],
                cache_examples=False,
                analytics_enabled=False
            )

        def load_models():
            """Refresh available models in dropdown."""
            models = OllamaClient().fetch_models()
            selected_model = models[0] if models else None
            
            # Update both dropdown and thinking toggle visibility
            has_thinking = has_thinking_capability(selected_model)
            info_text = format_model_info(selected_model)
            
            return (
                gr.Dropdown(choices=models, value=selected_model),
                info_text,
                gr.Checkbox(visible=has_thinking, value=True)
            )

        demo.load(load_models, outputs=[model_dropdown, model_info, thinking_toggle])
        refresh_btn.click(load_models, outputs=[model_dropdown, model_info, thinking_toggle])

    return demo


if __name__ == "__main__":
    interface = create_interface()
    interface.launch(
        inbrowser=True,
        server_port=7860,
        share=False
    )
