# CLAUDE.md - AI Assistant Guide for Project A.N.C.

**Version:** 3.3.0
**Last Updated:** 2025-11-04
**Purpose:** Guide for AI assistants working on Project A.N.C.

## Project Overview

Project A.N.C. (Alice Nexus Core) is a modern AI-powered desktop application built with Python and Flet. It features:

- **Alice**: AI chat assistant powered by Google Gemini or OpenAI
- **Multi-conversation management**: Tab-based conversations with persistence
- **Dynamic plugin system**: Auto-discovering AI analysis plugins
- **State management**: Centralized, reactive state with Observer pattern
- **File management**: Notes, memories, and daily reports (nippo)

### Key Statistics
- **Language:** Python 3.12+
- **Framework:** Flet 0.28+
- **Architecture:** v3.3.0 (Modern architecture with state management)
- **Code Quality:** ~1,300 lines of quality code (500 lines removed in v3.3.0)
- **Plugins:** 3 auto-discovered (tagging, summarization, sentiment_compass)

## Architecture Principles

### 1. Centralized State Management
```python
# Use AppState for all state operations
from app.state_manager import AppState

# Good
app_state.add_file(path, metadata)
app_state.add_conversation_message("user", "Hello")

# Bad - Don't manipulate state directly
self.files[path] = metadata  # ❌ Don't do this
```

### 2. Observer Pattern for Reactivity
```python
# Register observers for reactive UI updates
app_state.add_observer("file_added", on_file_added_callback)
app_state.add_observer("conversation_updated", on_conversation_updated)
```

### 3. Zero-Configuration Plugins
```python
# Plugins are auto-discovered - just inherit from BaseAnalysisPlugin
# No manual registration needed!
class MyPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__(name="my_plugin", description="...", version="1.0.0")
```

### 4. Thread Safety
- Use RLock for all shared state
- AppState and AsyncOperationManager are thread-safe
- All async operations use ThreadPoolExecutor

## Directory Structure

```
project-anc/
├── app/
│   ├── main.py                      # Entry point
│   ├── state_manager.py             # ⭐ Centralized state (416 lines)
│   ├── plugin_manager.py            # ⭐ Dynamic plugin discovery (302 lines)
│   ├── ui_components.py             # ⭐ Reusable UI library (542 lines)
│   ├── ui_redesign.py               # Main chat interface
│   ├── sidebar_tabs.py              # Sidebar tabs (4 tabs: 分析、記憶、日報、設定)
│   ├── alice_chat_manager.py        # Gemini/OpenAI integration
│   ├── async_operations.py          # Async task management
│   ├── logic.py                     # Business logic layer
│   ├── handlers.py                  # Event handlers
│   ├── logger.py                    # Daily rotating logs (7 types)
│   ├── security.py                  # Input validation
│   └── ai_analysis/
│       ├── base_plugin.py           # Plugin interface
│       ├── manager.py               # AI analysis coordinator
│       └── plugins/                 # ⭐ Auto-discovered plugins
│           ├── tagging_plugin.py
│           ├── summarization_plugin.py
│           └── sentiment_compass_plugin.py
├── config/
│   └── config.py                    # Configuration
├── data/
│   ├── notes/                       # User notes
│   │   ├── 0-System-Prompt.md       # Alice system instruction
│   │   └── 0-Memory.md              # Long-term memory
│   ├── chat_logs/                   # Daily chat logs (YYYY-MM-DD.md)
│   ├── conversation_state.json      # Multi-conversation persistence
│   ├── memories/                    # Generated memories
│   ├── nippo/                       # Daily reports
│   └── anc_db.json                  # TinyDB database
├── logs/
│   ├── app.log.*                    # System logs (daily rotation)
│   ├── errors.log.*                 # Error tracking
│   └── dialogs/                     # API call logs
├── docs/                            # ⭐ Comprehensive documentation (9 files)
└── tests/                           # Test suite (pytest)
```

⭐ = Critical files for understanding the project

## Key Design Patterns

### 1. State Management Pattern
```python
# AppState is the single source of truth
class AppState:
    def __init__(self):
        self._lock = threading.RLock()  # Thread-safe
        self._files = {}                 # File state
        self._conversations = {}         # Conversation state
        self._observers = {}             # Observer callbacks

    def add_file(self, path, metadata):
        with self._lock:
            self._files[path] = metadata
            self._notify_observers("file_added", path, metadata)
```

### 2. Plugin Discovery Pattern
```python
# PluginManager uses importlib for dynamic loading
class PluginManager:
    def discover_plugins(self):
        plugins_dir = Path("app/ai_analysis/plugins")
        for file in plugins_dir.glob("*_plugin.py"):
            module = importlib.import_module(f"ai_analysis.plugins.{file.stem}")
            # Auto-discover BaseAnalysisPlugin subclasses
```

