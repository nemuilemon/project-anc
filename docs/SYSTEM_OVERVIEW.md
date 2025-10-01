# Project A.N.C. System Overview

**Version:** 3.0.0 - Modern Architecture with State Management
**Date:** October 1, 2025
**Status:** Production Ready

## Executive Summary

Project A.N.C. (Alice Nexus Core) is a modern AI-powered desktop application featuring Alice, an intelligent AI assistant powered by Google Gemini. The system has evolved from a note-taking app into a comprehensive AI conversation platform with state management, dynamic plugin architecture, and modular UI components.

## System Architecture

```
Project A.N.C. v3.0 Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                    User Interface (Flet 0.28+)                  │
│  ┌──────────────────┐  ┌──────────────────────────────────┐    │
│  │  ui_redesign.py  │  │      sidebar_tabs.py              │    │
│  │  - Main Chat UI  │  │  - Memory Creation Tab            │    │
│  │  - Conversation  │  │  - Nippo (Daily Report) Tab       │    │
│  │  Area            │  │  - File Management Tab            │    │
│  └──────────────────┘  │  - Editor Tab                     │    │
│                        │  - AI Analysis Tab                 │    │
│                        │  - Settings Tab                    │    │
│                        └──────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    UI Components (ui_components.py)             │
│  DatePickerButton | ProgressButton | ExpandableSection          │
│  EditableTextField | SectionHeader | SearchField               │
├─────────────────────────────────────────────────────────────────┤
│                    State Management (state_manager.py)          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐        │
│  │ File State  │  │  Conversation │  │   UI State     │        │
│  │ Management  │  │  State        │  │   Settings     │        │
│  └─────────────┘  └──────────────┘  └────────────────┘        │
│           Observer Pattern for Reactive Updates                 │
├─────────────────────────────────────────────────────────────────┤
│                Event Handlers & Business Logic                  │
│  ┌──────────────────┐  ┌─────────────────────────────────┐    │
│  │   handlers.py    │  │         logic.py                 │    │
│  │  - UI Events     │  │  - File Operations               │    │
│  │  - User Actions  │  │  - Database Management           │    │
│  └──────────────────┘  └─────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                       Core Services                             │
│  ┌─────────────────────────┐  ┌──────────────────────────┐    │
│  │ alice_chat_manager.py   │  │  async_operations.py      │    │
│  │ - Gemini API Client     │  │  - Thread Pool Executor   │    │
│  │ - Conversation History  │  │  - Operation Tracking     │    │
│  │ - Context Management    │  │  - Cancellation Support   │    │
│  │ - Chat Log Persistence  │  │  - Progress Callbacks     │    │
│  └─────────────────────────┘  └──────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                    AI Analysis Plugin System                    │
│  ┌─────────────────────────┐  ┌──────────────────────────┐    │
│  │   plugin_manager.py     │  │   ai_analysis/           │    │
│  │ - Dynamic Plugin Loading│  │   - base_plugin.py       │    │
│  │ - Runtime Discovery     │  │   - manager.py           │    │
│  │ - Plugin Registry       │  │   plugins/               │    │
│  └─────────────────────────┘  │   - tagging_plugin.py    │    │
│                               │   - summarization_plugin.py│   │
│                               │   - sentiment_compass_plugin│  │
│                               └──────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                   Data Layer & External Services                │
│  ┌──────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │  TinyDB (JSON)   │  │  Google Gemini │  │   Ollama     │  │
│  │  - File Metadata │  │  - Alice Chat  │  │  - Analysis  │  │
│  │  - Analysis Data │  │  - API v1.38+  │  │  - Plugins   │  │
│  └──────────────────┘  └────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Cross-Cutting Concerns                       │
│  ┌──────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │   security.py    │  │   logger.py    │  │  config.py   │  │
│  │ - Validation     │  │ - Daily Rotate │  │ - Settings   │  │
│  │ - Sanitization   │  │ - 6 Log Types  │  │ - Paths      │  │
│  └──────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. Main Application (`app/main.py`)
- **Purpose:** Application initialization and orchestration
- **Key Features:**
  - Component initialization with error handling
  - RedesignedAppUI integration
  - Logger setup
  - Database initialization
- **Lines of Code:** ~150

### 2. State Management (`app/state_manager.py`) **[NEW v3.0]**
- **Purpose:** Centralized application state with reactive updates
- **Key Features:**
  - `AppState` class with Observer pattern
  - Thread-safe operations (RLock)
  - File state, conversation state, UI state
  - Event-driven updates
- **Lines of Code:** 416
- **State Types:**
  - `FileState`: Open files, modifications, active file
  - `ConversationState`: Alice chat messages, session info
  - UI state: Selected tabs, visibility
  - Settings: Application configuration

### 3. UI Components (`app/ui_components.py`) **[NEW v3.0]**
- **Purpose:** Reusable UI component library
- **Components:**
  - `DatePickerButton`: Date selection with picker
  - `ProgressButton`: Button with progress indicator
  - `ExpandableSection`: Collapsible sections
  - `EditableTextField`: Text editor with save
  - `FileListItem`: Consistent file display
  - `SectionHeader`: Standardized headers
  - `SearchField`: Search input
  - `StatusMessage`: Colored alerts
- **Lines of Code:** 542
- **Benefits:** 40% code reduction, UI consistency

### 4. User Interface

#### Main UI (`app/ui_redesign.py`)
- **Purpose:** Conversation-first chat interface
- **Features:**
  - Main conversation area with Alice
  - Message history display
  - Input field with send button
  - Clear/Export functions
  - Thinking indicator

#### Sidebar Tabs (`app/sidebar_tabs.py`)
- **Tabs:**
  1. **Memory Creation Tab**: Generate memories from chat logs
  2. **Nippo Creation Tab**: Daily report generation
  3. **File Tab**: File management and navigation
  4. **Editor Tab**: Multi-tab text editor
  5. **AI Analysis Tab**: Plugin-based analysis tools
  6. **Settings Tab**: Application configuration
- **All tabs:** Scrollable with `ft.ScrollMode.AUTO`

### 5. Alice Chat Manager (`app/alice_chat_manager.py`)
- **Purpose:** AI conversation management with Google Gemini
- **Key Features:**
  - Gemini API client (google-genai 1.38+)
  - System instruction loading
  - Long-term memory (0-Memory.md)
  - Conversation history management
  - Chat log persistence (data/chat_logs/YYYY-MM-DD.md)
  - **State Integration:** Uses `AppState` for conversation
- **API Content Structure:**
  1. Long-term memory
  2. Today's chat history (last X chars)
  3. Current session (AppState)
  4. Latest message

### 6. Plugin System (`app/plugin_manager.py`) **[NEW v3.0]**
- **Purpose:** Dynamic AI analysis plugin loading
- **Key Features:**
  - Runtime plugin discovery
  - No code changes needed for new plugins
  - Automatic registration
  - Plugin validation
  - Capability filtering
- **Lines of Code:** 302
- **Loaded Plugins:** 3 (auto-detected)

### 7. Async Operations (`app/async_operations.py`) **[ENHANCED v3.0]**
- **Purpose:** Non-blocking operations with tracking
- **New Features:**
  - `OperationStatus` enum (5 states)
  - `OperationInfo` dataclass
  - Cancellation via `threading.Event`
  - Thread-safe with RLock
  - 60-second operation retention
- **Operations:**
  - File read/write with progress
  - Generic async operations
  - Cancellation support

### 8. Business Logic (`app/logic.py`)
- **Purpose:** File and database operations
- **Responsibilities:**
  - File CRUD operations
  - Database synchronization
  - AI plugin integration (via PluginManager)
  - Security validation
  - Memory/Nippo file management

### 9. Event Handlers (`app/handlers.py`)
- **Purpose:** UI event handling
- **Responsibilities:**
  - File open/save/delete
  - AI analysis execution
  - Progress tracking
  - Error handling

## Key Technologies

### Core Framework
- **Flet 0.28+**: Cross-platform UI framework
- **Python 3.12+**: Modern Python features

### AI Services
- **Google Gemini API**: Alice chat (gemini-2.5-pro)
- **Ollama**: Local AI for analysis plugins (gemma3:4b)

### Data & State
- **TinyDB 4.8+**: JSON-based database
- **AppState**: Centralized state management

### Development
- **pytest**: Testing framework
- **black, isort, flake8, mypy**: Code quality tools

## Data Flow

### Alice Chat Flow
```
User Input
    ↓
