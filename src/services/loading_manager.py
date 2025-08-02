"""Loading Manager - Progressive Loading and State Management

Handles critical and deferred loading tasks to prevent UI freezing.
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Callable, Dict, List


class LoadingManager:
    """Manages progressive loading of application components."""

    def __init__(self):
        """Initialize loading manager."""
        self.logger = logging.getLogger("weather_dashboard.loading_manager")
        self.tasks: List[Dict[str, Any]] = []
        self.critical_loaded = False
        self._executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="LoadingManager")
        self._running = True
        self._callbacks: Dict[str, List[Callable]] = {
            "critical_complete": [],
            "deferred_complete": [],
            "task_complete": [],
            "error": [],
        }

    def add_callback(self, event: str, callback: Callable) -> None:
        """Add callback for loading events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _notify_callbacks(self, event: str, *args, **kwargs) -> None:
        """Notify registered callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Callback error for {event}: {e}")

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
        self.logger.info("🛑 Shutting down loading manager...")
        self._running = False

        try:
            self._executor.shutdown(wait=True, timeout=2.0)
            self.logger.info("✅ Loading manager shutdown complete")
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current loading status.

        Returns:
            Status dictionary with loading information
        """
        return {
            "critical_loaded": self.critical_loaded,
            "running": self._running,
            "active_tasks": len(self.tasks),
            "executor_active": not self._executor._shutdown,
        }
