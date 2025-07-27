"""Clean GitHub service with proper API authentication."""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

from config.settings import get_settings


class GitHubError(Exception):
    """Custom exception for GitHub service errors."""
    pass


class GitHubService:
    """Clean GitHub service for weather data sharing."""
    
    def __init__(self):
        self.settings = get_settings()
        self.session = None
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """Initialize GitHub service with proper authentication."""
        if not self.is_available():
            logging.warning("GitHub service not available - missing API key or requests library")
            return
        
        try:
            # Create session with authentication
            self.session = requests.Session()
            self.session.headers.update({
                'Authorization': f'token {self.settings.github_api_key}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Weather-Dashboard-App/1.0'
            })
            
            # Test authentication
            response = self.session.get('https://api.github.com/user')
            if response.status_code == 200:
                user_data = response.json()
                logging.info(f"GitHub service initialized for user: {user_data.get('login', 'Unknown')}")
            else:
                logging.error(f"GitHub authentication failed: {response.status_code}")
                self.session = None
                
        except Exception as e:
            logging.error(f"Failed to initialize GitHub service: {e}")
            self.session = None
            raise GitHubError(f"GitHub initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Check if GitHub service is available."""
        return (
            requests is not None and 
            self.settings.has_github and 
            bool(self.settings.github_api_key)
        )
    
    def is_ready(self) -> bool:
        """Check if service is ready for use."""
        return self.is_available() and self.session is not None
    
    def create_weather_gist(self, weather_data: Dict[str, Any], description: Optional[str] = None) -> Optional[str]:
        """Create a GitHub Gist with weather data.
        
        Args:
            weather_data: Dictionary containing weather information
            description: Optional description for the gist
            
        Returns:
            Gist URL if successful, None otherwise
        """
        if not self.is_ready():
            logging.warning("GitHub service not ready for gist creation")
            return None
        
        try:
            # Prepare gist data
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            location = weather_data.get('location', 'Unknown')
            
            gist_description = description or f"Weather data for {location} - {timestamp}"
            
            # Create formatted weather content
            weather_content = self._format_weather_data(weather_data, timestamp)
            
            gist_data = {
                'description': gist_description,
                'public': False,  # Private gist by default
                'files': {
                    f'weather-{location.lower().replace(" ", "-")}-{timestamp.replace(":", "-").replace(" ", "_")}.json': {
                        'content': weather_content
                    }
                }
            }
            
            # Create the gist
            response = self.session.post('https://api.github.com/gists', json=gist_data)
            
            if response.status_code == 201:
                gist_info = response.json()
                gist_url = gist_info.get('html_url')
                logging.info(f"Weather gist created successfully: {gist_url}")
                return gist_url
            else:
                logging.error(f"Failed to create gist: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Failed to create weather gist: {e}")
            raise GitHubError(f"Gist creation failed: {e}")
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information.
        
        Returns:
            User information dictionary or None if unavailable
        """
        if not self.is_ready():
            logging.warning("GitHub service not ready for user info")
            return None
        
        try:
            response = self.session.get('https://api.github.com/user')
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Failed to get user info: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Failed to get user info: {e}")
            raise GitHubError(f"User info retrieval failed: {e}")
    
    def list_weather_gists(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List weather-related gists for the authenticated user.
        
        Args:
            limit: Maximum number of gists to return
            
        Returns:
            List of gist information dictionaries
        """
        if not self.is_ready():
            logging.warning("GitHub service not ready for gist listing")
            return []
        
        try:
            response = self.session.get(f'https://api.github.com/gists?per_page={limit}')
            
            if response.status_code == 200:
                gists = response.json()
                # Filter for weather-related gists
                weather_gists = [
                    gist for gist in gists 
                    if 'weather' in gist.get('description', '').lower()
                ]
                return weather_gists
            else:
                logging.error(f"Failed to list gists: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Failed to list gists: {e}")
            raise GitHubError(f"Gist listing failed: {e}")
    
    def _format_weather_data(self, weather_data: Dict[str, Any], timestamp: str) -> str:
        """Format weather data for gist content."""
        formatted_data = {
            'timestamp': timestamp,
            'location': weather_data.get('location', 'Unknown'),
            'weather': {
                'temperature': weather_data.get('temperature'),
                'feels_like': weather_data.get('feels_like'),
                'humidity': weather_data.get('humidity'),
                'pressure': weather_data.get('pressure'),
                'description': weather_data.get('description'),
                'wind_speed': weather_data.get('wind_speed'),
                'wind_direction': weather_data.get('wind_direction'),
                'visibility': weather_data.get('visibility')
            },
            'metadata': {
                'source': 'Weather Dashboard App',
                'api_provider': 'OpenWeatherMap'
            }
        }
        
        return json.dumps(formatted_data, indent=2, ensure_ascii=False)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        user_info = None
        if self.is_ready():
            try:
                user_info = self.get_user_info()
            except:
                pass
        
        return {
            'available': self.is_available(),
            'ready': self.is_ready(),
            'has_api_key': bool(self.settings.github_api_key),
            'requests_available': requests is not None,
            'authenticated_user': user_info.get('login') if user_info else None
        }