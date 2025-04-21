# LLM Configuration Guide

## Overview
This document outlines the configuration system for LLM interactions in our static site generator. The system is designed to be flexible, supporting multiple LLM providers while maintaining a consistent interface.

## Configuration Structure

### Core Components
1. **Base Classes** (`scripts/llm/base.py`)
   - `LLMProvider`: Abstract base class for all LLM providers
   - `LLMResponse`: Standardized response object
   - `LLMConfig`: Configuration class for provider settings

2. **Factory Pattern** (`scripts/llm/factory.py`)
   - `LLMFactory`: Manages provider registration and instantiation
   - Supports dynamic provider registration
   - Implements singleton pattern for provider instances

3. **Configuration Management** (`scripts/llm/config.py`)
   - Loads configurations from JSON files and environment variables
   - Supports multiple named configurations
   - Provides fallback to environment variables

### Provider Support
Currently supported providers:
- **Ollama** (`scripts/llm/ollama.py`)
  - Local model hosting
  - Automatic model validation
  - Fallback to latest tag if specific version not found
  - Supports streaming and context windows

### Configuration Parameters
All LLM interactions support configurable parameters:
```python
LLMConfig(
    provider_type="ollama",  # Required: Type of provider
    model_name="llama3.1:70b",  # Required: Model identifier
    api_base="http://localhost:11434",  # Optional: API endpoint
    api_key=None,  # Optional: API key if required
    **kwargs  # Additional provider-specific parameters
)
```

### Environment Variables
Sensitive configuration can be managed through environment variables:
```env
LLM_PROVIDER_TYPE=ollama
LLM_MODEL_NAME=llama3.1:70b
LLM_API_BASE=http://localhost:11434
LLM_API_KEY=your_api_key_here
```

## Usage Examples

### Loading Configuration
```python
from scripts.llm.config import load_config

# Load from file or environment variables
configs = load_config("path/to/config.json")
default_config = configs["default"]
```

### Creating Provider Instance
```python
from scripts.llm.factory import LLMFactory

provider = LLMFactory.create_provider(default_config)
response = provider.generate_text("Your prompt here")
```

### Provider Capabilities
```python
capabilities = provider.get_capabilities()
# Returns: {
#     "streaming": True,
#     "function_calling": False,
#     "system_messages": True,
#     "context_window": True
# }
```

## Best Practices
1. **Configuration Management**
   - Store configurations in JSON files
   - Use environment variables for sensitive data
   - Implement proper error handling for missing configurations

2. **Provider Implementation**
   - Inherit from `LLMProvider` base class
   - Implement all required abstract methods
   - Handle errors gracefully with `LLMResponse`

3. **Model Selection**
   - Specify exact model versions in configuration
   - Implement fallback mechanisms for unavailable models
   - Validate model availability before use

4. **Error Handling**
   - Use standardized `LLMResponse` for all outputs
   - Include detailed error messages
   - Log errors appropriately

## Configuration Schema
The system uses a flexible schema defined in `config/llm_schema.yaml`:
```yaml
providers:
  ollama:
    name: "Ollama"
    models:
      - name: "llama3"
        capabilities:
          - text_generation
          - summarization
    required_parameters:
      - api_base
```

## UI Integration
The Flask application (`app.py`) provides:
- Model selection and configuration interface
- Real-time provider status checking
- Configuration validation and error reporting
- Provider capability display 

## Task Configuration

### Task Definition
Tasks are defined in `_data/llm_tasks.yaml` and specify:
- Task name and description
- Associated prompt reference
- Model-specific settings (temperature, max_tokens, etc.)
- UI elements (icons, etc.)

Example task configuration:
```yaml
generate_concept:
  name: "Generate Blog Concept"
  description: "Generate a concept paragraph for a Scottish heritage blog post"
  icon: "bi-lightbulb"
  prompt_ref: "concept_generation"
  model_settings:
    temperature: 0.7
    max_tokens: 200
    top_p: 0.9
```

### Model Usage in Tasks
Tasks use the following model configuration hierarchy:
1. **Task-specific settings**: Parameters defined in the task's `model_settings`
   - Can override the model name (e.g., use a different model for specific tasks)
   - Can override generation parameters (temperature, max_tokens, etc.)
2. **Default configuration**: Uses the "default" configuration from `load_config()`
3. **Fallback values**: If no configuration is found, uses hardcoded defaults

Example task configuration with model override:
```yaml
generate_concept:
  name: "Generate Blog Concept"
  description: "Generate a concept paragraph for a Scottish heritage blog post"
  icon: "bi-lightbulb"
  prompt_ref: "concept_generation"
  model_settings:
    model_name: "llama3.1:70b"  # Override default model
    temperature: 0.7
    max_tokens: 200
    top_p: 0.9
```

The system works as follows:
1. Each task loads its specific settings from `llm_tasks.yaml`
2. If a task specifies a model name other than "default", it uses that model
3. Otherwise, it uses the default configuration from `load_config()`
4. Task-specific parameters (temperature, max_tokens, etc.) override the model configuration
5. The provider is created using the combined configuration

Example execution flow with model override:
```python
# Load task configuration
task_config = llm_tasks['tasks'].get('generate_concept')

# Load default LLM configuration
configs = load_config()
default_config = configs.get("default", LLMConfig(...))

# Get task-specific model configuration
task_model_config = get_task_model_config(task_config, default_config)

# Create provider with task-specific config
provider = LLMFactory.create_provider(task_model_config)

# Execute task with task-specific parameters
response = provider.generate_text(
    prompt,
    temperature=task_config['model_settings']['temperature'],
    max_tokens=task_config['model_settings']['max_tokens'],
    top_p=task_config['model_settings']['top_p']
)
```

### Task Management
Tasks are managed through:
1. **Configuration Files**: `_data/llm_tasks.yaml` defines available tasks
2. **API Endpoints**: `/api/llm/actions` provides task metadata
3. **UI Integration**: Tasks are displayed in the Actions tab of the LLM interface

Each task can specify:
- Required model capabilities
- Task-specific parameters
- Associated prompts
- UI presentation details 