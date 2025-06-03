"""
Main entry point for the Ollama Chat application.
"""
import uvicorn
import gradio as gr
from src.api.app import create_app
from src.ui.interface import create_interface
from src.config import config

app = create_app()

interface = create_interface()
gr.mount_gradio_app(app, interface, path=config.GRADIO_PATH)

def main():
    """Run the application with uvicorn."""
    uvicorn.run(
        "src.main:app",  
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL,
        reload=False  
    )

if __name__ == "__main__":
    main()