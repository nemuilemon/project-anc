# **Project A.N.C. (Alice Nexus Core) - Technical Specification**

## **1. Project Overview**

Project A.N.C. is a **Personal Knowledge Engine** designed to integrate and enhance user thoughts and knowledge through AI collaboration. More than just a note-taking application, it functions as a dedicated "second brain" for users, supporting intellectual productivity through an advanced desktop application.

## **2. Core Architecture**

The application employs a loosely-coupled three-tier architecture consisting of UI, Data Management, and AI System layers.

### **UI (User Interface)**
* Built with **Flet**, a Python framework enabling rapid desktop application development with cross-platform capabilities using pure Python code.

### **Data Management (Hybrid Model)**
* **Note Content**: Stored as plain text **Markdown files (.md)** directly in the file system for maximum portability.
* **Metadata**: File metadata (title, path, tags, etc.) stored in **TinyDB**, a lightweight NoSQL JSON database for fast querying.
* This hybrid approach ensures data portability while maintaining high-speed metadata operations.

#### **Database Schema**
TinyDB record structure for each file:
```json
{
    "title": "filename.md",
    "path": "C:\\notes\\filename.md", 
    "tags": ["tag1", "tag2", "tag3"],
    "status": "active",
    "order_index": 1
}
```

**Field Descriptions:**
- `title`: Filename for display
- `path`: Absolute file path
- `tags`: Array of AI-generated or manually assigned tags
- `status`: File state (`"active"` or `"archived"`)  
- `order_index`: Display order (numeric, ascending)

**Legacy Support:**
Files without `status` or `order_index` default to `"active"` and `0` respectively.

### **AI System (Hybrid Brain)**
* Uses **Ollama** running locally as the "cerebellum" for AI operations.
* Analyzes note content via Ollama to extract keywords for **automated AI tagging**.

## **3. Technology Stack**

* **Programming Language**: **Python**
* **UI Framework**: **Flet**
* **Database**: **TinyDB** 
* **AI Integration**: **Ollama** (via `ollama` Python library)
* **Security**: **Enhanced input validation and path sanitization**
* **Performance**: **Asynchronous operations with progress tracking**
* **Logging**: **Comprehensive multi-category logging system**

## **4. System Architecture & Components**

The project follows separation of concerns principles with the following modular structure:

### **Core Application Modules**

* **`main.py`** (~150 lines)
    * **Application entry point** and initialization hub.
    * Handles Flet application startup, window creation, and component orchestration.
    * Streamlined through Phase 2 refactoring for cleaner architecture.

* **`handlers.py`** (~380 lines) - **[NEW IN PHASE 2]**
    * **Centralized event handling logic** extracted from main.py.
    * Manages all UI event handlers with comprehensive logging and error handling.
    * Provides clean separation between UI interactions and business logic.

* **`ui.py`** (~600+ lines)
    * **UI component definitions** and layout management.
    * Builds all user-facing interfaces using Flet widgets (AppBar, Tabs, ListTile, Dialogs).
    * Enhanced with progress indicators and delete confirmation dialogs.

* **`logic.py`** (~850+ lines)
    * **Core business logic** for all application operations.
    * Handles file I/O, database operations, Ollama API communication.
    * Enhanced with async methods and transaction-safe operations.

### **Infrastructure Modules**

* **`async_operations.py`** (~280 lines) - **[NEW IN PHASE 2]**
    * **Asynchronous operation management** for responsive UI.
    * Provides `AsyncOperationManager` and `ProgressTracker` for background tasks.
    * Prevents UI freezing during large file operations and AI analysis.

* **`logger.py`** (~320 lines) - **[NEW IN PHASE 2]**  
    * **Comprehensive logging system** with multiple specialized categories.
    * Generates structured logs: app.log, file_operations.log, ui_events.log, errors.log, security.log, performance.log.
    * Includes `PerformanceTimer` context manager for operation timing.

* **`security.py`** (~250 lines) - **[NEW IN PHASE 1]**
    * **Security utilities** for input validation and sanitization.
    * Prevents path traversal attacks and filename injection vulnerabilities.
    * Provides safe file operations with comprehensive validation.

* **`config.py`**
    * **Configuration management** for application settings.
    * Centralizes paths, database names, AI model settings for maintainability.

## **5. Development Environment Setup**

