"""State Management for Project A.N.C.

This module provides centralized state management for the application,
ensuring consistent state across all components and preventing state
inconsistencies.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
import threading
import json
import os


@dataclass
class FileState:
    """Represents the state of a file in the application."""
    path: str
    title: str
    content: str
    modified: bool = False
    tags: List[str] = field(default_factory=list)
    status: str = "active"  # active, archived
    last_modified: Optional[datetime] = None


@dataclass
class ConversationState:
    """Represents the state of a conversation with Alice."""
    session_id: str
    title: str = "新しい会話"
    messages: List[Dict[str, Any]] = field(default_factory=list)
    started_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None


class AppState:
    """Centralized state management for Project A.N.C.

    This class manages all application state including:
    - File states (open files, modifications, etc.)
    - Conversation history
    - UI state (selected tab, active file, etc.)
    - Application settings

    The state manager implements the Observer pattern, allowing
    components to subscribe to state changes.
    """

    def __init__(self, persistence_file: Optional[str] = None):
        """Initialize the application state.

        Args:
            persistence_file: Optional path to load/save state
        """
        # Thread safety
        self._lock = threading.RLock()

        # File states
        self._files: Dict[str, FileState] = {}
        self._active_file_path: Optional[str] = None

        # Conversation states (multiple conversations support)
        self._conversations: Dict[str, ConversationState] = {}
        self._active_conversation_id: Optional[str] = None

        # UI state
        self._selected_sidebar_tab: int = 0
        self._ui_visible: bool = True

        # Application settings
        self._settings: Dict[str, Any] = {}

        # Observers (callbacks for state changes)
        self._observers: Dict[str, List[Callable]] = {
            'file_added': [],
            'file_modified': [],
            'file_removed': [],
            'file_activated': [],
            'conversation_updated': [],
            'conversation_cleared': [],
            'settings_changed': [],
            'ui_state_changed': []
        }

        # Persistence
        self._persistence_file = persistence_file

        # Load state if persistence file exists
        if persistence_file:
            self.load_conversations(persistence_file)

    # File State Management

    def add_file(self, file_state: FileState) -> None:
        """Add a file to the state.

        Args:
            file_state: The file state to add
        """
        with self._lock:
            self._files[file_state.path] = file_state
            self._notify_observers('file_added', file_state)

    def update_file_content(self, path: str, content: str, modified: bool = True) -> None:
        """Update the content of a file.

        Args:
            path: The file path
            content: The new content
            modified: Whether the file is modified
        """
        with self._lock:
            if path in self._files:
                self._files[path].content = content
                self._files[path].modified = modified
                self._files[path].last_modified = datetime.now()
                self._notify_observers('file_modified', self._files[path])

    def remove_file(self, path: str) -> None:
        """Remove a file from the state.

        Args:
            path: The file path to remove
        """
        with self._lock:
            if path in self._files:
                file_state = self._files.pop(path)
                if self._active_file_path == path:
                    self._active_file_path = None
                self._notify_observers('file_removed', file_state)

    def get_file(self, path: str) -> Optional[FileState]:
        """Get a file state.

        Args:
            path: The file path

        Returns:
            The file state, or None if not found
        """
        with self._lock:
            return self._files.get(path)

    def get_all_files(self) -> List[FileState]:
        """Get all file states.

        Returns:
            List of all file states
        """
        with self._lock:
            return list(self._files.values())

    def set_active_file(self, path: Optional[str]) -> None:
        """Set the active file.

        Args:
            path: The file path to activate, or None to deactivate
        """
        with self._lock:
            if path and path not in self._files:
                raise ValueError(f"File not found: {path}")

            self._active_file_path = path
            if path:
                self._notify_observers('file_activated', self._files[path])

    def get_active_file(self) -> Optional[FileState]:
        """Get the active file state.

        Returns:
            The active file state, or None if no file is active
        """
        with self._lock:
            if self._active_file_path:
                return self._files.get(self._active_file_path)
            return None

    def get_modified_files(self) -> List[FileState]:
        """Get all modified files.

        Returns:
            List of modified file states
        """
        with self._lock:
            return [f for f in self._files.values() if f.modified]

    # Conversation State Management

    def create_new_conversation(self, title: Optional[str] = None) -> str:
        """Create a new conversation session.

        Args:
            title: Optional title for the conversation

        Returns:
            The session ID of the newly created conversation
        """
        with self._lock:
            import uuid
            session_id = f"session_{uuid.uuid4().hex[:8]}"

            # Generate default title if not provided
            if not title:
                conversation_count = len(self._conversations) + 1
                title = f"会話 {conversation_count}"

            self._conversations[session_id] = ConversationState(
                session_id=session_id,
                title=title,
                started_at=datetime.now()
            )

            # Set as active conversation
            self._active_conversation_id = session_id

            return session_id

    def set_active_conversation(self, session_id: str) -> None:
        """Set the active conversation.

        Args:
            session_id: The session ID to activate
        """
        with self._lock:
            if session_id not in self._conversations:
                raise ValueError(f"Conversation not found: {session_id}")

            self._active_conversation_id = session_id

    def get_active_conversation_id(self) -> Optional[str]:
        """Get the active conversation session ID.

        Returns:
            The active conversation session ID, or None if no conversation is active
        """
        with self._lock:
            return self._active_conversation_id

    def get_all_conversations(self) -> List[ConversationState]:
        """Get all conversation states.

        Returns:
            List of all conversation states
        """
        with self._lock:
            return list(self._conversations.values())

    def remove_conversation(self, session_id: str) -> None:
        """Remove a conversation session.

        Args:
            session_id: The session ID to remove
        """
        with self._lock:
            if session_id not in self._conversations:
                return

            # Remove the conversation
            del self._conversations[session_id]

            # If it was the active conversation, switch to another one
            if self._active_conversation_id == session_id:
                if self._conversations:
                    # Switch to the first available conversation
                    self._active_conversation_id = next(iter(self._conversations.keys()))
                else:
                    # No conversations left, create a new one
                    self.create_new_conversation()

    def init_conversation(self, session_id: str) -> None:
        """Initialize a new conversation session (deprecated, use create_new_conversation).

        Args:
            session_id: Unique session identifier
        """
        with self._lock:
            if session_id not in self._conversations:
                self._conversations[session_id] = ConversationState(
                    session_id=session_id,
                    started_at=datetime.now()
                )
                self._active_conversation_id = session_id

    def add_conversation_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a message to the active conversation.

        Args:
            role: The message role ('user' or 'model')
            content: The message content
            metadata: Optional metadata for the message
        """
        with self._lock:
            # Ensure there's an active conversation
            if not self._active_conversation_id or self._active_conversation_id not in self._conversations:
                self.create_new_conversation()

            message = {
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }

            conversation = self._conversations[self._active_conversation_id]
            conversation.messages.append(message)
            conversation.last_message_at = datetime.now()

            # Update title from first user message if still default
            if conversation.title.startswith("会話") and role == 'user' and len(conversation.messages) <= 2:
                # Use first 20 characters of user message as title
                conversation.title = content[:20] + ("..." if len(content) > 20 else "")

            self._notify_observers('conversation_updated', message)

    def clear_conversation(self, session_id: Optional[str] = None) -> None:
        """Clear messages in a conversation (or the active conversation).

        Args:
            session_id: The session ID to clear (uses active if None)
        """
        with self._lock:
            target_id = session_id or self._active_conversation_id
            if target_id and target_id in self._conversations:
                self._conversations[target_id].messages.clear()
                self._notify_observers('conversation_cleared', target_id)

    def get_conversation_messages(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get conversation messages.

        Args:
            session_id: The session ID (uses active if None)

        Returns:
            List of conversation messages
        """
        with self._lock:
            target_id = session_id or self._active_conversation_id
            if target_id and target_id in self._conversations:
                return self._conversations[target_id].messages.copy()
            return []

    def get_conversation_state(self, session_id: Optional[str] = None) -> Optional[ConversationState]:
        """Get a conversation state.

        Args:
            session_id: The session ID (uses active if None)

        Returns:
            The conversation state, or None if no conversation exists
        """
        with self._lock:
            target_id = session_id or self._active_conversation_id
            if target_id:
                return self._conversations.get(target_id)
            return None

    # UI State Management

    def set_selected_sidebar_tab(self, index: int) -> None:
        """Set the selected sidebar tab.

        Args:
            index: The tab index
        """
        with self._lock:
            self._selected_sidebar_tab = index
            self._notify_observers('ui_state_changed', {'sidebar_tab': index})

    def get_selected_sidebar_tab(self) -> int:
        """Get the selected sidebar tab index.

        Returns:
            The selected tab index
        """
        with self._lock:
            return self._selected_sidebar_tab

    # Settings Management

    def set_setting(self, key: str, value: Any) -> None:
        """Set an application setting.

        Args:
            key: The setting key
            value: The setting value
        """
        with self._lock:
            old_value = self._settings.get(key)
            self._settings[key] = value
            self._notify_observers('settings_changed', {
                'key': key,
                'old_value': old_value,
                'new_value': value
            })

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get an application setting.

        Args:
            key: The setting key
            default: The default value if key not found

        Returns:
            The setting value
        """
        with self._lock:
            return self._settings.get(key, default)

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all application settings.

        Returns:
            Dictionary of all settings
        """
        with self._lock:
            return self._settings.copy()

    # Observer Pattern Implementation

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to state change events.

        Args:
            event_type: The event type to subscribe to
            callback: The callback function to call when event occurs

        Raises:
            ValueError: If event_type is not valid
        """
        with self._lock:
            if event_type not in self._observers:
                raise ValueError(f"Invalid event type: {event_type}")

            if callback not in self._observers[event_type]:
                self._observers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from state change events.

        Args:
            event_type: The event type to unsubscribe from
            callback: The callback function to remove
        """
        with self._lock:
            if event_type in self._observers:
                if callback in self._observers[event_type]:
                    self._observers[event_type].remove(callback)

    def _notify_observers(self, event_type: str, data: Any) -> None:
        """Notify all observers of a state change.

        Args:
            event_type: The event type
            data: The event data
        """
        # Don't hold lock while notifying observers to prevent deadlock
        observers = []
        with self._lock:
            if event_type in self._observers:
                observers = self._observers[event_type].copy()

        for callback in observers:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in observer callback for {event_type}: {e}")

    # Utility Methods

    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current application state.

        Returns:
            Dictionary containing state summary
        """
        with self._lock:
            return {
                'files': {
                    'total': len(self._files),
                    'modified': len([f for f in self._files.values() if f.modified]),
                    'active': self._active_file_path
                },
                'conversation': {
                    'active': self._active_conversation_id is not None,
                    'total_conversations': len(self._conversations),
                    'message_count': len(self._conversations[self._active_conversation_id].messages) if self._active_conversation_id and self._active_conversation_id in self._conversations else 0
                },
                'ui': {
                    'selected_tab': self._selected_sidebar_tab
                }
            }

    # Persistence Methods

    def save_conversations(self, filepath: Optional[str] = None) -> bool:
        """Save conversation states to a JSON file.

        Args:
            filepath: Path to save to (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        target_file = filepath or self._persistence_file
        if not target_file:
            return False

        try:
            with self._lock:
                # Prepare conversation data
                conversations_data = {}
                for session_id, conv in self._conversations.items():
                    conversations_data[session_id] = {
                        'session_id': conv.session_id,
                        'title': conv.title,
                        'messages': conv.messages,
                        'started_at': conv.started_at.isoformat() if conv.started_at else None,
                        'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None
                    }

                state_data = {
                    'conversations': conversations_data,
                    'active_conversation_id': self._active_conversation_id,
                    'version': '1.0'
                }

            # Ensure directory exists
            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            # Write to file
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Error saving conversations to {target_file}: {e}")
            return False

    def load_conversations(self, filepath: Optional[str] = None) -> bool:
        """Load conversation states from a JSON file.

        Args:
            filepath: Path to load from (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        target_file = filepath or self._persistence_file
        if not target_file or not os.path.exists(target_file):
            return False

        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            with self._lock:
                # Clear existing conversations
                self._conversations.clear()

                # Load conversations
                conversations_data = state_data.get('conversations', {})
                for session_id, conv_data in conversations_data.items():
                    self._conversations[session_id] = ConversationState(
                        session_id=conv_data['session_id'],
                        title=conv_data.get('title', '新しい会話'),
                        messages=conv_data.get('messages', []),
                        started_at=datetime.fromisoformat(conv_data['started_at']) if conv_data.get('started_at') else None,
                        last_message_at=datetime.fromisoformat(conv_data['last_message_at']) if conv_data.get('last_message_at') else None
                    )

                # Load active conversation ID
                self._active_conversation_id = state_data.get('active_conversation_id')

                # Validate active conversation exists
                if self._active_conversation_id and self._active_conversation_id not in self._conversations:
                    self._active_conversation_id = None

            return True

        except Exception as e:
            print(f"Error loading conversations from {target_file}: {e}")
            return False


# Global state instance
app_state = AppState()
