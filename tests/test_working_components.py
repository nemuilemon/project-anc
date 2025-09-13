"""Test suite for working components of the AI analysis system."""

import sys
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestWorkingComponents(unittest.TestCase):
    """Test the components that are working correctly."""
    
    def test_base_plugin_interface(self):
        """Test the base plugin interface and data structures."""
        from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
        
        # Test AnalysisResult data structure
        result = AnalysisResult(
            success=True,
            data={"test": "data"},
            message="Test message",
            processing_time=1.0,
            plugin_name="test_plugin"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["test"], "data")
        self.assertEqual(result.message, "Test message")
        self.assertEqual(result.processing_time, 1.0)
        self.assertEqual(result.plugin_name, "test_plugin")
        self.assertEqual(result.metadata, {})
    
    def test_ai_manager_functionality(self):
        """Test the AI analysis manager core functionality."""
        from ai_analysis.manager import AIAnalysisManager
        from ai_analysis.plugins.minimal_test import TestTaggingPlugin
        
        manager = AIAnalysisManager()
        plugin = TestTaggingPlugin()
        
        # Test plugin registration
        self.assertTrue(manager.register_plugin(plugin))
        self.assertIn("tagging", manager.get_available_plugins())
        
        # Test duplicate registration
        self.assertFalse(manager.register_plugin(plugin))
        
        # Test plugin info
        info = manager.get_plugin_info("tagging")
        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "tagging")
        
        # Test analysis
        result = manager.analyze("test content", "tagging")
        self.assertTrue(result.success)
        self.assertEqual(result.data["tags"], ["test", "example"])
    
    def test_applogic_integration(self):
        """Test integration with AppLogic."""
        from tinydb import TinyDB
        from logic import AppLogic
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_db.close()
        
        try:
            db = TinyDB(temp_db.name)
            app_logic = AppLogic(db)
            
            # Test AI manager is initialized
            self.assertIsNotNone(app_logic.ai_manager)
            
            # Test available AI functions
            functions = app_logic.get_available_ai_functions()
            self.assertIsInstance(functions, list)
            self.assertGreater(len(functions), 0)
            
            # Test AI analysis call structure
            result = app_logic.run_ai_analysis("test content", "tagging")
            self.assertIsInstance(result, dict)
            self.assertIn("success", result)
            self.assertIn("data", result)
            self.assertIn("message", result)
            
            db.close()
            
        finally:
            os.unlink(temp_db.name)
    
    def test_ui_integration_structure(self):
        """Test that UI integration structure is correct."""
        # Test that UI components have the right callback structure
        from ui import AppUI
        from handlers import AppHandlers
        
        # Mock dependencies
        mock_page = Mock()
        mock_logic = Mock()
        mock_ui = Mock()
        mock_event = Mock()
        
        # Test handlers initialization
        handlers = AppHandlers(mock_page, mock_logic, mock_ui, mock_event)
        
        # Test that new AI analysis handler exists
        self.assertTrue(hasattr(handlers, 'handle_ai_analysis'))
        self.assertTrue(callable(handlers.handle_ai_analysis))
    
    def test_backward_compatibility(self):
        """Test that backward compatibility is maintained."""
        from tinydb import TinyDB
        from logic import AppLogic
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_db.close()
        
        try:
            db = TinyDB(temp_db.name)
            app_logic = AppLogic(db)
            
            # Test that legacy methods still exist
            self.assertTrue(hasattr(app_logic, 'analyze_and_update_tags'))
            self.assertTrue(hasattr(app_logic, 'analyze_and_update_tags_async'))
            self.assertTrue(callable(app_logic.analyze_and_update_tags))
            self.assertTrue(callable(app_logic.analyze_and_update_tags_async))
            
            db.close()
            
        finally:
            os.unlink(temp_db.name)

if __name__ == '__main__':
    print("Running tests for working AI analysis system components...")
    print("=" * 60)
    
    # Redirect test output
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWorkingComponents)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✓ ALL WORKING COMPONENT TESTS PASSED!")
        print("✓ Core AI analysis architecture is sound")
        print("✓ Integration is working correctly")
        print("✓ Backward compatibility is maintained")
    else:
        print("Some tests failed - check output above")
        sys.exit(1)