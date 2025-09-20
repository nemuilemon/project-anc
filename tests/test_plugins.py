"""Unit tests for specific AI analysis plugins.

Tests the concrete implementations of tagging and summarization plugins.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from threading import Event
import time

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_analysis.plugins.tagging_plugin import TaggingPlugin
from ai_analysis.plugins.summarization_plugin import SummarizationPlugin


class TestTaggingPlugin(unittest.TestCase):
    """Test cases for TaggingPlugin."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.plugin = TaggingPlugin()
    
    def test_plugin_properties(self):
        """Test plugin basic properties."""
        self.assertEqual(self.plugin.name, "tagging")
        self.assertIn("tags", self.plugin.description.lower())
        self.assertEqual(self.plugin.version, "1.0.0")
        self.assertTrue(self.plugin.requires_ollama)
    
    def test_validate_content_valid(self):
        """Test content validation with valid content."""
        self.assertTrue(self.plugin.validate_content("This is a long enough content for tagging"))
        self.assertTrue(self.plugin.validate_content("   Some content with spaces   "))
    
    def test_validate_content_invalid(self):
        """Test content validation with invalid content."""
        self.assertFalse(self.plugin.validate_content(""))
        self.assertFalse(self.plugin.validate_content("   "))
        self.assertFalse(self.plugin.validate_content("short"))  # Too short
        self.assertFalse(self.plugin.validate_content(None))
    
    @patch('ai_analysis.plugins.tagging_plugin.ollama.generate')
    def test_analyze_success(self, mock_generate):
        """Test successful tag analysis."""
        # Mock Ollama response
        mock_generate.return_value = {
            'response': 'Python, Programming, AI, Machine Learning'
        }
        
        result = self.plugin.analyze("This is a test content about Python programming and AI")
        
        self.assertTrue(result.success)
        self.assertIn("tags", result.data)
        self.assertEqual(result.data["tags"], ['Python', 'Programming', 'AI', 'Machine Learning'])
        self.assertIn("抽出しました", result.message)
        self.assertEqual(result.plugin_name, "tagging")
        self.assertGreater(result.processing_time, 0)
    
    @patch('ai_analysis.plugins.tagging_plugin.ollama.generate')
    def test_analyze_ollama_error(self, mock_generate):
        """Test analysis when Ollama raises exception."""
        mock_generate.side_effect = Exception("Connection error")
        
        result = self.plugin.analyze("Test content")
        
        self.assertFalse(result.success)
        self.assertIn("エラー", result.message)
    
    @patch('ai_analysis.plugins.tagging_plugin.ollama.generate')
    def test_analyze_long_response_retry(self, mock_generate):
        """Test handling of long responses with retry logic."""
        # First call returns long response, second returns good response
        mock_generate.side_effect = [
            {'response': 'A' * 150},  # Too long
            {'response': 'Python, AI, Test'}  # Good response
        ]
        
        result = self.plugin.analyze("Test content")
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["tags"], ['Python', 'AI', 'Test'])
        self.assertEqual(mock_generate.call_count, 2)
    
    @patch('ai_analysis.plugins.tagging_plugin.ollama.generate')
    def test_analyze_max_retries_exceeded(self, mock_generate):
        """Test when maximum retries are exceeded."""
        # Always return long responses
        mock_generate.return_value = {'response': 'A' * 150}
        
        result = self.plugin.analyze("Test content")
        
        self.assertTrue(result.success)  # Empty tags is still success
        self.assertEqual(result.data["tags"], [])
        self.assertEqual(mock_generate.call_count, 3)  # max_retries
    
    @patch('ai_analysis.plugins.tagging_plugin.ollama.generate')
    def test_analyze_async_with_cancellation(self, mock_generate):
        """Test async analysis with cancellation."""
        cancel_event = Event()
        cancel_event.set()  # Cancel immediately
        
        result = self.plugin.analyze_async("Test content", cancel_event=cancel_event)
        
        self.assertFalse(result.success)
        self.assertIn("中止", result.message)
        mock_generate.assert_not_called()
    
    @patch('ai_analysis.plugins.tagging_plugin.ollama.generate')
    def test_analyze_async_with_progress(self, mock_generate):
        """Test async analysis with progress tracking."""
        mock_generate.return_value = {
            'response': 'Python, AI, Test'
        }
        
        progress_calls = []
        
        def progress_callback(progress):
            progress_calls.append(progress)
        
        result = self.plugin.analyze_async("Test content", progress_callback=progress_callback)
        
        self.assertTrue(result.success)
        self.assertGreater(len(progress_calls), 0)
        self.assertEqual(max(progress_calls), 100)  # Should reach 100%


