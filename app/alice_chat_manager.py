"""Alice Chat Manager for Project A.N.C.

This module provides the AliceChatManager class for handling conversations
with the AI maid 'Alice' using Google Gemini API.
"""

import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from state_manager import app_state
import requests
import base64
import mimetypes

class AliceChatManager:
    """Manages conversations with Alice using Chat API Client.

    This class handles the AI chat functionality, including:
    - API client communication
    - Conversation history management
    - Message sending and receiving
    - Local logging
    """

    def __init__(self, config):
        """Initialize the Alice Chat Manager.

        Args:
            config: Configuration object containing API endpoint and settings
        """
        self.config = config
        self.max_history_length = getattr(config, 'ALICE_CHAT_CONFIG', {}).get('max_history_length', 50)

        # Dialog logs directory
        self.dialog_logs_dir = os.path.join(getattr(config, 'PROJECT_ROOT', '.'), "logs", "dialogs")
        os.makedirs(self.dialog_logs_dir, exist_ok=True)

        # API Endpoint configuration
        self.api_base_url = getattr(config, 'CHAT_API_BASE_URL', 'http://localhost:8000')
        self.api_endpoint = f"{self.api_base_url.rstrip('/')}/chat/gemini"
        self.api_key = getattr(config, 'COMPASS_API_KEY', None)

    def _log_api_dialog(self, request_data: Dict[str, Any], api_response: Dict[str, Any], error: Optional[str] = None):
        """Log dialog to a unique file for each API call.

        Args:
            request_data: The request data sent to the API (partial - config only)
            api_response: The JSON response from the API
            error: Error message if the call failed
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S-%f")[:-3]  # milliseconds precision
            log_file_path = os.path.join(self.dialog_logs_dir, f"dialog-{timestamp}.json")

            # Count messages with images
            messages = request_data.get("messages", [])
            image_count = sum(1 for msg in messages if msg.get("images"))
            image_info = []
            for msg in messages:
                if msg.get("images"):
                    for img in msg["images"]:
                        image_info.append({
                            "mime_type": img.get("mime_type"),
                            "data_size": len(img.get("data", ""))
                        })

            log_data = {
                "timestamp": datetime.now().isoformat(),
                "request": {
                    "config": request_data.get("config", {}),
                    "message_count": len(messages),
                    "image_count": image_count,
                    "images": image_info if image_info else None
                },
                "response": api_response if not error else None,
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

    def _convert_to_chat_messages(self, new_message_index: Optional[int] = None) -> List[Dict[str, Any]]:
        """Convert conversation history to ChatMessage format for API.

        Args:
            new_message_index: Index of the new message (only this message's image will be included).
                             If None, no images will be included (backward compatibility).

        Returns:
            List[Dict[str, Any]]: List of messages in ChatMessage format
        """
        history = app_state.get_conversation_messages()
        messages = []

        for idx, msg in enumerate(history):
            # Only include image data for the NEW message (not historical messages)
            should_include_image = (
                new_message_index is not None and
                idx == new_message_index and
                msg.get('metadata') and
                msg['metadata'].get('image_path')
            )

            if should_include_image:
                image_path = msg['metadata']['image_path']

                try:
                    # Read and encode image
                    with open(image_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')

                    # Determine MIME type
                    mime_type, _ = mimetypes.guess_type(image_path)
                    if mime_type is None or not mime_type.startswith('image/'):
                        mime_type = "image/jpeg"  # Default fallback

                    # Build ChatMessage with images (Compass API v1.3.0 format)
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content'],
                        "images": [
                            {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        ]
                    })
                    print(f"DEBUG: Image encoded for NEW message - {mime_type}, size: {len(image_data)} chars")

                except FileNotFoundError:
                    print(f"WARNING: Image file not found: {image_path}. Sending text only.")
                    # Send message without image if file not found
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
                except Exception as e:
                    print(f"ERROR: Failed to encode image {image_path}: {e}. Sending text only.")
                    # Send message without image if encoding fails
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
            else:
                # Text-only message (even if it originally had an image in history)
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })

        return messages

    def _build_chat_config(self) -> Dict[str, Any]:
        """Build ChatGeminiConfig format from ANC configuration.

        Returns:
            Dict[str, Any]: Configuration in ChatGeminiConfig format matching API server expectations
        """
        alice_config = getattr(self.config, 'ALICE_CHAT_CONFIG', {})
        compass_config = getattr(self.config, 'COMPASS_API_CONFIG', {})

        # Build config matching chat.py's ChatGeminiConfig
        model_name = alice_config.get('gemini_model', 'gemini-2.5-flash')

        # Build config with correct field order matching API server expectations
        limit = compass_config.get('limit', 0)

        config = {
            "model": model_name  # Top-level model (API server uses this)
        }

        # Only add memory_search_config if limit > 0 (API server requires limit > 0)
        if limit > 0:
            config["memory_search_config"] = {
                "enabled": True,
                "target": compass_config.get('target', 'content'),
                "limit": limit,
                "search_type": "graph" if compass_config.get('endpoint') == 'graph_search' else "normal"
            }

        return config

    def _call_chat_api(self, messages: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Chat API with messages and config.

        Args:
            messages: List of ChatMessage objects
            config: ChatGeminiConfig object

        Returns:
            Dict[str, Any]: API response JSON

        Raises:
            requests.HTTPError: If the API returns an error
            requests.Timeout: If the request times out
        """
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        request_data = {
            "messages": messages,
            "config": config
        }

        # Make API request
        response = requests.post(
            self.api_endpoint,
            json=request_data,
            headers=headers,
            timeout=90
        )

        response.raise_for_status()
        return response.json()

    def send_message(self, user_message: str, image_path: Optional[str] = None) -> str:
        """Send a message to Alice via API and get the response.

        Args:
            user_message (str): The user's message
            image_path (Optional[str]): Path to the image file (supports Compass API v1.3.0 multimodal)

        Returns:
            str: Alice's response message
        """
        if image_path:
            print(f"INFO: 画像を含むメッセージを送信します。")

        if not user_message.strip() and not image_path:
            return "メッセージを送信してください。"

        try:
            # 1. AppStateにユーザーメッセージ追加
            app_state.add_conversation_message(
                'user',
                user_message.strip(),
                metadata={'image_path': image_path} if image_path else None
            )

            # 2. APIリクエスト構築 - 新しいメッセージのインデックスを取得
            history = app_state.get_conversation_messages()
            new_message_index = len(history) - 1  # 最後のメッセージが新しいメッセージ

            # 画像は新しいメッセージのみに含める（履歴の画像は送信しない）
            messages = self._convert_to_chat_messages(new_message_index)
            config = self._build_chat_config()
            request_data = {"messages": messages, "config": config}

            # 3. API呼び出し
            api_response = self._call_chat_api(messages, config)
            response_text = api_response['response']['content']

            # 4. AppStateにモデルレスポンス追加
            app_state.add_conversation_message('model', response_text)

            # 5. ローカルログ保存
            self._save_to_chat_log(user_message.strip(), response_text)
            self._log_api_dialog(request_data, api_response)

            # 6. Trim history if it's too long
            self._trim_history()

            return response_text

        except requests.HTTPError as e:
            error_msg = f"APIエラー ({e.response.status_code})"
            try:
                error_detail = e.response.json().get('detail', '詳細不明')
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {e.response.text[:200]}"
            print(f"HTTP Error: {error_msg}")
            return error_msg
        except requests.Timeout:
            error_msg = "エラー: APIがタイムアウトしました。"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"申し訳ございません。エラーが発生しました: {str(e)}"
            print(f"Error in send_message: {e}")
            return error_msg

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
        """Check if Alice Chat is available (API endpoint is configured).

        Returns:
            bool: True if available, False otherwise
        """
        return bool(getattr(self.config, 'CHAT_API_BASE_URL', ''))