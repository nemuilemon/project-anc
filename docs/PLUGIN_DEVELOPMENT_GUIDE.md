# Plugin Development Guide

**Version:** 3.0.0
**Last Updated:** October 1, 2025
**Target Audience:** Plugin Developers

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Plugin Architecture](#plugin-architecture)
4. [Development Workflow](#development-workflow)
5. [Best Practices](#best-practices)
6. [Testing Plugins](#testing-plugins)
7. [Advanced Topics](#advanced-topics)
8. [Examples](#examples)

## Introduction

Project A.N.C. v3.0 features a **zero-configuration plugin system** that automatically discovers and loads analysis plugins at runtime. This guide will help you create powerful, production-ready plugins.

### What is a Plugin?

A plugin is a self-contained Python module that:
- Inherits from `BaseAnalysisPlugin`
- Implements analysis functionality
- Is automatically discovered in `app/ai_analysis/plugins/`
- Requires zero configuration or registration

### Plugin Capabilities

- **Synchronous Analysis**: Immediate results for quick operations
- **Asynchronous Analysis**: Non-blocking for long operations
- **Progress Tracking**: Real-time progress updates to UI
- **Cancellation Support**: User can cancel long-running operations
- **Ollama Integration**: Optional AI-powered analysis
- **Custom Parameters**: Accept plugin-specific configuration

## Quick Start

### Create Your First Plugin (5 minutes)

**Step 1:** Create plugin file `app/ai_analysis/plugins/hello_plugin.py`

```python
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
import time

class HelloPlugin(BaseAnalysisPlugin):
    """A simple hello world plugin"""

    def __init__(self):
        super().__init__(
            name="hello",
            description="Says hello to your content",
            version="1.0.0"
        )

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        """Analyze content and say hello"""
        start_time = time.time()

        word_count = len(content.split())

        return AnalysisResult(
            success=True,
            data={
                "greeting": f"Hello! Your content has {word_count} words.",
                "content_preview": content[:50] + "..."
            },
            message="Hello analysis completed",
            processing_time=time.time() - start_time,
            plugin_name=self.name
        )

    def analyze_async(self, content: str, progress_callback=None,
                      cancel_event=None, **kwargs) -> AnalysisResult:
        """Async version with progress tracking"""
        if progress_callback:
            progress_callback(0.5, "Saying hello...")

        return self.analyze(content, **kwargs)
```

**Step 2:** Restart application

```bash
python app/main.py
```

**Step 3:** Use your plugin

Open AI Analysis tab → Select "hello" → Run analysis

That's it! Your plugin is live.

## Plugin Architecture

### Class Structure

```python
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult

class MyPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__(
            name="my_plugin",           # Unique identifier
            description="Description",   # User-visible description
            version="1.0.0"             # Semantic version
        )
        # Plugin-specific initialization
        self.requires_ollama = False    # Set True if using Ollama
        self.max_retries = 3            # Max retry attempts
        self.timeout_seconds = 60       # Operation timeout

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        """Synchronous analysis - REQUIRED"""
        pass

    def analyze_async(self, content: str, progress_callback=None,
                      cancel_event=None, **kwargs) -> AnalysisResult:
        """Async analysis - REQUIRED"""
        pass

    def validate_content(self, content: str) -> bool:
        """Content validation - OPTIONAL"""
        return len(content) > 0

    def get_config(self) -> dict:
        """Plugin configuration - OPTIONAL"""
        return {
            "requires_ollama": self.requires_ollama,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds
        }
```

### AnalysisResult Structure

```python
AnalysisResult(
    success: bool,              # Did analysis succeed?
    data: Dict[str, Any],       # Analysis results
    message: str,               # User-facing message
    processing_time: float,     # Time taken (seconds)
    plugin_name: str,           # Your plugin name
    metadata: Dict[str, Any]    # Optional metadata
)
```

## Development Workflow

### 1. Planning Your Plugin

**Define the purpose:**
- What problem does it solve?
- What input does it need?
- What output will it produce?

**Choose analysis type:**
- Quick computation → Synchronous only
- Long AI processing → Async with progress
- External API calls → Async with retry logic

**Example planning:**
```
Plugin: Readability Analyzer
Purpose: Assess content readability level
Input: Text content
Output: Readability score, grade level, suggestions
Type: Synchronous (fast computation)
```

### 2. Implementation

**Create file structure:**
```
app/ai_analysis/plugins/
├── readability_plugin.py     # Your plugin
└── __init__.py               # Auto-generated
```

**Implement core logic:**

```python
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
import time

class ReadabilityPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__(
            name="readability",
            description="Analyze content readability",
            version="1.0.0"
        )

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        start_time = time.time()

        try:
            # Calculate readability metrics
            words = len(content.split())
            sentences = content.count('.') + content.count('!') + content.count('?')
            avg_words_per_sentence = words / max(sentences, 1)

            # Simple readability score
            if avg_words_per_sentence < 15:
                level = "Easy"
                grade = "5-8"
            elif avg_words_per_sentence < 25:
                level = "Medium"
                grade = "9-12"
            else:
                level = "Hard"
                grade = "College"

            return AnalysisResult(
                success=True,
                data={
                    "readability_level": level,
                    "grade_level": grade,
                    "words": words,
                    "sentences": sentences,
                    "avg_words_per_sentence": round(avg_words_per_sentence, 1)
                },
                message=f"Readability: {level} (Grade {grade})",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                data={},
                message=f"Readability analysis failed: {str(e)}",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

    def analyze_async(self, content: str, progress_callback=None,
                      cancel_event=None, **kwargs) -> AnalysisResult:
        # For simple plugins, just call synchronous version
        return self.analyze(content, **kwargs)
```

### 3. Testing

**Manual testing:**
```bash
# Restart app
python app/main.py

# Check logs
tail -f logs/app.log.*
# Look for: "Registered plugin: readability"
```

**Unit testing:**
```python
# tests/test_readability_plugin.py
from ai_analysis.plugins.readability_plugin import ReadabilityPlugin

def test_readability_easy():
    plugin = ReadabilityPlugin()
    content = "This is easy. It is simple. Very clear."
    result = plugin.analyze(content)

    assert result.success
    assert result.data["readability_level"] == "Easy"

def test_readability_hard():
    plugin = ReadabilityPlugin()
    content = "The implementation of quantum entanglement necessitates comprehensive understanding."
    result = plugin.analyze(content)

    assert result.success
    assert result.data["readability_level"] in ["Medium", "Hard"]
```

### 4. Deployment

**No deployment needed!** Just commit your plugin file:

```bash
git add app/ai_analysis/plugins/readability_plugin.py
git commit -m "feat: Add readability analysis plugin"
git push
```

## Best Practices

### Code Quality

**1. Error Handling**
```python
def analyze(self, content: str, **kwargs) -> AnalysisResult:
    try:
        # Analysis logic
        result = perform_analysis(content)
        return AnalysisResult(success=True, data=result, ...)
    except ValueError as e:
        # Specific error handling
        return AnalysisResult(success=False, message=f"Invalid input: {e}", ...)
    except Exception as e:
        # General error handling
        return AnalysisResult(success=False, message=f"Analysis failed: {e}", ...)
```

**2. Input Validation**
```python
def validate_content(self, content: str) -> bool:
    """Validate content before processing"""
    if not content or len(content.strip()) == 0:
        return False
    if len(content) > 1_000_000:  # 1MB limit
        return False
    return True

def analyze(self, content: str, **kwargs) -> AnalysisResult:
    if not self.validate_content(content):
        return AnalysisResult(
            success=False,
            message="Content validation failed",
            ...
        )
    # Continue with analysis
```

**3. Performance Optimization**
```python
def analyze(self, content: str, **kwargs) -> AnalysisResult:
    start_time = time.time()

    # Cache expensive computations
    if hasattr(self, '_cache') and content in self._cache:
        cached_result = self._cache[content]
        return AnalysisResult(
            success=True,
            data=cached_result,
            message="Retrieved from cache",
            processing_time=time.time() - start_time,
            plugin_name=self.name
        )

    # Perform analysis
    result = expensive_operation(content)

    # Update cache
    if not hasattr(self, '_cache'):
        self._cache = {}
    self._cache[content] = result

    return AnalysisResult(...)
```

### User Experience

**1. Clear Messages**
```python
# Bad
message="Done"

# Good
message="Analyzed 150 words, readability level: Easy (Grade 5-8)"
```

**2. Progress Updates**
```python
def analyze_async(self, content: str, progress_callback=None, **kwargs):
    if progress_callback:
        progress_callback(0.0, "Starting analysis...")

    # Step 1
    tokenize(content)
    if progress_callback:
        progress_callback(0.3, "Tokenizing content...")

    # Step 2
    analyze_tokens()
    if progress_callback:
        progress_callback(0.6, "Analyzing tokens...")

    # Step 3
    generate_report()
    if progress_callback:
        progress_callback(0.9, "Generating report...")

    if progress_callback:
        progress_callback(1.0, "Complete!")

    return result
```

**3. Cancellation Support**
```python
def analyze_async(self, content: str, cancel_event=None, **kwargs):
    for chunk in large_content_chunks:
        # Check cancellation
        if cancel_event and cancel_event.is_set():
            return AnalysisResult(
                success=False,
                message="Analysis cancelled by user",
                ...
            )

        # Process chunk
        process(chunk)

    return result
```

## Testing Plugins

### Unit Tests

```python
# tests/test_my_plugin.py
import pytest
from ai_analysis.plugins.my_plugin import MyPlugin

class TestMyPlugin:
    @pytest.fixture
    def plugin(self):
        """Create plugin instance for testing"""
        return MyPlugin()

    def test_basic_analysis(self, plugin):
        """Test basic functionality"""
        result = plugin.analyze("test content")
        assert result.success
        assert result.plugin_name == "my_plugin"
        assert "data_field" in result.data

    def test_empty_content(self, plugin):
        """Test edge case: empty content"""
        result = plugin.analyze("")
        assert not result.success

    def test_large_content(self, plugin):
        """Test edge case: large content"""
        large_content = "word " * 100000
        result = plugin.analyze(large_content)
        assert result.success or "too large" in result.message.lower()

    def test_async_with_progress(self, plugin):
        """Test async analysis with progress tracking"""
        progress_calls = []

        def track_progress(percent, message):
            progress_calls.append((percent, message))

        result = plugin.analyze_async(
            "test content",
            progress_callback=track_progress
        )

        assert result.success
        assert len(progress_calls) > 0

    def test_cancellation(self, plugin):
        """Test cancellation support"""
        import threading
        cancel_event = threading.Event()
        cancel_event.set()  # Immediately cancelled

        result = plugin.analyze_async(
            "test content",
            cancel_event=cancel_event
        )

        assert not result.success
        assert "cancel" in result.message.lower()
```

### Integration Tests

```python
# tests/test_plugin_integration.py
from app.logic import AppLogic

def test_plugin_discovery():
    """Test plugin is discovered by system"""
    logic = AppLogic()
    plugins = logic.get_available_plugins()

    plugin_names = [p['name'] for p in plugins]
    assert "my_plugin" in plugin_names

def test_plugin_execution():
    """Test plugin execution through AppLogic"""
    logic = AppLogic()
    result = logic.run_ai_analysis("test content", "my_plugin")

    assert result['success']
    assert 'data' in result

def test_plugin_with_database():
    """Test plugin results stored in database"""
    logic = AppLogic()

    # Run analysis
    result = logic.run_ai_analysis_async(
        path="test.txt",
        content="test content",
        analysis_type="my_plugin"
    )

    # Verify stored in database
    file_record = logic.get_file("test.txt")
    assert 'ai_analysis' in file_record
    assert 'my_plugin' in file_record['ai_analysis']
```

## Advanced Topics

### Using Ollama for AI-Powered Analysis

```python
import ollama
from config.config import OLLAMA_MODEL

class AIAnalysisPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__(
            name="ai_analyzer",
            description="AI-powered content analysis",
            version="1.0.0"
        )
        self.requires_ollama = True  # Mark as requiring Ollama

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        start_time = time.time()

        try:
            # Call Ollama API
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{
                    "role": "user",
                    "content": f"Analyze this content: {content}"
                }]
            )

            ai_response = response['message']['content']

            return AnalysisResult(
                success=True,
                data={"ai_analysis": ai_response},
                message="AI analysis completed",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

        except ollama.ResponseError as e:
            return AnalysisResult(
                success=False,
                message=f"Ollama error: {str(e)}",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                message=f"Analysis failed: {str(e)}",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )
```

### Retry Logic with Exponential Backoff

```python
import time

class RobustPlugin(BaseAnalysisPlugin):
    def analyze_with_retry(self, content: str, **kwargs) -> AnalysisResult:
        """Analyze with exponential backoff retry"""
        max_retries = self.max_retries
        base_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                result = self._perform_analysis(content, **kwargs)
                return result

            except TemporaryError as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    time.sleep(delay)
                    continue
                else:
                    return AnalysisResult(
                        success=False,
                        message=f"Failed after {max_retries} attempts: {e}",
                        plugin_name=self.name
                    )
```

### Custom Configuration

```python
class ConfigurablePlugin(BaseAnalysisPlugin):
    def __init__(self, custom_config: dict = None):
        super().__init__(
            name="configurable",
            description="Plugin with custom configuration",
            version="1.0.0"
        )

        # Load custom configuration
        self.config = custom_config or {}
        self.threshold = self.config.get('threshold', 0.5)
        self.mode = self.config.get('mode', 'default')

    def get_config(self) -> dict:
        """Return current configuration"""
        return {
            'threshold': self.threshold,
            'mode': self.mode,
            'requires_ollama': self.requires_ollama
        }

    def update_config(self, **kwargs):
        """Update configuration dynamically"""
        if 'threshold' in kwargs:
            self.threshold = kwargs['threshold']
        if 'mode' in kwargs:
            self.mode = kwargs['mode']

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        # Use configuration in analysis
        if self.mode == 'strict':
            threshold = self.threshold * 0.8
        else:
            threshold = self.threshold

        # Perform analysis with configured parameters
        score = calculate_score(content)
        passed = score >= threshold

        return AnalysisResult(
            success=True,
            data={
                'score': score,
                'passed': passed,
                'threshold_used': threshold,
                'mode': self.mode
            },
            message=f"Score: {score:.2f} (threshold: {threshold})",
            plugin_name=self.name
        )
```

## Examples

### Example 1: Word Frequency Analyzer

```python
from collections import Counter
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
import time

class WordFrequencyPlugin(BaseAnalysisPlugin):
    """Analyze word frequency in content"""

    def __init__(self):
        super().__init__(
            name="word_frequency",
            description="Analyze word frequency and find most common words",
            version="1.0.0"
        )

    def analyze(self, content: str, top_n: int = 10, **kwargs) -> AnalysisResult:
        start_time = time.time()

        try:
            # Tokenize and count
            words = content.lower().split()
            word_counts = Counter(words)

            # Get top N words
            top_words = word_counts.most_common(top_n)

            # Calculate statistics
            total_words = len(words)
            unique_words = len(word_counts)

            return AnalysisResult(
                success=True,
                data={
                    "top_words": [
                        {"word": word, "count": count, "frequency": count/total_words}
                        for word, count in top_words
                    ],
                    "total_words": total_words,
                    "unique_words": unique_words,
                    "vocabulary_richness": unique_words / total_words if total_words > 0 else 0
                },
                message=f"Found {unique_words} unique words in {total_words} total words",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                data={},
                message=f"Word frequency analysis failed: {str(e)}",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

    def analyze_async(self, content: str, progress_callback=None,
                      cancel_event=None, **kwargs) -> AnalysisResult:
        if progress_callback:
            progress_callback(0.5, "Analyzing word frequency...")

        return self.analyze(content, **kwargs)
```

### Example 2: Language Detector

```python
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
import time

class LanguageDetectorPlugin(BaseAnalysisPlugin):
    """Detect the language of content"""

    def __init__(self):
        super().__init__(
            name="language_detector",
            description="Detect content language",
            version="1.0.0"
        )

        # Simple language patterns (extend with real language detection library)
        self.patterns = {
            'japanese': ['は', 'が', 'を', 'に', 'の'],
            'english': ['the', 'is', 'are', 'and', 'of'],
            'chinese': ['的', '是', '了', '在', '和']
        }

    def detect_language(self, content: str) -> tuple:
        """Detect language with confidence score"""
        scores = {}

        for language, markers in self.patterns.items():
            score = sum(content.count(marker) for marker in markers)
            scores[language] = score

        if not scores or max(scores.values()) == 0:
            return 'unknown', 0.0

        detected = max(scores, key=scores.get)
        confidence = scores[detected] / sum(scores.values())

        return detected, confidence

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        start_time = time.time()

        try:
            language, confidence = self.detect_language(content)

            return AnalysisResult(
                success=True,
                data={
                    "detected_language": language,
                    "confidence": round(confidence, 2),
                    "all_scores": {lang: score for lang, score in
                                  zip(self.patterns.keys(),
                                      [sum(content.count(m) for m in markers)
                                       for markers in self.patterns.values()])}
                },
                message=f"Detected: {language.title()} (confidence: {confidence:.1%})",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                data={},
                message=f"Language detection failed: {str(e)}",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

    def analyze_async(self, content: str, progress_callback=None,
                      cancel_event=None, **kwargs) -> AnalysisResult:
        return self.analyze(content, **kwargs)
```

### Example 3: Content Statistics

```python
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
import time
import re

class ContentStatisticsPlugin(BaseAnalysisPlugin):
    """Comprehensive content statistics"""

    def __init__(self):
        super().__init__(
            name="content_statistics",
            description="Generate comprehensive content statistics",
            version="1.0.0"
        )

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        start_time = time.time()

        try:
            # Character statistics
            total_chars = len(content)
            letters = sum(c.isalpha() for c in content)
            digits = sum(c.isdigit() for c in content)
            spaces = sum(c.isspace() for c in content)
            punctuation = total_chars - letters - digits - spaces

            # Word statistics
            words = content.split()
            word_count = len(words)
            avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0

            # Sentence statistics
            sentences = re.split(r'[.!?]+', content)
            sentence_count = len([s for s in sentences if s.strip()])
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

            # Paragraph statistics
            paragraphs = [p for p in content.split('\n\n') if p.strip()]
            paragraph_count = len(paragraphs)

            return AnalysisResult(
                success=True,
                data={
                    "characters": {
                        "total": total_chars,
                        "letters": letters,
                        "digits": digits,
                        "spaces": spaces,
                        "punctuation": punctuation
                    },
                    "words": {
                        "count": word_count,
                        "average_length": round(avg_word_length, 1)
                    },
                    "sentences": {
                        "count": sentence_count,
                        "average_length": round(avg_sentence_length, 1)
                    },
                    "paragraphs": {
                        "count": paragraph_count
                    },
                    "reading_time_minutes": round(word_count / 200, 1)  # Assuming 200 WPM
                },
                message=f"{word_count} words, {sentence_count} sentences, ~{round(word_count/200, 1)} min read",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                data={},
                message=f"Statistics analysis failed: {str(e)}",
                processing_time=time.time() - start_time,
                plugin_name=self.name
            )

    def analyze_async(self, content: str, progress_callback=None,
                      cancel_event=None, **kwargs) -> AnalysisResult:
        if progress_callback:
            progress_callback(0.3, "Counting characters...")
            progress_callback(0.6, "Analyzing words...")
            progress_callback(0.9, "Calculating statistics...")

        return self.analyze(content, **kwargs)
```

## Troubleshooting

### Plugin Not Discovered

**Issue:** Plugin file created but not showing in UI

**Checklist:**
- [ ] File is in `app/ai_analysis/plugins/` directory
- [ ] Filename ends with `.py`
- [ ] Class inherits from `BaseAnalysisPlugin`
- [ ] `__init__()` calls `super().__init__()`
- [ ] Application has been restarted
- [ ] Check `logs/app.log.*` for errors

### Import Errors

**Issue:** Plugin fails to import

**Solutions:**
- Check for syntax errors: `python -m py_compile app/ai_analysis/plugins/my_plugin.py`
- Verify all imports are available
- Test import in isolation:
  ```python
  python -c "from ai_analysis.plugins.my_plugin import MyPlugin; print('OK')"
  ```

### Performance Issues

**Issue:** Plugin runs slowly

**Solutions:**
- Profile your code:
  ```python
  import cProfile
  cProfile.run('plugin.analyze(content)')
  ```
- Use async for long operations
- Implement caching for repeated analyses
- Break down large operations with progress updates

## Resources

### Documentation
- [AI Analysis System Overview](./AI_ANALYSIS_SYSTEM.md)
- [API Reference](./API_REFERENCE.md)
- [Testing Guide](./TESTING_GUIDE.md)

### Example Plugins
- `app/ai_analysis/plugins/tagging_plugin.py` - AI-powered tagging
- `app/ai_analysis/plugins/summarization_plugin.py` - Text summarization
- `app/ai_analysis/plugins/sentiment_compass_plugin.py` - Sentiment analysis

### Support
- GitHub Issues: Report bugs or request features
- Code Reviews: Submit PR for plugin review

---

**Version:** 3.0.0
**Last Updated:** October 1, 2025
**Maintained By:** Project A.N.C. Team
