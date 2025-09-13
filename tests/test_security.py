#!/usr/bin/env python3
"""Test script for Project A.N.C. security improvements.

This script tests the security features implemented in Phase 1: Foundation Hardening.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security import (
    sanitize_filename, 
    validate_file_path, 
    validate_search_input, 
    safe_file_operation,
    create_safe_directory,
    SecurityError
)

def test_filename_sanitization():
    """Test filename sanitization functionality."""
    print("Testing filename sanitization...")
    
    test_cases = [
        # (input, expected_valid, description)
        ("normal_file.md", True, "Normal filename"),
        ("file with spaces.md", True, "Filename with spaces"),
        ("file<>with|bad*chars.md", True, "Filename with forbidden characters"),
        ("CON.md", True, "Windows reserved name"),
        ("", False, "Empty filename"),
        ("   ", False, "Whitespace only filename"),
        ("file/with\\path.md", True, "Filename with path separators"),
        ("very" + "x" * 300 + ".md", True, "Very long filename"),
        ("..\\..\\dangerous.md", True, "Path traversal attempt"),
    ]
    
    passed = 0
    failed = 0
    
    for input_name, should_succeed, description in test_cases:
        try:
            result = sanitize_filename(input_name)
            if should_succeed:
                print(f"PASS {description}: '{input_name}' -> '{result}'")
                passed += 1
            else:
                print(f"FAIL {description}: Expected failure but got '{result}'")
                failed += 1
        except SecurityError:
            if not should_succeed:
                print(f"PASS {description}: Correctly rejected '{input_name}'")
                passed += 1
            else:
                print(f"FAIL {description}: Unexpected failure for '{input_name}'")
                failed += 1
        except Exception as e:
            print(f"FAIL {description}: Unexpected error: {e}")
            failed += 1
    
    print(f"Filename sanitization tests: {passed} passed, {failed} failed\n")
    return failed == 0

def test_path_validation():
    """Test file path validation functionality."""
    print("Testing path validation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        allowed_dirs = [temp_dir]
        
        test_cases = [
            # (path, should_succeed, description)
            (os.path.join(temp_dir, "valid.txt"), True, "Valid path within allowed directory"),
            (os.path.join(temp_dir, "subdir", "file.txt"), True, "Valid path in subdirectory"),
            ("/etc/passwd", False, "Path outside allowed directories"),
            ("C:\\Windows\\System32\\cmd.exe", False, "Dangerous system path"),
            (temp_dir + "/../outside.txt", False, "Path traversal attempt"),
        ]
        
        passed = 0
        failed = 0
        
        for test_path, should_succeed, description in test_cases:
            try:
                is_valid, message, normalized_path = validate_file_path(test_path, allowed_dirs)
                if should_succeed and is_valid:
                    print(f"PASS {description}: Path validated successfully")
                    passed += 1
                elif not should_succeed and not is_valid:
                    print(f"PASS {description}: Path correctly rejected")
                    passed += 1
                else:
                    print(f"FAIL {description}: Expected {should_succeed}, got {is_valid}")
                    failed += 1
            except Exception as e:
                print(f"FAIL {description}: Unexpected error: {e}")
                failed += 1
        
        print(f"Path validation tests: {passed} passed, {failed} failed\n")
        return failed == 0

def test_search_input_validation():
    """Test search input validation functionality."""
    print("Testing search input validation...")
    
    test_cases = [
        # (input, should_succeed, description)
        ("normal search", True, "Normal search text"),
        ("", True, "Empty search"),
        ("search with spaces", True, "Search with spaces"),
        ("../etc/passwd", False, "Path traversal in search"),
        ("<script>alert('xss')</script>", False, "Script injection attempt"),
        ("javascript:alert(1)", False, "JavaScript URI"),
        ("x" * 2000, False, "Overly long search text"),
        ("file:///etc/passwd", False, "File URI attempt"),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, should_succeed, description in test_cases:
        try:
            is_valid, message, sanitized = validate_search_input(input_text)
            if should_succeed and is_valid:
                print(f"PASS {description}: Search input validated successfully")
                passed += 1
            elif not should_succeed and not is_valid:
                print(f"PASS {description}: Search input correctly rejected")
                passed += 1
            else:
                print(f"FAIL {description}: Expected {should_succeed}, got {is_valid}")
                failed += 1
        except Exception as e:
            print(f"FAIL {description}: Unexpected error: {e}")
            failed += 1
    
    print(f"Search input validation tests: {passed} passed, {failed} failed\n")
    return failed == 0

def test_safe_file_operations():
    """Test safe file operation functionality."""
    print("Testing safe file operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        allowed_dirs = [temp_dir]
        test_file = os.path.join(temp_dir, "test.txt")
        test_content = "Hello, World!"
        
        passed = 0
        failed = 0
        
        # Test write operation
        try:
            success, message, _ = safe_file_operation('write', test_file, test_content, allowed_dirs)
            if success:
                print("PASS Safe write operation: File written successfully")
                passed += 1
            else:
                print(f"FAIL Safe write operation: {message}")
                failed += 1
        except Exception as e:
            print(f"FAIL Safe write operation: Unexpected error: {e}")
            failed += 1
        
        # Test read operation
        try:
            success, message, content = safe_file_operation('read', test_file, allowed_dirs=allowed_dirs)
            if success and content == test_content:
                print("PASS Safe read operation: File read successfully")
                passed += 1
            else:
                print(f"FAIL Safe read operation: {message}")
                failed += 1
        except Exception as e:
            print(f"FAIL Safe read operation: Unexpected error: {e}")
            failed += 1
        
        # Test delete operation
        try:
            success, message, _ = safe_file_operation('delete', test_file, allowed_dirs=allowed_dirs)
            if success:
                print("PASS Safe delete operation: File deleted successfully")
                passed += 1
            else:
                print(f"FAIL Safe delete operation: {message}")
                failed += 1
        except Exception as e:
            print(f"FAIL Safe delete operation: Unexpected error: {e}")
            failed += 1
        
        print(f"Safe file operation tests: {passed} passed, {failed} failed\n")
        return failed == 0

def test_directory_creation():
    """Test safe directory creation functionality."""
    print("Testing safe directory creation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_subdir = os.path.join(temp_dir, "subdir", "nested")
        
        passed = 0
        failed = 0
        
        try:
            success, message = create_safe_directory(test_subdir)
            if success and os.path.exists(test_subdir):
                print("PASS Safe directory creation: Directory created successfully")
                passed += 1
            else:
                print(f"FAIL Safe directory creation: {message}")
                failed += 1
        except Exception as e:
            print(f"FAIL Safe directory creation: Unexpected error: {e}")
            failed += 1
        
        print(f"Directory creation tests: {passed} passed, {failed} failed\n")
        return failed == 0

def main():
    """Run all security tests."""
    print("=== Project A.N.C. Security Test Suite ===\n")
    
    tests = [
        test_filename_sanitization,
        test_path_validation,
        test_search_input_validation,
        test_safe_file_operations,
        test_directory_creation,
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                total_passed += 1
            else:
                total_failed += 1
        except Exception as e:
            print(f"Test {test_func.__name__} failed with exception: {e}")
            total_failed += 1
    
    print("=== Test Results ===")
    print(f"Test suites passed: {total_passed}")
    print(f"Test suites failed: {total_failed}")
    
    if total_failed == 0:
        print("SUCCESS: All security tests passed!")
        return 0
    else:
        print("FAILURE: Some security tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())