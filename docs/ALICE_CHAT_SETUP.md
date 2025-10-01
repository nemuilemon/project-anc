# Alice Chat Setup Guide

## 🌸 Alice AI Chat Setup Guide

**Version:** 3.0.0
**Last Updated:** October 1, 2025

This guide explains how to set up and use Alice, the AI assistant powered by Google Gemini in Project A.N.C.

## Prerequisites

- Google AI Studio account
- Gemini API key (google-generativeai 1.38+)

## Setup Instructions

### 1. Get Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Create a new project or select an existing one
5. Copy the generated API key

### 2. Configure Environment Variable

#### Windows (Command Prompt)
```cmd
set GEMINI_API_KEY=your_api_key_here
```

#### Windows (PowerShell)
```powershell
$env:GEMINI_API_KEY = "your_api_key_here"
```

#### Linux/macOS
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 3. .env File Configuration (Recommended)

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

### 4. Verify Installation

1. Start Project A.N.C.
```bash
python app/main.py
```

2. The main chat interface with Alice will load automatically
3. Type a message and click send
4. Verify Alice responds

## Features

### 💫 Alice Chat Features (v3.0)

1. **Conversation-First UI** (`ui_redesign.py`)
   - Clean, focused chat interface
   - Scrollable message history with auto-scroll
   - Real-time message streaming
   - Thinking indicator during AI processing
   - Message timestamps
   - Clear/Export conversation functions

2. **State Management Integration** (`state_manager.py`)
   - Centralized conversation state with `AppState`
   - Thread-safe message history
   - Observer pattern for reactive UI updates
   - Session persistence across app restarts

3. **Context Management** (`alice_chat_manager.py`)
   - **Four-layer context system:**
     1. Long-term memory (`data/notes/0-Memory.md`)
     2. Today's chat history (from daily log)
     3. Current session history (AppState)
     4. Latest user message
   - Intelligent context window management
   - Automatic context trimming for API limits

4. **Chat Logging System**
   - Daily chat logs: `data/chat_logs/YYYY-MM-DD.md`
   - Dialog API logs: `logs/dialogs/dialog-*.json`
   - System logs: `logs/alice_chat.log.*`
   - Full request/response tracking for debugging

5. **AI Model Configuration**
   - Default model: **gemini-2.5-pro**
   - System instruction: `data/notes/0-System-Prompt.md`
   - Configurable via Settings tab
   - Support for model switching

## Troubleshooting

### API Key Errors

**Error:** "Alice connection unavailable" or API initialization failed

**Solutions:**
- Verify `GEMINI_API_KEY` is correctly set in environment or `.env` file
- Check API key validity at [Google AI Studio](https://aistudio.google.com/app/apikey)
- Ensure API key has no leading/trailing spaces
- Restart the application after setting the environment variable

### System Prompt Errors

**Error:** System instruction not loading

**Solutions:**
- Verify `data/notes/0-System-Prompt.md` exists
- Check file read permissions
- Ensure file encoding is UTF-8
- Create file from template if missing

### Memory File Errors

**Error:** Long-term memory not loading

**Solutions:**
- Verify `data/notes/0-Memory.md` exists
- Check file read/write permissions
- Ensure proper Markdown formatting

### Chat Log Errors

**Error:** Unable to save conversation logs

**Solutions:**
- Verify `data/chat_logs/` directory exists and is writable
- Check available disk space
- Review permissions on data directory
- Check `logs/alice_chat.log.*` for detailed errors

### Context Window Errors

**Error:** "Token limit exceeded" or context too large

**Solutions:**
- Alice automatically trims context to fit API limits
- Clear conversation history with "Clear" button
- Reduce long-term memory size if needed
- Check `logs/dialogs/` for token usage details

## File Structure

```
project-anc/
├── app/
│   ├── alice_chat_manager.py      # Gemini API client + context management
│   ├── ui_redesign.py             # Main chat interface
│   ├── state_manager.py           # AppState with conversation state
│   ├── handlers.py                # Chat event handlers
│   ├── logger.py                  # Logging system with daily rotation
│   └── main.py                    # App initialization
├── config/
│   └── config.py                  # Gemini API configuration
├── data/
│   ├── notes/
│   │   ├── 0-System-Prompt.md     # Alice system instruction
│   │   └── 0-Memory.md            # Long-term memory
│   └── chat_logs/                 # Daily conversation logs (auto-created)
│       └── YYYY-MM-DD.md          # Today's chat log
├── logs/
│   ├── alice_chat.log.*           # Daily rotated chat logs
│   └── dialogs/                   # API request/response logs
│       └── dialog-*.json          # Individual dialog logs
└── .env                           # Environment variables (API key)
```

## Usage Guide

### Starting a Conversation

1. Launch Project A.N.C.: `python app/main.py`
2. The main chat interface loads automatically (conversation-first design)
3. Type your message in the input field at the bottom
4. Press Enter or click the Send button
5. Watch the thinking indicator while Alice processes
6. View Alice's response in the chat history

### Conversation Management

- **Clear Chat**: Click "Clear" to reset the current session
- **Export Chat**: Click "Export" to save conversation to a file
- **View History**: Scroll through message history
- **Auto-Save**: All messages automatically saved to daily log

### Context Files

Alice uses multiple context sources:

1. **0-System-Prompt.md**: Defines Alice's personality and behavior
2. **0-Memory.md**: Long-term memory and important information
3. **Daily logs**: Conversation history from today
4. **Session state**: Messages from current session

Edit these files to customize Alice's knowledge and behavior.

### Advanced Features

- **State Observers**: UI automatically updates when conversation state changes
- **Thread Safety**: Concurrent message handling supported
- **Async Operations**: Non-blocking chat for smooth UI
- **Dialog Logging**: Every API call logged for debugging

## API Configuration

### Model Selection

Edit in Settings tab or `config/config.py`:

```python
GEMINI_MODEL = "gemini-2.5-pro"  # Default model
# Alternatives: gemini-2.0-flash-exp, gemini-1.5-pro
```

### Context Management

```python
MAX_HISTORY_CHARS = 4000  # Chat history character limit
MAX_MEMORY_CHARS = 2000   # Long-term memory limit
```

Alice automatically trims context to fit within API token limits while preserving important information.

## Best Practices

1. **API Key Security**
   - Never commit `.env` file to version control
   - Use `.env` for local development
   - Use system environment variables for production

2. **Memory Management**
   - Keep `0-Memory.md` concise and relevant
   - Update memory with important information
   - Clear outdated information regularly

3. **System Prompt**
   - Define clear personality and behavior
   - Include task-specific instructions
   - Keep instructions focused and actionable

4. **Log Management**
   - Review `logs/dialogs/` for API issues
   - Check `alice_chat.log.*` for system errors
   - Archive old chat logs periodically

---

**Version:** 3.0.0
**Last Updated:** October 1, 2025
**Security Note:** Keep your API key confidential. Never share it with others.