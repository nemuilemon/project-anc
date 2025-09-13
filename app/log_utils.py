"""Utilities for logging to log.md file."""

import os
from datetime import datetime
import threading

_log_lock = threading.Lock()

def log_to_md(message: str, category: str = "ERROR", log_file: str = "log.md"):
    """
    Log a message to log.md with timestamp and proper formatting.
    
    Args:
        message: The message to log
        category: Category of the log (ERROR, INFO, WARNING, etc.)
        log_file: Path to the log file (default: log.md)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the log entry
    log_entry = f"**{timestamp} [{category}]** {message}\n\n"
    
    # Thread-safe logging
    with _log_lock:
        try:
            # Check if file exists
            if not os.path.exists(log_file):
                # Create initial file with header
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("# Project A.N.C. Development Log\n\n")
            
            # Append the log entry
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            # Fallback to console if file logging fails
            print(f"Failed to log to {log_file}: {e}")
            print(f"Original message: [{category}] {message}")

def log_error(message: str):
    """Log an error message."""
    log_to_md(message, "ERROR")

def log_info(message: str):
    """Log an info message."""
    log_to_md(message, "INFO")

def log_warning(message: str):
    """Log a warning message."""
    log_to_md(message, "WARNING")