### 3. Async Operations Pattern
```python
# All long-running operations should be async
operation_id = async_mgr.run_async_operation(
    task_function,
    progress_callback=update_progress,
    cancel_event=cancel_event
)
```

### 4. Component Reusability Pattern
```python
# Use ui_components.py for all UI elements
from app.ui_components import ProgressButton, ExpandableSection

button = ProgressButton(text="Analyze", on_click=handle_click)
button.show_progress()  # Built-in progress indicator
```

## Common Tasks

### Adding a New Plugin

1. **Create plugin file** in `app/ai_analysis/plugins/`
   ```python
   # app/ai_analysis/plugins/my_plugin.py
   from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
   import time

   class MyPlugin(BaseAnalysisPlugin):
       def __init__(self):
           super().__init__(
               name="my_plugin",
               description="Does something useful",
               version="1.0.0"
           )
           self.requires_ollama = False  # Set True if using Ollama

       def analyze(self, content: str, **kwargs) -> AnalysisResult:
           start_time = time.time()
           try:
               # Your analysis logic here
               result_data = {"key": "value"}

               return AnalysisResult(
                   success=True,
                   data=result_data,
                   message="Analysis completed",
                   processing_time=time.time() - start_time,
                   plugin_name=self.name
               )
           except Exception as e:
               return AnalysisResult(
                   success=False,
                   data={},
                   message=f"Failed: {str(e)}",
                   processing_time=time.time() - start_time,
                   plugin_name=self.name
               )

       def analyze_async(self, content: str, progress_callback=None,
                         cancel_event=None, **kwargs) -> AnalysisResult:
           if progress_callback:
               progress_callback(0.5, "Processing...")
           return self.analyze(content, **kwargs)
   ```

2. **Restart application** - Plugin auto-discovered!

3. **No registration needed** - PluginManager finds it automatically

### Adding a New UI Component

1. **Add to `ui_components.py`**
   ```python
   class MyComponent:
       def __init__(self, **kwargs):
           self.container = ft.Container(
               # Your UI structure
           )

       def build(self):
           return self.container
   ```

2. **Use in other files**
   ```python
   from app.ui_components import MyComponent
   component = MyComponent()
   ```

### Adding State to AppState

1. **Add state variable** in `__init__`
   ```python
   self._my_state = {}
   ```

2. **Create getter/setter**
   ```python
   def get_my_state(self):
       with self._lock:
           return self._my_state.copy()

   def update_my_state(self, key, value):
       with self._lock:
           self._my_state[key] = value
           self._notify_observers("my_state_updated", key, value)
   ```

3. **Add observer event type** to docstring

### Modifying Alice's Behavior

1. **Edit system prompt**: `data/notes/0-System-Prompt.md`
2. **Edit long-term memory**: `data/notes/0-Memory.md`
3. **Change model**: `config/config.py` → `GEMINI_MODEL` or `OPENAI_MODEL`
4. **Switch provider**: `.env` → `CHAT_API_PROVIDER=google` or `openai`

## Important Conventions

### Code Style
- **Type hints**: Use them everywhere
- **Docstrings**: All public methods need docstrings
- **Error handling**: Always return AnalysisResult or appropriate error
- **Thread safety**: Use locks for shared state
- **Async operations**: Use AsyncOperationManager for long tasks

### File Naming
- **Plugins**: `*_plugin.py` (e.g., `tagging_plugin.py`)
- **Tests**: `test_*.py` (e.g., `test_tagging_plugin.py`)
- **UI files**: `ui_*.py` or descriptive names
- **Logs**: Daily rotation with timestamp

### Git Commit Messages
```
feat: Add new feature
fix: Fix bug
refactor: Refactor code
docs: Update documentation
test: Add tests
chore: Maintenance tasks
```

### API Integration
- **Gemini**: Use `google.generativeai` library
- **OpenAI**: Use `openai` library
- **Ollama**: Use `ollama` library for local AI
- **API keys**: Always from environment variables, never hardcoded

## Testing Guidelines

### Unit Tests
```python
# tests/test_my_plugin.py
import pytest
from ai_analysis.plugins.my_plugin import MyPlugin

class TestMyPlugin:
    @pytest.fixture
    def plugin(self):
        return MyPlugin()

    def test_basic_analysis(self, plugin):
        result = plugin.analyze("test content")
        assert result.success
        assert "key" in result.data

    def test_error_handling(self, plugin):
        result = plugin.analyze(None)
        assert not result.success
```

