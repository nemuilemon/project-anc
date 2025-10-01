"""State Management for Project A.N.C.

This module provides centralized state management for the application,
ensuring consistent state across all components and preventing state
inconsistencies.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading


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

    def __init__(self):
        """Initialize the application state."""
        # Thread safety
        self._lock = threading.RLock()

        # File states
        self._files: Dict[str, FileState] = {}
        self._active_file_path: Optional[str] = None

        # Conversation state
        self._conversation: Optional[ConversationState] = None

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

    def init_conversation(self, session_id: str) -> None:
        """Initialize a new conversation session.

        Args:
            session_id: Unique session identifier
        """
        with self._lock:
            self._conversation = ConversationState(
                session_id=session_id,
                started_at=datetime.now()
            )

    def add_conversation_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a message to the conversation.

        Args:
            role: The message role ('user' or 'model')
            content: The message content
            metadata: Optional metadata for the message
        """
        with self._lock:
            if not self._conversation:
                self.init_conversation(f"session_{datetime.now().isoformat()}")

            message = {
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }

            self._conversation.messages.append(message)
            self._conversation.last_message_at = datetime.now()
            self._notify_observers('conversation_updated', message)

    def clear_conversation(self) -> None:
        """Clear the current conversation."""
        with self._lock:
            self._conversation = None
            self._notify_observers('conversation_cleared', None)

    def get_conversation_messages(self) -> List[Dict[str, Any]]:
        """Get all conversation messages.

        Returns:
            List of conversation messages
        """
        with self._lock:
            if self._conversation:
                return self._conversation.messages.copy()
            return []

    def get_conversation_state(self) -> Optional[ConversationState]:
        """Get the current conversation state.

        Returns:
            The conversation state, or None if no conversation exists
        """
        with self._lock:
            return self._conversation

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
                    'active': self._conversation is not None,
                    'message_count': len(self._conversation.messages) if self._conversation else 0
                },
                'ui': {
                    'selected_tab': self._selected_sidebar_tab
                }
            }


# Global state instance
app_state = AppState()
