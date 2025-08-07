"""Custom exceptions for the Weather Dashboard application.

This module defines a hierarchy of custom exceptions to provide
specific error handling throughout the application.
"""

from typing import Optional, Dict, Any


class WeatherAppError(Exception):
    """Base exception for weather app.
    
    All custom exceptions in the weather app should inherit from this class.
    Provides common functionality for error handling and logging.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context
        }


class APIError(WeatherAppError):
    """API related errors.
    
    Raised when external API calls fail or return unexpected responses.
    """
    
    def __init__(self, message: str, status_code: Optional[int] = None,
                 api_name: Optional[str] = None, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.api_name = api_name
        self.retry_after = retry_after
        if status_code:
            self.context["status_code"] = status_code
        if api_name:
            self.context["api_name"] = api_name
        if retry_after:
            self.context["retry_after"] = retry_after


class RateLimitError(APIError):
    """Rate limit exceeded error.
    
    Specific API error for when rate limits are exceeded.
    """
    
    def __init__(self, api_name: str, retry_after: Optional[int] = None):
        message = f"Rate limit exceeded for {api_name}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, status_code=429, api_name=api_name)
        if retry_after:
            self.context["retry_after"] = retry_after


class ConfigurationError(WeatherAppError):
    """Configuration/setup errors.
    
    Raised when there are issues with application configuration,
    missing environment variables, or invalid settings.
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key
        if config_key:
            self.context["config_key"] = config_key


class DataValidationError(WeatherAppError):
    """Data validation errors.
    
    Raised when input data fails validation or is in an unexpected format.
    """
    
    def __init__(self, message: str, field_name: Optional[str] = None,
                 invalid_value: Optional[Any] = None, field: Optional[str] = None,
                 value: Optional[Any] = None, **kwargs):
        super().__init__(message, **kwargs)
        # Support both field_name/invalid_value and field/value parameters
        self.field_name = field_name or field
        self.invalid_value = invalid_value if invalid_value is not None else value
        if self.field_name:
            self.context["field_name"] = self.field_name
        if self.invalid_value is not None:
            self.context["invalid_value"] = str(self.invalid_value)


class DatabaseError(WeatherAppError):
    """Database operation errors.
    
    Raised when database operations fail or encounter issues.
    """
    
    def __init__(self, message: str, operation: Optional[str] = None,
                 table_name: Optional[str] = None, table: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.operation = operation
        # Support both table_name and table parameters
        self.table_name = table_name or table
        if operation:
            self.context["operation"] = operation
        if self.table_name:
            self.context["table_name"] = self.table_name


class CacheError(WeatherAppError):
    """Cache operation errors.
    
    Raised when cache operations fail or encounter issues.
    """
    
    def __init__(self, message: str, cache_key: Optional[str] = None,
                 cache_type: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.cache_key = cache_key
        self.cache_type = cache_type
        if cache_key:
            self.context["cache_key"] = cache_key
        if cache_type:
            self.context["cache_type"] = cache_type


class UIError(WeatherAppError):
    """User interface errors.
    
    Raised when UI components fail to render or encounter issues.
    """
    
    def __init__(self, message: str, component_name: Optional[str] = None,
                 widget_type: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.component_name = component_name
        self.widget_type = widget_type
        if component_name:
            self.context["component_name"] = component_name
        if widget_type:
            self.context["widget_type"] = widget_type


class NetworkError(WeatherAppError):
    """Network connectivity errors.
    
    Raised when network operations fail due to connectivity issues.
    """
    
    def __init__(self, message: str, url: Optional[str] = None,
                 timeout: Optional[float] = None, endpoint: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        # Support both url and endpoint parameters
        self.url = url or endpoint
        self.timeout = timeout
        if self.url:
            self.context["url"] = self.url
        if timeout:
            self.context["timeout"] = timeout


class AuthenticationError(WeatherAppError):
    """Authentication and authorization errors.
    
    Raised when API keys are invalid or authentication fails.
    """
    
    def __init__(self, message: str, service_name: Optional[str] = None, service: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        # Support both service_name and service parameters
        self.service_name = service_name or service
        if self.service_name:
            self.context["service_name"] = self.service_name


# Error message mapping for user-friendly display
ERROR_MESSAGES = {
    APIError: "Unable to fetch data from external service. Please try again later.",
    RateLimitError: "Service is temporarily busy. Please wait a moment and try again.",
    ConfigurationError: "Application configuration issue. Please check your settings.",
    DataValidationError: "Invalid input data. Please check your entries and try again.",
    DatabaseError: "Database operation failed. Please try again later.",
    CacheError: "Cache operation failed. Data may be temporarily unavailable.",
    UIError: "Interface error occurred. Please refresh the application.",
    NetworkError: "Network connection issue. Please check your internet connection.",
    AuthenticationError: "Authentication failed. Please check your API credentials.",
    WeatherAppError: "An unexpected error occurred. Please try again later."
}


def get_user_friendly_message(error: Exception) -> str:
    """Get user-friendly error message for display.
    
    Args:
        error: The exception that occurred
        
    Returns:
        User-friendly error message string
    """
    for error_type, message in ERROR_MESSAGES.items():
        if isinstance(error, error_type):
            return message
    
    # Fallback for unknown errors
    return "An unexpected error occurred. Please try again later."