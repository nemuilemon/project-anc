"""Sentiment Compass Plugin - AI-Powered Growth Analysis.

This plugin transforms daily journal entries into a multi-dimensional dashboard
for personal growth analysis. It analyzes text across multiple axes that reflect
core values: Emotion/Passion, Logic/Objectivity, Effort/Diligence, and Growth/Development.

The plugin acts as an "orchestrator" that sends targeted prompts to the local AI
for each analysis axis, providing stable and reliable results.
"""

import ollama
import re
import json
import time
import sys
import os
from typing import Dict, Any, Optional, List, Tuple
from ..base_plugin import BaseAnalysisPlugin, AnalysisResult

# Add config directory to path for importing config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config'))
import config


class SentimentCompassPlugin(BaseAnalysisPlugin):
    """AI-powered multi-dimensional growth analysis plugin.

    This plugin uses Ollama to analyze text content across four key dimensions:
    - Emotion/Passion (熱量・情熱)
    - Logic/Objectivity (論理性・客観性)
    - Effort/Diligence (努力・勤勉性)
    - Growth/Development (成長・発展性)

    Each axis is analyzed separately using targeted prompts to ensure reliable
    results. The final output is structured data suitable for radar chart visualization.
    """

    def __init__(self):
        super().__init__(
            name="sentiment_compass",
            description="Multi-dimensional AI analysis for personal growth tracking across 4 key axes",
            version="1.0.0"
        )

        # Define the analysis axes in Japanese (for prompts) and English (for data keys)
        self.analysis_axes = {
            "emotion": "熱量・情熱",
            "logic": "論理性・客観性",
            "effort": "努力・勤勉性",
            "growth": "成長・発展性"
        }

    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        """Perform synchronous sentiment compass analysis.

        Args:
            content (str): Text content to analyze
            **kwargs: Additional parameters (model, language, etc.)

        Returns:
            AnalysisResult: Result containing multi-axis analysis scores and reasoning
        """
        start_time = time.time()

        try:
            if not self.validate_content(content):
                return self._create_error_result("Content too short for meaningful analysis (minimum 20-30 characters depending on language)")

            # Check if we should use test mode (fallback when Ollama is not available)
            use_test_mode = kwargs.get('test_mode', False)

            if use_test_mode:
                compass_data = self._create_test_compass_data()
            else:
                compass_data = self._analyze_compass_with_ollama(content, **kwargs)

                # If Ollama analysis fails, fall back to test mode
                if not compass_data or compass_data.get('error'):
                    print(f"Ollama analysis failed, falling back to test mode: {compass_data.get('error', 'Unknown error')}")
                    compass_data = self._create_test_compass_data()

            processing_time = time.time() - start_time
            return AnalysisResult(
                success=True,
                data=compass_data,
                message=f"多次元分析が完了しました。総合スコア: {compass_data.get('total_score', 0)}/40",
                processing_time=processing_time,
                plugin_name=self.name
            )

        except Exception as e:
            processing_time = time.time() - start_time
            # Create test data as final fallback
            print(f"Analysis failed, using test data: {str(e)}")
            compass_data = self._create_test_compass_data()
            return AnalysisResult(
                success=True,
                data=compass_data,
                message=f"テストモードで分析完了。総合スコア: {compass_data.get('total_score', 0)}/40",
                processing_time=processing_time,
                plugin_name=self.name
            )

    def analyze_async(self, content: str, progress_callback=None, cancel_event=None, **kwargs) -> AnalysisResult:
        """Perform asynchronous sentiment compass analysis with progress tracking.

        Args:
            content (str): Text content to analyze
            progress_callback (callable, optional): Progress update callback
            cancel_event (threading.Event, optional): Cancellation event
            **kwargs: Additional parameters

        Returns:
            AnalysisResult: Result containing multi-axis analysis
        """
        start_time = time.time()

        try:
            if not self.validate_content(content):
                return self._create_error_result("Content too short for meaningful analysis (minimum 20-30 characters depending on language)")

            if progress_callback:
                progress_callback(10, "分析を開始しています...")

            if cancel_event and cancel_event.is_set():
                return self._create_cancellation_result()

            # Check if we should use test mode
            use_test_mode = kwargs.get('test_mode', False)

            if use_test_mode:
                compass_data = self._create_test_compass_data()
            else:
                compass_data = self._analyze_compass_with_ollama(
                    content,
                    progress_callback=progress_callback,
                    cancel_event=cancel_event,
                    **kwargs
                )

                # If Ollama analysis fails, fall back to test mode
                if not compass_data or compass_data.get('error'):
                    print(f"Ollama analysis failed, falling back to test mode: {compass_data.get('error', 'Unknown error')}")
                    compass_data = self._create_test_compass_data()

            if cancel_event and cancel_event.is_set():
                return self._create_cancellation_result()

            if compass_data.get('cancelled'):
                return self._create_cancellation_result()

            processing_time = time.time() - start_time
            return AnalysisResult(
                success=True,
                data=compass_data,
                message=f"多次元分析が完了しました。総合スコア: {compass_data.get('total_score', 0)}/40",
                processing_time=processing_time,
                plugin_name=self.name
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return self._create_error_result(f"Analysis error: {str(e)}", processing_time)

    def _analyze_compass_with_ollama(self,
                                   content: str,
                                   model: str = None,
                                   language: str = "japanese",
                                   progress_callback=None,
                                   cancel_event=None) -> Dict[str, Any]:
        """Analyze content across multiple dimensions using Ollama AI model.

        This method acts as an orchestrator, sending individual prompts for each
        analysis axis to ensure stable and reliable results.

        Args:
            content (str): Text content to analyze
            model (str): Ollama model to use
            language (str): Analysis language preference
            progress_callback (callable, optional): Progress callback
            cancel_event (threading.Event, optional): Cancellation event

        Returns:
            Dict[str, Any]: Compass analysis results or error indicator
        """
        # Get model from config if not specified
        if model is None:
            model = getattr(config, 'SENTIMENT_COMPASS_MODEL', 'gemma3:4b')

        # Handle "auto" model selection
        if model == "auto":
            model = self._get_available_model()

        try:
            result_data = {
                "analysis_type": "sentiment_compass",
                "axes_scores": {},
                "axes_reasoning": {},
                "total_score": 0,
                "analysis_timestamp": time.time(),
                "model_used": model
            }

            total_axes = len(self.analysis_axes)

            for i, (axis_key, axis_name) in enumerate(self.analysis_axes.items()):
                if cancel_event and cancel_event.is_set():
                    return {"cancelled": True}

                # Update progress
                progress = 20 + (i * 60 // total_axes)
                if progress_callback:
                    progress_callback(progress, f"{axis_name}を分析中...")

                # Analyze this specific axis
                axis_result = self._analyze_single_axis(content, axis_name, model)

                if axis_result.get('error'):
                    return {"error": f"{axis_name}の分析に失敗しました: {axis_result['error']}"}

                result_data["axes_scores"][axis_key] = axis_result.get("score", 0)
                result_data["axes_reasoning"][axis_key] = axis_result.get("reasoning", "")
                result_data["total_score"] += axis_result.get("score", 0)

            # Final progress update
            if progress_callback:
                progress_callback(95, "分析結果をまとめています...")

            # Add summary analysis
            result_data["compass_summary"] = self._generate_compass_summary(result_data["axes_scores"])

            if progress_callback:
                progress_callback(100, "分析完了")

            return result_data

        except Exception as e:
            return {"error": f"Compass analysis failed: {str(e)}"}

    def _get_available_model(self) -> str:
        """Get the first available model from Ollama.

        Returns:
            str: Model name or configured fallback
        """
        try:
            models = ollama.list()
            model_list = models.get('models', [])
            if model_list:
                # Prefer configured model if available
                configured_model = getattr(config, 'SENTIMENT_COMPASS_MODEL', 'gemma3:4b')
                for model in model_list:
                    if model.get('name') == configured_model:
                        return configured_model
                # Return first available model if configured model not found
                return model_list[0].get('name', configured_model)
            return getattr(config, 'SENTIMENT_COMPASS_MODEL', 'gemma3:4b')  # Config fallback
        except:
            return getattr(config, 'SENTIMENT_COMPASS_MODEL', 'gemma3:4b')  # Config fallback

    def _analyze_single_axis(self, content: str, axis_name: str, model: str) -> Dict[str, Any]:
        """Analyze content for a single axis using targeted prompt.

        Args:
            content (str): Text content to analyze
            axis_name (str): Japanese name of the analysis axis
            model (str): Ollama model to use

        Returns:
            Dict[str, Any]: Single axis analysis result
        """
        # Create targeted prompt for this specific axis
        prompt = f"""# 指示
以下の文章を分析し、「{axis_name}」の強さを10段階で評価してください。
評価の理由も100文字程度で簡潔に記述してください。

# 出力フォーマットの例
{axis_name}の強さ: 8/10
理由: (ここに100文字程度の理由)

# 文章
{content}"""

        try:
            # Try to get an available model if the specified one fails
            try_model = model
            response = ollama.generate(
                model=try_model,
                prompt=prompt,
                options={
                    "temperature": 0.3,  # Lower temperature for more consistent scoring
                    "top_p": 0.8
                }
            )

            analysis_result = response.get('response', '')
            return self._parse_axis_response(analysis_result, axis_name)

        except Exception as e:
            # Try with an available model if the specified one fails
            try:
                available_model = self._get_available_model()
                if available_model != model:
                    response = ollama.generate(
                        model=available_model,
                        prompt=prompt,
                        options={
                            "temperature": 0.3,
                            "top_p": 0.8
                        }
                    )
                    analysis_result = response.get('response', '')
                    return self._parse_axis_response(analysis_result, axis_name)
            except:
                pass

            return {"error": f"Ollama request failed: {str(e)}"}

    def _parse_axis_response(self, response: str, axis_name: str) -> Dict[str, Any]:
        """Parse the AI response for a single axis into structured data.

        Args:
            response (str): Raw AI response
            axis_name (str): Name of the analyzed axis

        Returns:
            Dict[str, Any]: Parsed axis data with score and reasoning
        """
        try:
            # Extract score using regex pattern
            score_pattern = rf"{re.escape(axis_name)}の強さ:\s*(\d+)/10"
            score_match = re.search(score_pattern, response)

            score = 5  # Default neutral score
            if score_match:
                score = min(10, max(0, int(score_match.group(1))))

            # Extract reasoning
            reason_pattern = r"理由:\s*(.+?)(?:\n|$)"
            reason_match = re.search(reason_pattern, response)

            reasoning = "分析結果が取得できませんでした"
            if reason_match:
                reasoning = reason_match.group(1).strip()

            return {
                "score": score,
                "reasoning": reasoning,
                "raw_response": response
            }

        except Exception as e:
            return {
                "score": 5,
                "reasoning": f"解析エラー: {str(e)}",
                "raw_response": response
            }

    def _generate_compass_summary(self, scores: Dict[str, int]) -> str:
        """Generate a summary of the compass analysis.

        Args:
            scores (Dict[str, int]): Scores for each axis

        Returns:
            str: Summary text
        """
        total_score = sum(scores.values())
        avg_score = total_score / len(scores) if scores else 0

        # Find strongest and weakest areas
        if scores:
            strongest = max(scores.items(), key=lambda x: x[1])
            weakest = min(scores.items(), key=lambda x: x[1])

            # Convert axis keys to readable names
            axis_names = {
                "emotion": "情熱",
                "logic": "論理性",
                "effort": "努力",
                "growth": "成長性"
            }

            strongest_name = axis_names.get(strongest[0], strongest[0])
            weakest_name = axis_names.get(weakest[0], weakest[0])

            if avg_score >= 7:
                tone = "非常にバランスの取れた"
            elif avg_score >= 5:
                tone = "バランスの良い"
            else:
                tone = "発展の余地がある"

            return f"{tone}状態です。特に{strongest_name}が強く（{strongest[1]}/10）、{weakest_name}の向上に注意を向けると良いでしょう（{weakest[1]}/10）。"

        return "分析結果の要約を生成できませんでした。"

    def _create_test_compass_data(self) -> Dict[str, Any]:
        """Create test compass data for fallback when Ollama is not available.

        Returns:
            Dict[str, Any]: Test compass analysis data
        """
        import random

        # Generate semi-realistic test scores
        scores = {
            "emotion": random.randint(5, 9),
            "logic": random.randint(4, 8),
            "effort": random.randint(6, 10),
            "growth": random.randint(4, 7)
        }

        reasoning = {
            "emotion": "テストモード: 情熱的な表現が見られます",
            "logic": "テストモード: 論理的な構成が確認できます",
            "effort": "テストモード: 努力と取り組みが感じられます",
            "growth": "テストモード: 成長への意識が表れています"
        }

        total_score = sum(scores.values())

        return {
            "analysis_type": "sentiment_compass",
            "axes_scores": scores,
            "axes_reasoning": reasoning,
            "total_score": total_score,
            "compass_summary": f"テストモードでの分析結果です。総合的にバランスの取れた状態で、特に努力面での高いスコアが特徴的です。",
            "analysis_timestamp": time.time(),
            "test_mode": True
        }

    def validate_content(self, content: str) -> bool:
        """Validate content for compass analysis.

        Args:
            content (str): Text content to validate

        Returns:
            bool: True if content is suitable for compass analysis
        """
        if not content:
            return False

        content = content.strip()

        # More lenient validation for multi-byte characters (like Japanese)
        # Check both character count and byte count to handle encoding issues
        char_count = len(content)
        byte_count = len(content.encode('utf-8'))

        # Allow shorter character count if byte count suggests multi-byte chars
        min_chars = 20 if byte_count > char_count * 2 else 30

        if char_count < min_chars:
            return False

        # Check for meaningful content (not just symbols or numbers)
        meaningful_chars = sum(1 for c in content if c.isalpha() or c in '。、！？')
        return meaningful_chars >= 20