### Running Tests
```bash
# All tests
pytest

# Specific file
pytest tests/test_my_plugin.py

# With coverage
pytest --cov=app --cov-report=html

# Fast tests only
pytest -m "not slow"
```

## Common Pitfalls

### ❌ DON'T
```python
# Don't manipulate state directly
self.files[path] = metadata

# Don't register plugins manually
ai_manager.register_plugin(MyPlugin())

# Don't block UI thread
result = long_running_task()  # Freezes UI!

# Don't hardcode API keys
GEMINI_API_KEY = "AIza..."

# Don't skip error handling
result = plugin.analyze(content)  # No try/except!
```

### ✅ DO
```python
# Use AppState
app_state.add_file(path, metadata)

# Just create plugin file - auto-discovered
# app/ai_analysis/plugins/my_plugin.py

# Use async operations
operation_id = async_mgr.run_async_operation(long_running_task)

# Use environment variables
api_key = os.getenv("GEMINI_API_KEY")

# Always handle errors
try:
    result = plugin.analyze(content)
except Exception as e:
    return AnalysisResult(success=False, message=str(e), ...)
```

## Debugging

### Check Logs
```bash
# System logs
tail -f logs/app.log.*

# Errors
tail -f logs/errors.log.*

# Alice chat
tail -f logs/alice_chat.log.*

# API calls
ls -lt logs/dialogs/ | head -5
```

### Plugin Discovery Issues
```bash
# Check plugins found
grep "PluginManager" logs/app.log.*

# Test plugin import
python -c "from ai_analysis.plugins.my_plugin import MyPlugin; print('OK')"

# Check for syntax errors
python -m py_compile app/ai_analysis/plugins/my_plugin.py
```

### State Issues
```python
# Debug state
python -c "
from app.state_manager import AppState
state = AppState()
print(state.get_all_files())
print(state.get_conversation_history())
"
```

## Configuration

### Environment Variables (.env)
```bash
# API Provider Selection
CHAT_API_PROVIDER=google        # or "openai"

# API Keys
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Alice Chat Configuration (v3.1.1+)
ALICE_HISTORY_CHAR_LIMIT=4000   # Conversation history character limit

# Compass API Configuration (v3.1.1+)
COMPASS_API_BASE_URL=http://127.0.0.1:8000    # Base URL (without endpoint path)
COMPASS_API_ENDPOINT=search                    # Endpoint type (search/graph_search)
COMPASS_API_TARGET=content                     # Target field for search
COMPASS_API_LIMIT=5                            # Number of initial results to fetch
COMPASS_API_RELATED_LIMIT=3                    # Number of related items (graph_search only)
COMPASS_API_COMPRESS=False                     # Enable/disable compression
COMPASS_API_SEARCH_MODE=latest                 # Search mode (latest/history)

# Models
OLLAMA_MODEL=gemma3:4b
GEMINI_MODEL=gemini-2.5-pro
OPENAI_MODEL=gpt-4-turbo

# Optional
LOG_LEVEL=INFO
MAX_WORKERS=4
DEBUG=False
```

### config/config.py
```python
# Paths
DATA_DIR = Path("data")
NOTES_DIR = DATA_DIR / "notes"
LOGS_DIR = Path("logs")

# AI Settings
MAX_HISTORY_CHARS = 4000
MAX_MEMORY_CHARS = 2000

# Models
OLLAMA_MODEL = "gemma3:4b"
GEMINI_MODEL = "gemini-2.5-pro"

# Compass API Configuration
COMPASS_API_BASE_URL = "http://127.0.0.1:8000"
COMPASS_API_ENDPOINT = "search"  # or "graph_search"
COMPASS_API_CONFIG = {
    "target": "content",           # "summary" or "content"
    "limit": 5,                    # Number of initial results
    "related_limit": 3,            # Number of related items (graph_search only)
    "compress": False,             # Enable/disable AI compression
    "search_mode": "latest",       # "latest" or "history"
    "endpoint": "search"           # "search" or "graph_search"
}
```

## External Dependencies

### Required Services
1. **Ollama** (for AI analysis plugins)
   - Install: https://ollama.com/download
   - Pull model: `ollama pull gemma3:4b`
   - Start: `ollama serve`

2. **Google Gemini API** or **OpenAI API** (for Alice chat)
   - Gemini: https://aistudio.google.com/app/apikey
   - OpenAI: https://platform.openai.com/api-keys

### Python Packages
```txt
flet>=0.28.0                # UI framework
tinydb>=4.8.0               # Database
ollama>=0.1.7               # Local AI
google-generativeai>=1.38.0 # Gemini API
openai>=1.0.0               # OpenAI API
python-dotenv>=1.0.0        # Environment variables
```

