"""Asynchronous operations module for Project A.N.C.

This module provides asynchronous file operations and long-running tasks
to prevent UI freezing during heavy operations like reading large files,
AI analysis, and batch operations.

Integrated with AppState for centralized state management.
"""

import asyncio
import threading
import time
import os
from typing import Callable, Optional, Any, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OperationStatus(Enum):
    """Status of an asynchronous operation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OperationInfo:
    """Information about an asynchronous operation."""
    operation_id: str
    operation_type: str
    status: OperationStatus = OperationStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: int = 0
    error: Optional[str] = None
    result: Optional[Any] = None
    cancellation_event: Optional[threading.Event] = field(default_factory=threading.Event)

    def duration(self) -> float:
        """Get operation duration in seconds."""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


class AsyncOperationManager:
    """Manages asynchronous operations with progress tracking and cancellation support.
    
    This class provides a centralized way to handle long-running operations
    asynchronously while maintaining UI responsiveness and providing progress
    feedback to users.
    """
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_operations: Dict[str, OperationInfo] = {}
        self.operation_counter = 0
        self._lock = threading.RLock()
    
    def create_operation_id(self) -> str:
        """Create a unique operation ID for tracking."""
        self.operation_counter += 1
        return f"op_{self.operation_counter}"
    
    async def run_async_file_read(
        self, 
        file_path: str, 
        progress_callback: Optional[Callable[[int], None]] = None,
        chunk_size: int = 8192
    ) -> Tuple[bool, str, Optional[str]]:
        """Asynchronously read a file with progress tracking.
        
        Args:
            file_path (str): Path to the file to read
            progress_callback (Callable, optional): Progress update callback
            chunk_size (int): Size of chunks to read for progress tracking
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, content)
        """
        try:
            # Get file size for progress calculation
            file_size = os.path.getsize(file_path)
            
            def _read_file_sync():
                content = ""
                bytes_read = 0
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        
                        content += chunk
                        bytes_read += len(chunk.encode('utf-8'))
                        
                        # Update progress
                        if progress_callback and file_size > 0:
                            progress = min(100, int((bytes_read / file_size) * 100))
                            progress_callback(progress)
                        
                        # Small delay for UI responsiveness on very large files
                        if file_size > 1024 * 1024:  # 1MB+
                            time.sleep(0.01)
                
                return content
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(self.executor, _read_file_sync)
            
            return True, "File read successfully", content
            
        except Exception as e:
            return False, f"Error reading file: {str(e)}", None
    
    async def run_async_file_write(
        self, 
        file_path: str, 
        content: str,
        progress_callback: Optional[Callable[[int], None]] = None,
        chunk_size: int = 8192
    ) -> Tuple[bool, str]:
        """Asynchronously write a file with progress tracking.
        
        Args:
            file_path (str): Path to write the file
            content (str): Content to write
            progress_callback (Callable, optional): Progress update callback
            chunk_size (int): Size of chunks to write for progress tracking
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            content_bytes = content.encode('utf-8')
            total_size = len(content_bytes)
            
            def _write_file_sync():
                bytes_written = 0
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Write in chunks for progress tracking
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i + chunk_size]
                        f.write(chunk)
                        
                        bytes_written += len(chunk.encode('utf-8'))
                        
                        # Update progress
                        if progress_callback and total_size > 0:
                            progress = min(100, int((bytes_written / total_size) * 100))
                            progress_callback(progress)
                        
                        # Small delay for UI responsiveness on very large files
                        if total_size > 1024 * 1024:  # 1MB+
                            time.sleep(0.01)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, _write_file_sync)
            
            return True, "File written successfully"
            
        except Exception as e:
            return False, f"Error writing file: {str(e)}"
    
    def run_async_operation(
        self,
        operation_func: Callable,
        operation_type: str = "generic",
        *args,
        progress_callback: Optional[Callable[[int], None]] = None,
        completion_callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None,
        **kwargs
    ) -> str:
        """Run an operation asynchronously with callbacks and cancellation support.

        Args:
            operation_func: Function to run asynchronously
            operation_type: Type/name of the operation for tracking
            *args: Arguments for the operation function
            progress_callback: Progress update callback
            completion_callback: Success completion callback
            error_callback: Error handling callback
            **kwargs: Keyword arguments for the operation function

        Returns:
            str: Operation ID for tracking
        """
        operation_id = self.create_operation_id()

        # Create operation info
        op_info = OperationInfo(
            operation_id=operation_id,
            operation_type=operation_type
        )

        with self._lock:
            self.active_operations[operation_id] = op_info

        def _run_operation():
            op_info.status = OperationStatus.RUNNING
            op_info.start_time = datetime.now()

            try:
                # Wrap progress callback to update operation info
                def _wrapped_progress_callback(progress: int):
                    op_info.progress = progress
                    if progress_callback:
                        progress_callback(progress)

                    # Check for cancellation
                    if op_info.cancellation_event.is_set():
                        raise InterruptedError("Operation cancelled by user")

                # Add cancellation event and progress callback to kwargs
                kwargs['cancellation_event'] = op_info.cancellation_event

                if 'progress_callback' in operation_func.__code__.co_varnames:
                    kwargs['progress_callback'] = _wrapped_progress_callback

                result = operation_func(*args, **kwargs)

                # Check one more time for cancellation
                if op_info.cancellation_event.is_set():
                    op_info.status = OperationStatus.CANCELLED
                else:
                    op_info.status = OperationStatus.COMPLETED
                    op_info.result = result
                    op_info.progress = 100

                    if completion_callback:
                        completion_callback(result)

            except InterruptedError as e:
                op_info.status = OperationStatus.CANCELLED
                op_info.error = str(e)
                if error_callback:
                    error_callback(e)

            except Exception as e:
                op_info.status = OperationStatus.FAILED
                op_info.error = str(e)
                if error_callback:
                    error_callback(e)

            finally:
                op_info.end_time = datetime.now()

                # Keep operation info for a while for status queries
                def _cleanup():
                    time.sleep(60)  # Keep for 1 minute
                    with self._lock:
                        if operation_id in self.active_operations:
                            del self.active_operations[operation_id]

                cleanup_thread = threading.Thread(target=_cleanup, daemon=True)
                cleanup_thread.start()

        # Start operation in background thread
        thread = threading.Thread(target=_run_operation, daemon=True)
        thread.start()

        return operation_id
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an active operation.

        Args:
            operation_id (str): ID of operation to cancel

        Returns:
            bool: True if operation was found and marked for cancellation
        """
        with self._lock:
            if operation_id in self.active_operations:
                op_info = self.active_operations[operation_id]
                if op_info.status in [OperationStatus.PENDING, OperationStatus.RUNNING]:
                    op_info.cancellation_event.set()
                    return True
        return False
    
    def get_operation_info(self, operation_id: str) -> Optional[OperationInfo]:
        """Get information about a specific operation.

        Args:
            operation_id: ID of the operation

        Returns:
            OperationInfo or None if not found
        """
        with self._lock:
            return self.active_operations.get(operation_id)

    def get_active_operations(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active operations.

        Returns:
            dict: Dictionary of active operations with their info
        """
        with self._lock:
            return {
                op_id: {
                    'type': info.operation_type,
                    'status': info.status.value,
                    'progress': info.progress,
                    'duration': info.duration(),
                    'error': info.error
                }
                for op_id, info in self.active_operations.items()
            }
    
    def shutdown(self):
        """Shutdown the async operation manager and clean up resources."""
        self.executor.shutdown(wait=True)


