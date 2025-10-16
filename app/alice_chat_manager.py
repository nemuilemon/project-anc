"""Alice Chat Manager for Project A.N.C.

This module provides the AliceChatManager class for handling conversations
with the AI maid 'Alice' using Google Gemini API.
"""

import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from state_manager import app_state
import requests
import PIL.Image

# OpenAI import (optional, will be None if not installed)
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

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
        self.api_provider = getattr(config, 'CHAT_API_PROVIDER', 'google').lower()
        self.system_instruction = ""
        self.long_term_memory = ""
        self.max_history_length = getattr(config, 'ALICE_CHAT_CONFIG', {}).get('max_history_length', 50)

        # Dialog logs directory
        self.dialog_logs_dir = os.path.join(getattr(config, 'PROJECT_ROOT', '.'), "logs", "dialogs")
        os.makedirs(self.dialog_logs_dir, exist_ok=True)

        # Initialize API client
        self._init_client()

        # Load system instruction and memory from files
        self._load_system_instruction()
        self._load_long_term_memory()

    def _init_client(self):
        """Initialize the API client based on configured provider."""
        try:
            if self.api_provider == 'google':
                # Initialize Google Gemini client
                api_key = getattr(self.config, 'GEMINI_API_KEY', '')
                if not api_key:
                    raise ValueError("GEMINI_API_KEY is not set in configuration")

                # Set API key as environment variable for genai client
                os.environ['GOOGLE_API_KEY'] = api_key

                self.client = genai.Client()
                print("Gemini API client initialized successfully")

            elif self.api_provider == 'openai':
                # Initialize OpenAI client
                if OpenAI is None:
                    raise ImportError("OpenAI library is not installed. Run: pip install openai")

                api_key = getattr(self.config, 'OPENAI_API_KEY', '')
                if not api_key:
                    raise ValueError("OPENAI_API_KEY is not set in configuration")

                self.client = OpenAI(api_key=api_key)
                print("OpenAI API client initialized successfully")

            else:
                raise ValueError(f"Unknown API provider: {self.api_provider}")

        except Exception as e:
            print(f"Failed to initialize API client: {e}")
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

    def _load_long_term_memory(self):
        """Load long-term memory from the specified file."""
        try:
            memory_file_path = getattr(self.config, 'ALICE_MEMORY_FILE_PATH', '')
            if memory_file_path and os.path.exists(memory_file_path):
                with open(memory_file_path, 'r', encoding='utf-8') as f:
                    self.long_term_memory = f.read().strip()
                print(f"Long-term memory loaded from: {memory_file_path}")
            else:
                print("Long-term memory file not found or not configured. Skipping.")
        except Exception as e:
            print(f"Failed to load long-term memory: {e}")
            self.long_term_memory = ""

    def _log_dialog(self, request_contents: List[str], response_text: str, error: Optional[str] = None):
        """Log dialog to a unique file for each API call.

        Args:
            request_contents: The contents sent to the API
            response_text: The response from the API
            error: Error message if the call failed
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S-%f")[:-3]  # milliseconds precision
            log_file_path = os.path.join(self.dialog_logs_dir, f"dialog-{timestamp}.json")

            log_data = {
                "timestamp": datetime.now().isoformat(),
                "request": {
                    "contents": request_contents,
                    "model": getattr(self.config, 'ALICE_CHAT_CONFIG', {}).get('model', 'gemini-2.5-flash')
                },
                "response": response_text if not error else None,
                "error": error
            }

            with open(log_file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)

            print(f"Dialog logged to: {log_file_path}")

        except Exception as e:
            print(f"Failed to log dialog: {e}")

    def _save_to_chat_log(self, user_message: str, alice_response: str):
        """Save conversation to daily chat log file.

        Args:
            user_message: The user's message
            alice_response: Alice's response
        """
        try:
            import sys
            sys.path.append(os.path.dirname(__file__))
            from date_utils import get_current_log_date

            # Get today's log date (3AM rule)
            today = get_current_log_date()
            chat_logs_dir = getattr(self.config, 'CHAT_LOGS_DIR',
                                  os.path.join(getattr(self.config, 'PROJECT_ROOT', '.'), "data", "chat_logs"))
            os.makedirs(chat_logs_dir, exist_ok=True)

            log_file_path = os.path.join(chat_logs_dir, f"{today}.md")
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Append to today's log file
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n## {timestamp}\n\n")
                f.write(f"**ご主人様:**\n{user_message}\n\n")
                f.write(f"**ありす:**\n{alice_response}\n\n")
                f.write("---------\n")

            print(f"Conversation saved to: {log_file_path}")

        except Exception as e:
            print(f"Failed to save conversation to chat log: {e}")

    def send_message(self, user_message: str, image_path: Optional[str] = None) -> str:
        """Send a message to Alice and get the response.

        Args:
            user_message (str): The user's message
            image_path (Optional[str]): Path to the image to be sent

        Returns:
            str: Alice's response message
        """
        if not self.client:
            return f"エラー: {self.api_provider.upper()} APIクライアントが初期化されていません。"

        if not user_message.strip() and not image_path:
            return "メッセージまたは画像を送信してください。"

        try:
            # Add user message to AppState
            app_state.add_conversation_message(
                'user',
                user_message.strip(),
                metadata={'image_path': image_path} if image_path else None
            )

            # Route to appropriate API handler
            if self.api_provider == 'google':
                response_text = self._send_message_gemini(image_path)
            elif self.api_provider == 'openai':
                response_text = self._send_message_openai(image_path)
            else:
                raise ValueError(f"Unknown API provider: {self.api_provider}")

            # Add Alice's response to AppState
            app_state.add_conversation_message('model', response_text)

            # Trim history if it's too long
            self._trim_history()

            return response_text

        except Exception as e:
            error_message = f"申し訳ございません。エラーが発生しました: {str(e)}"
            print(f"Error in send_message: {e}")
            return error_message

    def _send_message_gemini(self, image_path: Optional[str] = None) -> str:
        """Send message using Google Gemini API.

        Args:
            image_path (Optional[str]): Path to the image to be sent

        Returns:
            str: Alice's response message
        """
        # Prepare conversation contents for API
        prompt_parts = self._prepare_contents()
        contents = []
        for part in prompt_parts:
            if isinstance(part, str):
                contents.append(part)

        # Add image if provided
        if image_path:
            try:
                import mimetypes
                mime_type, _ = mimetypes.guess_type(image_path)
                if mime_type is None:
                    mime_type = 'image/jpeg' # Default mime type
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                contents.insert(0, types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ))
            except Exception as e:
                return f"画像ファイルの読み込みに失敗しました: {e}"

        # Get model name from config
        model_name = getattr(self.config, 'ALICE_CHAT_CONFIG', {}).get('gemini_model', 'gemini-2.5-flash')

        # Debug: Log contents being sent to the API
        print("\n" + "="*80)
        print(f"--- Calling Gemini API ({model_name}) ---")
        print(f"\n--- [System Instruction] ---\n{self.system_instruction}")
        print(f"\n--- Total parts: {len(contents)} ---")
        for i, part in enumerate(contents):
            if isinstance(part, str):
                print(f"\n--- [Content Part {i+1}: Text] ---\n{part}")
            else:  # It's an image part
                print(f"\n--- [Content Part {i+1}: Image] ---\nPath: {image_path}")
        print("\n" + "="*80 + "\n")

        # Make API request
        response = self.client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction
            )
        )

        # Extract response text
        response_text = response.text if hasattr(response, 'text') else str(response)

        # Log the dialog (for debugging/API tracking)
        self._log_dialog([str(p) for p in contents], response_text)

        return response_text

    def _send_message_openai(self, image_path: Optional[str] = None) -> str:
        """Send message using OpenAI API.

        Args:
            image_path (Optional[str]): Path to the image to be sent

        Returns:
            str: Alice's response message
        """
        # Prepare conversation contents
        contents = self._prepare_contents()

        # Convert contents to OpenAI messages format
        messages = []

        # Add system instruction as system message
        if self.system_instruction:
            messages.append({
                "role": "system",
                "content": self.system_instruction
            })

        # Add context blocks as user messages
        history = app_state.get_conversation_messages()
        for content in contents:
            # Skip the last user message if it's already in history
            if history and content.strip().startswith(history[-1]['content'][:50]):
                continue
            messages.append({
                "role": "user",
                "content": content
            })

        # Add conversation history from AppState
        for msg in history:
            message_content = [{"type": "text", "text": msg['content']}]
            if msg.get('metadata') and msg['metadata'].get('image_path'):
                image_path = msg['metadata']['image_path']
                try:
                    import base64
                    with open(image_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })
                except Exception as e:
                    print(f"Failed to encode image: {e}")

            messages.append({
                "role": "user" if msg['role'] == 'user' else "assistant",
                "content": message_content
            })

        # Get model name from config
        model_name = getattr(self.config, 'ALICE_CHAT_CONFIG', {}).get('openai_model', 'gpt-4-turbo')

        # Debug: Log messages being sent to the API
        print("\n" + "="*80)
        print(f"--- Calling OpenAI API ({model_name}) ---")
        print(f"\n--- [System Instruction] ---\n{self.system_instruction}")
        print(f"\n--- Total messages: {len(messages)} ---")
        
        # Create a serializable version of messages for logging, replacing image data
        import json
        messages_for_log = []
        has_image = False
        for msg in messages:
            log_msg = msg.copy()
            if isinstance(log_msg.get('content'), list):
                new_content_list = []
                for content_part in log_msg['content']:
                    if content_part.get('type') == 'image_url':
                        has_image = True
                        # Replace base64 data with a placeholder. The original path is not
                        # available in the final payload structure.
                        new_content_list.append({
                            "type": "image_url",
                            "image_path_note": "Path not available in final payload, see history item for path",
                            "image_url": {"url": "data:image/...;base64,[...truncated...]"}
                        })
                    else:
                        new_content_list.append(content_part)
                log_msg['content'] = new_content_list
            messages_for_log.append(log_msg)

        print(json.dumps(messages_for_log, indent=2, ensure_ascii=False))
        if has_image:
            print("\nNOTE: For OpenAI, image paths are not available in the final payload.")
            print("The 'image_path_note' is a reminder that the path is associated with the message in the conversation history state.")

        print("\n" + "="*80 + "\n")

        # Make API request
        response = self.client.chat.completions.create(
            model=model_name,
            messages=messages
        )

        # Extract response text
        response_text = response.choices[0].message.content

        # Log the dialog (for debugging/API tracking)
        self._log_dialog([str(messages)], response_text)

        return response_text

    def _get_past_conversations_from_compass_api(self, query_text: str) -> Optional[str]:
        """
        compass-apiを使用して過去の関連会話履歴を取得する。
        APIから返されるJSONデータを解析し、timestampとcontentのみを抽出して整形する。

        サポートされるエンドポイント:
        - /search: 標準的なベクトル類似度検索
        - /graph_search: 関連する記憶も含むグラフ検索
        """
        # 設定を動的にリロード（最新の値を取得）
        import importlib
        importlib.reload(self.config)

        compass_api_base_url = getattr(self.config, 'COMPASS_API_BASE_URL', None)
        api_config = getattr(self.config, 'COMPASS_API_CONFIG', {})

        if not compass_api_base_url:
            return None

        try:
            # エンドポイントタイプを取得 (search または graph_search)
            endpoint_type = api_config.get("endpoint", "search")
            compass_api_url = f"{compass_api_base_url.rstrip('/')}/{endpoint_type}"

            # UIから設定された値を使ってpayloadを構築
            payload = {
                "text": query_text,
                "config": {
                    "target": api_config.get("target", "content"),
                    "limit": api_config.get("limit", 3),
                    "compress": api_config.get("compress", False)  # 圧縮は使用しない
                }
            }

            # graph_searchの場合はrelated_limitも追加
            if endpoint_type == "graph_search":
                payload["config"]["related_limit"] = api_config.get("related_limit", 3)

            # デバッグ: 送信するpayloadをログ出力
            print(f"[Compass API] Endpoint: {compass_api_url}")
            print(f"[Compass API] Sending payload: {payload['config']}")
            print(f"[Compass API] Query text length: {len(query_text)} chars")

            # タイムアウトを設定
            response = requests.post(compass_api_url, json=payload, timeout=90)
            response.raise_for_status()  # エラーがあれば例外を発生させる

            # JSONレスポンスをパース
            data = response.json()
            results = data.get("results", [])

            if not results:
                return None

            # timestampとcontentを抽出して整形
            formatted_results = []
            for result in results:
                timestamp = result.get('timestamp', 'N/A')
                content = result.get('content', '内容なし')
                formatted_results.append(f"時刻: {timestamp}\n内容: {content}")

            print(f"[Compass API] Retrieved {len(results)} results")
            return "\n\n---\n\n".join(formatted_results)

        except requests.exceptions.RequestException as e:
            print(f"Error calling compass-api: {e}")
            return None
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON from compass-api response.")
            return None
        
    def _prepare_contents(self) -> List[Any]:
        """Prepare conversation contents for the API request.

        APIに渡す情報は以下の5つの要素で構成されます:
        1. 長期記憶（0-Memory.md）
        2. 過去の関連会話履歴（compass-apiから取得）
        3. 今日の会話履歴（末尾から指定文字数）
        4. 現在のセッションの会話履歴

        Returns:
            List[Any]: List of message contents (strings and potentially images)
        """
        contents = []

        # 1. 長期記憶（0-Memory.md）の内容を追加
        if self.long_term_memory:
            contents.append(f"=== 長期記憶 ===\n{self.long_term_memory}")

        # 2. 今日のチャットログファイルの内容を読み込み
        char_limit = getattr(self.config, 'ALICE_CHAT_CONFIG', {}).get('history_char_limit', 4000)
        today_log_content = self._load_today_chat_log(char_limit)

        # 3. 検索モードに基づいてクエリテキストを決定
        api_config = getattr(self.config, 'COMPASS_API_CONFIG', {})
        search_mode = api_config.get('search_mode', 'latest')
        history = app_state.get_conversation_messages()

        query_text = None
        if search_mode == 'latest':
            # 最新メッセージのみを使用
            if history and history[-1]['role'] == 'user':
                query_text = history[-1]['content']
        elif search_mode == 'history':
            # 最近の会話履歴を使用
            query_text = today_log_content

        # 4. compass-apiから過去の関連会話履歴を取得
        if query_text:
            past_conversations = self._get_past_conversations_from_compass_api(query_text)
            if past_conversations:
                contents.append(f"=== 過去の関連会話履歴 ===\n{past_conversations}")

        # 5. 今日の会話履歴を追加
        if today_log_content:
            contents.append(f"=== 今日の会話履歴 ===\n{today_log_content}")

        # 6. 現在のセッション履歴（AppStateから取得）
        if history:
            chatbox_content = "=== 現在のセッション ===\n"
            for entry in history:
                role_name = "ご主人様" if entry['role'] == 'user' else "ありす"
                chatbox_content += f"\n**{role_name}:**\n{entry['content']}\n"
            contents.append(chatbox_content)

        return contents if contents else ["こんにちは"]

    def _load_today_chat_log(self, char_limit: Optional[int] = None) -> Optional[str]:
        """今日のチャットログファイルを読み込む

        Args:
            char_limit (Optional[int]): 読み込む文字数の制限。Noneの場合は全て読み込む

        Returns:
            Optional[str]: 今日のチャットログの内容、ファイルが存在しない場合はNone
        """
        try:
            from datetime import datetime
            import os
            import sys
            sys.path.append(os.path.dirname(__file__))
            from date_utils import get_current_log_date

            # 3AM ルールに基づいて今日のログ日付を決定
            today = get_current_log_date()
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
            if not content:
                return None
            
            # 文字数制限0の場合return None
            if char_limit == 0:
                return None

            # 文字数制限が指定されている場合は末尾から指定された文字数を取得
            if char_limit is not None and len(content) > char_limit:
                content = content[-char_limit:]

            return content

        except Exception as e:
            print(f"Error loading today's chat log: {e}")
            return None

    def _trim_history(self):
        """Trim conversation history to maintain performance."""
        history = app_state.get_conversation_messages()
        if len(history) > self.max_history_length:
            # Keep the most recent messages
            # Re-initialize conversation with trimmed history
            session_id = f"alice_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            app_state.clear_conversation()
            app_state.init_conversation(session_id)
            for msg in history[-self.max_history_length:]:
                app_state.add_conversation_message(msg['role'], msg['content'], msg.get('metadata'))

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history.

        Returns:
            List[Dict[str, Any]]: List of conversation entries
        """
        return app_state.get_conversation_messages()

    def clear_history(self):
        """Clear the conversation history."""
        app_state.clear_conversation()
        # Re-initialize for new session
        session_id = f"alice_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        app_state.init_conversation(session_id)
        print("Conversation history cleared")

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation.

        Returns:
            Dict[str, Any]: Conversation summary with statistics
        """
        history = app_state.get_conversation_messages()
        conversation_state = app_state.get_conversation_state()

        total_messages = len(history)
        user_messages = len([msg for msg in history if msg['role'] == 'user'])
        alice_messages = len([msg for msg in history if msg['role'] == 'model'])

        return {
            'total_messages': total_messages,
            'user_messages': user_messages,
            'alice_messages': alice_messages,
            'conversation_started': conversation_state.started_at if conversation_state else None,
            'last_message': conversation_state.last_message_at if conversation_state else None
        }

    def export_conversation(self, format_type: str = 'json') -> str:
        """Export conversation history in specified format.

        Args:
            format_type (str): Export format ('json' or 'markdown')

        Returns:
            str: Formatted conversation history
        """
        history = app_state.get_conversation_messages()

        if format_type.lower() == 'json':
            return json.dumps(history, ensure_ascii=False, indent=2)

        elif format_type.lower() == 'markdown':
            md_content = "# 会話履歴\n\n"
            for entry in history:
                timestamp_str = entry.get('timestamp', '')
                role = "ご主人様" if entry['role'] == 'user' else "ありす"
                md_content += f"## {role} ({timestamp_str})\n\n{entry['content']}\n\n"
            return md_content

        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    def is_available(self) -> bool:
        """Check if Alice Chat is available (API client is initialized).

        Returns:
            bool: True if available, False otherwise
        """
        if self.api_provider == 'google':
            return self.client is not None and bool(getattr(self.config, 'GEMINI_API_KEY', ''))
        elif self.api_provider == 'openai':
            return self.client is not None and bool(getattr(self.config, 'OPENAI_API_KEY', ''))
        return False