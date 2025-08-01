"""Thread-safe service wrapper for all UI updates."""

import logging
import queue
from functools import wraps
from typing import Callable


class ThreadSafeUIUpdater:
    """Thread-safe UI update service that ensures all updates happen on main thread."""

    def __init__(self, root_widget):
        """Initialize with reference to root widget."""
        self.root = root_widget
        self.update_queue = queue.Queue()
        self.logger = logging.getLogger(__name__)
        self._running = True
        self._process_callback_id = None

        # Start processing updates
        self._process_updates()

    def _process_updates(self):
        """Process queued UI updates on main thread."""
        try:
            # Clear any existing callback ID
            self._process_callback_id = None

            # Process all queued updates
            while not self.update_queue.empty():
                try:
                    update_func = self.update_queue.get_nowait()
                    if callable(update_func):
                        update_func()
                except queue.Empty:
                    break
                except Exception as e:
                    self.logger.warning(f"UI update error: {e}")

            # Schedule next processing cycle only if still running
            if self._running and hasattr(self.root, "winfo_exists") and self.root.winfo_exists():
                self._process_callback_id = self.root.after(
                    50, self._process_updates
                )  # Process every 50ms

        except Exception as e:
            self.logger.error(f"Update processing error: {e}")
            if self._running and hasattr(self.root, "winfo_exists") and self.root.winfo_exists():
                self._process_callback_id = self.root.after(
                    100, self._process_updates
                )  # Retry with longer delay

    def schedule_update(self, update_func: Callable):
        """Schedule a UI update to run on the main thread."""
        try:
            self.update_queue.put(update_func)
        except Exception as e:
            self.logger.warning(f"Failed to schedule update: {e}")

    def safe_update(self, widget, update_func):
        """Safely update a widget with existence check."""

        def _update():
            try:
                if hasattr(widget, "winfo_exists") and widget.winfo_exists():
                    update_func()
            except Exception as e:
                self.logger.warning(f"Widget update failed: {e}")

        self.schedule_update(_update)

    def stop(self):
        """Stop the update processor."""
        self._running = False

        # Cancel any pending callback
        if self._process_callback_id and hasattr(self.root, "after_cancel"):
            try:
                self.root.after_cancel(self._process_callback_id)
                self._process_callback_id = None
            except Exception as e:
                self.logger.debug(f"Error cancelling process callback: {e}")


def thread_safe_ui_update(ui_updater: ThreadSafeUIUpdater):
    """Decorator to make UI update methods thread-safe."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def _update():
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.getLogger(__name__).warning(f"Thread-safe update error: {e}")

            ui_updater.schedule_update(_update)

        return wrapper

    return decorator
