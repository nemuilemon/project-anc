#!/usr/bin/env python3
"""Configure Ollama models for Project A.N.C."""

import sys
import os

# Add app and config directories to Python path
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
sys.path.insert(0, app_dir)
sys.path.insert(0, config_dir)

def configure_models():
    """Configure models for sentiment compass."""
    try:
        import ollama
        import config

        print("=== Project A.N.C. Model Configuration ===")
        print()

        # Check current configuration
        current_model = getattr(config, 'SENTIMENT_COMPASS_MODEL', 'gemma3:4b')
        print(f"Current Sentiment Compass Model: {current_model}")

        # List available models
        try:
            models_info = ollama.list()
            model_list = models_info.get('models', [])

            if model_list:
                print(f"\nAvailable Ollama Models ({len(model_list)} found):")
                for i, model in enumerate(model_list, 1):
                    name = model.get('name', 'Unknown')
                    size = model.get('size', 0)
                    size_mb = size / (1024 * 1024) if size else 0
                    modified = model.get('modified_at', 'Unknown')
                    print(f"  {i}. {name} ({size_mb:.1f} MB)")

                print(f"\nModel Descriptions:")
                descriptions = getattr(config, 'MODEL_DESCRIPTIONS', {})
                for model_name, description in descriptions.items():
                    print(f"  - {model_name}: {description}")

                # Interactive selection
                print(f"\nTo change the model, edit config/config.py:")
                print(f"  SENTIMENT_COMPASS_MODEL = \"your_preferred_model\"")
                print(f"\nRecommended models:")
                print(f"  - \"auto\": Auto-select the first available model")
                if model_list:
                    first_available = model_list[0].get('name')
                    print(f"  - \"{first_available}\": Use first available model")

            else:
                print("\n[WARNING] No Ollama models found!")
                print("[SUGGESTION] Install a model with: ollama pull gemma3:4b")

        except Exception as e:
            print(f"\n[ERROR] Cannot connect to Ollama: {e}")
            print("[SUGGESTION] Make sure Ollama is running with: ollama serve")

        print(f"\n=== Configuration Instructions ===")
        print(f"1. Edit config/config.py")
        print(f"2. Change SENTIMENT_COMPASS_MODEL to your preferred model")
        print(f"3. Available options:")
        print(f"   - \"auto\" (auto-select)")
        print(f"   - \"gemma3:4b\" (recommended)")
        print(f"   - Any model name from the list above")
        print(f"4. Restart the application")

        return True

    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Configuration failed: {e}")
        return False

if __name__ == "__main__":
    success = configure_models()
    sys.exit(0 if success else 1)