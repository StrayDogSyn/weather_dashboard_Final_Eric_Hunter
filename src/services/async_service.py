"""Async service for non-blocking operations and UI responsiveness.

Provides async wrappers, thread pools, and progress tracking for long-running tasks.
"""

import asyncio
import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable, Optional, Dict, List, Union, Coroutine
from dataclasses import dataclass, field
from enum import Enum
import queue
import weakref
from functools import wraps


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskProgress:
    """Task progress information."""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    result: Any = None
    error: Optional[Exception] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time if self.status == TaskStatus.RUNNING else None
    
    @property
    def is_complete(self) -> bool:
        """Check if task is complete."""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)


class ProgressCallback:
    """Progress callback for updating task progress."""
    
    def __init__(self, task_id: str, async_service: 'AsyncService'):
        self.task_id = task_id
        self.async_service = async_service
    
    def update(self, progress: float, message: str = "") -> None:
        """Update task progress.
        
        Args:
            progress: Progress value (0.0 to 1.0)
            message: Progress message
        """
        self.async_service.update_task_progress(self.task_id, progress, message)
    
    def __call__(self, progress: float, message: str = "") -> None:
        """Allow callable usage."""
        self.update(progress, message)


class AsyncService:
    """Service for managing async operations and background tasks."""
    
    def __init__(self, max_workers: int = 4, max_queue_size: int = 100):
        """
        Initialize async service.
        
        Args:
            max_workers: Maximum number of worker threads
            max_queue_size: Maximum queue size for pending tasks
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # Thread pool for CPU-intensive tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # Task tracking
        self._tasks: Dict[str, TaskProgress] = {}
        self._futures: Dict[str, Future] = {}
        self._task_counter = 0
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Progress callbacks
        self._progress_callbacks: Dict[str, List[Callable]] = {}
        
        # Request debouncing
        self._debounce_timers: Dict[str, threading.Timer] = {}
        
        # Task queue for rate limiting
        self._task_queue = queue.Queue(maxsize=max_queue_size)
        self._queue_worker_running = False
        
        # Weak references to UI components for updates
        self._ui_callbacks = weakref.WeakSet()
    
    def submit_task(self, func: Callable, *args, 
                   task_id: Optional[str] = None,
                   progress_callback: Optional[Callable] = None,
                   **kwargs) -> str:
        """Submit a task for async execution.
        
        Args:
            func: Function to execute
            *args: Function arguments
            task_id: Optional task ID (auto-generated if None)
            progress_callback: Optional progress callback
            **kwargs: Function keyword arguments
            
        Returns:
            Task ID
        """
        with self._lock:
            if task_id is None:
                self._task_counter += 1
                task_id = f"task_{self._task_counter}_{int(time.time())}"
            
            # Create task progress
            task_progress = TaskProgress(task_id=task_id)
            self._tasks[task_id] = task_progress
            
            # Create progress callback
            progress_cb = ProgressCallback(task_id, self)
            
            # Wrap function to handle progress and errors
            def wrapped_func():
                try:
                    task_progress.status = TaskStatus.RUNNING
                    self._notify_progress_callbacks(task_id)
                    
                    # Execute function with progress callback
                    if 'progress_callback' in func.__code__.co_varnames:
                        result = func(*args, progress_callback=progress_cb, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    
                    # Mark as completed
                    task_progress.status = TaskStatus.COMPLETED
                    task_progress.result = result
                    task_progress.progress = 1.0
                    task_progress.end_time = time.time()
                    
                    self._notify_progress_callbacks(task_id)
                    return result
                    
                except Exception as e:
                    task_progress.status = TaskStatus.FAILED
                    task_progress.error = e
                    task_progress.end_time = time.time()
                    self._logger.error(f"Task {task_id} failed: {e}")
                    self._notify_progress_callbacks(task_id)
                    raise
            
            # Submit to thread pool
            future = self.thread_pool.submit(wrapped_func)
            self._futures[task_id] = future
            
            # Add progress callback if provided
            if progress_callback:
                self.add_progress_callback(task_id, progress_callback)
            
            self._logger.debug(f"Submitted task {task_id}")
            return task_id
    
    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get task progress.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task progress or None if not found
        """
        return self._tasks.get(task_id)
    
    def update_task_progress(self, task_id: str, progress: float, message: str = "") -> None:
        """Update task progress.
        
        Args:
            task_id: Task ID
            progress: Progress value (0.0 to 1.0)
            message: Progress message
        """
        with self._lock:
            if task_id in self._tasks:
                task_progress = self._tasks[task_id]
                task_progress.progress = max(0.0, min(1.0, progress))
                task_progress.message = message
                self._notify_progress_callbacks(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was cancelled
        """
        with self._lock:
            if task_id in self._futures:
                future = self._futures[task_id]
                if future.cancel():
                    if task_id in self._tasks:
                        self._tasks[task_id].status = TaskStatus.CANCELLED
                        self._tasks[task_id].end_time = time.time()
                    self._logger.debug(f"Cancelled task {task_id}")
                    return True
            return False
    
    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Wait for task completion.
        
        Args:
            task_id: Task ID
            timeout: Timeout in seconds
            
        Returns:
            Task result
            
        Raises:
            Exception: If task failed
        """
        if task_id in self._futures:
            future = self._futures[task_id]
            return future.result(timeout=timeout)
        
        raise ValueError(f"Task {task_id} not found")
    
    def add_progress_callback(self, task_id: str, callback: Callable) -> None:
        """Add progress callback for task.
        
        Args:
            task_id: Task ID
            callback: Callback function
        """
        with self._lock:
            if task_id not in self._progress_callbacks:
                self._progress_callbacks[task_id] = []
            self._progress_callbacks[task_id].append(callback)
    
    def remove_progress_callback(self, task_id: str, callback: Callable) -> None:
        """Remove progress callback for task.
        
        Args:
            task_id: Task ID
            callback: Callback function
        """
        with self._lock:
            if task_id in self._progress_callbacks:
                try:
                    self._progress_callbacks[task_id].remove(callback)
                except ValueError:
                    pass
    
    def debounce(self, key: str, func: Callable, delay: float = 0.5, *args, **kwargs) -> str:
        """Debounce function calls.
        
        Args:
            key: Debounce key
            func: Function to debounce
            delay: Delay in seconds
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Task ID
        """
        # Cancel existing timer
        if key in self._debounce_timers:
            self._debounce_timers[key].cancel()
        
        # Create new timer
        def delayed_execution():
            task_id = self.submit_task(func, *args, **kwargs)
            if key in self._debounce_timers:
                del self._debounce_timers[key]
            return task_id
        
        timer = threading.Timer(delay, delayed_execution)
        self._debounce_timers[key] = timer
        timer.start()
        
        return f"debounced_{key}_{int(time.time())}"
    
    def batch_submit(self, tasks: List[Dict[str, Any]], 
                    max_concurrent: int = 2) -> List[str]:
        """Submit multiple tasks with concurrency control.
        
        Args:
            tasks: List of task dictionaries with 'func', 'args', 'kwargs'
            max_concurrent: Maximum concurrent tasks
            
        Returns:
            List of task IDs
        """
        task_ids = []
        semaphore = threading.Semaphore(max_concurrent)
        
        def wrapped_task(task_info):
            with semaphore:
                func = task_info['func']
                args = task_info.get('args', ())
                kwargs = task_info.get('kwargs', {})
                return func(*args, **kwargs)
        
        for task_info in tasks:
            task_id = self.submit_task(wrapped_task, task_info)
            task_ids.append(task_id)
        
        return task_ids
    
    def get_active_tasks(self) -> List[TaskProgress]:
        """Get list of active tasks.
        
        Returns:
            List of active task progress objects
        """
        with self._lock:
            return [
                task for task in self._tasks.values()
                if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
            ]
    
    def cleanup_completed_tasks(self, max_age: float = 3600) -> int:
        """Clean up old completed tasks.
        
        Args:
            max_age: Maximum age in seconds
            
        Returns:
            Number of tasks cleaned up
        """
        current_time = time.time()
        cleaned_count = 0
        
        with self._lock:
            tasks_to_remove = []
            
            for task_id, task in self._tasks.items():
                if (task.is_complete and 
                    task.end_time and 
                    current_time - task.end_time > max_age):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
                if task_id in self._futures:
                    del self._futures[task_id]
                if task_id in self._progress_callbacks:
                    del self._progress_callbacks[task_id]
                cleaned_count += 1
        
        if cleaned_count > 0:
            self._logger.debug(f"Cleaned up {cleaned_count} completed tasks")
        
        return cleaned_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics.
        
        Returns:
            Dictionary with service statistics
        """
        with self._lock:
            stats = {
                'total_tasks': len(self._tasks),
                'active_tasks': len(self.get_active_tasks()),
                'thread_pool_size': self.max_workers,
                'queue_size': self._task_queue.qsize() if hasattr(self._task_queue, 'qsize') else 0
            }
            
            # Count by status
            status_counts = {}
            for task in self._tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            stats['status_counts'] = status_counts
            return stats
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the async service.
        
        Args:
            wait: Whether to wait for running tasks to complete
        """
        self._logger.info("Shutting down async service")
        
        # Cancel debounce timers
        for timer in self._debounce_timers.values():
            timer.cancel()
        self._debounce_timers.clear()
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=wait)
        
        # Clear tasks
        with self._lock:
            self._tasks.clear()
            self._futures.clear()
            self._progress_callbacks.clear()
    
    def _notify_progress_callbacks(self, task_id: str) -> None:
        """Notify progress callbacks for task.
        
        Args:
            task_id: Task ID
        """
        if task_id in self._progress_callbacks:
            task_progress = self._tasks.get(task_id)
            if task_progress:
                for callback in self._progress_callbacks[task_id]:
                    try:
                        callback(task_progress)
                    except Exception as e:
                        self._logger.error(f"Error in progress callback: {e}")


# Decorators for async operations
def async_task(async_service: Optional[AsyncService] = None):
    """Decorator to make function async.
    
    Args:
        async_service: Async service instance
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            service = async_service or get_async_service()
            return service.submit_task(func, *args, **kwargs)
        
        wrapper._original_func = func
        wrapper._async_service = async_service
        return wrapper
    
    return decorator


def debounced(key: str, delay: float = 0.5, async_service: Optional[AsyncService] = None):
    """Decorator to debounce function calls.
    
    Args:
        key: Debounce key
        delay: Delay in seconds
        async_service: Async service instance
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            service = async_service or get_async_service()
            return service.debounce(key, func, delay, *args, **kwargs)
        
        wrapper._original_func = func
        wrapper._debounce_key = key
        wrapper._debounce_delay = delay
        return wrapper
    
    return decorator


# Global async service instance
_global_async_service = None


def get_async_service() -> AsyncService:
    """Get global async service instance."""
    global _global_async_service
    if _global_async_service is None:
        _global_async_service = AsyncService()
    return _global_async_service


def shutdown_async_service() -> None:
    """Shutdown global async service."""
    global _global_async_service
    if _global_async_service:
        _global_async_service.shutdown()
        _global_async_service = None