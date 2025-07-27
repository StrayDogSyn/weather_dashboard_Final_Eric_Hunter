"""Main application demonstrating clean architecture usage."""

import logging
from typing import Optional

from config.settings import settings
from services.weather_service import WeatherService, WeatherServiceError
from services.gemini_service import GeminiService, GeminiServiceError
from services.github_service import GitHubService, GitHubServiceError
from services.spotify_service import SpotifyService, SpotifyServiceError
from data.database import Database, DatabaseError


class WeatherDashboard:
    """Main weather dashboard application."""
    
    def __init__(self):
        # Initialize core services
        self.weather_service = WeatherService()
        self.database = Database()
        
        # Initialize optional services
        self.gemini_service = self._init_optional_service(GeminiService)
        self.github_service = self._init_optional_service(GitHubService)
        self.spotify_service = self._init_optional_service(SpotifyService)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO if settings.debug_mode else logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _init_optional_service(self, service_class):
        """Initialize optional service with error handling."""
        try:
            service = service_class()
            if service.is_available():
                self.logger.info(f"{service_class.__name__} initialized successfully")
                return service
            else:
                self.logger.warning(f"{service_class.__name__} not properly configured")
        except Exception as e:
            self.logger.warning(f"Failed to initialize {service_class.__name__}: {e}")
        return None
    
    def get_weather_with_insights(self, location: str) -> dict:
        """Get weather data with AI insights and music recommendations."""
        try:
            # Get weather data
            weather_data = self.weather_service.get_weather(location)
            
            # Store in database
            self.database.insert_weather_data(
                location=weather_data.location,
                temperature=weather_data.temperature,
                humidity=weather_data.humidity,
                description=weather_data.description
            )
            
            result = {
                'weather': {
                    'location': weather_data.location,
                    'temperature': weather_data.temperature,
                    'feels_like': weather_data.feels_like,
                    'humidity': weather_data.humidity,
                    'description': weather_data.description,
                    'wind_speed': weather_data.wind_speed,
                    'timestamp': weather_data.timestamp.isoformat()
                }
            }
            
            # Add AI insights if available
            if self.gemini_service:
                try:
                    insight = self.gemini_service.generate_weather_insight(result['weather'])
                    result['ai_insight'] = insight
                except GeminiServiceError as e:
                    self.logger.error(f"Gemini AI error: {e}")
            
            # Add music recommendations if available
            if self.spotify_service:
                try:
                    playlist = self.spotify_service.get_weather_playlist(
                        weather_data.description, limit=5
                    )
                    result['music_recommendations'] = playlist
                except SpotifyServiceError as e:
                    self.logger.error(f"Spotify error: {e}")
            
            return result
            
        except WeatherServiceError as e:
            self.logger.error(f"Weather service error: {e}")
            raise
        except DatabaseError as e:
            self.logger.error(f"Database error: {e}")
            # Continue without database storage
            return {'error': 'Database unavailable, but weather data retrieved'}
    
    def get_weather_history(self, location: Optional[str] = None, limit: int = 10) -> list:
        """Get weather history from database."""
        try:
            if location:
                return self.database.get_weather_by_location(location, limit)
            else:
                return self.database.get_recent_weather(limit)
        except DatabaseError as e:
            self.logger.error(f"Database error: {e}")
            return []
    
    def test_services(self) -> dict:
        """Test all configured services."""
        results = {
            'weather_service': True,  # Always available (required)
            'database': True,         # Always available (required)
            'gemini_service': False,
            'github_service': False,
            'spotify_service': False
        }
        
        # Test optional services
        if self.gemini_service:
            results['gemini_service'] = True
        
        if self.github_service:
            results['github_service'] = self.github_service.test_connection()
        
        if self.spotify_service:
            results['spotify_service'] = self.spotify_service.test_connection()
        
        return results


if __name__ == "__main__":
    # Example usage
    app = WeatherDashboard()
    
    print("Weather Dashboard - Clean Architecture Demo")
    print("=" * 50)
    
    # Test services
    service_status = app.test_services()
    print("\nService Status:")
    for service, status in service_status.items():
        status_text = "✓ Available" if status else "✗ Not configured"
        print(f"  {service}: {status_text}")
    
    # Get weather for a sample location
    try:
        print("\nGetting weather for London...")
        result = app.get_weather_with_insights("London")
        
        weather = result['weather']
        print(f"\nWeather in {weather['location']}:")
        print(f"  Temperature: {weather['temperature']}°C (feels like {weather['feels_like']}°C)")
        print(f"  Conditions: {weather['description']}")
        print(f"  Humidity: {weather['humidity']}%")
        print(f"  Wind Speed: {weather['wind_speed']} m/s")
        
        if 'ai_insight' in result:
            print(f"\nAI Insight: {result['ai_insight']}")
        
        if 'music_recommendations' in result:
            print("\nMusic Recommendations:")
            for track in result['music_recommendations'][:3]:
                print(f"  ♪ {track['name']} by {track['artist']}")
    
    except Exception as e:
        print(f"Error: {e}")