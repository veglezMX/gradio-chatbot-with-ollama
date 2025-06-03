import os
from typing import Optional

class Config:
    """Application configuration."""
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    TIMEOUT: int = 30
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "info"
    
    # Gradio settings
    GRADIO_PATH: str = "/gradio"
    
    # Thinking tags
    THINK_START_TAG: str = "<think>"
    THINK_END_TAG: str = "</think>"

config = Config()