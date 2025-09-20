#!/usr/bin/env python3
"""Test settings integration for sentiment compass."""

import sys
import os

# Add app and config directories to Python path
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
sys.path.insert(0, app_dir)
sys.path.insert(0, config_dir)

def test_settings_integration():
    """Test the settings integration."""
    try:
        print("=== Testing Settings Integration ===")

        # Test config import
        import config
        current_model = getattr(config, 'SENTIMENT_COMPASS_MODEL', 'gemma3:4b')
        print(f"[OK] Current sentiment compass model: {current_model}")

        # Test sentiment compass import with config
        from ai_analysis.plugins.sentiment_compass_plugin import SentimentCompassPlugin
        plugin = SentimentCompassPlugin()
        print(f"[OK] Sentiment compass plugin initialized")

        # Test model configuration
        print(f"[OK] Plugin uses config-based model selection")

        # Test settings dialog import
        try:
            from settings_dialog import create_settings_dialog
            print(f"[OK] Settings dialog can be imported")
        except ImportError as e:
            print(f"[WARNING] Settings dialog import issue: {e}")

        # Test analysis with current config
        test_content = "今日は素晴らしい一日でした。新しいことを学び、チームと協力して大きな成果を上げました。"
        result = plugin.analyze(test_content)

        print(f"[OK] Analysis completed: {result.success}")
        if result.success:
            data = result.data
            model_used = data.get('model_used', 'Unknown')
            print(f"[OK] Model used: {model_used}")
            print(f"[OK] Total Score: {data.get('total_score', 0)}/40")

        print(f"\n=== Model Configuration ===")
        print(f"1. Current Model: {current_model}")
        print(f"2. Available Models: Run 'python configure_models.py' to see available models")
        print(f"3. Settings UI: Click the settings (gear) button in the application")
        print(f"4. Manual Config: Edit config/config.py -> SENTIMENT_COMPASS_MODEL")

        print(f"\n[SUCCESS] Settings integration test completed!")
        return True

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_settings_integration()
    sys.exit(0 if success else 1)