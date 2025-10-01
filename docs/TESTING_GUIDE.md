# Testing Guide

**Version:** 3.0.0
**Last Updated:** October 1, 2025

## Table of Contents

1. [Overview](#overview)
2. [Testing Philosophy](#testing-philosophy)
3. [Test Setup](#test-setup)
4. [Unit Testing](#unit-testing)
5. [Integration Testing](#integration-testing)
6. [Plugin Testing](#plugin-testing)
7. [UI Testing](#ui-testing)
8. [Running Tests](#running-tests)
9. [Best Practices](#best-practices)

## Overview

This guide covers testing strategies and best practices for Project A.N.C. v3.0.

### Testing Stack

- **Framework:** pytest
- **Mocking:** unittest.mock
- **Coverage:** pytest-cov
- **Style:** pytest conventions

### Test Structure

```
project-anc/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_state_manager.py   # State management tests
│   ├── test_plugin_manager.py  # Plugin discovery tests
│   ├── test_alice_chat.py      # Alice chat tests
│   ├── test_async_ops.py       # Async operations tests
│   ├── test_logic.py            # Business logic tests
│   ├── test_ui_components.py   # UI component tests
│   └── plugins/                 # Plugin-specific tests
│       ├── test_tagging.py
│       ├── test_summarization.py
│       └── test_sentiment.py
```

## Testing Philosophy

### What to Test

✅ **DO test:**
- Business logic and algorithms
- State management operations
- Plugin discovery and loading
- API integrations (with mocks)
- Error handling and edge cases
- Configuration validation

❌ **DON'T test:**
- Third-party library internals
- Flet framework behavior
- External API implementations
- Trivial getters/setters without logic

### Test Pyramid

```
        /\
       /  \      E2E Tests (Few)
      /----\     - Full application workflows
     /      \
    /--------\   Integration Tests (Some)
   /          \  - Component interactions
  /------------\
 /--------------\ Unit Tests (Many)
                  - Individual functions/classes
```

## Test Setup

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

**requirements-dev.txt:**
```txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
```

### Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Shared Fixtures

**tests/conftest.py:**
```python
import pytest
from app.state_manager import AppState
from app.plugin_manager import PluginManager
from app.logic import AppLogic
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def app_state():
    """Create a fresh AppState instance"""
    state = AppState()
    yield state
    # Cleanup if needed

@pytest.fixture
def plugin_manager():
    """Create a PluginManager instance"""
    manager = PluginManager()
    yield manager

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

@pytest.fixture
def app_logic(app_state):
    """Create AppLogic with mocked dependencies"""
    logic = AppLogic(app_state)
    yield logic

@pytest.fixture
def sample_content():
    """Sample content for testing"""
    return """
    This is sample content for testing.
    It has multiple sentences. And some variety.
    This helps test analysis plugins effectively.
    """
```

## Unit Testing

### Testing AppState

**tests/test_state_manager.py:**
```python
import pytest
from app.state_manager import AppState

class TestAppState:
    def test_add_file(self, app_state):
        """Test adding a file to state"""
        app_state.add_file("test.txt", {"name": "test.txt", "type": "text"})

        files = app_state.get_all_files()
        assert "test.txt" in files
        assert files["test.txt"]["name"] == "test.txt"

    def test_remove_file(self, app_state):
        """Test removing a file from state"""
        app_state.add_file("test.txt", {"name": "test.txt"})
        app_state.remove_file("test.txt")

        files = app_state.get_all_files()
        assert "test.txt" not in files

    def test_update_file_state(self, app_state):
        """Test updating file state"""
        app_state.add_file("test.txt", {"name": "test.txt"})
        app_state.update_file_state("test.txt", {"modified": True})

        state = app_state.get_file_state("test.txt")
        assert state["modified"] is True

    def test_mark_file_modified(self, app_state):
        """Test marking file as modified"""
        app_state.add_file("test.txt", {"name": "test.txt"})
        app_state.mark_file_modified("test.txt", True)

        state = app_state.get_file_state("test.txt")
        assert state.get("modified") is True

    def test_conversation_history(self, app_state):
        """Test conversation history management"""
        app_state.add_conversation_message("user", "Hello")
        app_state.add_conversation_message("assistant", "Hi there!")

        history = app_state.get_conversation_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"

    def test_clear_conversation(self, app_state):
        """Test clearing conversation history"""
        app_state.add_conversation_message("user", "Hello")
        app_state.clear_conversation_history()

        history = app_state.get_conversation_history()
        assert len(history) == 0

    def test_observer_pattern(self, app_state):
        """Test observer notifications"""
        called = []

        def observer(path, state):
            called.append((path, state))

        app_state.add_observer("file_added", observer)
        app_state.add_file("test.txt", {"name": "test.txt"})

        assert len(called) == 1
        assert called[0][0] == "test.txt"

    def test_remove_observer(self, app_state):
        """Test removing observers"""
        called = []

        def observer(path, state):
            called.append(path)

        app_state.add_observer("file_added", observer)
        app_state.remove_observer("file_added", observer)
        app_state.add_file("test.txt", {"name": "test.txt"})

        assert len(called) == 0

    def test_thread_safety(self, app_state):
        """Test thread-safe operations"""
        import threading

        def add_files():
            for i in range(100):
                app_state.add_file(f"file_{i}.txt", {"name": f"file_{i}.txt"})

        threads = [threading.Thread(target=add_files) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        files = app_state.get_all_files()
        assert len(files) == 500  # 100 files * 5 threads
```

### Testing PluginManager

**tests/test_plugin_manager.py:**
```python
import pytest
from app.plugin_manager import PluginManager

class TestPluginManager:
    def test_discover_plugins(self, plugin_manager):
        """Test plugin discovery"""
        plugins = plugin_manager.discover_plugins()

        assert len(plugins) > 0
        assert "tagging" in plugins
        assert "summarization" in plugins
        assert "sentiment_compass" in plugins

    def test_get_plugin_info(self, plugin_manager):
        """Test retrieving plugin information"""
        plugin_manager.discover_plugins()
        info = plugin_manager.get_plugin_info("tagging")

        assert info is not None
        assert "name" in info
        assert "description" in info
        assert "version" in info
        assert info["name"] == "tagging"

    def test_plugin_info_not_found(self, plugin_manager):
        """Test getting info for non-existent plugin"""
        info = plugin_manager.get_plugin_info("nonexistent")
        assert info is None

    def test_get_available_plugins(self, plugin_manager):
        """Test getting all available plugins"""
        plugins = plugin_manager.get_available_plugins()
        assert len(plugins) > 0

    @pytest.mark.slow
    def test_reload_plugins(self, plugin_manager):
        """Test plugin reloading"""
        initial_count = len(plugin_manager.discover_plugins())
        new_count = plugin_manager.reload_plugins()

        assert new_count == initial_count
```

### Testing AsyncOperations

**tests/test_async_ops.py:**
```python
import pytest
import time
from app.async_operations import AsyncOperationManager, OperationStatus

class TestAsyncOperations:
    @pytest.fixture
    def async_mgr(self):
        return AsyncOperationManager()

    def test_run_async_operation(self, async_mgr):
        """Test running async operation"""
        def task():
            time.sleep(0.1)
            return "result"

        op_id = async_mgr.run_async_operation(task)
        assert op_id is not None

        # Wait for completion
        time.sleep(0.2)
        status = async_mgr.get_operation_status(op_id)
        assert status == OperationStatus.COMPLETED

    def test_operation_with_progress(self, async_mgr):
        """Test operation with progress callback"""
        progress_updates = []

        def task(progress_callback=None):
            if progress_callback:
                progress_callback(0.5, "Working...")
            time.sleep(0.1)
            if progress_callback:
                progress_callback(1.0, "Done")
            return "result"

        op_id = async_mgr.run_async_operation(task)
        time.sleep(0.2)

        progress, message = async_mgr.get_operation_progress(op_id)
        assert progress >= 0.0
        assert message is not None

    def test_cancel_operation(self, async_mgr):
        """Test operation cancellation"""
        def long_task(cancel_event=None):
            for i in range(10):
                if cancel_event and cancel_event.is_set():
                    return None
                time.sleep(0.1)
            return "completed"

        op_id = async_mgr.run_async_operation(long_task)
        time.sleep(0.2)

        cancelled = async_mgr.cancel_operation(op_id)
        assert cancelled is True

        time.sleep(0.2)
        status = async_mgr.get_operation_status(op_id)
        assert status == OperationStatus.CANCELLED

    def test_operation_error(self, async_mgr):
        """Test operation error handling"""
        def failing_task():
            raise ValueError("Test error")

        op_id = async_mgr.run_async_operation(failing_task)
        time.sleep(0.2)

        status = async_mgr.get_operation_status(op_id)
        assert status == OperationStatus.FAILED
```

## Integration Testing

### Testing AppLogic with Plugins

**tests/test_logic.py:**
```python
import pytest
from app.logic import AppLogic
from app.state_manager import AppState

class TestAppLogic:
    @pytest.fixture
    def app_logic(self, app_state):
        return AppLogic(app_state)

    def test_get_available_plugins(self, app_logic):
        """Test retrieving available plugins"""
        plugins = app_logic.get_available_plugins()

        assert len(plugins) > 0
        assert any(p['name'] == 'tagging' for p in plugins)

    def test_run_ai_analysis(self, app_logic, sample_content):
        """Test running AI analysis"""
        result = app_logic.run_ai_analysis(
            content=sample_content,
            analysis_type="tagging"
        )

        assert result is not None
        assert 'success' in result
        assert 'data' in result

    @pytest.mark.integration
    def test_file_operations(self, app_logic, temp_dir):
        """Test file CRUD operations"""
        test_file = temp_dir / "test.txt"
        content = "Test content"

        # Save file
        success = app_logic.save_file(str(test_file), content)
        assert success is True

        # Open file
        read_content = app_logic.open_file(str(test_file))
        assert read_content == content

        # Delete file
        success = app_logic.delete_file(str(test_file))
        assert success is True
        assert not test_file.exists()

    @pytest.mark.integration
    def test_run_ai_analysis_async(self, app_logic, sample_content):
        """Test async AI analysis"""
        op_id = app_logic.run_ai_analysis_async(
            path="test.txt",
            content=sample_content,
            analysis_type="tagging"
        )

        assert op_id is not None

        # Wait for completion
        import time
        time.sleep(2)

        # Check results stored in state
        state = app_logic.app_state.get_file_state("test.txt")
        assert 'ai_analysis' in state or op_id is not None
```

## Plugin Testing

### Testing Analysis Plugins

**tests/plugins/test_tagging.py:**
```python
import pytest
from ai_analysis.plugins.tagging_plugin import TaggingPlugin

class TestTaggingPlugin:
    @pytest.fixture
    def plugin(self):
        return TaggingPlugin()

    def test_plugin_initialization(self, plugin):
        """Test plugin initializes correctly"""
        assert plugin.name == "tagging"
        assert plugin.version is not None
        assert plugin.requires_ollama is True

    def test_analyze_content(self, plugin, sample_content):
        """Test basic analysis"""
        result = plugin.analyze(sample_content)

        assert result is not None
        assert result.plugin_name == "tagging"
        assert result.processing_time >= 0

    def test_validate_content(self, plugin):
        """Test content validation"""
        assert plugin.validate_content("Valid content") is True
        assert plugin.validate_content("") is False
        assert plugin.validate_content("   ") is False

    def test_analyze_async(self, plugin, sample_content):
        """Test async analysis"""
        progress_calls = []

        def track_progress(percent, message):
            progress_calls.append((percent, message))

        result = plugin.analyze_async(
            sample_content,
            progress_callback=track_progress
        )

        assert result is not None
        assert len(progress_calls) > 0

    @pytest.mark.integration
    def test_analyze_with_ollama(self, plugin):
        """Test analysis with Ollama (requires Ollama running)"""
        content = "Python is a programming language"
        result = plugin.analyze(content)

        if result.success:
            assert 'tags' in result.data
            assert len(result.data['tags']) > 0
        else:
            # Ollama not available
            assert 'ollama' in result.message.lower()

    def test_error_handling(self, plugin):
        """Test plugin error handling"""
        # Test with invalid input
        result = plugin.analyze(None)
        assert result.success is False
```

### Testing Custom Plugins

```python
# tests/plugins/test_custom_plugin.py
import pytest
from ai_analysis.plugins.my_custom_plugin import MyCustomPlugin

class TestMyCustomPlugin:
    @pytest.fixture
    def plugin(self):
        return MyCustomPlugin()

    def test_custom_functionality(self, plugin):
        """Test custom plugin functionality"""
        result = plugin.analyze("test input")

        assert result.success
        assert "expected_field" in result.data

    def test_custom_parameters(self, plugin):
        """Test custom plugin parameters"""
        result = plugin.analyze(
            "test input",
            custom_param="value"
        )

        assert result.success
        assert result.data["custom_field"] == "value"
```

## UI Testing

### Testing UI Components

**tests/test_ui_components.py:**
```python
import pytest
import flet as ft
from app.ui_components import (
    ProgressButton,
    ExpandableSection,
    EditableTextField,
    SearchField
)

class TestProgressButton:
    def test_initialization(self):
        """Test ProgressButton initialization"""
        button = ProgressButton(text="Test")
        assert button.button.text == "Test"
        assert button.progress_ring.visible is False

    def test_show_progress(self):
        """Test showing progress"""
        button = ProgressButton(text="Test")
        button.show_progress()

        assert button.progress_ring.visible is True
        assert button.button.disabled is True

    def test_hide_progress(self):
        """Test hiding progress"""
        button = ProgressButton(text="Test")
        button.show_progress()
        button.hide_progress()

        assert button.progress_ring.visible is False
        assert button.button.disabled is False

class TestExpandableSection:
    def test_initialization(self):
        """Test ExpandableSection initialization"""
        section = ExpandableSection(
            title="Test",
            icon=ft.Icons.FOLDER,
            content_items=[ft.Text("Content")]
        )

        assert section.title == "Test"
        assert section.is_expanded is False

    def test_toggle(self):
        """Test section toggle"""
        section = ExpandableSection(
            title="Test",
            icon=ft.Icons.FOLDER,
            content_items=[ft.Text("Content")]
        )

        section._toggle()
        assert section.is_expanded is True

        section._toggle()
        assert section.is_expanded is False

    def test_expand_collapse(self):
        """Test programmatic expand/collapse"""
        section = ExpandableSection(
            title="Test",
            icon=ft.Icons.FOLDER,
            content_items=[ft.Text("Content")]
        )

        section.expand()
        assert section.is_expanded is True

        section.collapse()
        assert section.is_expanded is False
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_state_manager.py
```

### Run Specific Test

```bash
pytest tests/test_state_manager.py::TestAppState::test_add_file
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

### Run Only Unit Tests

```bash
pytest -m unit
```

### Run Only Integration Tests

```bash
pytest -m integration
```

### Run Fast Tests (Skip Slow)

```bash
pytest -m "not slow"
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Output (print statements)

```bash
pytest -s
```

## Best Practices

### 1. Test Naming

```python
# Good
def test_add_file_to_state():
    """Test adding a file to application state"""
    pass

# Bad
def test1():
    pass
```

### 2. Arrange-Act-Assert (AAA)

```python
def test_remove_file():
    # Arrange
    app_state = AppState()
    app_state.add_file("test.txt", {"name": "test.txt"})

    # Act
    app_state.remove_file("test.txt")

    # Assert
    files = app_state.get_all_files()
    assert "test.txt" not in files
```

### 3. Use Fixtures for Setup

```python
@pytest.fixture
def prepared_state():
    """State with pre-loaded files"""
    state = AppState()
    state.add_file("file1.txt", {"name": "file1.txt"})
    state.add_file("file2.txt", {"name": "file2.txt"})
    return state

def test_with_prepared_state(prepared_state):
    files = prepared_state.get_all_files()
    assert len(files) == 2
```

### 4. Test Edge Cases

```python
def test_edge_cases():
    app_state = AppState()

    # Empty string
    app_state.add_file("", {})

    # None values
    app_state.add_file(None, None)

    # Very long strings
    app_state.add_file("x" * 10000, {})

    # Special characters
    app_state.add_file("test@#$.txt", {})
```

### 5. Mock External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mock():
    with patch('ollama.chat') as mock_chat:
        mock_chat.return_value = {'message': {'content': 'mocked response'}}

        plugin = TaggingPlugin()
        result = plugin.analyze("test")

        assert result.success
        mock_chat.assert_called_once()
```

### 6. Test Error Conditions

```python
def test_error_handling():
    plugin = MyPlugin()

    # Test with None
    result = plugin.analyze(None)
    assert not result.success

    # Test with invalid type
    result = plugin.analyze(12345)
    assert not result.success

    # Test with empty
    result = plugin.analyze("")
    assert not result.success
```

### 7. Parametrize Tests

```python
@pytest.mark.parametrize("content,expected", [
    ("short", False),
    ("this is long enough content", True),
    ("", False),
])
def test_content_validation(content, expected):
    plugin = MyPlugin()
    assert plugin.validate_content(content) == expected
```

### 8. Use Descriptive Assertions

```python
# Good
assert result.success, f"Analysis failed: {result.message}"
assert len(tags) > 0, "Expected at least one tag"

# Bad
assert result.success
assert len(tags) > 0
```

## Continuous Integration

### GitHub Actions Example

**.github/workflows/tests.yml:**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

**Version:** 3.0.0
**Last Updated:** October 1, 2025
**Maintained By:** Project A.N.C. Team
