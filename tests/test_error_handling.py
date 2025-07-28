#!/usr/bin/env python3
"""
Comprehensive Test Suite for Error Handling and Reliability Patterns

This test suite validates the error handling framework, reliability patterns,
and logging infrastructure implemented in the weather service.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0
"""

import unittest
import asyncio
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
from typing import Any, Dict, List
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.exceptions import (
    BaseApplicationError, ValidationError, ServiceError, ExternalServiceError,
    NetworkError, TimeoutError, DatabaseError, ConfigurationError,
    AuthenticationError, AuthorizationError, RateLimitError,
    ErrorSeverity, ErrorCategory
)
from src.core.reliability import (
    CircuitBreaker, CircuitState, RetryHandler,
    TimeoutManager, HealthCheck, GracefulDegradation
)
from src.core.error_handling import (
    ErrorContext, handle_errors, safe_execute, ErrorAggregator,
    ErrorRecovery, error_boundary, create_error_handler
)
from src.core.logging_framework import ContextualLogger, LogLevel
from src.services.weather_service_impl import WeatherServiceImpl, MockWeatherService


class TestExceptionHierarchy(unittest.TestCase):
    """Test the custom exception hierarchy."""
    
    def test_base_application_error_creation(self):
        """Test BaseApplicationError creation with all parameters."""
        error = BaseApplicationError(
            message="Test error",
            correlation_id="test-123",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.BUSINESS_LOGIC,
            context={"key": "value"},
            user_message="User-friendly message"
        )
        
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.correlation_id, "test-123")
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertEqual(error.category, ErrorCategory.BUSINESS_LOGIC)
        self.assertEqual(error.context, {"key": "value"})
        self.assertEqual(error.user_message, "User-friendly message")
        self.assertIsNotNone(error.timestamp)
    
    def test_validation_error_creation(self):
        """Test ValidationError with field-specific information."""
        error = ValidationError(
            message="Invalid input",
            field="email",
            value="invalid-email",
            constraint="Must be valid email format"
        )
        
        self.assertEqual(error.field, "email")
        self.assertEqual(error.value, "invalid-email")
        self.assertEqual(error.constraint, "Must be valid email format")
        self.assertEqual(error.category, ErrorCategory.VALIDATION)
    
    def test_external_service_error_creation(self):
        """Test ExternalServiceError with service-specific information."""
        error = ExternalServiceError(
            message="Service unavailable",
            service_name="weather-api",
            endpoint="/current",
            status_code=503,
            response_body="Service temporarily unavailable"
        )
        
        self.assertEqual(error.service_name, "weather-api")
        self.assertEqual(error.endpoint, "/current")
        self.assertEqual(error.status_code, 503)
        self.assertEqual(error.response_body, "Service temporarily unavailable")
        self.assertEqual(error.category, ErrorCategory.EXTERNAL_SERVICE)


