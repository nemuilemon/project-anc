"""Nippo Creation Manager for Project A.N.C.

This module provides the NippoCreationManager class for generating
daily nippo (report) from memory files using Google Gemini API.
"""

import os
import time
from typing import Tuple, Optional
from datetime import datetime
from google import genai
from google.genai import types


class NippoCreationManager:
    """Manages nippo creation from daily memories using Gemini API.

    This class handles:
    - Loading memory files for specific dates
    - Loading nippo generation prompt templates
    - Generating nippo using Gemini API
    - Error handling for various failure scenarios
    """

    def __init__(self, config):
        """Initialize the Nippo Creation Manager.

        Args:
            config: Configuration object containing API key and file paths
        """
        self.config = config
        self.client = None
        self.prompt_template = ""

        # Initialize API client
        self._init_client()

        # Load prompt template
        self._load_prompt_template()

    def _init_client(self):
        """Initialize the Gemini API client."""
        try:
            api_key = getattr(self.config, 'GEMINI_API_KEY', '')
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set in configuration")

            # Set API key as environment variable for genai client
            os.environ['GOOGLE_API_KEY'] = api_key

            self.client = genai.Client()
            print("Nippo Creation Manager: Gemini API client initialized successfully")

        except Exception as e:
            print(f"Failed to initialize Gemini API client for nippo creation: {e}")
            self.client = None

    def _load_prompt_template(self):
        """Load nippo creation prompt template from file."""
        try:
            prompt_path = getattr(self.config, 'CREATE_NIPPO_PROMPT_PATH', '')
            if not prompt_path or not os.path.exists(prompt_path):
                raise FileNotFoundError(f"Nippo creation prompt file not found: {prompt_path}")

            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.prompt_template = f.read().strip()

            print(f"Nippo creation prompt template loaded from: {prompt_path}")

        except Exception as e:
            print(f"Failed to load nippo creation prompt template: {e}")
            # Fallback prompt template
            self.prompt_template = """
以下の記憶の内容を基に、学校提出用の「日報」を作成してください。

記憶の内容:
{memory_content}

出力フォーマット:
学習データ用のJSONL形式で、以下の構造に従って出力してください：

{{"input": "記憶の原文をそのまま", "output": "生成された日報"}}

日報の作成指針:
- 学習活動を中心に記述してください
- 約200字程度でまとめてください
- ですます調を使用してください
- 学校提出用として無難で適切な表現を心がけてください
"""

    def create_nippo(self, target_date: str) -> Tuple[bool, str]:
        """Create nippo for the specified date.

        Args:
            target_date (str): Target date in YYYY-MM-DD format

        Returns:
            Tuple[bool, str]: (success, result_jsonl_or_error)
        """
        if not self.client:
            return False, "Gemini APIクライアントが初期化されていません。"

        if not target_date:
            return False, "日付を指定してください。"

        try:
            # Load memory for the target date
            memory_content = self._load_memory(target_date)
            if memory_content is None:
                return False, f"指定された日付（{target_date}）の記憶ファイルが見つかりません。"

            if not memory_content.strip():
                return False, f"指定された日付（{target_date}）の記憶ファイルは空です。"

            # Prepare the final prompt
            final_prompt = self.prompt_template.format(memory_content=memory_content)

            # Debug: Log prompt length
            print(f"Nippo creation prompt prepared: {len(final_prompt)} characters")

            # Get model name from config
            model_name = getattr(self.config, 'ALICE_CHAT_CONFIG', {}).get('model', 'gemini-2.0-flash-exp')

            # Make API request
            response = self.client.models.generate_content(
                model=model_name,
                contents=[final_prompt]
            )

            # Extract response text
            nippo_jsonl = response.text if hasattr(response, 'text') else str(response)

            if not nippo_jsonl or not nippo_jsonl.strip():
                return False, "AIから空の応答が返されました。再試行してください。"

            return True, nippo_jsonl.strip()

        except Exception as e:
            error_message = f"日報の生成中にエラーが発生しました: {str(e)}"
            print(f"Error in create_nippo: {e}")
            return False, error_message

    def _load_memory(self, target_date: str) -> Optional[str]:
        """Load memory file for the specified date.

        Args:
            target_date (str): Target date in YYYY-MM-DD format

        Returns:
            Optional[str]: Memory file content or None if not found
        """
        try:
            # Construct memory file path
            memories_dir = getattr(self.config, 'MEMORIES_DIR', '')
            if not memories_dir:
                raise ValueError("MEMORIES_DIR is not configured")

            # Convert YYYY-MM-DD to YY.MM.DD format for memory filename
            date_obj = datetime.strptime(target_date, "%Y-%m-%d")
            memory_filename = f"memory-{date_obj.strftime('%y.%m.%d')}.md"
            memory_file_path = os.path.join(memories_dir, memory_filename)

            # Check if file exists
            if not os.path.exists(memory_file_path):
                return None

            # Read file content
            with open(memory_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return content

        except Exception as e:
            print(f"Error loading memory for {target_date}: {e}")
            return None

    def is_available(self) -> bool:
        """Check if Nippo Creation Manager is available.

        Returns:
            bool: True if available, False otherwise
        """
        return (self.client is not None and
                bool(getattr(self.config, 'GEMINI_API_KEY', '')) and
                bool(self.prompt_template))

    def get_status(self) -> dict:
        """Get current status of Nippo Creation Manager.

        Returns:
            dict: Status information
        """
        return {
            'api_client_ready': self.client is not None,
            'prompt_template_loaded': bool(self.prompt_template),
            'config_available': bool(getattr(self.config, 'GEMINI_API_KEY', '')),
            'available': self.is_available()
        }