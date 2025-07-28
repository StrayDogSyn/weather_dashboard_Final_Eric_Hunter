#!/usr/bin/env python3
"""
Logging Service Implementation for Dependency Injection

This module provides the concrete implementation of ILoggingService interface,
creating a comprehensive logging system that works with the dependency injection system.
It demonstrates professional logging patterns and best practices.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0 (Dependency Injection Implementation)
"""

import logging
import logging.handlers
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

from core.interfaces import ILoggingService, IConfigurationService


class LoggingServiceImpl(ILoggingService):
    """Implementation of ILoggingService with comprehensive logging capabilities.
    
    This implementation provides structured logging with file rotation,
    multiple log levels, and configurable output formats. It demonstrates
    how to create a production-ready logging service for dependency injection.
    """
    
    def __init__(self, 
                 config_service: Optional[IConfigurationService] = None,
                 logger_name: str = "WeatherDashboard"):
        """Initialize the logging service implementation.
        
        Args:
            config_service: Optional configuration service for logging settings
            logger_name: Name for the logger instance
        """
        self._config_service = config_service
        self._logger_name = logger_name
        self._logger = logging.getLogger(logger_name)
        
        # Prevent duplicate handlers if logger already configured
        if not self._logger.handlers:
            self._setup_logging()
        
        self.info(f"LoggingServiceImpl initialized for {logger_name}")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration based on settings."""
        try:
            # Get logging configuration
            log_level = self._get_config('logging.level', 'INFO')
            file_enabled = self._get_config('logging.file_enabled', True)
            file_path = self._get_config('logging.file_path', 'logs/weather_dashboard.log')
            max_file_size_mb = self._get_config('logging.max_file_size_mb', 10)
            backup_count = self._get_config('logging.backup_count', 5)
            
            # Set logger level
            self._logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
            
            # File handler with rotation
            if file_enabled:
                log_path = Path(file_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.handlers.RotatingFileHandler(
                    filename=log_path,
                    maxBytes=max_file_size_mb * 1024 * 1024,  # Convert MB to bytes
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)
            
            # Prevent propagation to root logger
            self._logger.propagate = False
            
        except Exception as e:
            # Fallback to basic console logging if setup fails
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
            self._logger.setLevel(logging.INFO)
            self._logger.error(f"Error setting up logging: {e}")
    
    def _get_config(self, key: str, default: Any) -> Any:
        """Get configuration value with fallback to default.
        
        Args:
            key: Configuration key
            default: Default value
            
        Returns:
            Configuration value or default
        """
        if self._config_service:
            return self._config_service.get_setting(key, default)
        return default
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format log message with additional context.
        
        Args:
            message: Base log message
            **kwargs: Additional context data
            
        Returns:
            Formatted message string
        """
        if kwargs:
            context_parts = [f"{k}={v}" for k, v in kwargs.items()]
            context_str = " | ".join(context_parts)
            return f"{message} | {context_str}"
        return message
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message.
        
        Args:
            message: Debug message
            **kwargs: Additional context data
        """
        formatted_message = self._format_message(message, **kwargs)
        self._logger.debug(formatted_message)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message.
        
        Args:
            message: Info message
            **kwargs: Additional context data
        """
        formatted_message = self._format_message(message, **kwargs)
        self._logger.info(formatted_message)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message.
        
        Args:
            message: Warning message
            **kwargs: Additional context data
        """
        formatted_message = self._format_message(message, **kwargs)
        self._logger.warning(formatted_message)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message.
        
        Args:
            message: Error message
            **kwargs: Additional context data
        """
        formatted_message = self._format_message(message, **kwargs)
        self._logger.error(formatted_message)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message.
        
        Args:
            message: Critical message
            **kwargs: Additional context data
        """
        formatted_message = self._format_message(message, **kwargs)
        self._logger.critical(formatted_message)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log an exception with traceback.
        
        Args:
            message: Exception message
            **kwargs: Additional context data
        """
        formatted_message = self._format_message(message, **kwargs)
        self._logger.exception(formatted_message)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message at the specified level.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **kwargs: Additional context data
        """
        try:
            log_level = getattr(logging, level.upper(), logging.INFO)
            formatted_message = self._format_message(message, **kwargs)
            self._logger.log(log_level, formatted_message)
        except AttributeError:
            self.error(f"Invalid log level: {level}. Message: {message}", **kwargs)
    
    def set_level(self, level: str) -> bool:
        """Set the logging level.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            True if level was set successfully, False otherwise
        """
        try:
            log_level = getattr(logging, level.upper())
            self._logger.setLevel(log_level)
            self.info(f"Logging level set to {level.upper()}")
            return True
        except AttributeError:
            self.error(f"Invalid log level: {level}")
            return False
    
    def get_level(self) -> str:
        """Get the current logging level.
        
        Returns:
            Current log level name
        """
        return logging.getLevelName(self._logger.level)
    
    def add_handler(self, handler: logging.Handler) -> bool:
        """Add a custom logging handler.
        
        Args:
            handler: Logging handler to add
            
        Returns:
            True if handler was added successfully, False otherwise
        """
        try:
            self._logger.addHandler(handler)
            self.info(f"Added logging handler: {type(handler).__name__}")
            return True
        except Exception as e:
            self.error(f"Error adding logging handler: {e}")
            return False
    
    def remove_handler(self, handler: logging.Handler) -> bool:
        """Remove a logging handler.
        
        Args:
            handler: Logging handler to remove
            
        Returns:
            True if handler was removed successfully, False otherwise
        """
        try:
            self._logger.removeHandler(handler)
            self.info(f"Removed logging handler: {type(handler).__name__}")
            return True
        except Exception as e:
            self.error(f"Error removing logging handler: {e}")
            return False
    
    def get_logger_info(self) -> Dict[str, Any]:
        """Get information about the logger.
        
        Returns:
            Dictionary containing logger information
        """
        try:
            handlers_info = []
            for handler in self._logger.handlers:
                handler_info = {
                    'type': type(handler).__name__,
                    'level': logging.getLevelName(handler.level),
                    'formatter': str(handler.formatter._fmt) if handler.formatter else None
                }
                
                # Add specific info for file handlers
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler_info.update({
                        'filename': handler.baseFilename,
                        'max_bytes': handler.maxBytes,
                        'backup_count': handler.backupCount
                    })
                
                handlers_info.append(handler_info)
            
            info = {
                'logger_name': self._logger_name,
                'level': self.get_level(),
                'handlers_count': len(self._logger.handlers),
                'handlers': handlers_info,
                'propagate': self._logger.propagate,
                'disabled': self._logger.disabled
            }
            
            return info
            
        except Exception as e:
            self.error(f"Error getting logger info: {e}")
            return {}
    
    def flush(self) -> None:
        """Flush all logging handlers."""
        try:
            for handler in self._logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
        except Exception as e:
            self.error(f"Error flushing logging handlers: {e}")
    
    def close(self) -> None:
        """Close all logging handlers."""
        try:
            for handler in self._logger.handlers[:]:
                if hasattr(handler, 'close'):
                    handler.close()
                self._logger.removeHandler(handler)
            self.info("Logging service closed")
        except Exception as e:
            print(f"Error closing logging service: {e}")  # Use print since logger may be closed


class MockLoggingService(ILoggingService):
    """Mock logging service implementation for testing.
    
    This class provides a mock implementation of ILoggingService
    that can be used for unit testing and development scenarios
    where real logging is not needed or should be captured.
    """
    
    def __init__(self, capture_logs: bool = True):
        """Initialize the mock logging service.
        
        Args:
            capture_logs: Whether to capture log messages for testing
        """
        self._capture_logs = capture_logs
        self._captured_logs: List[Dict[str, Any]] = []
        self._current_level = 'INFO'
        self._should_fail = False
        
        if capture_logs:
            self.info("MockLoggingService initialized with log capture")
        else:
            print("MockLoggingService initialized without log capture")
    
    def _capture_log(self, level: str, message: str, **kwargs) -> None:
        """Capture a log message for testing.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional context data
        """
        if self._capture_logs:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message,
                'context': kwargs
            }
            self._captured_logs.append(log_entry)
        
        # Also print to console for visibility during development
        context_str = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        full_message = f"{message} | {context_str}" if context_str else message
        print(f"[{level}] {full_message}")
    
    def set_should_fail(self, should_fail: bool) -> None:
        """Set whether the service should simulate failures.
        
        Args:
            should_fail: Whether to simulate failures
        """
        self._should_fail = should_fail
    
    def get_captured_logs(self) -> List[Dict[str, Any]]:
        """Get all captured log messages.
        
        Returns:
            List of captured log entries
        """
        return self._captured_logs.copy()
    
    def clear_captured_logs(self) -> None:
        """Clear all captured log messages."""
        self._captured_logs.clear()
    
    def get_logs_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Get captured logs filtered by level.
        
        Args:
            level: Log level to filter by
            
        Returns:
            List of log entries at the specified level
        """
        return [log for log in self._captured_logs if log['level'] == level.upper()]
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message.
        
        Args:
            message: Debug message
            **kwargs: Additional context data
        """
        if not self._should_fail:
            self._capture_log('DEBUG', message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message.
        
        Args:
            message: Info message
            **kwargs: Additional context data
        """
        if not self._should_fail:
            self._capture_log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message.
        
        Args:
            message: Warning message
            **kwargs: Additional context data
        """
        if not self._should_fail:
            self._capture_log('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message.
        
        Args:
            message: Error message
            **kwargs: Additional context data
        """
        if not self._should_fail:
            self._capture_log('ERROR', message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message.
        
        Args:
            message: Critical message
            **kwargs: Additional context data
        """
        if not self._should_fail:
            self._capture_log('CRITICAL', message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log an exception with traceback.
        
        Args:
            message: Exception message
            **kwargs: Additional context data
        """
        if not self._should_fail:
            self._capture_log('EXCEPTION', message, **kwargs)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message at the specified level.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional context data
        """
        if not self._should_fail:
            self._capture_log(level.upper(), message, **kwargs)
    
    def set_level(self, level: str) -> bool:
        """Set the logging level.
        
        Args:
            level: Log level
            
        Returns:
            True unless simulating failure
        """
        if self._should_fail:
            return False
        
        self._current_level = level.upper()
        self.info(f"MockLoggingService level set to {self._current_level}")
        return True
    
    def get_level(self) -> str:
        """Get the current logging level.
        
        Returns:
            Current log level name
        """
        return self._current_level
    
    def add_handler(self, handler: logging.Handler) -> bool:
        """Add a custom logging handler.
        
        Args:
            handler: Logging handler to add
            
        Returns:
            True unless simulating failure
        """
        if self._should_fail:
            return False
        
        self.info(f"MockLoggingService added handler: {type(handler).__name__}")
        return True
    
    def remove_handler(self, handler: logging.Handler) -> bool:
        """Remove a logging handler.
        
        Args:
            handler: Logging handler to remove
            
        Returns:
            True unless simulating failure
        """
        if self._should_fail:
            return False
        
        self.info(f"MockLoggingService removed handler: {type(handler).__name__}")
        return True
    
    def get_logger_info(self) -> Dict[str, Any]:
        """Get information about the mock logger.
        
        Returns:
            Dictionary containing mock logger information
        """
        if self._should_fail:
            return {}
        
        info = {
            'logger_name': 'MockLogger',
            'level': self._current_level,
            'handlers_count': 1,  # Mock handler count
            'handlers': [{
                'type': 'MockHandler',
                'level': self._current_level,
                'formatter': 'MockFormatter'
            }],
            'propagate': False,
            'disabled': False,
            'captured_logs_count': len(self._captured_logs),
            'capture_enabled': self._capture_logs,
            'should_fail': self._should_fail
        }
        
        return info
    
    def flush(self) -> None:
        """Flush all logging handlers."""
        if not self._should_fail:
            self.debug("MockLoggingService flushed")
    
    def close(self) -> None:
        """Close all logging handlers."""
        if not self._should_fail:
            self.info("MockLoggingService closed")