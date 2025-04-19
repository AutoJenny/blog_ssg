import requests
from typing import Dict, Any, Optional
import json
import logging

from .base import LLMProvider, LLMResponse, LLMConfig

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    """Implementation of LLMProvider for Ollama."""
    
    def __init__(self, config: LLMConfig):
        """Initialize Ollama provider with configuration."""
        self.config = config
        self.api_base = config.api_base or "http://localhost:11434"
        self.model = config.model_name
        
        # Validate connection
        self._validate_connection()
    
    def _validate_connection(self) -> None:
        """Validate connection to Ollama server."""
        try:
            response = requests.get(f"{self.api_base}/api/tags")
            if response.status_code != 200:
                raise ConnectionError(f"Failed to connect to Ollama server: {response.text}")
            
            # Check if model is available
            models = response.json().get("models", [])
            if not any(model["name"] == self.model for model in models):
                logger.warning(f"Model {self.model} not found in available models: {models}")
                
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama server: {str(e)}")
    
    def generate_text(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using Ollama API."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                **kwargs
            }
            
            response = requests.post(
                f"{self.api_base}/api/generate",
                json=payload
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.text}"
                logger.error(error_msg)
                result = LLMResponse("", {"status_code": response.status_code})
                result.set_error(error_msg)
                return result
            
            # Parse streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            full_response += data["response"]
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse response line: {line}")
            
            return LLMResponse(
                full_response,
                {"model": self.model}
            )
            
        except Exception as e:
            error_msg = f"Error generating text: {str(e)}"
            logger.error(error_msg)
            result = LLMResponse("")
            result.set_error(error_msg)
            return result
    
    def generate_with_context(self, prompt: str, context: Dict[str, Any], **kwargs) -> LLMResponse:
        """Generate text with additional context."""
        # Format context into prompt
        context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
        full_prompt = f"Context:\n{context_str}\n\nPrompt: {prompt}"
        
        return self.generate_text(full_prompt, **kwargs)
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Return Ollama capabilities."""
        return {
            "streaming": True,
            "function_calling": False,
            "system_messages": True,
            "context_window": True
        } 