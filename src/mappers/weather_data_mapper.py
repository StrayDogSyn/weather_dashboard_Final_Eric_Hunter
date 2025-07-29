"""Weather Data Mapper

Handles mapping and transformation between different weather data models.
Provides conversion between API responses, internal models, and UI representations.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import json

from processors.weather_processor import ProcessedWeatherData, ProcessedAirQualityData


@dataclass
class UIWeatherModel:
    """Weather data model optimized for UI display."""
    # Basic display data
    temperature_display: str
    condition_display: str
    location_display: str
    icon: str
    
    # Detailed information
    feels_like_display: str
    humidity_display: str
    pressure_display: str
    wind_display: str
    visibility_display: str
    uv_display: str
    
    # Status information
    comfort_level: str
    alerts: List[str]
    recommendations: List[str]
    
    # Metadata
    last_updated: str
    data_source: str
    is_current: bool


@dataclass
class APIWeatherModel:
    """Weather data model for API communication."""
    location: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: float
    wind_speed: float
    wind_direction: int
    visibility: float
    condition: str
    description: str
    icon_code: str
    timestamp: int
    sunrise: Optional[int]
    sunset: Optional[int]
    country: str
    coordinates: Dict[str, float]


@dataclass
class StorageWeatherModel:
    """Weather data model for storage/caching."""
    id: str
    location: str
    data: Dict[str, Any]
    timestamp: datetime
    expiry: datetime
    source: str
    version: str


class WeatherDataMapper:
    """Mapper for weather data transformations."""
    
    def __init__(self):
        """Initialize the weather data mapper."""
        self.logger = logging.getLogger(__name__)
        self.version = "1.0.0"
    
    def to_ui_model(self, processed_data: ProcessedWeatherData) -> UIWeatherModel:
        """Convert processed weather data to UI model.
        
        Args:
            processed_data: Processed weather data
            
        Returns:
            UI-optimized weather model
        """
        try:
            return UIWeatherModel(
                temperature_display=processed_data.temperature_formatted,
                condition_display=processed_data.description,
                location_display=f"{processed_data.location}, {processed_data.country}",
                icon=processed_data.condition_icon,
                feels_like_display=f"Feels like {processed_data.feels_like_formatted}",
                humidity_display=f"{processed_data.humidity}%",
                pressure_display=processed_data.pressure_formatted,
                wind_display=f"{processed_data.wind_speed_formatted} {processed_data.wind_direction_text}",
                visibility_display=processed_data.visibility_formatted,
                uv_display=processed_data.uv_index_description,
                comfort_level=processed_data.comfort_level,
                alerts=processed_data.weather_alerts,
                recommendations=processed_data.recommendations,
                last_updated=processed_data.timestamp.strftime("%H:%M"),
                data_source="OpenWeatherMap",
                is_current=True
            )
        except Exception as e:
            self.logger.error(f"Error mapping to UI model: {e}")
            raise
    
    def to_api_model(self, raw_data: Dict[str, Any]) -> APIWeatherModel:
        """Convert raw API data to API model.
        
        Args:
            raw_data: Raw API response data
            
        Returns:
            API weather model
        """
        try:
            main = raw_data.get('main', {})
            weather = raw_data.get('weather', [{}])[0]
            wind = raw_data.get('wind', {})
            sys_data = raw_data.get('sys', {})
            coord = raw_data.get('coord', {})
            
            return APIWeatherModel(
                location=raw_data.get('name', 'Unknown'),
                temperature=main.get('temp', 0),
                feels_like=main.get('feels_like', 0),
                humidity=main.get('humidity', 0),
                pressure=main.get('pressure', 0),
                wind_speed=wind.get('speed', 0),
                wind_direction=wind.get('deg', 0),
                visibility=raw_data.get('visibility', 0),
                condition=weather.get('main', ''),
                description=weather.get('description', ''),
                icon_code=weather.get('icon', ''),
                timestamp=raw_data.get('dt', 0),
                sunrise=sys_data.get('sunrise'),
                sunset=sys_data.get('sunset'),
                country=sys_data.get('country', ''),
                coordinates={
                    'lat': coord.get('lat', 0),
                    'lon': coord.get('lon', 0)
                }
            )
        except Exception as e:
            self.logger.error(f"Error mapping to API model: {e}")
            raise
    
    def to_storage_model(self, processed_data: ProcessedWeatherData, 
                        location_id: str) -> StorageWeatherModel:
        """Convert processed data to storage model.
        
        Args:
            processed_data: Processed weather data
            location_id: Unique identifier for the location
            
        Returns:
            Storage weather model
        """
        try:
            # Convert processed data to dictionary for storage
            data_dict = {
                'temperature': processed_data.temperature,
                'feels_like': processed_data.feels_like,
                'humidity': processed_data.humidity,
                'pressure': processed_data.pressure,
                'wind_speed': processed_data.wind_speed,
                'wind_direction': processed_data.wind_direction,
                'visibility': processed_data.visibility,
                'uv_index': processed_data.uv_index,
                'condition': processed_data.condition,
                'description': processed_data.description,
                'location': processed_data.location,
                'country': processed_data.country,
                'sunrise': processed_data.sunrise.isoformat() if processed_data.sunrise else None,
                'sunset': processed_data.sunset.isoformat() if processed_data.sunset else None,
                'comfort_level': processed_data.comfort_level,
                'alerts': processed_data.weather_alerts,
                'recommendations': processed_data.recommendations
            }
            
            # Calculate expiry (1 hour from now)
            expiry = datetime.now(timezone.utc).replace(microsecond=0)
            expiry = expiry.replace(hour=expiry.hour + 1)
            
            return StorageWeatherModel(
                id=location_id,
                location=processed_data.location,
                data=data_dict,
                timestamp=processed_data.timestamp,
                expiry=expiry,
                source="openweathermap",
                version=self.version
            )
        except Exception as e:
            self.logger.error(f"Error mapping to storage model: {e}")
            raise
    
    def from_storage_model(self, storage_model: StorageWeatherModel) -> ProcessedWeatherData:
        """Convert storage model back to processed data.
        
        Args:
            storage_model: Storage weather model
            
        Returns:
            Processed weather data
        """
        try:
            data = storage_model.data
            
            # Parse datetime strings back to datetime objects
            sunrise = None
            sunset = None
            if data.get('sunrise'):
                sunrise = datetime.fromisoformat(data['sunrise'])
            if data.get('sunset'):
                sunset = datetime.fromisoformat(data['sunset'])
            
            return ProcessedWeatherData(
                temperature=data.get('temperature', 0),
                temperature_formatted=f"{data.get('temperature', 0):.1f}°C",
                feels_like=data.get('feels_like', 0),
                feels_like_formatted=f"{data.get('feels_like', 0):.1f}°C",
                humidity=data.get('humidity', 0),
                pressure=data.get('pressure', 0),
                pressure_formatted=f"{data.get('pressure', 0):.0f} hPa",
                wind_speed=data.get('wind_speed', 0),
                wind_speed_formatted=f"{data.get('wind_speed', 0):.1f} m/s",
                wind_direction=data.get('wind_direction', 0),
                wind_direction_text=self._get_wind_direction_text(data.get('wind_direction', 0)),
                visibility=data.get('visibility', 0),
                visibility_formatted=f"{data.get('visibility', 0):.1f} km",
                uv_index=data.get('uv_index'),
                uv_index_description=self._get_uv_description(data.get('uv_index')),
                condition=data.get('condition', ''),
                condition_icon=self._get_condition_icon(data.get('condition', '')),
                description=data.get('description', ''),
                timestamp=storage_model.timestamp,
                location=data.get('location', ''),
                country=data.get('country', ''),
                sunrise=sunrise,
                sunset=sunset,
                temperature_trend="Stable",  # Default value
                comfort_level=data.get('comfort_level', 'Unknown'),
                weather_alerts=data.get('alerts', []),
                recommendations=data.get('recommendations', [])
            )
        except Exception as e:
            self.logger.error(f"Error mapping from storage model: {e}")
            raise
    
    def to_json(self, data: Union[UIWeatherModel, APIWeatherModel, StorageWeatherModel]) -> str:
        """Convert weather model to JSON string.
        
        Args:
            data: Weather model to convert
            
        Returns:
            JSON string representation
        """
        try:
            if isinstance(data, StorageWeatherModel):
                # Handle datetime serialization for storage model
                data_dict = asdict(data)
                data_dict['timestamp'] = data.timestamp.isoformat()
                data_dict['expiry'] = data.expiry.isoformat()
                return json.dumps(data_dict, indent=2)
            else:
                return json.dumps(asdict(data), indent=2)
        except Exception as e:
            self.logger.error(f"Error converting to JSON: {e}")
            raise
    
    def from_json(self, json_str: str, model_type: str) -> Union[UIWeatherModel, APIWeatherModel, StorageWeatherModel]:
        """Convert JSON string to weather model.
        
        Args:
            json_str: JSON string to convert
            model_type: Type of model ('ui', 'api', 'storage')
            
        Returns:
            Weather model instance
        """
        try:
            data = json.loads(json_str)
            
            if model_type == 'ui':
                return UIWeatherModel(**data)
            elif model_type == 'api':
                return APIWeatherModel(**data)
            elif model_type == 'storage':
                # Handle datetime parsing for storage model
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                data['expiry'] = datetime.fromisoformat(data['expiry'])
                return StorageWeatherModel(**data)
            else:
                raise ValueError(f"Unknown model type: {model_type}")
        except Exception as e:
            self.logger.error(f"Error converting from JSON: {e}")
            raise
    
    def transform_for_export(self, processed_data: ProcessedWeatherData, 
                           export_format: str = 'csv') -> Dict[str, Any]:
        """Transform processed data for export.
        
        Args:
            processed_data: Processed weather data
            export_format: Export format ('csv', 'xml', 'json')
            
        Returns:
            Transformed data for export
        """
        try:
            base_data = {
                'Location': f"{processed_data.location}, {processed_data.country}",
                'Temperature_C': processed_data.temperature,
                'Feels_Like_C': processed_data.feels_like,
                'Humidity_Percent': processed_data.humidity,
                'Pressure_hPa': processed_data.pressure,
                'Wind_Speed_ms': processed_data.wind_speed,
                'Wind_Direction_Deg': processed_data.wind_direction,
                'Wind_Direction_Text': processed_data.wind_direction_text,
                'Visibility_km': processed_data.visibility,
                'UV_Index': processed_data.uv_index,
                'Condition': processed_data.condition,
                'Description': processed_data.description,
                'Comfort_Level': processed_data.comfort_level,
                'Timestamp': processed_data.timestamp.isoformat(),
                'Sunrise': processed_data.sunrise.isoformat() if processed_data.sunrise else None,
                'Sunset': processed_data.sunset.isoformat() if processed_data.sunset else None
            }
            
            if export_format == 'csv':
                # Flatten lists for CSV
                base_data['Alerts'] = '; '.join(processed_data.weather_alerts)
                base_data['Recommendations'] = '; '.join(processed_data.recommendations)
            else:
                # Keep lists for JSON/XML
                base_data['Alerts'] = processed_data.weather_alerts
                base_data['Recommendations'] = processed_data.recommendations
            
            return base_data
        except Exception as e:
            self.logger.error(f"Error transforming for export: {e}")
            raise
    
    def create_summary_model(self, weather_data_list: List[ProcessedWeatherData]) -> Dict[str, Any]:
        """Create summary model from multiple weather data points.
        
        Args:
            weather_data_list: List of processed weather data
            
        Returns:
            Summary model with aggregated information
        """
        try:
            if not weather_data_list:
                return {}
            
            temperatures = [data.temperature for data in weather_data_list]
            humidity_values = [data.humidity for data in weather_data_list]
            pressure_values = [data.pressure for data in weather_data_list]
            
            return {
                'location_count': len(set(data.location for data in weather_data_list)),
                'temperature_stats': {
                    'min': min(temperatures),
                    'max': max(temperatures),
                    'avg': sum(temperatures) / len(temperatures)
                },
                'humidity_stats': {
                    'min': min(humidity_values),
                    'max': max(humidity_values),
                    'avg': sum(humidity_values) / len(humidity_values)
                },
                'pressure_stats': {
                    'min': min(pressure_values),
                    'max': max(pressure_values),
                    'avg': sum(pressure_values) / len(pressure_values)
                },
                'common_conditions': self._get_common_conditions(weather_data_list),
                'alert_summary': self._get_alert_summary(weather_data_list),
                'last_updated': max(data.timestamp for data in weather_data_list).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error creating summary model: {e}")
            raise
    
    def _get_wind_direction_text(self, degrees: int) -> str:
        """Convert wind direction degrees to text."""
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def _get_uv_description(self, uv_index: Optional[float]) -> str:
        """Get UV index description."""
        if uv_index is None:
            return "Unknown"
        
        if uv_index <= 2:
            return "Low"
        elif uv_index <= 5:
            return "Moderate"
        elif uv_index <= 7:
            return "High"
        elif uv_index <= 10:
            return "Very High"
        else:
            return "Extreme"
    
    def _get_condition_icon(self, condition: str) -> str:
        """Get weather icon for condition."""
        icon_map = {
            'clear': '☀️',
            'clouds': '☁️',
            'rain': '🌧️',
            'snow': '❄️',
            'thunderstorm': '⛈️',
            'drizzle': '🌦️',
            'mist': '🌫️',
            'fog': '🌫️'
        }
        return icon_map.get(condition.lower(), '🌤️')
    
    def _get_common_conditions(self, weather_data_list: List[ProcessedWeatherData]) -> Dict[str, int]:
        """Get common weather conditions from data list."""
        condition_counts = {}
        for data in weather_data_list:
            condition = data.condition
            condition_counts[condition] = condition_counts.get(condition, 0) + 1
        
        # Sort by count and return top 5
        sorted_conditions = sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_conditions[:5])
    
    def _get_alert_summary(self, weather_data_list: List[ProcessedWeatherData]) -> Dict[str, int]:
        """Get summary of weather alerts from data list."""
        alert_counts = {}
        for data in weather_data_list:
            for alert in data.weather_alerts:
                alert_counts[alert] = alert_counts.get(alert, 0) + 1
        
        return alert_counts


class AirQualityDataMapper:
    """Mapper for air quality data transformations."""
    
    def __init__(self):
        """Initialize the air quality data mapper."""
        self.logger = logging.getLogger(__name__)
    
    def to_ui_model(self, processed_data: ProcessedAirQualityData) -> Dict[str, Any]:
        """Convert processed air quality data to UI model.
        
        Args:
            processed_data: Processed air quality data
            
        Returns:
            UI-optimized air quality model
        """
        try:
            return {
                'aqi_display': str(processed_data.aqi),
                'category_display': processed_data.category,
                'color': processed_data.color,
                'description': processed_data.description,
                'health_recommendations': processed_data.health_recommendations,
                'pollutant_details': self._format_pollutants(processed_data.pollutants),
                'last_updated': processed_data.timestamp.strftime("%H:%M"),
                'is_current': True
            }
        except Exception as e:
            self.logger.error(f"Error mapping air quality to UI model: {e}")
            raise
    
    def _format_pollutants(self, pollutants: Dict[str, float]) -> List[Dict[str, str]]:
        """Format pollutant data for UI display."""
        formatted = []
        pollutant_names = {
            'co': 'Carbon Monoxide',
            'no': 'Nitric Oxide',
            'no2': 'Nitrogen Dioxide',
            'o3': 'Ozone',
            'so2': 'Sulfur Dioxide',
            'pm2_5': 'PM2.5',
            'pm10': 'PM10',
            'nh3': 'Ammonia'
        }
        
        for key, value in pollutants.items():
            formatted.append({
                'name': pollutant_names.get(key, key.upper()),
                'value': f"{value:.2f}",
                'unit': 'μg/m³'
            })
        
        return formatted