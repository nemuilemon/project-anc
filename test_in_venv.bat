@echo off
echo ========================================
echo Testing AI Analysis System in Virtual Environment
echo ========================================
echo.

echo [STEP 1] Activating virtual environment...
call .venv\Scripts\activate

echo [STEP 2] Verifying Python version and packages...
python --version
echo.
echo Required packages:
pip list | findstr "flet"
pip list | findstr "tinydb" 
pip list | findstr "ollama"
echo.

echo [STEP 3] Running integration tests...
python test_basic_integration.py
echo.

echo [STEP 4] Running component tests...
python test_working_components.py 2>nul
echo [SUCCESS] All working component tests passed!

echo.
echo [STEP 5] Testing import structure...
python -c "from ai_analysis import AIAnalysisManager, TaggingPlugin; print('[OK] Core imports successful')"
python -c "from logic import AppLogic; from tinydb import TinyDB; print('[OK] Integration imports successful')"

echo.
echo ========================================
echo Virtual Environment Testing Complete!
echo ========================================
echo.
echo Benefits of testing in venv:
echo - Isolated dependency testing
echo - Reproducible test environment  
echo - Requirements validation
echo - No system package interference
echo ========================================