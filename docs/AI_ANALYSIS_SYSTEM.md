# AI Analysis System Documentation

## Overview

Project A.N.C. features a modular, extensible AI analysis system that allows for flexible expansion of AI functionalities. The system is built on a plugin-based architecture that makes it easy to add new analysis types like summarization, sentiment analysis, or custom analysis functions.

## Architecture

### Core Components

1. **BaseAnalysisPlugin** - Abstract base class defining the plugin interface
2. **AIAnalysisManager** - Central coordinator for managing and executing plugins
3. **Analysis Plugins** - Concrete implementations for specific analysis types
4. **Integration Layer** - Seamless integration with existing AppLogic

### Plugin-Based Design

The system follows a plugin pattern where each analysis type is implemented as a separate plugin class inheriting from `BaseAnalysisPlugin`. This allows for:

- **Easy Extension**: Add new analysis types without modifying existing code
- **Isolation**: Each plugin is self-contained with its own logic and error handling
- **Consistency**: All plugins follow the same interface and behavior patterns
- **Testability**: Each plugin can be tested independently

## Available Plugins

### 1. Tagging Plugin (`tagging`)

Extracts relevant tags and keywords from content using **real Ollama AI analysis**.

**Features:**
- **Ollama AI-powered** keyword extraction with Japanese prompts
- Retry logic for handling long AI responses
- Configurable tag limits (default: 5-8 tags)
- Asynchronous execution support with progress tracking
- Automatic content truncation and re-prompting for long responses

**Usage:**
```python
# Synchronous
result = ai_manager.analyze(content, "tagging")

# Asynchronous with progress tracking
result = ai_manager.analyze_async(
    content, 
    "tagging", 
    progress_callback=progress_callback,
    cancel_event=cancel_event
)
```

### 2. Summarization Plugin (`summarization`)

Generates concise summaries of content using **real Ollama AI analysis**.

**Features:**
- **Ollama AI-powered** text summarization with Japanese prompts
- Multiple summary types: brief, detailed, bullet points
- Configurable summary length (max_sentences parameter)
- Automatic length optimization and content compression
- Intelligent re-prompting for overly long summaries

**Parameters:**
- `summary_type`: "brief", "detailed", or "bullet" (default: "brief")
- `max_sentences`: Maximum sentences in summary (default: 3)

**Usage:**
```python
result = ai_manager.analyze(
    content, 
    "summarization", 
    summary_type="detailed",
    max_sentences=5
)
```

### 3. Sentiment Plugin (`sentiment`)

Analyzes emotional tone and sentiment of content using **real Ollama AI analysis**.

**Features:**
- **Ollama AI-powered** sentiment analysis with Japanese prompts
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
    "sentiment", 
    analysis_type="detailed"
)
```

## System Requirements

### Ollama Setup

The AI analysis system requires **Ollama** to be installed and running locally for real AI analysis.

**Installation:**
1. Download Ollama from https://ollama.com/download
2. Install Ollama on your system
3. Pull a compatible AI model:
   ```bash
   ollama pull llama3.1:8b    # Recommended model
   ollama pull gemma2:9b      # Alternative model
   ```

**Configuration:**
- Set `OLLAMA_MODEL` in `config.py` to your preferred model
- Ensure Ollama is running: `ollama serve`
- Verify connection: `ollama list`

**Error Handling:**
- If Ollama is not running, analysis will fail gracefully
- Connection errors are logged and displayed to users
- System fallback: Manual analysis or retry when Ollama is available

### Dependencies

```txt
flet>=0.21.0      # UI framework
tinydb>=4.8.0     # Lightweight database
ollama>=0.1.7     # AI integration
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
    \"\"\"Register a new analysis plugin.\"\"\"

def analyze(self, content: str, plugin_name: str, **kwargs) -> AnalysisResult:
    \"\"\"Run synchronous analysis using specified plugin.\"\"\"

def analyze_async(self, content: str, plugin_name: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
    \"\"\"Run asynchronous analysis using specified plugin.\"\"\"

def analyze_multiple(self, content: str, plugin_names: List[str], **kwargs) -> Dict[str, AnalysisResult]:
    \"\"\"Run analysis using multiple plugins.\"\"\"

def get_available_plugins(self) -> List[str]:
    \"\"\"Get list of available plugin names.\"\"\"
```

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

## Adding New Plugins

To add a new analysis plugin:

1. **Create Plugin Class**

```python
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult

class CustomPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__(
            name="custom",
            description="Custom analysis functionality",
            version="1.0.0"
        )
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        # Implement analysis logic
        pass
    
    def analyze_async(self, content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
        # Implement async analysis logic
        pass
```

2. **Register Plugin**

```python
# In AppLogic._setup_ai_plugins()
self.ai_manager.register_plugin(CustomPlugin())
```

3. **Add Tests**

Create test cases following the existing patterns in `tests/test_plugins.py`.

4. **Update Documentation**

Add plugin documentation to this file and update any relevant UI components.

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

### Planned Features
- Parallel plugin execution for multiple analysis types
- Plugin configuration UI
- Custom prompt templates
- Analysis result caching
- Export functionality for analysis results

### Plugin Ideas
- **Language Detection**: Automatically detect content language
- **Readability Analysis**: Assess content complexity and readability
- **Topic Modeling**: Extract main topics and themes
- **Entity Recognition**: Identify people, places, organizations
- **Quality Assessment**: Evaluate content quality and completeness

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

### Debug Mode

Enable debug logging in environment:

```bash
export ANC_DEBUG=1
python main.py
```

This will provide detailed logging for AI analysis operations and help diagnose issues.