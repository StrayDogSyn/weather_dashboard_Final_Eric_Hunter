"""Utilities Package

Provides helper functions for data formatting, validation, and common operations.
"""

from .formatters import (
    format_temperature,
    format_wind_speed,
    format_pressure,
    format_humidity,
    format_percentage,
    format_distance,
    format_time,
    format_datetime,
    format_duration
)

from .validators import (
    validate_api_key,
    validate_coordinates,
    validate_city_name,
    validate_temperature_range,
    validate_url,
    validate_email
)

from .helpers import (
    safe_float,
    safe_int,
    safe_get,
    retry_on_failure,
    debounce,
    rate_limit,
    calculate_distance,
    generate_cache_key,
    sanitize_filename
)

__version__ = "1.0.0"
__author__ = "Weather Dashboard Team"

__all__ = [
    # Formatters
    "format_temperature",
    "format_wind_speed",
    "format_pressure",
    "format_humidity",
    "format_percentage",
    "format_distance",
    "format_time",
    "format_datetime",
    "format_duration",
    
    # Validators
    "validate_api_key",
    "validate_coordinates",
    "validate_city_name",
    "validate_temperature_range",
    "validate_url",
    "validate_email",
    
    # Helpers
    "safe_float",
    "safe_int",
    "safe_get",
    "retry_on_failure",
    "debounce",
    "rate_limit",
    "calculate_distance",
    "generate_cache_key",
    "sanitize_filename"
]