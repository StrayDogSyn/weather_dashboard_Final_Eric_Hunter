"""Enhanced Loading Manager - High-Performance Progressive Loading

Handles critical and deferred loading tasks with priority queue, request deduplication,
progress indicators, and cancellation support for optimal performance.
"""

import asyncio
import hashlib
import logging
import queue
import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor, TimeoutError, Future
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class LoadingTask:
    """Enhanced loading task with priority and metadata."""
    name: str
    func: Callable
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: float = 5.0
    retry_count: int = 0
    max_retries: int = 2
    dependencies: List[str] = field(default_factory=list)
    progress_callback: Optional[Callable[[float], None]] = None
    cancellation_token: Optional[threading.Event] = None
    request_hash: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if self.cancellation_token is None:
            self.cancellation_token = threading.Event()
        if self.request_hash is None:
            self.request_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate hash for request deduplication."""
        content = f"{self.name}_{self.func.__name__ if hasattr(self.func, '__name__') else str(self.func)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_cancelled(self) -> bool:
        """Check if task is cancelled."""
        return self.cancellation_token.is_set()
    
    def cancel(self) -> None:
        """Cancel the task."""
        self.cancellation_token.set()


class LoadingManager:
    """Enhanced loading manager with performance optimizations."""

    def __init__(self, max_workers: int = 4):
        """Initialize enhanced loading manager.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.logger = logging.getLogger("weather_dashboard.loading_manager")
        
        # Priority queue for tasks
        self._task_queue = queue.PriorityQueue()
        self._active_tasks: Dict[str, LoadingTask] = {}
        self._completed_tasks: Set[str] = set()
        self._failed_tasks: Set[str] = set()
        
        # Request deduplication
        self._pending_requests: Dict[str, Future] = {}
        self._request_results: Dict[str, Any] = {}
        
        # Thread management
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, 
            thread_name_prefix="EnhancedLoadingManager"
        )
        self._worker_thread = None
        self._running = True
        
        # Progress tracking
        self._progress_callbacks: Dict[str, List[Callable[[str, float], None]]] = {
            "task_progress": [],
            "overall_progress": [],
        }
        
        # State tracking
        self.critical_loaded = False
        self._total_tasks = 0
        self._completed_count = 0
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            "critical_complete": [],
            "deferred_complete": [],
            "task_complete": [],
            "task_progress": [],
            "error": [],
            "cancelled": [],
        }
        
        # Start worker thread
        self._start_worker()
        
        # Weak references for cleanup
        self._cleanup_refs: List[weakref.ref] = []

    def add_callback(self, event: str, callback: Callable) -> None:
        """Add callback for loading events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
        elif event in self._progress_callbacks:
            self._progress_callbacks[event].append(callback)

    def _notify_callbacks(self, event: str, *args, **kwargs) -> None:
        """Notify registered callbacks."""
        callbacks = self._callbacks.get(event, []) + self._progress_callbacks.get(event, [])
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Callback error for {event}: {e}")
    
    def _start_worker(self) -> None:
        """Start the worker thread for processing tasks."""
        self._worker_thread = threading.Thread(
            target=self._process_task_queue,
            daemon=True,
            name="LoadingManagerWorker"
        )
        self._worker_thread.start()
    
    def _process_task_queue(self) -> None:
        """Process tasks from the priority queue."""
        while self._running:
            try:
                # Get next task with timeout
                priority, task_id, task = self._task_queue.get(timeout=1.0)
                
                if not self._running or task.is_cancelled():
                    self._task_queue.task_done()
                    continue
                
                # Check dependencies
                if not self._check_dependencies(task):
                    # Re-queue with slight delay
                    self._task_queue.put((priority, task_id, task))
                    self._task_queue.task_done()
                    time.sleep(0.1)
                    continue
                
                # Execute task
                self._execute_task(task)
                self._task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker thread error: {e}")
    
    def _check_dependencies(self, task: LoadingTask) -> bool:
        """Check if task dependencies are satisfied."""
        for dep in task.dependencies:
            if dep not in self._completed_tasks:
                return False
        return True
    
    def _execute_task(self, task: LoadingTask) -> None:
        """Execute a single task with deduplication and progress tracking."""
        try:
            # Check for duplicate request
            if task.request_hash in self._pending_requests:
                self.logger.debug(f"Deduplicating request: {task.name}")
                future = self._pending_requests[task.request_hash]
                result = future.result(timeout=task.timeout)
                self._handle_task_completion(task, result)
                return
            
            # Check cached result
            if task.request_hash in self._request_results:
                self.logger.debug(f"Using cached result: {task.name}")
                result = self._request_results[task.request_hash]
                self._handle_task_completion(task, result)
                return
            
            # Execute new task
            self._active_tasks[task.name] = task
            
            # Wrap function with progress tracking
            wrapped_func = self._wrap_with_progress(task)
            
            # Submit to executor
            future = self._executor.submit(wrapped_func)
            self._pending_requests[task.request_hash] = future
            
            try:
                result = future.result(timeout=task.timeout)
                
                # Cache result for deduplication
                self._request_results[task.request_hash] = result
                
                self._handle_task_completion(task, result)
                
            except TimeoutError:
                self.logger.warning(f"Task '{task.name}' timed out after {task.timeout}s")
                future.cancel()
                self._handle_task_failure(task, "Timeout")
                
            except Exception as e:
                self.logger.error(f"Task '{task.name}' failed: {e}")
                self._handle_task_failure(task, str(e))
            
            finally:
                # Cleanup
                self._active_tasks.pop(task.name, None)
                self._pending_requests.pop(task.request_hash, None)
                
        except Exception as e:
            self.logger.error(f"Error executing task '{task.name}': {e}")
            self._handle_task_failure(task, str(e))
    
    def _wrap_with_progress(self, task: LoadingTask) -> Callable:
        """Wrap task function with progress tracking."""
        def wrapped_func():
            if task.is_cancelled():
                raise RuntimeError("Task was cancelled")
            
            # Report start
            self._report_progress(task.name, 0.0)
            
            # Execute original function
            if task.progress_callback:
                # If function supports progress callback
                try:
                    result = task.func(progress_callback=task.progress_callback)
                except TypeError:
                    # Function doesn't support progress callback
                    result = task.func()
                    self._report_progress(task.name, 1.0)
            else:
                result = task.func()
                self._report_progress(task.name, 1.0)
            
            return result
        
        return wrapped_func
    
    def _report_progress(self, task_name: str, progress: float) -> None:
        """Report task progress."""
        self._notify_callbacks("task_progress", task_name, progress)
        
        # Update overall progress
        if self._total_tasks > 0:
            overall_progress = (self._completed_count + progress) / self._total_tasks
            self._notify_callbacks("overall_progress", overall_progress)
    
    def _handle_task_completion(self, task: LoadingTask, result: Any) -> None:
        """Handle successful task completion."""
        self._completed_tasks.add(task.name)
        self._completed_count += 1
        
        self.logger.info(f"✅ Task '{task.name}' completed successfully")
        self._notify_callbacks("task_complete", task.name, result)
        
        # Report final progress
        self._report_progress(task.name, 1.0)
    
    def _handle_task_failure(self, task: LoadingTask, error: str) -> None:
        """Handle task failure with retry logic."""
        if task.retry_count < task.max_retries and not task.is_cancelled():
            task.retry_count += 1
            self.logger.info(f"🔄 Retrying task '{task.name}' (attempt {task.retry_count}/{task.max_retries})")
            
            # Re-queue with exponential backoff
            delay = 2 ** task.retry_count
            threading.Timer(delay, lambda: self.add_task(task)).start()
        else:
            self._failed_tasks.add(task.name)
            self.logger.error(f"❌ Task '{task.name}' failed permanently: {error}")
            self._notify_callbacks("error", task.name, error)
    
    def add_task(self, task: LoadingTask) -> str:
        """Add a task to the priority queue.
        
        Args:
            task: LoadingTask to add
            
        Returns:
            Task ID for tracking
        """
        if task.is_cancelled():
            return task.name
        
        # Generate unique task ID
        task_id = f"{task.name}_{int(time.time() * 1000)}"
        
        # Add to queue with priority
        priority_value = task.priority.value
        self._task_queue.put((priority_value, task_id, task))
        
        self._total_tasks += 1
        self.logger.debug(f"Added task '{task.name}' with priority {task.priority.name}")
        
        return task_id
    
    def add_tasks(self, tasks: List[LoadingTask]) -> List[str]:
        """Add multiple tasks to the queue.
        
        Args:
            tasks: List of LoadingTask objects
            
        Returns:
            List of task IDs
        """
        task_ids = []
        for task in tasks:
            task_id = self.add_task(task)
            task_ids.append(task_id)
        return task_ids
    
    def cancel_task(self, task_name: str) -> bool:
        """Cancel a specific task.
        
        Args:
            task_name: Name of task to cancel
            
        Returns:
            True if task was cancelled
        """
        # Cancel active task
        if task_name in self._active_tasks:
            task = self._active_tasks[task_name]
            task.cancel()
            self.logger.info(f"Cancelled active task: {task_name}")
            self._notify_callbacks("cancelled", task_name)
            return True
        
        # Cancel pending request
        for request_hash, future in self._pending_requests.items():
            if task_name in request_hash:  # Simple matching
                future.cancel()
                self.logger.info(f"Cancelled pending task: {task_name}")
                self._notify_callbacks("cancelled", task_name)
                return True
        
        return False
    
    def cancel_all_tasks(self) -> int:
        """Cancel all pending and active tasks.
        
        Returns:
            Number of tasks cancelled
        """
        cancelled_count = 0
        
        # Cancel active tasks
        for task in self._active_tasks.values():
            task.cancel()
            cancelled_count += 1
        
        # Cancel pending requests
        for future in self._pending_requests.values():
            if future.cancel():
                cancelled_count += 1
        
        # Clear queue
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
                self._task_queue.task_done()
                cancelled_count += 1
            except queue.Empty:
                break
        
        self.logger.info(f"Cancelled {cancelled_count} tasks")
        self._notify_callbacks("cancelled", "all", cancelled_count)
        
        return cancelled_count
    
    def get_progress(self) -> Dict[str, float]:
        """Get progress for all active tasks.
        
        Returns:
            Dictionary mapping task names to progress (0.0-1.0)
        """
        progress = {}
        
        for task_name in self._active_tasks:
            # This would be updated by progress callbacks
            progress[task_name] = 0.5  # Placeholder
        
        for task_name in self._completed_tasks:
            progress[task_name] = 1.0
        
        return progress
    
    def get_overall_progress(self) -> float:
        """Get overall loading progress.
        
        Returns:
            Overall progress (0.0-1.0)
        """
        if self._total_tasks == 0:
            return 1.0
        
        return self._completed_count / self._total_tasks
    
    def clear_cache(self) -> None:
        """Clear request deduplication cache."""
        self._request_results.clear()
        self.logger.info("Cleared request deduplication cache")
    
    def load_critical(self, ui_setup_func: Callable, timeout: float = 2.0) -> bool:
        """Load only essential UI elements first.

        Args:
            ui_setup_func: Function to set up critical UI components
            timeout: Maximum time to wait for critical loading

        Returns:
            True if critical loading succeeded, False otherwise
        """
        try:
            self.logger.info("🚀 Starting critical loading phase...")
            start_time = time.time()

            # Submit critical task with timeout
            future = self._executor.submit(ui_setup_func)

            try:
                future.result(timeout=timeout)
                self.critical_loaded = True
                elapsed = time.time() - start_time
                self.logger.info(
                    f"✅ Critical loading completed in {
                        elapsed:.2f}s"
                )
                self._notify_callbacks("critical_complete")
                return True

            except TimeoutError:
                self.logger.error(f"⏰ Critical loading timed out after {timeout}s")
                future.cancel()
                self._notify_callbacks("error", "Critical loading timeout")
                return False

        except Exception as e:
            self.logger.error(f"❌ Critical loading failed: {e}")
            self._notify_callbacks("error", str(e))
            return False

    def load_deferred(self, tasks: List[Dict[str, Any]], max_timeout: float = 10.0) -> None:
        """Load weather data, charts, etc. after UI is ready.

        Args:
            tasks: List of task dictionaries with 'name', 'func', and optional 'timeout'
            max_timeout: Maximum time for any single deferred task
        """
        if not self.critical_loaded:
            self.logger.warning("⚠️ Attempting deferred loading before critical loading complete")

        self.logger.info(
            f"🔄 Starting deferred loading of {
                len(tasks)} tasks..."
        )

        def _run_deferred_tasks():
            completed_tasks = []
            failed_tasks = []

            for task in tasks:
                if not self._running:
                    break

                task_name = task.get("name", "Unknown")
                task_func = task.get("func")
                task_timeout = min(task.get("timeout", 5.0), max_timeout)

                if not task_func:
                    self.logger.error(f"❌ Task {task_name} has no function")
                    failed_tasks.append(task_name)
                    continue

                try:
                    self.logger.debug(f"🔄 Loading deferred task: {task_name}")
                    start_time = time.time()

                    # Submit task with timeout
                    future = self._executor.submit(task_func)
                    result = future.result(timeout=task_timeout)

                    elapsed = time.time() - start_time
                    self.logger.info(
                        f"✅ Task '{task_name}' completed in {
                            elapsed:.2f}s"
                    )
                    completed_tasks.append(task_name)
                    self._notify_callbacks("task_complete", task_name, result)

                except TimeoutError:
                    self.logger.warning(f"⏰ Task '{task_name}' timed out after {task_timeout}s")
                    failed_tasks.append(task_name)
                    future.cancel()

                except Exception as e:
                    self.logger.error(f"❌ Task '{task_name}' failed: {e}")
                    failed_tasks.append(task_name)
                    self._notify_callbacks("error", f"Task {task_name}: {str(e)}")

            self.logger.info(
                f"🏁 Deferred loading complete. Success: {
                    len(completed_tasks)}, Failed: {
                    len(failed_tasks)}"
            )
            if failed_tasks:
                self.logger.warning(
                    f"⚠️ Failed tasks: {
                        ', '.join(failed_tasks)}"
                )

            self._notify_callbacks("deferred_complete", completed_tasks, failed_tasks)

        # Run deferred tasks in background thread
        threading.Thread(target=_run_deferred_tasks, daemon=True, name="DeferredLoader").start()

    def load_with_timeout(
        self, func: Callable, timeout: float = 5.0, fallback_result: Any = None
    ) -> Any:
        """Load a single function with timeout and fallback.

        Args:
            func: Function to execute
            timeout: Maximum time to wait
            fallback_result: Result to return if timeout or error occurs

        Returns:
            Function result or fallback_result
        """
        try:
            future = self._executor.submit(func)
            return future.result(timeout=timeout)

        except TimeoutError:
            self.logger.warning(f"⏰ Function timed out after {timeout}s, using fallback")
            return fallback_result

        except Exception as e:
            self.logger.error(f"❌ Function failed: {e}, using fallback")
            return fallback_result

    def create_offline_fallback(self, data_type: str) -> Dict[str, Any]:
        """Create offline fallback data.

        Args:
            data_type: Type of data to create fallback for

        Returns:
            Fallback data dictionary
        """
        fallbacks = {
            "weather": {
                "location": "Offline Mode",
                "temperature": "--",
                "condition": "No connection",
                "description": "Weather data unavailable",
                "humidity": "--",
                "pressure": "--",
                "wind_speed": "--",
                "timestamp": time.time(),
            },
            "forecast": {"days": [], "message": "Forecast unavailable in offline mode"},
            "air_quality": {"aqi": "--", "description": "Air quality data unavailable"},
        }

        return fallbacks.get(data_type, {"error": "Unknown data type"})

    def shutdown(self) -> None:
        """Shutdown loading manager and cleanup resources."""
        self.logger.info("🛑 Shutting down enhanced loading manager...")
        self._running = False
        
        # Cancel all tasks
        cancelled_count = self.cancel_all_tasks()
        
        # Wait for worker thread
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
        
        # Shutdown executor
        try:
            self._executor.shutdown(wait=True, timeout=2.0)
            self.logger.info(f"✅ Enhanced loading manager shutdown complete (cancelled {cancelled_count} tasks)")
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")
        
        # Clear caches
        self._request_results.clear()
        self._pending_requests.clear()
        
        # Cleanup weak references
        self._cleanup_refs.clear()

    def get_status(self) -> Dict[str, Any]:
        """Get current enhanced loading status.

        Returns:
            Status dictionary with comprehensive loading information
        """
        return {
            "critical_loaded": self.critical_loaded,
            "running": self._running,
            "active_tasks": len(self._active_tasks),
            "completed_tasks": len(self._completed_tasks),
            "failed_tasks": len(self._failed_tasks),
            "queued_tasks": self._task_queue.qsize(),
            "total_tasks": self._total_tasks,
            "overall_progress": self.get_overall_progress(),
            "executor_active": not self._executor._shutdown,
            "worker_thread_alive": self._worker_thread.is_alive() if self._worker_thread else False,
            "pending_requests": len(self._pending_requests),
            "cached_results": len(self._request_results),
        }
