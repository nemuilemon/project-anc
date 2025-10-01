# Troubleshooting Guide

**Version:** 3.0.0
**Last Updated:** October 1, 2025

## Table of Contents

1. [Common Issues](#common-issues)
2. [Installation Problems](#installation-problems)
3. [Runtime Errors](#runtime-errors)
4. [Plugin Issues](#plugin-issues)
5. [Alice Chat Problems](#alice-chat-problems)
6. [Performance Issues](#performance-issues)
7. [Database Issues](#database-issues)
8. [UI Issues](#ui-issues)
9. [Getting Help](#getting-help)

## Common Issues

### Application Won't Start

#### Symptom
```
Error: No module named 'flet'
```

#### Solution
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

#### Symptom
```
Error: Python version 3.12 or higher required
```

#### Solution
```bash
# Check Python version
python --version

# Install Python 3.12+ from python.org
# Create new virtual environment with correct version
python3.12 -m venv .venv
```

---

#### Symptom
Application window opens but immediately closes

#### Solution
```bash
# Run from command line to see errors
python app/main.py

# Check logs
tail -f logs/app.log.*
tail -f logs/errors.log.*
```

---

### Import Errors

#### Symptom
```
ModuleNotFoundError: No module named 'app'
```

#### Solution
```bash
# Ensure you're in project root
cd /path/to/project-anc

# Run with correct path
python app/main.py

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/macOS
set PYTHONPATH=%PYTHONPATH%;%CD%          # Windows
```

---

#### Symptom
```
ImportError: cannot import name 'AppState' from 'app.state_manager'
```

#### Solution
```bash
# Check file exists
ls app/state_manager.py

# Check for syntax errors
python -m py_compile app/state_manager.py

# Reinstall if corrupted
git checkout app/state_manager.py
```

## Installation Problems

### pip Install Fails

#### Symptom
```
ERROR: Could not find a version that satisfies the requirement flet>=0.28.0
```

#### Solution
```bash
# Update pip
python -m pip install --upgrade pip

# Try installing again
pip install -r requirements.txt

# Or install packages individually
pip install flet tinydb ollama google-generativeai python-dotenv
```

---

### Virtual Environment Issues

#### Symptom
Cannot activate virtual environment

#### Solution

**Windows:**
```bash
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or use cmd instead of PowerShell
.venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
# Check permissions
chmod +x .venv/bin/activate

# Source the script
source .venv/bin/activate
```

---

### Dependency Conflicts

#### Symptom
```
ERROR: pip's dependency resolver does not currently take into account all packages
```

#### Solution
```bash
# Create fresh virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Check for conflicts
pip check
```

## Runtime Errors

### Gemini API Key Not Found

#### Symptom
```
Error: GEMINI_API_KEY not found in environment
```

#### Solution
```bash
# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env

# Or set environment variable
export GEMINI_API_KEY="your_key_here"  # Linux/macOS
set GEMINI_API_KEY=your_key_here       # Windows cmd
$env:GEMINI_API_KEY="your_key_here"    # Windows PowerShell

# Verify
python -c "import os; print(os.getenv('GEMINI_API_KEY'))"
```

---

### Permission Denied Errors

#### Symptom
```
PermissionError: [Errno 13] Permission denied: 'data/notes/test.txt'
```

#### Solution
```bash
# Fix directory permissions
chmod -R 755 data/
chmod -R 755 logs/

# Check ownership
ls -la data/

# Change ownership if needed (Linux/macOS)
sudo chown -R $USER:$USER data/ logs/
```

---

### File Not Found Errors

#### Symptom
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/notes/0-System-Prompt.md'
```

#### Solution
```bash
# Create missing directories
mkdir -p data/notes data/memories data/nippo data/chat_logs logs

# Create system files
cat > data/notes/0-System-Prompt.md << EOF
# Alice System Prompt
You are Alice, a helpful AI assistant.
EOF

cat > data/notes/0-Memory.md << EOF
# Alice's Long-Term Memory
EOF

# Or restore from backup
git checkout data/notes/
```

## Plugin Issues

### Plugins Not Discovered

#### Symptom
```
[INFO] PluginManager: Discovered 0 plugins
```

#### Solution
```bash
# Check plugin directory exists
ls -la app/ai_analysis/plugins/

# Check for __init__.py
touch app/ai_analysis/plugins/__init__.py

# Verify plugin files
ls app/ai_analysis/plugins/*.py

# Check plugin syntax
python -m py_compile app/ai_analysis/plugins/tagging_plugin.py

# Check logs for import errors
grep "PluginManager" logs/errors.log.*
```

---

### Plugin Import Errors

#### Symptom
```
[ERROR] Failed to load plugin: tagging_plugin
ImportError: cannot import name 'BaseAnalysisPlugin'
```

#### Solution
```bash
# Check base plugin exists
ls app/ai_analysis/base_plugin.py

# Verify import path
python -c "from ai_analysis.base_plugin import BaseAnalysisPlugin; print('OK')"

# Check for circular imports
python -c "from ai_analysis.plugins.tagging_plugin import TaggingPlugin; print('OK')"

# Reinstall if corrupted
git checkout app/ai_analysis/
```

---

### Plugin Analysis Fails

#### Symptom
```
Analysis failed: Ollama connection error
```

#### Solution
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve

# Check model is installed
ollama list

# Pull model if missing
ollama pull gemma3:4b

# Test Ollama
ollama run gemma3:4b "Hello"
```

---

### Custom Plugin Not Working

#### Symptom
Custom plugin file created but not showing in UI

#### Checklist

- [ ] File is in `app/ai_analysis/plugins/` directory
- [ ] Filename ends with `.py`
- [ ] Class inherits from `BaseAnalysisPlugin`
- [ ] `__init__()` calls `super().__init__()`
- [ ] `analyze()` method implemented
- [ ] `analyze_async()` method implemented
- [ ] No syntax errors (`python -m py_compile plugin_file.py`)
- [ ] Application restarted after adding plugin

#### Debug
```bash
# Test plugin import
python -c "
from ai_analysis.plugins.my_plugin import MyPlugin
plugin = MyPlugin()
print(f'Plugin loaded: {plugin.name}')
result = plugin.analyze('test')
print(f'Analysis result: {result.success}')
"

# Check logs
grep "my_plugin" logs/app.log.*
```

## Alice Chat Problems

### Alice Not Responding

#### Symptom
Send message but no response from Alice

#### Solution
```bash
# Check API key
echo $GEMINI_API_KEY

# Test API key
python -c "
import os
from google import generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-pro')
response = model.generate_content('Hello')
print(response.text)
"

# Check logs
tail -f logs/alice_chat.log.*
tail -f logs/errors.log.*

# Check dialog logs
ls -lt logs/dialogs/ | head -10
cat logs/dialogs/dialog-*.json | jq .
```

---

### API Rate Limit Errors

#### Symptom
```
Error: 429 Resource has been exhausted (e.g. check quota)
```

#### Solution
```bash
# Check API quota at https://aistudio.google.com/

# Wait for quota reset (usually per minute)

# Implement rate limiting in code
# config/config.py
RATE_LIMIT_REQUESTS_PER_MINUTE = 10

# Use exponential backoff for retries
```

---

### Context Too Large

#### Symptom
```
Error: Token limit exceeded
```

#### Solution
```bash
# Reduce context in config/config.py
MAX_HISTORY_CHARS = 2000  # Reduced from 4000
MAX_MEMORY_CHARS = 1000   # Reduced from 2000

# Clear conversation history
# Use "Clear" button in UI

# Reduce 0-Memory.md size
# Edit data/notes/0-Memory.md
```

---

### System Prompt Not Loading

#### Symptom
Alice behaves differently than expected

#### Solution
```bash
# Check system prompt file
cat data/notes/0-System-Prompt.md

# Verify file encoding (should be UTF-8)
file data/notes/0-System-Prompt.md

# Check file permissions
ls -l data/notes/0-System-Prompt.md

# Check logs for loading errors
grep "System.*Prompt" logs/alice_chat.log.*

# Recreate from template
cat > data/notes/0-System-Prompt.md << 'EOF'
# Alice System Prompt

You are Alice, an intelligent and helpful AI assistant.

## Personality
- Friendly and approachable
- Clear and concise
- Helpful and informative

## Guidelines
- Always be respectful
- Provide accurate information
- Ask for clarification when needed
EOF
```

## Performance Issues

### Slow Startup

#### Symptom
Application takes >10 seconds to start

#### Solution
```bash
# Check plugin discovery time
grep "PluginManager" logs/performance.log.*

# Disable unused plugins temporarily
# Move plugins out of plugins/ directory

# Check database size
ls -lh data/anc_db.json

# Optimize database if large
# Backup and recreate database

# Check for network delays
# Verify Ollama and Gemini API connectivity
```

---

### High Memory Usage

#### Symptom
Application uses >500MB RAM

#### Solution
```bash
# Check memory usage
top -p $(pgrep -f "python app/main.py")

# Reduce workers in .env
MAX_WORKERS=2

# Clear conversation history regularly

# Check for memory leaks
# Run with memory profiler
pip install memory_profiler
python -m memory_profiler app/main.py
```

---

### Slow Analysis

#### Symptom
AI analysis takes very long (>30 seconds)

#### Solution
```bash
# Check Ollama model size
ollama list

# Use smaller model
ollama pull gemma3:4b  # Smaller than 8b or 9b

# Check Ollama performance
time ollama run gemma3:4b "Test"

# Increase timeout
# In plugin: self.timeout_seconds = 120

# Check system resources
top
free -h
df -h
```

---

### UI Freezing

#### Symptom
UI becomes unresponsive during operations

#### Solution
```bash
# Ensure async operations are used
# Check async_operations.py integration

# Increase async workers
# .env: MAX_WORKERS=4

# Use progress callbacks
# All long operations should use progress_callback

# Check logs for blocking operations
grep "WARN" logs/performance.log.*
```

## Database Issues

### Database Corrupted

#### Symptom
```
json.decoder.JSONDecodeError: Expecting value
```

#### Solution
```bash
# Backup corrupted database
cp data/anc_db.json data/anc_db.json.backup

# Try to repair JSON
python -c "
import json
with open('data/anc_db.json', 'r') as f:
    data = json.load(f)  # This will show where corruption is
"

# If repair fails, restore from backup
cp data/anc_db.json.backup data/anc_db.json

# Or create fresh database
rm data/anc_db.json
# Restart application
```

---

### Database Lock

#### Symptom
```
Error: Database is locked
```

#### Solution
```bash
# Check for multiple instances
ps aux | grep "python app/main.py"

# Kill duplicate instances
pkill -f "python app/main.py"

# Wait a moment, then restart
sleep 2
python app/main.py
```

---

### Missing Records

#### Symptom
Files exist but not showing in database

#### Solution
```bash
# Refresh database
# Use "Refresh Files" button in UI

# Or rebuild database
python -c "
from app.logic import AppLogic
from app.state_manager import AppState
logic = AppLogic(AppState())
logic.refresh_all_files()
"

# Check database content
python -c "
from tinydb import TinyDB
db = TinyDB('data/anc_db.json')
print(f'Total records: {len(db.all())}')
for record in db.all()[:5]:
    print(record)
"
```

## UI Issues

### Window Won't Open

#### Symptom
No window appears when starting application

#### Solution
```bash
# Check Flet version
pip show flet

# Update Flet
pip install --upgrade flet

# Check display environment (Linux)
echo $DISPLAY
export DISPLAY=:0

# Check logs
tail -f logs/ui_events.log.*
```

---

### UI Elements Not Updating

#### Symptom
Changes not reflected in UI

#### Solution
```python
# Ensure update() is called
component.update()

# Check observer registration
app_state.add_observer("event_type", callback)

# Force page update
page.update()

# Check logs for observer errors
grep "Observer" logs/errors.log.*
```

---

### UI Layout Broken

#### Symptom
UI elements overlapping or misaligned

#### Solution
```bash
# Clear cache and restart
rm -rf .flet/
python app/main.py

# Check Flet version compatibility
pip install flet==0.28.0

# Update UI components
git checkout app/ui_components.py
git checkout app/ui_redesign.py
```

## Getting Help

### Before Asking for Help

Please gather this information:

1. **System Information**
   ```bash
   python --version
   pip list
   uname -a  # Linux/macOS
   ver       # Windows
   ```

2. **Error Logs**
   ```bash
   tail -100 logs/errors.log.* > error_log.txt
   tail -100 logs/app.log.* > app_log.txt
   ```

3. **Configuration**
   ```bash
   # Redact sensitive information!
   cat .env | sed 's/GEMINI_API_KEY=.*/GEMINI_API_KEY=***/' > config.txt
   ```

4. **Steps to Reproduce**
   - What were you doing?
   - What did you expect to happen?
   - What actually happened?

### Where to Get Help

1. **Documentation**
   - Read relevant docs in `docs/` directory
   - Check [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)
   - Review [API_REFERENCE.md](./API_REFERENCE.md)

2. **GitHub Issues**
   - Search existing issues: https://github.com/yourusername/project-anc/issues
   - Create new issue with template
   - Provide all information from "Before Asking for Help"

3. **Debug Mode**
   ```bash
   # Enable debug logging
   export ANC_DEBUG=1  # Linux/macOS
   set ANC_DEBUG=1     # Windows

   # Run application
   python app/main.py

   # Check detailed logs
   tail -f logs/app.log.*
   ```

4. **Community**
   - Check discussions
   - Review pull requests for similar issues
   - Join community chat (if available)

### Creating a Bug Report

Include:

1. **Environment**
   - OS and version
   - Python version
   - Package versions
   - Project A.N.C. version

2. **Issue Description**
   - Clear, concise summary
   - Expected behavior
   - Actual behavior
   - Steps to reproduce

3. **Logs and Screenshots**
   - Relevant log excerpts
   - Screenshots if UI issue
   - Error messages

4. **Attempted Solutions**
   - What you've tried
   - Results of troubleshooting steps

### Template

```markdown
**Environment:**
- OS: Ubuntu 22.04
- Python: 3.12.0
- Project A.N.C.: v3.0.0

**Description:**
[Clear description of the issue]

**Expected Behavior:**
[What you expected to happen]

**Actual Behavior:**
[What actually happened]

**Steps to Reproduce:**
1. [First step]
2. [Second step]
3. [...]

**Logs:**
```
[Relevant log excerpts]
```

**Attempted Solutions:**
- [What you tried]
- [Results]

**Additional Context:**
[Any other relevant information]
```

---

**Version:** 3.0.0
**Last Updated:** October 1, 2025
**Maintained By:** Project A.N.C. Team
