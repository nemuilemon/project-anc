"""Integration tests for the AI analysis system.

Tests the complete system integration including backwards compatibility
and interaction with the main application logic.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import json
from tinydb import TinyDB

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_analysis import AIAnalysisManager, TaggingPlugin, SummarizationPlugin
from logic import AppLogic


class TestAIAnalysisIntegration(unittest.TestCase):
    """Integration tests for the complete AI analysis system."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary database for testing
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_db_file.close()
        
        self.db = TinyDB(self.temp_db_file.name)
        
        # Mock config paths to use temp directories
        self.temp_notes_dir = tempfile.mkdtemp()
        self.temp_archive_dir = tempfile.mkdtemp()
        
        with patch('config.NOTES_DIR', self.temp_notes_dir), \
             patch('config.ARCHIVE_DIR', self.temp_archive_dir):
            self.app_logic = AppLogic(self.db)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.db.close()
        os.unlink(self.temp_db_file.name)
        
        # Clean up temp directories
        import shutil
        shutil.rmtree(self.temp_notes_dir, ignore_errors=True)
        shutil.rmtree(self.temp_archive_dir, ignore_errors=True)
    
    def test_app_logic_ai_system_initialization(self):
        """Test that AppLogic properly initializes the AI system."""
        # Check that AI manager is created
        self.assertIsInstance(self.app_logic.ai_manager, AIAnalysisManager)
        
        # Check that plugins are registered
        available_plugins = self.app_logic.ai_manager.get_available_plugins()
        expected_plugins = ["tagging", "summarization"]
        
        for plugin in expected_plugins:
            self.assertIn(plugin, available_plugins)
    
    def test_get_available_ai_functions(self):
        """Test getting available AI functions."""
        functions = self.app_logic.get_available_ai_functions()
        
        self.assertIsInstance(functions, list)
        self.assertEqual(len(functions), 2)  # tagging, summarization
        
        # Check that each function has required properties
        for func in functions:
            self.assertIn("name", func)
            self.assertIn("description", func)
            self.assertIn("version", func)
    
    @patch('ai_analysis.plugins.tagging_plugin.ollama.generate')
    def test_run_ai_analysis_tagging(self, mock_generate):
        """Test running AI analysis for tagging."""
        mock_generate.return_value = {
            'response': 'Python, Testing, AI, Analysis'
        }
        
        result = self.app_logic.run_ai_analysis(
            "This is test content about Python testing and AI analysis",
            "tagging"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("tags", result["data"])
        self.assertEqual(result["data"]["tags"], ['Python', 'Testing', 'AI', 'Analysis'])
        self.assertEqual(result["plugin_name"], "tagging")
    
    @patch('ai_analysis.plugins.summarization_plugin.ollama.generate')
    def test_run_ai_analysis_summarization(self, mock_generate):
        """Test running AI analysis for summarization."""
        mock_generate.return_value = {
            'response': 'This is a test summary of the content.'
        }
        
        content = "Long content that needs summarization. " * 20
        result = self.app_logic.run_ai_analysis(content, "summarization")
        
        self.assertTrue(result["success"])
        self.assertIn("summary", result["data"])
        self.assertEqual(result["data"]["summary"], "This is a test summary of the content.")
        self.assertEqual(result["plugin_name"], "summarization")
    
    def test_run_ai_analysis_invalid_plugin(self):
        """Test running AI analysis with invalid plugin name."""
        result = self.app_logic.run_ai_analysis("test content", "non_existent_plugin")
        
        self.assertFalse(result["success"])
        self.assertIn("not found", result["message"])
        self.assertEqual(result["plugin_name"], "non_existent_plugin")
    
    @patch('ai_analysis.plugins.tagging_plugin.ollama.generate')
    def test_analyze_and_update_tags_backwards_compatibility(self, mock_generate):
        """Test that the legacy analyze_and_update_tags method still works."""
        mock_generate.return_value = {
            'response': 'Legacy, Compatibility, Test'
        }
        
        # Create a test file record in database
        test_path = os.path.join(self.temp_notes_dir, "test.md")
        self.db.insert({
            'title': 'test.md',
            'path': test_path,
            'tags': [],
            'status': 'active',
            'order_index': 1
        })
        
        success, message = self.app_logic.analyze_and_update_tags(
            test_path,
            "This is legacy test content for backwards compatibility"
        )
        
        self.assertTrue(success)
        self.assertIn("更新しました", message)
        
        # Check that tags were updated in database
        from tinydb import Query
        File = Query()
        doc = self.db.get(File.path == test_path)
        self.assertIsNotNone(doc)
        self.assertEqual(doc['tags'], ['Legacy', 'Compatibility', 'Test'])
    
    @patch('ai_analysis.plugins.tagging_plugin.ollama.generate')
    def test_analyze_and_update_tags_async_backwards_compatibility(self, mock_generate):
        """Test that async tagging method works with new system."""
        mock_generate.return_value = {
            'response': 'Async, Legacy, Test'
        }
        
        # Create a test file record in database
        test_path = os.path.join(self.temp_notes_dir, "async_test.md")
        self.db.insert({
            'title': 'async_test.md',
            'path': test_path,
            'tags': [],
            'status': 'active',
            'order_index': 1
        })
        
        # Mock the async operation manager to execute synchronously for testing
        with patch('logic.async_manager.run_async_operation') as mock_async:
            # Make it call the function directly
            def call_directly(func, **kwargs):
                return func()
            mock_async.side_effect = call_directly
            
            operation_id = self.app_logic.analyze_and_update_tags_async(
                test_path,
                "This is async test content"
            )
        
        # Check that tags were updated
        from tinydb import Query
        File = Query()
        doc = self.db.get(File.path == test_path)
        self.assertIsNotNone(doc)
        self.assertEqual(doc['tags'], ['Async', 'Legacy', 'Test'])
    
    @patch('ai_analysis.plugins.summarization_plugin.ollama.generate')
    def test_run_ai_analysis_async_with_database_storage(self, mock_generate):
        """Test async AI analysis with database storage of results."""
        mock_generate.return_value = {
            'response': 'This is a test summary for async analysis.'
        }
        
        # Create a test file record
        test_path = os.path.join(self.temp_notes_dir, "summary_test.md")
        self.db.insert({
            'title': 'summary_test.md',
            'path': test_path,
            'tags': [],
            'status': 'active',
            'order_index': 1
        })
        
        content = "Long content for summarization testing. " * 20
        
        # Mock async manager to execute synchronously
        with patch('logic.async_manager.run_async_operation') as mock_async:
            def call_directly(func, **kwargs):
                return func()
            mock_async.side_effect = call_directly
            
            operation_id = self.app_logic.run_ai_analysis_async(
                test_path,
                content,
                "summarization",
                summary_type="brief"
            )
        
        # Check that analysis results were stored in database
        from tinydb import Query
        File = Query()
        doc = self.db.get(File.path == test_path)
        
        self.assertIsNotNone(doc)
        self.assertIn("ai_analysis", doc)
        self.assertIn("summarization", doc["ai_analysis"])
        
        summary_data = doc["ai_analysis"]["summarization"]
        self.assertIn("data", summary_data)
        self.assertIn("timestamp", summary_data)
        self.assertIn("processing_time", summary_data)
        self.assertEqual(
            summary_data["data"]["summary"], 
            "This is a test summary for async analysis."
        )
    
    def test_plugin_error_handling(self):
        """Test error handling when plugin encounters issues."""
        # Test with content that will cause validation to fail
        result = self.app_logic.run_ai_analysis("", "tagging")  # Empty content
        
        self.assertFalse(result["success"])
        self.assertIn("validation", result["message"].lower())
    
    def test_system_robustness_with_missing_ollama(self):
        """Test system behavior when Ollama is not available."""
        # This test simulates Ollama connection failure
        with patch('ai_analysis.plugins.tagging_plugin.ollama.generate') as mock_generate:
            mock_generate.side_effect = Exception("Ollama connection failed")
            
            result = self.app_logic.run_ai_analysis("test content", "tagging")
            
            self.assertFalse(result["success"])
            self.assertIn("エラー", result["message"])
    
    def test_multiple_analysis_types(self):
        """Test running multiple analysis types on the same content."""
        content = "This is a comprehensive test content for multiple analysis types. " * 5

        with patch('ai_analysis.plugins.tagging_plugin.ollama.generate') as mock_tag, \
             patch('ai_analysis.plugins.summarization_plugin.ollama.generate') as mock_sum:

            mock_tag.return_value = {'response': 'Multi, Analysis, Test'}
            mock_sum.return_value = {'response': 'This is a multi-analysis test summary.'}

            # Run both analysis types
            tag_result = self.app_logic.run_ai_analysis(content, "tagging")
            summary_result = self.app_logic.run_ai_analysis(content, "summarization")

            # Check both succeeded
            self.assertTrue(tag_result["success"])
            self.assertTrue(summary_result["success"])

            # Check each has expected data structure
            self.assertIn("tags", tag_result["data"])
            self.assertIn("summary", summary_result["data"])


class TestBackwardsCompatibility(unittest.TestCase):
    """Test backwards compatibility with existing application functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_db_file.close()
        
        self.db = TinyDB(self.temp_db_file.name)
        
        self.temp_notes_dir = tempfile.mkdtemp()
        self.temp_archive_dir = tempfile.mkdtemp()
        
        with patch('config.NOTES_DIR', self.temp_notes_dir), \
             patch('config.ARCHIVE_DIR', self.temp_archive_dir):
            self.app_logic = AppLogic(self.db)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.db.close()
        os.unlink(self.temp_db_file.name)
        
        import shutil
        shutil.rmtree(self.temp_notes_dir, ignore_errors=True)
        shutil.rmtree(self.temp_archive_dir, ignore_errors=True)
    
    def test_existing_database_records_compatibility(self):
        """Test that existing database records work with new AI system."""
        # Insert a legacy record (without ai_analysis field)
        legacy_record = {
            'title': 'legacy.md',
            'path': os.path.join(self.temp_notes_dir, 'legacy.md'),
            'tags': ['old', 'legacy'],
            'status': 'active',
            'order_index': 1
        }
        self.db.insert(legacy_record)
        
        # Test that get_file_list still works
        files = self.app_logic.get_file_list()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['title'], 'legacy.md')
        self.assertEqual(files[0]['tags'], ['old', 'legacy'])
    
    def test_ai_analysis_extends_existing_records(self):
        """Test that AI analysis extends existing records without breaking them."""
        # Create existing record
        test_path = os.path.join(self.temp_notes_dir, "extend_test.md")
        self.db.insert({
            'title': 'extend_test.md',
            'path': test_path,
            'tags': ['existing', 'tags'],
            'status': 'active',
            'order_index': 1
        })
        
        # Mock AI analysis
        with patch('ai_analysis.plugins.summarization_plugin.ollama.generate') as mock_sum:
            mock_sum.return_value = {'response': 'Test summary'}
            
            # Run analysis that should extend the record
            with patch('logic.async_manager.run_async_operation') as mock_async:
                def call_directly(func, **kwargs):
                    return func()
                mock_async.side_effect = call_directly
                
                self.app_logic.run_ai_analysis_async(
                    test_path,
                    "Content for extension test",
                    "summarization"
                )
        
        # Check that original fields are preserved and ai_analysis is added
        from tinydb import Query
        File = Query()
        doc = self.db.get(File.path == test_path)
        
        self.assertIsNotNone(doc)
        self.assertEqual(doc['tags'], ['existing', 'tags'])  # Original preserved
        self.assertEqual(doc['status'], 'active')  # Original preserved
        self.assertIn('ai_analysis', doc)  # New field added
        self.assertIn('summarization', doc['ai_analysis'])
    
    def test_new_system_maintains_original_api(self):
        """Test that the new system maintains the original API contracts."""
        # The analyze_and_update_tags method should still return (bool, str)
        with patch('ai_analysis.plugins.tagging_plugin.ollama.generate') as mock_generate:
            mock_generate.return_value = {'response': 'API, Test'}
            
            test_path = os.path.join(self.temp_notes_dir, "api_test.md")
            self.db.insert({
                'title': 'api_test.md',
                'path': test_path,
                'tags': [],
                'status': 'active',
                'order_index': 1
            })
            
            result = self.app_logic.analyze_and_update_tags(test_path, "test content")
            
            # Should return tuple of (bool, str) as before
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            self.assertIsInstance(result[0], bool)
            self.assertIsInstance(result[1], str)


if __name__ == '__main__':
    unittest.main()