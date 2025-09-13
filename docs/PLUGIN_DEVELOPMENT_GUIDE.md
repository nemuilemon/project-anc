# Plugin Development Guide

## Overview

This guide explains how to create new AI analysis plugins for Project A.N.C.'s modular AI analysis system. The plugin architecture allows developers to easily add new analysis capabilities without modifying existing code.

## Plugin Architecture

### Base Plugin Interface

All plugins must inherit from `BaseAnalysisPlugin` and implement the required methods:

```python
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
import time
from typing import Optional, Callable
from threading import Event

class MyCustomPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__(
            name="my_custom",           # Unique identifier
            description="My custom analysis plugin",
            version="1.0.0"
        )
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        \"\"\"Synchronous analysis implementation\"\"\"
        # Your analysis logic here
        pass
    
    def analyze_async(self, 
                     content: str,
                     progress_callback: Optional[Callable[[int], None]] = None,
                     cancel_event: Optional[Event] = None,
                     **kwargs) -> AnalysisResult:
        \"\"\"Asynchronous analysis with progress tracking\"\"\"
        # Your async analysis logic here
        pass
    
    def validate_content(self, content: str) -> bool:
        \"\"\"Validate content suitability for this analysis\"\"\"
        return bool(content and content.strip())
```

### Required Methods

#### 1. `__init__(self)`
Initialize your plugin with unique name, description, and version.

#### 2. `analyze(self, content: str, **kwargs) -> AnalysisResult`
Perform synchronous analysis and return results.

#### 3. `analyze_async(self, content, progress_callback, cancel_event, **kwargs) -> AnalysisResult`
Perform asynchronous analysis with progress tracking and cancellation support.

#### 4. `validate_content(self, content: str) -> bool`
Check if content is suitable for your analysis type.

### AnalysisResult Structure

```python
@dataclass
class AnalysisResult:
    success: bool                    # Whether analysis succeeded
    data: Dict[str, Any]            # Analysis results
    message: str                    # User-friendly message
    processing_time: float = 0.0    # Time taken in seconds
    plugin_name: str = ""           # Plugin identifier
    metadata: Dict[str, Any] = None # Additional metadata
```

## Step-by-Step Plugin Creation

### Step 1: Create Plugin File

Create a new file in `ai_analysis/plugins/` directory:

```bash
# Example: ai_analysis/plugins/readability_plugin.py
```

### Step 2: Implement Plugin Class

