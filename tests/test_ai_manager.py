"""Unit tests for the AI Analysis Manager.

Tests the central coordination system for AI analysis plugins.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from threading import Event
import time

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_analysis.manager import AIAnalysisManager
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult


class MockPlugin(BaseAnalysisPlugin):
    """Mock plugin for testing manager functionality."""
    
    def __init__(self, name="mock", should_fail=False, processing_time=0.1):
        super().__init__(name, f"Mock plugin {name}", "1.0.0")
        self.should_fail = should_fail
        self.processing_time = processing_time
        self.analyze_calls = []
        self.analyze_async_calls = []
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        self.analyze_calls.append((content, kwargs))
        
        if self.should_fail:
            raise RuntimeError("Mock analysis failed")
        
        time.sleep(self.processing_time)
        
        return self._create_success_result(
            {"mock_result": f"analyzed {content}"},
            f"Mock analysis completed for {self.name}",
            self.processing_time
        )
    
    def analyze_async(self, content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
        self.analyze_async_calls.append((content, kwargs))
        
        if progress_callback:
            progress_callback(25)
        
        if self._check_cancellation(cancel_event):
            return self._create_error_result("Analysis cancelled")
        
        if progress_callback:
            progress_callback(75)
        
        result = self.analyze(content, **kwargs)
        
        if progress_callback:
            progress_callback(100)
        
        return result


class TestAIAnalysisManager(unittest.TestCase):
    """Test cases for AIAnalysisManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = AIAnalysisManager()
        self.mock_plugin = MockPlugin("test_plugin")
        self.failing_plugin = MockPlugin("failing_plugin", should_fail=True)
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        self.assertEqual(len(self.manager.plugins), 0)
        self.assertEqual(self.manager.get_available_plugins(), [])
    
    def test_register_plugin_success(self):
        """Test successful plugin registration."""
        result = self.manager.register_plugin(self.mock_plugin)
        
        self.assertTrue(result)
        self.assertIn("test_plugin", self.manager.plugins)
        self.assertEqual(self.manager.get_available_plugins(), ["test_plugin"])
    
    def test_register_plugin_duplicate(self):
        """Test registering duplicate plugin."""
        # Register first time
        self.assertTrue(self.manager.register_plugin(self.mock_plugin))
        
        # Try to register again
        duplicate_plugin = MockPlugin("test_plugin")
        self.assertFalse(self.manager.register_plugin(duplicate_plugin))
        
        # Should still only have one
        self.assertEqual(len(self.manager.plugins), 1)
    
    def test_unregister_plugin(self):
        """Test plugin unregistration."""
        # Register then unregister
        self.manager.register_plugin(self.mock_plugin)
        result = self.manager.unregister_plugin("test_plugin")
        
        self.assertTrue(result)
        self.assertEqual(len(self.manager.plugins), 0)
        
        # Try to unregister non-existent plugin
        self.assertFalse(self.manager.unregister_plugin("non_existent"))
    
    def test_get_plugin_info(self):
        """Test getting plugin information."""
        self.manager.register_plugin(self.mock_plugin)
        
        info = self.manager.get_plugin_info("test_plugin")
        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "test_plugin")
        self.assertEqual(info["description"], "Mock plugin test_plugin")
        
        # Non-existent plugin
        self.assertIsNone(self.manager.get_plugin_info("non_existent"))
    
    def test_analyze_success(self):
        """Test successful analysis."""
        self.manager.register_plugin(self.mock_plugin)
        
        result = self.manager.analyze("test content", "test_plugin", param1="value1")
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["mock_result"], "analyzed test content")
        self.assertEqual(result.plugin_name, "test_plugin")
        self.assertGreater(result.processing_time, 0)
        
        # Check plugin was called with correct parameters
        self.assertEqual(len(self.mock_plugin.analyze_calls), 1)
        content, kwargs = self.mock_plugin.analyze_calls[0]
        self.assertEqual(content, "test content")
        self.assertEqual(kwargs["param1"], "value1")
    
    def test_analyze_plugin_not_found(self):
        """Test analysis with non-existent plugin."""
        result = self.manager.analyze("test content", "non_existent")
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.message)
        self.assertEqual(result.plugin_name, "non_existent")
    
    def test_analyze_invalid_content(self):
        """Test analysis with invalid content."""
        self.manager.register_plugin(self.mock_plugin)
        
        # Mock plugin validation to return False for empty content
        with patch.object(self.mock_plugin, 'validate_content', return_value=False):
            result = self.manager.analyze("", "test_plugin")
        
        self.assertFalse(result.success)
        self.assertIn("validation failed", result.message.lower())
    
    def test_analyze_plugin_error(self):
        """Test analysis when plugin raises exception."""
        self.manager.register_plugin(self.failing_plugin)
        
        result = self.manager.analyze("test content", "failing_plugin")
        
        self.assertFalse(result.success)
        self.assertIn("failed", result.message.lower())
        self.assertEqual(result.plugin_name, "failing_plugin")
        self.assertIn("error_type", result.metadata)
    
    def test_analyze_async_success(self):
        """Test successful async analysis."""
        self.manager.register_plugin(self.mock_plugin)
        progress_calls = []
        
        def progress_callback(progress):
            progress_calls.append(progress)
        
        result = self.manager.analyze_async(
            "test content", 
            "test_plugin", 
            progress_callback=progress_callback,
            param2="value2"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["mock_result"], "analyzed test content")
        self.assertGreater(len(progress_calls), 0)
        
        # Check plugin was called correctly
        self.assertEqual(len(self.mock_plugin.analyze_async_calls), 1)
        content, kwargs = self.mock_plugin.analyze_async_calls[0]
        self.assertEqual(content, "test content")
        self.assertEqual(kwargs["param2"], "value2")
    
    def test_analyze_async_cancellation(self):
        """Test async analysis cancellation."""
        self.manager.register_plugin(self.mock_plugin)
        cancel_event = Event()
        cancel_event.set()
        
        result = self.manager.analyze_async(
            "test content",
            "test_plugin",
            cancel_event=cancel_event
        )
        
        self.assertFalse(result.success)
        self.assertIn("cancelled", result.message.lower())
    
    def test_analyze_multiple_success(self):
        """Test analyzing with multiple plugins."""
        plugin1 = MockPlugin("plugin1")
        plugin2 = MockPlugin("plugin2")
        
        self.manager.register_plugin(plugin1)
        self.manager.register_plugin(plugin2)
        
        results = self.manager.analyze_multiple(
            "test content",
            ["plugin1", "plugin2"],
            shared_param="shared_value"
        )
        
        self.assertEqual(len(results), 2)
        self.assertTrue(results["plugin1"].success)
        self.assertTrue(results["plugin2"].success)
        
        # Check both plugins were called
        self.assertEqual(len(plugin1.analyze_calls), 1)
        self.assertEqual(len(plugin2.analyze_calls), 1)
    
    def test_analyze_multiple_partial_failure(self):
        """Test multiple analysis with one plugin failing."""
        self.manager.register_plugin(self.mock_plugin)
        self.manager.register_plugin(self.failing_plugin)
        
        results = self.manager.analyze_multiple(
            "test content",
            ["test_plugin", "failing_plugin"]
        )
        
        self.assertEqual(len(results), 2)
        self.assertTrue(results["test_plugin"].success)
        self.assertFalse(results["failing_plugin"].success)
    
    def test_get_analysis_summary(self):
        """Test analysis summary generation."""
        # Create mock results
        successful_result = AnalysisResult(
            success=True,
            data={"test": "data"},
            message="Success",
            processing_time=1.5,
            plugin_name="success_plugin"
        )
        
        failed_result = AnalysisResult(
            success=False,
            data={},
            message="Failed",
            processing_time=0.5,
            plugin_name="failed_plugin"
        )
        
        results = {
            "success_plugin": successful_result,
            "failed_plugin": failed_result
        }
        
        summary = self.manager.get_analysis_summary(results)
        
        self.assertEqual(summary["total_plugins"], 2)
        self.assertEqual(summary["successful_plugins"], 1)
        self.assertEqual(summary["failed_plugins"], 1)
        self.assertEqual(summary["total_processing_time"], 2.0)
        self.assertEqual(summary["success_rate"], 0.5)
        self.assertTrue(summary["plugin_results"]["success_plugin"])
        self.assertFalse(summary["plugin_results"]["failed_plugin"])
    
    def test_get_analysis_summary_empty(self):
        """Test analysis summary with no results."""
        summary = self.manager.get_analysis_summary({})
        
        self.assertEqual(summary["total_plugins"], 0)
        self.assertEqual(summary["successful_plugins"], 0)
        self.assertEqual(summary["failed_plugins"], 0)
        self.assertEqual(summary["success_rate"], 0)


if __name__ == '__main__':
    unittest.main()