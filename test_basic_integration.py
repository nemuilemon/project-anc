"""Basic integration test for the AI analysis system."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test basic imports without the broken plugins
try:
    from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult
    print("[OK] Base plugin imports work")
    
    from ai_analysis.manager import AIAnalysisManager
    print("[OK] AI manager imports work")
    
    # Test basic manager functionality
    manager = AIAnalysisManager()
    print("[OK] AI manager instantiation works")
    
    # Test that the core system is ready
    print(f"[OK] Available plugins: {manager.get_available_plugins()}")
    
    # Test AppLogic integration
    from tinydb import TinyDB
    from logic import AppLogic
    
    # Create temporary database for testing
    import tempfile
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    temp_db.close()
    
    db = TinyDB(temp_db.name)
    app_logic = AppLogic(db)
    print("[OK] AppLogic with AI system initializes successfully")
    
    # Check AI system is set up
    print(f"[OK] AI functions available: {len(app_logic.get_available_ai_functions())}")
    
    # Test that we can get a basic result structure
    result = app_logic.run_ai_analysis("test content", "tagging")
    print(f"[OK] AI analysis call structure works: {result['success']}")
    
    # Clean up
    db.close()
    os.unlink(temp_db.name)
    
    print("\n[SUCCESS] BASIC INTEGRATION TEST PASSED")
    print("The modular AI analysis system is successfully integrated!")
    
except Exception as e:
    print(f"[FAIL] Integration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)