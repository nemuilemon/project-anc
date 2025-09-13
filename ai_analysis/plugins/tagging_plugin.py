"""Tagging Analysis Plugin.

This plugin extracts relevant tags/keywords from content using AI analysis.
It replaces the original tagging functionality from logic.py with a modular,
extensible implementation.
"""

import time
from typing import List, Optional, Callable
from threading import Event
import ollama

from ..base_plugin import BaseAnalysisPlugin, AnalysisResult
import config


class TaggingPlugin(BaseAnalysisPlugin):
    """AI-powered tagging analysis plugin.
    
    This plugin uses Ollama to analyze content and extract relevant tags/keywords.
    It includes retry logic for handling long responses and supports both
    synchronous and asynchronous execution.
    """
    
    def __init__(self):
        super().__init__(
            name="tagging",
            description="Extract relevant tags and keywords from content using AI",
            version="1.0.0"
        )
        self.max_tags_length = 100  # Maximum allowed response length
        self.max_retries = 3        # Maximum retry attempts for long responses
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        """Perform synchronous tag analysis.
        
        Args:
            content (str): Text content to analyze for tags
            **kwargs: Additional parameters (unused for tagging)
            
        Returns:
            AnalysisResult: Result containing extracted tags
        """
        start_time = time.time()
        
        try:
            tags = self._generate_tags_from_ollama(content)
            processing_time = time.time() - start_time
            
            if "tag_error" in tags:
                return self._create_error_result("タグ分析に失敗しました。")
            
            return self._create_success_result(
                data={"tags": tags},
                message=f"タグを{len(tags)}個抽出しました。",
                processing_time=processing_time
            )
            
        except Exception as e:
            return self._create_error_result("タグの更新中にエラーが発生しました。", e)
    
    def analyze_async(self,
                     content: str,
                     progress_callback: Optional[Callable[[int], None]] = None,
                     cancel_event: Optional[Event] = None,
                     **kwargs) -> AnalysisResult:
        """Perform asynchronous tag analysis with progress tracking.
        
        Args:
            content (str): Text content to analyze for tags
            progress_callback (Callable, optional): Progress update function
            cancel_event (Event, optional): Cancellation event
            **kwargs: Additional parameters (unused for tagging)
            
        Returns:
            AnalysisResult: Result containing extracted tags
        """
        start_time = time.time()
        
        try:
            self._update_progress(progress_callback, 10)
            
            tags = self._generate_tags_from_ollama(content, cancel_event, progress_callback)
            
            if self._check_cancellation(cancel_event):
                return self._create_error_result("分析を中止しました。")
            
            self._update_progress(progress_callback, 100)
            processing_time = time.time() - start_time
            
            if "tag_cancelled" in tags:
                return self._create_error_result("分析を中止しました。")
            
            if "tag_error" in tags:
                return self._create_error_result("タグ分析に失敗しました。")
            
            return self._create_success_result(
                data={"tags": tags},
                message=f"タグを{len(tags)}個抽出しました。",
                processing_time=processing_time
            )
            
        except Exception as e:
            return self._create_error_result("タグの更新中にエラーが発生しました。", e)
    
    def _generate_tags_from_ollama(self,
                                  content: str,
                                  cancel_event: Optional[Event] = None,
                                  progress_callback: Optional[Callable[[int], None]] = None) -> List[str]:
        """Generate tags using Ollama AI model.
        
        Args:
            content (str): Text content to analyze
            cancel_event (Event, optional): Cancellation event
            progress_callback (Callable, optional): Progress update function
            
        Returns:
            List[str]: List of extracted tags or error indicators
        """
        if not content.strip():
            return []

        current_content = content
        progress_step = 70 // self.max_retries  # Distribute progress across retries

        for attempt in range(self.max_retries):
            # Check for cancellation at start of each attempt
            if self._check_cancellation(cancel_event):
                print("Cancellation detected. Stopping tag generation.")
                return ["tag_cancelled"]
            
            # Update progress
            if progress_callback:
                base_progress = 20 + (attempt * progress_step)
                self._update_progress(progress_callback, base_progress)
            
            print(f"--- タグ生成試行: {attempt + 1}回目 ---")
            
            try:
                prompt = f"""以下の文章の主要なキーワードを5つから8つ、コンマ区切りで単語のみ抽出してください。
出力例: "Python, Flet, データベース, AI"
文章:「{current_content}」"""
                
                response = ollama.generate(
                    model=config.OLLAMA_MODEL,
                    prompt=prompt
                )
                tags_string = response['response'].strip()

                # Check success condition
                if len(tags_string) <= self.max_tags_length:
                    tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
                    print(f"AIが生成したタグ (成功): {tags}")
                    return tags

                # Handle long response - use response as next input
                print(f"AIの応答が長すぎます ({len(tags_string)}文字)。応答内容を元に再試行します。")
                current_content = tags_string

            except Exception as e:
                print(f"Ollamaへの接続エラー: {e}")
                return ["tag_error"]

        # Maximum retries exceeded
        print(f"最大試行回数({self.max_retries}回)を超えました。タグ付けをスキップします。")
        return []
    
    def validate_content(self, content: str) -> bool:
        """Validate content for tag analysis.
        
        Args:
            content (str): Content to validate
            
        Returns:
            bool: True if content is suitable for tagging
        """
        return bool(content and content.strip() and len(content.strip()) > 10)