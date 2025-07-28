#!/usr/bin/env python3
"""
Standardized Error Handling Framework

Provides decorators and utilities for consistent error handling across
the application, including error logging, user notification, and recovery.

Follows Microsoft's recommended patterns for enterprise error handling.
"""

import functools
import traceback
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Dict, Type, Union, List
from contextlib import contextmanager
import logging

from .exceptions import (
    BaseApplicationError,
    ValidationError,
    ServiceError,
    ExternalServiceError,
    DatabaseError,
    ConfigurationError,
    NetworkError,
    TimeoutError,
    ErrorSeverity,
    ErrorCategory
)
from .reliability import CircuitBreaker, RetryHandler, TimeoutManager

logger = logging.getLogger(__name__)


class ErrorContext:
    """Context manager for error handling with automatic logging and recovery."""
    
    def __init__(
        self,
        operation: str,
        *,
        log_errors: bool = True,
        reraise: bool = True,
        fallback_value: Any = None,
        error_callback: Optional[Callable[[Exception], None]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.operation = operation
        self.log_errors = log_errors
        self.reraise = reraise
        self.fallback_value = fallback_value
        self.error_callback = error_callback
        self.context = context or {}
        self.exception: Optional[Exception] = None
        self.start_time: Optional[datetime] = None
    
    def __enter__(self):
        self.start_time = datetime.now(timezone.utc)
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            self.exception = exc_value
            execution_time = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            
            # Convert to application error if needed
            if not isinstance(exc_value, BaseApplicationError):
                exc_value = self._convert_to_application_error(exc_value)
            
            # Add context
            exc_value.context.update({
                'operation': self.operation,
                'execution_time_seconds': execution_time,
                **self.context
            })
            
            if self.log_errors:
                self._log_error(exc_value)
            
            if self.error_callback:
                try:
                    self.error_callback(exc_value)
                except Exception as callback_error:
                    logger.error(f"Error callback failed: {callback_error}")
            
            if not self.reraise:
                return True  # Suppress the exception
        
        return False
    
    def _convert_to_application_error(self, exception: Exception) -> BaseApplicationError:
        """Convert standard exceptions to application errors."""
        if isinstance(exception, (ConnectionError, OSError)):
            return NetworkError(
                f"Network error in {self.operation}: {exception}",
                inner_exception=exception
            )
        elif isinstance(exception, TimeoutError):
            return TimeoutError(
                f"Timeout in {self.operation}: {exception}",
                operation=self.operation,
                inner_exception=exception
            )
        elif isinstance(exception, ValueError):
            return ValidationError(
                f"Validation error in {self.operation}: {exception}",
                inner_exception=exception
            )
        else:
            return ServiceError(
                f"Unexpected error in {self.operation}: {exception}",
                operation=self.operation,
                inner_exception=exception
            )
    
    def _log_error(self, error: BaseApplicationError):
        """Log error with appropriate level based on severity."""
        error_dict = error.to_dict()
        error_dict.pop('message', None)  # Remove 'message' to avoid conflict with LogRecord
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error in {self.operation}: {error.message}", extra=error_dict)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error in {self.operation}: {error.message}", extra=error_dict)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error in {self.operation}: {error.message}", extra=error_dict)
        else:
            logger.info(f"Low severity error in {self.operation}: {error.message}", extra=error_dict)
    
    def get_fallback_value(self):
        """Get fallback value if exception was suppressed."""
        return self.fallback_value


def handle_errors(
    operation: Optional[str] = None,
    *,
    log_errors: bool = True,
    reraise: Optional[bool] = None,
    fallback_value: Any = None,
    error_callback: Optional[Callable[[Exception], None]] = None,
    expected_exceptions: Optional[tuple[Type[Exception], ...]] = None,
    context: Optional[Dict[str, Any]] = None
):
    """Decorator for standardized error handling.
    
    Args:
        operation: Name of the operation for logging
        log_errors: Whether to log errors
        reraise: Whether to reraise exceptions
        fallback_value: Value to return if exception is suppressed
        error_callback: Callback function for error handling
        expected_exceptions: Tuple of expected exception types
        context: Additional context for error logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            
            # Auto-determine reraise behavior: if fallback_value is provided, don't reraise
            should_reraise = reraise if reraise is not None else (fallback_value is None)
            
            with ErrorContext(
                op_name,
                log_errors=log_errors,
                reraise=should_reraise,
                fallback_value=fallback_value,
                error_callback=error_callback,
                context=context or {}
            ) as error_ctx:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if expected_exceptions and isinstance(e, expected_exceptions):
                        # Expected exception, handle normally
                        raise
                    else:
                        # Unexpected exception, let ErrorContext handle it
                        raise
            
            # If we get here, exception was suppressed
            return error_ctx.get_fallback_value()
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_value: Any = None,
    log_errors: bool = True,
    operation: Optional[str] = None,
    **kwargs
) -> Any:
    """Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Arguments for the function
        default_value: Value to return on error
        log_errors: Whether to log errors
        operation: Operation name for logging
        **kwargs: Keyword arguments for the function
    
    Returns:
        Function result or default_value on error
    """
    op_name = operation or getattr(func, '__name__', 'unknown_operation')
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {op_name}: {e}", exc_info=True)
        return default_value


class ErrorAggregator:
    """Aggregates multiple errors for batch processing."""
    
    def __init__(self, operation: str = "batch_operation"):
        self.operation = operation
        self.errors: List[BaseApplicationError] = []
        self.warnings: List[str] = []
    
    def add_error(self, error: Union[Exception, str], **context):
        """Add an error to the aggregator."""
        if isinstance(error, str):
            error = ServiceError(error, operation=self.operation, context=context)
        elif not isinstance(error, BaseApplicationError):
            error = ServiceError(
                f"Error in {self.operation}: {error}",
                operation=self.operation,
                inner_exception=error,
                context=context
            )
        
        self.errors.append(error)
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_errors(self) -> List[BaseApplicationError]:
        """Get all errors."""
        return self.errors.copy()
    
    def get_error_count(self) -> int:
        """Get the total number of errors."""
        return len(self.errors)
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[BaseApplicationError]:
        """Get errors filtered by severity level."""
        return [error for error in self.errors if error.severity == severity]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all errors and warnings."""
        # Count errors by category
        by_category = {}
        for error in self.errors:
            category = error.category.value if hasattr(error.category, 'value') else str(error.category)
            by_category[category] = by_category.get(category, 0) + 1
        
        # Count errors by severity
        by_severity = {}
        for error in self.errors:
            severity = error.severity.value if hasattr(error.severity, 'value') else str(error.severity)
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            'operation': self.operation,
            'total_errors': len(self.errors),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'by_category': by_category,
            'by_severity': by_severity,
            'errors': [error.to_dict() for error in self.errors],
            'warnings': self.warnings,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def raise_if_errors(self):
        """Raise aggregated error if any errors exist."""
        if self.has_errors():
            error_messages = [str(error) for error in self.errors]
            raise ServiceError(
                f"Multiple errors in {self.operation}: {'; '.join(error_messages)}",
                operation=self.operation,
                context=self.get_summary()
            )
    
    def log_all(self):
        """Log all errors and warnings."""
        for error in self.errors:
            logger.error(f"Aggregated error in {self.operation}: {error}")
        
        for warning in self.warnings:
            logger.warning(f"Warning in {self.operation}: {warning}")


class ErrorRecovery:
    """Error recovery strategies for different error types."""
    
    def __init__(self):
        self._recovery_strategies: Dict[Type[Exception], Callable] = {}
    
    def register_strategy(self, exception_type: Type[Exception], strategy: Callable):
        """Register a recovery strategy for an exception type."""
        self._recovery_strategies[exception_type] = strategy
    
    def recover(self, exception: Exception, *args, **kwargs) -> Any:
        """Attempt to recover from an exception."""
        for exc_type, strategy in self._recovery_strategies.items():
            if isinstance(exception, exc_type):
                try:
                    return strategy(exception, *args, **kwargs)
                except Exception as recovery_error:
                    logger.error(f"Recovery strategy failed: {recovery_error}")
                    break
        
        # No recovery strategy found or recovery failed
        raise exception


class ErrorBoundary:
    """Error boundary context object."""
    
    def __init__(self, operation: str, fallback_value=None):
        self.operation = operation
        self.fallback_value = fallback_value
        self.error = None
        self.success = True


@contextmanager
def error_boundary(operation: str, logger_instance=None, fallback_value=None, **kwargs):
    """Context manager that acts as an error boundary.
    
    Catches and handles all exceptions within the boundary,
    preventing them from propagating further.
    """
    boundary = ErrorBoundary(operation, fallback_value)
    
    try:
        yield boundary
    except Exception as e:
        boundary.error = e
        boundary.success = False
        
        # Use provided logger or default
        log_instance = logger_instance or logger
        log_instance.error(f"Error boundary caught exception in {operation}: {e}", exc_info=True)
        
        # Convert to application error if needed
        if not isinstance(e, BaseApplicationError):
            app_error = ServiceError(
                f"Error in {operation}: {e}",
                operation=operation,
                inner_exception=e,
                context=kwargs
            )
        else:
            app_error = e
            app_error.context.update(kwargs)
        
        # Log the structured error (exclude 'message' to avoid LogRecord conflict)
        error_dict = app_error.to_dict()
        error_dict.pop('message', None)  # Remove 'message' to avoid conflict with LogRecord
        log_instance.error(f"Structured error in {operation}: {app_error.message}", extra=error_dict)
        
        # Don't reraise if fallback_value is provided
        if fallback_value is not None:
            return fallback_value
        
        # Don't reraise - this is an error boundary


def create_error_handler(
    circuit_breaker: Optional[CircuitBreaker] = None,
    retry_handler: Optional[RetryHandler] = None,
    timeout_manager: Optional[TimeoutManager] = None,
    operation: Optional[str] = None
):
    """Create a comprehensive error handler with reliability patterns.
    
    Combines circuit breaker, retry logic, timeout management,
    and error handling into a single decorator.
    """
    def decorator(func: Callable) -> Callable:
        # Apply reliability patterns in order
        enhanced_func = func
        
        if timeout_manager:
            enhanced_func = timeout_manager(operation)(enhanced_func)
        
        if retry_handler:
            enhanced_func = retry_handler(enhanced_func)
        
        if circuit_breaker:
            enhanced_func = circuit_breaker(enhanced_func)
        
        # Apply error handling
        enhanced_func = handle_errors(
            operation=operation or func.__name__,
            log_errors=True,
            reraise=True
        )(enhanced_func)
        
        return enhanced_func
    
    return decorator


# Global error recovery instance
global_error_recovery = ErrorRecovery()

# Register common recovery strategies
def _network_recovery_strategy(exception: NetworkError, *args, **kwargs):
    """Recovery strategy for network errors."""
    logger.info("Attempting network error recovery...")
    # Could implement connection reset, DNS refresh, etc.
    return None

def _database_recovery_strategy(exception: DatabaseError, *args, **kwargs):
    """Recovery strategy for database errors."""
    logger.info("Attempting database error recovery...")
    # Could implement connection pool reset, transaction rollback, etc.
    return None

global_error_recovery.register_strategy(NetworkError, _network_recovery_strategy)
global_error_recovery.register_strategy(DatabaseError, _database_recovery_strategy)


# Convenience functions
def log_and_suppress(operation: str):
    """Decorator that logs errors but suppresses them."""
    return handle_errors(operation, reraise=False, log_errors=True)


def fail_fast(operation: str):
    """Decorator that logs errors and fails fast."""
    return handle_errors(operation, reraise=True, log_errors=True)


def with_fallback_value(operation: str, fallback_value: Any):
    """Decorator that returns a fallback value on error."""
    return handle_errors(
        operation, 
        reraise=False, 
        log_errors=True, 
        fallback_value=fallback_value
    )