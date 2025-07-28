#!/usr/bin/env python3
"""
Comprehensive Logging Framework

Provides standardized logging with:
- Structured logging with correlation IDs
- Performance monitoring and metrics
- Contextual logging with automatic enrichment
- Multiple output formats (JSON, text)
- Log aggregation and filtering
- Security-aware logging (PII scrubbing)

Follows Microsoft's recommended logging practices for production applications.
"""

import json
import logging
import logging.handlers
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, Union, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from enum import Enum
from threading import local
import traceback
import re

from .exceptions import BaseApplicationError, ErrorSeverity


class LogLevel(Enum):
    """Enhanced log levels with numeric values."""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    AUDIT = 60


class LogFormat(Enum):
    """Log output formats."""
    JSON = "json"
    TEXT = "text"
    STRUCTURED = "structured"


@dataclass
class LogContext:
    """Context information for log entries."""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    success: bool = True
    error_count: int = 0
    
    def finish(self):
        """Mark operation as finished and calculate metrics."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)


class PIIScrubber:
    """Scrubs personally identifiable information from logs."""
    
    def __init__(self):
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            'api_key': re.compile(r'\b[A-Za-z0-9]{32,}\b'),
            'password': re.compile(r'(password|pwd|pass)\s*[:=]\s*[^\s]+', re.IGNORECASE)
        }
    
    def scrub(self, text: str) -> str:
        """Scrub PII from text."""
        if not isinstance(text, str):
            return text
        
        scrubbed = text
        for pattern_name, pattern in self.patterns.items():
            scrubbed = pattern.sub(f'[REDACTED_{pattern_name.upper()}]', scrubbed)
        
        return scrubbed
    
    def scrub_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively scrub PII from dictionary."""
        if not isinstance(data, dict):
            return data
        
        scrubbed = {}
        for key, value in data.items():
            if isinstance(value, str):
                scrubbed[key] = self.scrub(value)
            elif isinstance(value, dict):
                scrubbed[key] = self.scrub_dict(value)
            elif isinstance(value, list):
                scrubbed[key] = [self.scrub_dict(item) if isinstance(item, dict) else self.scrub(str(item)) for item in value]
            else:
                scrubbed[key] = value
        
        return scrubbed


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def __init__(self, format_type: LogFormat = LogFormat.JSON, scrub_pii: bool = True):
        super().__init__()
        self.format_type = format_type
        self.scrubber = PIIScrubber() if scrub_pii else None
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured data."""
        # Build base log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process
        }
        
        # Add context if available
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
        
        # Add performance metrics if available
        if hasattr(record, 'performance'):
            log_entry['performance'] = record.performance
        
        # Add exception information
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info', 'context', 'correlation_id', 'performance']:
                log_entry['extra'] = log_entry.get('extra', {})
                log_entry['extra'][key] = value
        
        # Scrub PII if enabled
        if self.scrubber:
            log_entry = self.scrubber.scrub_dict(log_entry)
        
        # Format output
        if self.format_type == LogFormat.JSON:
            return json.dumps(log_entry, default=str, ensure_ascii=False)
        elif self.format_type == LogFormat.STRUCTURED:
            return self._format_structured(log_entry)
        else:
            return self._format_text(log_entry)
    
    def _format_structured(self, log_entry: Dict[str, Any]) -> str:
        """Format as structured text."""
        parts = [
            f"[{log_entry['timestamp']}]",
            f"[{log_entry['level']}]",
            f"[{log_entry.get('correlation_id', 'N/A')}]",
            f"[{log_entry['logger']}]",
            log_entry['message']
        ]
        
        if 'context' in log_entry:
            parts.append(f"Context: {json.dumps(log_entry['context'])}")
        
        if 'performance' in log_entry:
            perf = log_entry['performance']
            if 'duration_ms' in perf:
                parts.append(f"Duration: {perf['duration_ms']:.2f}ms")
        
        return ' '.join(parts)
    
    def _format_text(self, log_entry: Dict[str, Any]) -> str:
        """Format as human-readable text."""
        timestamp = log_entry['timestamp'][:19]  # Remove timezone for readability
        return f"{timestamp} [{log_entry['level']}] {log_entry['logger']}: {log_entry['message']}"


class ContextualLogger:
    """Logger with automatic context enrichment."""
    
    def __init__(self, name: str, context: Optional[LogContext] = None):
        self.logger = logging.getLogger(name)
        self.context = context or LogContext()
        self._local = local()
    
    def _get_current_context(self) -> LogContext:
        """Get current context, merging thread-local and instance context."""
        # Start with instance context
        merged_context = LogContext(**asdict(self.context))
        
        # Merge thread-local context if available
        if hasattr(self._local, 'context'):
            local_context = self._local.context
            for field_name, field_value in asdict(local_context).items():
                if field_value is not None:
                    setattr(merged_context, field_name, field_value)
        
        return merged_context
    
    def _log_with_context(self, level: int, message: str, *args, **kwargs):
        """Log message with context enrichment."""
        current_context = self._get_current_context()
        
        # Create extra dict for context
        extra = kwargs.get('extra', {})
        extra['context'] = current_context.to_dict()
        extra['correlation_id'] = current_context.correlation_id
        kwargs['extra'] = extra
        
        self.logger.log(level, message, *args, **kwargs)
    
    def trace(self, message: str, *args, **kwargs):
        """Log trace message."""
        self._log_with_context(LogLevel.TRACE.value, message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self._log_with_context(LogLevel.DEBUG.value, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self._log_with_context(LogLevel.INFO.value, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self._log_with_context(LogLevel.WARNING.value, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self._log_with_context(LogLevel.ERROR.value, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self._log_with_context(LogLevel.CRITICAL.value, message, *args, **kwargs)
    
    def audit(self, message: str, *args, **kwargs):
        """Log audit message."""
        self._log_with_context(LogLevel.AUDIT.value, message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback."""
        kwargs['exc_info'] = True
        self.error(message, *args, **kwargs)
    
    def log_error(self, error: BaseApplicationError):
        """Log application error with structured data."""
        extra = {
            'error_data': error.to_dict(),
            'correlation_id': error.correlation_id
        }
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.critical(f"Critical error: {error.message}", extra=extra)
        elif error.severity == ErrorSeverity.HIGH:
            self.error(f"High severity error: {error.message}", extra=extra)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.warning(f"Medium severity error: {error.message}", extra=extra)
        else:
            self.info(f"Low severity error: {error.message}", extra=extra)
    
    @contextmanager
    def context(self, **context_updates):
        """Context manager for temporary context updates."""
        # Save current context
        old_context = getattr(self._local, 'context', None)
        
        # Create new context
        new_context = self._get_current_context()
        for key, value in context_updates.items():
            if hasattr(new_context, key):
                setattr(new_context, key, value)
            else:
                new_context.custom_fields[key] = value
        
        self._local.context = new_context
        
        try:
            yield
        finally:
            # Restore old context
            if old_context:
                self._local.context = old_context
            else:
                delattr(self._local, 'context')
    
    @contextmanager
    def performance_tracking(self, operation: str):
        """Context manager for performance tracking."""
        metrics = PerformanceMetrics(operation=operation, start_time=time.time())
        
        try:
            yield metrics
            metrics.success = True
        except Exception as e:
            metrics.success = False
            metrics.error_count = 1
            raise
        finally:
            metrics.finish()
            
            # Log performance metrics
            extra = {'performance': metrics.to_dict()}
            self.info(f"Performance: {operation} completed in {metrics.duration_ms:.2f}ms", extra=extra)


