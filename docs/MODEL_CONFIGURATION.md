# Model Configuration Guide for Project A.N.C.

## Overview

Project A.N.C. now supports configurable AI models for the Sentiment Compass (Growth Analysis) feature. You can choose which Ollama model to use for optimal performance based on your system capabilities.

## Configuration Methods

### 1. Settings UI (Recommended)
- Open Project A.N.C.
- Click the **Settings (⚙️) button** in the top navigation bar
- Select your preferred model from the dropdown
- Click "Test Connection" to verify the model works
- Click "Save Settings" to apply changes
- Restart the application for changes to take effect

### 2. Command Line Configuration
```bash
python configure_models.py
```
This script will:
- Show your current model configuration
- List available Ollama models
- Provide recommendations for model selection

### 3. Manual Configuration
Edit `config/config.py` and change:
```python
SENTIMENT_COMPASS_MODEL = "your_preferred_model"
```

## Available Model Options

| Model | Description | Memory Usage | Recommended For |
|-------|-------------|--------------|-----------------|
| `auto` | Automatic selection | Varies | Users unsure which model to use |
| `gemma3:4b` | Balanced performance | ~4GB | Most users (recommended) |
| `gemma3:27b` | High quality analysis | ~27GB | Users with high-end systems |
| `llama3.2` | General purpose | Varies | Llama model users |

## Model Requirements

1. **Ollama Installation**: Ensure Ollama is installed and running
2. **Model Download**: Your chosen model must be downloaded
   ```bash
   ollama pull gemma3:4b
   ollama pull llama3.2
   ```
3. **System Resources**: Ensure sufficient RAM for your chosen model

## Fallback Behavior

If the configured model fails:
1. System tries to use any available Ollama model
2. If no models work, falls back to test mode with sample data
3. Growth Analysis will always work, even without Ollama

## Troubleshooting

### Model Not Found (404 Error)
```bash
# Install the missing model
ollama pull gemma3:4b
```

### Connection Failed
```bash
# Start Ollama service
ollama serve
```

### Performance Issues
- Use `gemma3:4b` instead of larger models
- Set model to `auto` for automatic optimization
- Check available system RAM

## Testing Your Configuration

Run the test script to verify everything works:
```bash
python test_settings_integration.py
```

## Advanced Configuration

### Custom Model Names
If you have custom or renamed models, add them directly to the config:
```python
SENTIMENT_COMPASS_MODEL = "your_custom_model_name"
```

### Model Descriptions
Update `MODEL_DESCRIPTIONS` in `config.py` to add custom model information for the UI.

## Support

For issues with model configuration:
1. Run `python configure_models.py` for diagnostics
2. Check Ollama is running: `ollama list`
3. Verify model installation: `ollama show model_name`
4. Test with `auto` model selection as fallback