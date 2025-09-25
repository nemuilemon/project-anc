"""Alice Chat Manager for Project A.N.C.

This module provides the AliceChatManager class for handling conversations
with the AI maid 'Alice' using Google Gemini API.
"""

import os
import time
import json
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

class AliceChatManager:
    """Manages conversations with Alice using Gemini API.

    This class handles the AI chat functionality, including:
    - Gemini API client initialization
    - System instruction loading from file
    - Conversation history management
    - Message sending and receiving
    """

    def __init__(self, config):
        """Initialize the Alice Chat Manager.

        Args:
            config: Configuration object containing API key and system prompt path
        """
        self.config = config
        self.client = None
        self.system_instruction = ""
        self.history = []
        self.max_history_length = getattr(config, 'ALICE_CHAT_CONFIG', {}).get('max_history_length', 50)

        # Initialize API client
        self._init_client()

        # Load system instruction from file
        self._load_system_instruction()

    def _init_client(self):
        """Initialize the Gemini API client."""
        try:
            api_key = getattr(self.config, 'GEMINI_API_KEY', '')
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set in configuration")

            # Set API key as environment variable for genai client
            os.environ['GOOGLE_API_KEY'] = api_key

            self.client = genai.Client()
            print("Gemini API client initialized successfully")

        except Exception as e:
            print(f"Failed to initialize Gemini API client: {e}")
            self.client = None

    def _load_system_instruction(self):
        """Load system instruction from the specified file."""
        try:
            system_prompt_path = getattr(self.config, 'ALICE_SYSTEM_PROMPT_PATH', '')
            if not system_prompt_path or not os.path.exists(system_prompt_path):
                raise FileNotFoundError(f"System prompt file not found: {system_prompt_path}")

            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                self.system_instruction = f.read().strip()

            print(f"System instruction loaded from: {system_prompt_path}")

        except Exception as e:
            print(f"Failed to load system instruction: {e}")
            # Fallback system instruction
            self.system_instruction = "You are Alice, a helpful AI assistant."

    def send_message(self, user_message: str) -> str:
        """Send a message to Alice and get the response.

        Args:
            user_message (str): The user's message

        Returns:
            str: Alice's response message
        """
        if not self.client:
            return "エラー: Gemini APIクライアントが初期化されていません。"

        if not user_message or not user_message.strip():
            return "メッセージを入力してください。"

        try:
            # Add user message to history
            user_entry = {
                'role': 'user',
                'content': user_message.strip(),
                'timestamp': time.time()
            }
            self.history.append(user_entry)

            # Prepare conversation contents for API
            contents = self._prepare_contents()

            # Debug: Log contents structure (for development)
            print(f"API Contents: {len(contents)} blocks prepared")
            for i, content in enumerate(contents):
                content_preview = content[:100].replace('\n', '\\n') + "..." if len(content) > 100 else content.replace('\n', '\\n')
                print(f"  Block {i+1}: {content_preview}")

            # Get model name from config
            model_name = getattr(self.config, 'ALICE_CHAT_CONFIG', {}).get('model', 'gemini-2.0-flash-exp')

            # Make API request
            response = self.client.models.generate_content(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction
                ),
                contents=contents
            )

            # Extract response text
            response_text = response.text if hasattr(response, 'text') else str(response)

            # Add Alice's response to history
            alice_entry = {
                'role': 'model',
                'content': response_text,
                'timestamp': time.time()
            }
            self.history.append(alice_entry)

            # Trim history if it's too long
            self._trim_history()

            return response_text

        except Exception as e:
            error_message = f"申し訳ございません。エラーが発生しました: {str(e)}"
            print(f"Error in send_message: {e}")
            return error_message

    def _prepare_contents(self) -> List[str]:
        """Prepare conversation contents for the API request.

        今日のチャットログファイルの内容 + 現在のチャットボックスの会話履歴を組み合わせて送信

        Returns:
            List[str]: List of message contents
        """
        contents = []

        # 1. 今日のチャットログファイルの内容を読み込み
        today_log_content = self._load_today_chat_log()
        if today_log_content:
            contents.append(f"=== 今日のチャット履歴 ===\n{today_log_content}")

        # 2. 現在のチャットボックスの会話履歴を追加
        if self.history:
            chatbox_content = "=== 現在のセッション ===\n"
            for entry in self.history:
                role_name = "ご主人様" if entry['role'] == 'user' else "ありす"
                chatbox_content += f"\n**{role_name}:**\n{entry['content']}\n"

            contents.append(chatbox_content)

        # 3. 最新のユーザーメッセージを明示的に追加（APIが確実に認識するため）
        if self.history and self.history[-1]['role'] == 'user':
            contents.append(f"最新メッセージ: {self.history[-1]['content']}")

        return contents if contents else ["こんにちは"]

    def _load_today_chat_log(self) -> Optional[str]:
        """今日のチャットログファイルを読み込む

        Returns:
            Optional[str]: 今日のチャットログの内容、ファイルが存在しない場合はNone
        """
        try:
            from datetime import datetime
            import os

            # 今日の日付でログファイルパスを構築
            today = datetime.now().strftime("%Y-%m-%d")
            chat_logs_dir = getattr(self.config, 'CHAT_LOGS_DIR',
                                  os.path.join(getattr(self.config, 'PROJECT_ROOT', '.'), "data", "chat_logs"))
            log_file_path = os.path.join(chat_logs_dir, f"{today}.md")

            # ファイルが存在するかチェック
            if not os.path.exists(log_file_path):
                return None

            # ファイルを読み込み
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            # 内容が空の場合はNoneを返す
            return content if content else None

        except Exception as e:
            print(f"Error loading today's chat log: {e}")
            return None

    def _trim_history(self):
        """Trim conversation history to maintain performance."""
        if len(self.history) > self.max_history_length:
            # Keep the most recent messages
            self.history = self.history[-self.max_history_length:]

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history.

        Returns:
            List[Dict[str, Any]]: List of conversation entries
        """
        return self.history.copy()

    def clear_history(self):
        """Clear the conversation history."""
        self.history.clear()
        print("Conversation history cleared")

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation.

        Returns:
            Dict[str, Any]: Conversation summary with statistics
        """
        total_messages = len(self.history)
        user_messages = len([msg for msg in self.history if msg['role'] == 'user'])
        alice_messages = len([msg for msg in self.history if msg['role'] == 'model'])

        return {
            'total_messages': total_messages,
            'user_messages': user_messages,
            'alice_messages': alice_messages,
            'conversation_started': self.history[0]['timestamp'] if self.history else None,
            'last_message': self.history[-1]['timestamp'] if self.history else None
        }

    def export_conversation(self, format_type: str = 'json') -> str:
        """Export conversation history in specified format.

        Args:
            format_type (str): Export format ('json' or 'markdown')

        Returns:
            str: Formatted conversation history
        """
        if format_type.lower() == 'json':
            return json.dumps(self.history, ensure_ascii=False, indent=2)

        elif format_type.lower() == 'markdown':
            md_content = "# 会話履歴\n\n"
            for entry in self.history:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry['timestamp']))
                role = "ご主人様" if entry['role'] == 'user' else "ありす"
                md_content += f"## {role} ({timestamp})\n\n{entry['content']}\n\n"
            return md_content

        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    def is_available(self) -> bool:
        """Check if Alice Chat is available (API client is initialized).

        Returns:
            bool: True if available, False otherwise
        """
        return self.client is not None and bool(getattr(self.config, 'GEMINI_API_KEY', ''))