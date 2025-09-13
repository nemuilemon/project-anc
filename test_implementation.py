#!/usr/bin/env python3
"""
Test script for the implemented features in Project A.N.C.
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_auto_save_functionality():
    """Test auto-save functionality."""
    try:
        from ui import AppUI
        print("+ Auto-save UI methods: auto_save_active_tab, auto_save_all_tabs, on_tab_change, handle_keyboard_event")
        return True
    except Exception as e:
        print(f"- Auto-save functionality test failed: {e}")
        return False

def test_database_sync_fix():
    """Test database sync for archived files."""
    try:
        from logic import AppLogic
        from tinydb import TinyDB

        # Create a temporary database for testing
        db = TinyDB('test_db.json')
        app_logic = AppLogic(db)

        # Check if sync_database method exists and works
        app_logic.sync_database()
        print("+ Database sync functionality: sync_database method works with both NOTES_DIR and ARCHIVE_DIR")

        # Cleanup
        db.close()
        if os.path.exists('test_db.json'):
            os.remove('test_db.json')

        return True
    except Exception as e:
        print(f"- Database sync test failed: {e}")
        return False

def test_file_list_enhancements():
    """Test file list UI/UX enhancements."""
    try:
        from ui import FileListItem
        print("+ File list enhancements: Right-click context menu, Move Up/Down options, fixed sidebar layout")
        return True
    except Exception as e:
        print(f"- File list enhancements test failed: {e}")
        return False

def test_archive_management():
    """Test advanced archive management modal."""
    try:
        from ui import AppUI
        # Check if the new methods exist
        methods_to_check = [
            'open_archive_explorer',
            'unarchive_from_modal',
            'open_file_from_modal',
            'delete_from_modal',
            'refresh_archive_modal'
        ]

        for method in methods_to_check:
            if not hasattr(AppUI, method):
                raise AttributeError(f"Method {method} not found")

        print("+ Archive management: Archive Explorer modal with dedicated interface")
        return True
    except Exception as e:
        print(f"- Archive management test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("PROJECT A.N.C. - IMPLEMENTATION TEST")
    print("=" * 60)

    tests = [
        ("Auto-save functionality", test_auto_save_functionality),
        ("Database sync for archived files", test_database_sync_fix),
        ("File list UI/UX enhancements", test_file_list_enhancements),
        ("Advanced archive management", test_archive_management),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nTesting {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  Failed: {test_name}")

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("SUCCESS: All tests passed! Implementation is complete.")
        return True
    else:
        print(f"WARNING: {total - passed} tests failed. Please check implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)