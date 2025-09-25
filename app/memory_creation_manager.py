"""Memory Creation Manager for Project A.N.C.

This module provides the MemoryCreationManager class for generating
daily memories from chat logs using Google Gemini API.
"""

import os
import time
from typing import Tuple, Optional
from datetime import datetime
from google import genai
from google.genai import types


class MemoryCreationManager:
    """Manages memory creation from daily chat logs using Gemini API.

    This class handles:
    - Loading chat log files for specific dates
    - Loading memory generation prompt templates
    - Generating memories using Gemini API
    - Error handling for various failure scenarios
    """

    def __init__(self, config):
        """Initialize the Memory Creation Manager.

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
            print("Memory Creation Manager: Gemini API client initialized successfully")

        except Exception as e:
            print(f"Failed to initialize Gemini API client for memory creation: {e}")
            self.client = None

    def _load_prompt_template(self):
        """Load memory creation prompt template from file."""
        try:
            prompt_path = getattr(self.config, 'CREATE_MEMORY_PROMPT_PATH', '')
            if not prompt_path or not os.path.exists(prompt_path):
                raise FileNotFoundError(f"Memory creation prompt file not found: {prompt_path}")

            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.prompt_template = f.read().strip()

            print(f"Memory creation prompt template loaded from: {prompt_path}")

        except Exception as e:
            print(f"Failed to load memory creation prompt template: {e}")
            # Fallback prompt template
            self.prompt_template = """
以下のチャットログから、この一日の「記憶」を生成してください。

チャットログ:
{chat_log_content}

出力フォーマット:
#### 記憶：{target_date_formatted}

* **タイトル:** [この一日を象徴するタイトル]
* **主要な出来事:** [重要な出来事のリスト]
* **成果と学び:** [得られた学びや成果]
* **総括:** [この日の意味と感想]
"""

    def create_memory(self, target_date: str) -> Tuple[bool, str]:
        """Create memory for the specified date.

        Args:
            target_date (str): Target date in YYYY-MM-DD format

        Returns:
            Tuple[bool, str]: (success, result_message_or_error)
        """
        if not self.client:
            return False, "Gemini APIクライアントが初期化されていません。"

        if not target_date:
            return False, "日付を指定してください。"

        try:
            # Load chat log for the target date
            chat_log_content = self._load_chat_log(target_date)
            if chat_log_content is None:
                return False, f"指定された日付（{target_date}）のチャットログが見つかりません。"

            if not chat_log_content.strip():
                return False, f"指定された日付（{target_date}）のチャットログは空です。"

            # Format the date for display
            target_date_formatted = self._format_date_for_display(target_date)

            # Prepare the final prompt
            final_prompt = self.prompt_template.format(
                chat_log_content=chat_log_content,
                target_date_formatted=target_date_formatted
            )

            # Debug: Log prompt length
            print(f"Memory creation prompt prepared: {len(final_prompt)} characters")

            # Get model name from config
            model_name = getattr(self.config, 'ALICE_CHAT_CONFIG', {}).get('model', 'gemini-2.0-flash-exp')

            # Make API request
            response = self.client.models.generate_content(
                model=model_name,
                contents=[final_prompt]
            )

            # Extract response text
            memory_text = response.text if hasattr(response, 'text') else str(response)

            if not memory_text or not memory_text.strip():
                return False, "AIから空の応答が返されました。再試行してください。"

            return True, memory_text.strip()

        except Exception as e:
            error_message = f"記憶の生成中にエラーが発生しました: {str(e)}"
            print(f"Error in create_memory: {e}")
            return False, error_message

    def _load_chat_log(self, target_date: str) -> Optional[str]:
        """Load chat log file for the specified date.

        Args:
            target_date (str): Target date in YYYY-MM-DD format

        Returns:
            Optional[str]: Chat log content or None if not found
        """
        try:
            # Construct chat log file path
            chat_logs_dir = getattr(self.config, 'CHAT_LOGS_DIR', '')
            if not chat_logs_dir:
                raise ValueError("CHAT_LOGS_DIR is not configured")

            log_file_path = os.path.join(chat_logs_dir, f"{target_date}.md")

            # Check if file exists
            if not os.path.exists(log_file_path):
                return None

            # Read file content
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return content

        except Exception as e:
            print(f"Error loading chat log for {target_date}: {e}")
            return None

    def _format_date_for_display(self, date_str: str) -> str:
        """Format date string for display in memory.

        Args:
            date_str (str): Date in YYYY-MM-DD format

        Returns:
            str: Formatted date string
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%Y年%m月%d日")
        except ValueError:
            # Fallback to original string if parsing fails
            return date_str

    def is_available(self) -> bool:
        """Check if Memory Creation Manager is available.

        Returns:
            bool: True if available, False otherwise
        """
        return (self.client is not None and
                bool(getattr(self.config, 'GEMINI_API_KEY', '')) and
                bool(self.prompt_template))

    def get_status(self) -> dict:
        """Get current status of Memory Creation Manager.

        Returns:
            dict: Status information
        """
        return {
            'api_client_ready': self.client is not None,
            'prompt_template_loaded': bool(self.prompt_template),
            'config_available': bool(getattr(self.config, 'GEMINI_API_KEY', '')),
            'available': self.is_available()
        }