### **Virtual Environment**
The project uses **Python virtual environment (.venv)** for dependency management:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux  
source .venv/bin/activate
```

### **Dependencies** 
Install from `requirements.txt`:
```bash
pip install -r requirements.txt
```

**Core Dependencies:**
* **flet>=0.21.0**: UI framework
* **tinydb>=4.8.0**: Lightweight JSON database
* **ollama>=0.1.7**: AI integration library

### **Execution**
```bash
# After activating virtual environment
python main.py
```

## **6. Feature Set**

### **Core Features**
* **Tabbed Text Editor**: Edit multiple notes simultaneously with tab interface.
* **File Creation**: Create new .md files via AppBar "+" button with automatic tab opening.
* **File List Display**: Browse all Markdown files in the designated directory.
* **File Reordering**: Button-based file reordering system (replaces drag & drop for better UX).
* **Archive System**: Move files to `.archive` folder with toggle visibility control.
* **Hybrid Save**: Automatic dual-save (content to .md, metadata to anc_db.json).
* **AI Tag Analysis**: "Analyze Tags" button sends content to Ollama for automatic tag generation.
* **Manual Refresh**: "Refresh" button synchronizes directory contents with database.
* **Tag Management**: Manual tag editing via dedicated interface.
* **File Renaming**: Rename files through popup menu interface.
* **Tab Management**: Auto-save on tab close with × button.

### **Phase 1: Foundation Hardening Features** - **[COMPLETED]**
* **Security Enhancements**:
  - Path traversal attack prevention
  - Filename sanitization and validation
  - Input validation for all user inputs
  - Safe file operations with security checks

* **Error Handling**:
  - Comprehensive try-catch blocks throughout application
  - Transaction-like mechanisms with rollback capability
  - Graceful error recovery and user feedback

* **Development Environment**:
  - Complete `requirements.txt` for reproducible builds
  - Comprehensive security test suite (26 individual tests)

### **Phase 2: UX & Refactoring Features** - **[COMPLETED]**
* **Delete Function with Safety Confirmations**:
  - Custom confirmation dialog with warning styling
  - Transaction-safe deletion with automatic rollback on failure
  - Automatic tab closure and file list refresh

* **Asynchronous File Processing**:
  - Background file operations preventing UI freezing
  - Chunked I/O for large files with progress tracking
  - Thread pool execution for optimal performance

* **Progress Indicators**:
  - Visual progress bars in AppBar for long-running operations
  - Status text with operation descriptions
  - Automatic show/hide based on operation type

* **Code Quality Improvements**:
  - Clean separation of concerns (main.py reduced from ~400 to ~150 lines)
  - Modular architecture with dedicated handler module
  - Enhanced maintainability and testability

* **Comprehensive Logging System**:
  - Six specialized log categories for different event types
  - Performance timing and monitoring
  - Structured logging with UTF-8 encoding
  - Debug mode support via environment variables

## **7. Security Features** - **[ENHANCED]**

* **Path Validation**: Prevents directory traversal attacks (../ sequences)
* **Filename Sanitization**: Removes dangerous characters and prevents reserved names
* **Input Validation**: Validates all user inputs before processing
* **Transaction Safety**: Rollback mechanisms for data integrity
* **Security Logging**: Dedicated security event tracking
* **Safe Operations**: All file operations include security validation

## **8. Performance Features** - **[NEW]**

* **Async Operations**: Non-blocking file I/O operations
* **Progress Tracking**: Real-time progress feedback for user awareness  
* **Memory Efficiency**: Chunked file processing for large files
* **Background Processing**: AI analysis runs in background threads
* **Resource Management**: Proper cleanup and shutdown procedures

## **9. Logging & Monitoring** - **[NEW]**

### **Log Categories**
* **app.log**: General application events and lifecycle
* **file_operations.log**: All file I/O operations and results
* **ui_events.log**: User interface interactions and events
* **errors.log**: Application errors with full stack traces
* **security.log**: Security-related events and violations
* **performance.log**: Performance metrics and timing data

### **Features**
* **Structured Logging**: Consistent timestamps and contextual information
* **Performance Timing**: Automatic operation timing with `PerformanceTimer`
* **Debug Support**: Environment variable controlled debug output
* **Log Rotation**: Automatic cleanup of old log files

## **10. Architecture Benefits**

### **For Users**
* **Responsive Interface**: No UI freezing during heavy operations
* **Progress Feedback**: Clear indication of operation status
* **Safe Operations**: Confirmation dialogs and transaction safety
* **Better Error Handling**: Clear error messages and recovery options

### **For Developers**  
* **Clean Architecture**: Well-separated concerns for easy maintenance
* **Comprehensive Logging**: Full activity tracking for debugging
* **Async Framework**: Foundation for future performance improvements
* **Modular Design**: Easy to add new features and components

### **For System Reliability**
* **Robust Error Handling**: Comprehensive exception management
* **Security Protection**: Defense against common attack vectors
* **Performance Monitoring**: Built-in metrics and timing
* **Graceful Degradation**: Safe handling of edge cases

## **11. Future Development Foundation**

The current architecture provides a solid foundation for future enhancements:

* **Modular Structure**: Easy addition of new features
* **Async Infrastructure**: Ready for more performance improvements  
* **Logging Framework**: Comprehensive monitoring capabilities
* **Security Layer**: Foundation for additional security measures
* **Progress System**: Extensible to new types of operations

## **12. Production Readiness**

**Project A.N.C. is now production-ready** with:

* ✅ **Security Hardening**: Comprehensive input validation and attack prevention
* ✅ **Performance Optimization**: Async operations and progress tracking
* ✅ **Code Quality**: Clean, maintainable, and well-documented architecture
* ✅ **Error Handling**: Robust exception management and recovery
* ✅ **Logging**: Complete activity monitoring and debugging support
* ✅ **Backward Compatibility**: All existing functionality preserved
* ✅ **User Experience**: Responsive UI with comprehensive feedback

---

**Project A.N.C. (Alice Nexus Core)** - A production-ready personal knowledge engine with advanced UX, robust security, and clean architecture designed for comfortable daily use and future expansion.

**Development Status**: ✅ **Phase 1 & 2 COMPLETED**  
**Production Ready**: ✅ **YES**  
**Architecture**: ✅ **Clean & Modular**  
**Security**: ✅ **Hardened**  
**Performance**: ✅ **Optimized**