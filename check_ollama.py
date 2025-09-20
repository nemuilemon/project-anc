#!/usr/bin/env python3
"""Check Ollama setup and available models."""

import sys
import os

# Add app directory to Python path
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
sys.path.insert(0, app_dir)

def check_ollama():
    """Check Ollama setup."""
    try:
        import ollama
        print("=== Ollama Setup Check ===")

        # Check if Ollama is running
        try:
            models = ollama.list()
            print("[OK] Ollama is running and accessible")

            model_list = models.get('models', [])
            print(f"[OK] Found {len(model_list)} models:")

            for model in model_list:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0)
                size_mb = size / (1024 * 1024) if size else 0
                print(f"  - {name} ({size_mb:.1f} MB)")

            # Check if llama3.2 specifically is available
            llama_models = [m for m in model_list if 'llama' in m.get('name', '').lower()]
            if llama_models:
                print(f"[OK] Found {len(llama_models)} Llama models")
                recommended_model = llama_models[0].get('name')
                print(f"[RECOMMENDATION] Use model: '{recommended_model}' instead of 'llama3.2'")
            else:
                print("[WARNING] No Llama models found")
                print("[SUGGESTION] Install a model with: ollama pull llama3.2")

        except Exception as e:
            print(f"[ERROR] Cannot connect to Ollama: {e}")
            print("[SUGGESTION] Make sure Ollama is running with: ollama serve")
            return False

        print("\n=== Testing Growth Analysis ===")
        print("The Growth Analysis feature will work with fallback test data even without Ollama.")
        print("For full AI-powered analysis, make sure Ollama is running with a suitable model.")

        return True

    except ImportError:
        print("[ERROR] Ollama Python package not found")
        print("[SUGGESTION] Install with: pip install ollama")
        return False

if __name__ == "__main__":
    success = check_ollama()
    if success:
        print("\n[SUCCESS] Ollama check completed!")
    else:
        print("\n[INFO] Growth Analysis will use test mode until Ollama is properly configured.")