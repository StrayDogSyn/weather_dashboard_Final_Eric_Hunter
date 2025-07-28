#!/usr/bin/env python3
"""
Reliability Patterns for Production-Ready Applications

Implements enterprise-grade reliability patterns including:
- Circuit Breaker: Prevents cascading failures
- Retry with Exponential Backoff: Handles transient failures
- Timeout Management: Prevents hanging operations
- Health Checks: Monitors service health
- Graceful Degradation: Fallback mechanisms

Follows Microsoft's recommended patterns for resilient cloud applications.
"""

import asyncio
import functools
import time
import random
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional, Dict, List, Union, TypeVar, Generic
from dataclasses import dataclass, field
from threading import Lock, RLock
import logging

from .exceptions import (
    BaseApplicationError, 
    ExternalServiceError, 
    TimeoutError, 
    NetworkError,
    ErrorSeverity
)

T = TypeVar('T')
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting calls
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes to close from half-open
    timeout: float = 30.0               # Operation timeout in seconds
    expected_exceptions: tuple = (ExternalServiceError, NetworkError, TimeoutError)


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    total_requests: int = 0
    failed_requests: int = 0
    successful_requests: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    @property
    def success_rate(self) -> float:
        """Calculate current success rate."""
        return 1.0 - self.failure_rate


class CircuitBreaker:
    """Circuit breaker implementation for preventing cascading failures.
    
    Monitors operation failures and opens the circuit when failure threshold
    is exceeded, preventing further calls until the service recovers.
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._lock = RLock()
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to wrap functions with circuit breaker."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return self._execute(func, *args, **kwargs)
        return wrapper
    
    def _execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        with self._lock:
            self._check_state()
            
            if self.state == CircuitState.OPEN:
                raise ExternalServiceError(
                    f"Circuit breaker '{self.name}' is OPEN",
                    service_name=self.name,
                    user_message="Service is temporarily unavailable due to repeated failures.",
                    retry_after=self.config.recovery_timeout
                )
            
            self.metrics.total_requests += 1
            
        try:
            # Execute with timeout
            start_time = time.time()
            if asyncio.iscoroutinefunction(func):
                result = asyncio.wait_for(
                    func(*args, **kwargs), 
                    timeout=self.config.timeout
                )
            else:
                result = func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            self._on_success(execution_time)
            return result
            
        except self.config.expected_exceptions as e:
            self._on_failure(e)
            raise
        except Exception as e:
            # Unexpected exceptions don't count as circuit breaker failures
            logger.warning(f"Unexpected exception in circuit breaker '{self.name}': {e}")
            raise
    
    def _check_state(self):
        """Check and update circuit breaker state."""
        now = datetime.utcnow()
        
        if self.state == CircuitState.OPEN:
            if (self._last_failure_time and 
                now - self._last_failure_time >= timedelta(seconds=self.config.recovery_timeout)):
                self._transition_to_half_open()
    
    def _on_success(self, execution_time: float):
        """Handle successful operation."""
        with self._lock:
            self.metrics.successful_requests += 1
            self.metrics.last_success_time = datetime.utcnow()
            
            if self.state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
    
    def _on_failure(self, exception: Exception):
        """Handle failed operation."""
        with self._lock:
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = datetime.utcnow()
            self._last_failure_time = self.metrics.last_failure_time
            
            if self.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN]:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition circuit breaker to OPEN state."""
        self.state = CircuitState.OPEN
        self._log_state_change("OPEN", "Failure threshold exceeded")
    
    def _transition_to_half_open(self):
        """Transition circuit breaker to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self._success_count = 0
        self._log_state_change("HALF_OPEN", "Recovery timeout elapsed")
    
    def _transition_to_closed(self):
        """Transition circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._log_state_change("CLOSED", "Success threshold reached")
    
    def _log_state_change(self, new_state: str, reason: str):
        """Log state change for monitoring."""
        change_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "from_state": self.state.value if hasattr(self.state, 'value') else str(self.state),
            "to_state": new_state,
            "reason": reason,
            "failure_count": self._failure_count,
            "success_count": self._success_count
        }
        self.metrics.state_changes.append(change_info)
        logger.info(f"Circuit breaker '{self.name}' state changed: {change_info}")
    
    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._log_state_change("CLOSED", "Manual reset")
    
    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get current circuit breaker metrics."""
        return self.metrics


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0         # Base delay in seconds
    max_delay: float = 60.0         # Maximum delay in seconds
    exponential_base: float = 2.0   # Exponential backoff base
    jitter: bool = True             # Add random jitter
    retryable_exceptions: tuple = (ExternalServiceError, NetworkError, TimeoutError)


class RetryHandler:
    """Retry handler with exponential backoff and jitter.
    
    Implements intelligent retry logic for transient failures with
    exponential backoff and optional jitter to prevent thundering herd.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to add retry logic to functions."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return self._execute_with_retry(func, *args, **kwargs)
        return wrapper
    
    def _execute_with_retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Function {func.__name__} succeeded on attempt {attempt + 1}")
                return result
                
            except self.config.retryable_exceptions as e:
                last_exception = e
                
                if attempt == self.config.max_attempts - 1:
                    # Last attempt failed
                    logger.error(
                        f"Function {func.__name__} failed after {self.config.max_attempts} attempts: {e}"
                    )
                    raise
                
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Function {func.__name__} failed on attempt {attempt + 1}, "
                    f"retrying in {delay:.2f}s: {e}"
                )
                time.sleep(delay)
            
            except Exception as e:
                # Non-retryable exception
                logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                raise
        
        # Should never reach here, but just in case
        raise last_exception or Exception("Retry logic failed unexpectedly")
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff with jitter."""
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        if self.config.jitter:
            # Add ±25% jitter
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


class TimeoutManager:
    """Timeout management for operations.
    
    Provides consistent timeout handling across the application with
    configurable timeouts per operation type.
    """
    
    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout
        self._operation_timeouts: Dict[str, float] = {}
    
    def set_timeout(self, operation: str, timeout: float):
        """Set timeout for specific operation."""
        self._operation_timeouts[operation] = timeout
    
    def get_timeout(self, operation: Optional[str] = None) -> float:
        """Get timeout for operation."""
        if operation and operation in self._operation_timeouts:
            return self._operation_timeouts[operation]
        return self.default_timeout
    
    def __call__(self, operation: Optional[str] = None, timeout: Optional[float] = None):
        """Decorator to add timeout to functions."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> T:
                actual_timeout = timeout or self.get_timeout(operation)
                return self._execute_with_timeout(func, actual_timeout, *args, **kwargs)
            return wrapper
        return decorator
    
    def _execute_with_timeout(self, func: Callable[..., T], timeout: float, *args, **kwargs) -> T:
        """Execute function with timeout."""
        if asyncio.iscoroutinefunction(func):
            return asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        else:
            # For synchronous functions, we'll use a simple approach
            # In production, consider using threading or multiprocessing for true timeouts
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                if execution_time > timeout:
                    logger.warning(
                        f"Function {func.__name__} took {execution_time:.2f}s, "
                        f"exceeding timeout of {timeout}s"
                    )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                if execution_time > timeout:
                    raise TimeoutError(
                        f"Operation '{func.__name__}' timed out after {execution_time:.2f}s",
                        operation=func.__name__,
                        timeout_seconds=timeout
                    )
                raise