ui_redesign.py (UI Event)
    ↓
handlers.py (Event Handler)
    ↓
alice_chat_manager.py
    ├── Load long-term memory (0-Memory.md)
    ├── Load today's chat log (data/chat_logs/YYYY-MM-DD.md)
    ├── Get session history (AppState)
    ├── Prepare API request (4 elements)
    ↓
Google Gemini API
    ↓
Response
    ├── Update AppState (add_conversation_message)
    ├── Save to daily log (append to .md)
    ├── Log API call (logs/dialogs/dialog-*.json)
    ↓
UI Update (display response)
```

### AI Analysis Flow (Plugins)
```
User selects content + analysis type
    ↓
logic.py (get_available_plugins via PluginManager)
    ↓
plugin_manager.py (dynamic plugin loading)
    ├── Scan ai_analysis/plugins/
    ├── Load plugins with importlib
    ├── Register to AIAnalysisManager
    ↓
handlers.py (execute analysis)
    ↓
async_operations.py (run_async_operation)
    ↓
Plugin (analyze/analyze_async)
    ↓
Ollama API (for AI plugins)
    ↓
Results (AnalysisResult)
    ↓
UI Display
```

## File Structure

```
project-anc/
├── app/
│   ├── main.py                    # Application entry point
│   ├── state_manager.py           # [NEW] State management
│   ├── ui_components.py           # [NEW] Reusable UI components
│   ├── plugin_manager.py          # [NEW] Dynamic plugin system
│   ├── ui_redesign.py             # Main chat UI
│   ├── sidebar_tabs.py            # Sidebar tabs
│   ├── alice_chat_manager.py      # [UPDATED] Gemini chat + AppState
│   ├── async_operations.py        # [ENHANCED] Async ops
│   ├── logic.py                   # Business logic
│   ├── handlers.py                # Event handlers
│   ├── logger.py                  # [ENHANCED] Daily log rotation
│   ├── security.py                # Security validation
│   ├── ai_analysis/
│   │   ├── __init__.py            # [v2.0] Dynamic imports
│   │   ├── base_plugin.py         # Plugin interface
│   │   ├── manager.py             # Analysis manager
│   │   └── plugins/               # Auto-discovered plugins
│   │       ├── tagging_plugin.py
│   │       ├── summarization_plugin.py
│   │       └── sentiment_compass_plugin.py
│   └── ...
├── config/
│   └── config.py                  # Configuration
├── data/
│   ├── notes/                     # User notes
│   │   ├── 0-Memory.md            # Alice long-term memory
│   │   └── 0-System-Prompt.md     # Alice system instruction
│   ├── chat_logs/                 # Daily chat logs (YYYY-MM-DD.md)
│   ├── memories/                  # Generated memories
│   ├── nippo/                     # Daily reports
│   └── anc_db.json                # TinyDB database
├── logs/
│   ├── app.log.*                  # Daily rotated system logs
│   └── dialogs/                   # API call logs (dialog-*.json)
├── docs/                          # Documentation
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── .env.example                   # Environment template
└── README.md                      # Project readme
```

## Security Features

1. **Input Validation** (`security.py`)
   - Filename sanitization
   - Path traversal prevention
   - Safe file operations

2. **API Security**
   - Environment variable for API keys
   - No hardcoded credentials
   - .env files in .gitignore

3. **Thread Safety**
   - RLock in AppState
   - RLock in AsyncOperationManager
   - Thread-safe plugin loading

## Logging System

### Log Types (Daily Rotated)
1. **app.log**: System logs
2. **file_operations.log**: File I/O
3. **ui_events.log**: UI interactions
4. **errors.log**: Error tracking
5. **security.log**: Security events
6. **performance.log**: Performance metrics
7. **alice_chat.log**: Chat-related logs

### Dialog Logs
- Location: `logs/dialogs/dialog-YYYY-MM-DD-HHMMSS-mmm.json`
- Content: Request, response, model, timestamp, errors
- Purpose: API debugging and analysis

## Version History

- **v3.0.0 (Oct 2025)**: Modern architecture refactoring
  - State management system
  - Dynamic plugin loading
  - UI component library
  - Enhanced async operations
  - 7,000 lines of legacy code removed
  - 1,800 lines of quality code added

- **v2.0.0 (Sep 2025)**: AI architecture evolution
  - Plugin-based AI analysis
  - Modular design

- **v1.0.0**: Initial release
  - Basic note-taking
  - File management

## Performance Characteristics

- **Startup Time**: ~2-3 seconds
- **Plugin Discovery**: <100ms (3 plugins)
- **State Updates**: O(1) with observers
- **File Operations**: Async for files >1MB
- **Memory Usage**: ~150MB typical

## Extensibility

### Adding a New Plugin
1. Create `.py` file in `app/ai_analysis/plugins/`
2. Inherit from `BaseAnalysisPlugin`
3. Implement `analyze()` and `analyze_async()`
4. Plugin auto-discovered on next launch

### Adding a New UI Component
1. Add to `app/ui_components.py`
2. Follow existing component patterns
3. Use Flet controls and layout
4. Document parameters

### Adding State to AppState
1. Add state variable to `__init__`
2. Create getter/setter methods
3. Add observer event type
4. Notify observers on changes

## Future Enhancements

- [ ] Plugin hot-reload without restart
- [ ] UI component theme system
- [ ] Advanced state serialization
- [ ] Plugin dependency management
- [ ] Comprehensive test suite
- [ ] Performance profiling dashboard
- [ ] Plugin marketplace/discovery

---

**Documentation Version:** 3.0.0
**Last Updated:** October 1, 2025
**Maintained By:** Project A.N.C. Team
