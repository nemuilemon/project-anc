"""Sentiment Analysis Plugin.

This plugin analyzes the emotional tone and sentiment of content using AI.
Useful for understanding the mood, tone, and emotional context of notes.
"""

import time
from typing import Optional, Callable, Dict, Any
from threading import Event
import ollama

from ..base_plugin import BaseAnalysisPlugin, AnalysisResult
import config


class SentimentPlugin(BaseAnalysisPlugin):
    """AI-powered sentiment analysis plugin.
    
    This plugin uses Ollama to analyze the emotional tone, sentiment,
    and mood of text content. It provides both overall sentiment and
    detailed emotional analysis.
    """
    
    def __init__(self):
        super().__init__(
            name="sentiment",
            description="Analyze emotional tone and sentiment of content using AI",
            version="1.0.0"
        )
        self.min_content_length = 20  # Minimum content length for meaningful analysis
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        """Perform synchronous sentiment analysis.
        
        Args:
            content (str): Text content to analyze for sentiment
            **kwargs: Additional parameters:
                - analysis_type (str): "basic", "detailed", or "emotional" (default: "basic")
                - language (str): Content language hint (default: "japanese")
            
        Returns:
            AnalysisResult: Result containing sentiment analysis
        """
        start_time = time.time()
        
        try:
            analysis_type = kwargs.get('analysis_type', 'basic')
            language = kwargs.get('language', 'japanese')
            
            sentiment_data = self._analyze_sentiment_with_ollama(content, analysis_type, language)
            processing_time = time.time() - start_time
            
            if not sentiment_data or sentiment_data.get('error'):
                return self._create_error_result("感情分析に失敗しました。")
            
            return self._create_success_result(
                data=sentiment_data,
                message=f"感情分析が完了しました（{sentiment_data.get('overall_sentiment', 'unknown')}）。",
                processing_time=processing_time
            )
            
        except Exception as e:
            return self._create_error_result("感情分析中にエラーが発生しました。", e)
    
    def analyze_async(self,
                     content: str,
                     progress_callback: Optional[Callable[[int], None]] = None,
                     cancel_event: Optional[Event] = None,
                     **kwargs) -> AnalysisResult:
        """Perform asynchronous sentiment analysis with progress tracking.
        
        Args:
            content (str): Text content to analyze for sentiment
            progress_callback (Callable, optional): Progress update function
            cancel_event (Event, optional): Cancellation event
            **kwargs: Additional parameters (same as analyze method)
            
        Returns:
            AnalysisResult: Result containing sentiment analysis
        """
        start_time = time.time()
        
        try:
            self._update_progress(progress_callback, 10)
            
            if self._check_cancellation(cancel_event):
                return self._create_error_result("感情分析を中止しました。")
            
            analysis_type = kwargs.get('analysis_type', 'basic')
            language = kwargs.get('language', 'japanese')
            
            self._update_progress(progress_callback, 30)
            
            sentiment_data = self._analyze_sentiment_with_ollama(
                content, analysis_type, language, cancel_event, progress_callback
            )
            
            if self._check_cancellation(cancel_event):
                return self._create_error_result("感情分析を中止しました。")
            
            self._update_progress(progress_callback, 100)
            processing_time = time.time() - start_time
            
            if not sentiment_data or sentiment_data.get('error'):
                return self._create_error_result("感情分析に失敗しました。")
            
            if sentiment_data.get('cancelled'):
                return self._create_error_result("感情分析を中止しました。")
            
            return self._create_success_result(
                data=sentiment_data,
                message=f"感情分析が完了しました（{sentiment_data.get('overall_sentiment', 'unknown')}）。",
                processing_time=processing_time
            )
            
        except Exception as e:
            return self._create_error_result("感情分析中にエラーが発生しました。", e)
    
    def _analyze_sentiment_with_ollama(self,
                                      content: str,
                                      analysis_type: str = "basic",
                                      language: str = "japanese",
                                      cancel_event: Optional[Event] = None,
                                      progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        """Analyze sentiment using Ollama AI model.
        
        Args:
            content (str): Text content to analyze
            analysis_type (str): Type of analysis to perform
            language (str): Content language hint
            cancel_event (Event, optional): Cancellation event
            progress_callback (Callable, optional): Progress update function
            
        Returns:
            Dict[str, Any]: Sentiment analysis results or error indicator
        """
        if self._check_cancellation(cancel_event):
            return {"cancelled": True}
        
        try:
            # Create prompt based on analysis type
            if analysis_type == "detailed":
                prompt = f\"\"\"
                以下のテキストの感情を詳細に分析してください。
                以下の形式で回答してください:
                
                全体的な感情: [ポジティブ/ネガティブ/ニュートラル]
                感情の強さ: [弱い/中程度/強い]
                主要な感情: [喜び/悲しみ/怒り/恐れ/驚き/嫌悪/その他]
                トーン: [フォーマル/カジュアル/情熱的/冷静/その他]
                
                テキスト: 「{content}」
                \"\"\"
            elif analysis_type == "emotional":
                prompt = f\"\"\"
                以下のテキストに含まれる感情を分析し、感情ごとの強度を評価してください。
                以下の形式で回答してください:
                
                喜び: [0-10の数値]
                悲しみ: [0-10の数値]
                怒り: [0-10の数値]
                恐れ: [0-10の数値]
                驚き: [0-10の数値]
                全体的印象: [一言で]
                
                テキスト: 「{content}」
                \"\"\"
            else:  # basic
                prompt = f\"\"\"
                以下のテキストの感情を分析してください。
                「ポジティブ」「ネガティブ」「ニュートラル」のいずれかで回答し、
                その後に理由を簡潔に説明してください。
                
                テキスト: 「{content}」
                \"\"\"
            
            if progress_callback:
                self._update_progress(progress_callback, 60)
            
            response = ollama.generate(
                model=config.OLLAMA_MODEL,
                prompt=prompt
            )
            
            if progress_callback:
                self._update_progress(progress_callback, 90)
            
            analysis_result = response['response'].strip()
            
            # Parse the response based on analysis type
            parsed_result = self._parse_sentiment_response(analysis_result, analysis_type)
            parsed_result['raw_response'] = analysis_result
            parsed_result['analysis_type'] = analysis_type
            parsed_result['content_length'] = len(content)
            
            print(f"感情分析結果: {parsed_result}")
            return parsed_result
            
        except Exception as e:
            print(f"Ollamaによる感情分析エラー: {e}")
            return {"error": str(e)}
    
    def _parse_sentiment_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Parse the AI response into structured sentiment data.
        
        Args:
            response (str): Raw AI response
            analysis_type (str): Type of analysis performed
            
        Returns:
            Dict[str, Any]: Parsed sentiment data
        """
        result = {"raw_analysis": response}
        
        try:
            # Basic parsing - look for key sentiment indicators
            response_lower = response.lower()
            
            # Determine overall sentiment
            if any(word in response_lower for word in ['ポジティブ', 'positive', '肯定的', '良い', '明るい']):
                result['overall_sentiment'] = 'ポジティブ'
            elif any(word in response_lower for word in ['ネガティブ', 'negative', '否定的', '悪い', '暗い']):
                result['overall_sentiment'] = 'ネガティブ'
            else:
                result['overall_sentiment'] = 'ニュートラル'
            
            # Extract emotional indicators
            emotions = {
                'joy': any(word in response_lower for word in ['喜び', '嬉しい', '楽しい', 'joy', 'happy']),
                'sadness': any(word in response_lower for word in ['悲しみ', '悲しい', 'sad', 'sorrow']),
                'anger': any(word in response_lower for word in ['怒り', '怒っている', 'angry', 'anger']),
                'fear': any(word in response_lower for word in ['恐れ', '恐怖', '不安', 'fear', 'anxiety']),
                'surprise': any(word in response_lower for word in ['驚き', '驚いた', 'surprise', 'surprised'])
            }
            
            result['emotions_detected'] = [emotion for emotion, present in emotions.items() if present]
            
            # Try to extract intensity
            if any(word in response_lower for word in ['強い', '激しい', 'strong', 'intense']):
                result['intensity'] = '強い'
            elif any(word in response_lower for word in ['弱い', 'weak', 'mild']):
                result['intensity'] = '弱い'
            else:
                result['intensity'] = '中程度'
                
        except Exception as e:
            print(f"Response parsing error: {e}")
            result['parsing_error'] = str(e)
        
        return result
    
    def validate_content(self, content: str) -> bool:
        """Validate content for sentiment analysis.
        
        Args:
            content (str): Content to validate
            
        Returns:
            bool: True if content is suitable for sentiment analysis
        """
        return (bool(content and content.strip() and 
                    len(content.strip()) >= self.min_content_length))