```python
\"\"\"Readability Analysis Plugin.

This plugin analyzes text readability using various metrics.
\"\"\"

import time
import re
from typing import List, Dict, Any, Optional, Callable
from threading import Event

from ..base_plugin import BaseAnalysisPlugin, AnalysisResult

class ReadabilityPlugin(BaseAnalysisPlugin):
    \"\"\"Readability analysis plugin.
    
    Analyzes text complexity using readability metrics like
    Flesch Reading Ease, word complexity, sentence structure, etc.
    \"\"\"
    
    def __init__(self):
        super().__init__(
            name="readability",
            description="Analyze text readability and complexity",
            version="1.0.0"
        )
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        \"\"\"Perform synchronous readability analysis.\"\"\"
        start_time = time.time()
        
        try:
            # Calculate readability metrics
            metrics = self._calculate_readability_metrics(content)
            processing_time = time.time() - start_time
            
            return self._create_success_result(
                data={"readability_metrics": metrics},
                message=f"Readability score: {metrics.get('flesch_score', 0):.1f}",
                processing_time=processing_time
            )
            
        except Exception as e:
            return self._create_error_result("Readability analysis failed", e)
    
    def analyze_async(self,
                     content: str,
                     progress_callback: Optional[Callable[[int], None]] = None,
                     cancel_event: Optional[Event] = None,
                     **kwargs) -> AnalysisResult:
        \"\"\"Perform asynchronous readability analysis.\"\"\"
        start_time = time.time()
        
        try:
            self._update_progress(progress_callback, 20)
            
            if self._check_cancellation(cancel_event):
                return self._create_error_result("Analysis cancelled")
            
            # Calculate metrics with progress updates
            metrics = self._calculate_readability_metrics(content)
            
            self._update_progress(progress_callback, 100)
            processing_time = time.time() - start_time
            
            return self._create_success_result(
                data={"readability_metrics": metrics},
                message=f"Readability score: {metrics.get('flesch_score', 0):.1f}",
                processing_time=processing_time
            )
            
        except Exception as e:
            return self._create_error_result("Readability analysis failed", e)
    
    def _calculate_readability_metrics(self, content: str) -> Dict[str, Any]:
        \"\"\"Calculate various readability metrics.\"\"\"
        # Count sentences, words, syllables
        sentences = len(re.findall(r'[.!?]+', content))
        words = len(content.split())
        syllables = self._count_syllables(content)
        
        # Calculate Flesch Reading Ease Score
        if sentences > 0 and words > 0:
            flesch_score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        else:
            flesch_score = 0
        
        # Determine reading level
        if flesch_score >= 90:
            reading_level = "Very Easy"
        elif flesch_score >= 80:
            reading_level = "Easy"
        elif flesch_score >= 70:
            reading_level = "Fairly Easy"
        elif flesch_score >= 60:
            reading_level = "Standard"
        elif flesch_score >= 50:
            reading_level = "Fairly Difficult"
        elif flesch_score >= 30:
            reading_level = "Difficult"
        else:
            reading_level = "Very Difficult"
        
        return {
            "flesch_score": flesch_score,
            "reading_level": reading_level,
            "sentence_count": sentences,
            "word_count": words,
            "syllable_count": syllables,
            "avg_words_per_sentence": words / sentences if sentences > 0 else 0,
            "avg_syllables_per_word": syllables / words if words > 0 else 0
        }
    
    def _count_syllables(self, text: str) -> int:
        \"\"\"Simple syllable counting algorithm.\"\"\"
        # Simple vowel-based syllable counting
        vowels = "aeiouyAEIOUY"
        syllable_count = 0
        prev_was_vowel = False
        
        for char in text:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Handle special cases
        if text.endswith('e'):
            syllable_count -= 1
        if syllable_count == 0:
            syllable_count = 1
            
        return syllable_count
    
    def validate_content(self, content: str) -> bool:
        \"\"\"Validate content for readability analysis.\"\"\"
        return bool(content and content.strip() and len(content.strip()) > 50)
```

### Step 3: Register Plugin

Add your plugin to the main `__init__.py` file:

```python
# In ai_analysis/__init__.py
from .plugins.readability_plugin import ReadabilityPlugin

__all__ = [
    'BaseAnalysisPlugin',
    'AnalysisResult', 
    'AIAnalysisManager',
    'TaggingPlugin',
    'SummarizationPlugin',
    'SentimentPlugin',
    'ReadabilityPlugin'  # Add your plugin
]
```

### Step 4: Register in AppLogic

Add plugin registration in `logic.py`:

```python
# In logic.py _setup_ai_plugins method
def _setup_ai_plugins(self):
    \"\"\"Initialize and register AI analysis plugins.\"\"\"
    from ai_analysis import TaggingPlugin, SummarizationPlugin, SentimentPlugin, ReadabilityPlugin
    
    # Register plugins
    self.ai_manager.register_plugin(TaggingPlugin())
    self.ai_manager.register_plugin(SummarizationPlugin())
    self.ai_manager.register_plugin(SentimentPlugin())
    self.ai_manager.register_plugin(ReadabilityPlugin())  # Add your plugin
```

### Step 5: Add UI Support

Update the UI dropdown in `ui.py`:

```python
# In ui.py
self.ai_analysis_dropdown = ft.Dropdown(
    label="AI Analysis Type",
    width=150,
    value="tagging",
    options=[
        ft.dropdown.Option("tagging", "Tags"),
        ft.dropdown.Option("summarization", "Summary"),
        ft.dropdown.Option("sentiment", "Sentiment"),
        ft.dropdown.Option("readability", "Readability")  # Add your option
    ]
)
```

### Step 6: Handle Results Display

Add result display logic in `ui.py`:

