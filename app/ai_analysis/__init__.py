"""AI Analysis Module for Project A.N.C.

This module provides a modular, extensible AI analysis system that allows
for easy addition of new AI analysis functions like tagging, summarization,
sentiment analysis, etc.

The architecture follows a plugin-based pattern where each analysis type
is implemented as a separate plugin class inheriting from BaseAnalysisPlugin.
"""

from .base_plugin import BaseAnalysisPlugin, AnalysisResult
from .manager import AIAnalysisManager

# Import real AI analysis plugins
from .plugins.tagging_plugin import TaggingPlugin
from .plugins.summarization_plugin import SummarizationPlugin
from .plugins.sentiment_plugin import SentimentPlugin

__all__ = [
    'BaseAnalysisPlugin',
    'AnalysisResult', 
    'AIAnalysisManager',
    'TaggingPlugin',
    'SummarizationPlugin',
    'SentimentPlugin'
]

__version__ = '1.0.0'