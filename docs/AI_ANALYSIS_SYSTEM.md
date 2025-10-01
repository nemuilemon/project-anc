# AI Analysis System Documentation

**Version:** 3.0.0
**Last Updated:** October 1, 2025
**Status:** Production Ready with Dynamic Plugin Loading

## Overview

Project A.N.C. features a **dynamic, auto-discovering AI analysis system** that automatically loads plugins at runtime without requiring code changes. The system is built on a modern plugin architecture with dynamic discovery, making it effortless to add new analysis types.

## Architecture v3.0

### Core Components

1. **BaseAnalysisPlugin** - Abstract base class defining the plugin interface
2. **AIAnalysisManager** - Central coordinator for managing and executing plugins
3. **PluginManager** - **[NEW v3.0]** Dynamic plugin discovery and loading system
4. **Analysis Plugins** - Auto-discovered concrete implementations
5. **Integration Layer** - Seamless integration with AppLogic and AppState

### Dynamic Plugin System (v3.0)

The system uses **runtime plugin discovery** via `PluginManager`:

```python
# app/plugin_manager.py
class PluginManager:
    """Dynamically discovers and loads analysis plugins at runtime"""

    def discover_plugins(self) -> Dict[str, Type[BaseAnalysisPlugin]]:
        """Automatically scans ai_analysis/plugins/ for plugin classes"""
        # Returns dictionary of plugin_name -> plugin_class
```

**Key Features:**
- **Zero Configuration**: Drop a new plugin file in `ai_analysis/plugins/` and it's automatically discovered
- **Runtime Loading**: Uses `importlib` for dynamic module loading
- **Validation**: Automatic plugin validation and error handling
- **Registry**: Centralized plugin registry with metadata
- **Capability Filtering**: Filter plugins by capabilities (async, Ollama, etc.)

**Benefits:**
- **Easy Extension**: Add plugins without modifying any existing code
- **Hot Discovery**: Plugins discovered on app startup
- **Isolation**: Each plugin is self-contained with its own logic
- **Consistency**: All plugins follow the same interface
- **Testability**: Each plugin can be tested independently

## Available Plugins (Auto-Discovered)

All plugins are automatically discovered from `app/ai_analysis/plugins/` directory. As of v3.0, the following plugins are included:

### 1. Tagging Plugin (`tagging_plugin.py`)

**File:** `app/ai_analysis/plugins/tagging_plugin.py`
**Auto-Discovered:** ✓

Extracts relevant tags and keywords from content using **Ollama AI analysis**.

**Features:**
- AI-powered keyword extraction with Japanese prompts
- Retry logic for handling long AI responses
- Configurable tag limits (default: 5-8 tags)
- Asynchronous execution with progress tracking
- Automatic content truncation and re-prompting

**Usage:**
```python
# Via PluginManager (automatic discovery)
plugins = plugin_manager.get_available_plugins()
result = plugins['tagging'].analyze(content)

# Via AIAnalysisManager
result = ai_manager.analyze(content, "tagging")

# Asynchronous with progress tracking
result = ai_manager.analyze_async(
    content,
    "tagging",
    progress_callback=progress_callback,
    cancel_event=cancel_event
)
```

### 2. Summarization Plugin (`summarization_plugin.py`)

**File:** `app/ai_analysis/plugins/summarization_plugin.py`
**Auto-Discovered:** ✓

Generates concise summaries using **Ollama AI analysis**.

**Features:**
- AI-powered text summarization with Japanese prompts
- Multiple summary types: brief, detailed, bullet points
- Configurable summary length (max_sentences parameter)
- Automatic length optimization
- Intelligent re-prompting for overly long summaries

**Parameters:**
- `summary_type`: "brief", "detailed", or "bullet" (default: "brief")
- `max_sentences`: Maximum sentences (default: 3)

**Usage:**
```python
result = ai_manager.analyze(
    content,
    "summarization",
    summary_type="detailed",
    max_sentences=5
)
```

### 3. Sentiment Compass Plugin (`sentiment_compass_plugin.py`)

