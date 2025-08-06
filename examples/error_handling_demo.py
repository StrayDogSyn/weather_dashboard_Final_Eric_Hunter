#!/usr/bin/env python3
"""
Error Handling and Logging Demo

This demo showcases the comprehensive error handling and logging system
implemented for the Weather Dashboard application.
"""

import sys
import os
import time
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.services.exceptions import (
    WeatherAppError, APIError, ConfigurationError, DataValidationError,
    DatabaseError, CacheError, UIError, NetworkError, AuthenticationError,
    RateLimitError, get_user_friendly_message
)
from src.services.logging_config import setup_logging, get_logger
from src.services.error_handler import (
    ErrorHandler, RetryConfig, CircuitBreaker,
    retry_on_exception, async_retry_on_exception,
    safe_execute, handle_api_error, handle_database_error
)


def demo_custom_exceptions():
    """Demonstrate custom exception hierarchy."""
    logger = get_logger(__name__)
    logger.info("=== Custom Exception Hierarchy Demo ===")
    
    exceptions_to_test = [
        APIError("API service unavailable", status_code=503, retry_after=60),
        RateLimitError("Too many requests", retry_after=120),
        ConfigurationError("Missing API key", config_key="openweather_api_key"),
        DataValidationError("Invalid temperature value", field="temperature", value="invalid"),
        DatabaseError("Connection timeout", operation="SELECT", table="weather_data"),
        CacheError("Cache miss", cache_key="weather_london_current"),
        UIError("Widget not found", widget_type="TemperatureChart"),
        NetworkError("Connection refused", endpoint="api.openweathermap.org"),
        AuthenticationError("Invalid credentials", service="OpenWeatherMap")
    ]
    
    for exc in exceptions_to_test:
        logger.info(f"Exception: {type(exc).__name__}")
        logger.info(f"Message: {exc}")
        logger.info(f"User-friendly: {get_user_friendly_message(exc)}")
        logger.info(f"Context: {exc.context}")
        logger.info("-" * 50)


def demo_retry_mechanism():
    """Demonstrate retry mechanism with exponential backoff."""
    logger = get_logger(__name__)
    logger.info("=== Retry Mechanism Demo ===")
    
    attempt_count = 0
    
    @retry_on_exception(
        exceptions=(NetworkError, APIError),
        config=RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True
        )
    )
    def unreliable_api_call():
        nonlocal attempt_count
        attempt_count += 1
        logger.info(f"API call attempt #{attempt_count}")
        
        if attempt_count < 3:
            raise NetworkError("Simulated network failure", endpoint="api.example.com")
        
        return {"status": "success", "data": "weather_data"}
    
    try:
        result = unreliable_api_call()
        logger.info(f"Success after {attempt_count} attempts: {result}")
    except Exception as e:
        logger.error(f"Failed after all retries: {e}")


async def demo_async_retry():
    """Demonstrate async retry mechanism."""
    logger = get_logger(__name__)
    logger.info("=== Async Retry Mechanism Demo ===")
    
    attempt_count = 0
    
    @async_retry_on_exception(
        exceptions=(APIError,),
        config=RetryConfig(
            max_attempts=2,
            base_delay=0.5
        )
    )
    async def async_api_call():
        nonlocal attempt_count
        attempt_count += 1
        logger.info(f"Async API call attempt #{attempt_count}")
        
        await asyncio.sleep(0.1)  # Simulate async operation
        
        if attempt_count < 2:
            raise APIError("Simulated API error", status_code=500)
        
        return {"async_result": "success"}
    
    try:
        result = await async_api_call()
        logger.info(f"Async success: {result}")
    except Exception as e:
        logger.error(f"Async failed: {e}")


def demo_circuit_breaker():
    """Demonstrate circuit breaker pattern."""
    logger = get_logger(__name__)
    logger.info("=== Circuit Breaker Demo ===")
    
    circuit_breaker = CircuitBreaker(
        failure_threshold=3,
        timeout=5.0,
        expected_exception=APIError
    )
    
    @circuit_breaker
    def failing_service():
        raise APIError("Service consistently failing", status_code=500)
    
    # Demonstrate circuit breaker states
    for i in range(6):
        try:
            logger.info(f"Call #{i+1} - Circuit state: {circuit_breaker.state}")
            result = failing_service()
            logger.info(f"Success: {result}")
        except Exception as e:
            logger.warning(f"Failed: {e}")
        
        time.sleep(0.5)
    
    # Wait for recovery timeout
    logger.info("Waiting for circuit breaker recovery...")
    time.sleep(6)
    
    try:
        logger.info(f"Recovery attempt - Circuit state: {circuit_breaker.state}")
        result = failing_service()
    except Exception as e:
        logger.warning(f"Still failing: {e}")


