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
        # Ensure model name includes tag
        self.model = config.model_name if ":" in config.model_name else f"{config.model_name}:latest"
        
        # Don't validate connection on init, do it when needed
        self._is_connected = False
    
    def _validate_connection(self) -> None:
        """Validate connection to Ollama server."""
        if self._is_connected:
            return
            
        try:
            response = requests.get(f"{self.api_base}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"Failed to connect to Ollama server: {response.text}")
            
            # Check if model is available
            models = response.json().get("models", [])
            if not any(model["name"] == self.model for model in models):
                available_models = [m["name"] for m in models]
                logger.warning(f"Model {self.model} not found. Available models: {available_models}")
                # Try to find a matching model with latest tag
                base_model = self.model.split(":")[0]
                matching_models = [m["name"] for m in models if m["name"].startswith(f"{base_model}:")]
                if matching_models:
                    self.model = matching_models[0]
                    logger.info(f"Using model {self.model} instead")
                else:
                    raise ValueError(f"Model {self.model} not found in available models: {available_models}")
                
            self._is_connected = True
                
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama server: {str(e)}")
    
    def generate_text(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using Ollama API."""
        try:
            # Validate connection and model
            self._validate_connection()
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,  # Disable streaming for simplicity
                **kwargs
            }
            
            response = requests.post(
                f"{self.api_base}/api/generate",
                json=payload,
                timeout=kwargs.get('timeout', 30)  # Use provided timeout or default to 30
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama API error (HTTP {response.status_code}): {response.text}"
                logger.error(error_msg)
                result = LLMResponse("")
                result.set_error(error_msg)
                return result
            
            try:
                data = response.json()
                if "response" not in data:
                    error_msg = f"Invalid response format from Ollama: {data}"
                    logger.error(error_msg)
                    result = LLMResponse("")
                    result.set_error(error_msg)
                    return result
                    
                return LLMResponse(
                    data["response"],
                    {"model": self.model}
                )
                
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse Ollama response: {str(e)}"
                logger.error(error_msg)
                result = LLMResponse("")
                result.set_error(error_msg)
                return result
            
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