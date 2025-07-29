"""API Response Parser

Handles parsing and validation of API responses from different weather services.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from dataclasses import dataclass
import json

from interfaces.weather_service_interface import IDataParser


@dataclass
class ParsedWeatherResponse:
    """Parsed weather response with standardized format."""
    success: bool
    data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    error_code: Optional[str]
    timestamp: datetime
    source: str
    raw_response: Optional[Dict[str, Any]]


@dataclass
class ParsedForecastResponse:
    """Parsed forecast response."""
    success: bool
    forecasts: List[Dict[str, Any]]
    error_message: Optional[str]
    error_code: Optional[str]
    timestamp: datetime
    source: str
    location: Optional[str]


class APIResponseParser(IDataParser):
    """Parser for API responses from weather services."""
    
    def __init__(self):
        """Initialize the API response parser."""
        self.logger = logging.getLogger(__name__)
        
        # Expected response structures for validation
        self.required_weather_fields = {
            'main': ['temp', 'humidity', 'pressure'],
            'weather': ['main', 'description'],
            'wind': ['speed'],
            'sys': ['country']
        }
        
        self.required_forecast_fields = {
            'list': [],  # Array of forecast items
            'city': ['name', 'country']
        }
    
    def parse(self, response: Union[str, Dict[str, Any]], response_type: str = 'weather') -> ParsedWeatherResponse:
        """Parse API response based on type.
        
        Args:
            response: Raw API response (JSON string or dict)
            response_type: Type of response ('weather', 'forecast', 'air_quality')
            
        Returns:
            ParsedWeatherResponse object
        """
        try:
            # Convert string response to dict if needed
            if isinstance(response, str):
                response_data = json.loads(response)
            else:
                response_data = response
            
            # Check for API error responses
            if 'cod' in response_data and str(response_data['cod']) != '200':
                return self._create_error_response(
                    error_message=response_data.get('message', 'API error'),
                    error_code=str(response_data.get('cod', 'unknown')),
                    raw_response=response_data
                )
            
            # Parse based on response type
            if response_type == 'weather':
                return self._parse_weather_response(response_data)
            elif response_type == 'forecast':
                return self._parse_forecast_response(response_data)
            elif response_type == 'air_quality':
                return self._parse_air_quality_response(response_data)
            else:
                return self._create_error_response(
                    error_message=f"Unknown response type: {response_type}",
                    error_code="INVALID_TYPE"
                )
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            return self._create_error_response(
                error_message="Invalid JSON response",
                error_code="JSON_ERROR"
            )
        except Exception as e:
            self.logger.error(f"Error parsing API response: {e}")
            return self._create_error_response(
                error_message=str(e),
                error_code="PARSE_ERROR"
            )
    
    def parse_forecast(self, response: Union[str, Dict[str, Any]]) -> ParsedForecastResponse:
        """Parse forecast API response.
        
        Args:
            response: Raw forecast API response
            
        Returns:
            ParsedForecastResponse object
        """
        try:
            # Convert string response to dict if needed
            if isinstance(response, str):
                response_data = json.loads(response)
            else:
                response_data = response
            
            # Check for API error responses
            if 'cod' in response_data and str(response_data['cod']) != '200':
                return ParsedForecastResponse(
                    success=False,
                    forecasts=[],
                    error_message=response_data.get('message', 'API error'),
                    error_code=str(response_data.get('cod', 'unknown')),
                    timestamp=datetime.now(timezone.utc),
                    source='openweathermap',
                    location=None
                )
            
            # Validate forecast response structure
            if not self._validate_forecast_structure(response_data):
                return ParsedForecastResponse(
                    success=False,
                    forecasts=[],
                    error_message="Invalid forecast response structure",
                    error_code="INVALID_STRUCTURE",
                    timestamp=datetime.now(timezone.utc),
                    source='openweathermap',
                    location=None
                )
            
            # Extract forecast data
            forecasts = self._extract_forecast_data(response_data)
            location = self._extract_location_from_forecast(response_data)
            
            return ParsedForecastResponse(
                success=True,
                forecasts=forecasts,
                error_message=None,
                error_code=None,
                timestamp=datetime.now(timezone.utc),
                source='openweathermap',
                location=location
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing forecast response: {e}")
            return ParsedForecastResponse(
                success=False,
                forecasts=[],
                error_message=str(e),
                error_code="PARSE_ERROR",
                timestamp=datetime.now(timezone.utc),
                source='openweathermap',
                location=None
            )
    
    def validate(self, data: Any) -> bool:
        """Validate parsed response data.
        
        Args:
            data: ParsedWeatherResponse to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        if not isinstance(data, ParsedWeatherResponse):
            return False
        
        # Check required fields
        if not hasattr(data, 'success') or not hasattr(data, 'timestamp'):
            return False
        
        # If successful, data should be present
        if data.success and not data.data:
            return False
        
        # If failed, error message should be present
        if not data.success and not data.error_message:
            return False
        
        return True
    
    def _parse_weather_response(self, response_data: Dict[str, Any]) -> ParsedWeatherResponse:
        """Parse current weather response."""
        # Validate response structure
        if not self._validate_weather_structure(response_data):
            return self._create_error_response(
                error_message="Invalid weather response structure",
                error_code="INVALID_STRUCTURE",
                raw_response=response_data
            )
        
        # Extract and normalize weather data
        normalized_data = self._normalize_weather_data(response_data)
        
        return ParsedWeatherResponse(
            success=True,
            data=normalized_data,
            error_message=None,
            error_code=None,
            timestamp=datetime.now(timezone.utc),
            source='openweathermap',
            raw_response=response_data
        )
    
    def _parse_forecast_response(self, response_data: Dict[str, Any]) -> ParsedWeatherResponse:
        """Parse forecast response."""
        # Validate response structure
        if not self._validate_forecast_structure(response_data):
            return self._create_error_response(
                error_message="Invalid forecast response structure",
                error_code="INVALID_STRUCTURE",
                raw_response=response_data
            )
        
        # Extract forecast data
        forecast_data = {
            'forecasts': self._extract_forecast_data(response_data),
            'location': self._extract_location_from_forecast(response_data),
            'count': len(response_data.get('list', []))
        }
        
        return ParsedWeatherResponse(
            success=True,
            data=forecast_data,
            error_message=None,
            error_code=None,
            timestamp=datetime.now(timezone.utc),
            source='openweathermap',
            raw_response=response_data
        )
    
    def _parse_air_quality_response(self, response_data: Dict[str, Any]) -> ParsedWeatherResponse:
        """Parse air quality response."""
        # Basic validation for air quality response
        if 'main' not in response_data or 'aqi' not in response_data['main']:
            return self._create_error_response(
                error_message="Invalid air quality response structure",
                error_code="INVALID_STRUCTURE",
                raw_response=response_data
            )
        
        # Normalize air quality data
        normalized_data = {
            'main': response_data['main'],
            'components': response_data.get('components', {}),
            'coord': response_data.get('coord', {}),
            'dt': response_data.get('dt')
        }
        
        return ParsedWeatherResponse(
            success=True,
            data=normalized_data,
            error_message=None,
            error_code=None,
            timestamp=datetime.now(timezone.utc),
            source='openweathermap',
            raw_response=response_data
        )
    
    def _validate_weather_structure(self, data: Dict[str, Any]) -> bool:
        """Validate weather response structure."""
        for section, fields in self.required_weather_fields.items():
            if section not in data:
                self.logger.warning(f"Missing section: {section}")
                return False
            
            section_data = data[section]
            if isinstance(section_data, list):
                if not section_data:  # Empty list
                    self.logger.warning(f"Empty section: {section}")
                    return False
                section_data = section_data[0]  # Check first item
            
            for field in fields:
                if field not in section_data:
                    self.logger.warning(f"Missing field {field} in section {section}")
                    return False
        
        return True
    
    def _validate_forecast_structure(self, data: Dict[str, Any]) -> bool:
        """Validate forecast response structure."""
        if 'list' not in data or not isinstance(data['list'], list):
            return False
        
        if not data['list']:  # Empty forecast list
            return False
        
        # Check first forecast item structure
        first_item = data['list'][0]
        required_fields = ['dt', 'main', 'weather']
        for field in required_fields:
            if field not in first_item:
                return False
        
        return True
    
    def _normalize_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize weather data to standard format."""
        normalized = {
            'main': data.get('main', {}),
            'weather': data.get('weather', []),
            'wind': data.get('wind', {}),
            'clouds': data.get('clouds', {}),
            'sys': data.get('sys', {}),
            'visibility': data.get('visibility'),
            'dt': data.get('dt'),
            'timezone': data.get('timezone'),
            'name': data.get('name'),
            'coord': data.get('coord', {})
        }
        
        # Add computed fields
        normalized['location'] = {
            'name': data.get('name', 'Unknown'),
            'country': data.get('sys', {}).get('country', ''),
            'coordinates': data.get('coord', {})
        }
        
        # Add timestamp information
        normalized['timestamps'] = {
            'current': data.get('dt'),
            'sunrise': data.get('sys', {}).get('sunrise'),
            'sunset': data.get('sys', {}).get('sunset')
        }
        
        return normalized
    
    def _extract_forecast_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and normalize forecast data."""
        forecasts = []
        
        for item in data.get('list', []):
            forecast = {
                'dt': item.get('dt'),
                'dt_txt': item.get('dt_txt'),
                'main': item.get('main', {}),
                'weather': item.get('weather', []),
                'wind': item.get('wind', {}),
                'clouds': item.get('clouds', {}),
                'visibility': item.get('visibility'),
                'pop': item.get('pop', 0),  # Probability of precipitation
                'rain': item.get('rain', {}),
                'snow': item.get('snow', {})
            }
            
            # Add formatted datetime
            if forecast['dt']:
                forecast['datetime'] = datetime.fromtimestamp(
                    forecast['dt'], tz=timezone.utc
                )
            
            forecasts.append(forecast)
        
        return forecasts
    
    def _extract_location_from_forecast(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract location information from forecast response."""
        city_data = data.get('city', {})
        if city_data:
            name = city_data.get('name', '')
            country = city_data.get('country', '')
            if name and country:
                return f"{name}, {country}"
            elif name:
                return name
        
        return None
    
    def _create_error_response(self, error_message: str, error_code: str, 
                             raw_response: Optional[Dict[str, Any]] = None) -> ParsedWeatherResponse:
        """Create error response object."""
        return ParsedWeatherResponse(
            success=False,
            data=None,
            error_message=error_message,
            error_code=error_code,
            timestamp=datetime.now(timezone.utc),
            source='openweathermap',
            raw_response=raw_response
        )


class WeatherAPIErrorHandler:
    """Handler for weather API specific errors."""
    
    def __init__(self):
        """Initialize error handler."""
        self.logger = logging.getLogger(__name__)
        
        # Common API error codes and their meanings
        self.error_codes = {
            '400': 'Bad Request - Invalid parameters',
            '401': 'Unauthorized - Invalid API key',
            '404': 'Not Found - Location not found',
            '429': 'Too Many Requests - Rate limit exceeded',
            '500': 'Internal Server Error - API server error',
            '502': 'Bad Gateway - API server unavailable',
            '503': 'Service Unavailable - API temporarily unavailable'
        }
    
    def handle_error(self, error_code: str, error_message: str) -> Dict[str, str]:
        """Handle API error and provide user-friendly message.
        
        Args:
            error_code: API error code
            error_message: Original error message
            
        Returns:
            Dictionary with user-friendly error information
        """
        user_message = self.error_codes.get(error_code, error_message)
        
        # Provide specific guidance based on error type
        guidance = self._get_error_guidance(error_code)
        
        return {
            'code': error_code,
            'message': user_message,
            'guidance': guidance,
            'original_message': error_message
        }
    
    def _get_error_guidance(self, error_code: str) -> str:
        """Get guidance for specific error codes."""
        guidance_map = {
            '401': 'Please check your API key configuration',
            '404': 'Please verify the location name and try again',
            '429': 'Please wait a moment before making another request',
            '500': 'Please try again later',
            '502': 'Weather service is temporarily unavailable',
            '503': 'Weather service is under maintenance'
        }
        
        return guidance_map.get(error_code, 'Please try again or contact support')