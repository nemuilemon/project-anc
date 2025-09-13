"""Test runner for the AI Analysis System.

This script runs all unit tests and generates a comprehensive test report.
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from tests.test_base_plugin import TestAnalysisResult, TestBaseAnalysisPlugin
from tests.test_ai_manager import TestAIAnalysisManager
from tests.test_plugins import TestTaggingPlugin, TestSummarizationPlugin, TestSentimentPlugin, TestPluginIntegration
from tests.test_integration import TestAIAnalysisIntegration, TestBackwardsCompatibility


class TestResult(unittest.TestResult):
    """Custom test result class for detailed reporting."""
    
    def __init__(self):
        super().__init__()
        self.test_results = []
        self.start_time = None
    
    def startTest(self, test):
        super().startTest(test)
        self.start_time = time.time()
    
    def stopTest(self, test):
        super().stopTest(test)
        duration = time.time() - self.start_time
        
        status = "PASS"
        error_info = None
        
        if self.errors and self.errors[-1][0] == test:
            status = "ERROR"
            error_info = self.errors[-1][1]
        elif self.failures and self.failures[-1][0] == test:
            status = "FAIL"
            error_info = self.failures[-1][1]
        elif self.skipped and self.skipped[-1][0] == test:
            status = "SKIP"
            error_info = self.skipped[-1][1]
        
        self.test_results.append({
            'test': str(test),
            'status': status,
            'duration': duration,
            'error': error_info
        })


def create_test_suite():
    """Create comprehensive test suite."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestAnalysisResult,
        TestBaseAnalysisPlugin,
        TestAIAnalysisManager,
        TestTaggingPlugin,
        TestSummarizationPlugin,
        TestSentimentPlugin,
        TestPluginIntegration,
        TestAIAnalysisIntegration,
        TestBackwardsCompatibility
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_tests_with_report():
    """Run tests and generate detailed report."""
    print("="*70)
    print("AI ANALYSIS SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print()
    
    # Create test suite
    suite = create_test_suite()
    
    # Run tests with custom result collector
    result = TestResult()
    start_time = time.time()
    
    suite.run(result)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Generate report
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Total time: {total_duration:.2f}s")
    print()
    
    # Success rate
    passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    success_rate = (passed / result.testsRun * 100) if result.testsRun > 0 else 0
    
    print(f"Success rate: {success_rate:.1f}% ({passed}/{result.testsRun})")
    print()
    
    # Detailed results by category
    categories = {}
    for test_result in result.test_results:
        test_name = test_result['test']
        category = test_name.split('.')[0].replace('tests.test_', '')
        
        if category not in categories:
            categories[category] = {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0}
        
        categories[category]['total'] += 1
        if test_result['status'] == 'PASS':
            categories[category]['passed'] += 1
        elif test_result['status'] == 'FAIL':
            categories[category]['failed'] += 1
        elif test_result['status'] == 'ERROR':
            categories[category]['errors'] += 1
    
    print("Results by Category:")
    print("-" * 50)
    for category, stats in categories.items():
        category_success = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"{category:20s}: {stats['passed']:2d}/{stats['total']:2d} ({category_success:5.1f}%)")
    print()
    
    # Show failures and errors
    if result.failures:
        print("FAILURES:")
        print("-" * 50)
        for test, traceback in result.failures:
            print(f"FAIL: {test}")
            print(traceback)
            print()
    
    if result.errors:
        print("ERRORS:")
        print("-" * 50)
        for test, traceback in result.errors:
            print(f"ERROR: {test}")
            print(traceback)
            print()
    
    # Overall status
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("🎉 ALL TESTS PASSED! The AI Analysis System is ready for deployment.")
    else:
        print("❌ Some tests failed. Please review the issues above.")
    
    print()
    print("="*70)
    
    return result


def run_specific_test_category(category):
    """Run tests for a specific category."""
    print(f"Running {category} tests...")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    category_map = {
        'base': [TestAnalysisResult, TestBaseAnalysisPlugin],
        'manager': [TestAIAnalysisManager],
        'plugins': [TestTaggingPlugin, TestSummarizationPlugin, TestSentimentPlugin, TestPluginIntegration],
        'integration': [TestAIAnalysisIntegration, TestBackwardsCompatibility]
    }
    
    if category not in category_map:
        print(f"Unknown category: {category}")
        print(f"Available categories: {', '.join(category_map.keys())}")
        return
    
    for test_class in category_map[category]:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    if len(sys.argv) > 1:
        category = sys.argv[1]
        run_specific_test_category(category)
    else:
        run_tests_with_report()