class HealthCheck:
    """Health check implementation for service monitoring.
    
    Provides standardized health checking with dependency validation
    and detailed health status reporting.
    """
    
    def __init__(self, name: str):
        self.name = name
        self._checks: Dict[str, Callable[[], bool]] = {}
        self._last_check_time: Optional[datetime] = None
        self._last_status: Optional[Dict[str, Any]] = None
    
    def add_check(self, name: str, check_func: Callable[[], bool]):
        """Add a health check function."""
        self._checks[name] = check_func
    
    def check_health(self) -> Dict[str, Any]:
        """Perform all health checks and return status."""
        self._last_check_time = datetime.utcnow()
        status = {
            "service": self.name,
            "timestamp": self._last_check_time.isoformat(),
            "healthy": True,
            "checks": {},
            "errors": []
        }
        
        for check_name, check_func in self._checks.items():
            try:
                result = check_func()
                status["checks"][check_name] = {
                    "healthy": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                if not result:
                    status["healthy"] = False
                    status["errors"].append(f"Health check '{check_name}' failed")
            except Exception as e:
                status["checks"][check_name] = {
                    "healthy": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                status["healthy"] = False
                status["errors"].append(f"Health check '{check_name}' threw exception: {e}")
        
        self._last_status = status
        return status
    
    def is_healthy(self) -> bool:
        """Quick health check returning boolean."""
        status = self.check_health()
        return status["healthy"]
    
    def get_last_status(self) -> Optional[Dict[str, Any]]:
        """Get last health check status."""
        return self._last_status


class GracefulDegradation:
    """Graceful degradation handler for fallback mechanisms.
    
    Provides fallback functionality when primary services fail,
    ensuring the application continues to function with reduced capability.
    """
    
    def __init__(self, name: str):
        self.name = name
        self._fallbacks: List[Callable] = []
    
    def add_fallback(self, fallback_func: Callable[..., T]):
        """Add a fallback function."""
        self._fallbacks.append(fallback_func)
    
    def __call__(self, primary_func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to add graceful degradation to functions."""
        @functools.wraps(primary_func)
        def wrapper(*args, **kwargs) -> T:
            return self._execute_with_fallback(primary_func, *args, **kwargs)
        return wrapper
    
    def _execute_with_fallback(self, primary_func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with fallback logic."""
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary function {primary_func.__name__} failed: {e}")
            
            for i, fallback in enumerate(self._fallbacks):
                try:
                    logger.info(f"Trying fallback {i + 1} for {primary_func.__name__}")
                    result = fallback(*args, **kwargs)
                    logger.info(f"Fallback {i + 1} succeeded for {primary_func.__name__}")
                    return result
                except Exception as fallback_error:
                    logger.warning(
                        f"Fallback {i + 1} failed for {primary_func.__name__}: {fallback_error}"
                    )
                    continue
            
            # All fallbacks failed
            logger.error(f"All fallbacks failed for {primary_func.__name__}")
            raise e


# Global instances for common use
default_timeout_manager = TimeoutManager()
default_retry_handler = RetryHandler()


# Convenience decorators
def with_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator to add circuit breaker protection."""
    return CircuitBreaker(name, config)


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator to add retry logic."""
    return RetryHandler(config)


def with_timeout(timeout: float):
    """Decorator to add timeout protection."""
    return default_timeout_manager(timeout=timeout)


def with_fallback(name: str, *fallback_funcs):
    """Decorator to add graceful degradation."""
    degradation = GracefulDegradation(name)
    for fallback in fallback_funcs:
        degradation.add_fallback(fallback)
    return degradation