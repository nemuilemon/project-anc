# Alice Chat Setup Guide

## 🌸 Alice AI Chat Setup Guide

**Version:** 3.1.0
**Last Updated:** October 9, 2025

This guide explains how to set up and use Alice, the AI assistant powered by **Google Gemini** or **OpenAI** in Project A.N.C.

## Prerequisites

### For Google Gemini
- Google AI Studio account
- Gemini API key (google-generativeai 1.38+)

### For OpenAI
- OpenAI Platform account
- OpenAI API key (openai 1.0+)

## Setup Instructions

### 1. Get API Keys

#### Google Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Create a new project or select an existing one
5. Copy the generated API key

#### OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in with your OpenAI account
3. Click "Create new secret key"
4. Give it a name (e.g., "Project ANC")
5. Copy the generated API key (you won't be able to see it again!)

### 2. Configure Environment Variables

#### Option A: Using .env File (Recommended)

Create a `.env` file in the project root:

```env
# API Provider Selection (google or openai)
CHAT_API_PROVIDER=google

# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
```

#### Option B: System Environment Variables

##### Windows (Command Prompt)
```cmd
set CHAT_API_PROVIDER=google
set GEMINI_API_KEY=your_gemini_api_key_here
set OPENAI_API_KEY=your_openai_api_key_here
```

##### Windows (PowerShell)
```powershell
$env:CHAT_API_PROVIDER = "google"
$env:GEMINI_API_KEY = "your_gemini_api_key_here"
$env:OPENAI_API_KEY = "your_openai_api_key_here"
```

##### Linux/macOS
```bash
export CHAT_API_PROVIDER="google"
export GEMINI_API_KEY="your_gemini_api_key_here"
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 3. Configure via Settings UI (Easiest)

1. Launch Project A.N.C.: `python app/main.py`
2. Open the **Settings Tab** in the sidebar
3. Expand the **API設定** (API Settings) section
4. Select your preferred **API Provider** (Google Gemini or OpenAI)
5. Enter the appropriate API key(s)
6. Click **設定を保存** (Save Settings)
7. **Restart the application** for changes to take effect

### 4. Verify Installation

1. Start Project A.N.C.
```bash
python app/main.py
```

2. The main chat interface with Alice will load automatically
3. Check the console output for "API client initialized successfully"
4. Type a message and click send
5. Verify Alice responds

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
   - **Google Gemini**: gemini-2.5-pro (default)
   - **OpenAI**: gpt-4-turbo (default)
   - System instruction: `data/notes/0-System-Prompt.md`
   - Configurable via Settings tab
   - Support for provider and model switching

## Troubleshooting

### API Key Errors

**Error:** "Alice connection unavailable" or API initialization failed

**Solutions:**
- Verify `CHAT_API_PROVIDER` is set to either "google" or "openai"
- For Google Gemini:
  - Verify `GEMINI_API_KEY` is correctly set in environment or `.env` file
  - Check API key validity at [Google AI Studio](https://aistudio.google.com/app/apikey)
- For OpenAI:
  - Verify `OPENAI_API_KEY` is correctly set in environment or `.env` file
  - Check API key validity at [OpenAI Platform](https://platform.openai.com/api-keys)
- Ensure API keys have no leading/trailing spaces
- Restart the application after setting the environment variables
- Check console output for specific error messages

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

### API Provider Selection

Configure in `.env` file or via Settings tab:

```env
CHAT_API_PROVIDER=google  # or "openai"
```

### Model Selection

Edit in `config/config.py`:

```python
ALICE_CHAT_CONFIG = {
    "gemini_model": "gemini-2.5-pro",  # Google Gemini model
    "openai_model": "gpt-4-turbo",     # OpenAI model
    # ... other settings
}

# Google Gemini alternatives: gemini-2.0-flash-exp, gemini-1.5-pro
# OpenAI alternatives: gpt-4, gpt-3.5-turbo, gpt-4-turbo-preview
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

## Switching Between API Providers

You can switch between Google Gemini and OpenAI at any time:

### Method 1: Settings UI (Recommended)
1. Open Settings tab
2. Expand "API設定" section
3. Select desired provider from dropdown
4. Enter corresponding API key if needed
5. Click "設定を保存"
6. Restart the application

### Method 2: Edit .env File
1. Open `.env` file in project root
2. Change `CHAT_API_PROVIDER` to `google` or `openai`
3. Ensure the corresponding API key is set
4. Save the file
5. Restart the application

### Method 3: Edit config.py
1. Open `config/config.py`
2. Locate the line: `CHAT_API_PROVIDER = os.environ.get('CHAT_API_PROVIDER', 'google')`
3. Change the default value from `'google'` to `'openai'` (or vice versa)
4. Save the file
5. Restart the application

## Comparison: Google Gemini vs OpenAI

| Feature | Google Gemini | OpenAI |
|---------|---------------|--------|
| **Default Model** | gemini-2.5-pro | gpt-4-turbo |
| **Context Window** | ~1M tokens | 128k tokens |
| **Pricing** | Free tier available | Pay per token |
| **API Library** | google-genai | openai |
| **Best For** | Long context, free usage | General purpose, stability |

---

**Version:** 3.1.0
**Last Updated:** October 9, 2025
**Security Note:** Keep your API keys confidential. Never share them or commit them to version control.