def demo_safe_execute():
    """Demonstrate safe execution wrapper."""
    logger = get_logger(__name__)
    logger.info("=== Safe Execute Demo ===")
    
    def risky_operation(should_fail=False):
        if should_fail:
            raise ValueError("Simulated error")
        return "Operation successful"
    
    # Safe execution with fallback
    result = safe_execute(
        risky_operation, True,  # should_fail=True
        exception_types=(ValueError,),
        default_return="Fallback result",
        log_errors=True
    )
    logger.info(f"Safe execute result: {result}")
    
    # Safe execution without fallback
    result = safe_execute(
        risky_operation, False,  # should_fail=False
        exception_types=(ValueError,),
        log_errors=True
    )
    logger.info(f"Safe execute success: {result}")


def demo_error_handler():
    """Demonstrate centralized error handler."""
    logger = get_logger(__name__)
    logger.info("=== Error Handler Demo ===")
    
    error_handler = ErrorHandler()
    
    # Register custom fallback handlers
    def api_fallback_handler(error: APIError):
        logger.info(f"API fallback triggered for: {error}")
        return {"fallback": True, "cached_data": "stale_weather_data"}
    
    def network_fallback_handler(error: NetworkError):
        logger.info(f"Network fallback triggered for: {error}")
        return {"offline_mode": True}
    
    error_handler.register_fallback(APIError, api_fallback_handler)
    error_handler.register_fallback(NetworkError, network_fallback_handler)
    
    # Test error handling with fallbacks
    def simulate_api_error():
        raise APIError("API temporarily unavailable", status_code=503)
    
    def simulate_network_error():
        raise NetworkError("No internet connection", endpoint="api.weather.com")
    
    # Handle API error
    result = error_handler.handle_error(simulate_api_error)
    logger.info(f"API error handled: {result}")
    
    # Handle network error
    result = error_handler.handle_error(simulate_network_error)
    logger.info(f"Network error handled: {result}")


def demo_decorators():
    """Demonstrate error handling decorators."""
    logger = get_logger(__name__)
    logger.info("=== Error Handling Decorators Demo ===")
    
    @handle_api_error
    def api_operation():
        # Simulate API call that might fail
        import random
        if random.random() < 0.5:
            raise APIError("Random API failure", status_code=500)
        return {"api_data": "success"}
    
    @handle_database_error
    def database_operation():
        # Simulate database operation that might fail
        import random
        if random.random() < 0.3:
            raise DatabaseError("Database connection lost", operation="SELECT")
        return {"db_data": "retrieved"}
    
    # Test decorated functions
    for i in range(3):
        logger.info(f"API operation attempt #{i+1}")
        result = api_operation()
        logger.info(f"API result: {result}")
        
        logger.info(f"Database operation attempt #{i+1}")
        result = database_operation()
        logger.info(f"Database result: {result}")
        
        time.sleep(1)


def demo_logging_levels():
    """Demonstrate different logging levels and structured logging."""
    logger = get_logger(__name__)
    logger.info("=== Logging Levels Demo ===")
    
    # Different log levels
    logger.debug("Debug message - detailed information for troubleshooting")
    logger.info("Info message - general application flow")
    logger.warning("Warning message - something unexpected happened")
    logger.error("Error message - serious problem occurred")
    logger.critical("Critical message - application may not continue")
    
    # Structured logging with context
    logger.info(
        "Weather data fetched",
        extra={
            "location": "London",
            "temperature": 15.5,
            "humidity": 65,
            "response_time_ms": 245
        }
    )
    
    # Exception logging
    try:
        raise ValueError("Example exception for logging")
    except Exception:
        logger.exception("Exception occurred with full traceback")


def main():
    """Run all error handling and logging demos."""
    # Setup logging
    setup_logging(debug_mode=True)
    logger = get_logger(__name__)
    
    logger.info("🚀 Starting Error Handling and Logging Demo")
    logger.info("=" * 60)
    
    try:
        # Run all demos
        demo_custom_exceptions()
        demo_retry_mechanism()
        
        # Run async demo
        asyncio.run(demo_async_retry())
        
        demo_circuit_breaker()
        demo_safe_execute()
        demo_error_handler()
        demo_decorators()
        demo_logging_levels()
        
        logger.info("=" * 60)
        logger.info("✅ All error handling and logging demos completed successfully!")
        
    except Exception as e:
        logger.exception(f"Demo failed with unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)