class TestSummarizationPlugin(unittest.TestCase):
    """Test cases for SummarizationPlugin."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.plugin = SummarizationPlugin()
    
    def test_plugin_properties(self):
        """Test plugin basic properties."""
        self.assertEqual(self.plugin.name, "summarization")
        self.assertIn("summar", self.plugin.description.lower())
        self.assertEqual(self.plugin.version, "1.0.0")
    
    def test_validate_content(self):
        """Test content validation."""
        # Valid content (>= 100 chars)
        long_content = "This is a long content that should be suitable for summarization. " * 2
        self.assertTrue(self.plugin.validate_content(long_content))
        
        # Invalid content (< 100 chars)
        self.assertFalse(self.plugin.validate_content("Short content"))
        self.assertFalse(self.plugin.validate_content(""))
    
    @patch('ai_analysis.plugins.summarization_plugin.ollama.generate')
    def test_analyze_brief_summary(self, mock_generate):
        """Test brief summary generation."""
        mock_generate.return_value = {
            'response': 'This is a brief summary of the content.'
        }
        
        content = "Long content to be summarized. " * 10
        result = self.plugin.analyze(content, summary_type="brief", max_sentences=2)
        
        self.assertTrue(result.success)
        self.assertIn("summary", result.data)
        self.assertEqual(result.data["summary"], "This is a brief summary of the content.")
        self.assertEqual(result.data["summary_type"], "brief")
        self.assertIn("original_length", result.data)
        self.assertIn("compression_ratio", result.data)
    
    @patch('ai_analysis.plugins.summarization_plugin.ollama.generate')
    def test_analyze_detailed_summary(self, mock_generate):
        """Test detailed summary generation."""
        mock_generate.return_value = {
            'response': 'This is a detailed summary with more information about the content.'
        }
        
        content = "Long content to be summarized. " * 10
        result = self.plugin.analyze(content, summary_type="detailed", max_sentences=3)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["summary_type"], "detailed")
        mock_generate.assert_called_once()
        
        # Check that the prompt contains "詳細に"
        call_args = mock_generate.call_args[1]
        self.assertIn("詳細に", call_args['prompt'])
    
    @patch('ai_analysis.plugins.summarization_plugin.ollama.generate')
    def test_analyze_bullet_summary(self, mock_generate):
        """Test bullet point summary generation."""
        mock_generate.return_value = {
            'response': '・First point\n・Second point\n・Third point'
        }
        
        content = "Long content to be summarized. " * 10
        result = self.plugin.analyze(content, summary_type="bullet", max_sentences=3)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["summary_type"], "bullet")
        
        # Check that the prompt contains "箇条書き"
        call_args = mock_generate.call_args[1]
        self.assertIn("箇条書き", call_args['prompt'])
    
    @patch('ai_analysis.plugins.summarization_plugin.ollama.generate')
    def test_analyze_long_summary_shortening(self, mock_generate):
        """Test automatic shortening of too-long summaries."""
        # First call returns long summary, second returns shortened version
        mock_generate.side_effect = [
            {'response': 'A' * 600},  # Too long
            {'response': 'Shortened summary'}  # Good length
        ]
        
        content = "Long content to be summarized. " * 10
        result = self.plugin.analyze(content)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["summary"], "Shortened summary")
        self.assertEqual(mock_generate.call_count, 2)



class TestPluginIntegration(unittest.TestCase):
    """Integration tests for plugin interactions."""
    
    def test_all_plugins_implement_interface(self):
        """Test that all plugins properly implement the base interface."""
        plugins = [TaggingPlugin(), SummarizationPlugin()]
        
        for plugin in plugins:
            # Test required methods exist
            self.assertTrue(hasattr(plugin, 'analyze'))
            self.assertTrue(hasattr(plugin, 'analyze_async'))
            self.assertTrue(hasattr(plugin, 'validate_content'))
            self.assertTrue(hasattr(plugin, 'get_config'))
            
            # Test basic properties
            self.assertIsInstance(plugin.name, str)
            self.assertIsInstance(plugin.description, str)
            self.assertIsInstance(plugin.version, str)
            
            # Test config structure
            config = plugin.get_config()
            required_keys = ["name", "description", "version", "requires_ollama"]
            for key in required_keys:
                self.assertIn(key, config)


if __name__ == '__main__':
    unittest.main()