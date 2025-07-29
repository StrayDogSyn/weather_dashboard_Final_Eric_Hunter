"""Tests for Weather Service

Unit tests for weather API integration and data handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.weather_service import WeatherService
from models.weather_models import WeatherData, ForecastData, WeatherCondition, Location
from services.config_service import WeatherConfig


class TestWeatherService(unittest.TestCase):
    """Test cases for WeatherService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = WeatherConfig(
            api_key="test_api_key_12345678901234567890",
            base_url="https://api.openweathermap.org/data/2.5",
            timeout=10,
            cache_ttl=300,
            units="metric"
        )
        self.weather_service = WeatherService(self.config)
    
    def test_init(self):
        """Test WeatherService initialization."""
        self.assertEqual(self.weather_service.config, self.config)
        self.assertIsNotNone(self.weather_service.session)
        self.assertIsNotNone(self.weather_service.cache)
    
    @patch('requests.Session.get')
    def test_get_current_weather_success(self, mock_get):
        """Test successful current weather retrieval."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "coord": {"lon": -74.006, "lat": 40.7143},
            "weather": [{
                "id": 800,
                "main": "Clear",
                "description": "clear sky",
                "icon": "01d"
            }],
            "base": "stations",
            "main": {
                "temp": 22.5,
                "feels_like": 23.1,
                "temp_min": 20.0,
                "temp_max": 25.0,
                "pressure": 1013,
                "humidity": 65
            },
            "visibility": 10000,
            "wind": {
                "speed": 3.5,
                "deg": 180
            },
            "clouds": {
                "all": 0
            },
            "dt": 1609459200,
            "sys": {
                "type": 1,
                "id": 1234,
                "country": "US",
                "sunrise": 1609423200,
                "sunset": 1609459200
            },
            "timezone": -18000,
            "id": 5128581,
            "name": "New York",
            "cod": 200
        }
        mock_get.return_value = mock_response
        
        # Test the method
        result = self.weather_service.get_current_weather("New York")
        
        # Assertions
        self.assertIsInstance(result, WeatherData)
        self.assertEqual(result.location.name, "New York")
        self.assertEqual(result.temperature, 22.5)
        self.assertEqual(result.condition.main, "Clear")
        self.assertEqual(result.humidity, 65)
    
    @patch('requests.Session.get')
    def test_get_current_weather_api_error(self, mock_get):
        """Test current weather retrieval with API error."""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "cod": "404",
            "message": "city not found"
        }
        mock_get.return_value = mock_response
        
        # Test the method
        result = self.weather_service.get_current_weather("NonexistentCity")
        
        # Should return None on error
        self.assertIsNone(result)
    
    @patch('requests.Session.get')
    def test_get_forecast_success(self, mock_get):
        """Test successful forecast retrieval."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cod": "200",
            "message": 0,
            "cnt": 2,
            "list": [
                {
                    "dt": 1609459200,
                    "main": {
                        "temp": 22.5,
                        "feels_like": 23.1,
                        "temp_min": 20.0,
                        "temp_max": 25.0,
                        "pressure": 1013,
                        "humidity": 65
                    },
                    "weather": [{
                        "id": 800,
                        "main": "Clear",
                        "description": "clear sky",
                        "icon": "01d"
                    }],
                    "wind": {
                        "speed": 3.5,
                        "deg": 180
                    },
                    "dt_txt": "2021-01-01 12:00:00"
                },
                {
                    "dt": 1609470000,
                    "main": {
                        "temp": 20.0,
                        "feels_like": 19.5,
                        "temp_min": 18.0,
                        "temp_max": 22.0,
                        "pressure": 1015,
                        "humidity": 70
                    },
                    "weather": [{
                        "id": 801,
                        "main": "Clouds",
                        "description": "few clouds",
                        "icon": "02d"
                    }],
                    "wind": {
                        "speed": 2.5,
                        "deg": 200
                    },
                    "dt_txt": "2021-01-01 15:00:00"
                }
            ],
            "city": {
                "id": 5128581,
                "name": "New York",
                "coord": {
                    "lat": 40.7143,
                    "lon": -74.006
                },
                "country": "US",
                "timezone": -18000
            }
        }
        mock_get.return_value = mock_response
        
        # Test the method
        result = self.weather_service.get_forecast("New York")
        
        # Assertions
        self.assertIsInstance(result, ForecastData)
        self.assertEqual(result.location.name, "New York")
        self.assertEqual(len(result.hourly_forecasts), 2)
        self.assertEqual(result.hourly_forecasts[0].temperature, 22.5)
        self.assertEqual(result.hourly_forecasts[1].temperature, 20.0)
    
    def test_cache_functionality(self):
        """Test caching functionality."""
        # Test cache key generation
        key1 = self.weather_service._generate_cache_key("current", "New York")
        key2 = self.weather_service._generate_cache_key("current", "New York")
        key3 = self.weather_service._generate_cache_key("current", "London")
        
        self.assertEqual(key1, key2)  # Same parameters should generate same key
        self.assertNotEqual(key1, key3)  # Different parameters should generate different keys
        
        # Test cache operations
        test_data = {"test": "data"}
        self.weather_service.cache.set(key1, test_data)
        
        cached_data = self.weather_service.cache.get(key1)
        self.assertEqual(cached_data, test_data)
        
        # Test cache miss
        missing_data = self.weather_service.cache.get("nonexistent_key")
        self.assertIsNone(missing_data)
    
    @patch('requests.Session.get')
    def test_get_current_weather_with_coordinates(self, mock_get):
        """Test current weather retrieval using coordinates."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "coord": {"lon": -74.006, "lat": 40.7143},
            "weather": [{
                "id": 800,
                "main": "Clear",
                "description": "clear sky",
                "icon": "01d"
            }],
            "main": {
                "temp": 22.5,
                "feels_like": 23.1,
                "temp_min": 20.0,
                "temp_max": 25.0,
                "pressure": 1013,
                "humidity": 65
            },
            "wind": {
                "speed": 3.5,
                "deg": 180
            },
            "name": "New York",
            "sys": {"country": "US"},
            "dt": 1609459200
        }
        mock_get.return_value = mock_response
        
        # Test with coordinates
        result = self.weather_service.get_current_weather_by_coords(40.7143, -74.006)
        
        # Assertions
        self.assertIsInstance(result, WeatherData)
        self.assertEqual(result.location.latitude, 40.7143)
        self.assertEqual(result.location.longitude, -74.006)
    
    def test_request_timeout_handling(self):
        """Test request timeout handling."""
        with patch('requests.Session.get') as mock_get:
            # Mock timeout exception
            mock_get.side_effect = Exception("Request timeout")
            
            # Test current weather
            result = self.weather_service.get_current_weather("New York")
            self.assertIsNone(result)
            
            # Test forecast
            result = self.weather_service.get_forecast("New York")
            self.assertIsNone(result)
    
    def test_invalid_api_key_handling(self):
        """Test handling of invalid API key."""
        with patch('requests.Session.get') as mock_get:
            # Mock invalid API key response
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "cod": 401,
                "message": "Invalid API key"
            }
            mock_get.return_value = mock_response
            
            result = self.weather_service.get_current_weather("New York")
            self.assertIsNone(result)
    
    def test_rate_limiting_handling(self):
        """Test handling of rate limiting."""
        with patch('requests.Session.get') as mock_get:
            # Mock rate limit response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                "cod": 429,
                "message": "Rate limit exceeded"
            }
            mock_get.return_value = mock_response
            
            result = self.weather_service.get_current_weather("New York")
            self.assertIsNone(result)
    
    def test_malformed_response_handling(self):
        """Test handling of malformed API responses."""
        with patch('requests.Session.get') as mock_get:
            # Mock malformed response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = mock_response
            
            result = self.weather_service.get_current_weather("New York")
            self.assertIsNone(result)
    
    def test_empty_city_name_handling(self):
        """Test handling of empty city names."""
        result = self.weather_service.get_current_weather("")
        self.assertIsNone(result)
        
        result = self.weather_service.get_current_weather(None)
        self.assertIsNone(result)
    
    def test_invalid_coordinates_handling(self):
        """Test handling of invalid coordinates."""
        # Test invalid latitude
        result = self.weather_service.get_current_weather_by_coords(91.0, 0.0)
        self.assertIsNone(result)
        
        # Test invalid longitude
        result = self.weather_service.get_current_weather_by_coords(0.0, 181.0)
        self.assertIsNone(result)
    
    def test_cache_expiration(self):
        """Test cache expiration functionality."""
        # Set a very short TTL for testing
        short_ttl_config = WeatherConfig(
            api_key="test_api_key_12345678901234567890",
            base_url="https://api.openweathermap.org/data/2.5",
            timeout=10,
            cache_ttl=1,  # 1 second TTL
            units="metric"
        )
        service = WeatherService(short_ttl_config)
        
        # Add data to cache
        test_data = {"test": "data"}
        cache_key = "test_key"
        service.cache.set(cache_key, test_data)
        
        # Should be available immediately
        cached_data = service.cache.get(cache_key)
        self.assertEqual(cached_data, test_data)
        
        # Wait for expiration and test
        import time
        time.sleep(1.1)
        
        expired_data = service.cache.get(cache_key)
        self.assertIsNone(expired_data)


class TestWeatherDataModels(unittest.TestCase):
    """Test cases for weather data models."""
    
    def test_weather_condition_creation(self):
        """Test WeatherCondition creation and methods."""
        condition = WeatherCondition(
            id=800,
            main="Clear",
            description="clear sky",
            icon="01d"
        )
        
        self.assertEqual(condition.id, 800)
        self.assertEqual(condition.main, "Clear")
        self.assertEqual(condition.description, "clear sky")
        self.assertEqual(condition.icon, "01d")
        
        # Test icon URL generation
        icon_url = condition.get_icon_url()
        self.assertIn("01d", icon_url)
        self.assertTrue(icon_url.startswith("https://"))
    
    def test_location_creation(self):
        """Test Location creation."""
        location = Location(
            name="New York",
            country="US",
            latitude=40.7143,
            longitude=-74.006
        )
        
        self.assertEqual(location.name, "New York")
        self.assertEqual(location.country, "US")
        self.assertEqual(location.latitude, 40.7143)
        self.assertEqual(location.longitude, -74.006)
    
    def test_weather_data_creation(self):
        """Test WeatherData creation and properties."""
        condition = WeatherCondition(800, "Clear", "clear sky", "01d")
        location = Location("New York", "US", 40.7143, -74.006)
        
        weather_data = WeatherData(
            location=location,
            condition=condition,
            temperature=22.5,
            feels_like=23.1,
            humidity=65,
            pressure=1013,
            wind_speed=3.5,
            wind_direction=180,
            visibility=10000,
            timestamp=datetime.now()
        )
        
        self.assertEqual(weather_data.temperature, 22.5)
        self.assertEqual(weather_data.humidity, 65)
        
        # Test temperature conversion
        fahrenheit = weather_data.temperature_fahrenheit
        self.assertAlmostEqual(fahrenheit, 72.5, places=1)
        
        # Test wind direction
        direction = weather_data.wind_direction_text
        self.assertEqual(direction, "S")


if __name__ == '__main__':
    unittest.main()