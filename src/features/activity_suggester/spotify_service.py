"""Spotify integration for mood-based music recommendations.

This module provides music recommendations that complement activity suggestions
based on activity type, weather conditions, and user mood.
"""

import logging
from typing import Optional, Dict, Any

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except ImportError:
    spotipy = None

from .models import ActivitySuggestion, ActivityCategory


class SpotifyIntegration:
    """Spotify integration for mood-based music recommendations."""

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.spotify = None
        self.logger = logging.getLogger(__name__)

        if client_id and client_secret and spotipy:
            try:
                credentials = SpotifyClientCredentials(
                    client_id=client_id,
                    client_secret=client_secret
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=credentials)
                self.logger.info("Spotify integration initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing Spotify: {e}")
                self.spotify = None
        else:
            self.logger.warning("Spotify integration not available")

    def get_activity_playlist(
        self,
        activity: ActivitySuggestion,
        weather_data
    ) -> Optional[Dict[str, Any]]:
        """Get Spotify playlist recommendations for an activity."""
        if not self.spotify:
            return None

        try:
            # Determine mood and genre based on activity and weather
            mood_keywords = self._get_mood_keywords(activity, weather_data)

            # Search for playlists
            results = self.spotify.search(
                q=f"{mood_keywords} {activity.category.value}",
                type='playlist',
                limit=5
            )

            if results['playlists']['items']:
                playlist = results['playlists']['items'][0]
                return {
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'description': playlist['description'],
                    'url': playlist['external_urls']['spotify'],
                    'image_url': playlist['images'][0]['url'] if playlist['images'] else None,
                    'tracks_total': playlist['tracks']['total']
                }

            return None

        except Exception as e:
            self.logger.error(f"Error getting Spotify playlist: {e}")
            return None

    def search_playlists_by_mood(self, mood: str, limit: int = 10) -> list:
        """Search for playlists by mood keywords."""
        if not self.spotify:
            return []

        try:
            results = self.spotify.search(q=mood, type='playlist', limit=limit)
            playlists = []
            
            for playlist in results['playlists']['items']:
                playlists.append({
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'description': playlist['description'],
                    'url': playlist['external_urls']['spotify'],
                    'image_url': playlist['images'][0]['url'] if playlist['images'] else None,
                    'tracks_total': playlist['tracks']['total']
                })
            
            return playlists
        except Exception as e:
            self.logger.error(f"Error searching playlists: {e}")
            return []

    def get_playlist_tracks(self, playlist_id: str, limit: int = 50) -> list:
        """Get tracks from a specific playlist."""
        if not self.spotify:
            return []

        try:
            results = self.spotify.playlist_tracks(playlist_id, limit=limit)
            tracks = []
            
            for item in results['items']:
                track = item['track']
                if track:
                    tracks.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'duration_ms': track['duration_ms'],
                        'preview_url': track.get('preview_url'),
                        'external_url': track['external_urls']['spotify']
                    })
            
            return tracks
        except Exception as e:
            self.logger.error(f"Error getting playlist tracks: {e}")
            return []

    def _get_mood_keywords(self, activity: ActivitySuggestion, weather_data) -> str:
        """Generate mood keywords for playlist search."""
        keywords = []

        # Activity-based keywords
        if activity.category == ActivityCategory.EXERCISE:
            keywords.extend(["workout", "energetic", "upbeat"])
        elif activity.category == ActivityCategory.RELAXATION:
            keywords.extend(["chill", "relaxing", "ambient"])
        elif activity.category == ActivityCategory.CREATIVE:
            keywords.extend(["focus", "instrumental", "creative"])
        elif activity.category == ActivityCategory.OUTDOOR:
            keywords.extend(["adventure", "nature", "uplifting"])
        elif activity.category == ActivityCategory.SOCIAL:
            keywords.extend(["party", "social", "fun"])
        elif activity.category == ActivityCategory.CULINARY:
            keywords.extend(["cooking", "jazz", "smooth"])
        elif activity.category == ActivityCategory.EDUCATIONAL:
            keywords.extend(["study", "focus", "classical"])
        elif activity.category == ActivityCategory.ENTERTAINMENT:
            keywords.extend(["fun", "entertainment", "popular"])
        else:
            keywords.extend(["mood", "ambient"])

        # Weather-based keywords
        if hasattr(weather_data, 'condition'):
            if 'sunny' in weather_data.condition.lower():
                keywords.extend(["sunny", "happy", "bright"])
            elif 'rain' in weather_data.condition.lower():
                keywords.extend(["rainy", "cozy", "mellow"])
            elif 'snow' in weather_data.condition.lower():
                keywords.extend(["winter", "peaceful", "calm"])
            elif 'cloud' in weather_data.condition.lower():
                keywords.extend(["cloudy", "calm", "mellow"])

        # Difficulty-based keywords
        if activity.difficulty.value == "easy":
            keywords.extend(["easy", "calm"])
        elif activity.difficulty.value in ["challenging", "expert"]:
            keywords.extend(["intense", "energy"])

        return " ".join(keywords[:3])  # Use top 3 keywords

    def is_available(self) -> bool:
        """Check if Spotify integration is available."""
        return self.spotify is not None

    def get_featured_playlists(self, limit: int = 20) -> list:
        """Get Spotify's featured playlists."""
        if not self.spotify:
            return []

        try:
            results = self.spotify.featured_playlists(limit=limit)
            playlists = []
            
            for playlist in results['playlists']['items']:
                playlists.append({
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'description': playlist['description'],
                    'url': playlist['external_urls']['spotify'],
                    'image_url': playlist['images'][0]['url'] if playlist['images'] else None,
                    'tracks_total': playlist['tracks']['total']
                })
            
            return playlists
        except Exception as e:
            self.logger.error(f"Error getting featured playlists: {e}")
            return []