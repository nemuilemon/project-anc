"""Base plugin interface for AI analysis functions.

This module defines the abstract base class and data structures that all
AI analysis plugins must implement, ensuring consistent behavior and
interface across different analysis types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Callable
from threading import Event
import time


@dataclass
class AnalysisResult:
    """Data structure for AI analysis results.
    
    Attributes:
        success (bool): Whether the analysis completed successfully
        data (Dict[str, Any]): Analysis results (tags, summary, sentiment, etc.)
        message (str): Human-readable status/error message
        processing_time (float): Time taken for analysis in seconds
        plugin_name (str): Name of the plugin that performed the analysis
        metadata (Dict[str, Any]): Additional metadata about the analysis
    """
    success: bool
    data: Dict[str, Any]
    message: str
    processing_time: float = 0.0
    plugin_name: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAnalysisPlugin(ABC):
    """Abstract base class for all AI analysis plugins.
    
    This class defines the interface that all AI analysis plugins must implement.
    It provides common functionality like progress tracking, cancellation support,
    and error handling while allowing each plugin to implement its specific
    analysis logic.
    
    Attributes:
        name (str): Unique identifier for this plugin
        description (str): Human-readable description of what this plugin does
        version (str): Plugin version for compatibility tracking
        requires_ollama (bool): Whether this plugin requires Ollama connection
        max_retries (int): Maximum number of retry attempts for failed operations
        timeout_seconds (int): Maximum time to wait for analysis completion
    """
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.requires_ollama = True
        self.max_retries = 3
        self.timeout_seconds = 60
        
    @abstractmethod
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        """Perform synchronous analysis on the given content.
        
        Args:
            content (str): Text content to analyze
            **kwargs: Additional plugin-specific parameters
            
        Returns:
            AnalysisResult: Results of the analysis operation
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    @abstractmethod
    def analyze_async(self, 
                     content: str, 
                     progress_callback: Optional[Callable[[int], None]] = None,
                     cancel_event: Optional[Event] = None,
                     **kwargs) -> AnalysisResult:
        """Perform asynchronous analysis on the given content.
        
        Args:
            content (str): Text content to analyze
            progress_callback (Callable, optional): Function to call with progress updates (0-100)
            cancel_event (Event, optional): Threading event for cancellation support
            **kwargs: Additional plugin-specific parameters
            
        Returns:
            AnalysisResult: Results of the analysis operation
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    def validate_content(self, content: str) -> bool:
        """Validate that the content is suitable for this analysis type.
        
        Args:
            content (str): Content to validate
            
        Returns:
            bool: True if content is valid for analysis
        """
        return bool(content and content.strip())
    
    def get_config(self) -> Dict[str, Any]:
        """Get plugin configuration parameters.
        
        Returns:
            Dict[str, Any]: Configuration dictionary with plugin settings
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "requires_ollama": self.requires_ollama,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds
        }
    
    def _create_error_result(self, message: str, error: Optional[Exception] = None) -> AnalysisResult:
        """Create a standardized error result.
        
        Args:
            message (str): Error message for the user
            error (Exception, optional): Original exception for debugging
            
        Returns:
            AnalysisResult: Error result object
        """
        metadata = {"error_type": type(error).__name__ if error else "AnalysisError"}
        if error:
            metadata["error_details"] = str(error)
            
        return AnalysisResult(
            success=False,
            data={},
            message=message,
            plugin_name=self.name,
            metadata=metadata
        )
    
    def _create_success_result(self, data: Dict[str, Any], message: str, processing_time: float = 0.0) -> AnalysisResult:
        """Create a standardized success result.
        
        Args:
            data (Dict[str, Any]): Analysis results
            message (str): Success message for the user
            processing_time (float): Time taken for analysis
            
        Returns:
            AnalysisResult: Success result object
        """
        return AnalysisResult(
            success=True,
            data=data,
            message=message,
            processing_time=processing_time,
            plugin_name=self.name,
            metadata={"content_length": len(str(data))}
        )
    
    def _check_cancellation(self, cancel_event: Optional[Event]) -> bool:
        """Check if operation should be cancelled.
        
        Args:
            cancel_event (Event, optional): Cancellation event
            
        Returns:
            bool: True if operation should be cancelled
        """
        return cancel_event is not None and cancel_event.is_set()
    
    def _update_progress(self, progress_callback: Optional[Callable[[int], None]], progress: int):
        """Update progress if callback is provided.
        
        Args:
            progress_callback (Callable, optional): Progress update function
            progress (int): Progress percentage (0-100)
        """
        if progress_callback:
            progress_callback(max(0, min(100, progress)))