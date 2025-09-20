#!/usr/bin/env python3
"""Test script for the Sentiment Compass plugin."""

import sys
import os

# Add app directory to Python path
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
sys.path.insert(0, app_dir)

# Add config directory to path
config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
sys.path.insert(0, config_dir)

def test_sentiment_compass():
    """Test the Sentiment Compass functionality."""
    try:
        from ai_analysis.plugins.minimal_test import TestSentimentCompassPlugin

        print("=== Testing Sentiment Compass Plugin ===")
        plugin = TestSentimentCompassPlugin()

        print(f"[OK] Plugin Name: {plugin.name}")
        print(f"[OK] Plugin Description: {plugin.description}")
        print(f"[OK] Plugin Version: {plugin.version}")

        # Test analysis
        test_content = "今日は素晴らしい一日でした。新しいプロジェクトに取り組み、多くのことを学びました。チームと協力して課題を解決し、大きな成果を上げることができました。"
        result = plugin.analyze(test_content)

        print(f"[OK] Analysis Success: {result.success}")
        print(f"[OK] Analysis Type: {result.data.get('analysis_type')}")
        print(f"[OK] Total Score: {result.data.get('total_score')}/40")

        axes_scores = result.data.get('axes_scores', {})
        print("\n=== Axis Scores ===")
        for axis, score in axes_scores.items():
            print(f"  {axis}: {score}/10")

        print(f"\n[OK] Compass Summary: {result.data.get('compass_summary')}")
        print(f"[OK] Processing Time: {result.processing_time:.3f}s")

        print("\n[SUCCESS] Sentiment Compass plugin test completed successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_sentiment_compass()
    sys.exit(0 if success else 1)