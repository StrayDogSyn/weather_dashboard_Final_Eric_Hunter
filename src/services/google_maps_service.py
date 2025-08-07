"""Google Maps Service - Location and Mapping Integration

Handles Google Maps API integration for geocoding, place search,
directions, and enhanced location services.
"""

import requests
import logging
from typing import Dict, Any, Optional, List, Tuple
import json
from dataclasses import dataclass

from .config.config_service import ConfigService


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
        self.logger = logging.getLogger('weather_dashboard.google_maps_service')
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_request_time = 0
        self._request_interval = 0.1  # 100ms between requests
        
        # Get API key from config
        self.api_key = self.config.get_setting('api.google_maps_api_key')
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
    
    def _make_request(self, endpoint: str, params: Dict[str, Any], cache_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Make API request with caching and rate limiting."""
        # Check cache first
        if cache_key and cache_key in self._cache:
            if self._is_cache_valid(self._cache[cache_key]):
                self.logger.debug(f"📋 Using cached result for {cache_key}")
                return self._cache[cache_key]['data']
        
        if not self.api_key:
            self.logger.error("❌ No API key available for Google Maps request")
            return None
        
        try:
            self._rate_limit()
            
            # Add API key to params
            params['key'] = self.api_key
            
            url = f"{self.base_url}/{endpoint}"
            self.logger.debug(f"🌐 Making request to {url}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK':
                self.logger.error(f"❌ API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
                return None
            
            # Cache successful response
            if cache_key:
                self._cache[cache_key] = {
                    'data': data,
                    'timestamp': datetime.now().timestamp()
                }
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to parse response: {e}")
            return None
    
    def search_places(self, query: str, location: Optional[Tuple[float, float]] = None, 
                     radius: int = 50000) -> List[PlaceResult]:
        """Search for places using text query."""
        self.logger.info(f"🔍 Searching places: {query}")
        
        params = {
            'query': query,
            'fields': 'place_id,name,formatted_address,geometry,types,rating,price_level,photos'
        }
        
        if location:
            params['location'] = f"{location[0]},{location[1]}"
            params['radius'] = radius
        
        cache_key = f"search_{hash(str(params))}"
        data = self._make_request('place/textsearch/json', params, cache_key)
        
        if not data:
            return []
        
        results = []
        for result in data.get('results', []):
            try:
                geometry = result.get('geometry', {})
                location_data = geometry.get('location', {})
                
                photo_ref = None
                if 'photos' in result and result['photos']:
                    photo_ref = result['photos'][0].get('photo_reference')
                
                place = PlaceResult(
                    place_id=result.get('place_id', ''),
                    name=result.get('name', ''),
                    formatted_address=result.get('formatted_address', ''),
                    latitude=location_data.get('lat', 0.0),
                    longitude=location_data.get('lng', 0.0),
                    types=result.get('types', []),
                    rating=result.get('rating'),
                    price_level=result.get('price_level'),
                    photo_reference=photo_ref
                )
                results.append(place)
                
            except Exception as e:
                self.logger.error(f"❌ Error parsing place result: {e}")
                continue
        
        self.logger.info(f"✅ Found {len(results)} places")
        return results
    
    def geocode(self, address: str) -> Optional[GeocodeResult]:
        """Geocode an address to coordinates."""
        self.logger.info(f"📍 Geocoding: {address}")
        
        params = {'address': address}
        cache_key = f"geocode_{hash(address)}"
        data = self._make_request('geocode/json', params, cache_key)
        
        if not data or not data.get('results'):
            return None
        
        result = data['results'][0]
        geometry = result.get('geometry', {})
        location = geometry.get('location', {})
        
        # Parse address components
        address_components = {}
        for component in result.get('address_components', []):
            for comp_type in component.get('types', []):
                address_components[comp_type] = component.get('long_name', '')
        
        geocode_result = GeocodeResult(
            formatted_address=result.get('formatted_address', ''),
            latitude=location.get('lat', 0.0),
            longitude=location.get('lng', 0.0),
            place_id=result.get('place_id', ''),
            types=result.get('types', []),
            address_components=address_components
        )
        
        self.logger.info(f"✅ Geocoded to: {geocode_result.latitude}, {geocode_result.longitude}")
        return geocode_result
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[GeocodeResult]:
        """Reverse geocode coordinates to address."""
        self.logger.info(f"📍 Reverse geocoding: {latitude}, {longitude}")
        
        params = {'latlng': f"{latitude},{longitude}"}
        cache_key = f"reverse_{hash(str(params))}"
        data = self._make_request('geocode/json', params, cache_key)
        
        if not data or not data.get('results'):
            return None
        
        result = data['results'][0]
        geometry = result.get('geometry', {})
        location = geometry.get('location', {})
        
        # Parse address components
        address_components = {}
        for component in result.get('address_components', []):
            for comp_type in component.get('types', []):
                address_components[comp_type] = component.get('long_name', '')
        
        geocode_result = GeocodeResult(
            formatted_address=result.get('formatted_address', ''),
            latitude=location.get('lat', 0.0),
            longitude=location.get('lng', 0.0),
            place_id=result.get('place_id', ''),
            types=result.get('types', []),
            address_components=address_components
        )
        
        self.logger.info(f"✅ Reverse geocoded to: {geocode_result.formatted_address}")
        return geocode_result
    
    def get_directions(self, origin: str, destination: str, mode: str = 'driving') -> Optional[DirectionsResult]:
        """Get directions between two points."""
        self.logger.info(f"🗺️ Getting directions: {origin} → {destination}")
        
        params = {
            'origin': origin,
            'destination': destination,
            'mode': mode
        }
        
        cache_key = f"directions_{hash(str(params))}"
        data = self._make_request('directions/json', params, cache_key)
        
        if not data or not data.get('routes'):
            return None
        
        route = data['routes'][0]
        leg = route['legs'][0]
        
        # Parse steps
        steps = []
        for step in leg.get('steps', []):
            direction_step = DirectionStep(
                instruction=step.get('html_instructions', ''),
                distance=step.get('distance', {}).get('text', ''),
                duration=step.get('duration', {}).get('text', ''),
                start_location=(
                    step.get('start_location', {}).get('lat', 0.0),
                    step.get('start_location', {}).get('lng', 0.0)
                ),
                end_location=(
                    step.get('end_location', {}).get('lat', 0.0),
                    step.get('end_location', {}).get('lng', 0.0)
                )
            )
            steps.append(direction_step)
        
        directions_result = DirectionsResult(
            origin=leg.get('start_address', ''),
            destination=leg.get('end_address', ''),
            distance=leg.get('distance', {}).get('text', ''),
            duration=leg.get('duration', {}).get('text', ''),
            steps=steps,
            polyline=route.get('overview_polyline', {}).get('points', '')
        )
        
        self.logger.info(f"✅ Found route: {directions_result.distance}, {directions_result.duration}")
        return directions_result
    
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
        self.logger.info("🗑️ Google Maps service cache cleared")