class TestCircuitBreaker(unittest.TestCase):
    """Test the Circuit Breaker reliability pattern."""
    
    def setUp(self):
        """Set up test fixtures."""
        from core.reliability import CircuitBreakerConfig
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1.0,
            success_threshold=1  # Allow single success to close circuit for testing
        )
        self.circuit_breaker = CircuitBreaker("test_circuit", config)
    
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in CLOSED state."""
        self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)
        self.assertEqual(self.circuit_breaker._failure_count, 0)
    
    def test_circuit_breaker_failure_counting(self):
        """Test circuit breaker failure counting and state transitions."""
        def failing_function():
            raise ExternalServiceError("Test failure", "test_service")
        
        # First two failures should keep circuit closed
        for i in range(2):
            with self.assertRaises(ExternalServiceError):
                self.circuit_breaker._execute(failing_function)
            self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)
        
        # Third failure should open the circuit
        with self.assertRaises(ExternalServiceError):
            self.circuit_breaker._execute(failing_function)
        self.assertEqual(self.circuit_breaker.state, CircuitState.OPEN)
    
    def test_circuit_breaker_open_state_behavior(self):
        """Test circuit breaker behavior when open."""
        # Force circuit to open state
        self.circuit_breaker.state = CircuitState.OPEN
        self.circuit_breaker._last_failure_time = datetime.now(timezone.utc)
        
        def dummy_function():
            return "success"
        
        # Should raise ExternalServiceError when circuit is open
        with self.assertRaises(ExternalServiceError) as context:
            self.circuit_breaker._execute(dummy_function)
        
        self.assertIn("Circuit breaker", str(context.exception))
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        from datetime import datetime, timedelta
        # Force circuit to open state with old timestamp
        self.circuit_breaker.state = CircuitState.OPEN
        self.circuit_breaker._last_failure_time = datetime.now(timezone.utc) - timedelta(seconds=2)
        
        def success_function():
            return "success"
        
        # Should transition to HALF_OPEN and then CLOSED on success
        result = self.circuit_breaker._execute(success_function)
        self.assertEqual(result, "success")
        self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)


class TestRetryHandler(unittest.TestCase):
    """Test the Retry with Exponential Backoff pattern."""
    
    def setUp(self):
        """Set up test fixtures."""
        from core.reliability import RetryConfig
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )
        self.retry = RetryHandler(config)
    
    def test_retry_success_on_first_attempt(self):
        """Test successful execution on first attempt."""
        def success_function():
            return "success"
        
        result = self.retry._execute_with_retry(success_function)
        self.assertEqual(result, "success")
    
    def test_retry_success_after_failures(self):
        """Test successful execution after some failures."""
        call_count = 0
        
        def eventually_success_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ExternalServiceError("Temporary failure", "test_service")
            return "success"
        
        result = self.retry._execute_with_retry(eventually_success_function)
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    def test_retry_exhaustion(self):
        """Test behavior when all retry attempts are exhausted."""
        def always_fail_function():
            raise ExternalServiceError("Persistent failure", "test_service")
        
        with self.assertRaises(ExternalServiceError) as context:
            self.retry._execute_with_retry(always_fail_function)
        
        self.assertIn("Persistent failure", str(context.exception))
    
    @patch('time.sleep')
    def test_retry_backoff_timing(self, mock_sleep):
        """Test exponential backoff timing."""
        call_count = 0
        
        def fail_twice_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ExternalServiceError("Temporary failure", "test_service")
            return "success"
        
        result = self.retry._execute_with_retry(fail_twice_function)
        self.assertEqual(result, "success")
        
        # Should have called sleep twice (after first and second failures)
        self.assertEqual(mock_sleep.call_count, 2)
        
        # Check backoff progression: 0.1, 0.2
        expected_delays = [0.1, 0.2]
        actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
        
        for expected, actual in zip(expected_delays, actual_delays):
            self.assertAlmostEqual(expected, actual, places=1)


class TestTimeoutManager(unittest.TestCase):
    """Test the Timeout Manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timeout_manager = TimeoutManager(default_timeout=1.0)
    
    def test_timeout_success(self):
        """Test successful execution within timeout."""
        def quick_function():
            time.sleep(0.1)
            return "success"
        
        result = self.timeout_manager._execute_with_timeout(quick_function, 0.5)
        self.assertEqual(result, "success")
    
    def test_timeout_failure(self):
        """Test timeout when function takes too long."""
        def slow_function():
            time.sleep(2.0)
            return "success"
        
        with self.assertRaises(TimeoutError) as context:
            self.timeout_manager._execute_with_timeout(slow_function, 0.5)
        
        self.assertIn("timed out", str(context.exception))


class TestErrorHandlingDecorator(unittest.TestCase):
    """Test the error handling decorator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = ContextualLogger("test")
    
    def test_handle_errors_success(self):
        """Test decorator with successful function execution."""
        @handle_errors(operation="test_operation")
        def success_function(value: str) -> str:
            return f"processed: {value}"
        
        result = success_function("test")
        self.assertEqual(result, "processed: test")
    
    def test_handle_errors_with_exception(self):
        """Test decorator with function that raises exception."""
        @handle_errors(operation="test_operation")
        def failing_function():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            failing_function()
    
    def test_handle_errors_with_fallback(self):
        """Test decorator with fallback value."""
        @handle_errors(operation="test_operation", fallback_value="fallback")
        def failing_function():
            raise Exception("Test error")
        
        result = failing_function()
        self.assertEqual(result, "fallback")


class TestErrorBoundary(unittest.TestCase):
    """Test the error boundary context manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = ContextualLogger("test")
    
    def test_error_boundary_success(self):
        """Test error boundary with successful execution."""
        with error_boundary("test_operation", self.logger) as boundary:
            result = "success"
        
        self.assertIsNone(boundary.error)
        self.assertTrue(boundary.success)
    
    def test_error_boundary_with_exception(self):
        """Test error boundary with exception."""
        with error_boundary("test_operation", self.logger) as boundary:
            raise ValueError("Test error")
        
        # Error boundary should catch and suppress the exception
        self.assertIsNotNone(boundary.error)
        self.assertFalse(boundary.success)
        self.assertIsInstance(boundary.error, ValueError)
    
    def test_error_boundary_with_fallback(self):
        """Test error boundary with fallback value."""
        with error_boundary("test_operation", self.logger, fallback_value="fallback") as boundary:
            raise Exception("Test error")
        
        self.assertIsNotNone(boundary.error)
        self.assertFalse(boundary.success)
        # The fallback value would be returned by the context manager


