"""Comprehensive logging system for Project A.N.C.

This module provides a centralized logging system that outputs application
activity logs to files for troubleshooting and monitoring purposes.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class AppLogger:
    """Centralized logger for Project A.N.C.
    
    This class sets up and manages all logging for the application,
    including file operations, UI events, errors, and system activities.
    """
    
    def __init__(self, log_dir: str = "logs", app_name: str = "ProjectANC"):
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create different log files for different purposes
        self.log_files = {
            'main': self.log_dir / 'app.log',
            'file_ops': self.log_dir / 'file_operations.log',
            'ui_events': self.log_dir / 'ui_events.log',
            'errors': self.log_dir / 'errors.log',
            'security': self.log_dir / 'security.log',
            'performance': self.log_dir / 'performance.log'
        }
        
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Set up different loggers for different purposes."""
        
        # Common formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # Main application logger
        self.main_logger = logging.getLogger(f"{self.app_name}.main")
        self.main_logger.setLevel(logging.INFO)
        
        main_handler = logging.FileHandler(self.log_files['main'], encoding='utf-8')
        main_handler.setFormatter(formatter)
        self.main_logger.addHandler(main_handler)
        
        # File operations logger
        self.file_ops_logger = logging.getLogger(f"{self.app_name}.file_ops")
        self.file_ops_logger.setLevel(logging.INFO)
        
        file_ops_handler = logging.FileHandler(self.log_files['file_ops'], encoding='utf-8')
        file_ops_handler.setFormatter(formatter)
        self.file_ops_logger.addHandler(file_ops_handler)
        
        # UI events logger
        self.ui_logger = logging.getLogger(f"{self.app_name}.ui")
        self.ui_logger.setLevel(logging.INFO)
        
        ui_handler = logging.FileHandler(self.log_files['ui_events'], encoding='utf-8')
        ui_handler.setFormatter(formatter)
        self.ui_logger.addHandler(ui_handler)
        
        # Error logger
        self.error_logger = logging.getLogger(f"{self.app_name}.error")
        self.error_logger.setLevel(logging.ERROR)
        
        error_handler = logging.FileHandler(self.log_files['errors'], encoding='utf-8')
        error_handler.setFormatter(formatter)
        self.error_logger.addHandler(error_handler)
        
        # Security events logger
        self.security_logger = logging.getLogger(f"{self.app_name}.security")
        self.security_logger.setLevel(logging.WARNING)
        
        security_handler = logging.FileHandler(self.log_files['security'], encoding='utf-8')
        security_handler.setFormatter(formatter)
        self.security_logger.addHandler(security_handler)
        
        # Performance logger
        self.perf_logger = logging.getLogger(f"{self.app_name}.performance")
        self.perf_logger.setLevel(logging.INFO)
        
        perf_handler = logging.FileHandler(self.log_files['performance'], encoding='utf-8')
        perf_handler.setFormatter(formatter)
        self.perf_logger.addHandler(perf_handler)
        
        # Console logging for development
        if os.getenv('ANC_DEBUG', '').lower() in ('1', 'true', 'yes'):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            
            self.main_logger.addHandler(console_handler)
            self.error_logger.addHandler(console_handler)
    
    def log_app_start(self):
        """Log application startup."""
        self.main_logger.info("=== Project A.N.C. Application Started ===")
        self.main_logger.info(f"Python version: {sys.version}")
        self.main_logger.info(f"Working directory: {os.getcwd()}")
        self.perf_logger.info("Application startup initiated")
    
    def log_app_shutdown(self):
        """Log application shutdown."""
        self.main_logger.info("=== Project A.N.C. Application Shutdown ===")
        self.perf_logger.info("Application shutdown completed")
    
    def log_file_operation(self, operation: str, file_path: str, success: bool, details: str = ""):
        """Log file operations (read, write, delete, etc.)."""
        status = "SUCCESS" if success else "FAILED"
        message = f"File {operation}: {file_path} - {status}"
        if details:
            message += f" - {details}"
        
        if success:
            self.file_ops_logger.info(message)
        else:
            self.file_ops_logger.error(message)
    
    def log_ui_event(self, event_type: str, component: str, details: str = ""):
        """Log UI events and user interactions."""
        message = f"UI Event: {event_type} on {component}"
        if details:
            message += f" - {details}"
        
        self.ui_logger.info(message)
    
    def log_error(self, error: Exception, context: str = "", additional_info: str = ""):
        """Log errors with full context."""
        import traceback
        
        message = f"Error in {context}: {str(error)}"
        if additional_info:
            message += f" - Additional info: {additional_info}"
        
        self.error_logger.error(message)
        self.error_logger.error(f"Traceback: {traceback.format_exc()}")
    
    def log_security_event(self, event_type: str, details: str, severity: str = "WARNING"):
        """Log security-related events."""
        message = f"Security Event [{severity}]: {event_type} - {details}"
        
        if severity == "ERROR":
            self.security_logger.error(message)
        elif severity == "CRITICAL":
            self.security_logger.critical(message)
        else:
            self.security_logger.warning(message)
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """Log performance metrics."""
        message = f"Performance: {operation} took {duration:.3f}s"
        if details:
            message += f" - {details}"
        
        # Log slow operations as warnings
        if duration > 5.0:  # 5 seconds threshold
            self.perf_logger.warning(f"SLOW OPERATION: {message}")
        elif duration > 1.0:  # 1 second threshold
            self.perf_logger.info(f"MODERATE: {message}")
        else:
            self.perf_logger.debug(message)
    
    def log_database_operation(self, operation: str, table: str, success: bool, details: str = ""):
        """Log database operations."""
        status = "SUCCESS" if success else "FAILED"
        message = f"Database {operation} on {table}: {status}"
        if details:
            message += f" - {details}"
        
        if success:
            self.main_logger.info(message)
        else:
            self.main_logger.error(message)
    
    def log_ai_operation(self, operation: str, model: str, success: bool, duration: float, details: str = ""):
        """Log AI/ML operations."""
        status = "SUCCESS" if success else "FAILED"
        message = f"AI Operation: {operation} using {model} - {status} ({duration:.2f}s)"
        if details:
            message += f" - {details}"
        
        if success:
            self.main_logger.info(message)
            if duration > 10.0:  # Long AI operations
                self.perf_logger.warning(f"SLOW AI OPERATION: {message}")
        else:
            self.main_logger.error(message)
    
    def log_async_operation(self, operation_id: str, operation_type: str, status: str, details: str = ""):
        """Log asynchronous operations."""
        message = f"Async Operation [{operation_id}]: {operation_type} - {status}"
        if details:
            message += f" - {details}"
        
        if status in ["STARTED", "COMPLETED"]:
            self.main_logger.info(message)
        elif status in ["FAILED", "CANCELLED"]:
            self.main_logger.warning(message)
        else:
            self.main_logger.debug(message)
    
    def get_log_summary(self) -> dict:
        """Get a summary of log file sizes and recent activity."""
        summary = {}
        
        for log_type, log_file in self.log_files.items():
            if log_file.exists():
                stat = log_file.stat()
                summary[log_type] = {
                    'size_bytes': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'exists': True
                }
            else:
                summary[log_type] = {'exists': False}
        
        return summary
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up log files older than specified days."""
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        cleaned_files = []
        for log_type, log_file in self.log_files.items():
            if log_file.exists() and log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_files.append(str(log_file))
                    self.main_logger.info(f"Cleaned up old log file: {log_file}")
                except Exception as e:
                    self.error_logger.error(f"Failed to cleanup log file {log_file}: {e}")
        
        return cleaned_files


# Global logger instance
app_logger = AppLogger()


# Convenience functions for easy logging throughout the application
def log_info(message: str, logger_type: str = "main"):
    """Log an info message."""
    getattr(app_logger, f"{logger_type}_logger").info(message)

def log_error(error: Exception, context: str = ""):
    """Log an error with context."""
    app_logger.log_error(error, context)

def log_file_op(operation: str, file_path: str, success: bool, details: str = ""):
    """Log a file operation."""
    app_logger.log_file_operation(operation, file_path, success, details)

def log_ui_event(event_type: str, component: str, details: str = ""):
    """Log a UI event."""
    app_logger.log_ui_event(event_type, component, details)

def log_security(event_type: str, details: str, severity: str = "WARNING"):
    """Log a security event."""
    app_logger.log_security_event(event_type, details, severity)

def log_performance(operation: str, duration: float, details: str = ""):
    """Log performance metrics."""
    app_logger.log_performance(operation, duration, details)


# Context manager for performance logging
class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, operation_name: str, details: str = ""):
        self.operation_name = operation_name
        self.details = details
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now().timestamp()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = datetime.now().timestamp() - self.start_time
            log_performance(self.operation_name, duration, self.details)