**File:** `app/ai_analysis/plugins/sentiment_compass_plugin.py`
**Auto-Discovered:** ✓

Analyzes emotional tone and sentiment using **Ollama AI analysis**.

**Features:**
- AI-powered sentiment analysis with Japanese prompts
- Overall sentiment classification (positive/negative/neutral)
- Detailed emotion detection (joy, sadness, anger, fear, surprise, disgust)
- Intensity analysis (weak/moderate/strong) with 0-10 scales
- Multiple analysis modes: basic, detailed, emotional
- Tone analysis (formal/casual/passionate/calm)

**Parameters:**
- `analysis_type`: "basic", "detailed", or "emotional" (default: "basic")
- `language`: Content language hint (default: "japanese")

**Usage:**
```python
result = ai_manager.analyze(
    content,
    "sentiment_compass",
    analysis_type="detailed"
)
```

### Plugin Discovery Statistics

Current system (v3.0):
- **Total Plugins Discovered:** 3
- **Discovery Time:** <100ms
- **Loading Method:** Dynamic importlib
- **Auto-Registration:** ✓ Enabled

## System Requirements

### Ollama Setup

The AI analysis system requires **Ollama** to be installed and running locally.

**Installation:**
1. Download Ollama from https://ollama.com/download
2. Install Ollama on your system
3. Pull the required AI model:
   ```bash
   ollama pull gemma3:4b    # Default model (v3.0)
   ```

**Alternative Models:**
```bash
ollama pull llama3.1:8b    # Larger, more capable
ollama pull gemma2:9b      # Alternative option
```

**Configuration:**
Set `OLLAMA_MODEL` in `config/config.py`:
```python
OLLAMA_MODEL = "gemma3:4b"  # Default for v3.0
```

**Verify Installation:**
```bash
ollama serve                # Start Ollama server
ollama list                 # Check installed models
```

**Error Handling:**
- If Ollama is not running, analysis fails gracefully with user-friendly messages
- Connection errors are logged to `logs/errors.log.*`
- System fallback: Manual analysis or retry when Ollama becomes available
- Plugin status displayed in AI Analysis tab

### Dependencies

```txt
flet>=0.28.0               # UI framework
tinydb>=4.8.0              # Lightweight database
ollama>=0.1.7              # AI integration
google-generativeai>=1.38  # Gemini API (for Alice)
python-dotenv>=1.0.0       # Environment variables
```

## API Reference

### BaseAnalysisPlugin

Abstract base class for all AI analysis plugins.

#### Methods

```python
def analyze(self, content: str, **kwargs) -> AnalysisResult:
    \"\"\"Perform synchronous analysis on the given content.\"\"\"

def analyze_async(self, content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
    \"\"\"Perform asynchronous analysis with progress tracking and cancellation support.\"\"\"

def validate_content(self, content: str) -> bool:
    \"\"\"Validate that content is suitable for this analysis type.\"\"\"

def get_config(self) -> Dict[str, Any]:
    \"\"\"Get plugin configuration parameters.\"\"\"
```

#### Properties

- `name`: Unique plugin identifier
- `description`: Human-readable description
- `version`: Plugin version
- `requires_ollama`: Whether plugin requires Ollama connection
- `max_retries`: Maximum retry attempts
- `timeout_seconds`: Operation timeout

### AIAnalysisManager

Central management system for AI analysis plugins.

#### Methods

```python
def register_plugin(self, plugin: BaseAnalysisPlugin) -> bool:
    \"\"\"Register a new analysis plugin (called by PluginManager).\"\"\"

def analyze(self, content: str, plugin_name: str, **kwargs) -> AnalysisResult:
    \"\"\"Run synchronous analysis using specified plugin.\"\"\"

def analyze_async(self, content: str, plugin_name: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
    \"\"\"Run asynchronous analysis using specified plugin.\"\"\"

def analyze_multiple(self, content: str, plugin_names: List[str], **kwargs) -> Dict[str, AnalysisResult]:
    \"\"\"Run analysis using multiple plugins.\"\"\"

def get_available_plugins(self) -> List[str]:
    \"\"\"Get list of available plugin names.\"\"\"
```