class TestErrorAggregator(unittest.TestCase):
    """Test the error aggregator for batch processing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.aggregator = ErrorAggregator()
    
    def test_error_aggregation(self):
        """Test adding and retrieving errors."""
        error1 = ValidationError("Error 1")
        error2 = ServiceError("Error 2")
        
        self.aggregator.add_error(error1)
        self.aggregator.add_error(error2)
        
        self.assertTrue(self.aggregator.has_errors())
        self.assertEqual(len(self.aggregator.get_errors()), 2)
        self.assertEqual(self.aggregator.get_error_count(), 2)
    
    def test_error_filtering(self):
        """Test filtering errors by severity."""
        high_error = ValidationError("High error", severity=ErrorSeverity.HIGH)
        low_error = ServiceError("Low error", severity=ErrorSeverity.LOW)
        
        self.aggregator.add_error(high_error)
        self.aggregator.add_error(low_error)
        
        high_errors = self.aggregator.get_errors_by_severity(ErrorSeverity.HIGH)
        self.assertEqual(len(high_errors), 1)
        self.assertEqual(high_errors[0].message, "High error")
    
    def test_error_summary(self):
        """Test error summary generation."""
        self.aggregator.add_error(ValidationError("Validation error"))
        self.aggregator.add_error(ServiceError("Service error"))
        
        summary = self.aggregator.get_summary()
        
        self.assertIn("total_errors", summary)
        self.assertIn("by_category", summary)
        self.assertIn("by_severity", summary)
        self.assertEqual(summary["total_errors"], 2)


class TestWeatherServiceErrorHandling(unittest.TestCase):
    """Test error handling in the weather service implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_weather_service = MockWeatherService()
    
    def test_successful_weather_request(self):
        """Test successful weather data retrieval."""
        result = self.mock_weather_service.get_current_weather("New York")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.location, "New York")
        self.assertIsInstance(result.temperature, (int, float))
    
    def test_validation_error_empty_location(self):
        """Test validation error for empty location."""
        with self.assertRaises(ValueError) as context:
            self.mock_weather_service.get_current_weather("")
        
        self.assertIn("Location cannot be empty", str(context.exception))
    
    def test_validation_error_invalid_forecast_days(self):
        """Test validation error for invalid forecast days."""
        with self.assertRaises(ValueError) as context:
            self.mock_weather_service.get_forecast("Paris", days=20)
        
        self.assertIn("Days must be between 1 and 14", str(context.exception))
    
    def test_simulated_service_failure(self):
        """Test simulated service failure handling."""
        self.mock_weather_service.set_should_fail(True)
        
        with self.assertRaises(ExternalServiceError) as context:
            self.mock_weather_service.get_current_weather("London")
        
        self.assertIn("temporarily unavailable", context.exception.user_message)
        
        # Reset failure simulation
        self.mock_weather_service.set_should_fail(False)
    
    def test_connection_test_success(self):
        """Test successful connection test."""
        result = self.mock_weather_service.test_connection()
        self.assertTrue(result)
    
    def test_connection_test_failure(self):
        """Test connection test with simulated failure."""
        self.mock_weather_service.set_should_fail(True)
        
        result = self.mock_weather_service.test_connection()
        self.assertFalse(result)
        
        # Reset failure simulation
        self.mock_weather_service.set_should_fail(False)
    
    def test_provider_status_retrieval(self):
        """Test provider status information retrieval."""
        status = self.mock_weather_service.get_provider_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn("demo_mode", status)
        self.assertIn("call_count", status)
        self.assertTrue(status["demo_mode"])


