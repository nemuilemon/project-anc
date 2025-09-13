# Deployment Guide

## Production Deployment

### 🚀 Quick Production Setup

#### System Requirements
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Python**: 3.12+ 
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB for application + content storage
- **Network**: Optional (for Ollama model downloads)

#### Production Installation

```bash
# 1. Clone repository
git clone https://github.com/your-username/project-anc.git
cd project-anc

# 2. Create production virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 4. Install production dependencies
pip install -r requirements.txt

# 5. Install and configure Ollama
# Download from https://ollama.com/download
ollama pull llama3.1:8b  # Or your preferred model

# 6. Configure application
cp config.py.example config.py
# Edit config.py with your settings

# 7. Initialize application
python main.py
```

### 🔧 Production Configuration

#### Environment Configuration (`config.py`)

```python
# Production settings
PRODUCTION_MODE = True
DEBUG_MODE = False

# File Management
NOTES_DIR = "/opt/project-anc/data/notes"
ARCHIVE_DIR = "/opt/project-anc/data/notes/.archive"
DATABASE_PATH = "/opt/project-anc/data/anc_db.json"

# AI Configuration
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_HOST = "localhost:11434"

# Security Settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = [".md", ".txt"]
ENABLE_SECURITY_LOGGING = True

# Performance Settings
MAX_FILES_DISPLAY = 1000
AUTO_SAVE_INTERVAL = 30
ENABLE_PERFORMANCE_MONITORING = True

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_ROTATION_SIZE = 10 * 1024 * 1024  # 10MB
LOG_RETENTION_DAYS = 30
```

#### Directory Structure

**Development/Local Structure (Current):**
```
project-anc/
├── main.py                 # Application entry point
├── ui.py                   # User interface components
├── logic.py                # Business logic
├── handlers.py             # Event handling
├── security.py             # Security utilities
├── async_operations.py     # Background processing
├── logger.py               # Logging system
├── config.py               # Configuration
├── log_utils.py            # Log utilities
├── ai_analysis/            # AI analysis system
│   ├── __init__.py
│   ├── base_plugin.py
│   ├── manager.py
│   └── plugins/
├── docs/                   # Documentation
├── tests/                  # Test files
├── notes/                  # User notes (created at runtime)
├── logs/                   # Log files (created at runtime)
├── anc_db.json             # Database (created at runtime)
├── requirements.txt        # Dependencies
└── .venv/                  # Virtual environment
```

**Production Server Structure (Recommended):**
```
/opt/project-anc/
├── app/                    # Application code
│   ├── main.py
│   ├── ui.py
│   ├── logic.py
│   ├── handlers.py
│   ├── security.py
│   ├── async_operations.py
│   ├── logger.py
│   ├── config.py
│   ├── log_utils.py
│   └── ai_analysis/
├── data/                   # Data directory
│   ├── notes/              # User notes
│   ├── anc_db.json         # Database
│   └── backups/            # Automated backups
├── logs/                   # Log files
├── config/                 # Configuration files
└── .venv/                  # Virtual environment
```

### 🐳 Docker Deployment

#### Dockerfile

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data/notes

# Expose ports
EXPOSE 8080 11434

# Set environment variables
ENV PYTHONPATH=/app
ENV NOTES_DIR=/app/data/notes
ENV DATABASE_PATH=/app/data/anc_db.json

# Start script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  project-anc:
    build: .
    ports:
      - "8080:8080"
      - "11434:11434"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PRODUCTION_MODE=true
      - DEBUG_MODE=false
      - OLLAMA_HOST=localhost:11434
    restart: unless-stopped
```

#### Docker Commands

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Scale service
docker-compose up -d --scale project-anc=2

# Update application
docker-compose pull
docker-compose up -d

# Backup data
docker run --rm -v project-anc_data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data
```

### ☁️ Cloud Deployment

#### AWS EC2 Deployment

```bash
# 1. Launch EC2 instance (t3.medium recommended)
# 2. Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# 3. Clone and setup application
git clone https://github.com/your-username/project-anc.git
cd project-anc
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b

# 5. Configure systemd service
sudo cp deployment/project-anc.service /etc/systemd/system/
sudo systemctl enable project-anc
sudo systemctl start project-anc
```

#### Systemd Service (`project-anc.service`)

