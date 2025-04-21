from typing import Dict, Any, Optional
from pathlib import Path
import json
import os

from .base import LLMConfig

def load_config(config_path: Optional[str] = None) -> Dict[str, LLMConfig]:
    """Load LLM configurations from a JSON file or environment variables."""
    configs = {}
    
    # Try loading from file first
    if config_path:
        try:
            with open(config_path) as f:
                config_data = json.load(f)
                for name, data in config_data.items():
                    configs[name] = LLMConfig(**data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load config file: {e}")
    
    # Load from environment variables as fallback
    env_prefix = "LLM_"
    provider_type = os.environ.get(f"{env_prefix}PROVIDER_TYPE", "ollama")
    model_name = os.environ.get(f"{env_prefix}MODEL_NAME", "mistral")
    api_base = os.environ.get(f"{env_prefix}API_BASE")
    api_key = os.environ.get(f"{env_prefix}API_KEY")
    
    # Create default config if none loaded from file
    if not configs:
        configs["default"] = LLMConfig(
            provider_type=provider_type,
            model_name=model_name,
            api_base=api_base,
            api_key=api_key
        )
    
    return configs

def save_config(configs: Dict[str, LLMConfig], config_path: str) -> None:
    """Save LLM configurations to a JSON file."""
    config_data = {
        name: config.to_dict()
        for name, config in configs.items()
    }
    
    # Ensure directory exists
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2) 