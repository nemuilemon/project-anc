# Changelog

All notable changes to Project A.N.C. (Alice Nexus Core) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.2.0] - 2025-10-15

### Added
- **Compass API Graph Search Support**: Added support for `/graph_search` endpoint
  - New endpoint type selection in Settings UI (standard search vs graph search)
  - Graph search retrieves both similar memories and related memories
  - Configurable `related_limit` parameter for graph search results
  - Dynamic endpoint construction based on user selection
- **Enhanced Compass API Configuration**:
  - Split API URL into base URL and endpoint path for flexibility
  - New `COMPASS_API_BASE_URL` environment variable (without endpoint path)
  - New `COMPASS_API_ENDPOINT` environment variable (search/graph_search)
  - New `COMPASS_API_RELATED_LIMIT` environment variable (graph search only)
- **UI Improvements in Settings Tab**:
  - Endpoint type dropdown: "標準検索 (search)" or "グラフ検索 (graph_search)"
  - Related memories count field for graph search configuration
  - Helper text explaining when each option is applicable
- **Application Window Icon**: Added custom window icon for better branding
  - Created `assets/icon.ico` with multiple resolutions (256x256, 128x128, 64x64, 32x32, 16x16)
  - Configured `page.window.icon` with absolute path for `flet run` compatibility
  - Added `assets_dir` parameter to `ft.app()` for proper asset loading

### Changed
- **alice_chat_manager.py**: Updated `_get_past_conversations_from_compass_api()` method
  - Now constructs API URL dynamically: `{base_url}/{endpoint}`
  - Adds `related_limit` parameter when endpoint is `graph_search`
  - Enhanced logging to show which endpoint is being used
- **config.py**: Updated Compass API configuration structure
  - `COMPASS_API_URL` replaced with `COMPASS_API_BASE_URL`
  - Added `COMPASS_API_ENDPOINT` with "search" as default
  - Added `related_limit` to `COMPASS_API_CONFIG` dictionary
- **.env.example**: Updated with new environment variables and clearer documentation
  - Restructured Compass API section with detailed comments
  - Added examples for both search modes

### Technical Details
- Backward compatible: Default values maintain existing behavior (standard search)
- All settings are hot-swappable through the UI without app restart
- Thread-safe configuration reloading using `importlib.reload()`
- Comprehensive validation for new numeric fields

## [3.1.1] - 2025-10-13

### Added
- **Tag Editing UI**: Complete tag management interface in file context menu
  - Tag chips display with individual delete buttons
  - Add new tags functionality with validation
  - Save/Cancel dialog for tag editing
  - Proper state management to avoid reference issues
- **Text Input Fields for Settings**: Replaced sliders with numeric text fields
  - Conversation history character count now accepts 0 and any positive integer
  - Compass API fetch count now accepts 0 and any positive integer
  - Input validation with clear error messages for invalid values

### Changed
- **Configuration Management**: Full migration from config.py to .env file
  - All settings from UI now write to .env file instead of config.py
  - Added new environment variables:
    - `ALICE_HISTORY_CHAR_LIMIT`: Controls conversation history character limit
    - `COMPASS_API_URL`: Compass API endpoint URL
    - `COMPASS_API_TARGET`: Target field for Compass search
    - `COMPASS_API_LIMIT`: Number of results to fetch
    - `COMPASS_API_COMPRESS`: Enable/disable response compression
    - `COMPASS_API_SEARCH_MODE`: Search mode (latest/relevant)
- **config.py**: Now reads all dynamic settings from environment variables
  - `COMPASS_API_URL`: Reads from `COMPASS_API_URL` env var
  - `COMPASS_API_CONFIG`: All fields read from individual env vars
  - `ALICE_CHAT_CONFIG['history_char_limit']`: Reads from `ALICE_HISTORY_CHAR_LIMIT`
  - All settings include proper default values for missing env vars

### Fixed
- **Tag Display Bug**: Resolved reported issue of garbled tag display on deletion
  - Root cause: Tag editing functionality was completely missing
  - Implemented full tag editing dialog to prevent data issues
- **Settings Validation**: Added >= 0 validation for numeric input fields
  - Prevents negative values in configuration
  - Clear error messages guide users to valid inputs

### Technical Improvements
- Boolean environment variable parsing with multiple accepted formats (true/1/yes)
- Integer conversion with proper error handling
- Thread-safe tag list operations using `.copy()` to avoid mutations
- Comprehensive syntax validation for modified files

## [3.1.0] - 2025-10-13

### Added
- Multi-conversation tab management with persistence
- Markdown rendering for AI responses
- Conversation state persistence (data/conversation_state.json)
- OpenAI integration alongside Google Gemini

### Changed
- Improved UI layout with modern conversation tabs
- Enhanced state management for conversation history

## [3.0.0] - 2025-09-25

### Added
- Centralized state management system (state_manager.py)
- Dynamic plugin discovery system (plugin_manager.py)
- Reusable UI component library (ui_components.py)
- Thread-safe operations with RLock
- Observer pattern for reactive updates

### Changed
- Complete architecture refactor
- 40% code reduction from v2.0 (~1,800 lines of quality code)
- Automatic plugin registration (zero-configuration)

### Breaking Changes
- Plugin registration is now automatic (remove manual registration code)
- State access must use AppState methods (no direct manipulation)
- UI components must import from ui_components module

## [2.0.0] - 2025-09

### Added
- AI analysis system with Ollama integration
- Plugin-based architecture for analysis types
- Tagging plugin for keyword extraction
- Summarization plugin for content summaries
- Sentiment analysis plugin
- Comprehensive security and error handling
- Virtual environment testing validation

### Changed
- Modular plugin system for extensibility
- Enhanced error handling across all modules

## [1.0.0] - Initial Release

### Added
- Basic note-taking functionality
- File management with TinyDB
- Markdown editor
- Search and filtering
- Archive system

---

## Release Types

- **Major version** (X.0.0): Breaking changes, major new features
- **Minor version** (0.X.0): New features, backwards compatible
- **Patch version** (0.0.X): Bug fixes, minor improvements

## Links

- [Documentation](docs/)
- [Issue Tracker](https://github.com/your-username/project-anc/issues)
- [Releases](https://github.com/your-username/project-anc/releases)
