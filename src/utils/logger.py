#!/usr/bin/env python3
"""
Logging Utility - Professional Application Logging

This module provides comprehensive logging configuration for the weather dashboard,
demonstrating professional logging practices including:
- Structured logging with multiple handlers
- Log rotation and file management
- Performance monitoring integration
- Debug and production configurations
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import sys
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds color coding to console output.

    This enhances development experience by making log levels
    visually distinct in the console output.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        """Format log record with color coding."""
        # Get the original formatted message
        formatted = super().format(record)

        # Add color if outputting to a terminal
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            formatted = f"{color}{formatted}{reset}"

        return formatted


class PerformanceFilter(logging.Filter):
    """
    Custom filter that adds performance metrics to log records.

    This filter demonstrates advanced logging techniques by adding
    contextual information to log records for performance monitoring.
    """

    def __init__(self):
        super().__init__()
        self.start_time = datetime.now()

    def filter(self, record):
        """Add performance metrics to log record."""
        # Add application uptime
        uptime = datetime.now() - self.start_time
        record.uptime = f"{uptime.total_seconds():.2f}s"

        # Add memory usage if available
        try:
            import psutil
            process = psutil.Process()
            record.memory_mb = f"{process.memory_info().rss / 1024 / 1024:.1f}MB"
        except ImportError:
            record.memory_mb = "N/A"

        return True


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_performance: bool = False
) -> None:
    """
    Set up comprehensive logging for the weather dashboard application.

    This function demonstrates professional logging configuration including:
    - Multiple output handlers (console, file, rotating file)
    - Custom formatters for different output types
    - Performance monitoring integration
    - Proper log level management

    Args:
        log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_dir: Directory for log files (defaults to ~/.weather_dashboard/logs)
        enable_console: Whether to enable console logging
        enable_file: Whether to enable file logging
        enable_performance: Whether to enable performance monitoring
    """

    # Set up log directory
    if log_dir is None:
        log_dir = Path.home() / ".weather_dashboard" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler with colored output
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)

        # Use colored formatter for console
        console_format = (
            "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
        )

        if enable_performance:
            console_format = (
                "%(asctime)s | %(name)-20s | %(levelname)-8s | "
                "[%(uptime)s | %(memory_mb)s] | %(message)s"
            )
            console_handler.addFilter(PerformanceFilter())

        console_formatter = ColoredFormatter(
            console_format,
            datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler for persistent logging
    if enable_file:
        # Main log file
        file_handler = logging.FileHandler(
            log_dir / "weather_dashboard.log",
            encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)

        # Detailed format for file logging
        file_format = (
            "%(asctime)s | %(name)s | %(levelname)s | "
            "%(filename)s:%(lineno)d | %(funcName)s | %(message)s"
        )

        if enable_performance:
            file_format = (
                "%(asctime)s | %(name)s | %(levelname)s | "
                "[%(uptime)s | %(memory_mb)s] | "
                "%(filename)s:%(lineno)d | %(funcName)s | %(message)s"
            )
            file_handler.addFilter(PerformanceFilter())

        file_formatter = logging.Formatter(
            file_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Rotating file handler for long-running applications
        rotating_handler = logging.handlers.RotatingFileHandler(
            log_dir / "weather_dashboard_rotating.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        rotating_handler.setLevel(numeric_level)
        rotating_handler.setFormatter(file_formatter)

        if enable_performance:
            rotating_handler.addFilter(PerformanceFilter())

        root_logger.addHandler(rotating_handler)

        # Error-only file handler
        error_handler = logging.FileHandler(
            log_dir / "weather_dashboard_errors.log",
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

    # Set specific log levels for third-party libraries
    _configure_third_party_logging()

    # Log the logging configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, Console: {enable_console}, File: {enable_file}")
    logger.info(f"Log directory: {log_dir}")

    if enable_performance:
        logger.info("Performance monitoring enabled")


def _configure_third_party_logging() -> None:
    """
    Configure logging levels for third-party libraries.

    This prevents verbose third-party logs from cluttering our application logs
    while still capturing important information.
    """
    # Reduce verbosity of common third-party libraries
    third_party_loggers = {
        "urllib3": logging.WARNING,
        "requests": logging.WARNING,
        "PIL": logging.WARNING,
        "matplotlib": logging.WARNING,
        "github": logging.WARNING,
        "google": logging.WARNING,
        "spotipy": logging.WARNING,
    }

    for logger_name, level in third_party_loggers.items():
        logging.getLogger(logger_name).setLevel(level)


class LoggerMixin:
    """
    Mixin class that provides easy logging access to any class.

    This mixin demonstrates a professional pattern for adding logging
    capabilities to classes without inheritance complexity.
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class."""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


class ContextLogger:
    """
    Context manager for adding contextual information to logs.

    This class demonstrates advanced logging patterns for adding
    request/operation context to log messages.
    """

    def __init__(self, logger: logging.Logger, context: str, **kwargs):
        """
        Initialize context logger.

        Args:
            logger: Logger instance
            context: Context description
            **kwargs: Additional context data
        """
        self.logger = logger
        self.context = context
        self.context_data = kwargs
        self.start_time = None

    def __enter__(self):
        """Enter context and log start."""
        self.start_time = datetime.now()
        context_str = self._format_context()
        self.logger.info(f"Starting {self.context}{context_str}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and log completion/error."""
        duration = datetime.now() - self.start_time
        context_str = self._format_context()

        if exc_type is None:
            self.logger.info(
                f"Completed {self.context}{context_str} in {duration.total_seconds():.2f}s"
            )
        else:
            self.logger.error(
                f"Failed {self.context}{context_str} after {duration.total_seconds():.2f}s: {exc_val}"
            )

        # Don't suppress exceptions
        return False

    def _format_context(self) -> str:
        """Format context data for logging."""
        if not self.context_data:
            return ""

        context_items = [f"{k}={v}" for k, v in self.context_data.items()]
        return f" ({', '.join(context_items)})"


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    This is a convenience function that ensures consistent logger naming
    throughout the application.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_performance(func):
    """
    Decorator for logging function performance.

    This decorator demonstrates how to add performance monitoring
    to functions without modifying their implementation.

    Args:
        func: Function to monitor

    Returns:
        Wrapped function with performance logging
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)

        with ContextLogger(logger, f"function {func.__name__}"):
            return func(*args, **kwargs)

    return wrapper


# Example usage and testing functions
def test_logging_configuration():
    """
    Test function to verify logging configuration.

    This function can be called during development to ensure
    logging is working correctly.
    """
    logger = get_logger(__name__)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Test context logging
    with ContextLogger(logger, "test operation", user="test_user", operation_id="12345"):
        logger.info("Performing test operation")
        # Simulate some work
        import time
        time.sleep(0.1)

    logger.info("Logging test completed")


if __name__ == "__main__":
    # Test the logging configuration
    setup_logging(log_level="DEBUG", enable_performance=True)
    test_logging_configuration()
