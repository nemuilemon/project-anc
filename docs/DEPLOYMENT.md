# Deployment Guide

**Version:** 3.0.0
**Last Updated:** October 1, 2025

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Development Deployment](#development-deployment)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Post-Deployment](#post-deployment)
8. [Troubleshooting](#troubleshooting)

## Overview

This guide covers deploying Project A.N.C. v3.0 in various environments.

### Deployment Options

- **Development**: Local development with hot-reload
- **Production**: Optimized production deployment
- **Docker**: Containerized deployment
- **Portable**: Standalone executable (future)

## Prerequisites

### System Requirements

**Minimum:**
- Python 3.12+
- 4GB RAM
- 2GB disk space
- Windows 10/11, macOS 11+, or Linux

**Recommended:**
- Python 3.12+
- 8GB RAM
- 5GB disk space
- SSD storage

### Required Software

1. **Python 3.12+**
   ```bash
   python --version  # Should be 3.12 or higher
   ```

2. **pip** (Python package manager)
   ```bash
   pip --version
   ```

3. **Git** (for version control)
   ```bash
   git --version
   ```

4. **Ollama** (for AI analysis)
   - Download from https://ollama.com/download
   - Install and run: `ollama serve`

### API Keys

1. **Google Gemini API Key**
   - Get from https://aistudio.google.com/app/apikey
   - Required for Alice chat functionality

## Development Deployment

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/project-anc.git
cd project-anc
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```txt
flet>=0.28.0
tinydb>=4.8.0
ollama>=0.1.7
google-generativeai>=1.38.0
python-dotenv>=1.0.0
```

### 4. Configure Environment

Create `.env` file:

```bash
# .env
GEMINI_API_KEY=your_gemini_api_key_here
OLLAMA_MODEL=gemma3:4b
GEMINI_MODEL=gemini-2.5-pro
```

### 5. Initialize Data Directories

```bash
# Windows
mkdir data\notes data\memories data\nippo data\chat_logs logs

# macOS/Linux
mkdir -p data/{notes,memories,nippo,chat_logs} logs
```

### 6. Create Initial Files

**data/notes/0-System-Prompt.md:**
```markdown
# Alice System Prompt

You are Alice, a helpful AI assistant.
```

**data/notes/0-Memory.md:**
```markdown
# Alice's Long-Term Memory

Important information Alice should remember.
```

### 7. Setup Ollama

```bash
# Pull required model
ollama pull gemma3:4b

# Verify installation
ollama list
```

### 8. Run Application

```bash
python app/main.py
```

### 9. Verify Installation

- Check logs in `logs/app.log.*`
- Verify plugins discovered: "Discovered 3 plugins"
- Test Alice chat: Send a message
- Test AI analysis: Run tagging on sample text

## Production Deployment

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/project-anc.git
cd project-anc
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

### 2. Install Production Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Production Environment

**.env:**
```bash
# Production settings
GEMINI_API_KEY=your_production_api_key
OLLAMA_MODEL=gemma3:4b
GEMINI_MODEL=gemini-2.5-pro

# Optional: Production-specific settings
LOG_LEVEL=INFO
MAX_WORKERS=4
```

### 4. Production Optimizations

**config/config.py adjustments:**
```python
# Production settings
DEBUG = False
LOG_LEVEL = "INFO"
MAX_WORKERS = 4
ENABLE_PROFILING = False
```

### 5. Setup System Service (Linux)

**/etc/systemd/system/project-anc.service:**
```ini
[Unit]
Description=Project A.N.C.
After=network.target

[Service]
Type=simple
User=anc
WorkingDirectory=/opt/project-anc
Environment="PATH=/opt/project-anc/.venv/bin"
ExecStart=/opt/project-anc/.venv/bin/python app/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable project-anc
sudo systemctl start project-anc
sudo systemctl status project-anc
```

### 6. Setup Log Rotation

**/etc/logrotate.d/project-anc:**
```
/opt/project-anc/logs/*.log* {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 anc anc
    sharedscripts
    postrotate
        systemctl reload project-anc > /dev/null 2>&1 || true
    endscript
}
```

## Docker Deployment

### 1. Create Dockerfile

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/notes data/memories data/nippo data/chat_logs logs

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (if needed for web interface)
EXPOSE 8080

# Run application
CMD ["python", "app/main.py"]
```

### 2. Create Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  project-anc:
    build: .
    container_name: project-anc
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OLLAMA_MODEL=gemma3:4b
      - GEMINI_MODEL=gemini-2.5-pro
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    restart: unless-stopped

volumes:
  ollama_data:
```

### 3. Build and Run

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Initialize Ollama Model

```bash
# Pull model in ollama container
docker-compose exec ollama ollama pull gemma3:4b

# Verify
docker-compose exec ollama ollama list
```

## Environment Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | None | Yes |
| `OLLAMA_MODEL` | Ollama model name | gemma3:4b | No |
| `GEMINI_MODEL` | Gemini model name | gemini-2.5-pro | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `MAX_WORKERS` | Max async workers | 4 | No |
| `DEBUG` | Debug mode | False | No |

### Configuration Files

**config/config.py:**
```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
NOTES_DIR = DATA_DIR / "notes"
MEMORIES_DIR = DATA_DIR / "memories"
NIPPO_DIR = DATA_DIR / "nippo"
CHAT_LOGS_DIR = DATA_DIR / "chat_logs"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "anc_db.json"

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

# Application Settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# AI Analysis Settings
MAX_HISTORY_CHARS = 4000
MAX_MEMORY_CHARS = 2000

# Ensure directories exist
for directory in [DATA_DIR, NOTES_DIR, MEMORIES_DIR, NIPPO_DIR,
                  CHAT_LOGS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
```

## Post-Deployment

### 1. Health Checks

Create health check script:

**scripts/health_check.py:**
```python
import sys
import requests
from pathlib import Path

def check_health():
    checks = []

    # Check directories exist
    required_dirs = ['data/notes', 'data/memories', 'logs']
    for dir_path in required_dirs:
        exists = Path(dir_path).exists()
        checks.append(('Directory: ' + dir_path, exists))

    # Check Ollama
    try:
        response = requests.get('http://localhost:11434/api/tags')
        ollama_ok = response.status_code == 200
    except:
        ollama_ok = False
    checks.append(('Ollama API', ollama_ok))

    # Check environment variables
    import os
    api_key = os.getenv('GEMINI_API_KEY') is not None
    checks.append(('GEMINI_API_KEY', api_key))

    # Print results
    all_ok = True
    for check, result in checks:
        status = '✓' if result else '✗'
        print(f"{status} {check}")
        if not result:
            all_ok = False

    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(check_health())
```

Run health check:
```bash
python scripts/health_check.py
```

### 2. Monitoring

**Monitor logs:**
```bash
# Watch application logs
tail -f logs/app.log.*

# Watch error logs
tail -f logs/errors.log.*

# Check plugin loading
grep "PluginManager" logs/app.log.* | tail -20
```

**Monitor system resources:**
```bash
# CPU and memory usage
top -p $(pgrep -f "python app/main.py")

# Disk usage
df -h
du -sh data/ logs/
```

### 3. Backup Strategy

**Backup script:**

**scripts/backup.sh:**
```bash
#!/bin/bash

BACKUP_DIR="/backups/project-anc"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup data and logs
tar -czf "$BACKUP_FILE" \
    data/ \
    logs/ \
    .env

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete

echo "Backup created: $BACKUP_FILE"
```

**Schedule with cron:**
```bash
# Run daily at 2 AM
0 2 * * * /opt/project-anc/scripts/backup.sh
```

### 4. Performance Tuning

**Optimize Python:**
```bash
# Use optimized Python
python -O app/main.py
```

**Increase workers:**
```bash
# .env
MAX_WORKERS=8  # Increase for more concurrent operations
```

**Database optimization:**
```python
# config/config.py
# Use in-memory caching
ENABLE_CACHING = True
CACHE_SIZE = 1000
```

## Troubleshooting

### Application Won't Start

**Check Python version:**
```bash
python --version  # Must be 3.12+
```

**Check dependencies:**
```bash
pip list
pip check
```

**Check logs:**
```bash
tail -100 logs/app.log.*
tail -100 logs/errors.log.*
```

### Plugin Discovery Issues

**Verify plugin directory:**
```bash
ls -la app/ai_analysis/plugins/
```

**Check for import errors:**
```bash
python -c "from ai_analysis.plugins.tagging_plugin import TaggingPlugin; print('OK')"
```

**Check logs:**
```bash
grep "PluginManager" logs/app.log.* | tail -20
```

### Ollama Connection Errors

**Check Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

**Check model installed:**
```bash
ollama list
```

**Pull model if missing:**
```bash
ollama pull gemma3:4b
```

### Gemini API Errors

**Verify API key:**
```bash
echo $GEMINI_API_KEY
```

**Test API key:**
```bash
python -c "
import os
from google import generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
print('API key valid')
"
```

### Performance Issues

**Check system resources:**
```bash
top
free -h
df -h
```

**Reduce workers:**
```bash
# .env
MAX_WORKERS=2
```

**Enable profiling:**
```bash
# .env
ENABLE_PROFILING=true
```

### Database Issues

**Backup database:**
```bash
cp data/anc_db.json data/anc_db.json.backup
```

**Reset database:**
```bash
rm data/anc_db.json
# Restart application to create new database
```

## Security Considerations

### 1. API Key Protection

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Set restrictive permissions
chmod 600 .env
```

### 2. File Permissions

```bash
# Restrict data directory
chmod 700 data/
chmod 700 logs/

# Restrict config files
chmod 600 .env
chmod 600 config/config.py
```

### 3. Network Security

- Run on localhost only by default
- Use firewall rules to restrict access
- Consider VPN for remote access

### 4. Update Dependencies

```bash
# Check for vulnerabilities
pip list --outdated

# Update packages
pip install --upgrade -r requirements.txt
```

---

**Version:** 3.0.0
**Last Updated:** October 1, 2025
**Maintained By:** Project A.N.C. Team