```python
# In show_ai_analysis_results method
elif analysis_type == "readability":
    metrics = result_data.get("readability_metrics", {})
    flesch_score = metrics.get("flesch_score", 0)
    reading_level = metrics.get("reading_level", "Unknown")
    
    content_widgets.extend([
        ft.Text(f"Reading Level: {reading_level}", weight=ft.FontWeight.BOLD),
        ft.Text(f"Flesch Score: {flesch_score:.1f}"),
        ft.Text(f"Words: {metrics.get('word_count', 0)}"),
        ft.Text(f"Sentences: {metrics.get('sentence_count', 0)}"),
        ft.Text(f"Avg Words/Sentence: {metrics.get('avg_words_per_sentence', 0):.1f}")
    ])
```

## Testing Your Plugin

### Unit Testing

Create tests for your plugin:

```python
# In test_working_components.py
def test_readability_plugin(self):
    \"\"\"Test readability plugin functionality.\"\"\"
    from ai_analysis.plugins.readability_plugin import ReadabilityPlugin
    
    plugin = ReadabilityPlugin()
    
    # Test basic functionality
    self.assertEqual(plugin.name, "readability")
    self.assertTrue(plugin.validate_content("This is a test sentence with enough content for analysis."))
    
    # Test analysis
    content = "This is a simple test. It has two sentences."
    result = plugin.analyze(content)
    
    self.assertTrue(result.success)
    self.assertIn("readability_metrics", result.data)
    self.assertGreater(result.processing_time, 0)
```

### Integration Testing

Test with AI manager:

```python
def test_readability_integration(self):
    \"\"\"Test readability plugin integration with AI manager.\"\"\"
    from ai_analysis import AIAnalysisManager
    from ai_analysis.plugins.readability_plugin import ReadabilityPlugin
    
    manager = AIAnalysisManager()
    plugin = ReadabilityPlugin()
    
    # Test registration
    self.assertTrue(manager.register_plugin(plugin))
    self.assertIn("readability", manager.get_available_plugins())
    
    # Test analysis
    result = manager.analyze("Test content for readability analysis.", "readability")
    self.assertTrue(result.success)
```

## Best Practices

### 1. Error Handling
- Always wrap analysis logic in try-catch blocks
- Return meaningful error messages to users
- Log detailed errors for debugging

```python
try:
    # Analysis logic
    result = your_analysis_function(content)
    return self._create_success_result(data=result, message="Analysis completed")
except Exception as e:
    self.logger.error(f"Analysis failed: {e}")
    return self._create_error_result("Analysis failed", e)
```

### 2. Progress Tracking
- Update progress at meaningful intervals
- Check for cancellation regularly
- Provide percentage-based progress (0-100)

```python
self._update_progress(progress_callback, 25)   # 25% complete
# ... processing ...
if self._check_cancellation(cancel_event):
    return self._create_error_result("Cancelled by user")
# ... more processing ...
self._update_progress(progress_callback, 75)   # 75% complete
```

### 3. Content Validation
- Implement meaningful validation in `validate_content()`
- Check content length, format, language as appropriate
- Return clear validation requirements

```python
def validate_content(self, content: str) -> bool:
    \"\"\"Validate content for analysis.\"\"\"
    if not content or not content.strip():
        return False
    if len(content.strip()) < 100:  # Minimum length requirement
        return False
    # Add specific validation for your analysis type
    return True
```

### 4. Configuration
- Use class attributes for configurable parameters
- Document all configuration options
- Provide sensible defaults

```python
def __init__(self):
    super().__init__(name="my_plugin", description="...", version="1.0.0")
    self.min_content_length = 100
    self.max_processing_time = 30
    self.analysis_depth = "standard"
```

### 5. Documentation
- Provide comprehensive docstrings
- Include usage examples
- Document all parameters and return values

## Advanced Features

### Ollama Integration

For AI-powered plugins, integrate with Ollama:

```python
import ollama
import config

def _analyze_with_ollama(self, content: str, prompt: str) -> str:
    \"\"\"Use Ollama for AI analysis.\"\"\"
    try:
        response = ollama.generate(
            model=config.OLLAMA_MODEL,
            prompt=prompt
        )
        return response['response'].strip()
    except Exception as e:
        raise Exception(f"Ollama analysis failed: {e}")
```

### Custom Parameters

Support plugin-specific parameters:

