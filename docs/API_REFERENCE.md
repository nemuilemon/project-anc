# API Reference

**Version:** 3.0.0
**Last Updated:** October 1, 2025

## Table of Contents

1. [AppState](#appstate)
2. [PluginManager](#pluginmanager)
3. [AliceChatManager](#alicechatmanager)
4. [AsyncOperationManager](#asyncoperationmanager)
5. [AppLogic](#applogic)
6. [BaseAnalysisPlugin](#baseanalysisplugin)
7. [AIAnalysisManager](#aianalysismanager)
8. [UI Components](#ui-components)

---

## AppState

**File:** `app/state_manager.py`

Centralized application state management with Observer pattern for reactive UI updates.

### Constructor

```python
AppState()
```

Creates a new application state instance with thread-safe operations.

### File State Methods

#### `add_file(path: str, metadata: dict) -> None`
Add a file to the state.

**Parameters:**
- `path` (str): File path
- `metadata` (dict): File metadata (name, type, size, etc.)

**Example:**
```python
app_state.add_file("notes/test.txt", {
    "name": "test.txt",
    "type": "text",
    "size": 1024
})
```

#### `remove_file(path: str) -> None`
Remove a file from the state.

#### `update_file_state(path: str, updates: dict) -> None`
Update file state with partial updates.

**Example:**
```python
app_state.update_file_state("notes/test.txt", {
    "modified": True,
    "tags": ["important", "work"]
})
```

#### `get_file_state(path: str) -> dict`
Get current state for a file.

**Returns:** File state dictionary or empty dict if not found.

#### `get_all_files() -> dict`
Get all files in state.

**Returns:** Dictionary mapping file paths to state.

#### `mark_file_modified(path: str, modified: bool = True) -> None`
Mark file as modified/unmodified.

#### `set_active_file(path: str) -> None`
Set the currently active file.

#### `get_active_file() -> Optional[str]`
Get the currently active file path.

### Conversation State Methods

#### `add_conversation_message(role: str, content: str) -> None`
Add a message to the conversation history.

**Parameters:**
- `role` (str): "user" or "assistant"
- `content` (str): Message content

**Example:**
```python
app_state.add_conversation_message("user", "Hello Alice")
app_state.add_conversation_message("assistant", "Hello! How can I help?")
```

#### `get_conversation_history() -> list`
Get all conversation messages.

**Returns:** List of `{"role": str, "content": str, "timestamp": float}` dicts.

#### `clear_conversation_history() -> None`
Clear all conversation history.

### Observer Pattern

#### `add_observer(event_type: str, callback: callable) -> None`
Register an observer for state changes.

**Parameters:**
- `event_type` (str): Event type to observe
  - `"file_added"`
  - `"file_removed"`
  - `"file_updated"`
  - `"file_modified"`
  - `"conversation_updated"`
  - `"ui_updated"`
- `callback` (callable): Function to call on event

**Example:**
```python
def on_file_added(path, state):
    print(f"File added: {path}")

app_state.add_observer("file_added", on_file_added)
```

#### `remove_observer(event_type: str, callback: callable) -> None`
Unregister an observer.

---

## PluginManager

**File:** `app/plugin_manager.py`

Dynamic plugin discovery and loading system.

### Constructor

```python
PluginManager()
```

Creates a plugin manager that scans `app/ai_analysis/plugins/` for plugins.

### Methods

#### `discover_plugins() -> Dict[str, Type[BaseAnalysisPlugin]]`
Discover all plugins in plugins directory.

**Returns:** Dictionary mapping plugin names to plugin classes.

**Example:**
```python
plugins = plugin_manager.discover_plugins()
# {'tagging': TaggingPlugin, 'summarization': SummarizationPlugin, ...}
```

#### `get_available_plugins() -> Dict[str, Type[BaseAnalysisPlugin]]`
Get all discovered plugins.

**Returns:** Same as `discover_plugins()`.

#### `get_plugin_info(plugin_name: str) -> Dict[str, Any]`
Get detailed information about a specific plugin.

**Returns:**
```python
{
    'name': 'tagging',
    'description': 'Extract tags from content',
    'version': '1.0.0',
    'file': 'tagging_plugin.py',
    'requires_ollama': True
}
```

#### `reload_plugins() -> int`
Reload all plugins (for future hot-reload support).

**Returns:** Number of plugins discovered.

---

## AliceChatManager

**File:** `app/alice_chat_manager.py`

Manages Alice AI chat conversations with Google Gemini.

### Constructor

```python
AliceChatManager(app_state: AppState)
```

**Parameters:**
- `app_state` (AppState): Application state instance

### Methods

#### `send_message(user_message: str) -> str`
Send a message to Alice and get response.

**Parameters:**
- `user_message` (str): User's message

**Returns:** Alice's response text

**Raises:** `Exception` if API call fails

**Example:**
```python
response = alice_chat_manager.send_message("Hello Alice")
print(response)  # "Hello! How can I help you today?"
```

#### `load_system_instruction() -> str`
Load system instruction from `data/notes/0-System-Prompt.md`.

**Returns:** System instruction text or default if file not found.

#### `load_long_term_memory() -> str`
Load long-term memory from `data/notes/0-Memory.md`.

**Returns:** Memory text or empty string if file not found.

#### `load_todays_chat_log() -> str`
Load today's chat log from `data/chat_logs/YYYY-MM-DD.md`.

**Returns:** Today's chat history or empty string.

#### `save_to_daily_log(user_message: str, assistant_response: str) -> None`
Save conversation to daily log file.

---

## AsyncOperationManager

**File:** `app/async_operations.py`

Manages asynchronous operations with progress tracking and cancellation.

### Constructor

```python
AsyncOperationManager()
```

### Methods

#### `run_async_operation(operation_func: callable, *args, **kwargs) -> str`
Execute an operation asynchronously with tracking.

**Parameters:**
- `operation_func` (callable): Function to execute
- `*args`, `**kwargs`: Arguments to pass to function

**Returns:** Operation ID (string)

**Example:**
```python
def long_task(data, progress_callback=None):
    # Long-running operation
    if progress_callback:
        progress_callback(0.5, "Processing...")
    return result

op_id = async_mgr.run_async_operation(long_task, data="test")
```

#### `get_operation_status(operation_id: str) -> OperationStatus`
Get current status of an operation.

**Returns:** `OperationStatus` enum value:
- `PENDING`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

#### `cancel_operation(operation_id: str) -> bool`
Cancel a running operation.

**Returns:** `True` if cancellation initiated, `False` otherwise.

#### `get_operation_progress(operation_id: str) -> Tuple[float, str]`
Get operation progress.

**Returns:** Tuple of (progress_percent, status_message)

**Example:**
```python
progress, message = async_mgr.get_operation_progress(op_id)
print(f"{progress*100:.0f}%: {message}")
```

---

## AppLogic

**File:** `app/logic.py`

Business logic layer for file operations and AI analysis.

### Constructor

```python
AppLogic(app_state: AppState)
```

### File Operations

#### `list_files(category: str = "notes") -> list`
List all files in a category.

**Parameters:**
- `category` (str): File category ("notes", "memories", "nippo")

**Returns:** List of file metadata dictionaries.

#### `open_file(path: str) -> str`
Open and read a file.

**Returns:** File content as string.

**Raises:** `FileNotFoundError` if file doesn't exist.

#### `save_file(path: str, content: str) -> bool`
Save content to a file.

**Returns:** `True` on success, `False` on failure.

#### `delete_file(path: str) -> bool`
Delete a file.

**Returns:** `True` on success, `False` on failure.

### AI Analysis

#### `run_ai_analysis(content: str, analysis_type: str, **kwargs) -> dict`
Run AI analysis on content.

**Parameters:**
- `content` (str): Content to analyze
- `analysis_type` (str): Plugin name ("tagging", "summarization", etc.)
- `**kwargs`: Plugin-specific parameters

**Returns:** Analysis result dictionary:
```python
{
    'success': True,
    'data': {...},
    'message': 'Analysis completed',
    'processing_time': 1.23,
    'plugin_name': 'tagging'
}
```

**Example:**
```python
result = app_logic.run_ai_analysis(
    content="Sample text",
    analysis_type="summarization",
    summary_type="brief",
    max_sentences=3
)
```

#### `get_available_plugins() -> List[Dict[str, Any]]`
Get list of all available AI analysis plugins.

**Returns:** List of plugin metadata dictionaries.

#### `run_ai_analysis_async(path: str, content: str, analysis_type: str, **kwargs) -> str`
Run async AI analysis and store results.

**Returns:** Operation ID.

---

## BaseAnalysisPlugin

**File:** `app/ai_analysis/base_plugin.py`

Abstract base class for all analysis plugins.

### Constructor

```python
BaseAnalysisPlugin(name: str, description: str, version: str)
```

**Parameters:**
- `name` (str): Unique plugin identifier
- `description` (str): Human-readable description
- `version` (str): Semantic version (e.g., "1.0.0")

### Abstract Methods (Must Implement)

#### `analyze(content: str, **kwargs) -> AnalysisResult`
Perform synchronous analysis.

**Must be implemented by subclasses.**

#### `analyze_async(content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult`
Perform asynchronous analysis with progress tracking.

**Must be implemented by subclasses.**

### Optional Methods

#### `validate_content(content: str) -> bool`
Validate content before analysis.

**Default:** Returns `True` for non-empty content.

#### `get_config() -> Dict[str, Any]`
Get plugin configuration.

**Default:** Returns basic config dict.

### Properties

- `name` (str): Plugin name
- `description` (str): Plugin description
- `version` (str): Plugin version
- `requires_ollama` (bool): Whether plugin needs Ollama
- `max_retries` (int): Maximum retry attempts
- `timeout_seconds` (int): Operation timeout

### AnalysisResult Class

```python
@dataclass
class AnalysisResult:
    success: bool
    data: Dict[str, Any]
    message: str
    processing_time: float
    plugin_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## AIAnalysisManager

**File:** `app/ai_analysis/manager.py`

Central management for AI analysis plugins.

### Constructor

```python
AIAnalysisManager()
```

### Methods

#### `register_plugin(plugin: BaseAnalysisPlugin) -> bool`
Register a plugin with the manager.

**Returns:** `True` on success.

#### `analyze(content: str, plugin_name: str, **kwargs) -> AnalysisResult`
Run synchronous analysis.

**Raises:** `ValueError` if plugin not found.

#### `analyze_async(content: str, plugin_name: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult`
Run asynchronous analysis.

#### `analyze_multiple(content: str, plugin_names: List[str], **kwargs) -> Dict[str, AnalysisResult]`
Run multiple analyses in parallel.

**Returns:** Dictionary mapping plugin names to results.

**Example:**
```python
results = ai_manager.analyze_multiple(
    content="Sample text",
    plugin_names=["tagging", "summarization", "sentiment_compass"]
)

for plugin_name, result in results.items():
    print(f"{plugin_name}: {result.message}")
```

#### `get_available_plugins() -> List[str]`
Get list of registered plugin names.

---

## UI Components

**File:** `app/ui_components.py`

Reusable UI component library.

### DatePickerButton

Date picker with button component.

```python
DatePickerButton(
    label: str = "日付選択",
    initial_date: Optional[datetime] = None,
    on_date_change: Optional[Callable] = None
)
```

**Methods:**
- `get_selected_date() -> datetime`
- `get_date_string(format: str = "%Y-%m-%d") -> str`

### ProgressButton

Button with integrated progress ring.

```python
ProgressButton(
    text: str,
    icon: Optional[str] = None,
    on_click: Optional[Callable] = None,
    button_style: Optional[ft.ButtonStyle] = None
)
```

**Methods:**
- `show_progress()`: Show progress indicator
- `hide_progress()`: Hide progress indicator

### ExpandableSection

Expandable/collapsible section.

```python
ExpandableSection(
    title: str,
    icon: str,
    content_items: List[ft.Control],
    initial_expanded: bool = False
)
```

**Methods:**
- `expand()`: Expand the section
- `collapse()`: Collapse the section

### EditableTextField

Multiline text field with save button.

```python
EditableTextField(
    label: str = "編集",
    initial_value: str = "",
    min_lines: int = 10,
    max_lines: int = 20,
    on_save: Optional[Callable] = None,
    save_button_text: str = "保存"
)
```

**Methods:**
- `get_value() -> str`
- `set_value(value: str)`

### FileListItem

File list item with actions.

```python
FileListItem(
    icon: str,
    icon_color: str,
    title: str,
    subtitle: Optional[str] = None,
    on_click: Optional[Callable] = None,
    actions: Optional[List[Dict[str, Any]]] = None
)
```

### SectionHeader

Styled section header.

```python
SectionHeader(
    title: str,
    bgcolor: str = ft.Colors.BLUE_50,
    actions: Optional[List[ft.Control]] = None
)
```

### SearchField

Search field with icon.

```python
SearchField(
    hint_text: str = "検索...",
    on_change: Optional[Callable] = None
)
```

### StatusMessage

Colored status message.

```python
StatusMessage(
    message: str,
    status_type: str = "info"  # info, success, warning, error
)
```

### Utility Functions

#### `create_loading_overlay(message: str = "処理中...") -> ft.Container`
Create a loading overlay.

#### `create_confirmation_dialog(...) -> ft.AlertDialog`
Create a confirmation dialog.

---

## Type Definitions

### OperationStatus (Enum)

```python
class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### OperationInfo (DataClass)

```python
@dataclass
class OperationInfo:
    operation_id: str
    status: OperationStatus
    progress: float  # 0.0 to 1.0
    message: str
    result: Any
    error: Optional[str]
    start_time: float
    end_time: Optional[float]
```

---

## Configuration

**File:** `config/config.py`

### Constants

```python
# Paths
NOTES_DIR = Path("data/notes")
MEMORIES_DIR = Path("data/memories")
NIPPO_DIR = Path("data/nippo")
CHAT_LOGS_DIR = Path("data/chat_logs")
DB_PATH = Path("data/anc_db.json")

# AI Models
GEMINI_MODEL = "gemini-2.5-pro"
OLLAMA_MODEL = "gemma3:4b"

# API Keys (from environment)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Limits
MAX_HISTORY_CHARS = 4000
MAX_MEMORY_CHARS = 2000
```

---

**Version:** 3.0.0
**Last Updated:** October 1, 2025
**Maintained By:** Project A.N.C. Team
