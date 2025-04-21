# LLM Configuration Guide

## Overview
This document outlines the configuration system for LLM interactions in our static site generator.

## Configuration Structure
The LLM configuration system should be designed with the following principles:

### Model Selection
- No hardcoded defaults
- Models should be configurable via the UI
- Available models should be clearly listed in the interface
- Each action should specify its required model capabilities

### Configuration Parameters
All LLM interactions should support configurable parameters through the UI:
- Temperature
- Max tokens
- Top P
- Frequency penalty
- Presence penalty

### Environment Variables
While environment variables can be used for sensitive data (API keys), core configuration should be managed through the UI:

```env
LLM_API_KEY=your_api_key_here
```

### Provider Support
Currently supported providers:
- OpenAI
- Anthropic
- Local models (via Ollama)

Note: Hugging Face integration should be removed as it's not part of our core functionality.

## Best Practices
1. Never rely on default configurations
2. Always specify model requirements explicitly
3. Store configurations in a dedicated config directory, not in backups
4. Use version control for tracking configuration changes
5. Implement validation for all configuration parameters

## Configuration Schema
```yaml
actions:
  content_generation:
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 1000
  summarization:
    model: "claude-3-sonnet"
    temperature: 0.3
    max_tokens: 500
```

## UI Integration
The configuration interface should provide:
- Model selection dropdown for each action
- Parameter adjustment sliders/inputs
- Validation feedback
- Configuration export/import capabilities 