### PluginManager (v3.0)

**File:** `app/plugin_manager.py`

Dynamic plugin discovery and loading system.

#### Methods

```python
def discover_plugins(self) -> Dict[str, Type[BaseAnalysisPlugin]]:
    \"\"\"Discover all plugins in ai_analysis/plugins/ directory.

    Returns:
        Dictionary mapping plugin names to plugin classes
    \"\"\"

def get_available_plugins(self) -> Dict[str, Type[BaseAnalysisPlugin]]:
    \"\"\"Get all discovered plugins.\"\"\"

def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
    \"\"\"Get metadata for a specific plugin.

    Returns:
        {
            'name': str,
            'description': str,
            'version': str,
            'file': str,
            'requires_ollama': bool
        }
    \"\"\"

def reload_plugins(self) -> int:
    \"\"\"Reload all plugins (for future hot-reload support).

    Returns:
        Number of plugins discovered
    \"\"\"
```

#### Discovery Process

1. Scans `app/ai_analysis/plugins/` directory
2. Imports each `.py` file using `importlib`
3. Inspects module for `BaseAnalysisPlugin` subclasses
4. Validates plugin interface compliance
5. Registers valid plugins to `AIAnalysisManager`
6. Logs discovery statistics

### AnalysisResult

Data structure for analysis results.

#### Attributes

- `success` (bool): Whether analysis completed successfully
- `data` (Dict[str, Any]): Analysis results (tags, summary, sentiment, etc.)
- `message` (str): Human-readable status/error message
- `processing_time` (float): Time taken for analysis in seconds
- `plugin_name` (str): Name of plugin that performed analysis
- `metadata` (Dict[str, Any]): Additional metadata about analysis

## Integration with AppLogic

The AI analysis system is seamlessly integrated with the existing AppLogic class:

### New Methods

```python
def run_ai_analysis(self, content: str, analysis_type: str, **kwargs) -> dict:
    \"\"\"Run any AI analysis type and return results.\"\"\"

def get_available_ai_functions(self) -> list:
    \"\"\"Get list of available AI analysis functions.\"\"\"

def run_ai_analysis_async(self, path: str, content: str, analysis_type: str, **kwargs) -> str:
    \"\"\"Run async AI analysis and store results in database.\"\"\"
```

### Backwards Compatibility

Existing methods continue to work unchanged:

```python
def analyze_and_update_tags(self, path, content, cancel_event=None):
    \"\"\"Legacy tagging method - now uses new plugin system internally.\"\"\"

def analyze_and_update_tags_async(self, path: str, content: str, **kwargs) -> str:
    \"\"\"Legacy async tagging - now uses new plugin system internally.\"\"\"
```

## Database Integration

Analysis results are automatically stored in the database:

- **Tagging results**: Stored in the `tags` field (maintains existing behavior)
- **Other analysis results**: Stored in the `ai_analysis` field with structure:

```json
{
  "ai_analysis": {
    "summarization": {
      "data": {"summary": "...", "summary_type": "brief"},
      "timestamp": 1699123456.789,
      "processing_time": 2.34
    },
    "sentiment": {
      "data": {"overall_sentiment": "positive", "emotions_detected": ["joy"]},
      "timestamp": 1699123456.789,
      "processing_time": 1.23
    }
  }
}
```

## Error Handling

The system includes comprehensive error handling:

### Plugin Level
- Content validation
- Ollama connection errors
- Processing timeouts
- Retry logic with exponential backoff

### Manager Level
- Plugin not found errors
- Invalid parameter handling
- Progress tracking errors
- Cancellation support

### Integration Level
- Database transaction safety
- File system error recovery
- Legacy compatibility maintenance

## Testing

The system includes a comprehensive test suite:

### Test Categories

1. **Base Plugin Tests** (`test_base_plugin.py`)
   - Abstract base class functionality
   - AnalysisResult data structure
   - Common plugin behaviors

2. **Manager Tests** (`test_ai_manager.py`)
   - Plugin registration and management
   - Analysis coordination
   - Error handling and recovery

