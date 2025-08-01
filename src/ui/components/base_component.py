"""Base component class with proper after() cleanup handling."""

import logging
from typing import Callable, Optional

import customtkinter as ctk


class BaseComponent(ctk.CTkFrame):
    """Base class for all UI components with proper cleanup handling."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._scheduled_callbacks = set()
        self._is_destroyed = False

    def after(self, ms: int, func: Optional[Callable] = None, *args) -> Optional[str]:
        """Override after method to track scheduled callbacks for proper cleanup."""
        if self._is_destroyed:
            self.logger.debug("Component destroyed, skipping after call")
            return None

        if func is None:
            return super().after(ms)

        try:
            callback_id = super().after(ms, func, *args)
            if callback_id:
                self._scheduled_callbacks.add(callback_id)
            return callback_id
        except Exception as e:
            error_msg = str(e).lower()
            if (
                "invalid command name" in error_msg
                or "main thread is not in main loop" in error_msg
            ):
                self.logger.debug(f"Suppressed after scheduling error: {e}")
                return None
            else:
                raise e

    def after_cancel(self, id: str) -> None:
        """Override after_cancel to remove from tracking set."""
        try:
            super().after_cancel(id)
            self._scheduled_callbacks.discard(id)
        except Exception as e:
            # Callback may have already executed or been cancelled
            self._scheduled_callbacks.discard(id)
            self.logger.debug(f"after_cancel error (ignored): {e}")

    def cleanup(self) -> None:
        """Cancel all pending callbacks and mark as destroyed."""
        if self._is_destroyed:
            return

        self._is_destroyed = True
        cancelled_count = 0

        for callback_id in list(self._scheduled_callbacks):
            try:
                self.after_cancel(callback_id)
                cancelled_count += 1
            except Exception:
                pass  # Callback may have already executed

        self._scheduled_callbacks.clear()

        if cancelled_count > 0:
            self.logger.debug(f"Cancelled {cancelled_count} pending callbacks")

    def destroy(self) -> None:
        """Override destroy to ensure cleanup."""
        self.cleanup()
        super().destroy()
