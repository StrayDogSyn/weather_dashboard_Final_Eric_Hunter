"""Error handling utilities for the Weather Dashboard application.

This module provides retry logic, fallback behavior, and user-friendly
error handling patterns with exponential backoff and circuit breaker patterns.
"""

import asyncio
import functools
import random
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union, Tuple
from datetime import datetime, timedelta
import logging

from .exceptions import (
    WeatherAppError, APIError, RateLimitError, NetworkError,
    get_user_friendly_message
)
from .logging_config import get_logger, log_exception


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, exponential_base: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            delay *= (0.5 + random.random() * 0.5)
        
        return delay


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.logger = get_logger(__name__)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker pattern."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self._call(func, *args, **kwargs)
        return wrapper
    
    def _call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker logic."""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
                self.logger.info(f"Circuit breaker half-open for {func.__name__}")
            else:
                raise APIError(f"Circuit breaker is OPEN for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure(func.__name__)
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.last_failure_time is None:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout)
    
    def _on_success(self) -> None:
        """Handle successful execution."""
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
            self.logger.info("Circuit breaker reset to CLOSED")
        self.failure_count = 0
    
    def _on_failure(self, func_name: str) -> None:
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            self.logger.warning(
                f"Circuit breaker OPEN for {func_name} after {self.failure_count} failures"
            )


class ErrorHandler:
    """Centralized error handling with retry logic and fallbacks."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.fallback_handlers: Dict[Type[Exception], Callable] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def register_fallback(self, exception_type: Type[Exception], 
                         handler: Callable) -> None:
        """Register a fallback handler for specific exception type."""
        self.fallback_handlers[exception_type] = handler
    
    def get_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create a circuit breaker for a named operation."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(**kwargs)
        return self.circuit_breakers[name]
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                    show_user_message: bool = True) -> Tuple[str, bool]:
        """Handle an error and return user message and recovery status.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            show_user_message: Whether to return user-friendly message
            
        Returns:
            Tuple of (user_message, can_retry)
        """
        # Log the error with context
        log_exception(self.logger, error, context)
        
        # Check for fallback handlers
        for exception_type, handler in self.fallback_handlers.items():
            if isinstance(error, exception_type):
                try:
                    handler(error, context)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback handler failed: {fallback_error}")
        
        # Determine if retry is possible
        can_retry = self._can_retry(error)
        
        # Get user-friendly message
        if show_user_message:
            user_message = get_user_friendly_message(error)
        else:
            user_message = str(error)
        
        return user_message, can_retry
    
    def _can_retry(self, error: Exception) -> bool:
        """Determine if an error is retryable."""
        # Network errors are usually retryable
        if isinstance(error, NetworkError):
            return True
        
        # API errors depend on the status code
        if isinstance(error, APIError):
            if hasattr(error, 'status_code'):
                # Retry on server errors and rate limits
                return error.status_code in [429, 500, 502, 503, 504]
            return True
        
        # Rate limit errors are retryable after delay
        if isinstance(error, RateLimitError):
            return True
        
        # Other errors are generally not retryable
        return False


def retry_on_exception(exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
                      config: Optional[RetryConfig] = None,
                      fallback: Optional[Callable] = None) -> Callable:
    """Decorator to retry function on specific exceptions.
    
    Args:
        exceptions: Exception types to retry on
        config: Retry configuration
        fallback: Fallback function to call if all retries fail
        
    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()
    
    logger = get_logger(__name__)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_attempts} attempts"
                        )
                        break
                    
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
            
            # All retries failed
            if fallback:
                try:
                    logger.info(f"Calling fallback for {func.__name__}")
                    return fallback(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback failed for {func.__name__}: {fallback_error}")
            
            # Re-raise the last exception
            raise last_exception
        
        return wrapper
    return decorator


def async_retry_on_exception(exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
                            config: Optional[RetryConfig] = None,
                            fallback: Optional[Callable] = None) -> Callable:
    """Async version of retry decorator."""
    if config is None:
        config = RetryConfig()
    
    logger = get_logger(__name__)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        logger.error(
                            f"Async function {func.__name__} failed after {config.max_attempts} attempts"
                        )
                        break
                    
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"Async attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
            
            # All retries failed
            if fallback:
                try:
                    logger.info(f"Calling async fallback for {func.__name__}")
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    else:
                        return fallback(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Async fallback failed for {func.__name__}: {fallback_error}")
            
            # Re-raise the last exception
            raise last_exception
        
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default_return: Any = None,
                exception_types: Tuple[Type[Exception], ...] = (Exception,),
                log_errors: bool = True, **kwargs) -> Any:
    """Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        default_return: Value to return on error
        exception_types: Exception types to catch
        log_errors: Whether to log errors
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or default_return on error
    """
    logger = get_logger(__name__)
    
    try:
        return func(*args, **kwargs)
    except exception_types as e:
        if log_errors:
            log_exception(logger, e, {
                "function": func.__name__,
                "args": str(args)[:100],  # Limit arg string length
                "kwargs": str(kwargs)[:100]
            })
        return default_return


# Global error handler instance
error_handler = ErrorHandler()


# Convenience functions
def handle_api_error(func: Callable) -> Callable:
    """Decorator for handling API errors with retry and circuit breaker."""
    circuit_breaker = error_handler.get_circuit_breaker(
        f"api_{func.__name__}",
        failure_threshold=3,
        timeout=30.0,
        expected_exception=APIError
    )
    
    @circuit_breaker
    @retry_on_exception(
        exceptions=(APIError, NetworkError),
        config=RetryConfig(max_attempts=3, base_delay=1.0)
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    return wrapper


def handle_database_error(func: Callable) -> Callable:
    """Decorator for handling database errors."""
    @retry_on_exception(
        exceptions=(Exception,),  # Catch database-specific exceptions
        config=RetryConfig(max_attempts=2, base_delay=0.5)
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    return wrapper