3. **Plugin Tests** (`test_plugins.py`)
   - Individual plugin functionality
   - Ollama integration mocking
   - Plugin-specific features

4. **Integration Tests** (`test_integration.py`)
   - Complete system integration
   - Backwards compatibility
   - Database interactions

### Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific category
python tests/run_tests.py plugins
python tests/run_tests.py integration
```

## Configuration

### Ollama Model Configuration

The system uses the model specified in `config.py`:

```python
OLLAMA_MODEL = "llama3.1:8b"  # Recommended model for AI analysis
```

### Plugin Configuration

Each plugin can be configured individually:

```python
# Example: Configure tagging plugin
tagging_plugin = TaggingPlugin()
tagging_plugin.max_retries = 5
tagging_plugin.timeout_seconds = 120
```

## Adding New Plugins (v3.0 - Zero Configuration!)

Adding a new plugin in v3.0 is incredibly simple thanks to automatic discovery:

### Step 1: Create Plugin File

Create a new Python file in `app/ai_analysis/plugins/`:

```python
# app/ai_analysis/plugins/my_custom_plugin.py

from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
import time

class MyCustomPlugin(BaseAnalysisPlugin):
    """Custom analysis plugin - automatically discovered!"""

    def __init__(self):
        super().__init__(
            name="my_custom",
            description="My custom analysis functionality",
            version="1.0.0"
        )
        self.requires_ollama = False  # Set to True if using Ollama

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        """Synchronous analysis implementation."""
        start_time = time.time()

        try:
            # Implement your analysis logic here
            result_data = {
                "analysis_result": "Your analysis here",
                "custom_field": kwargs.get("custom_param", "default")
            }

            return AnalysisResult(
                success=True,
                data=result_data,
                message="Analysis completed successfully",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                data={},
                message=f"Analysis failed: {str(e)}",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

    def analyze_async(self, content: str, progress_callback=None,
                      cancel_event=None, **kwargs) -> AnalysisResult:
        """Async analysis with progress tracking."""
        # Implement async logic with progress updates
        if progress_callback:
            progress_callback(0.5, "Processing...")

        return self.analyze(content, **kwargs)
```

### Step 2: Restart Application

**That's it!** The plugin is automatically discovered and loaded.

No code changes needed. No registration calls needed. Just drop the file and restart.

### Step 3: Verify Plugin Loaded

Check application logs:

```
[INFO] PluginManager: Discovered 4 plugins
[INFO] PluginManager: Registered plugin: my_custom
```

### Step 4: Use Your Plugin

```python
# In your code
result = app_logic.run_ai_analysis(content, "my_custom", custom_param="value")

# Or via UI
# Select "My Custom" from AI Analysis dropdown
```

### Step 5: Add Tests (Optional but Recommended)

```python
# tests/test_custom_plugin.py

def test_my_custom_plugin():
    plugin = MyCustomPlugin()
    result = plugin.analyze("test content")
    assert result.success
    assert "analysis_result" in result.data
```

### Plugin Development Best Practices

1. **Naming Convention**: Use `*_plugin.py` for plugin files
2. **Class Naming**: Use descriptive class names (e.g., `MyCustomPlugin`)
3. **Error Handling**: Always return `AnalysisResult` with success status
4. **Progress Callbacks**: Implement for long-running operations
5. **Cancellation**: Check `cancel_event` in async methods
6. **Documentation**: Add docstrings to your plugin class and methods

### Advanced Plugin Features

**Using Ollama in Your Plugin:**

```python
import ollama
from config.config import OLLAMA_MODEL

class OllamaPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__(name="ollama_custom", ...)
        self.requires_ollama = True

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        try:
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": f"Analyze: {content}"}]
            )
            return AnalysisResult(success=True, data=response, ...)
        except Exception as e:
            return AnalysisResult(success=False, message=str(e), ...)
```

**Progress Tracking:**

```python
def analyze_async(self, content: str, progress_callback=None, **kwargs):
    if progress_callback:
        progress_callback(0.0, "Starting analysis...")

    # Do work...
    if progress_callback:
        progress_callback(0.5, "Processing content...")

    # More work...
    if progress_callback:
        progress_callback(1.0, "Complete!")

    return result
