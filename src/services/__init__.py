"""Services package.

Provides all application services including weather, database, AI, configuration,
and performance optimization services.
"""

# Import service modules
from . import weather
from . import database
from . import ai
from . import config
from . import cache

# Import remaining services
from .github_team_service import GitHubTeamService
from .google_maps_service import GoogleMapsService
from .logging_service import LoggingService
from .maps_service import WeatherMapsService
from .search_state_service import SearchStateService

# Import performance optimization services
from .async_service import AsyncService, get_async_service
from .lazy_loading import LazyService, lazy_property, lazy_init
from .memory_optimizer import MemoryOptimizer, get_memory_optimizer
from .database_optimizer import DatabaseOptimizer, get_database_optimizer
from .image_optimizer import ImageOptimizer, get_image_optimizer
from .chart_optimizer import ChartOptimizer, get_chart_optimizer
from .ai_optimizer import AIResponseOptimizer, get_ai_optimizer
from .performance_monitor import PerformanceMonitor, get_performance_monitor

# Import error handling and logging
from .exceptions import (
    WeatherAppError, APIError, ConfigurationError, DataValidationError,
    DatabaseError, CacheError, UIError, NetworkError, AuthenticationError,
    RateLimitError, get_user_friendly_message
)
from .logging_config import setup_logging, get_logger, WeatherAppLogger
from .error_handler import (
    ErrorHandler, RetryConfig, CircuitBreaker,
    retry_on_exception, async_retry_on_exception,
    safe_execute, handle_api_error, handle_database_error
)

__all__ = [
    # Core service modules
    "weather",
    "database",
    "ai",
    "config",
    "cache",
    
    # Legacy services
    "GitHubTeamService",
    "GoogleMapsService",
    "LoggingService",
    "WeatherMapsService",
    "SearchStateService",
    
    # Performance optimization services
    "AsyncService",
    "get_async_service",
    "LazyService",
    "lazy_property",
    "lazy_init",
    "MemoryOptimizer",
    "get_memory_optimizer",
    "DatabaseOptimizer",
    "get_database_optimizer",
    "ImageOptimizer",
    "get_image_optimizer",
    "ChartOptimizer",
    "get_chart_optimizer",
    "AIResponseOptimizer",
    "get_ai_optimizer",
    "PerformanceMonitor",
    "get_performance_monitor",
    
    # Error handling
    "WeatherAppError",
    "APIError",
    "ConfigurationError",
    "DataValidationError",
    "DatabaseError",
    "CacheError",
    "UIError",
    "NetworkError",
    "AuthenticationError",
    "RateLimitError",
    "get_user_friendly_message",
    
    # Logging
    "setup_logging",
    "get_logger",
    "WeatherAppLogger",
    
    # Error handling utilities
    "ErrorHandler",
    "RetryConfig",
    "CircuitBreaker",
    "retry_on_exception",
    "async_retry_on_exception",
    "safe_execute",
    "handle_api_error",
    "handle_database_error",
]
