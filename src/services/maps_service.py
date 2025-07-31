"""Google Maps Service - Location and Mapping Integration

Handles Google Maps API integration for geocoding, place search,
directions, and enhanced location services.
"""

import requests
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from .config_service import ConfigService


@dataclass
class PlaceResult:
    """Represents a place search result."""
    place_id: str
    name: str
    formatted_address: str
    latitude: float
    longitude: float
    types: List[str]
    rating: Optional[float] = None
    price_level: Optional[int] = None
    photo_reference: Optional[str] = None


@dataclass
class GeocodeResult:
    """Represents a geocoding result."""
    formatted_address: str
    latitude: float
    longitude: float
    place_id: str
    types: List[str]
    address_components: Dict[str, str]


@dataclass
class DirectionStep:
    """Represents a single step in directions."""
    instruction: str
    distance: str
    duration: str
    start_location: Tuple[float, float]
    end_location: Tuple[float, float]


@dataclass
class DirectionsResult:
    """Represents directions between two points."""
    origin: str
    destination: str
    distance: str
    duration: str
    steps: List[DirectionStep]
    polyline: str


class GoogleMapsService:
    """Google Maps API service for location and mapping functionality."""
    
    def __init__(self, config_service: ConfigService):
        """Initialize Google Maps service."""
        self.config = config_service
        self.logger = logging.getLogger('weather_dashboard.maps_service')
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_request_time = 0
        self._request_interval = 0.1  # 100ms between requests
        
        # Get API key from config
        self.api_key = self.config.get('google_maps_api_key')
        if not self.api_key:
            self.logger.warning("⚠️ Google Maps API key not found in configuration")
        
        self.base_url = "https://maps.googleapis.com/maps/api"
        
        self.logger.info("🗺️ Google Maps service initialized")
    
    def _rate_limit(self) -> None:
        """Implement rate limiting for API requests."""
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._request_interval:
            import time
            time.sleep(self._request_interval - time_since_last)
        
        self._last_request_time = datetime.now().timestamp()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any], max_age_seconds: int = 3600) -> bool:
        """Check if cache entry is still valid."""
        if 'timestamp' not in cache_entry:
            return False
        
        age = datetime.now().timestamp() - cache_entry['timestamp']
        return age < max_age_seconds
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API request with error handling and rate limiting."""
        if not self.api_key:
            self.logger.error("❌ Google Maps API key not available")
            return None
        
        try:
            # Rate limiting
            self._rate_limit()
            
            # Add API key
            params['key'] = self.api_key
            
            url = f"{self.base_url}/{endpoint}"
            
            self.logger.debug(f"🌐 Making Maps API request: {endpoint}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK':
                self.logger.error(f"❌ Maps API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Maps API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to parse Maps API response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Unexpected error in Maps API request: {e}")
            return None
    
    def geocode(self, address: str) -> Optional[GeocodeResult]:
        """Geocode an address to get coordinates and details."""
        cache_key = f"geocode_{address.lower()}"
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            self.logger.debug(f"📋 Using cached geocoding for {address}")
            cached_data = self._cache[cache_key]['data']
            return GeocodeResult(**cached_data)
        
        try:
            self.logger.info(f"🔍 Geocoding address: {address}")
            
            params = {
                'address': address,
                'language': 'en'
            }
            
            data = self._make_request('geocode/json', params)
            if not data or not data.get('results'):
                return None
            
            result = data['results'][0]
            geometry = result['geometry']['location']
            
            # Parse address components
            address_components = {}
            for component in result.get('address_components', []):
                for comp_type in component['types']:
                    address_components[comp_type] = component['long_name']
            
            geocode_result = GeocodeResult(
                formatted_address=result['formatted_address'],
                latitude=geometry['lat'],
                longitude=geometry['lng'],
                place_id=result['place_id'],
                types=result['types'],
                address_components=address_components
            )
            
            # Cache the result
            self._cache[cache_key] = {
                'timestamp': datetime.now().timestamp(),
                'data': asdict(geocode_result)
            }
            
            self.logger.info(f"✅ Geocoded {address} to {geometry['lat']}, {geometry['lng']}")
            return geocode_result
            
        except Exception as e:
            self.logger.error(f"❌ Geocoding failed for {address}: {e}")
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[GeocodeResult]:
        """Reverse geocode coordinates to get address."""
        cache_key = f"reverse_{latitude}_{longitude}"
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            self.logger.debug(f"📋 Using cached reverse geocoding for {latitude}, {longitude}")
            cached_data = self._cache[cache_key]['data']
            return GeocodeResult(**cached_data)
        
        try:
            self.logger.info(f"🔍 Reverse geocoding: {latitude}, {longitude}")
            
            params = {
                'latlng': f"{latitude},{longitude}",
                'language': 'en'
            }
            
            data = self._make_request('geocode/json', params)
            if not data or not data.get('results'):
                return None
            
            result = data['results'][0]
            geometry = result['geometry']['location']
            
            # Parse address components
            address_components = {}
            for component in result.get('address_components', []):
                for comp_type in component['types']:
                    address_components[comp_type] = component['long_name']
            
            geocode_result = GeocodeResult(
                formatted_address=result['formatted_address'],
                latitude=geometry['lat'],
                longitude=geometry['lng'],
                place_id=result['place_id'],
                types=result['types'],
                address_components=address_components
            )
            
            # Cache the result
            self._cache[cache_key] = {
                'timestamp': datetime.now().timestamp(),
                'data': asdict(geocode_result)
            }
            
            return geocode_result
            
        except Exception as e:
            self.logger.error(f"❌ Reverse geocoding failed: {e}")
            return None
    
    def search_places(self, query: str, location: Optional[Tuple[float, float]] = None, 
                     radius: int = 50000, place_type: Optional[str] = None) -> List[PlaceResult]:
        """Search for places using Google Places API."""
        cache_key = f"places_{query.lower()}_{location}_{radius}_{place_type}"
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key], 1800):  # 30 min cache
            self.logger.debug(f"📋 Using cached place search for {query}")
            cached_data = self._cache[cache_key]['data']
            return [PlaceResult(**item) for item in cached_data]
        
        try:
            self.logger.info(f"🔍 Searching places: {query}")
            
            params = {
                'query': query,
                'language': 'en'
            }
            
            if location:
                params['location'] = f"{location[0]},{location[1]}"
                params['radius'] = radius
            
            if place_type:
                params['type'] = place_type
            
            data = self._make_request('place/textsearch/json', params)
            if not data or not data.get('results'):
                return []
            
            results = []
            for result in data['results'][:10]:  # Limit to 10 results
                geometry = result['geometry']['location']
                
                # Get photo reference if available
                photo_ref = None
                if result.get('photos'):
                    photo_ref = result['photos'][0]['photo_reference']
                
                place_result = PlaceResult(
                    place_id=result['place_id'],
                    name=result['name'],
                    formatted_address=result.get('formatted_address', ''),
                    latitude=geometry['lat'],
                    longitude=geometry['lng'],
                    types=result.get('types', []),
                    rating=result.get('rating'),
                    price_level=result.get('price_level'),
                    photo_reference=photo_ref
                )
                results.append(place_result)
            
            # Cache the results
            self._cache[cache_key] = {
                'timestamp': datetime.now().timestamp(),
                'data': [asdict(result) for result in results]
            }
            
            self.logger.info(f"✅ Found {len(results)} places for {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Place search failed for {query}: {e}")
            return []
    
    def get_directions(self, origin: str, destination: str, mode: str = 'driving') -> Optional[DirectionsResult]:
        """Get directions between two points."""
        cache_key = f"directions_{origin.lower()}_{destination.lower()}_{mode}"
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key], 1800):  # 30 min cache
            self.logger.debug(f"📋 Using cached directions from {origin} to {destination}")
            cached_data = self._cache[cache_key]['data']
            return DirectionsResult(**cached_data)
        
        try:
            self.logger.info(f"🗺️ Getting directions from {origin} to {destination}")
            
            params = {
                'origin': origin,
                'destination': destination,
                'mode': mode,
                'language': 'en'
            }
            
            data = self._make_request('directions/json', params)
            if not data or not data.get('routes'):
                return None
            
            route = data['routes'][0]
            leg = route['legs'][0]
            
            # Parse steps
            steps = []
            for step in leg['steps']:
                direction_step = DirectionStep(
                    instruction=step['html_instructions'],
                    distance=step['distance']['text'],
                    duration=step['duration']['text'],
                    start_location=(step['start_location']['lat'], step['start_location']['lng']),
                    end_location=(step['end_location']['lat'], step['end_location']['lng'])
                )
                steps.append(direction_step)
            
            directions_result = DirectionsResult(
                origin=leg['start_address'],
                destination=leg['end_address'],
                distance=leg['distance']['text'],
                duration=leg['duration']['text'],
                steps=steps,
                polyline=route['overview_polyline']['points']
            )
            
            # Cache the result
            self._cache[cache_key] = {
                'timestamp': datetime.now().timestamp(),
                'data': asdict(directions_result)
            }
            
            return directions_result
            
        except Exception as e:
            self.logger.error(f"❌ Directions failed from {origin} to {destination}: {e}")
            return None
    
    def get_place_photo_url(self, photo_reference: str, max_width: int = 400) -> Optional[str]:
        """Get URL for a place photo."""
        if not self.api_key or not photo_reference:
            return None
        
        return f"{self.base_url}/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={self.api_key}"
    
    def get_static_map_url(self, center: Tuple[float, float], zoom: int = 13, 
                          size: Tuple[int, int] = (400, 300), markers: Optional[List[Tuple[float, float]]] = None) -> Optional[str]:
        """Generate URL for static map image."""
        if not self.api_key:
            return None
        
        params = {
            'center': f"{center[0]},{center[1]}",
            'zoom': zoom,
            'size': f"{size[0]}x{size[1]}",
            'maptype': 'roadmap',
            'key': self.api_key
        }
        
        if markers:
            marker_strings = []
            for lat, lng in markers:
                marker_strings.append(f"{lat},{lng}")
            params['markers'] = '|'.join(marker_strings)
        
        # Build URL
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}/staticmap?{param_string}"
    
    def clear_cache(self) -> None:
        """Clear the service cache."""
        self._cache.clear()
        self.logger.info("🗑️ Maps service cache cleared")