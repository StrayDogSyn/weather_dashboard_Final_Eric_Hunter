"""Loading Manager for handling async operations with timeout and progress tracking."""

import logging
import threading
import time
from concurrent.futures import TimeoutError
from typing import Any, Callable, Dict, Set


class LoadingManager:
    """Manages loading operations with timeout, progress tracking, and error handling.
    
    Provides methods for executing tasks with different priorities, timeout handling,
    and proper cleanup of resources.
    """

    def __init__(self, max_workers: int = 4, ui_widget=None):
        """Initialize the LoadingManager.

        Args:
            max_workers: Maximum number of concurrent loading operations
            ui_widget: Reference to the main UI widget for thread-safe callbacks
        """
        self.logger = logging.getLogger(__name__)
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._threads: Set[threading.Thread] = set()
        self._shutdown = False
        self._ui_widget = ui_widget

        self.logger.info(f"LoadingManager initialized with {max_workers} max workers, ui_widget: {ui_widget is not None}")

    def load_critical(
        self,
        task: Callable,
        on_success: Callable = None,
        on_error: Callable = None,
        timeout: float = 30.0,
        task_name: str = "critical_task",
    ) -> str:
        """Load critical data with high priority and timeout."""
        return self._execute_task(
            task_func=task,
            on_success=on_success,
            on_error=on_error,
            timeout=timeout,
            task_name=task_name,
            priority="critical",
        )

    def load_background(
        self,
        task: Callable,
        on_success: Callable = None,
        on_error: Callable = None,
        timeout: float = 15.0,
        task_name: str = "background_task",
    ) -> str:
        """Load data in background with lower priority."""
        return self._execute_task(
            task_func=task,
            on_success=on_success,
            on_error=on_error,
            timeout=timeout,
            task_name=task_name,
            priority="background",
        )

    def _execute_task(
        self,
        task_func: Callable,
        on_success: Callable = None,
        on_error: Callable = None,
        timeout: float = 30.0,
        task_name: str = "task",
        priority: str = "normal",
    ) -> str:
        """Execute a task with proper error handling and timeout."""
        if self._shutdown:
            return None

        task_id = f"{task_name}_{len(self._active_tasks)}"

        def task_wrapper():
            start_time = time.time()
            try:
                self.logger.info(f"🔄 Starting {priority} task: {task_name}")

                # Execute the task with timeout
                result = self._run_with_timeout(task_func, timeout)

                elapsed = time.time() - start_time
                self.logger.info(
                    f"✅ Task {task_name} completed in {
                        elapsed:.2f}s"
                )

                # Call success callback directly to avoid threading issues
                if on_success and result is not None:
                    try:
                        self._safe_callback(on_success, result)
                    except Exception as e:
                        self.logger.error(
                            f"Success callback failed for {task_name}: {e}"
                        )

            except TimeoutError:
                elapsed = time.time() - start_time
                error_msg = f"Task {task_name} timed out after {elapsed:.2f}s"
                self.logger.warning(f"⏰ {error_msg}")
                if on_error:
                    try:
                        self._safe_callback(on_error, TimeoutError(error_msg))
                    except Exception as e:
                        self.logger.error(f"Error callback failed for {task_name}: {e}")

            except Exception as e:
                elapsed = time.time() - start_time
                self.logger.error(
                    f"❌ Task {task_name} failed after {
                        elapsed:.2f}s: {e}"
                )
                if on_error:
                    try:
                        self._safe_callback(on_error, e)
                    except Exception as callback_error:
                        self.logger.error(
                            f"Error callback failed for {task_name}: {callback_error}"
                        )

            finally:
                # Clean up task tracking
                self._active_tasks.pop(task_id, None)

        # Start the task in a thread
        thread = threading.Thread(
            target=task_wrapper, daemon=True, name=f"LoadingTask-{task_name}"
        )
        self._active_tasks[task_id] = {
            "thread": thread,
            "start_time": time.time(),
            "task_name": task_name,
            "priority": priority,
        }

        thread.start()
        self._threads.add(thread)

        return task_id

    def _run_with_timeout(self, task: Callable, timeout: float):
        """Run a task with timeout using threading."""
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = task()
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            # Task is still running, consider it timed out
            raise TimeoutError(f"Task timed out after {timeout} seconds")

        if exception[0]:
            raise exception[0]

        return result[0]

    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active tasks."""
        current_time = time.time()
        active_info = {}

        for task_id, task_info in self._active_tasks.items():
            elapsed = current_time - task_info["start_time"]
            active_info[task_id] = {
                "task_name": task_info["task_name"],
                "priority": task_info["priority"],
                "elapsed_time": elapsed,
                "is_alive": task_info["thread"].is_alive(),
            }

        return active_info

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a specific task.

        Args:
            task_id: The ID of the task to cancel

        Returns:
            True if task was found and cancelled, False otherwise
        """
        if task_id in self._active_tasks:
            task_info = self._active_tasks[task_id]
            self.logger.info(f"Cancelling task: {task_info['task_name']}")

            # Note: We can't actually stop a running thread in Python,
            # but we can remove it from tracking
            self._active_tasks.pop(task_id, None)
            return True

        return False

    def cancel_all_tasks(self):
        """Cancel all active tasks."""
        task_ids = list(self._active_tasks.keys())
        for task_id in task_ids:
            self.cancel_task(task_id)

        self.logger.info(f"Cancelled {len(task_ids)} tasks")

    def get_task_count(self) -> int:
        """Get the number of currently active tasks."""
        return len(self._active_tasks)

    def is_busy(self) -> bool:
        """Check if there are any active tasks."""
        return len(self._active_tasks) > 0

    def _safe_callback(self, callback: Callable, arg=None):
        """Execute a callback safely with error handling.
        
        Args:
            callback: The callback function to execute
            arg: Single argument to pass to the callback
        """
        try:
            if arg is not None:
                callback(arg)
            else:
                callback()
        except Exception as e:
            self.logger.error(f"Callback execution failed: {e}")

    def cleanup(self):
        """Clean up resources and stop all loading operations."""
        self._shutdown = True

        # Cancel all pending tasks
        for task_id in list(self._active_tasks.keys()):
            self.cancel_task(task_id)

        # Wait for threads to finish
        for thread in list(self._threads):
            if thread.is_alive():
                thread.join(timeout=1.0)

        self._threads.clear()
        self._active_tasks.clear()
        self.logger.info("LoadingManager cleanup completed")

    def shutdown(self):
        """Shutdown the LoadingManager."""
        self.cleanup()

    def __del__(self):
        """Cleanup when the object is destroyed."""
        self.cleanup()