# Global instance
async_manager = AsyncOperationManager()


class ProgressTracker:
    """Helper class for tracking progress of long-running operations."""
    
    def __init__(self, total_steps: int = 100):
        self.total_steps = total_steps
        self.current_step = 0
        self.callbacks = []
    
    def add_callback(self, callback: Callable[[int], None]):
        """Add a progress callback function."""
        self.callbacks.append(callback)
    
    def update_progress(self, step: int):
        """Update progress and notify callbacks."""
        self.current_step = min(step, self.total_steps)
        progress_percent = int((self.current_step / self.total_steps) * 100)
        
        for callback in self.callbacks:
            try:
                callback(progress_percent)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    def increment(self, steps: int = 1):
        """Increment progress by specified steps."""
        self.update_progress(self.current_step + steps)
    
    def complete(self):
        """Mark progress as complete."""
        self.update_progress(self.total_steps)


def run_with_progress(
    operation_func: Callable,
    progress_callback: Optional[Callable[[int], None]] = None,
    *args,
    **kwargs
) -> str:
    """Convenience function to run an operation with progress tracking.
    
    Args:
        operation_func: Function to run
        progress_callback: Progress update callback
        *args: Arguments for operation function
        **kwargs: Keyword arguments for operation function
        
    Returns:
        str: Operation ID
    """
    return async_manager.run_async_operation(
        operation_func,
        *args,
        progress_callback=progress_callback,
        **kwargs
    )