"""Error Handler

Centralized error handling and reporting for the application.
"""

import logging
import traceback
from typing import Any, Dict, Optional

from .event_bus import EventTypes, publish_event
from .interfaces import IErrorHandler


class ErrorHandler(IErrorHandler):
    """Centralized error handler for the application."""

    def __init__(self):
        """Initialize the error handler."""
        self.logger = logging.getLogger(__name__)
        self.error_count = 0
        self.error_history: Dict[str, int] = {}

    def handle_error(self, error: Exception, context: str) -> None:
        """Handle an error.

        Args:
            error: The error that occurred
            context: Context where the error occurred
        """
        self.error_count += 1
        error_type = type(error).__name__

        # Track error frequency
        if error_type in self.error_history:
            self.error_history[error_type] += 1
        else:
            self.error_history[error_type] = 1

        # Log the error
        self.logger.error(
            f"Error in {context}: {error}",
            exc_info=True
        )

        # Publish error event
        publish_event(EventTypes.ERROR_OCCURRED, {
            'error_type': error_type,
            'error_message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        })

        # Show user-friendly error
        user_message = self.show_user_friendly_error(error)
        self.logger.info(f"User-friendly error message: {user_message}")

    def show_user_friendly_error(self, error: Exception) -> str:
        """Convert technical error to user-friendly message.

        Args:
            error: The technical error

        Returns:
            User-friendly error message
        """
        error_type = type(error).__name__

        # Map common errors to user-friendly messages
        error_messages = {
            'ConnectionError': "Unable to connect to weather service. Please check your internet connection.",
            'TimeoutError': "Request timed out. Please try again.",
            'ValueError': "Invalid data received. Please try again.",
            'KeyError': "Missing configuration. Please check your settings.",
            'AttributeError': "Application configuration error. Please restart the application.",
            'FileNotFoundError': "Required file not found. Please check your installation.",
            'PermissionError': "Permission denied. Please check file permissions.",
            'ImportError': "Module import error. Please check your installation.",
            'TypeError': "Data type error. Please try again.",
            'IndexError': "Data access error. Please try again.",
            'ZeroDivisionError': "Calculation error. Please try again.",
            'OSError': "System error. Please try again.",
            'MemoryError': "Insufficient memory. Please close other applications.",
            'KeyboardInterrupt': "Operation cancelled by user.",
            'SystemExit': "Application is shutting down.",
        }

        # Get specific message or default
        message = error_messages.get(error_type, "An unexpected error occurred. Please try again.")

        # Add context if available
        if hasattr(error, 'context'):
            message += f" Context: {error.context}"

        return message

    def log_error(self, error: Exception, context: str) -> None:
        """Log error for debugging.

        Args:
            error: The error to log
            context: Context where the error occurred
        """
        self.logger.error(
            f"Error in {context}: {error}",
            exc_info=True,
            extra={
                'error_type': type(error).__name__,
                'context': context,
                'error_count': self.error_count
            }
        )

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics.

        Returns:
            Dictionary with error statistics
        """
        return {
            'total_errors': self.error_count,
            'error_types': self.error_history,
            'most_common_error': max(self.error_history.items(), key=lambda x: x[1]) if self.error_history else None
        }

    def clear_error_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()
        self.error_count = 0
        self.logger.info("Error history cleared")

    def is_error_frequent(self, error_type: str, threshold: int = 5) -> bool:
        """Check if an error type is occurring frequently.

        Args:
            error_type: Type of error to check
            threshold: Frequency threshold

        Returns:
            True if error is frequent
        """
        return self.error_history.get(error_type, 0) >= threshold

    def get_error_summary(self) -> str:
        """Get a summary of recent errors.

        Returns:
            Error summary string
        """
        if not self.error_history:
            return "No errors recorded."

        summary = f"Total errors: {self.error_count}\n"
        summary += "Error breakdown:\n"

        for error_type, count in sorted(self.error_history.items(), key=lambda x: x[1], reverse=True):
            summary += f"  {error_type}: {count}\n"

        return summary


class ErrorContext:
    """Context manager for error handling."""

    def __init__(self, error_handler: ErrorHandler, context: str):
        """Initialize error context.

        Args:
            error_handler: Error handler instance
            context: Context name
        """
        self.error_handler = error_handler
        self.context = context

    def __enter__(self):
        """Enter error context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit error context."""
        if exc_val is not None:
            self.error_handler.handle_error(exc_val, self.context)
            return False  # Re-raise the exception
        return True


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance.

    Returns:
        Global error handler
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(error: Exception, context: str) -> None:
    """Handle an error using the global error handler.

    Args:
        error: The error to handle
        context: Context where the error occurred
    """
    get_error_handler().handle_error(error, context)


def show_user_friendly_error(error: Exception) -> str:
    """Show user-friendly error message.

    Args:
        error: The technical error

    Returns:
        User-friendly error message
    """
    return get_error_handler().show_user_friendly_error(error)


def error_context(context: str):
    """Decorator for error context.

    Args:
        context: Context name

    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(e, context)
                raise
        return wrapper
    return decorator


class ErrorRecovery:
    """Error recovery utilities."""

    @staticmethod
    def retry_operation(operation: callable, max_retries: int = 3, delay: float = 1.0):
        """Retry an operation with exponential backoff.

        Args:
            operation: Operation to retry
            max_retries: Maximum number of retries
            delay: Initial delay in seconds

        Returns:
            Operation result

        Raises:
            Exception: If all retries fail
        """
        import time

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff

        raise last_exception

    @staticmethod
    def fallback_operation(primary_operation: callable, fallback_operation: callable):
        """Execute fallback operation if primary fails.

        Args:
            primary_operation: Primary operation to try
            fallback_operation: Fallback operation

        Returns:
            Result from primary or fallback operation
        """
        try:
            return primary_operation()
        except Exception as e:
            handle_error(e, "primary_operation")
            return fallback_operation()

    @staticmethod
    def safe_execute(operation: callable, default_value: Any = None):
        """Safely execute an operation with a default value.

        Args:
            operation: Operation to execute
            default_value: Default value if operation fails

        Returns:
            Operation result or default value
        """
        try:
            return operation()
        except Exception as e:
            handle_error(e, "safe_execute")
            return default_value
