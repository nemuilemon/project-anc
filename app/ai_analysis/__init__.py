"""AI Analysis Module for Project A.N.C.

This module provides a modular, extensible AI analysis system that allows
for easy addition of new AI analysis functions like tagging, summarization, etc.

The architecture follows a plugin-based pattern where each analysis type
is implemented as a separate plugin class inheriting from BaseAnalysisPlugin.

Plugins are now loaded dynamically at runtime, eliminating the need for
static imports and making it easy to add new plugins without code changes.
"""

from .base_plugin import BaseAnalysisPlugin, AnalysisResult
from .manager import AIAnalysisManager

# Note: Plugins are now loaded dynamically via PluginManager
# No need to import specific plugins here

__all__ = [
    'BaseAnalysisPlugin',
    'AnalysisResult',
    'AIAnalysisManager'
]

__version__ = '2.0.0'