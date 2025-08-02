"""Logging Service - Application Logging Management

Provides centralized logging configuration and management.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for terminal output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        """Format log record with colors."""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        colored_level = f"{level_color}{
            record.levelname}{
            self.COLORS['RESET']}"

        # Create colored record
        record.colored_levelname = colored_level

        return super().format(record)


class LoggingService:
    """Service for managing application logging."""

    def __init__(self):
        """Initialize logging service."""
        self._logger: Optional[logging.Logger] = None
        self._log_file: Optional[Path] = None
        self._setup_complete = False

    def setup_logging(
        self, level: int = logging.INFO, debug_mode: bool = False, log_file: Optional[str] = None
    ) -> None:
        """Setup logging configuration."""
        if self._setup_complete:
            return

        # Create logs directory
        logs_dir = Path.cwd() / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Setup log file
        if log_file:
            self._log_file = logs_dir / log_file
        else:
            timestamp = datetime.now().strftime("%Y%m%d")
            self._log_file = logs_dir / f"weather_dashboard_{timestamp}.log"

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if debug_mode else level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        console_format = "%(colored_levelname)s " "[%(asctime)s] " "%(name)s: " "%(message)s"
        console_formatter = ColoredFormatter(console_format, datefmt="%H:%M:%S")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(self._log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        file_format = "%(levelname)s " "[%(asctime)s] " "%(name)s:%(lineno)d - " "%(message)s"
        file_formatter = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Create main logger
        self._logger = logging.getLogger("weather_dashboard")
        self._setup_complete = True

        # Log setup completion
        self._logger.info(f"📝 Logging initialized - Level: {logging.getLevelName(level)}")
        self._logger.debug(f"📁 Log file: {self._log_file}")

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for the given name."""
        if not self._setup_complete:
            self.setup_logging()

        return logging.getLogger(f"weather_dashboard.{name}")

    def set_level(self, level: int) -> None:
        """Set logging level for all handlers."""
        if not self._setup_complete:
            return

        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                handler.setLevel(level)

    def get_log_file_path(self) -> Optional[Path]:
        """Get the current log file path."""
        return self._log_file

    def get_recent_logs(self, lines: int = 50) -> list[str]:
        """Get recent log entries from file."""
        if not self._log_file or not self._log_file.exists():
            return []

        try:
            with open(self._log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return [line.strip() for line in all_lines[-lines:]]
        except Exception as e:
            return [f"Error reading log file: {e}"]

    def clear_logs(self) -> bool:
        """Clear the current log file."""
        if not self._log_file:
            return False

        try:
            with open(self._log_file, "w", encoding="utf-8") as f:
                f.write("")

            if self._logger:
                self._logger.info("📝 Log file cleared")

            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to clear log file: {e}")
            return False
