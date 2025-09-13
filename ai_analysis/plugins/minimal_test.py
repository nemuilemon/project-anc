"""Minimal plugins for testing."""

from ..base_plugin import BaseAnalysisPlugin, AnalysisResult


class TestTaggingPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__("tagging", "Test tagging plugin", "1.0.0")
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        return self._create_success_result(
            {"tags": ["test", "example"]},
            "Test tags generated",
            0.1
        )
    
    def analyze_async(self, content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
        if progress_callback:
            progress_callback(100)
        return self.analyze(content, **kwargs)


class TestSummarizationPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__("summarization", "Test summarization plugin", "1.0.0")
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        return self._create_success_result(
            {"summary": "This is a test summary", "summary_type": "brief"},
            "Test summary generated",
            0.1
        )
    
    def analyze_async(self, content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
        if progress_callback:
            progress_callback(100)
        return self.analyze(content, **kwargs)


class TestSentimentPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__("sentiment", "Test sentiment plugin", "1.0.0")
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        return self._create_success_result(
            {"overall_sentiment": "ニュートラル", "emotions_detected": []},
            "Test sentiment analysis",
            0.1
        )
    
    def analyze_async(self, content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
        if progress_callback:
            progress_callback(100)
        return self.analyze(content, **kwargs)