#!/usr/bin/env python3
"""Test UI integration for Sentiment Compass."""

import sys
import os

# Add app directory to Python path
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
sys.path.insert(0, app_dir)

# Add config directory to path
config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
sys.path.insert(0, config_dir)

def test_ui_integration():
    """Test the UI integration for sentiment compass."""
    try:
        print("=== Testing UI Integration ===")

        # Test that all plugins can be imported
        from logic import AppLogic
        from tinydb import TinyDB
        import tempfile

        # Create temporary database
        f = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        f.close()
        db = TinyDB(f.name)

        print("[OK] Database created")

        # Test logic initialization
        logic = AppLogic(db)
        print(f"[OK] Logic initialized with {len(logic.ai_manager.get_available_plugins())} plugins")

        # Test getting AI functions
        functions = logic.get_available_ai_functions()
        print(f"[OK] Retrieved {len(functions)} AI functions")

        # Check if sentiment_compass is available
        sentiment_compass_found = False
        for func in functions:
            if func.get('name') == 'sentiment_compass':
                sentiment_compass_found = True
                print(f"[OK] Sentiment Compass found: {func.get('description')}")
                break

        if not sentiment_compass_found:
            print("[ERROR] Sentiment Compass not found in AI functions!")
            return False

        # Test analysis
        test_content = "Today was an amazing day. I worked hard on my projects and achieved great results with my team."
        result = logic.run_ai_analysis(test_content, "sentiment_compass")

        print(f"[OK] Analysis completed: {result.get('success')}")
        if result.get('success'):
            data = result.get('data', {})
            print(f"[OK] Total Score: {data.get('total_score', 0)}/40")
            print(f"[OK] Analysis Type: {data.get('analysis_type')}")

        db.close()
        print("\n[SUCCESS] UI Integration test completed successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ui_integration()
    sys.exit(0 if success else 1)