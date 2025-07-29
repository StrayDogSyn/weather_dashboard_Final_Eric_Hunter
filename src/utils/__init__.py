"""Utilities Package

Provides helper functions for data formatting, validation, and common operations.
"""

from utils.formatters import (
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

from utils.validators import (
    validate_api_key,
    validate_coordinates,
    validate_city_name,
    validate_temperature_range,
    validate_url,
    validate_email
)

from utils.helpers import (
    Debouncer,
    SimpleCache,
    generate_cache_key,
    retry_on_failure,
    safe_divide,
    safe_get,
    merge_dicts,
    flatten_dict,
    chunk_list,
    truncate_string,
    get_resource_path,
    ensure_directory,
    get_file_size,
    is_file_older_than,
    get_system_info
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
    "Debouncer",
    "SimpleCache",
    "generate_cache_key",
    "retry_on_failure",
    "safe_divide",
    "safe_get",
    "merge_dicts",
    "flatten_dict",
    "chunk_list",
    "truncate_string",
    "get_resource_path",
    "ensure_directory",
    "get_file_size",
    "is_file_older_than",
    "get_system_info"
]