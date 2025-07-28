#!/usr/bin/env python3
"""
Comprehensive Exception Hierarchy for Weather Dashboard

This module defines a standardized exception hierarchy for production-ready
error handling, following Microsoft's recommended patterns for robust
application development.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels for categorizing exceptions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification and handling."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    USER_INPUT = "user_input"


class BaseApplicationError(Exception):
    """Base exception class for all application errors.
    
    Provides structured error information including:
    - Unique error correlation ID for tracing
    - Error severity and category classification
    - Contextual information for debugging
    - User-friendly error messages
    - Timestamp for error tracking
    """
    
    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        correlation_id: Optional[str] = None,
        inner_exception: Optional[Exception] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(message)
        
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.category = category
        self.context = context or {}
        self.user_message = user_message or "An error occurred. Please try again."
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.inner_exception = inner_exception
        self.retry_after = retry_after
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "severity": self.severity.value,
            "category": self.category.value,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "retry_after": self.retry_after,
            "inner_exception": str(self.inner_exception) if self.inner_exception else None
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message} (ID: {self.correlation_id})"


class ValidationError(BaseApplicationError):
    """Exception for input validation failures."""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rules: Optional[List[str]] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            "field_name": field_name,
            "field_value": str(field_value) if field_value is not None else None,
            "validation_rules": validation_rules or []
        })
        
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            user_message=f"Invalid input: {message}",
            context=context,
            **kwargs
        )


class ServiceError(BaseApplicationError):
    """Exception for service layer errors."""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            "service_name": service_name,
            "operation": operation
        })
        
        super().__init__(
            message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            **kwargs
        )


class ExternalServiceError(BaseApplicationError):
    """Exception for external service integration failures."""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            "service_name": service_name,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_body": response_body
        })
        
        # Determine retry strategy based on status code
        retry_after = None
        if status_code in [429, 503, 504]:  # Rate limit, service unavailable, gateway timeout
            retry_after = 60  # Retry after 60 seconds
        
        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH if status_code and status_code >= 500 else ErrorSeverity.MEDIUM,
            user_message="External service is temporarily unavailable. Please try again later.",
            retry_after=retry_after,
            context=context,
            **kwargs
        )


class DatabaseError(BaseApplicationError):
    """Exception for database operation failures."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            "operation": operation,
            "table_name": table_name,
            "query": query
        })
        
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            user_message="Data operation failed. Please try again.",
            context=context,
            **kwargs
        )


class ConfigurationError(BaseApplicationError):
    """Exception for configuration-related errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            "config_key": config_key,
            "config_file": config_file
        })
        
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            user_message="Application configuration error. Please contact support.",
            context=context,
            **kwargs
        )


class AuthenticationError(BaseApplicationError):
    """Exception for authentication failures."""
    
    def __init__(
        self,
        message: str,
        username: Optional[str] = None,
        auth_method: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            "username": username,
            "auth_method": auth_method
        })
        
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="Authentication failed. Please check your credentials.",
            context=context,
            **kwargs
        )


class AuthorizationError(BaseApplicationError):
    """Exception for authorization failures."""
    
    def __init__(
        self,
        message: str,
        resource: Optional[str] = None,
        required_permission: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            "resource": resource,
            "required_permission": required_permission
        })
        
        super().__init__(
            message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="Access denied. You don't have permission to perform this action.",
            context=context,
            **kwargs
        )


class NetworkError(BaseApplicationError):
    """Exception for network-related failures."""
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            "url": url,
            "timeout": timeout
        })
        
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            user_message="Network connection failed. Please check your internet connection.",
            retry_after=30,  # Retry after 30 seconds for network issues
            context=context,
            **kwargs
        )


class TimeoutError(BaseApplicationError):
    """Exception for operation timeout failures."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            "operation": operation,
            "timeout_seconds": timeout_seconds
        })
        
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            user_message="Operation timed out. Please try again.",
            retry_after=10,  # Retry after 10 seconds for timeouts
            context=context,
            **kwargs
        )


class RateLimitError(BaseApplicationError):
    """Exception for rate limiting scenarios."""
    
    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            "limit": limit,
            "window_seconds": window_seconds
        })
        
        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            user_message="Rate limit exceeded. Please wait before trying again.",
            retry_after=window_seconds or 60,
            context=context,
            **kwargs
        )


# Legacy exception compatibility
DependencyResolutionError = ServiceError
CircularDependencyError = ServiceError
GeminiError = ExternalServiceError