```

**Cancellation Support:**

```python
def analyze_async(self, content: str, cancel_event=None, **kwargs):
    for i in range(10):
        if cancel_event and cancel_event.is_set():
            return AnalysisResult(
                success=False,
                message="Analysis cancelled by user",
                ...
            )
        # Do work...
```

## Performance Considerations

### Asynchronous Execution
- Use async methods for large content analysis
- Implement progress callbacks for user feedback
- Support cancellation for long-running operations

### Memory Management
- Plugins handle content validation to prevent oversized inputs
- Results are structured to avoid memory leaks
- Database storage is optimized for query performance

### Ollama Integration
- Connection pooling for multiple concurrent requests
- Retry logic with exponential backoff for network issues
- Graceful degradation when Ollama is unavailable

## Security Considerations

### Input Validation
- All content is validated before processing
- Path traversal protection in file operations
- Input sanitization for AI prompts

### Error Information
- Error messages don't expose internal system details
- Logging captures detailed information for debugging
- User-facing messages are localized and appropriate

## Future Enhancements

### Planned Features (Post v3.0)
- [x] Dynamic plugin discovery (✓ Completed in v3.0)
- [x] Zero-configuration plugin loading (✓ Completed in v3.0)
- [ ] Hot-reload plugins without app restart
- [ ] Parallel plugin execution for multiple analysis types
- [ ] Plugin configuration UI in Settings tab
- [ ] Custom prompt templates per plugin
- [ ] Analysis result caching system
- [ ] Export functionality for analysis results
- [ ] Plugin dependency management
- [ ] Plugin marketplace/sharing system
- [ ] Plugin performance profiling

### Plugin Ideas for Future Development
- **Language Detection**: Automatically detect content language
- **Readability Analysis**: Assess content complexity and readability
- **Topic Modeling**: Extract main topics and themes
- **Entity Recognition**: Identify people, places, organizations
- **Quality Assessment**: Evaluate content quality and completeness
- **Translation**: Translate content between languages
- **Grammar Check**: Detect and suggest grammar corrections
- **Plagiarism Detection**: Check for duplicate content
- **SEO Analysis**: Analyze content for search optimization
- **Code Analysis**: Analyze code snippets for quality/security

## Troubleshooting

### Common Issues

**Plugin Not Found**
```
Error: Plugin 'unknown' not found
Solution: Check plugin name spelling and ensure plugin is registered
```

**Ollama Connection Failed**
```
Error: Ollama connection failed
Solution: Ensure Ollama is running and accessible at configured endpoint
```

**Content Validation Failed**
```
Error: Content validation failed
Solution: Check content length and format requirements for specific plugin
```

**Analysis Timeout**
```
Error: Analysis operation timed out
Solution: Increase timeout_seconds or check Ollama model performance
```

### Plugin Not Discovered

**Issue:** Custom plugin not appearing in AI Analysis tab

**Solutions:**
1. Verify file is in `app/ai_analysis/plugins/` directory
2. Ensure filename ends with `.py`
3. Check class inherits from `BaseAnalysisPlugin`
4. Verify plugin has `__init__()` method calling `super().__init__()`
5. Check logs for plugin loading errors:
   ```
   logs/app.log.* - Search for "PluginManager"
   ```
6. Restart application completely

### Plugin Import Errors

**Issue:** Plugin discovered but fails to load

**Solutions:**
1. Check for syntax errors in plugin file
2. Verify all imports are available
3. Review `logs/errors.log.*` for detailed stack trace
4. Test plugin in isolation:
   ```python
   from ai_analysis.plugins.my_plugin import MyPlugin
   plugin = MyPlugin()
   ```

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export ANC_DEBUG=1

# Or in .env file
ANC_DEBUG=1

# Run application
python app/main.py
```

Check logs:
- `logs/app.log.*` - General application logs
- `logs/errors.log.*` - Error tracking
- `logs/performance.log.*` - Performance metrics

---

**Version:** 3.0.0
**Last Updated:** October 1, 2025
**Documentation Maintained By:** Project A.N.C. Team