```python
def analyze(self, content: str, **kwargs) -> AnalysisResult:
    \"\"\"Analyze with custom parameters.\"\"\"
    analysis_depth = kwargs.get('depth', 'standard')
    language = kwargs.get('language', 'auto')
    
    # Use parameters in analysis
    if analysis_depth == 'deep':
        # Perform more detailed analysis
        pass
```

### Caching Results

Implement result caching for expensive operations:

```python
import hashlib

def analyze(self, content: str, **kwargs) -> AnalysisResult:
    \"\"\"Analyze with caching support.\"\"\"
    # Generate cache key
    cache_key = hashlib.md5(content.encode()).hexdigest()
    
    # Check cache
    if cache_key in self._cache:
        return self._cache[cache_key]
    
    # Perform analysis
    result = self._perform_analysis(content, **kwargs)
    
    # Cache result
    self._cache[cache_key] = result
    return result
```

## Plugin Examples

### Simple Text Statistics Plugin

```python
class TextStatsPlugin(BaseAnalysisPlugin):
    \"\"\"Basic text statistics plugin.\"\"\"
    
    def __init__(self):
        super().__init__(
            name="textstats",
            description="Basic text statistics analysis",
            version="1.0.0"
        )
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        start_time = time.time()
        
        try:
            stats = {
                "character_count": len(content),
                "word_count": len(content.split()),
                "sentence_count": len(re.findall(r'[.!?]+', content)),
                "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
                "avg_word_length": sum(len(word) for word in content.split()) / len(content.split()) if content.split() else 0
            }
            
            processing_time = time.time() - start_time
            
            return self._create_success_result(
                data={"statistics": stats},
                message=f"Analyzed {stats['word_count']} words",
                processing_time=processing_time
            )
        except Exception as e:
            return self._create_error_result("Text analysis failed", e)
```

### Language Detection Plugin

```python
class LanguageDetectionPlugin(BaseAnalysisPlugin):
    \"\"\"Language detection plugin.\"\"\"
    
    def __init__(self):
        super().__init__(
            name="language",
            description="Detect content language",
            version="1.0.0"
        )
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        start_time = time.time()
        
        try:
            # Simple language detection based on character patterns
            language = self._detect_language(content)
            confidence = self._calculate_confidence(content, language)
            
            processing_time = time.time() - start_time
            
            return self._create_success_result(
                data={
                    "detected_language": language,
                    "confidence": confidence,
                    "language_name": self._get_language_name(language)
                },
                message=f"Detected language: {self._get_language_name(language)} ({confidence:.1%} confidence)",
                processing_time=processing_time
            )
        except Exception as e:
            return self._create_error_result("Language detection failed", e)
    
    def _detect_language(self, content: str) -> str:
        \"\"\"Simple language detection logic.\"\"\"
        # Check for Japanese characters
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', content):
            return "ja"
        # Check for common English patterns
        elif re.search(r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b', content.lower()):
            return "en"
        else:
            return "unknown"
```

## Troubleshooting

### Common Issues

1. **Plugin Not Loading**
   - Check that plugin file is in correct directory
   - Verify __init__.py includes your plugin
   - Check for syntax errors in plugin code

2. **Import Errors**
   - Ensure all required dependencies are installed
   - Check import paths and module names
   - Verify BaseAnalysisPlugin is properly imported

3. **Analysis Failures**
   - Check content validation logic
   - Verify error handling is implemented
   - Test with various content types and lengths

4. **UI Integration Issues**
   - Ensure plugin name matches dropdown option value
   - Add result display logic for your data format
   - Test UI components with your result structure

### Debugging Tips

1. **Add Debug Logging**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.debug(f"Processing content: {content[:100]}...")
   ```

2. **Test Incrementally**
   - Test plugin in isolation first
   - Add to manager and test
   - Finally integrate with UI

3. **Use Virtual Environment Testing**
   ```bash
   source .venv/Scripts/activate
   python -c "from ai_analysis.plugins.your_plugin import YourPlugin; print('Import successful')"
   ```

## Contributing

When contributing new plugins:

1. Follow the established patterns and conventions
2. Include comprehensive tests
3. Add documentation and usage examples
4. Update relevant documentation files
5. Test in virtual environment
6. Ensure backward compatibility

This plugin system makes Project A.N.C. infinitely extensible - new analysis capabilities can be added easily while maintaining system stability and user experience.