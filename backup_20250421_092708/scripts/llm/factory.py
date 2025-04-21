from typing import Dict, Type, Optional
from .base import LLMProvider, LLMConfig
from .ollama import OllamaProvider

class LLMFactory:
    """Factory class for creating and managing LLM provider instances."""
    
    _providers: Dict[str, Type[LLMProvider]] = {
        'ollama': OllamaProvider
    }
    
    _instances: Dict[str, LLMProvider] = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[LLMProvider]) -> None:
        """Register a new provider class."""
        cls._providers[name] = provider_class
    
    @classmethod
    def create_provider(cls, config: LLMConfig) -> Optional[LLMProvider]:
        """Create a new provider instance based on configuration."""
        provider_type = config.provider_type
        
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
            
        # Check if we already have an instance for this config
        instance_key = f"{provider_type}_{config.model_name}_{config.api_base}"
        
        if instance_key in cls._instances:
            return cls._instances[instance_key]
            
        # Create new instance
        provider_class = cls._providers[provider_type]
        instance = provider_class(config)
        cls._instances[instance_key] = instance
        
        return instance
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, Type[LLMProvider]]:
        """Get dictionary of registered provider types."""
        return cls._providers.copy() 