```ini
[Unit]
Description=Project A.N.C. AI Note Taking System
After=network.target

[Service]
Type=simple
User=project-anc
WorkingDirectory=/opt/project-anc
Environment=PYTHONPATH=/opt/project-anc
ExecStart=/opt/project-anc/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 🔒 Security Configuration

#### SSL/TLS Setup

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Firewall Configuration

```bash
# UFW setup
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 11434  # Ollama (if external access needed)
```

#### Application Security

```python
# In config.py
SECURITY_SETTINGS = {
    "enable_rate_limiting": True,
    "max_requests_per_minute": 60,
    "enable_csrf_protection": True,
    "secure_session_cookies": True,
    "force_https": True,
    "content_security_policy": True
}
```

### 📊 Monitoring and Logging

#### Log Management

```bash
# Logrotate configuration
sudo cat > /etc/logrotate.d/project-anc << EOF
/opt/project-anc/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 project-anc project-anc
    postrotate
        systemctl reload project-anc
    endscript
}
EOF
```



#### Prometheus Metrics (Optional)

```python
# In main.py, add metrics endpoint
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('project_anc_requests_total', 'Total requests')
REQUEST_DURATION = Histogram('project_anc_request_duration_seconds', 'Request duration')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### 🔄 Backup and Recovery

#### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/project-anc"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp /opt/project-anc/data/anc_db.json $BACKUP_DIR/anc_db_$DATE.json

# Backup notes
tar -czf $BACKUP_DIR/notes_$DATE.tar.gz /opt/project-anc/data/notes/

# Backup configuration
cp /opt/project-anc/config.py $BACKUP_DIR/config_$DATE.py

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.json" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### Cron Job for Automated Backups

```bash
# Add to crontab
0 2 * * * /opt/project-anc/scripts/backup.sh >> /var/log/project-anc-backup.log 2>&1
```

#### Recovery Procedure

```bash
# 1. Stop service
sudo systemctl stop project-anc

# 2. Restore database
cp /opt/backups/project-anc/anc_db_YYYYMMDD_HHMMSS.json /opt/project-anc/data/anc_db.json

# 3. Restore notes
tar -xzf /opt/backups/project-anc/notes_YYYYMMDD_HHMMSS.tar.gz -C /

# 4. Restore configuration
cp /opt/backups/project-anc/config_YYYYMMDD_HHMMSS.py /opt/project-anc/config.py

# 5. Start service
sudo systemctl start project-anc
```

### 🚀 Performance Optimization

#### Application Optimization

```python
# In config.py
PERFORMANCE_SETTINGS = {
    "enable_caching": True,
    "cache_ttl": 300,  # 5 minutes
    "enable_compression": True,
    "max_concurrent_ai_requests": 2,
    "database_connection_pool": 5
}
```

#### System Optimization

```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize Python
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# Memory optimization
echo 'vm.swappiness=10' >> /etc/sysctl.conf
```

### 📱 Multi-Instance Deployment

#### Load Balancer Configuration

```nginx
upstream project_anc {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
}

server {
    listen 80;
    location / {
        proxy_pass http://project_anc;
    }
}
```

#### Shared Storage Setup

```bash
# NFS setup for shared notes directory
sudo apt install nfs-kernel-server
echo "/opt/project-anc/data 192.168.1.0/24(rw,sync,no_subtree_check)" >> /etc/exports
sudo systemctl restart nfs-kernel-server
```

### 🧪 Staging Environment

#### Staging Configuration

```python
# config_staging.py
STAGING_MODE = True
DEBUG_MODE = True
NOTES_DIR = "/opt/project-anc-staging/data/notes"
DATABASE_PATH = "/opt/project-anc-staging/data/anc_db.json"
OLLAMA_MODEL = "gemma2:2b"  # Smaller model for faster testing
```

#### CI/CD Pipeline (.github/workflows/deploy.yml)

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python test_basic_integration.py
        python test_working_components.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to production
      run: |
        ssh ${{ secrets.PROD_HOST }} "cd /opt/project-anc && git pull && systemctl restart project-anc"
```

### 📋 Production Checklist

Before deploying to production:

- [ ] All tests passing
- [ ] Configuration reviewed and updated
- [ ] SSL certificates configured
- [ ] Firewall rules in place
- [ ] Backup system configured
- [ ] Monitoring setup complete
- [ ] Log rotation configured
- [ ] Performance testing completed
- [ ] Security scan performed
- [ ] Documentation updated
- [ ] Rollback plan prepared

### 🆘 Troubleshooting Production Issues

#### Common Production Issues

1. **High Memory Usage**
   - Monitor with `htop` or `ps aux`
   - Check for memory leaks in logs
   - Restart service if necessary

2. **AI Service Unresponsive**
   - Check Ollama status: `systemctl status ollama`
   - Restart Ollama: `systemctl restart ollama`
   - Check GPU/CPU resources

3. **Database Corruption**
   - Stop service immediately
   - Restore from latest backup
   - Check file system integrity

4. **Network Issues**
   - Check firewall rules
   - Verify SSL certificate validity
   - Test DNS resolution

Remember: Always test deployments in staging environment first, maintain regular backups, and have a rollback plan ready.