from typing import Generator, Union, List, Optional
import gradio as gr
from src.clients.ollama import OllamaClient
from src.chat.streamer import ChatStreamer
from src.chat.utils import prepare_prompt
from src.utils.logger import logger

def chatbot_response(
    message: str,
    history: Optional[List[Union[gr.ChatMessage, dict, list]]],
    selected_model: str,
    custom_instructions: str = ""
) -> Generator[Union[gr.ChatMessage, List[gr.ChatMessage]], None, None]:
    """Handle chat responses with streaming and thinking indicators."""
    try:
        client = OllamaClient()
        prompt = prepare_prompt(history, message, custom_instructions)
        
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

        custom_instructions = gr.Textbox(
            label="Instructions",
            placeholder="Provide any custom instructions here...",
            lines=3,
            scale=4
        )

        with gr.Row():
            gr.ChatInterface(
                fn=chatbot_response,
                additional_inputs=[model_dropdown, custom_instructions],
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