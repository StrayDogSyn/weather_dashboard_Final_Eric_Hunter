"""Clean Spotify service with proper OAuth authentication."""

import logging
from typing import Optional, Dict, Any, List

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except ImportError:
    spotipy = None
    SpotifyClientCredentials = None

from config.settings import get_settings


class SpotifyError(Exception):
    """Custom exception for Spotify service errors."""
    pass


class SpotifyService:
    """Clean Spotify service for weather-based music recommendations."""
    
    # Weather condition to genre mapping
    WEATHER_GENRES = {
        'clear': ['pop', 'indie', 'acoustic', 'folk'],
        'sunny': ['pop', 'indie', 'acoustic', 'folk'],
        'clouds': ['indie', 'alternative', 'chill'],
        'cloudy': ['indie', 'alternative', 'chill'],
        'rain': ['jazz', 'blues', 'ambient', 'classical'],
        'drizzle': ['jazz', 'blues', 'ambient', 'classical'],
        'thunderstorm': ['rock', 'metal', 'electronic'],
        'snow': ['classical', 'ambient', 'folk', 'indie'],
        'mist': ['ambient', 'chill', 'downtempo'],
        'fog': ['ambient', 'chill', 'downtempo'],
        'haze': ['ambient', 'chill', 'downtempo'],
        'default': ['pop', 'indie', 'alternative']
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.spotify = None
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """Initialize Spotify service with proper OAuth."""
        if not self.is_available():
            logging.warning("Spotify service not available - missing credentials or library")
            return
        
        try:
            # Use Client Credentials flow for app-only access
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.settings.spotify_client_id,
                client_secret=self.settings.spotify_client_secret
            )
            
            self.spotify = spotipy.Spotify(
                client_credentials_manager=client_credentials_manager,
                requests_timeout=10,
                retries=3
            )
            
            # Test the connection
            test_result = self.spotify.search(q='test', type='track', limit=1)
            if test_result:
                logging.info("Spotify service initialized successfully")
            else:
                logging.error("Spotify service test failed")
                self.spotify = None
                
        except Exception as e:
            logging.error(f"Failed to initialize Spotify service: {e}")
            self.spotify = None
            raise SpotifyError(f"Spotify initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Spotify service is available."""
        return (
            spotipy is not None and 
            self.settings.has_spotify and 
            bool(self.settings.spotify_client_id) and 
            bool(self.settings.spotify_client_secret)
        )
    
    def is_ready(self) -> bool:
        """Check if service is ready for use."""
        return self.is_available() and self.spotify is not None
    
    def get_weather_playlist(self, weather_condition: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Get music recommendations based on weather condition.
        
        Args:
            weather_condition: Current weather condition
            limit: Number of tracks to return
            
        Returns:
            List of track dictionaries or None if service unavailable
        """
        if not self.is_ready():
            logging.warning("Spotify service not ready for playlist generation")
            return None
        
        try:
            # Normalize weather condition and get genres
            normalized_condition = self._normalize_weather_condition(weather_condition)
            genres = self.WEATHER_GENRES.get(normalized_condition, self.WEATHER_GENRES['default'])
            
            tracks = []
            tracks_per_genre = max(1, limit // len(genres))
            
            for genre in genres:
                try:
                    # Search for tracks in this genre
                    results = self.spotify.search(
                        q=f'genre:{genre}',
                        type='track',
                        limit=tracks_per_genre,
                        market='US'
                    )
                    
                    for track in results['tracks']['items']:
                        if len(tracks) >= limit:
                            break
                        
                        track_info = self._extract_track_info(track)
                        if track_info:
                            tracks.append(track_info)
                            
                except Exception as e:
                    logging.warning(f"Failed to search genre '{genre}': {e}")
                    continue
                
                if len(tracks) >= limit:
                    break
            
            logging.info(f"Generated playlist with {len(tracks)} tracks for weather: {weather_condition}")
            return tracks[:limit]
            
        except Exception as e:
            logging.error(f"Failed to generate weather playlist: {e}")
            raise SpotifyError(f"Playlist generation failed: {e}")
    
    def search_tracks(self, query: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Search for tracks by query.
        
        Args:
            query: Search query
            limit: Number of tracks to return
            
        Returns:
            List of track dictionaries or None if service unavailable
        """
        if not self.is_ready():
            logging.warning("Spotify service not ready for track search")
            return None
        
        try:
            results = self.spotify.search(q=query, type='track', limit=limit, market='US')
            
            tracks = []
            for track in results['tracks']['items']:
                track_info = self._extract_track_info(track)
                if track_info:
                    tracks.append(track_info)
            
            logging.info(f"Found {len(tracks)} tracks for query: {query}")
            return tracks
            
        except Exception as e:
            logging.error(f"Failed to search tracks: {e}")
            raise SpotifyError(f"Track search failed: {e}")
    
    def get_track_features(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get audio features for a track.
        
        Args:
            track_id: Spotify track ID
            
        Returns:
            Track features dictionary or None if unavailable
        """
        if not self.is_ready():
            logging.warning("Spotify service not ready for track features")
            return None
        
        try:
            features = self.spotify.audio_features(track_id)
            if features and features[0]:
                return features[0]
            return None
            
        except Exception as e:
            logging.error(f"Failed to get track features: {e}")
            raise SpotifyError(f"Track features retrieval failed: {e}")
    
    def _normalize_weather_condition(self, condition: str) -> str:
        """Normalize weather condition to match genre mapping."""
        if not condition:
            return 'default'
        
        condition_lower = condition.lower()
        
        # Direct matches
        if condition_lower in self.WEATHER_GENRES:
            return condition_lower
        
        # Partial matches
        for key in self.WEATHER_GENRES.keys():
            if key in condition_lower or condition_lower in key:
                return key
        
        # Weather-specific mappings
        if any(word in condition_lower for word in ['sun', 'bright', 'clear']):
            return 'sunny'
        elif any(word in condition_lower for word in ['cloud', 'overcast']):
            return 'cloudy'
        elif any(word in condition_lower for word in ['rain', 'shower', 'precipitation']):
            return 'rain'
        elif any(word in condition_lower for word in ['storm', 'thunder']):
            return 'thunderstorm'
        elif any(word in condition_lower for word in ['snow', 'blizzard', 'flurr']):
            return 'snow'
        elif any(word in condition_lower for word in ['mist', 'fog', 'haze']):
            return 'mist'
        
        return 'default'
    
    def _extract_track_info(self, track: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract relevant information from Spotify track object."""
        try:
            artists = [artist['name'] for artist in track.get('artists', [])]
            
            return {
                'id': track.get('id'),
                'name': track.get('name'),
                'artists': artists,
                'artist_names': ', '.join(artists),
                'album': track.get('album', {}).get('name'),
                'duration_ms': track.get('duration_ms'),
                'popularity': track.get('popularity'),
                'preview_url': track.get('preview_url'),
                'external_url': track.get('external_urls', {}).get('spotify'),
                'image_url': track.get('album', {}).get('images', [{}])[0].get('url') if track.get('album', {}).get('images') else None
            }
        except Exception as e:
            logging.warning(f"Failed to extract track info: {e}")
            return None
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            'available': self.is_available(),
            'ready': self.is_ready(),
            'has_client_id': bool(self.settings.spotify_client_id),
            'has_client_secret': bool(self.settings.spotify_client_secret),
            'library_installed': spotipy is not None
        }