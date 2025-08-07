"""Logging configuration for the Weather Dashboard application.

This module provides centralized logging configuration with structured
logging, file rotation, and different log levels for development and production.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
        
        # Add context information
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'session_id'):
            log_data["session_id"] = record.session_id
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """Filter to add contextual information to log records."""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context information to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class WeatherAppLogger:
    """Centralized logger configuration for the Weather Dashboard."""
    
    _instance = None
    _configured = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._configured:
            self.setup_logging()
            self._configured = True
    
    def setup_logging(self, debug_mode: Optional[bool] = None, 
                     log_dir: Optional[str] = None,
                     structured_logging: bool = False) -> None:
        """Setup logging configuration.
        
        Args:
            debug_mode: Enable debug logging. If None, checks environment
            log_dir: Directory for log files. Defaults to 'logs'
            structured_logging: Use JSON structured logging format
        """
        # Determine debug mode
        if debug_mode is None:
            debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # Set log level
        level = logging.DEBUG if debug_mode else logging.INFO
        
        # Create log directory
        if log_dir is None:
            log_dir = 'logs'
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # Choose formatter
        if structured_logging:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / 'weather_app.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / 'weather_app_errors.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Console handler (warnings and above in production)
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.WARNING if not debug_mode else logging.DEBUG)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)
        
        # Configure specific loggers
        self._configure_library_loggers(debug_mode)
        
        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured - Debug mode: {debug_mode}, Level: {logging.getLevelName(level)}")
    
    def _configure_library_loggers(self, debug_mode: bool) -> None:
        """Configure logging levels for third-party libraries."""
        # Reduce noise from third-party libraries
        library_loggers = {
            'urllib3': logging.WARNING,
            'requests': logging.WARNING,
            'matplotlib': logging.WARNING,
            'PIL': logging.WARNING,
            'tkinter': logging.WARNING,
            'asyncio': logging.WARNING if not debug_mode else logging.INFO
        }
        
        for logger_name, level in library_loggers.items():
            logging.getLogger(logger_name).setLevel(level)
    
    def get_logger(self, name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """Get a logger with optional context.
        
        Args:
            name: Logger name (usually __name__)
            context: Additional context to include in logs
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        
        if context:
            context_filter = ContextFilter(context)
            logger.addFilter(context_filter)
        
        return logger


# Global logger instance
_logger_instance = WeatherAppLogger()


def setup_logging(debug_mode: Optional[bool] = None, 
                 log_dir: Optional[str] = None,
                 structured_logging: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        debug_mode: Enable debug logging. If None, checks environment
        log_dir: Directory for log files. Defaults to 'logs'
        structured_logging: Use JSON structured logging format
    """
    _logger_instance.setup_logging(debug_mode, log_dir, structured_logging)


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """Get a logger with optional context.
    
    Args:
        name: Logger name (usually __name__)
        context: Additional context to include in logs
        
    Returns:
        Configured logger instance
    """
    return _logger_instance.get_logger(name, context)


def log_exception(logger: logging.Logger, error: Exception, 
                 context: Optional[Dict[str, Any]] = None) -> None:
    """Log an exception with context information.
    
    Args:
        logger: Logger instance
        error: Exception to log
        context: Additional context information
    """
    extra_data = {
        "error_type": type(error).__name__,
        "error_message": str(error)
    }
    
    if context:
        extra_data.update(context)
    
    # Add exception context if it's a custom exception
    if hasattr(error, 'to_dict'):
        extra_data.update(error.to_dict())
    
    logger.error(
        f"Exception occurred: {type(error).__name__}: {error}",
        exc_info=True,
        extra={'extra_data': extra_data}
    )


def log_performance(logger: logging.Logger, operation: str, 
                   duration: float, context: Optional[Dict[str, Any]] = None) -> None:
    """Log performance metrics.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        duration: Duration in seconds
        context: Additional context information
    """
    extra_data = {
        "operation": operation,
        "duration_seconds": duration,
        "performance_metric": True
    }
    
    if context:
        extra_data.update(context)
    
    logger.info(
        f"Performance: {operation} completed in {duration:.3f}s",
        extra={'extra_data': extra_data}
    )


def log_api_call(logger: logging.Logger, api_name: str, endpoint: str,
                status_code: Optional[int] = None, duration: Optional[float] = None,
                context: Optional[Dict[str, Any]] = None) -> None:
    """Log API call information.
    
    Args:
        logger: Logger instance
        api_name: Name of the API service
        endpoint: API endpoint called
        status_code: HTTP status code
        duration: Request duration in seconds
        context: Additional context information
    """
    extra_data = {
        "api_name": api_name,
        "endpoint": endpoint,
        "api_call": True
    }
    
    if status_code is not None:
        extra_data["status_code"] = status_code
    if duration is not None:
        extra_data["duration_seconds"] = duration
    if context:
        extra_data.update(context)
    
    message = f"API call: {api_name} - {endpoint}"
    if status_code:
        message += f" (Status: {status_code})"
    if duration:
        message += f" (Duration: {duration:.3f}s)"
    
    logger.info(message, extra={'extra_data': extra_data})


# Initialize logging on module import
setup_logging()