## Version History & Migration

### v3.3.0 (Current) - Settings UI Fix & Code Cleanup
- **Fixed**: Settings UI now preserves all .env variables when saving
- **Removed**: File and Editor tabs from Auxiliary Tools (500 lines removed)
- **Improved**: .env file updating with backup and rollback functionality
- Auxiliary Tools now has 4 tabs: Analysis, Memory, Nippo, Settings
- **Breaking change**: Removed file browsing and editing features from UI
- **Non-breaking** for core functionality (Alice chat, memory, nippo, analysis)

### v3.1.1 - Tag Editing & Configuration Enhancement
- Tag editing UI with full CRUD operations
- Text input fields for settings (replaced sliders)
- Complete .env file migration for all settings
- Environment variable reading in config.py
- **Non-breaking update** from v3.1.0

### v3.1.0 - Multi-Conversation Management
- Multi-conversation tabs with persistence
- Markdown rendering for AI responses
- Conversation state persistence (`data/conversation_state.json`)
- **Non-breaking update** from v3.0.0

### v3.0.0 - Modern Architecture
- State management system (`state_manager.py`)
- Dynamic plugin discovery (`plugin_manager.py`)
- UI component library (`ui_components.py`)
- **Breaking changes** from v2.0.0:
  - Plugin registration: Now automatic
  - State access: Use AppState methods
  - UI components: Import from ui_components

### Migrating Code
```python
# v2.0 → v3.0 Migration

# OLD (v2.0)
self.ai_manager.register_plugin(TaggingPlugin())
self.files[path] = metadata

# NEW (v3.0+)
# Plugins auto-registered - no code needed
app_state.add_file(path, metadata)
```

## Performance Considerations

- **Startup time**: ~2-3 seconds
- **Plugin discovery**: <100ms (3 plugins)
- **Memory usage**: ~150MB typical (reduced from ~200MB in v3.1.1)
- **Async operations**: Use for files >1MB or analysis >1s
- **Database**: TinyDB is fast for <10,000 records

## Security Notes

1. **Never commit**:
   - `.env` file (API keys)
   - `data/conversation_state.json` (if contains sensitive data)
   - Any file with API keys or credentials

2. **Input validation**:
   - Use `security.py` functions
   - Sanitize filenames: `sanitize_filename()`
   - Validate paths: No path traversal

3. **API keys**:
   - Always from environment
   - Never log API keys
   - Use `.env.example` for templates

## Documentation

Comprehensive docs in `/docs`:
- `SYSTEM_OVERVIEW.md` - Architecture overview
- `ALICE_CHAT_SETUP.md` - Alice setup guide
- `AI_ANALYSIS_SYSTEM.md` - Plugin system docs
- `PLUGIN_DEVELOPMENT_GUIDE.md` - Plugin creation guide
- `API_REFERENCE.md` - Complete API reference
- `TESTING_GUIDE.md` - Testing practices
- `DEPLOYMENT.md` - Deployment guide
- `TROUBLESHOOTING.md` - Common issues
- `CHANGELOG.md` - Version history

## Quick Reference

### Most Important Files
1. `app/state_manager.py` - Centralized state (read first!)
2. `app/plugin_manager.py` - Plugin discovery system
3. `app/ui_components.py` - Reusable UI components
4. `app/alice_chat_manager.py` - AI chat integration
5. `config/config.py` - Configuration

### Most Common Operations
```python
# Add file to state
app_state.add_file(path, {"name": "file.txt", "type": "text"})

# Add conversation message
app_state.add_conversation_message("user", "Hello")

# Run AI analysis
result = app_logic.run_ai_analysis(content, "tagging")

# Run async operation
op_id = async_mgr.run_async_operation(task_func)

# Get available plugins
plugins = plugin_manager.get_available_plugins()
```

### Emergency Commands
```bash
# Reset database
rm data/anc_db.json

# Clear conversation state
rm data/conversation_state.json

# Clear logs
rm -rf logs/*

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Run tests
pytest -v
```

## When Making Changes

### Before Committing
- [ ] Run tests: `pytest`
- [ ] Check code style: `black app/` (if using black)
- [ ] Update CHANGELOG.md if user-facing change
- [ ] Update documentation if API changed
- [ ] Test plugin discovery still works
- [ ] Ensure no sensitive data in commit

### Pull Request Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or documented in CHANGELOG)
- [ ] Code follows project conventions
- [ ] Added tests for new functionality

---

**Last Updated:** 2025-11-04
**Project Version:** v3.3.0
**For Questions:** See `docs/TROUBLESHOOTING.md` or create GitHub issue
