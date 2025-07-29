"""Weather Data Processor

Handles processing and transformation of weather data,
extracting business logic from UI components.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass

from interfaces.weather_service_interface import IDataProcessor
from config.app_config import WEATHER_ICONS, AQI_COLORS, UNIT_CONVERSIONS


@dataclass
class ProcessedWeatherData:
    """Processed weather data with enhanced information."""
    temperature: float
    temperature_formatted: str
    feels_like: float
    feels_like_formatted: str
    humidity: int
    pressure: float
    pressure_formatted: str
    wind_speed: float
    wind_speed_formatted: str
    wind_direction: int
    wind_direction_text: str
    visibility: float
    visibility_formatted: str
    uv_index: Optional[float]
    uv_index_description: str
    condition: str
    condition_icon: str
    description: str
    timestamp: datetime
    location: str
    country: str
    sunrise: Optional[datetime]
    sunset: Optional[datetime]
    
    # Enhanced data
    temperature_trend: str
    comfort_level: str
    weather_alerts: List[str]
    recommendations: List[str]


@dataclass
class ProcessedAirQualityData:
    """Processed air quality data."""
    aqi: int
    category: str
    color: str
    description: str
    health_recommendations: List[str]
    pollutants: Dict[str, float]
    timestamp: datetime


class WeatherDataProcessor(IDataProcessor):
    """Processor for weather data with business logic and enhancements."""
    
    def __init__(self, config_service=None):
        """Initialize the weather data processor.
        
        Args:
            config_service: Configuration service instance
        """
        self.logger = logging.getLogger(__name__)
        self.config_service = config_service
        
        # Temperature thresholds for comfort assessment
        self.comfort_thresholds = {
            'very_cold': -10,
            'cold': 5,
            'cool': 15,
            'comfortable': 25,
            'warm': 30,
            'hot': 35
        }
        
        # Wind speed thresholds (m/s)
        self.wind_thresholds = {
            'calm': 1,
            'light': 3,
            'gentle': 5,
            'moderate': 8,
            'fresh': 11,
            'strong': 14
        }
    
    def process(self, raw_data: Dict[str, Any]) -> ProcessedWeatherData:
        """Process raw weather data into enhanced format.
        
        Args:
            raw_data: Raw weather data from API
            
        Returns:
            ProcessedWeatherData object with enhanced information
        """
        try:
            # Extract basic weather information
            main = raw_data.get('main', {})
            weather = raw_data.get('weather', [{}])[0]
            wind = raw_data.get('wind', {})
            sys_data = raw_data.get('sys', {})
            
            # Process temperature data
            temp = main.get('temp', 0)
            feels_like = main.get('feels_like', temp)
            
            # Process location data
            location = raw_data.get('name', 'Unknown')
            country = sys_data.get('country', '')
            
            # Process timestamps
            timestamp = datetime.now(timezone.utc)
            sunrise = self._convert_timestamp(sys_data.get('sunrise'))
            sunset = self._convert_timestamp(sys_data.get('sunset'))
            
            # Process weather condition
            condition = weather.get('main', '').lower()
            description = weather.get('description', '')
            icon = self._get_weather_icon(condition, description)
            
            # Process wind data
            wind_speed = wind.get('speed', 0)
            wind_direction = wind.get('deg', 0)
            wind_direction_text = self._get_wind_direction_text(wind_direction)
            
            # Process visibility
            visibility = raw_data.get('visibility', 0) / 1000  # Convert to km
            
            # Get UV index if available
            uv_index = raw_data.get('uvi')
            uv_description = self._get_uv_description(uv_index)
            
            # Generate enhanced data
            temperature_trend = self._analyze_temperature_trend(temp, feels_like)
            comfort_level = self._assess_comfort_level(temp, main.get('humidity', 0), wind_speed)
            weather_alerts = self._generate_weather_alerts(raw_data)
            recommendations = self._generate_recommendations(temp, condition, wind_speed, main.get('humidity', 0))
            
            return ProcessedWeatherData(
                temperature=temp,
                temperature_formatted=self._format_temperature(temp),
                feels_like=feels_like,
                feels_like_formatted=self._format_temperature(feels_like),
                humidity=main.get('humidity', 0),
                pressure=main.get('pressure', 0),
                pressure_formatted=self._format_pressure(main.get('pressure', 0)),
                wind_speed=wind_speed,
                wind_speed_formatted=self._format_wind_speed(wind_speed),
                wind_direction=wind_direction,
                wind_direction_text=wind_direction_text,
                visibility=visibility,
                visibility_formatted=self._format_visibility(visibility),
                uv_index=uv_index,
                uv_index_description=uv_description,
                condition=condition,
                condition_icon=icon,
                description=description.title(),
                timestamp=timestamp,
                location=location,
                country=country,
                sunrise=sunrise,
                sunset=sunset,
                temperature_trend=temperature_trend,
                comfort_level=comfort_level,
                weather_alerts=weather_alerts,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error processing weather data: {e}")
            raise
    
    def process_air_quality(self, raw_data: Dict[str, Any]) -> ProcessedAirQualityData:
        """Process raw air quality data.
        
        Args:
            raw_data: Raw air quality data from API
            
        Returns:
            ProcessedAirQualityData object
        """
        try:
            main = raw_data.get('main', {})
            components = raw_data.get('components', {})
            
            aqi = main.get('aqi', 1)
            category = self._get_aqi_category(aqi)
            color = AQI_COLORS.get(category, '#808080')
            description = self._get_aqi_description(aqi)
            health_recommendations = self._get_aqi_health_recommendations(aqi)
            
            return ProcessedAirQualityData(
                aqi=aqi,
                category=category,
                color=color,
                description=description,
                health_recommendations=health_recommendations,
                pollutants=components,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"Error processing air quality data: {e}")
            raise
    
    def validate(self, data: Any) -> bool:
        """Validate processed weather data.
        
        Args:
            data: ProcessedWeatherData to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        if not isinstance(data, ProcessedWeatherData):
            return False
        
        # Check required fields
        required_fields = ['temperature', 'condition', 'location', 'timestamp']
        for field in required_fields:
            if not hasattr(data, field) or getattr(data, field) is None:
                return False
        
        # Validate temperature range (reasonable values)
        if not -100 <= data.temperature <= 60:  # Celsius
            return False
        
        # Validate humidity range
        if not 0 <= data.humidity <= 100:
            return False
        
        return True
    
    def _convert_timestamp(self, timestamp: Optional[int]) -> Optional[datetime]:
        """Convert Unix timestamp to datetime."""
        if timestamp:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return None
    
    def _get_weather_icon(self, condition: str, description: str) -> str:
        """Get weather icon for condition."""
        # Try exact match first
        if description.lower() in WEATHER_ICONS:
            return WEATHER_ICONS[description.lower()]
        
        # Try condition match
        if condition in WEATHER_ICONS:
            return WEATHER_ICONS[condition]
        
        # Default icon
        return "🌤️"
    
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
    
    def _analyze_temperature_trend(self, temp: float, feels_like: float) -> str:
        """Analyze temperature trend."""
        diff = feels_like - temp
        if abs(diff) < 1:
            return "Stable"
        elif diff > 0:
            return "Feels warmer"
        else:
            return "Feels cooler"
    
    def _assess_comfort_level(self, temp: float, humidity: int, wind_speed: float) -> str:
        """Assess comfort level based on weather conditions."""
        # Heat index calculation for comfort
        if temp < self.comfort_thresholds['cold']:
            return "Very Cold"
        elif temp < self.comfort_thresholds['cool']:
            return "Cold"
        elif temp < self.comfort_thresholds['comfortable']:
            if humidity > 80:
                return "Cool & Humid"
            return "Cool"
        elif temp < self.comfort_thresholds['warm']:
            if humidity > 70:
                return "Comfortable but Humid"
            return "Comfortable"
        elif temp < self.comfort_thresholds['hot']:
            if humidity > 60:
                return "Warm & Humid"
            return "Warm"
        else:
            return "Hot"
    
    def _generate_weather_alerts(self, raw_data: Dict[str, Any]) -> List[str]:
        """Generate weather alerts based on conditions."""
        alerts = []
        
        main = raw_data.get('main', {})
        wind = raw_data.get('wind', {})
        
        # Temperature alerts
        temp = main.get('temp', 0)
        if temp > 35:
            alerts.append("⚠️ Extreme heat warning")
        elif temp < -10:
            alerts.append("❄️ Extreme cold warning")
        
        # Wind alerts
        wind_speed = wind.get('speed', 0)
        if wind_speed > 14:  # Strong wind
            alerts.append("💨 Strong wind advisory")
        
        # Visibility alerts
        visibility = raw_data.get('visibility', 10000)
        if visibility < 1000:  # Less than 1km
            alerts.append("🌫️ Low visibility warning")
        
        # Humidity alerts
        humidity = main.get('humidity', 0)
        if humidity > 90:
            alerts.append("💧 Very high humidity")
        
        return alerts
    
    def _generate_recommendations(self, temp: float, condition: str, wind_speed: float, humidity: int) -> List[str]:
        """Generate weather-based recommendations."""
        recommendations = []
        
        # Temperature-based recommendations
        if temp > 30:
            recommendations.append("Stay hydrated and seek shade")
            recommendations.append("Wear light, breathable clothing")
        elif temp < 5:
            recommendations.append("Dress warmly in layers")
            recommendations.append("Protect exposed skin")
        
        # Condition-based recommendations
        if 'rain' in condition or 'storm' in condition:
            recommendations.append("Carry an umbrella")
            recommendations.append("Drive carefully if traveling")
        elif 'snow' in condition:
            recommendations.append("Wear appropriate footwear")
            recommendations.append("Allow extra travel time")
        
        # Wind-based recommendations
        if wind_speed > 10:
            recommendations.append("Secure loose outdoor items")
        
        # Humidity-based recommendations
        if humidity > 80:
            recommendations.append("Expect muggy conditions")
        elif humidity < 30:
            recommendations.append("Use moisturizer for dry air")
        
        return recommendations
    
    def _format_temperature(self, temp: float) -> str:
        """Format temperature with appropriate precision."""
        precision = 1 if self.config_service else 1
        if self.config_service:
            precision = self.config_service.get_temperature_precision()
        return f"{temp:.{precision}f}°C"
    
    def _format_pressure(self, pressure: float) -> str:
        """Format pressure value."""
        return f"{pressure:.0f} hPa"
    
    def _format_wind_speed(self, speed: float) -> str:
        """Format wind speed value."""
        return f"{speed:.1f} m/s"
    
    def _format_visibility(self, visibility: float) -> str:
        """Format visibility value."""
        return f"{visibility:.1f} km"
    
    def _get_aqi_category(self, aqi: int) -> str:
        """Get AQI category from index value."""
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    def _get_aqi_description(self, aqi: int) -> str:
        """Get AQI description."""
        category = self._get_aqi_category(aqi)
        descriptions = {
            "Good": "Air quality is satisfactory",
            "Moderate": "Air quality is acceptable for most people",
            "Unhealthy for Sensitive Groups": "Sensitive individuals may experience problems",
            "Unhealthy": "Everyone may experience problems",
            "Very Unhealthy": "Health alert: everyone may experience serious effects",
            "Hazardous": "Health warning: emergency conditions"
        }
        return descriptions.get(category, "Unknown air quality")
    
    def _get_aqi_health_recommendations(self, aqi: int) -> List[str]:
        """Get health recommendations based on AQI."""
        if aqi <= 50:
            return ["Enjoy outdoor activities"]
        elif aqi <= 100:
            return ["Sensitive individuals should limit prolonged outdoor exertion"]
        elif aqi <= 150:
            return [
                "Sensitive groups should avoid outdoor activities",
                "Others should limit prolonged outdoor exertion"
            ]
        elif aqi <= 200:
            return [
                "Everyone should avoid outdoor activities",
                "Sensitive groups should remain indoors"
            ]
        elif aqi <= 300:
            return [
                "Everyone should avoid all outdoor activities",
                "Stay indoors with windows closed"
            ]
        else:
            return [
                "Emergency conditions - avoid all outdoor exposure",
                "Stay indoors and use air purifiers if available"
            ]