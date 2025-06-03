import requests
from typing import List
from src.config import config
from src.utils.logger import logger

class OllamaClient:
    """Client for interacting with the Ollama API."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.session = requests.Session()
        self.timeout = config.TIMEOUT

    def fetch_models(self) -> List[str]:
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