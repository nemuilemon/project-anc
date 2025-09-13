"""Security utilities for Project A.N.C.

This module provides security-focused utilities for validating and sanitizing
file paths, filenames, and user inputs to prevent security vulnerabilities.
"""

import os
import re
from pathlib import Path
from typing import Tuple, Optional


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize a filename to prevent path traversal and invalid characters.
    
    Args:
        filename (str): The filename to sanitize
        max_length (int): Maximum allowed filename length
        
    Returns:
        str: Sanitized filename
        
    Raises:
        SecurityError: If filename is empty or contains only invalid characters
    """
    if not filename or not filename.strip():
        raise SecurityError("Filename cannot be empty")
    
    # Remove leading/trailing whitespace
    filename = filename.strip()
    
    # Remove or replace dangerous characters
    # Windows forbidden characters: < > : " | ? * \ /
    # Also remove null bytes and control characters
    forbidden_chars = r'[<>:"|?*\\/\x00-\x1f]'
    filename = re.sub(forbidden_chars, '_', filename)
    
    # Remove leading dots and spaces (Windows issue)
    filename = filename.lstrip('. ')
    
    # Check for Windows reserved names
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    name_without_ext = filename.rsplit('.', 1)[0].upper()
    if name_without_ext in reserved_names:
        filename = f"_{filename}"
    
    # Truncate if too long, preserving extension
    if len(filename) > max_length:
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            filename = name[:max_name_length] + '.' + ext
        else:
            filename = filename[:max_length]
    
    # Final check - ensure we still have a valid filename
    if not filename or filename.isspace():
        raise SecurityError("Filename becomes invalid after sanitization")
    
    return filename


def validate_file_path(file_path: str, allowed_base_dirs: list) -> Tuple[bool, str, Optional[str]]:
    """Validate that a file path is safe and within allowed directories.
    
    Args:
        file_path (str): The file path to validate
        allowed_base_dirs (list): List of allowed base directories
        
    Returns:
        Tuple[bool, str, Optional[str]]: (is_valid, message, normalized_path)
    """
    try:
        # Convert to absolute path and resolve any symlinks/relative components
        abs_path = Path(file_path).resolve()
        
        # Check if path is within any allowed base directory
        is_allowed = False
        for base_dir in allowed_base_dirs:
            try:
                base_path = Path(base_dir).resolve()
                abs_path.relative_to(base_path)
                is_allowed = True
                break
            except ValueError:
                continue
        
        if not is_allowed:
            return False, "File path is outside allowed directories", None
        
        return True, "Path is valid", str(abs_path)
        
    except (OSError, ValueError) as e:
        return False, f"Invalid file path: {str(e)}", None


def validate_search_input(search_text: str, max_length: int = 1000) -> Tuple[bool, str, Optional[str]]:
    """Validate search input to prevent injection attacks.
    
    Args:
        search_text (str): The search text to validate
        max_length (int): Maximum allowed search text length
        
    Returns:
        Tuple[bool, str, Optional[str]]: (is_valid, message, sanitized_text)
    """
    if not search_text:
        return True, "Empty search is valid", ""
    
    # Check length
    if len(search_text) > max_length:
        return False, f"Search text exceeds maximum length of {max_length}", None
    
    # Remove null bytes and excessive whitespace
    sanitized = search_text.replace('\x00', '').strip()
    
    # Check for potentially dangerous patterns
    dangerous_patterns = [
        r'\.\./',  # Path traversal
        r'\.\.\\',  # Path traversal (Windows)
        r'<script',  # Script injection
        r'javascript:',  # JavaScript URI
        r'data:',  # Data URI
        r'file:',  # File URI
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            return False, "Search contains potentially dangerous content", None
    
    return True, "Search input is valid", sanitized


def create_safe_directory(dir_path: str) -> Tuple[bool, str]:
    """Safely create a directory with proper error handling.
    
    Args:
        dir_path (str): Directory path to create
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True, f"Directory created: {dir_path}"
    except PermissionError:
        return False, f"Permission denied creating directory: {dir_path}"
    except OSError as e:
        return False, f"Error creating directory {dir_path}: {str(e)}"


def safe_file_operation(operation_type: str, file_path: str, content: str = None, allowed_dirs: list = None) -> Tuple[bool, str, Optional[str]]:
    """Perform file operations with security validation.
    
    Args:
        operation_type (str): Type of operation ('read', 'write', 'delete')
        file_path (str): Path to the file
        content (str, optional): Content to write (for write operations)
        allowed_dirs (list, optional): List of allowed directories
        
    Returns:
        Tuple[bool, str, Optional[str]]: (success, message, content_if_read)
    """
    if allowed_dirs:
        is_valid, msg, validated_path = validate_file_path(file_path, allowed_dirs)
        if not is_valid:
            return False, f"Security validation failed: {msg}", None
        file_path = validated_path
    
    try:
        if operation_type == 'read':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return True, "File read successfully", content
            
        elif operation_type == 'write':
            if content is None:
                return False, "No content provided for write operation", None
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "File written successfully", None
            
        elif operation_type == 'delete':
            os.remove(file_path)
            return True, "File deleted successfully", None
            
        else:
            return False, f"Unknown operation type: {operation_type}", None
            
    except PermissionError:
        return False, f"Permission denied: {file_path}", None
    except FileNotFoundError:
        return False, f"File not found: {file_path}", None
    except OSError as e:
        return False, f"File operation error: {str(e)}", None