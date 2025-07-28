#!/usr/bin/env python3
"""
Services Package

This package contains service implementations for the weather dashboard application,
including database services, weather services, and other business logic components.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0 (Modularized Services)
"""

# Import modularized database components
from .database_service import DatabaseImpl
from .mock_database import MockDatabase

# Import other service implementations
try:
    from .weather_service_impl import WeatherServiceImpl
except ImportError:
    # Weather service implementation may not exist yet
    pass

try:
    from .logging_service_impl import LoggingServiceImpl
except ImportError:
    # Logging service implementation may not exist yet
    pass

try:
    from .configuration_service_impl import ConfigurationServiceImpl
except ImportError:
    # Configuration service implementation may not exist yet
    pass

# Backward compatibility - import original database_impl if it exists
try:
    from .database_impl import DatabaseImpl as DatabaseImplLegacy, MockDatabase as MockDatabaseLegacy
except ImportError:
    # Original database_impl may have been renamed or removed
    DatabaseImplLegacy = None
    MockDatabaseLegacy = None

# Export all components
__all__ = [
    # New modularized components
    'DatabaseImpl',
    'MockDatabase',
    
    # Backward compatibility (if available)
    'DatabaseImplLegacy',
    'MockDatabaseLegacy',
]

# Add conditional exports for other services if they exist
if 'WeatherServiceImpl' in locals():
    __all__.append('WeatherServiceImpl')

if 'LoggingServiceImpl' in locals():
    __all__.append('LoggingServiceImpl')

if 'ConfigurationServiceImpl' in locals():
    __all__.append('ConfigurationServiceImpl')