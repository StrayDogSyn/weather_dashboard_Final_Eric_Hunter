"""Data Formatters

Utilities for formatting weather data and other values for display.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
import math

from ..models.app_models import TemperatureUnit, WindSpeedUnit, PressureUnit


def format_temperature(
    temp: float,
    unit: TemperatureUnit = TemperatureUnit.CELSIUS,
    precision: int = 1,
    show_unit: bool = True
) -> str:
    """Format temperature with appropriate unit.
    
    Args:
        temp: Temperature value in Celsius
        unit: Target unit for display
        precision: Number of decimal places
        show_unit: Whether to include unit symbol
    
    Returns:
        Formatted temperature string
    """
    if unit == TemperatureUnit.FAHRENHEIT:
        temp = (temp * 9/5) + 32
    
    formatted = f"{temp:.{precision}f}"
    
    if show_unit:
        formatted += unit.symbol()
    
    return formatted


def format_wind_speed(
    speed: Optional[float],
    unit: WindSpeedUnit = WindSpeedUnit.METERS_PER_SECOND,
    precision: int = 1,
    show_unit: bool = True
) -> str:
    """Format wind speed with appropriate unit.
    
    Args:
        speed: Wind speed in m/s (None for unknown)
        unit: Target unit for display
        precision: Number of decimal places
        show_unit: Whether to include unit symbol
    
    Returns:
        Formatted wind speed string
    """
    if speed is None:
        return "N/A"
    
    # Convert from m/s to target unit
    if unit == WindSpeedUnit.KILOMETERS_PER_HOUR:
        speed = speed * 3.6
    elif unit == WindSpeedUnit.MILES_PER_HOUR:
        speed = speed * 2.237
    
    formatted = f"{speed:.{precision}f}"
    
    if show_unit:
        formatted += f" {unit.symbol()}"
    
    return formatted


def format_pressure(
    pressure: float,
    unit: PressureUnit = PressureUnit.HECTOPASCAL,
    precision: int = 1,
    show_unit: bool = True
) -> str:
    """Format atmospheric pressure with appropriate unit.
    
    Args:
        pressure: Pressure in hPa
        unit: Target unit for display
        precision: Number of decimal places
        show_unit: Whether to include unit symbol
    
    Returns:
        Formatted pressure string
    """
    # Convert from hPa to target unit
    if unit == PressureUnit.INCHES_MERCURY:
        pressure = pressure * 0.02953
    elif unit == PressureUnit.MILLIBARS:
        # hPa and mbar are equivalent
        pass
    
    formatted = f"{pressure:.{precision}f}"
    
    if show_unit:
        formatted += f" {unit.symbol()}"
    
    return formatted


def format_humidity(humidity: int, show_unit: bool = True) -> str:
    """Format humidity percentage.
    
    Args:
        humidity: Humidity percentage (0-100)
        show_unit: Whether to include % symbol
    
    Returns:
        Formatted humidity string
    """
    formatted = str(humidity)
    
    if show_unit:
        formatted += "%"
    
    return formatted


def format_percentage(
    value: Optional[float],
    precision: int = 0,
    show_unit: bool = True,
    multiply_by_100: bool = False
) -> str:
    """Format percentage value.
    
    Args:
        value: Percentage value (None for unknown)
        precision: Number of decimal places
        show_unit: Whether to include % symbol
        multiply_by_100: Whether to multiply by 100 (for 0-1 range values)
    
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "N/A"
    
    if multiply_by_100:
        value = value * 100
    
    formatted = f"{value:.{precision}f}"
    
    if show_unit:
        formatted += "%"
    
    return formatted


def format_distance(
    distance: Optional[float],
    unit: str = "km",
    precision: int = 1,
    show_unit: bool = True
) -> str:
    """Format distance with appropriate unit.
    
    Args:
        distance: Distance value in km (None for unknown)
        unit: Target unit ('km', 'mi', 'm')
        precision: Number of decimal places
        show_unit: Whether to include unit symbol
    
    Returns:
        Formatted distance string
    """
    if distance is None:
        return "N/A"
    
    # Convert from km to target unit
    if unit == "mi":
        distance = distance * 0.621371
    elif unit == "m":
        distance = distance * 1000
        precision = 0  # Meters are usually whole numbers
    
    formatted = f"{distance:.{precision}f}"
    
    if show_unit:
        formatted += f" {unit}"
    
    return formatted


def format_time(
    time: Optional[datetime],
    format_string: str = "%H:%M",
    default: str = "N/A"
) -> str:
    """Format time for display.
    
    Args:
        time: DateTime object (None for unknown)
        format_string: strftime format string
        default: Default value for None input
    
    Returns:
        Formatted time string
    """
    if time is None:
        return default
    
    return time.strftime(format_string)


def format_datetime(
    dt: Optional[datetime],
    format_string: str = "%Y-%m-%d %H:%M:%S",
    default: str = "N/A"
) -> str:
    """Format datetime for display.
    
    Args:
        dt: DateTime object (None for unknown)
        format_string: strftime format string
        default: Default value for None input
    
    Returns:
        Formatted datetime string
    """
    if dt is None:
        return default
    
    return dt.strftime(format_string)


