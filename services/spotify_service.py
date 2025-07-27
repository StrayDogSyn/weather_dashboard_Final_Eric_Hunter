"""Spotify service for music integration based on weather."""

import logging
from typing import Optional, List, Dict, Any

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except ImportError:
    spotipy = None
    SpotifyClientCredentials = None

from config.settings import settings


class SpotifyServiceError(Exception):
    """Custom exception for Spotify service errors."""
    pass


class SpotifyService:
    """Spotify API service for weather-based music recommendations."""
    
    # Weather-to-genre mapping
    WEATHER_GENRES = {
        'clear': ['pop', 'indie', 'summer'],
        'clouds': ['chill', 'ambient', 'indie'],
        'rain': ['jazz', 'blues', 'acoustic'],
        'snow': ['classical', 'ambient', 'winter'],
        'thunderstorm': ['rock', 'electronic', 'dramatic'],
        'mist': ['ambient', 'chill', 'atmospheric'],
        'fog': ['ambient', 'chill', 'atmospheric']
    }
    
    def __init__(self):
        if not spotipy:
            raise SpotifyServiceError(
                "spotipy package not installed. "
                "Install with: pip install spotipy"
            )
        
        if not settings.spotify_client_id or not settings.spotify_client_secret:
            raise SpotifyServiceError(
                "Spotify credentials not configured. "
                "Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your .env file."
            )
        
        # Initialize Spotify client with client credentials flow
        auth_manager = SpotifyClientCredentials(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret
        )
        
        self.spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    def get_weather_playlist(self, weather_condition: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get music recommendations based on weather conditions."""
        try:
            # Map weather condition to genres
            condition_key = self._normalize_weather_condition(weather_condition)
            genres = self.WEATHER_GENRES.get(condition_key, ['pop', 'indie'])
            
            # Get recommendations
            recommendations = self.spotify.recommendations(
                seed_genres=genres[:3],  # Spotify allows max 5 seeds, use 3 genres
                limit=limit,
                market='US'
            )
            
            return [
                {
                    'name': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'preview_url': track['preview_url'],
                    'external_url': track['external_urls']['spotify'],
                    'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None
                }
                for track in recommendations['tracks']
            ]
            
        except Exception as e:
            logging.error(f"Spotify API error: {e}")
            raise SpotifyServiceError(f"Failed to get recommendations: {e}")
    
    def search_tracks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tracks by query."""
        try:
            results = self.spotify.search(q=query, type='track', limit=limit, market='US')
            
            return [
                {
                    'name': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'preview_url': track['preview_url'],
                    'external_url': track['external_urls']['spotify'],
                    'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None
                }
                for track in results['tracks']['items']
            ]
            
        except Exception as e:
            logging.error(f"Spotify search error: {e}")
            raise SpotifyServiceError(f"Search failed: {e}")
    
    def _normalize_weather_condition(self, condition: str) -> str:
        """Normalize weather condition to match genre mapping."""
        condition = condition.lower()
        
        # Map common weather descriptions to our keys
        if 'clear' in condition or 'sunny' in condition:
            return 'clear'
        elif 'cloud' in condition or 'overcast' in condition:
            return 'clouds'
        elif 'rain' in condition or 'drizzle' in condition:
            return 'rain'
        elif 'snow' in condition or 'blizzard' in condition:
            return 'snow'
        elif 'thunder' in condition or 'storm' in condition:
            return 'thunderstorm'
        elif 'mist' in condition or 'haze' in condition:
            return 'mist'
        elif 'fog' in condition:
            return 'fog'
        else:
            return 'clear'  # Default fallback
    
    def is_available(self) -> bool:
        """Check if Spotify service is properly configured and available."""
        return bool(
            spotipy and 
            settings.spotify_client_id and 
            settings.spotify_client_secret
        )
    
    def test_connection(self) -> bool:
        """Test Spotify API connection."""
        try:
            # Try a simple search to test connection
            self.spotify.search(q='test', type='track', limit=1)
            return True
        except Exception:
            return False