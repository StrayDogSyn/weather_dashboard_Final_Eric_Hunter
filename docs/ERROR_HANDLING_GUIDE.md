# Error Handling & Reliability Patterns Guide

## Overview

This guide documents the comprehensive error handling and reliability patterns implemented in the Weather Dashboard application. The framework provides production-ready error management, logging, and resilience patterns following Microsoft's recommended practices for conversational AI and cloud applications.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Exception Hierarchy](#exception-hierarchy)
3. [Reliability Patterns](#reliability-patterns)
4. [Error Handling Framework](#error-handling-framework)
5. [Logging Infrastructure](#logging-infrastructure)
6. [Implementation Examples](#implementation-examples)
7. [Testing Strategy](#testing-strategy)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Architecture Overview

The error handling framework consists of four core components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Error Handling Framework (decorators, boundaries, utils)  │
├─────────────────────────────────────────────────────────────┤
│     Reliability Patterns (circuit breaker, retry, etc.)    │
├─────────────────────────────────────────────────────────────┤
│        Exception Hierarchy (custom exception types)        │
├─────────────────────────────────────────────────────────────┤
│         Logging Infrastructure (structured logging)        │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

- **Structured Exception Hierarchy**: Custom exceptions with rich context
- **Reliability Patterns**: Circuit breaker, retry, timeout management
- **Comprehensive Logging**: Structured logging with correlation IDs
- **Error Recovery**: Graceful degradation and fallback mechanisms
- **Production Ready**: Performance monitoring and health checks

## Exception Hierarchy

### Base Exception Class

```python
from core.exceptions import BaseApplicationError, ErrorSeverity, ErrorCategory

# Create a custom exception with full context
error = BaseApplicationError(
    message="Service temporarily unavailable",
    correlation_id="req-123-456",
    severity=ErrorSeverity.HIGH,
    category=ErrorCategory.EXTERNAL_SERVICE,
    context={"service": "weather-api", "endpoint": "/current"},
    user_message="Weather data is temporarily unavailable. Please try again later."
)
```

### Specialized Exception Types

| Exception Type | Use Case | Category |
|----------------|----------|----------|
| `ValidationError` | Input validation failures | VALIDATION |
| `ServiceError` | Internal service errors | BUSINESS_LOGIC |
| `ExternalServiceError` | Third-party API failures | EXTERNAL_SERVICE |
| `NetworkError` | Network connectivity issues | INFRASTRUCTURE |
| `TimeoutError` | Operation timeout | INFRASTRUCTURE |
| `DatabaseError` | Database operation failures | DATA_ACCESS |
| `ConfigurationError` | Configuration issues | CONFIGURATION |
| `AuthenticationError` | Authentication failures | SECURITY |
| `AuthorizationError` | Authorization failures | SECURITY |
| `RateLimitError` | Rate limiting violations | EXTERNAL_SERVICE |

### Error Severity Levels

- **CRITICAL**: System-wide failures requiring immediate attention
- **HIGH**: Service degradation affecting user experience
- **MEDIUM**: Recoverable errors with potential impact
- **LOW**: Minor issues with minimal impact
- **INFO**: Informational errors for monitoring

## Reliability Patterns

### Circuit Breaker Pattern

Prevents cascading failures by monitoring service health:

```python
from core.reliability import CircuitBreaker

# Initialize circuit breaker
circuit_breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=30.0,    # Try recovery after 30 seconds
    expected_exception=ExternalServiceError
)

# Use circuit breaker
try:
    result = circuit_breaker.call(external_api_call)
except ServiceError as e:
    # Circuit is open, service is unavailable
    handle_service_unavailable(e)
```

**States:**
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Service is failing, requests are blocked
- **HALF_OPEN**: Testing if service has recovered

### Retry with Exponential Backoff

Automatically retries failed operations with increasing delays:

```python
from core.reliability import RetryWithBackoff

# Configure retry policy
retry = RetryWithBackoff(
    max_attempts=3,           # Maximum 3 attempts
    base_delay=1.0,          # Start with 1 second delay
    max_delay=30.0,          # Maximum 30 second delay
    backoff_multiplier=2.0,  # Double delay each time
    jitter=True              # Add randomization
)

# Execute with retry
result = retry.execute(lambda: call_external_service())
```

**Backoff Progression:**
- Attempt 1: Immediate
- Attempt 2: 1.0s delay (+ jitter)
- Attempt 3: 2.0s delay (+ jitter)
- Attempt 4: 4.0s delay (+ jitter)

### Timeout Management

Prevents operations from hanging indefinitely:

```python
from core.reliability import TimeoutManager

# Initialize timeout manager
timeout_manager = TimeoutManager(default_timeout=30.0)

# Execute with timeout
try:
    result = timeout_manager.execute(
        operation=long_running_task,
        timeout=10.0  # Override default timeout
    )
except TimeoutError as e:
    # Handle timeout
    logger.warning(f"Operation timed out: {e}")
```

### Health Checks

Monitor service health and dependencies:

```python
from core.reliability import HealthCheck

# Define health check
health_check = HealthCheck(
    name="weather-service",
    check_function=lambda: weather_service.test_connection(),
    timeout=5.0,
    interval=60.0  # Check every minute
)

# Get health status
status = health_check.get_status()
if not status.is_healthy:
    logger.error(f"Health check failed: {status.error}")
```

### Graceful Degradation

Provide fallback functionality when services are unavailable:

```python
from core.reliability import GracefulDegradation

# Configure degradation strategy
degradation = GracefulDegradation()

# Register fallback for weather service
degradation.register_fallback(
    service="weather",
    fallback=lambda location: get_cached_weather(location),
    condition=lambda: not weather_service.is_available()
)

# Use with automatic fallback
weather_data = degradation.execute(
    service="weather",
    primary=lambda: weather_service.get_current_weather(location),
    location=location
)
```

## Error Handling Framework

### Error Handling Decorator

Simplify error handling with decorators:

```python
from core.error_handling import handle_errors

@handle_errors(
    operation="get_weather_data",
    fallback_value=None,
    log_errors=True
)
def get_weather_data(location: str):
    return weather_service.get_current_weather(location)

# Usage
weather = get_weather_data("Seattle")
if weather is None:
    # Handle fallback case
    display_error_message("Weather data unavailable")
```

### Error Boundary Context Manager

Provide structured error handling for code blocks:

```python
from core.error_handling import error_boundary

with error_boundary(
    operation="weather_dashboard_load",
    logger=logger,
    fallback_value={"status": "degraded"}
) as boundary:
    # Load weather data
    current_weather = weather_service.get_current_weather(location)
    forecast = weather_service.get_forecast(location, days=5)
    
    # Process data
    dashboard_data = process_weather_data(current_weather, forecast)

# Check results
if boundary.success:
    render_dashboard(dashboard_data)
else:
    render_error_page(boundary.error)
```

### Safe Execution Utility

Combine multiple reliability patterns:

```python
from core.error_handling import safe_execute

# Execute with combined patterns
result = safe_execute(
    operation=lambda: weather_service.get_current_weather(location),
    circuit_breaker=circuit_breaker,
    retry=retry_policy,
    timeout_manager=timeout_manager,
    operation_name="get_current_weather",
    context={"location": location}
)
```

### Error Aggregation

Collect and analyze multiple errors:

```python
from core.error_handling import ErrorAggregator

# Collect errors from batch operations
aggregator = ErrorAggregator()

for location in locations:
    try:
        weather_data = get_weather_data(location)
        process_weather_data(weather_data)
    except Exception as e:
        aggregator.add_error(e)

# Analyze collected errors
if aggregator.has_errors():
    summary = aggregator.get_summary()
    logger.error(f"Batch processing completed with {summary['total_errors']} errors")
    
    # Get high-severity errors for immediate attention
    critical_errors = aggregator.get_errors_by_severity(ErrorSeverity.HIGH)
    for error in critical_errors:
        send_alert(error)
```

## Logging Infrastructure

### Structured Logging

Consistent, searchable log format:

```python
from core.logging_framework import StructuredLogger

# Initialize logger
logger = StructuredLogger(
    name="weather-service",
    service_name="weather-dashboard",
    service_version="2.0.0"
)

# Log with structured data
logger.info(
    "Weather data retrieved successfully",
    extra={
        "location": "Seattle",
        "temperature": 22.5,
        "response_time_ms": 150,
        "cache_hit": True
    }
)

# Log errors with context
logger.error(
    "Failed to retrieve weather data",
    extra={
        "location": "Seattle",
        "error_code": "WEATHER_API_TIMEOUT",
        "retry_count": 3,
        "last_attempt_time": "2024-01-15T10:30:00Z"
    },
    exc_info=True  # Include stack trace
)
```

### Correlation IDs

Track requests across service boundaries:

```python
# Correlation ID is automatically generated
correlation_id = logger.correlation_id

# Pass to downstream services
headers = {"X-Correlation-ID": correlation_id}
response = requests.get(api_url, headers=headers)

# All logs will include the correlation ID
logger.info("API call completed", extra={"status_code": response.status_code})
```

### Performance Monitoring

Track operation performance:

```python
# Automatic performance tracking
with logger.performance_context("weather_api_call"):
    weather_data = weather_api.get_current_weather(location)

# Manual performance logging
start_time = time.time()
weather_data = weather_api.get_current_weather(location)
end_time = time.time()

logger.info(
    "Weather API call completed",
    extra={
        "operation": "get_current_weather",
        "duration_ms": (end_time - start_time) * 1000,
        "location": location
    }
)
```

## Implementation Examples

### Weather Service Integration

Complete example of integrating error handling into a service:

```python
from core.exceptions import ExternalServiceError, ValidationError
from core.error_handling import handle_errors, safe_execute
from core.reliability import CircuitBreaker, RetryWithBackoff, TimeoutManager
from core.logging_framework import StructuredLogger

class WeatherServiceImpl:
    def __init__(self):
        self._logger = StructuredLogger(
            name="weather-service",
            service_name="weather-dashboard",
            service_version="2.0.0"
        )
        
        # Initialize reliability patterns
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30.0,
            expected_exception=ExternalServiceError
        )
        
        self._retry = RetryWithBackoff(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0
        )
        
        self._timeout_manager = TimeoutManager(default_timeout=30.0)
    
    @handle_errors(operation="get_current_weather")
    def get_current_weather(self, location: str):
        # Input validation
        if not location or not location.strip():
            raise ValidationError(
                message="Location parameter is required",
                field="location",
                value=location,
                constraint="Must be non-empty string",
                user_message="Please provide a valid location."
            )
        
        # Execute with reliability patterns
        return safe_execute(
            operation=lambda: self._fetch_weather_data(location),
            circuit_breaker=self._circuit_breaker,
            retry=self._retry,
            timeout_manager=self._timeout_manager,
            operation_name="fetch_weather_data",
            context={"location": location}
        )
    
    def _fetch_weather_data(self, location: str):
        try:
            # Simulate API call
            response = weather_api.get_current_weather(location)
            
            self._logger.info(
                "Weather data retrieved successfully",
                extra={
                    "location": location,
                    "temperature": response.temperature,
                    "response_time_ms": response.response_time
                }
            )
            
            return response
            
        except requests.exceptions.Timeout as e:
            raise TimeoutError(
                message=f"Weather API timeout for location: {location}",
                operation="fetch_weather_data",
                timeout_duration=30.0,
                context={"location": location},
                user_message="Weather service is taking longer than expected. Please try again."
            ) from e
            
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(
                message=f"Network error accessing weather API: {e}",
                operation="fetch_weather_data",
                context={"location": location},
                user_message="Unable to connect to weather service. Please check your internet connection."
            ) from e
            
        except Exception as e:
            raise ExternalServiceError(
                message=f"Weather API error: {e}",
                service_name="weather-api",
                endpoint="/current",
                context={"location": location},
                user_message="Weather service is temporarily unavailable. Please try again later."
            ) from e
```

### Bot Framework Integration

Integrating error handling into a Bot Framework application:

```python
from botbuilder.core import ActivityHandler, TurnContext
from core.error_handling import handle_errors, error_boundary
from core.logging_framework import StructuredLogger

class WeatherBot(ActivityHandler):
    def __init__(self, weather_service):
        self._weather_service = weather_service
        self._logger = StructuredLogger(
            name="weather-bot",
            service_name="weather-bot",
            service_version="2.0.0"
        )
    
    @handle_errors(operation="on_message_activity")
    async def on_message_activity(self, turn_context: TurnContext):
        user_message = turn_context.activity.text
        
        with error_boundary(
            operation="process_weather_request",
            logger=self._logger,
            fallback_value="I'm sorry, I'm having trouble accessing weather information right now."
        ) as boundary:
            # Extract location from user message
            location = self._extract_location(user_message)
            
            if not location:
                response = "Please specify a location for weather information."
            else:
                # Get weather data
                weather_data = self._weather_service.get_current_weather(location)
                response = self._format_weather_response(weather_data)
        
        # Send response (either success or fallback)
        if boundary.success:
            await turn_context.send_activity(response)
        else:
            # Log the error and send fallback message
            self._logger.error(
                "Failed to process weather request",
                extra={
                    "user_message": user_message,
                    "error": str(boundary.error)
                }
            )
            await turn_context.send_activity(boundary.fallback_value)
```

## Testing Strategy

### Unit Tests

Test individual components:

```python
import unittest
from unittest.mock import Mock, patch
from core.exceptions import ExternalServiceError
from core.reliability import CircuitBreaker

class TestCircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1.0
        )
    
    def test_circuit_breaker_opens_after_failures(self):
        def failing_function():
            raise Exception("Test failure")
        
        # First two failures should keep circuit closed
        for _ in range(2):
            with self.assertRaises(Exception):
                self.circuit_breaker.call(failing_function)
            self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.CLOSED)
        
        # Third failure should open the circuit
        with self.assertRaises(Exception):
            self.circuit_breaker.call(failing_function)
        self.assertEqual(self.circuit_breaker.state, CircuitBreakerState.OPEN)
```

### Integration Tests

Test complete error handling flows:

```python
class TestWeatherServiceErrorHandling(unittest.TestCase):
    def setUp(self):
        self.weather_service = MockWeatherService()
    
    def test_end_to_end_error_recovery(self):
        # Enable failure simulation
        self.weather_service.set_should_fail(True)
        
        with error_boundary("test_operation", logger, fallback_value=None) as boundary:
            result = self.weather_service.get_current_weather("Seattle")
        
        # Should handle error gracefully
        self.assertIsNone(result)  # Fallback value
        self.assertFalse(boundary.success)
        self.assertIsInstance(boundary.error, ExternalServiceError)
```

### Load Testing

Test reliability patterns under load:

```python
import asyncio
import concurrent.futures

async def load_test_circuit_breaker():
    """Test circuit breaker behavior under concurrent load."""
    circuit_breaker = CircuitBreaker(failure_threshold=10)
    
    async def make_request():
        try:
            return circuit_breaker.call(lambda: weather_api.get_weather("Seattle"))
        except Exception as e:
            return f"Error: {e}"
    
    # Simulate 100 concurrent requests
    tasks = [make_request() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    
    # Analyze results
    successes = sum(1 for r in results if not str(r).startswith("Error"))
    failures = len(results) - successes
    
    print(f"Load test results: {successes} successes, {failures} failures")
```

## Best Practices

### Error Handling Guidelines

1. **Use Specific Exception Types**
   ```python
   # Good
   raise ValidationError("Invalid email format", field="email")
   
   # Avoid
   raise Exception("Something went wrong")
   ```

2. **Provide User-Friendly Messages**
   ```python
   raise ExternalServiceError(
       message="Weather API returned 503",
       user_message="Weather service is temporarily unavailable. Please try again in a few minutes."
   )
   ```

3. **Include Rich Context**
   ```python
   raise NetworkError(
       message="Connection timeout",
       context={
           "endpoint": "https://api.weather.com/v1/current",
           "timeout": 30.0,
           "retry_count": 3
       }
   )
   ```

4. **Log Before Raising**
   ```python
   logger.error(
       "External service call failed",
       extra={"service": "weather-api", "error": str(e)}
   )
   raise ExternalServiceError("Weather API unavailable") from e
   ```

### Reliability Pattern Guidelines

1. **Configure Circuit Breakers Appropriately**
   - Use lower thresholds for critical services (3-5 failures)
   - Use higher thresholds for non-critical services (10-20 failures)
   - Set recovery timeouts based on service SLA

2. **Implement Exponential Backoff**
   - Start with short delays (1-2 seconds)
   - Cap maximum delay (30-60 seconds)
   - Add jitter to prevent thundering herd

3. **Set Reasonable Timeouts**
   - API calls: 10-30 seconds
   - Database queries: 5-15 seconds
   - Health checks: 3-5 seconds

4. **Design Graceful Degradation**
   - Identify core vs. optional functionality
   - Implement meaningful fallbacks
   - Communicate degraded state to users

### Logging Best Practices

1. **Use Structured Logging**
   ```python
   # Good
   logger.info("User login successful", extra={
       "user_id": user.id,
       "login_method": "oauth",
       "duration_ms": 150
   })
   
   # Avoid
   logger.info(f"User {user.id} logged in via oauth in 150ms")
   ```

2. **Include Correlation IDs**
   ```python
   # Automatically included in structured logger
   logger.info("Processing request", extra={"operation": "get_weather"})
   ```

3. **Log at Appropriate Levels**
   - **ERROR**: Failures requiring attention
   - **WARNING**: Recoverable issues
   - **INFO**: Important business events
   - **DEBUG**: Detailed diagnostic information

4. **Avoid Logging Sensitive Data**
   ```python
   # Good
   logger.info("User authenticated", extra={"user_id": user.id})
   
   # Avoid
   logger.info("User authenticated", extra={"password": user.password})
   ```

## Troubleshooting

### Common Issues

1. **Circuit Breaker Not Opening**
   - Check failure threshold configuration
   - Verify exception types are being caught
   - Review failure counting logic

2. **Retry Exhaustion**
   - Increase max attempts if appropriate
   - Check if underlying issue is transient
   - Review backoff timing

3. **Timeout Issues**
   - Verify timeout values are reasonable
   - Check for network latency issues
   - Consider async operation patterns

4. **Missing Correlation IDs**
   - Ensure structured logger is used consistently
   - Verify correlation ID propagation
   - Check middleware configuration

### Debugging Tools

1. **Error Analysis Dashboard**
   ```python
   # Get error summary for analysis
   aggregator = ErrorAggregator()
   summary = aggregator.get_summary()
   
   print(f"Total errors: {summary['total_errors']}")
   print(f"By category: {summary['by_category']}")
   print(f"By severity: {summary['by_severity']}")
   ```

2. **Health Check Monitoring**
   ```python
   # Monitor service health
   health_status = health_check.get_status()
   if not health_status.is_healthy:
       print(f"Service unhealthy: {health_status.error}")
       print(f"Last check: {health_status.last_check}")
   ```

3. **Circuit Breaker Status**
   ```python
   # Check circuit breaker state
   print(f"Circuit state: {circuit_breaker.state}")
   print(f"Failure count: {circuit_breaker.failure_count}")
   print(f"Last failure: {circuit_breaker.last_failure_time}")
   ```

### Performance Monitoring

1. **Response Time Tracking**
   ```python
   with logger.performance_context("weather_api_call") as perf:
       result = weather_api.get_current_weather(location)
   
   if perf.duration_ms > 5000:  # 5 second threshold
       logger.warning("Slow API response", extra={
           "duration_ms": perf.duration_ms,
           "operation": "get_current_weather"
       })
   ```

2. **Error Rate Monitoring**
   ```python
   # Track error rates
   error_rate = (error_count / total_requests) * 100
   if error_rate > 5.0:  # 5% threshold
       send_alert(f"High error rate: {error_rate}%")
   ```

## Conclusion

This error handling and reliability framework provides a comprehensive foundation for building resilient, production-ready applications. By following the patterns and practices outlined in this guide, you can ensure your application gracefully handles failures, provides meaningful feedback to users, and maintains high availability even when dependencies are unavailable.

For additional support or questions, refer to the test suite and example implementations provided in the codebase.