def format_duration(
    duration: Optional[timedelta],
    precision: str = "seconds",
    show_units: bool = True
) -> str:
    """Format time duration for display.
    
    Args:
        duration: TimeDelta object (None for unknown)
        precision: Level of precision ('days', 'hours', 'minutes', 'seconds')
        show_units: Whether to include unit labels
    
    Returns:
        Formatted duration string
    """
    if duration is None:
        return "N/A"
    
    total_seconds = int(duration.total_seconds())
    
    if total_seconds < 0:
        return "0s" if show_units else "0"
    
    # Calculate components
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    # Format based on precision
    if precision == "days":
        if days > 0:
            return f"{days}d" if show_units else str(days)
        elif hours > 0:
            return f"{hours}h" if show_units else str(hours)
        elif minutes > 0:
            return f"{minutes}m" if show_units else str(minutes)
        else:
            return f"{seconds}s" if show_units else str(seconds)
    
    elif precision == "hours":
        if days > 0:
            total_hours = days * 24 + hours
            return f"{total_hours}h" if show_units else str(total_hours)
        elif hours > 0:
            return f"{hours}h" if show_units else str(hours)
        elif minutes > 0:
            return f"{minutes}m" if show_units else str(minutes)
        else:
            return f"{seconds}s" if show_units else str(seconds)
    
    elif precision == "minutes":
        if total_seconds >= 3600:  # 1 hour or more
            total_minutes = total_seconds // 60
            return f"{total_minutes}m" if show_units else str(total_minutes)
        elif minutes > 0:
            return f"{minutes}m" if show_units else str(minutes)
        else:
            return f"{seconds}s" if show_units else str(seconds)
    
    else:  # seconds
        return f"{total_seconds}s" if show_units else str(total_seconds)


def format_uv_index(uv_index: Optional[float]) -> str:
    """Format UV index with descriptive text.
    
    Args:
        uv_index: UV index value (None for unknown)
    
    Returns:
        Formatted UV index string with description
    """
    if uv_index is None:
        return "N/A"
    
    # Round to nearest integer
    uv_int = round(uv_index)
    
    # Get description
    if uv_int <= 2:
        description = "Low"
    elif uv_int <= 5:
        description = "Moderate"
    elif uv_int <= 7:
        description = "High"
    elif uv_int <= 10:
        description = "Very High"
    else:
        description = "Extreme"
    
    return f"{uv_int} ({description})"


def format_air_quality_index(aqi: Optional[int]) -> str:
    """Format Air Quality Index with descriptive text.
    
    Args:
        aqi: AQI value (None for unknown)
    
    Returns:
        Formatted AQI string with description
    """
    if aqi is None:
        return "N/A"
    
    # Get description based on AQI ranges
    if aqi <= 50:
        description = "Good"
    elif aqi <= 100:
        description = "Moderate"
    elif aqi <= 150:
        description = "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        description = "Unhealthy"
    elif aqi <= 300:
        description = "Very Unhealthy"
    else:
        description = "Hazardous"
    
    return f"{aqi} ({description})"


def format_wind_direction(degrees: Optional[int]) -> str:
    """Format wind direction from degrees to compass direction.
    
    Args:
        degrees: Wind direction in degrees (None for unknown)
    
    Returns:
        Compass direction string
    """
    if degrees is None:
        return "N/A"
    
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    
    # Normalize degrees to 0-360 range
    degrees = degrees % 360
    
    # Calculate index (each direction covers 22.5 degrees)
    index = round(degrees / 22.5) % 16
    
    return directions[index]


def format_coordinates(
    latitude: float,
    longitude: float,
    precision: int = 4
) -> str:
    """Format geographic coordinates.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        precision: Number of decimal places
    
    Returns:
        Formatted coordinates string
    """
    lat_dir = "N" if latitude >= 0 else "S"
    lon_dir = "E" if longitude >= 0 else "W"
    
    lat_abs = abs(latitude)
    lon_abs = abs(longitude)
    
    return f"{lat_abs:.{precision}f}°{lat_dir}, {lon_abs:.{precision}f}°{lon_dir}"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def format_number(
    value: Union[int, float],
    precision: Optional[int] = None,
    thousands_separator: str = ","
) -> str:
    """Format number with thousands separator.
    
    Args:
        value: Numeric value
        precision: Number of decimal places (None for auto)
        thousands_separator: Character to use for thousands separation
    
    Returns:
        Formatted number string
    """
    if precision is not None:
        formatted = f"{value:.{precision}f}"
    else:
        formatted = str(value)
    
    # Add thousands separator
    if thousands_separator and "." in formatted:
        integer_part, decimal_part = formatted.split(".")
        integer_part = f"{int(integer_part):,}".replace(",", thousands_separator)
        return f"{integer_part}.{decimal_part}"
    elif thousands_separator:
        return f"{int(value):,}".replace(",", thousands_separator)
    
    return formatted