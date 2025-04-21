from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class LLMProvider(ABC):
    """Base class for LLM providers. All LLM implementations must inherit from this."""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass
    
    @abstractmethod
    def generate_with_context(self, prompt: str, context: Dict[str, Any], **kwargs) -> str:
        """Generate text with additional context."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """Return a dictionary of provider capabilities."""
        pass

class LLMResponse:
    """Standardized response object for LLM generations."""
    
    def __init__(self, text: str, metadata: Optional[Dict[str, Any]] = None, prompt: Optional[str] = None):
        self.text = text
        self.metadata = metadata or {}
        self.error = None
        self.prompt = prompt
    
    def set_error(self, error: str) -> None:
        """Set an error message if generation failed."""
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        return {
            "text": self.text,
            "metadata": self.metadata,
            "error": self.error,
            "prompt": self.prompt
        }

class LLMConfig:
    """Configuration class for LLM providers."""
    
    def __init__(self, 
                 provider_type: str,
                 model_name: str,
                 api_base: Optional[str] = None,
                 api_key: Optional[str] = None,
                 **kwargs):
        self.provider_type = provider_type
        self.model_name = model_name
        self.api_base = api_base
        self.api_key = api_key
        self.additional_config = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary format."""
        return {
            "provider_type": self.provider_type,
            "model_name": self.model_name,
            "api_base": self.api_base,
            "api_key": self.api_key,
            **self.additional_config
        } 