#!/usr/bin/env python3
"""
Logging Configuration for Weather Dashboard Scripts

Provides centralized logging setup with:
- Consistent formatting
- File and console output
- Configurable log levels
- Rotation support
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Setup logger with consistent configuration.
    
    Args:
        name: Logger name (usually script name)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (defaults to project_root/logs)
        console_output: Enable console output
        file_output: Enable file output
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set log level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatters
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output:
        if log_dir is None:
            # Find project root and create logs directory
            current = Path(__file__).parent
            while current != current.parent:
                if (current / "main.py").exists() or (current / "requirements.txt").exists():
                    log_dir = current / "logs"
                    break
                current = current.parent
            else:
                log_dir = Path.cwd() / "logs"
        
        # Create log directory if it doesn't exist
        log_dir.mkdir(exist_ok=True)
        
        # Create log file path
        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one with default settings."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


class LogContext:
    """Context manager for temporary log level changes."""
    
    def __init__(self, logger: logging.Logger, level: str):
        self.logger = logger
        self.new_level = getattr(logging, level.upper())
        self.old_level = logger.level
    
    def __enter__(self):
        self.logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)


# Convenience function for script logging
def log_script_start(logger: logging.Logger, script_name: str, version: str, args: dict = None):
    """Log script startup information."""
    logger.info(f"="*60)
    logger.info(f"Starting {script_name} v{version}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    if args:
        logger.info("Arguments:")
        for key, value in args.items():
            logger.info(f"  {key}: {value}")
    logger.info(f"="*60)


def log_script_end(logger: logging.Logger, script_name: str, execution_time: float, success: bool = True):
    """Log script completion information."""
    status = "COMPLETED" if success else "FAILED"
    logger.info(f"="*60)
    logger.info(f"{script_name} {status}")
    logger.info(f"Execution time: {execution_time:.2f} seconds")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"="*60)