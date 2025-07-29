"""Data Validators

Utilities for validating user input and API data.
"""

import re
from typing import Optional, Tuple, Union
from urllib.parse import urlparse


def validate_api_key(api_key: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate OpenWeather API key format.
    
    Args:
        api_key: API key string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key:
        return False, "API key is required"
    
    if not isinstance(api_key, str):
        return False, "API key must be a string"
    
    # Remove whitespace
    api_key = api_key.strip()
    
    if len(api_key) == 0:
        return False, "API key cannot be empty"
    
    # OpenWeather API keys are typically 32 character hexadecimal strings
    if len(api_key) != 32:
        return False, "API key must be 32 characters long"
    
    # Check if it's a valid hexadecimal string
    if not re.match(r'^[a-fA-F0-9]{32}$', api_key):
        return False, "API key must contain only hexadecimal characters (0-9, a-f)"
    
    return True, None


def validate_coordinates(
    latitude: Union[str, float, int],
    longitude: Union[str, float, int]
) -> Tuple[bool, Optional[str], Optional[Tuple[float, float]]]:
    """Validate geographic coordinates.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
    
    Returns:
        Tuple of (is_valid, error_message, parsed_coordinates)
    """
    try:
        # Convert to float
        lat = float(latitude)
        lon = float(longitude)
        
        # Validate latitude range (-90 to 90)
        if lat < -90 or lat > 90:
            return False, "Latitude must be between -90 and 90 degrees", None
        
        # Validate longitude range (-180 to 180)
        if lon < -180 or lon > 180:
            return False, "Longitude must be between -180 and 180 degrees", None
        
        return True, None, (lat, lon)
        
    except (ValueError, TypeError):
        return False, "Coordinates must be valid numbers", None


def validate_city_name(city_name: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate city name format.
    
    Args:
        city_name: City name string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not city_name:
        return False, "City name is required"
    
    if not isinstance(city_name, str):
        return False, "City name must be a string"
    
    # Remove leading/trailing whitespace
    city_name = city_name.strip()
    
    if len(city_name) == 0:
        return False, "City name cannot be empty"
    
    if len(city_name) < 2:
        return False, "City name must be at least 2 characters long"
    
    if len(city_name) > 100:
        return False, "City name cannot exceed 100 characters"
    
    # Check for valid characters (letters, spaces, hyphens, apostrophes, periods)
    if not re.match(r"^[a-zA-Z\s\-'.]+$", city_name):
        return False, "City name can only contain letters, spaces, hyphens, apostrophes, and periods"
    
    # Check for consecutive spaces or special characters
    if re.search(r'[\s\-\'.]{{2,}}', city_name):
        return False, "City name cannot have consecutive spaces or special characters"
    
    # Check that it doesn't start or end with special characters
    if re.match(r'^[\s\-\'.]+|[\s\-\'.]+$', city_name):
        return False, "City name cannot start or end with spaces or special characters"
    
    return True, None


def validate_temperature_range(
    min_temp: Union[str, float, int],
    max_temp: Union[str, float, int],
    unit: str = "celsius"
) -> Tuple[bool, Optional[str]]:
    """Validate temperature range.
    
    Args:
        min_temp: Minimum temperature
        max_temp: Maximum temperature
        unit: Temperature unit ('celsius' or 'fahrenheit')
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        min_t = float(min_temp)
        max_t = float(max_temp)
        
        # Check that min is less than max
        if min_t >= max_t:
            return False, "Minimum temperature must be less than maximum temperature"
        
        # Validate reasonable temperature ranges
        if unit.lower() == "celsius":
            if min_t < -100 or max_t > 70:
                return False, "Temperature range seems unrealistic for Celsius (-100°C to 70°C)"
        elif unit.lower() == "fahrenheit":
            if min_t < -148 or max_t > 158:
                return False, "Temperature range seems unrealistic for Fahrenheit (-148°F to 158°F)"
        else:
            return False, "Temperature unit must be 'celsius' or 'fahrenheit'"
        
        return True, None
        
    except (ValueError, TypeError):
        return False, "Temperature values must be valid numbers"


def validate_url(url: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate URL format.
    
    Args:
        url: URL string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"
    
    if not isinstance(url, str):
        return False, "URL must be a string"
    
    url = url.strip()
    
    if len(url) == 0:
        return False, "URL cannot be empty"
    
    try:
        result = urlparse(url)
        
        # Check that scheme and netloc are present
        if not result.scheme:
            return False, "URL must include a scheme (http:// or https://)"
        
        if not result.netloc:
            return False, "URL must include a domain name"
        
        # Check for valid schemes
        if result.scheme.lower() not in ['http', 'https']:
            return False, "URL scheme must be http or https"
        
        return True, None
        
    except Exception:
        return False, "Invalid URL format"


def validate_email(email: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate email address format.
    
    Args:
        email: Email address string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email address is required"
    
    if not isinstance(email, str):
        return False, "Email address must be a string"
    
    email = email.strip().lower()
    
    if len(email) == 0:
        return False, "Email address cannot be empty"
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Invalid email address format"
    
    # Additional checks
    if len(email) > 254:
        return False, "Email address is too long"
    
    local_part, domain = email.split('@')
    
    if len(local_part) > 64:
        return False, "Email local part is too long"
    
    if len(domain) > 253:
        return False, "Email domain is too long"
    
    return True, None


def validate_port(port: Union[str, int]) -> Tuple[bool, Optional[str], Optional[int]]:
    """Validate network port number.
    
    Args:
        port: Port number to validate
    
    Returns:
        Tuple of (is_valid, error_message, parsed_port)
    """
    try:
        port_num = int(port)
        
        if port_num < 1 or port_num > 65535:
            return False, "Port number must be between 1 and 65535", None
        
        return True, None, port_num
        
    except (ValueError, TypeError):
        return False, "Port must be a valid integer", None


def validate_timeout(timeout: Union[str, int, float]) -> Tuple[bool, Optional[str], Optional[float]]:
    """Validate timeout value.
    
    Args:
        timeout: Timeout value in seconds
    
    Returns:
        Tuple of (is_valid, error_message, parsed_timeout)
    """
    try:
        timeout_val = float(timeout)
        
        if timeout_val <= 0:
            return False, "Timeout must be greater than 0", None
        
        if timeout_val > 300:  # 5 minutes max
            return False, "Timeout cannot exceed 300 seconds", None
        
        return True, None, timeout_val
        
    except (ValueError, TypeError):
        return False, "Timeout must be a valid number", None


def validate_cache_ttl(ttl: Union[str, int]) -> Tuple[bool, Optional[str], Optional[int]]:
    """Validate cache time-to-live value.
    
    Args:
        ttl: TTL value in seconds
    
    Returns:
        Tuple of (is_valid, error_message, parsed_ttl)
    """
    try:
        ttl_val = int(ttl)
        
        if ttl_val < 0:
            return False, "Cache TTL cannot be negative", None
        
        if ttl_val > 86400:  # 24 hours max
            return False, "Cache TTL cannot exceed 86400 seconds (24 hours)", None
        
        return True, None, ttl_val
        
    except (ValueError, TypeError):
        return False, "Cache TTL must be a valid integer", None


def validate_log_level(level: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate logging level.
    
    Args:
        level: Log level string
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not level:
        return False, "Log level is required"
    
    if not isinstance(level, str):
        return False, "Log level must be a string"
    
    level = level.strip().upper()
    
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    if level not in valid_levels:
        return False, f"Log level must be one of: {', '.join(valid_levels)}"
    
    return True, None


def validate_refresh_interval(interval: Union[str, int]) -> Tuple[bool, Optional[str], Optional[int]]:
    """Validate auto-refresh interval.
    
    Args:
        interval: Refresh interval in seconds
    
    Returns:
        Tuple of (is_valid, error_message, parsed_interval)
    """
    try:
        interval_val = int(interval)
        
        if interval_val < 30:  # Minimum 30 seconds
            return False, "Refresh interval must be at least 30 seconds", None
        
        if interval_val > 3600:  # Maximum 1 hour
            return False, "Refresh interval cannot exceed 3600 seconds (1 hour)", None
        
        return True, None, interval_val
        
    except (ValueError, TypeError):
        return False, "Refresh interval must be a valid integer", None


def validate_file_path(file_path: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate file path format.
    
    Args:
        file_path: File path string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "File path is required"
    
    if not isinstance(file_path, str):
        return False, "File path must be a string"
    
    file_path = file_path.strip()
    
    if len(file_path) == 0:
        return False, "File path cannot be empty"
    
    # Check for invalid characters (varies by OS, but these are generally problematic)
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in invalid_chars:
        if char in file_path:
            return False, f"File path cannot contain '{char}'"
    
    # Check length (Windows has a 260 character limit for full paths)
    if len(file_path) > 250:
        return False, "File path is too long"
    
    return True, None


def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitize user input by removing potentially harmful characters.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        return ""
    
    # Remove control characters and limit length
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)
    sanitized = sanitized.strip()[:max_length]
    
    return sanitized