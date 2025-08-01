"""Custom Exceptions

Defines custom exception classes for better error handling
and debugging throughout the application.
"""

from typing import Any, Dict, Optional


class WeatherDashboardError(Exception):
    """Base exception class for all weather dashboard errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize the exception.

        Args:
            message: Error message
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation of the exception."""
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class WeatherServiceError(WeatherDashboardError):
    """Exception raised when weather service operations fail."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the weather service exception.

        Args:
            message: Error message
            service_name: Name of the weather service that failed
            status_code: HTTP status code if applicable
            details: Optional additional error details
        """
        super().__init__(message, details)
        self.service_name = service_name
        self.status_code = status_code

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]
        if self.service_name:
            parts.append(f"Service: {self.service_name}")
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)


class ConfigurationError(WeatherDashboardError):
    """Exception raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the configuration exception.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
            details: Optional additional error details
        """
        super().__init__(message, details)
        self.config_key = config_key

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]
        if self.config_key:
            parts.append(f"Key: {self.config_key}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)


class DataPersistenceError(WeatherDashboardError):
    """Exception raised when data persistence operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the data persistence exception.

        Args:
            message: Error message
            operation: Database operation that failed (save, get, update, delete)
            entity_type: Type of entity involved
            entity_id: ID of the entity involved
            details: Optional additional error details
        """
        super().__init__(message, details)
        self.operation = operation
        self.entity_type = entity_type
        self.entity_id = entity_id

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        if self.entity_type:
            parts.append(f"Entity: {self.entity_type}")
        if self.entity_id:
            parts.append(f"ID: {self.entity_id}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)


class APIError(WeatherDashboardError):
    """Exception raised when API calls fail."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        api_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the API exception.

        Args:
            message: Error message
            status_code: HTTP status code
            api_name: Name of the API that failed
            endpoint: API endpoint that was called
            response_data: Response data from the API
            details: Optional additional error details
        """
        super().__init__(message, details)
        self.status_code = status_code
        self.api_name = api_name
        self.endpoint = endpoint
        self.response_data = response_data or {}

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]
        if self.api_name:
            parts.append(f"API: {self.api_name}")
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")
        if self.response_data:
            parts.append(f"Response: {self.response_data}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)

    @property
    def is_client_error(self) -> bool:
        """Check if this is a client error (4xx status code)."""
        return self.status_code is not None and 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """Check if this is a server error (5xx status code)."""
        return self.status_code is not None and 500 <= self.status_code < 600

    @property
    def is_rate_limited(self) -> bool:
        """Check if this is a rate limiting error."""
        return self.status_code == 429

    @property
    def is_unauthorized(self) -> bool:
        """Check if this is an unauthorized error."""
        return self.status_code == 401

    @property
    def is_forbidden(self) -> bool:
        """Check if this is a forbidden error."""
        return self.status_code == 403

    @property
    def is_not_found(self) -> bool:
        """Check if this is a not found error."""
        return self.status_code == 404


class ValidationError(WeatherDashboardError):
    """Exception raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rule: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the validation exception.

        Args:
            message: Error message
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
            validation_rule: Validation rule that was violated
            details: Optional additional error details
        """
        super().__init__(message, details)
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]
        if self.field_name:
            parts.append(f"Field: {self.field_name}")
        if self.field_value is not None:
            parts.append(f"Value: {self.field_value}")
        if self.validation_rule:
            parts.append(f"Rule: {self.validation_rule}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)


class CacheError(WeatherDashboardError):
    """Exception raised when cache operations fail."""

    def __init__(
        self,
        message: str,
        cache_key: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the cache exception.

        Args:
            message: Error message
            cache_key: Cache key involved in the operation
            operation: Cache operation that failed (get, set, delete, clear)
            details: Optional additional error details
        """
        super().__init__(message, details)
        self.cache_key = cache_key
        self.operation = operation

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        if self.cache_key:
            parts.append(f"Key: {self.cache_key}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)


class ServiceUnavailableError(WeatherDashboardError):
    """Exception raised when a required service is unavailable."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the service unavailable exception.

        Args:
            message: Error message
            service_name: Name of the unavailable service
            retry_after: Suggested retry delay in seconds
            details: Optional additional error details
        """
        super().__init__(message, details)
        self.service_name = service_name
        self.retry_after = retry_after

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]
        if self.service_name:
            parts.append(f"Service: {self.service_name}")
        if self.retry_after:
            parts.append(f"Retry after: {self.retry_after}s")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)


class TimeoutError(WeatherDashboardError):
    """Exception raised when operations timeout."""

    def __init__(
        self,
        message: str,
        timeout_duration: Optional[float] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the timeout exception.

        Args:
            message: Error message
            timeout_duration: Timeout duration in seconds
            operation: Operation that timed out
            details: Optional additional error details
        """
        super().__init__(message, details)
        self.timeout_duration = timeout_duration
        self.operation = operation

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        if self.timeout_duration:
            parts.append(f"Timeout: {self.timeout_duration}s")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)
