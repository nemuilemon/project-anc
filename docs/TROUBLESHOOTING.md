# Troubleshooting Guide

## Common Issues and Solutions

### 🔥 Critical Issues

#### Application Won't Start

**Error: "ModuleNotFoundError"**
```bash
# Solution: Install dependencies
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Error: "Permission denied"**
```bash
# Solution: Check file permissions
chmod +x main.py
# Or run with python explicitly
python main.py
```

#### Database Issues

**Error: "Could not create database"**
- Check write permissions in project directory
- Ensure `notes` directory exists and is writable
- Verify no other processes are using `anc_db.json`

**Error: "Database corrupted"**
```bash
# Backup and recreate database
cp anc_db.json anc_db.json.backup
rm anc_db.json
# Restart application to recreate clean database
```

### 🤖 AI Analysis Issues

#### Ollama Connection Problems

**Error: "Failed to connect to Ollama"**
```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve

# If not installed, install from https://ollama.com/download
```

**Error: "Model not found"**
```bash
# Pull the required model
ollama pull llama3.1:8b

# Or check available models
ollama list

# Update config.py if using different model
OLLAMA_MODEL = "your-model-name"
```

#### AI Analysis Fails Silently

**Check these items:**
1. Ollama service is running: `ollama serve`
2. Model is available: `ollama list`
3. Content is not empty or too short
4. Check error logs in `logs/errors.log`

**Enable debug logging:**
```python
# In config.py, add:
DEBUG_MODE = True
LOG_LEVEL = "DEBUG"
```

#### Long AI Processing Times

**Normal processing times:**
- Tagging: 2-5 seconds
- Summarization: 3-8 seconds  
- Sentiment: 2-4 seconds

**If taking longer than 30 seconds:**
- Check system resources (CPU/Memory)
- Try smaller content chunks
- Consider using faster model (e.g., gemma2:2b)
- Check Ollama logs: `ollama logs`

### 📁 File Management Issues

#### Files Not Appearing

**Check these items:**
1. Files are in correct directory (`notes/` by default)
2. Files have allowed extensions (`.md`, `.txt`)
3. Files are not in `.archive` subdirectory (unless showing archived files)
4. Refresh the file list (Ctrl+R or restart app)

#### Cannot Save Files

**Error: "Permission denied"**
- Check write permissions on `notes` directory
- Ensure file is not locked by another application
- Check available disk space

**Error: "File name invalid"**
- Avoid special characters: `< > : " | ? * /`
- Don't use reserved names: `CON`, `PRN`, `AUX`, etc.
- Keep filename length under 250 characters

#### Search Not Working

**If search returns no results:**
- Check search term spelling
- Try partial matches instead of exact phrases
- Clear search and try again
- Restart application to refresh file index

### 🎨 UI Issues

#### Interface Elements Missing

**Dropdown menus not showing:**
- Check window size (resize to larger)
- Try switching tabs or refreshing
- Check for console errors (F12 in debug mode)

**Buttons not responding:**
- Wait for any ongoing operations to complete
- Check progress indicators
- Try clicking different areas of the button

#### Text Not Displaying Properly

**Encoding issues:**
- Ensure files are saved as UTF-8
- Check content language settings
- Verify system font support for characters used

### ⚡ Performance Issues

#### Slow Startup

**Application takes >10 seconds to start:**
- Check file count in `notes` directory (limit: ~1000 files)
- Scan for very large files (limit: 10MB per file)
- Check available system memory
- Consider archiving old files

#### High Memory Usage

**Application using >500MB RAM:**
- Check for memory leaks in error logs
- Restart application periodically
- Reduce number of open tabs
- Archive unused files

### 🔒 Security Issues

#### Path-Related Errors

**Error: "Path not allowed"**
- Ensure files are within allowed directories
- Check `ALLOWED_DIRS` in config.py
- Avoid using absolute paths or `../` patterns

**Error: "Filename contains invalid characters"**
- Remove special characters from filenames
- Use alphanumeric characters and basic punctuation
- Check filename length (<250 characters)

### 🧪 Testing Issues

#### Tests Failing

**Virtual environment tests fail:**
```bash
# Ensure virtual environment is clean
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python test_basic_integration.py
```

**Import errors in tests:**
```bash
# Check Python path
echo $PYTHONPATH

# Run from project root directory
cd /path/to/project-anc
python test_basic_integration.py
```

### 🔌 Plugin Development Issues

#### Plugin Not Loading

**Error: "Plugin not found"**
- Check plugin file location: `ai_analysis/plugins/`
- Verify plugin class name matches file name
- Ensure plugin is registered in `__init__.py`
- Check for syntax errors: `python -c "from ai_analysis.plugins.your_plugin import YourPlugin"`

#### Plugin Analysis Fails

**Common issues:**
- Plugin `analyze()` method not implemented
- Missing required parameters
- Error in custom analysis logic
- Check plugin logs in error log files

### 📱 Platform-Specific Issues

#### Windows Issues

**Error: "Cannot execute .bat file"**
```cmd
# Use Command Prompt instead of PowerShell
cmd.exe
test_in_venv.bat
```

**Path separator issues:**
- Use forward slashes `/` or `os.path.join()`
- Avoid hardcoded backslashes `\`

#### macOS Issues

**Error: "Permission denied" on startup**
```bash
# Grant permissions
chmod +x main.py
xattr -dr com.apple.quarantine /path/to/project-anc
```

#### Linux Issues

**Missing dependencies:**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-tk python3-dev

# For some distributions, install additional packages
sudo apt-get install python3-pip python3-venv
```

## 🆘 Getting Help

### Debug Information to Collect

When reporting issues, include:

1. **System Information:**
   - Operating System and version
   - Python version: `python --version`
   - Flet version: `pip list | grep flet`

2. **Application Information:**
   - Project A.N.C. version
   - Error message (exact text)
   - Steps to reproduce

3. **Log Files:**
   - `logs/errors.log` (if exists)
   - `logs/app.log` (recent entries)
   - Console output

4. **Configuration:**
   - `config.py` settings (remove sensitive data)
   - Ollama version: `ollama version`
   - Available models: `ollama list`

### Enabling Debug Mode

```python
# In config.py, add these lines:
DEBUG_MODE = True
LOG_LEVEL = "DEBUG"
VERBOSE_ERRORS = True

# Run application with debug output
python main.py --debug
```

### Log Analysis

**Check these log files for clues:**
- `logs/errors.log` - Application errors and exceptions
- `logs/app.log` - General application events
- `logs/performance.log` - Performance metrics and timing
- `logs/ui_events.log` - User interface events
- `logs/security.log` - Security-related events

### Emergency Recovery

**If application completely broken:**
```bash
# 1. Backup your data
cp -r notes/ notes_backup/
cp anc_db.json anc_db.json.backup

# 2. Clean installation
rm -rf .venv/
rm anc_db.json
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Restart application
python main.py

# 4. If needed, restore notes manually
```

### Community Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check all docs/ files for detailed info
- **Plugin Examples**: See existing plugins for reference implementations
- **Testing**: Run test suite to validate installation

### Still Having Issues?

If none of these solutions work:

1. Create a [GitHub Issue](https://github.com/your-repo/issues) with:
   - Detailed problem description
   - Steps to reproduce
   - System information
   - Error messages and log files

2. Check existing issues for similar problems

3. Consider running in a fresh virtual environment

4. Try the latest version from the repository

Remember: Most issues are related to environment setup, missing dependencies, or configuration problems. The troubleshooting steps above solve 95% of common issues.