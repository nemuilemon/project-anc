"""Unit tests for the base AI analysis plugin interface.

Tests the abstract base class and data structures used by all AI analysis plugins.
"""

import unittest
from unittest.mock import Mock, patch
import time
from threading import Event

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult


class MockPlugin(BaseAnalysisPlugin):
    """Mock plugin implementation for testing base functionality."""
    
    def __init__(self):
        super().__init__("mock", "Mock plugin for testing", "1.0.0")
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        if content == "error":
            raise ValueError("Mock error")
        if content == "empty":
            return self._create_error_result("Empty content")
        
        return self._create_success_result(
            {"result": f"analyzed: {content}"},
            "Analysis successful",
            0.1
        )
    
    def analyze_async(self, content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
        if self._check_cancellation(cancel_event):
            return self._create_error_result("Analysis cancelled")
        
        if progress_callback:
            progress_callback(50)
        
        time.sleep(0.01)  # Simulate processing
        
        if progress_callback:
            progress_callback(100)
        
        return self.analyze(content, **kwargs)


class TestAnalysisResult(unittest.TestCase):
    """Test cases for AnalysisResult data structure."""
    
    def test_analysis_result_creation(self):
        """Test creating AnalysisResult with required fields."""
        result = AnalysisResult(
            success=True,
            data={"tags": ["test", "example"]},
            message="Success",
            processing_time=1.5,
            plugin_name="test_plugin"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["tags"], ["test", "example"])
        self.assertEqual(result.message, "Success")
        self.assertEqual(result.processing_time, 1.5)
        self.assertEqual(result.plugin_name, "test_plugin")
        self.assertEqual(result.metadata, {})
    
    def test_analysis_result_with_metadata(self):
        """Test creating AnalysisResult with metadata."""
        metadata = {"error_type": "ValidationError", "retry_count": 2}
        result = AnalysisResult(
            success=False,
            data={},
            message="Validation failed",
            metadata=metadata
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.metadata, metadata)


class TestBaseAnalysisPlugin(unittest.TestCase):
    """Test cases for BaseAnalysisPlugin abstract base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.plugin = MockPlugin()
    
    def test_plugin_initialization(self):
        """Test plugin initialization with basic properties."""
        self.assertEqual(self.plugin.name, "mock")
        self.assertEqual(self.plugin.description, "Mock plugin for testing")
        self.assertEqual(self.plugin.version, "1.0.0")
        self.assertTrue(self.plugin.requires_ollama)
        self.assertEqual(self.plugin.max_retries, 3)
        self.assertEqual(self.plugin.timeout_seconds, 60)
    
    def test_get_config(self):
        """Test getting plugin configuration."""
        config = self.plugin.get_config()
        
        expected_keys = ["name", "description", "version", "requires_ollama", "max_retries", "timeout_seconds"]
        for key in expected_keys:
            self.assertIn(key, config)
        
        self.assertEqual(config["name"], "mock")
        self.assertEqual(config["description"], "Mock plugin for testing")
    
    def test_validate_content_valid(self):
        """Test content validation with valid content."""
        self.assertTrue(self.plugin.validate_content("This is valid content"))
        self.assertTrue(self.plugin.validate_content("   Valid with spaces   "))
    
    def test_validate_content_invalid(self):
        """Test content validation with invalid content."""
        self.assertFalse(self.plugin.validate_content(""))
        self.assertFalse(self.plugin.validate_content("   "))
        self.assertFalse(self.plugin.validate_content(None))
    
    def test_analyze_success(self):
        """Test successful analysis."""
        result = self.plugin.analyze("test content")
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["result"], "analyzed: test content")
        self.assertEqual(result.message, "Analysis successful")
        self.assertEqual(result.plugin_name, "mock")
    
    def test_analyze_error(self):
        """Test analysis with error."""
        result = self.plugin.analyze("error")
        
        self.assertFalse(result.success)
        self.assertEqual(result.data, {})
        self.assertIn("error", result.message.lower())
    
    def test_analyze_custom_error(self):
        """Test analysis with custom error result."""
        result = self.plugin.analyze("empty")
        
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Empty content")
        self.assertEqual(result.plugin_name, "mock")
    
    def test_analyze_async_success(self):
        """Test successful async analysis."""
        progress_calls = []
        
        def progress_callback(progress):
            progress_calls.append(progress)
        
        result = self.plugin.analyze_async("test content", progress_callback=progress_callback)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["result"], "analyzed: test content")
        self.assertGreater(len(progress_calls), 0)  # Should have progress updates
    
    def test_analyze_async_cancellation(self):
        """Test async analysis cancellation."""
        cancel_event = Event()
        cancel_event.set()  # Cancel immediately
        
        result = self.plugin.analyze_async("test content", cancel_event=cancel_event)
        
        self.assertFalse(result.success)
        self.assertIn("cancelled", result.message.lower())
    
    def test_create_success_result(self):
        """Test creating success result."""
        data = {"test": "value"}
        message = "Test success"
        processing_time = 1.23
        
        result = self.plugin._create_success_result(data, message, processing_time)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data, data)
        self.assertEqual(result.message, message)
        self.assertEqual(result.processing_time, processing_time)
        self.assertEqual(result.plugin_name, "mock")
    
    def test_create_error_result(self):
        """Test creating error result."""
        message = "Test error"
        error = ValueError("Test exception")
        
        result = self.plugin._create_error_result(message, error)
        
        self.assertFalse(result.success)
        self.assertEqual(result.data, {})
        self.assertEqual(result.message, message)
        self.assertEqual(result.plugin_name, "mock")
        self.assertIn("error_type", result.metadata)
        self.assertEqual(result.metadata["error_type"], "ValueError")
    
    def test_check_cancellation(self):
        """Test cancellation checking."""
        # No event - should not be cancelled
        self.assertFalse(self.plugin._check_cancellation(None))
        
        # Event not set - should not be cancelled
        event = Event()
        self.assertFalse(self.plugin._check_cancellation(event))
        
        # Event set - should be cancelled
        event.set()
        self.assertTrue(self.plugin._check_cancellation(event))
    
    def test_update_progress(self):
        """Test progress updating."""
        progress_calls = []
        
        def progress_callback(progress):
            progress_calls.append(progress)
        
        # With callback
        self.plugin._update_progress(progress_callback, 50)
        self.assertEqual(progress_calls, [50])
        
        # Without callback - should not raise error
        self.plugin._update_progress(None, 75)
        
        # Test bounds enforcement
        self.plugin._update_progress(progress_callback, -10)  # Should be 0
        self.plugin._update_progress(progress_callback, 150)  # Should be 100
        
        self.assertEqual(progress_calls, [50, 0, 100])


if __name__ == '__main__':
    unittest.main()