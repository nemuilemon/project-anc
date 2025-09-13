#!/usr/bin/env python3
"""
Test script specifically for archive functionality
"""

import sys
import os
from tinydb import TinyDB

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))

def test_archive_functionality():
    """Test the archive functionality directly."""
    try:
        from logic import AppLogic
        import config

        print("=" * 60)
        print("ARCHIVE FUNCTIONALITY TEST")
        print("=" * 60)

        # Create temporary test database
        test_db = TinyDB('test_archive_db.json')
        app_logic = AppLogic(test_db)

        print(f"NOTES_DIR: {config.NOTES_DIR}")
        print(f"ARCHIVE_DIR: {config.ARCHIVE_DIR}")

        # Check if directories exist
        print(f"Notes dir exists: {os.path.exists(config.NOTES_DIR)}")
        print(f"Archive dir exists: {os.path.exists(config.ARCHIVE_DIR)}")

        # Find a test file to archive
        if os.path.exists(config.NOTES_DIR):
            test_files = [f for f in os.listdir(config.NOTES_DIR) if f.endswith('.md')]
            if test_files:
                test_file = os.path.join(config.NOTES_DIR, test_files[0])
                print(f"Testing with file: {test_file}")
                print(f"File exists: {os.path.exists(test_file)}")

                # Test archive operation
                print("\n--- Testing Archive Operation ---")
                success, message = app_logic.archive_file(test_file)
                print(f"Result: {success}")
                print(f"Message: {message}")

                if success:
                    archive_path = os.path.join(config.ARCHIVE_DIR, test_files[0])
                    print(f"Archive file exists: {os.path.exists(archive_path)}")

                    # Test unarchive operation
                    print("\n--- Testing Unarchive Operation ---")
                    success2, message2 = app_logic.unarchive_file(archive_path)
                    print(f"Result: {success2}")
                    print(f"Message: {message2}")

                    if success2:
                        print(f"Original file restored: {os.path.exists(test_file)}")

            else:
                print("No .md files found in notes directory for testing")
        else:
            print("Notes directory not found")

        # Cleanup
        test_db.close()
        if os.path.exists('test_archive_db.json'):
            os.remove('test_archive_db.json')

        print("\nTest completed!")
        return True

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_archive_functionality()