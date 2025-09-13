#!/usr/bin/env python3
"""
Project A.N.C. (Alice Nexus Core) - Main Entry Point

This is the main entry point for the application, which loads the actual
application code from the app/ directory.
"""

import sys
import os

# Add app directory to Python path
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
sys.path.insert(0, app_dir)

# Import and run the main application
if __name__ == "__main__":
    from main import safe_main
    safe_main()