# AI Analysis System - API Reference

## Table of Contents

1. [Core Classes](#core-classes)
2. [Plugin Interface](#plugin-interface)
3. [Manager Interface](#manager-interface)
4. [Data Structures](#data-structures)
5. [Integration Layer](#integration-layer)
6. [Error Handling](#error-handling)
7. [Examples](#examples)

## Core Classes

### BaseAnalysisPlugin

Abstract base class that defines the interface all AI analysis plugins must implement.

#### Constructor

```python
def __init__(self, name: str, description: str, version: str = "1.0.0")
```

**Parameters:**
- `name` (str): Unique identifier for the plugin
- `description` (str): Human-readable description of plugin functionality
- `version` (str): Plugin version string (default: "1.0.0")

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | Unique plugin identifier |
| `description` | str | Human-readable description |
| `version` | str | Plugin version |
| `requires_ollama` | bool | Whether plugin requires Ollama connection |
| `max_retries` | int | Maximum retry attempts (default: 3) |
| `timeout_seconds` | int | Operation timeout in seconds (default: 60) |

#### Abstract Methods

##### analyze(content: str, **kwargs) -> AnalysisResult

Perform synchronous analysis on the given content.

**Parameters:**
- `content` (str): Text content to analyze
- `**kwargs`: Additional plugin-specific parameters

**Returns:**
- `AnalysisResult`: Analysis results or error information

**Raises:**
- `NotImplementedError`: If not implemented by subclass

##### analyze_async(content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult

Perform asynchronous analysis with progress tracking and cancellation support.

**Parameters:**
- `content` (str): Text content to analyze
- `progress_callback` (Callable[[int], None], optional): Function to call with progress updates (0-100)
- `cancel_event` (threading.Event, optional): Event for cancellation support
- `**kwargs`: Additional plugin-specific parameters

**Returns:**
- `AnalysisResult`: Analysis results or error information

#### Helper Methods

##### validate_content(content: str) -> bool

Validate that content is suitable for this analysis type.

**Parameters:**
- `content` (str): Content to validate

**Returns:**
- `bool`: True if content is valid for analysis

##### get_config() -> Dict[str, Any]

Get plugin configuration parameters.

**Returns:**
- `Dict[str, Any]`: Configuration dictionary with plugin settings

#### Protected Methods

##### _create_success_result(data: Dict[str, Any], message: str, processing_time: float = 0.0) -> AnalysisResult

Create a standardized success result.

**Parameters:**
- `data` (Dict[str, Any]): Analysis results
- `message` (str): Success message
- `processing_time` (float): Time taken for analysis

**Returns:**
- `AnalysisResult`: Success result object

##### _create_error_result(message: str, error: Optional[Exception] = None) -> AnalysisResult

Create a standardized error result.

**Parameters:**
- `message` (str): Error message for the user
- `error` (Exception, optional): Original exception for debugging

**Returns:**
- `AnalysisResult`: Error result object

##### _check_cancellation(cancel_event: Optional[Event]) -> bool

Check if operation should be cancelled.

**Parameters:**
- `cancel_event` (Event, optional): Cancellation event

**Returns:**
- `bool`: True if operation should be cancelled

##### _update_progress(progress_callback: Optional[Callable[[int], None]], progress: int)

Update progress if callback is provided.

**Parameters:**
- `progress_callback` (Callable, optional): Progress update function
- `progress` (int): Progress percentage (0-100)

## Plugin Interface

### TaggingPlugin

AI-powered tagging analysis plugin for extracting relevant tags and keywords.

#### Constructor

```python
def __init__(self)
```

#### Properties

- `name`: "tagging"
- `description`: "Extract relevant tags and keywords from content using AI"
- `max_tags_length`: 100 (maximum allowed response length)

#### Methods

##### analyze(content: str, **kwargs) -> AnalysisResult

Extract tags from content using Ollama AI.

**Returns AnalysisResult with:**
- `data.tags` (List[str]): List of extracted tags
- Message indicating number of tags extracted

##### analyze_async(content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult

Asynchronous tag extraction with progress tracking.

##### validate_content(content: str) -> bool

Validates content is at least 10 characters long.

### SummarizationPlugin

AI-powered content summarization plugin.

#### Constructor

```python
def __init__(self)
```

#### Properties

- `name`: "summarization"
- `description`: "Generate concise summaries of content using AI"
- `max_summary_length`: 500 (maximum characters for summary)
- `min_content_length`: 100 (minimum content length to summarize)

#### Methods

##### analyze(content: str, **kwargs) -> AnalysisResult

Generate summary of content.

**Parameters:**
- `summary_type` (str): "brief", "detailed", or "bullet" (default: "brief")
- `max_sentences` (int): Maximum sentences in summary (default: 3)

**Returns AnalysisResult with:**
- `data.summary` (str): Generated summary
- `data.summary_type` (str): Type of summary generated
- `data.original_length` (int): Length of original content
- `data.summary_length` (int): Length of generated summary
- `data.compression_ratio` (float): Ratio of summary to original length

##### validate_content(content: str) -> bool

Validates content is at least 100 characters long.

### SentimentPlugin

AI-powered sentiment analysis plugin.

#### Constructor

```python
def __init__(self)
```

#### Properties

- `name`: "sentiment"
- `description`: "Analyze emotional tone and sentiment of content using AI"
- `min_content_length`: 20 (minimum content length for meaningful analysis)

#### Methods

##### analyze(content: str, **kwargs) -> AnalysisResult

Analyze sentiment of content.

**Parameters:**
- `analysis_type` (str): "basic", "detailed", or "emotional" (default: "basic")
- `language` (str): Content language hint (default: "japanese")

**Returns AnalysisResult with:**
- `data.overall_sentiment` (str): Overall sentiment classification
- `data.emotions_detected` (List[str]): List of detected emotions
- `data.intensity` (str): Emotional intensity level
- `data.raw_analysis` (str): Raw AI response
- `data.analysis_type` (str): Type of analysis performed

##### validate_content(content: str) -> bool

Validates content is at least 20 characters long.

## Manager Interface

### AIAnalysisManager

Central management system for AI analysis plugins.

#### Constructor

```python
def __init__(self)
```

#### Properties

- `plugins` (Dict[str, BaseAnalysisPlugin]): Dictionary of registered plugins
- `logger` (logging.Logger): Logger for operation tracking

#### Methods

##### register_plugin(plugin: BaseAnalysisPlugin) -> bool

Register a new analysis plugin.

**Parameters:**
- `plugin` (BaseAnalysisPlugin): Plugin instance to register

**Returns:**
- `bool`: True if registration successful, False if plugin name conflicts

##### unregister_plugin(plugin_name: str) -> bool

Unregister an analysis plugin.

**Parameters:**
- `plugin_name` (str): Name of plugin to unregister

**Returns:**
- `bool`: True if unregistration successful

##### get_available_plugins() -> List[str]

Get list of available plugin names.

**Returns:**
- `List[str]`: Names of all registered plugins

##### get_plugin_info(plugin_name: str) -> Optional[Dict[str, Any]]

Get information about a specific plugin.

**Parameters:**
- `plugin_name` (str): Name of the plugin

**Returns:**
- `Optional[Dict[str, Any]]`: Plugin configuration or None if not found

##### analyze(content: str, plugin_name: str, **kwargs) -> AnalysisResult

Run synchronous analysis using specified plugin.

**Parameters:**
- `content` (str): Content to analyze
- `plugin_name` (str): Name of plugin to use
- `**kwargs`: Additional plugin-specific parameters

**Returns:**
- `AnalysisResult`: Analysis results or error

##### analyze_async(content: str, plugin_name: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult

Run asynchronous analysis using specified plugin.

**Parameters:**
- `content` (str): Content to analyze
- `plugin_name` (str): Name of plugin to use
- `progress_callback` (Callable, optional): Progress update function
- `cancel_event` (Event, optional): Cancellation event
- `**kwargs`: Additional plugin-specific parameters

**Returns:**
- `AnalysisResult`: Analysis results or error

##### analyze_multiple(content: str, plugin_names: List[str], parallel: bool = False, **kwargs) -> Dict[str, AnalysisResult]

Run analysis using multiple plugins.

**Parameters:**
- `content` (str): Content to analyze
- `plugin_names` (List[str]): Names of plugins to use
- `parallel` (bool): Whether to run plugins in parallel (not implemented yet)
- `**kwargs`: Additional plugin-specific parameters

**Returns:**
- `Dict[str, AnalysisResult]`: Results from each plugin

##### get_analysis_summary(results: Dict[str, AnalysisResult]) -> Dict[str, Any]

Generate summary of analysis results from multiple plugins.

**Parameters:**
- `results` (Dict[str, AnalysisResult]): Results from multiple plugins

**Returns:**
- `Dict[str, Any]`: Summary information including success rates and timing

## Data Structures

### AnalysisResult

Data structure for AI analysis results.

#### Constructor

```python
@dataclass
class AnalysisResult:
    success: bool
    data: Dict[str, Any]
    message: str
    processing_time: float = 0.0
    plugin_name: str = ""
    metadata: Dict[str, Any] = None
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `success` | bool | Whether the analysis completed successfully |
| `data` | Dict[str, Any] | Analysis results (tags, summary, sentiment, etc.) |
| `message` | str | Human-readable status/error message |
| `processing_time` | float | Time taken for analysis in seconds |
| `plugin_name` | str | Name of the plugin that performed the analysis |
| `metadata` | Dict[str, Any] | Additional metadata about the analysis |

## Integration Layer

### AppLogic Integration

The AI analysis system is integrated into the existing AppLogic class.

#### New Methods

##### run_ai_analysis(content: str, analysis_type: str, **kwargs) -> dict

Run AI analysis using the new modular system.

**Parameters:**
- `content` (str): Text content to analyze
- `analysis_type` (str): Type of analysis ("tagging", "summarization", "sentiment")
- `**kwargs`: Analysis-type specific parameters

**Returns:**
- `dict`: Analysis result dictionary with keys: success, data, message, processing_time, plugin_name, metadata

##### get_available_ai_functions() -> list

Get list of available AI analysis functions.

**Returns:**
- `list`: List of plugin information dictionaries

##### run_ai_analysis_async(path: str, content: str, analysis_type: str, **kwargs) -> str

Run AI analysis asynchronously and store results in database.

**Parameters:**
- `path` (str): File path for database storage
- `content` (str): Text content to analyze
- `analysis_type` (str): Type of analysis to perform
- `**kwargs`: Analysis-type specific parameters including callbacks

**Returns:**
- `str`: Operation ID for async operation tracking

#### Modified Methods

##### analyze_and_update_tags(path, content, cancel_event=None) -> Tuple[bool, str]

Updated to use new AI analysis system internally while maintaining API compatibility.

##### analyze_and_update_tags_async(path: str, content: str, **kwargs) -> str

Updated to use new AI analysis system internally while maintaining API compatibility.

## Error Handling

### Exception Types

The system uses standard Python exceptions with specific handling:

- `ValueError`: Invalid input parameters
- `RuntimeError`: Plugin execution errors
- `ConnectionError`: Ollama connection issues
- `TimeoutError`: Operation timeout
- `SecurityError`: Security validation failures

### Error Result Structure

Error results follow a consistent structure:

```python
AnalysisResult(
    success=False,
    data={},
    message="User-friendly error message",
    plugin_name="plugin_name",
    metadata={
        "error_type": "ExceptionType",
        "error_details": "Detailed error information"
    }
)
```

## Examples

### Basic Usage

```python
from ai_analysis import AIAnalysisManager, TaggingPlugin

# Initialize manager and register plugins
manager = AIAnalysisManager()
manager.register_plugin(TaggingPlugin())

# Run analysis
content = "This is a document about Python programming and machine learning."
result = manager.analyze(content, "tagging")

if result.success:
    tags = result.data["tags"]
    print(f"Extracted tags: {tags}")
else:
    print(f"Analysis failed: {result.message}")
```

### Asynchronous Analysis with Progress

```python
from threading import Event

def progress_callback(progress):
    print(f"Progress: {progress}%")

def completion_callback(result):
    if result.success:
        print(f"Analysis completed: {result.message}")
    else:
        print(f"Analysis failed: {result.message}")

cancel_event = Event()

# Run async analysis
manager.analyze_async(
    content,
    "summarization",
    progress_callback=progress_callback,
    summary_type="detailed",
    max_sentences=5
)
```

### Multiple Analysis Types

```python
# Run multiple analysis types
plugins = ["tagging", "summarization", "sentiment"]
results = manager.analyze_multiple(content, plugins)

for plugin_name, result in results.items():
    if result.success:
        print(f"{plugin_name}: {result.message}")
    else:
        print(f"{plugin_name} failed: {result.message}")

# Get summary
summary = manager.get_analysis_summary(results)
print(f"Success rate: {summary['success_rate']:.1%}")
```

### Integration with AppLogic

```python
from logic import AppLogic
from tinydb import TinyDB

# Initialize application
db = TinyDB('test.json')
app_logic = AppLogic(db)

# Get available functions
functions = app_logic.get_available_ai_functions()
print("Available AI functions:")
for func in functions:
    print(f"- {func['name']}: {func['description']}")

# Run analysis
result = app_logic.run_ai_analysis(content, "sentiment", analysis_type="detailed")
if result["success"]:
    sentiment = result["data"]["overall_sentiment"]
    print(f"Content sentiment: {sentiment}")
```

### Custom Plugin Development

```python
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
import time

class ReadabilityPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__(
            name="readability",
            description="Analyze content readability and complexity",
            version="1.0.0"
        )
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        start_time = time.time()
        
        # Simple readability analysis
        words = len(content.split())
        sentences = content.count('.') + content.count('!') + content.count('?')
        avg_words_per_sentence = words / max(sentences, 1)
        
        if avg_words_per_sentence < 15:
            level = "Easy"
        elif avg_words_per_sentence < 20:
            level = "Medium"
        else:
            level = "Hard"
        
        processing_time = time.time() - start_time
        
        return self._create_success_result(
            data={
                "readability_level": level,
                "word_count": words,
                "sentence_count": sentences,
                "avg_words_per_sentence": round(avg_words_per_sentence, 1)
            },
            message=f"Readability analysis completed: {level} level",
            processing_time=processing_time
        )
    
    def analyze_async(self, content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
        if progress_callback:
            progress_callback(50)
        
        result = self.analyze(content, **kwargs)
        
        if progress_callback:
            progress_callback(100)
        
        return result

# Register and use custom plugin
manager.register_plugin(ReadabilityPlugin())
result = manager.analyze(content, "readability")
```