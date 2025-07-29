"""Validator Service

Provides comprehensive data validation for weather application.
Separates validation logic from UI components and business logic.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_value: Any = None
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


class BaseValidator(ABC):
    """Abstract base class for validators."""
    
    def __init__(self):
        """Initialize the validator."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """Validate a value.
        
        Args:
            value: Value to validate
            **kwargs: Additional validation parameters
            
        Returns:
            ValidationResult object
        """
        pass
    
    def _create_result(self, is_valid: bool = True, sanitized_value: Any = None) -> ValidationResult:
        """Create a validation result."""
        return ValidationResult(
            is_valid=is_valid,
            errors=[],
            warnings=[],
            sanitized_value=sanitized_value
        )


class LocationValidator(BaseValidator):
    """Validator for location data."""
    
    def __init__(self):
        """Initialize the location validator."""
        super().__init__()
        self.city_pattern = re.compile(r'^[a-zA-Z\s\-\'\u00C0-\u017F]+$')
        self.coordinate_pattern = re.compile(r'^-?\d+\.?\d*$')
    
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """Validate location input.
        
        Args:
            value: Location string or coordinates
            **kwargs: Additional parameters (validation_type)
            
        Returns:
            ValidationResult object
        """
        result = self._create_result()
        
        if not value:
            result.add_error("Location cannot be empty")
            return result
        
        validation_type = kwargs.get('validation_type', 'auto')
        
        if validation_type == 'coordinates':
            return self._validate_coordinates(value, result)
        elif validation_type == 'city':
            return self._validate_city_name(value, result)
        else:
            # Auto-detect type
            return self._validate_auto(value, result)
    
    def _validate_coordinates(self, value: Any, result: ValidationResult) -> ValidationResult:
        """Validate coordinate input."""
        try:
            if isinstance(value, str):
                # Parse coordinate string "lat,lon"
                if ',' in value:
                    parts = [part.strip() for part in value.split(',')]
                    if len(parts) != 2:
                        result.add_error("Coordinates must be in format 'latitude,longitude'")
                        return result
                    
                    try:
                        lat, lon = float(parts[0]), float(parts[1])
                    except ValueError:
                        result.add_error("Coordinates must be valid numbers")
                        return result
                else:
                    result.add_error("Coordinates must be in format 'latitude,longitude'")
                    return result
            elif isinstance(value, (list, tuple)) and len(value) == 2:
                try:
                    lat, lon = float(value[0]), float(value[1])
                except (ValueError, TypeError):
                    result.add_error("Coordinates must be valid numbers")
                    return result
            else:
                result.add_error("Invalid coordinate format")
                return result
            
            # Validate coordinate ranges
            if not (-90 <= lat <= 90):
                result.add_error(f"Latitude {lat} is out of range (-90 to 90)")
            
            if not (-180 <= lon <= 180):
                result.add_error(f"Longitude {lon} is out of range (-180 to 180)")
            
            if result.is_valid:
                result.sanitized_value = {'lat': lat, 'lon': lon, 'type': 'coordinates'}
            
            return result
        except Exception as e:
            self.logger.error(f"Error validating coordinates: {e}")
            result.add_error("Error processing coordinates")
            return result
    
    def _validate_city_name(self, value: Any, result: ValidationResult) -> ValidationResult:
        """Validate city name input."""
        try:
            if not isinstance(value, str):
                result.add_error("City name must be a string")
                return result
            
            # Clean and validate
            city = value.strip()
            
            if len(city) < 2:
                result.add_error("City name must be at least 2 characters long")
                return result
            
            if len(city) > 100:
                result.add_error("City name must be less than 100 characters")
                return result
            
            # Check for valid characters (including international characters)
            if not self.city_pattern.match(city):
                result.add_error("City name contains invalid characters")
                return result
            
            # Check for common patterns
            if city.lower() in ['test', 'example', 'null', 'undefined']:
                result.add_warning("City name appears to be a placeholder")
            
            # Parse city, country if comma-separated
            if ',' in city:
                parts = [part.strip() for part in city.split(',')]
                if len(parts) == 2:
                    city_name, country = parts
                    if len(city_name) < 2:
                        result.add_error("City name part must be at least 2 characters")
                        return result
                    
                    result.sanitized_value = {
                        'city': city_name,
                        'country': country,
                        'type': 'city_country'
                    }
                else:
                    result.add_error("Invalid city,country format")
                    return result
            else:
                result.sanitized_value = {
                    'city': city,
                    'country': None,
                    'type': 'city'
                }
            
            return result
        except Exception as e:
            self.logger.error(f"Error validating city name: {e}")
            result.add_error("Error processing city name")
            return result
    
    def _validate_auto(self, value: Any, result: ValidationResult) -> ValidationResult:
        """Auto-detect and validate location type."""
        if not isinstance(value, str):
            result.add_error("Location must be a string")
            return result
        
        value = value.strip()
        
        # Check if it looks like coordinates
        if ',' in value and len(value.split(',')) == 2:
            parts = value.split(',')
            if all(self.coordinate_pattern.match(part.strip()) for part in parts):
                return self._validate_coordinates(value, result)
        
        # Otherwise treat as city name
        return self._validate_city_name(value, result)


class WeatherDataValidator(BaseValidator):
    """Validator for weather data."""
    
    def __init__(self):
        """Initialize the weather data validator."""
        super().__init__()
        self.temperature_ranges = {
            'celsius': (-100, 60),
            'fahrenheit': (-148, 140),
            'kelvin': (173, 333)
        }
    
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """Validate weather data.
        
        Args:
            value: Weather data dictionary
            **kwargs: Additional parameters
            
        Returns:
            ValidationResult object
        """
        result = self._create_result()
        
        if not isinstance(value, dict):
            result.add_error("Weather data must be a dictionary")
            return result
        
        sanitized_data = {}
        
        # Validate temperature
        temp_result = self.validate_temperature(
            value.get('temperature'),
            kwargs.get('temp_unit', 'celsius')
        )
        if not temp_result.is_valid:
            result.errors.extend(temp_result.errors)
        else:
            sanitized_data['temperature'] = temp_result.sanitized_value
        
        # Validate humidity
        humidity_result = self.validate_humidity(value.get('humidity'))
        if not humidity_result.is_valid:
            result.errors.extend(humidity_result.errors)
        else:
            sanitized_data['humidity'] = humidity_result.sanitized_value
        
        # Validate pressure
        pressure_result = self.validate_pressure(value.get('pressure'))
        if not pressure_result.is_valid:
            result.errors.extend(pressure_result.errors)
        else:
            sanitized_data['pressure'] = pressure_result.sanitized_value
        
        # Validate wind speed
        wind_result = self.validate_wind_speed(value.get('wind_speed'))
        if not wind_result.is_valid:
            result.errors.extend(wind_result.errors)
        else:
            sanitized_data['wind_speed'] = wind_result.sanitized_value
        
        # Validate wind direction
        wind_dir_result = self.validate_wind_direction(value.get('wind_direction'))
        if not wind_dir_result.is_valid:
            result.errors.extend(wind_dir_result.errors)
        else:
            sanitized_data['wind_direction'] = wind_dir_result.sanitized_value
        
        # Validate UV index
        uv_result = self.validate_uv_index(value.get('uv_index'))
        if not uv_result.is_valid:
            result.errors.extend(uv_result.errors)
        else:
            sanitized_data['uv_index'] = uv_result.sanitized_value
        
        # Validate visibility
        vis_result = self.validate_visibility(value.get('visibility'))
        if not vis_result.is_valid:
            result.errors.extend(vis_result.errors)
        else:
            sanitized_data['visibility'] = vis_result.sanitized_value
        
        if result.errors:
            result.is_valid = False
        else:
            result.sanitized_value = sanitized_data
        
        return result
    
    def validate_temperature(self, value: Any, unit: str = 'celsius') -> ValidationResult:
        """Validate temperature value."""
        result = self._create_result()
        
        if value is None:
            result.add_error("Temperature cannot be None")
            return result
        
        try:
            temp = float(value)
        except (ValueError, TypeError):
            result.add_error("Temperature must be a number")
            return result
        
        min_temp, max_temp = self.temperature_ranges.get(unit.lower(), (-100, 60))
        
        if not (min_temp <= temp <= max_temp):
            result.add_error(f"Temperature {temp}°{unit[0].upper()} is out of reasonable range ({min_temp} to {max_temp})")
            return result
        
        # Add warnings for extreme temperatures
        if unit.lower() == 'celsius':
            if temp < -40:
                result.add_warning("Extremely cold temperature detected")
            elif temp > 45:
                result.add_warning("Extremely hot temperature detected")
        
        result.sanitized_value = round(temp, 1)
        return result
    
    def validate_humidity(self, value: Any) -> ValidationResult:
        """Validate humidity percentage."""
        result = self._create_result()
        
        if value is None:
            result.add_error("Humidity cannot be None")
            return result
        
        try:
            humidity = float(value)
        except (ValueError, TypeError):
            result.add_error("Humidity must be a number")
            return result
        
        if not (0 <= humidity <= 100):
            result.add_error(f"Humidity {humidity}% is out of range (0-100%)")
            return result
        
        result.sanitized_value = round(humidity)
        return result
    
    def validate_pressure(self, value: Any) -> ValidationResult:
        """Validate atmospheric pressure."""
        result = self._create_result()
        
        if value is None:
            result.add_error("Pressure cannot be None")
            return result
        
        try:
            pressure = float(value)
        except (ValueError, TypeError):
            result.add_error("Pressure must be a number")
            return result
        
        if not (800 <= pressure <= 1200):
            result.add_error(f"Pressure {pressure} hPa is out of reasonable range (800-1200 hPa)")
            return result
        
        # Add warnings for extreme pressure
        if pressure < 950:
            result.add_warning("Very low atmospheric pressure detected")
        elif pressure > 1050:
            result.add_warning("Very high atmospheric pressure detected")
        
        result.sanitized_value = round(pressure, 1)
        return result
    
    def validate_wind_speed(self, value: Any) -> ValidationResult:
        """Validate wind speed."""
        result = self._create_result()
        
        if value is None:
            result.add_error("Wind speed cannot be None")
            return result
        
        try:
            wind_speed = float(value)
        except (ValueError, TypeError):
            result.add_error("Wind speed must be a number")
            return result
        
        if wind_speed < 0:
            result.add_error("Wind speed cannot be negative")
            return result
        
        if wind_speed > 150:  # Extreme hurricane speeds
            result.add_error(f"Wind speed {wind_speed} m/s is unreasonably high")
            return result
        
        # Add warnings for high wind speeds
        if wind_speed > 25:  # Hurricane force
            result.add_warning("Hurricane force winds detected")
        elif wind_speed > 17:  # Gale force
            result.add_warning("Gale force winds detected")
        
        result.sanitized_value = round(wind_speed, 1)
        return result
    
    def validate_wind_direction(self, value: Any) -> ValidationResult:
        """Validate wind direction in degrees."""
        result = self._create_result()
        
        if value is None:
            result.add_error("Wind direction cannot be None")
            return result
        
        try:
            direction = float(value)
        except (ValueError, TypeError):
            result.add_error("Wind direction must be a number")
            return result
        
        # Normalize to 0-360 range
        direction = direction % 360
        
        result.sanitized_value = round(direction)
        return result
    
    def validate_uv_index(self, value: Any) -> ValidationResult:
        """Validate UV index."""
        result = self._create_result()
        
        if value is None:
            # UV index is optional
            result.sanitized_value = None
            return result
        
        try:
            uv_index = float(value)
        except (ValueError, TypeError):
            result.add_error("UV index must be a number")
            return result
        
        if uv_index < 0:
            result.add_error("UV index cannot be negative")
            return result
        
        if uv_index > 20:
            result.add_error(f"UV index {uv_index} is unreasonably high")
            return result
        
        # Add warnings for high UV
        if uv_index > 10:
            result.add_warning("Extreme UV levels detected")
        elif uv_index > 7:
            result.add_warning("Very high UV levels detected")
        
        result.sanitized_value = round(uv_index, 1)
        return result
    
    def validate_visibility(self, value: Any) -> ValidationResult:
        """Validate visibility distance."""
        result = self._create_result()
        
        if value is None:
            result.add_error("Visibility cannot be None")
            return result
        
        try:
            visibility = float(value)
        except (ValueError, TypeError):
            result.add_error("Visibility must be a number")
            return result
        
        if visibility < 0:
            result.add_error("Visibility cannot be negative")
            return result
        
        if visibility > 50:  # 50km is very good visibility
            result.add_warning("Unusually high visibility detected")
        elif visibility < 1:  # Less than 1km is poor visibility
            result.add_warning("Poor visibility conditions detected")
        
        result.sanitized_value = round(visibility, 1)
        return result


class APIResponseValidator(BaseValidator):
    """Validator for API response data."""
    
    def __init__(self):
        """Initialize the API response validator."""
        super().__init__()
    
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """Validate API response structure.
        
        Args:
            value: API response data
            **kwargs: Additional parameters (api_type)
            
        Returns:
            ValidationResult object
        """
        result = self._create_result()
        
        if not isinstance(value, dict):
            result.add_error("API response must be a dictionary")
            return result
        
        api_type = kwargs.get('api_type', 'openweathermap')
        
        if api_type == 'openweathermap':
            return self._validate_openweathermap_response(value, result)
        else:
            result.add_error(f"Unknown API type: {api_type}")
            return result
    
    def _validate_openweathermap_response(self, data: Dict[str, Any], 
                                        result: ValidationResult) -> ValidationResult:
        """Validate OpenWeatherMap API response."""
        required_fields = ['main', 'weather', 'wind', 'name']
        
        for field in required_fields:
            if field not in data:
                result.add_error(f"Missing required field: {field}")
        
        if result.has_errors():
            return result
        
        # Validate main weather data
        main_data = data.get('main', {})
        required_main_fields = ['temp', 'humidity', 'pressure']
        
        for field in required_main_fields:
            if field not in main_data:
                result.add_error(f"Missing required main field: {field}")
        
        # Validate weather array
        weather_data = data.get('weather', [])
        if not isinstance(weather_data, list) or len(weather_data) == 0:
            result.add_error("Weather data must be a non-empty array")
        else:
            weather_item = weather_data[0]
            required_weather_fields = ['main', 'description']
            for field in required_weather_fields:
                if field not in weather_item:
                    result.add_error(f"Missing required weather field: {field}")
        
        # Validate wind data
        wind_data = data.get('wind', {})
        if 'speed' not in wind_data:
            result.add_error("Missing wind speed data")
        
        # Validate location name
        if not data.get('name'):
            result.add_error("Missing location name")
        
        if not result.has_errors():
            result.sanitized_value = data
        
        return result


class ConfigValidator(BaseValidator):
    """Validator for configuration data."""
    
    def __init__(self):
        """Initialize the config validator."""
        super().__init__()
    
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """Validate configuration data.
        
        Args:
            value: Configuration dictionary
            **kwargs: Additional parameters
            
        Returns:
            ValidationResult object
        """
        result = self._create_result()
        
        if not isinstance(value, dict):
            result.add_error("Configuration must be a dictionary")
            return result
        
        sanitized_config = {}
        
        # Validate API key
        api_key = value.get('api_key')
        if api_key:
            if not isinstance(api_key, str) or len(api_key) < 16:
                result.add_error("API key must be at least 16 characters")
            elif not api_key.replace('-', '').isalnum():
                result.add_error("API key contains invalid characters")
            else:
                sanitized_config['api_key'] = api_key.strip()
        
        # Validate units
        units = value.get('units', 'metric')
        valid_units = ['metric', 'imperial', 'kelvin']
        if units not in valid_units:
            result.add_error(f"Units must be one of: {', '.join(valid_units)}")
        else:
            sanitized_config['units'] = units
        
        # Validate refresh interval
        refresh_interval = value.get('refresh_interval', 300)
        try:
            refresh_interval = int(refresh_interval)
            if refresh_interval < 60:
                result.add_warning("Refresh interval less than 60 seconds may exceed API limits")
            elif refresh_interval > 3600:
                result.add_warning("Refresh interval greater than 1 hour may provide stale data")
            sanitized_config['refresh_interval'] = refresh_interval
        except (ValueError, TypeError):
            result.add_error("Refresh interval must be a number")
        
        # Validate cache duration
        cache_duration = value.get('cache_duration', 300)
        try:
            cache_duration = int(cache_duration)
            if cache_duration < 0:
                result.add_error("Cache duration cannot be negative")
            sanitized_config['cache_duration'] = cache_duration
        except (ValueError, TypeError):
            result.add_error("Cache duration must be a number")
        
        if not result.has_errors():
            result.sanitized_value = sanitized_config
        
        return result


class ValidatorService:
    """Main validator service that combines all validators."""
    
    def __init__(self):
        """Initialize the validator service."""
        self.location = LocationValidator()
        self.weather_data = WeatherDataValidator()
        self.api_response = APIResponseValidator()
        self.config = ConfigValidator()
        self.logger = logging.getLogger(__name__)
    
    def validate_search_input(self, search_input: str) -> ValidationResult:
        """Validate user search input.
        
        Args:
            search_input: User's search input
            
        Returns:
            ValidationResult object
        """
        return self.location.validate(search_input)
    
    def validate_weather_response(self, response_data: Dict[str, Any], 
                                api_type: str = 'openweathermap') -> ValidationResult:
        """Validate weather API response.
        
        Args:
            response_data: API response data
            api_type: Type of weather API
            
        Returns:
            ValidationResult object
        """
        # First validate the API response structure
        api_result = self.api_response.validate(response_data, api_type=api_type)
        if not api_result.is_valid:
            return api_result
        
        # Then validate the weather data values
        weather_data = self._extract_weather_data(response_data, api_type)
        return self.weather_data.validate(weather_data)
    
    def validate_app_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Validate application configuration.
        
        Args:
            config_data: Configuration data
            
        Returns:
            ValidationResult object
        """
        return self.config.validate(config_data)
    
    def validate_batch(self, validations: List[Tuple[Any, str, Dict[str, Any]]]) -> Dict[str, ValidationResult]:
        """Validate multiple items in batch.
        
        Args:
            validations: List of (value, validator_type, kwargs) tuples
            
        Returns:
            Dictionary of validation results
        """
        results = {}
        
        for i, (value, validator_type, kwargs) in enumerate(validations):
            try:
                if validator_type == 'location':
                    result = self.location.validate(value, **kwargs)
                elif validator_type == 'weather_data':
                    result = self.weather_data.validate(value, **kwargs)
                elif validator_type == 'api_response':
                    result = self.api_response.validate(value, **kwargs)
                elif validator_type == 'config':
                    result = self.config.validate(value, **kwargs)
                else:
                    result = ValidationResult(False, [f"Unknown validator type: {validator_type}"], [])
                
                results[f"validation_{i}"] = result
            except Exception as e:
                self.logger.error(f"Error in batch validation {i}: {e}")
                results[f"validation_{i}"] = ValidationResult(
                    False, [f"Validation error: {str(e)}"], []
                )
        
        return results
    
    def _extract_weather_data(self, response_data: Dict[str, Any], 
                            api_type: str) -> Dict[str, Any]:
        """Extract weather data from API response for validation.
        
        Args:
            response_data: API response data
            api_type: Type of weather API
            
        Returns:
            Extracted weather data dictionary
        """
        if api_type == 'openweathermap':
            main = response_data.get('main', {})
            wind = response_data.get('wind', {})
            
            return {
                'temperature': main.get('temp'),
                'humidity': main.get('humidity'),
                'pressure': main.get('pressure'),
                'wind_speed': wind.get('speed'),
                'wind_direction': wind.get('deg'),
                'visibility': response_data.get('visibility', 0) / 1000,  # Convert to km
                'uv_index': None  # Not included in basic weather response
            }
        
        return {}