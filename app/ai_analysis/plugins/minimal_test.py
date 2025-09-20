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


class TestSentimentCompassPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__("sentiment_compass", "Test sentiment compass plugin", "1.0.0")

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        return self._create_success_result(
            {
                "analysis_type": "sentiment_compass",
                "axes_scores": {
                    "emotion": 7,
                    "logic": 6,
                    "effort": 8,
                    "growth": 5
                },
                "axes_reasoning": {
                    "emotion": "テスト用の情熱分析結果",
                    "logic": "テスト用の論理性分析結果",
                    "effort": "テスト用の努力分析結果",
                    "growth": "テスト用の成長性分析結果"
                },
                "total_score": 26,
                "compass_summary": "テスト用のバランス分析結果です。"
            },
            "Test sentiment compass analysis",
            0.1
        )

    def analyze_async(self, content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
        if progress_callback:
            progress_callback(100)
        return self.analyze(content, **kwargs)


