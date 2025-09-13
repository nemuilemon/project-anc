#!/usr/bin/env python3
"""
Test script for duplicate file error handling
"""

import sys
import os
from tinydb import TinyDB

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))

def test_duplicate_file_error():
    """Test duplicate file error handling."""
    try:
        from logic import AppLogic
        import config

        print("=" * 60)
        print("DUPLICATE FILE ERROR TEST")
        print("=" * 60)

        # Create temporary test database
        test_db = TinyDB('test_duplicate_db.json')
        app_logic = AppLogic(test_db)

        # Create test files to simulate conflict
        test_file_notes = os.path.join(config.NOTES_DIR, "test_duplicate.md")
        test_file_archive = os.path.join(config.ARCHIVE_DIR, "test_duplicate.md")

        print(f"Creating test files:")
        print(f"Notes: {test_file_notes}")
        print(f"Archive: {test_file_archive}")

        # Create test file in notes
        with open(test_file_notes, 'w', encoding='utf-8') as f:
            f.write("# Test File in Notes\nThis is a test file.")

        # Create test file in archive (same name)
        os.makedirs(config.ARCHIVE_DIR, exist_ok=True)
        with open(test_file_archive, 'w', encoding='utf-8') as f:
            f.write("# Test File in Archive\nThis is an existing archived file.")

        print(f"Notes file exists: {os.path.exists(test_file_notes)}")
        print(f"Archive file exists: {os.path.exists(test_file_archive)}")

        # Try to archive the notes file (should fail due to duplicate)
        print("\n--- Testing Archive with Duplicate Name ---")
        success, message = app_logic.archive_file(test_file_notes)
        print(f"Success: {success}")
        print(f"Error Message: {message}")

        # Expected: False, with detailed error message about duplicate

        # Test unarchive conflict too
        print("\n--- Testing Unarchive with Duplicate Name ---")
        # First, move the notes file out of the way
        temp_notes = test_file_notes + ".temp"
        os.rename(test_file_notes, temp_notes)

        # Try to unarchive (should fail because original file exists as .temp)
        os.rename(temp_notes, test_file_notes)  # Put it back
        success2, message2 = app_logic.unarchive_file(test_file_archive)
        print(f"Success: {success2}")
        print(f"Error Message: {message2}")

        # Cleanup
        if os.path.exists(test_file_notes):
            os.remove(test_file_notes)
        if os.path.exists(test_file_archive):
            os.remove(test_file_archive)
        test_db.close()
        if os.path.exists('test_duplicate_db.json'):
            os.remove('test_duplicate_db.json')

        print("\n[SUCCESS] Duplicate file error handling test completed!")
        print("Expected: Both operations should fail with clear error messages")
        return success is False and success2 is False  # Both should fail

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_duplicate_file_error()