class TestStructuredLogging(unittest.TestCase):
    """Test the structured logging framework."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = ContextualLogger("test-logger")
    
    def test_logger_initialization(self):
        """Test logger initialization with metadata."""
        self.assertEqual(self.logger.logger.name, "test-logger")
        self.assertIsNotNone(self.logger.context.correlation_id)
    
    @patch('logging.Logger.log')
    def test_structured_info_logging(self, mock_log):
        """Test structured info logging."""
        self.logger.info("Test message", extra={"key": "value"})
        
        # Verify that the underlying logger was called
        mock_log.assert_called_once()
    
    @patch('logging.Logger.log')
    def test_structured_error_logging(self, mock_log):
        """Test structured error logging."""
        self.logger.error("Error message", extra={"error_code": "E001"})
        
        # Verify that the underlying logger was called
        mock_log.assert_called_once()
    
    def test_correlation_id_generation(self):
        """Test correlation ID generation and consistency."""
        correlation_id = self.logger.context.correlation_id
        
        self.assertIsNotNone(correlation_id)
        self.assertIsInstance(correlation_id, str)
        self.assertTrue(len(correlation_id) > 0)
        
        # Should be consistent across calls
        self.assertEqual(correlation_id, self.logger.context.correlation_id)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete error handling scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.weather_service = MockWeatherService()
        self.logger = ContextualLogger("integration-test")
    
    def test_end_to_end_success_scenario(self):
        """Test complete successful weather request flow."""
        try:
            with error_boundary("weather_request", self.logger) as boundary:
                weather_data = self.weather_service.get_current_weather("Seattle")
                forecast_data = self.weather_service.get_forecast("Seattle", days=3)
                connection_status = self.weather_service.test_connection()
                provider_status = self.weather_service.get_provider_status()
            
            self.assertIsNotNone(weather_data)
            self.assertIsNotNone(forecast_data)
            self.assertTrue(connection_status)
            self.assertIsNotNone(provider_status)
            self.assertTrue(boundary.success)
            
        except Exception as e:
            self.fail(f"End-to-end success scenario failed: {e}")
    
    def test_end_to_end_failure_recovery_scenario(self):
        """Test complete failure and recovery flow."""
        # Enable failure simulation
        self.weather_service.set_should_fail(True)
        
        weather_data = None
        try:
            with error_boundary("weather_request_with_failure", self.logger, fallback_value=None) as boundary:
                weather_data = self.weather_service.get_current_weather("Portland")
            
            # If we reach here without exception, the boundary caught it
            # Check if the boundary caught an error
            if not boundary.success:
                weather_data = boundary.fallback_value
            
            # Should handle the error gracefully
            self.assertIsNone(weather_data)  # Fallback value
            self.assertFalse(boundary.success)
            self.assertIsNotNone(boundary.error)
            
        except Exception as e:
            # Should not reach here due to error boundary
            self.fail(f"Error boundary should have caught the exception: {e}")
        
        finally:
            # Reset failure simulation
            self.weather_service.set_should_fail(False)
    
    def test_multiple_service_calls_with_mixed_results(self):
        """Test multiple service calls with some successes and failures."""
        results = []
        
        # Successful call
        try:
            weather_data = self.weather_service.get_current_weather("Denver")
            results.append(("success", weather_data))
        except Exception as e:
            results.append(("error", e))
        
        # Enable failure for next call
        self.weather_service.set_should_fail(True)
        
        # Failed call
        try:
            weather_data = self.weather_service.get_current_weather("Phoenix")
            results.append(("success", weather_data))
        except Exception as e:
            results.append(("error", e))
        
        # Reset and try again
        self.weather_service.set_should_fail(False)
        
        # Another successful call
        try:
            weather_data = self.weather_service.get_current_weather("Miami")
            results.append(("success", weather_data))
        except Exception as e:
            results.append(("error", e))
        
        # Verify mixed results
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0][0], "success")  # First call succeeded
        self.assertEqual(results[1][0], "error")    # Second call failed
        self.assertEqual(results[2][0], "success")  # Third call succeeded


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)