class LoggingManager:
    """Central logging manager for application-wide configuration."""
    
    def __init__(self):
        self.loggers: Dict[str, ContextualLogger] = {}
        self.handlers: List[logging.Handler] = []
        self.configured = False
    
    def configure(
        self,
        level: Union[str, int] = logging.INFO,
        format_type: LogFormat = LogFormat.JSON,
        log_file: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_output: bool = True,
        scrub_pii: bool = True,
        correlation_id: Optional[str] = None
    ):
        """Configure application-wide logging."""
        if self.configured:
            return
        
        # Clear existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Set root level
        root_logger.setLevel(level)
        
        # Create formatter
        formatter = StructuredFormatter(format_type, scrub_pii)
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(level)
            root_logger.addHandler(console_handler)
            self.handlers.append(console_handler)
        
        # File handler with rotation
        if log_file:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            root_logger.addHandler(file_handler)
            self.handlers.append(file_handler)
        
        # Error-only file handler
        if log_file:
            error_file = log_file.replace('.log', '_errors.log')
            error_handler = logging.handlers.RotatingFileHandler(
                error_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setFormatter(formatter)
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)
            self.handlers.append(error_handler)
        
        # Add custom log levels
        logging.addLevelName(LogLevel.TRACE.value, 'TRACE')
        logging.addLevelName(LogLevel.AUDIT.value, 'AUDIT')
        
        self.configured = True
    
    def get_logger(
        self, 
        name: str, 
        context: Optional[LogContext] = None
    ) -> ContextualLogger:
        """Get or create a contextual logger."""
        if name not in self.loggers:
            self.loggers[name] = ContextualLogger(name, context)
        return self.loggers[name]
    
    def set_global_context(self, **context_updates):
        """Set global context for all loggers."""
        for logger in self.loggers.values():
            for key, value in context_updates.items():
                if hasattr(logger.context, key):
                    setattr(logger.context, key, value)
                else:
                    logger.context.custom_fields[key] = value
    
    def shutdown(self):
        """Shutdown logging and close all handlers."""
        for handler in self.handlers:
            handler.close()
        logging.shutdown()


# Global logging manager instance
logging_manager = LoggingManager()


# Convenience functions
def get_logger(name: str, context: Optional[LogContext] = None) -> ContextualLogger:
    """Get a contextual logger instance."""
    return logging_manager.get_logger(name, context)


def configure_logging(**kwargs):
    """Configure application-wide logging."""
    logging_manager.configure(**kwargs)


def set_global_context(**context_updates):
    """Set global logging context."""
    logging_manager.set_global_context(**context_updates)


@contextmanager
def log_performance(logger: ContextualLogger, operation: str):
    """Context manager for performance logging."""
    with logger.performance_tracking(operation) as metrics:
        yield metrics


def log_function_call(logger: Optional[ContextualLogger] = None):
    """Decorator to log function calls with performance metrics."""
    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with logger.performance_tracking(func.__name__):
                logger.debug(f"Calling {func.__name__} with args={len(args)}, kwargs={list(kwargs.keys())}")
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"Successfully completed {func.__name__}")
                    return result
                except Exception as e:
                    logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                    raise
        
        return wrapper
    return decorator