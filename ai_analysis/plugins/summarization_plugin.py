"""Summarization Analysis Plugin.

This plugin generates concise summaries of content using AI analysis.
Useful for creating quick overviews of long documents or notes.
"""

import time
from typing import Optional, Callable
from threading import Event
import ollama

from ..base_plugin import BaseAnalysisPlugin, AnalysisResult
import config


class SummarizationPlugin(BaseAnalysisPlugin):
    """AI-powered content summarization plugin.
    
    This plugin uses Ollama to analyze content and generate concise summaries.
    It supports different summary lengths and can handle both short and long content.
    """
    
    def __init__(self):
        super().__init__(
            name="summarization",
            description="Generate concise summaries of content using AI",
            version="1.0.0"
        )
        self.max_summary_length = 500  # Maximum characters for summary
        self.min_content_length = 100  # Minimum content length to summarize
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        """Perform synchronous content summarization.
        
        Args:
            content (str): Text content to summarize
            **kwargs: Additional parameters:
                - summary_type (str): "brief", "detailed", or "bullet" (default: "brief")
                - max_sentences (int): Maximum sentences in summary (default: 3)
            
        Returns:
            AnalysisResult: Result containing generated summary
        """
        start_time = time.time()
        
        try:
            summary_type = kwargs.get('summary_type', 'brief')
            max_sentences = kwargs.get('max_sentences', 3)
            
            summary = self._generate_summary_from_ollama(content, summary_type, max_sentences)
            processing_time = time.time() - start_time
            
            if not summary or summary == "summary_error":
                return self._create_error_result("要約の生成に失敗しました。")
            
            return self._create_success_result(
                data={
                    "summary": summary,
                    "summary_type": summary_type,
                    "original_length": len(content),
                    "summary_length": len(summary),
                    "compression_ratio": round(len(summary) / len(content), 2)
                },
                message=f"要約を生成しました（{len(summary)}文字）。",
                processing_time=processing_time
            )
            
        except Exception as e:
            return self._create_error_result("要約の生成中にエラーが発生しました。", e)
    
    def analyze_async(self,
                     content: str,
                     progress_callback: Optional[Callable[[int], None]] = None,
                     cancel_event: Optional[Event] = None,
                     **kwargs) -> AnalysisResult:
        """Perform asynchronous content summarization with progress tracking.
        
        Args:
            content (str): Text content to summarize
            progress_callback (Callable, optional): Progress update function
            cancel_event (Event, optional): Cancellation event
            **kwargs: Additional parameters (same as analyze method)
            
        Returns:
            AnalysisResult: Result containing generated summary
        """
        start_time = time.time()
        
        try:
            self._update_progress(progress_callback, 10)
            
            if self._check_cancellation(cancel_event):
                return self._create_error_result("要約処理を中止しました。")
            
            summary_type = kwargs.get('summary_type', 'brief')
            max_sentences = kwargs.get('max_sentences', 3)
            
            self._update_progress(progress_callback, 30)
            
            summary = self._generate_summary_from_ollama(
                content, summary_type, max_sentences, cancel_event, progress_callback
            )
            
            if self._check_cancellation(cancel_event):
                return self._create_error_result("要約処理を中止しました。")
            
            self._update_progress(progress_callback, 100)
            processing_time = time.time() - start_time
            
            if not summary or summary == "summary_error":
                return self._create_error_result("要約の生成に失敗しました。")
            
            if summary == "summary_cancelled":
                return self._create_error_result("要約処理を中止しました。")
            
            return self._create_success_result(
                data={
                    "summary": summary,
                    "summary_type": summary_type,
                    "original_length": len(content),
                    "summary_length": len(summary),
                    "compression_ratio": round(len(summary) / len(content), 2)
                },
                message=f"要約を生成しました（{len(summary)}文字）。",
                processing_time=processing_time
            )
            
        except Exception as e:
            return self._create_error_result("要約の生成中にエラーが発生しました。", e)
    
    def _generate_summary_from_ollama(self,
                                     content: str,
                                     summary_type: str = "brief",
                                     max_sentences: int = 3,
                                     cancel_event: Optional[Event] = None,
                                     progress_callback: Optional[Callable[[int], None]] = None) -> str:
        """Generate summary using Ollama AI model.
        
        Args:
            content (str): Text content to summarize
            summary_type (str): Type of summary ("brief", "detailed", "bullet")
            max_sentences (int): Maximum sentences in summary
            cancel_event (Event, optional): Cancellation event
            progress_callback (Callable, optional): Progress update function
            
        Returns:
            str: Generated summary or error indicator
        """
        if self._check_cancellation(cancel_event):
            return "summary_cancelled"
        
        try:
            # Create prompt based on summary type
            if summary_type == "bullet":
                prompt = f\"\"\"
                以下の文章を{max_sentences}つの箇条書きポイントで要約してください。
                各ポイントは「・」で始めてください。
                
                文章:「{content}」
                \"\"\"
            elif summary_type == "detailed":
                prompt = f\"\"\"
                以下の文章を{max_sentences}文以内で詳細に要約してください。
                重要なポイントと背景情報を含めてください。
                
                文章:「{content}」
                \"\"\"
            else:  # brief
                prompt = f\"\"\"
                以下の文章を{max_sentences}文以内で簡潔に要約してください。
                最も重要なポイントのみを含めてください。
                
                文章:「{content}」
                \"\"\"
            
            if progress_callback:
                self._update_progress(progress_callback, 60)
            
            response = ollama.generate(
                model=config.OLLAMA_MODEL,
                prompt=prompt
            )
            
            if progress_callback:
                self._update_progress(progress_callback, 90)
            
            summary = response['response'].strip()
            
            # Validate summary length
            if len(summary) > self.max_summary_length:
                # If too long, try to shorten it
                shorter_prompt = f\"\"\"
                以下の要約をさらに短く（200文字以内）まとめてください:
                {summary}
                \"\"\"
                
                shorter_response = ollama.generate(
                    model=config.OLLAMA_MODEL,
                    prompt=shorter_prompt
                )
                summary = shorter_response['response'].strip()
            
            print(f"生成された要約: {summary}")
            return summary
            
        except Exception as e:
            print(f"Ollamaによる要約生成エラー: {e}")
            return "summary_error"
    
    def validate_content(self, content: str) -> bool:
        """Validate content for summarization.
        
        Args:
            content (str): Content to validate
            
        Returns:
            bool: True if content is suitable for summarization
        """
        return (bool(content and content.strip() and 
                    len(content.strip()) >= self.min_content_length))