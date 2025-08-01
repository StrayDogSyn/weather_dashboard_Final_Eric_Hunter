"""Enhanced Weather Service - Extended API Integration

Handles weather data, air quality, astronomical data, and advanced search.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from ..models.weather_models import Location, WeatherCondition, WeatherData
from .config_service import ConfigService


@dataclass
class AirQualityData:
    """Air quality data model."""

    aqi: int  # Air Quality Index (1-5)
    co: float  # Carbon monoxide
    no: float  # Nitric oxide
    no2: float  # Nitrogen dioxide
    o3: float  # Ozone
    so2: float  # Sulphur dioxide
    pm2_5: float  # PM2.5
    pm10: float  # PM10
    nh3: float  # Ammonia
    timestamp: datetime

    def get_aqi_description(self) -> str:
        """Get AQI description."""
        descriptions = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
        return descriptions.get(self.aqi, "Unknown")

    def get_health_recommendation(self) -> str:
        """Get health recommendation based on AQI."""
        recommendations = {
            1: "Air quality is satisfactory for most people.",
            2: "Unusually sensitive people should consider reducing outdoor activities.",
            3: "Sensitive groups should reduce outdoor activities.",
            4: "Everyone should reduce outdoor activities.",
            5: "Everyone should avoid outdoor activities.",
        }
        return recommendations.get(self.aqi, "No recommendation available.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AirQualityData":
        """Create from dictionary."""
        if isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class AstronomicalData:
    """Astronomical data model."""

    sunrise: datetime
    sunset: datetime
    moonrise: Optional[datetime]
    moonset: Optional[datetime]
    moon_phase: float  # 0-1 (0 = new moon, 0.5 = full moon)
    day_length: timedelta

    def get_moon_phase_name(self) -> str:
        """Get moon phase name."""
        if self.moon_phase < 0.125:
            return "New Moon"
        elif self.moon_phase < 0.375:
            return "Waxing Crescent"
        elif self.moon_phase < 0.625:
            return "Full Moon"
        elif self.moon_phase < 0.875:
            return "Waning Crescent"
        else:
            return "New Moon"

    def get_moon_phase_emoji(self) -> str:
        """Get moon phase emoji."""
        if self.moon_phase < 0.125:
            return "🌑"
        elif self.moon_phase < 0.375:
            return "🌒"
        elif self.moon_phase < 0.625:
            return "🌕"
        elif self.moon_phase < 0.875:
            return "🌘"
        else:
            return "🌑"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["sunrise"] = self.sunrise.isoformat()
        data["sunset"] = self.sunset.isoformat()
        data["moonrise"] = self.moonrise.isoformat() if self.moonrise else None
        data["moonset"] = self.moonset.isoformat() if self.moonset else None
        data["day_length"] = self.day_length.total_seconds()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AstronomicalData":
        """Create from dictionary."""
        if isinstance(data["sunrise"], str):
            data["sunrise"] = datetime.fromisoformat(data["sunrise"])
        if isinstance(data["sunset"], str):
            data["sunset"] = datetime.fromisoformat(data["sunset"])
        if data["moonrise"] and isinstance(data["moonrise"], str):
            data["moonrise"] = datetime.fromisoformat(data["moonrise"])
        if data["moonset"] and isinstance(data["moonset"], str):
            data["moonset"] = datetime.fromisoformat(data["moonset"])
        if isinstance(data["day_length"], (int, float)):
            data["day_length"] = timedelta(seconds=data["day_length"])
        return cls(**data)


@dataclass
class WeatherAlert:
    """Weather alert data model."""

    event: str
    description: str
    severity: str  # minor, moderate, severe, extreme
    start_time: datetime
    end_time: datetime
    areas: List[str]

    def get_severity_color(self) -> str:
        """Get color for severity level."""
        colors = {
            "minor": "#FFEB3B",
            "moderate": "#FF9800",
            "severe": "#F44336",
            "extreme": "#9C27B0",
        }
        return colors.get(self.severity.lower(), "#757575")

    def get_severity_emoji(self) -> str:
        """Get emoji for severity level."""
        emojis = {"minor": "⚠️", "moderate": "🟡", "severe": "🔴", "extreme": "🟣"}
        return emojis.get(self.severity.lower(), "⚠️")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeatherAlert":
        """Create from dictionary."""
        if isinstance(data["start_time"], str):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if isinstance(data["end_time"], str):
            data["end_time"] = datetime.fromisoformat(data["end_time"])
        return cls(**data)


@dataclass
class EnhancedWeatherData(WeatherData):
    """Enhanced weather data with additional information."""

    air_quality: Optional[AirQualityData] = None
    astronomical: Optional[AstronomicalData] = None
    alerts: List[WeatherAlert] = None

    def __post_init__(self):
        if self.alerts is None:
            self.alerts = []


class LocationSearchResult:
    """Location search result with enhanced information."""

    def __init__(
        self,
        name: str,
        country: str,
        state: str = None,
        lat: float = None,
        lon: float = None,
        **kwargs,
    ):
        self.name = name
        self.country = country
        self.state = state
        self.lat = lat
        self.lon = lon
        self.display = self._create_display_name()

    def _create_display_name(self) -> str:
        """Create display name for location."""
        parts = [self.name]
        if self.state:
            parts.append(self.state)
        parts.append(self.country)
        return ", ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "country": self.country,
            "state": self.state,
            "lat": self.lat,
            "lon": self.lon,
            "display": self.display,
        }


class EnhancedWeatherService:
    """Enhanced weather service with extended capabilities."""

    def __init__(self, config_service: ConfigService):
        """Initialize enhanced weather service."""
        self.config = config_service
        self.logger = logging.getLogger("weather_dashboard.enhanced_weather_service")
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_file = Path.cwd() / "cache" / "enhanced_weather_cache.json"
        self._load_cache()

        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum seconds between requests

        # API endpoints
        self.base_url = self.config.weather.base_url
        self.api_key = self.config.weather.api_key

    def _load_cache(self) -> None:
        """Load enhanced weather cache from file."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                self.logger.debug(f"📁 Loaded enhanced cache with {len(self._cache)} entries")
        except Exception as e:
            self.logger.warning(f"Failed to load enhanced cache: {e}")
            self._cache = {}

    def _save_cache(self) -> None:
        """Save enhanced weather cache to file."""
        try:
            self._cache_file.parent.mkdir(exist_ok=True)
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, default=str)
            self.logger.debug("💾 Enhanced cache saved successfully")
        except Exception as e:
            self.logger.warning(f"Failed to save enhanced cache: {e}")

    def _is_cache_valid(self, cache_entry: Dict[str, Any], cache_duration: int = None) -> bool:
        """Check if cache entry is still valid."""
        try:
            cached_time = datetime.fromisoformat(cache_entry["timestamp"])
            duration = cache_duration or self.config.app.cache_duration
            cache_duration_delta = timedelta(seconds=duration)
            return datetime.now() - cached_time < cache_duration_delta
        except (KeyError, ValueError):
            return False

    def _rate_limit(self) -> None:
        """Implement rate limiting."""
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            import time

            time.sleep(sleep_time)

        self._last_request_time = datetime.now().timestamp()

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API request with enhanced error handling and rate limiting."""
        try:
            # Rate limiting
            self._rate_limit()

            # Add API key and default parameters
            params.update({"appid": self.api_key, "units": self.config.weather.units})

            url = f"{self.base_url}/{endpoint}"

            self.logger.debug(f"🌐 Making enhanced API request: {endpoint}")

            response = requests.get(url, params=params, timeout=self.config.weather.timeout)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            self.logger.error("⏰ Enhanced API request timed out")
            raise Exception("Weather service timeout - please try again")

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                self.logger.error("🔑 Invalid API key")
                raise Exception("Invalid API key - please check your configuration")
            elif response.status_code == 404:
                self.logger.debug("🏙️ Location not found")
                raise Exception("Location not found - please check the spelling")

    def _make_geocoding_request(
        self, endpoint: str, params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make geocoding API request with correct base URL."""
        try:
            # Rate limiting
            self._rate_limit()

            # Add API key (no units for geocoding)
            params.update({"appid": self.api_key})

            # Use correct geocoding base URL
            url = f"https://api.openweathermap.org/{endpoint}"

            self.logger.debug(f"🌐 Making geocoding API request: {endpoint}")

            response = requests.get(url, params=params, timeout=self.config.weather.timeout)

            if response.status_code == 404:
                # For geocoding, 404 just means location not found
                self.logger.debug("🏙️ Location not found")
                return None

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            self.logger.error("⏰ Geocoding API request timed out")
            raise Exception("Geocoding service timeout - please try again")

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                self.logger.error("🔑 Invalid API key for geocoding")
                raise Exception("Invalid API key - please check your configuration")
            else:
                self.logger.error(f"🌐 Geocoding API error: {response.status_code}")
                raise Exception(f"Geocoding service error: {response.status_code}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"🌐 Geocoding request failed: {e}")
            raise Exception("Geocoding service unavailable - please try again")

        except requests.exceptions.ConnectionError:
            self.logger.error("🌐 Connection error")
            raise Exception("No internet connection - please check your network")

        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {e}")
            raise Exception(f"Weather service error: {str(e)}")

    def search_locations(self, query: str, limit: int = 5) -> List[LocationSearchResult]:
        """Enhanced location search with support for multiple formats including zipcodes."""
        # Validate and clean query input
        if not query or not isinstance(query, str):
            self.logger.warning("Invalid search query: must be a non-empty string")
            return []

        query = query.strip()
        if len(query) < 2:
            self.logger.warning("Search query too short: must be at least 2 characters")
            return []

        # Validate limit parameter
        if not isinstance(limit, int) or limit < 1:
            limit = 5
        elif limit > 20:  # Reasonable upper bound
            limit = 20

        cache_key = f"search_{query.lower()}_{limit}"

        # Check cache first (longer cache for search results)
        if cache_key in self._cache and self._is_cache_valid(
            self._cache[cache_key], 3600
        ):  # 1 hour cache
            self.logger.debug(f"📋 Using cached search results for {query}")
            cached_data = self._cache[cache_key]["data"]
            return [LocationSearchResult(**item) for item in cached_data]

        try:
            self.logger.info(f"🔍 Enhanced search for locations: {query}")

            # Detect query type and use appropriate search method
            search_type = self._detect_query_type(query)
            self.logger.debug(f"🔍 Detected query type: {search_type} for '{query}'")

            locations = []

            if search_type == "zipcode":
                locations = self._search_by_zipcode(query, limit)
            elif search_type == "coordinates":
                locations = self._search_by_coordinates(query)
            else:
                # Default to geocoding search for city names and general queries
                locations = self._search_by_geocoding(query, limit)

            # If primary search fails, try fallback methods
            if not locations and search_type != "geocoding":
                self.logger.debug(f"🔄 Primary search failed, trying geocoding fallback")
                locations = self._search_by_geocoding(query, limit)

            # Cache the results
            self._cache[cache_key] = {
                "data": [loc.to_dict() for loc in locations],
                "timestamp": datetime.now().isoformat(),
            }
            self._save_cache()

            self.logger.info(f"✅ Found {len(locations)} locations for {query}")
            return locations

        except Exception as e:
            self.logger.warning(f"Enhanced location search failed: {e}")
            return []

    def _detect_query_type(self, query: str) -> str:
        """Detect the type of location query (zipcode, coordinates, or general)."""
        import re

        query = query.strip()

        # Check for coordinates (lat,lon format)
        coord_pattern = r"^-?\d+\.?\d*\s*,\s*-?\d+\.?\d*$"
        if re.match(coord_pattern, query):
            return "coordinates"

        # Check for US zipcode (5 digits or 5+4 format)
        us_zip_pattern = r"^\d{5}(-\d{4})?$"
        if re.match(us_zip_pattern, query):
            return "zipcode"

        # Check for international postal codes (various formats)
        # UK: SW1A 1AA, Canada: K1A 0A6, etc.
        intl_postal_patterns = [
            r"^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$",  # UK
            r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$",  # Canada
            r"^\d{4,5}$",  # Germany, France, etc.
            r"^\d{3}-\d{4}$",  # Japan
        ]

        for pattern in intl_postal_patterns:
            if re.match(pattern, query.upper()):
                return "zipcode"

        # Default to geocoding for city names and general queries
        return "geocoding"

    def _search_by_zipcode(self, zipcode: str, limit: int = 5) -> List[LocationSearchResult]:
        """Search location by zipcode using OpenWeather's zip endpoint with geocoding fallback."""
        try:
            # Format zipcode for API (remove spaces, handle international formats)
            formatted_zip = zipcode.replace(" ", "")

            # For US zipcodes, use simple format
            if formatted_zip.isdigit() and len(formatted_zip) == 5:
                query_param = f"{formatted_zip},US"
            elif "-" in formatted_zip and len(formatted_zip.split("-")[0]) == 5:
                # US ZIP+4 format
                query_param = f"{formatted_zip.split('-')[0]},US"
            else:
                # International postal code - try without country code first
                query_param = formatted_zip

            self.logger.debug(f"🏷️ Searching by zipcode: {query_param}")

            # Use zip endpoint for direct zipcode lookup
            data = self._make_geocoding_request("geo/1.0/zip", {"zip": query_param})

            if data and "lat" in data and "lon" in data:
                location = LocationSearchResult(
                    name=data.get("name", zipcode),
                    country=data.get("country", ""),
                    state="",  # Zip endpoint doesn't provide state
                    lat=data.get("lat"),
                    lon=data.get("lon"),
                )
                return [location]

            # If zip endpoint fails, try geocoding as fallback for international postal codes
            self.logger.debug(f"🔄 Zip endpoint failed, trying geocoding fallback for: {zipcode}")
            return self._search_by_geocoding(zipcode, limit)

        except Exception as e:
            self.logger.warning(f"Zipcode search failed for {zipcode}: {e}")
            # Try geocoding as final fallback
            try:
                return self._search_by_geocoding(zipcode, limit)
            except Exception as fallback_e:
                self.logger.warning(f"Geocoding fallback also failed for {zipcode}: {fallback_e}")
                return []

    def _search_by_coordinates(self, coords: str) -> List[LocationSearchResult]:
        """Search location by coordinates using reverse geocoding."""
        try:
            # Parse coordinates
            parts = coords.replace(" ", "").split(",")
            if len(parts) != 2:
                return []

            lat = float(parts[0])
            lon = float(parts[1])

            # Validate coordinate ranges
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                self.logger.warning(f"Invalid coordinates: {lat}, {lon}")
                return []

            # Warn about extreme coordinates that might not have meaningful results
            if abs(lat) >= 89 or abs(lon) >= 179:
                self.logger.debug(
                    f"⚠️ Using extreme coordinates: {lat}, {lon} - results may be limited"
                )

            self.logger.debug(f"🌍 Reverse geocoding coordinates: {lat}, {lon}")

            # Use reverse geocoding
            data = self._make_geocoding_request(
                "geo/1.0/reverse", {"lat": lat, "lon": lon, "limit": 1}
            )

            if data and len(data) > 0:
                item = data[0]
                location = LocationSearchResult(
                    name=item.get("name", f"{lat}, {lon}"),
                    country=item.get("country", ""),
                    state=item.get("state", ""),
                    lat=lat,
                    lon=lon,
                )
                return [location]

            # If reverse geocoding fails, still return the coordinates as a valid location
            self.logger.debug(f"🔄 Reverse geocoding failed, returning coordinates as location")
            location = LocationSearchResult(
                name=f"Location at {lat}, {lon}", country="", state="", lat=lat, lon=lon
            )
            return [location]

        except (ValueError, IndexError) as e:
            self.logger.warning(f"Coordinate parsing failed for {coords}: {e}")
            return []
        except Exception as e:
            self.logger.warning(f"Coordinate search failed for {coords}: {e}")
            return []

    def _search_by_geocoding(self, query: str, limit: int = 5) -> List[LocationSearchResult]:
        """Search location using standard geocoding API with multiple query strategies and enhanced fallback."""
        # Try multiple query formats for better results
        query_variations = self._generate_query_variations(query)

        # If query looks like a postal code, add international variations
        if self._detect_query_type(query) == "zipcode":
            postal_variations = [
                f"{query}, UK",
                f"{query}, Canada",
                f"{query}, Germany",
                f"{query}, France",
                f"{query}, Japan",
                f"{query}, Australia",
            ]
            query_variations.extend(postal_variations)

        for i, query_variant in enumerate(query_variations):
            try:
                self.logger.debug(
                    f"🏙️ Geocoding search attempt {i+1}/{len(query_variations)}: {query_variant}"
                )

                data = self._make_geocoding_request(
                    "geo/1.0/direct", {"q": query_variant, "limit": limit}
                )

                if data and len(data) > 0:
                    locations = []
                    for item in data:
                        location = LocationSearchResult(
                            name=item.get("name", ""),
                            country=item.get("country", ""),
                            state=item.get("state", ""),
                            lat=item.get("lat"),
                            lon=item.get("lon"),
                        )
                        locations.append(location)

                    self.logger.debug(
                        f"✅ Found {len(locations)} locations with query: {query_variant}"
                    )
                    return locations

            except Exception as e:
                self.logger.debug(f"Query variant '{query_variant}' failed: {e}")
                continue

        self.logger.warning(f"All geocoding attempts failed for: {query}")
        return []

    def _generate_query_variations(self, query: str) -> List[str]:
        """Generate multiple query variations to improve search success."""
        variations = [query.strip()]

        # Remove common suffixes that might confuse the API
        suffixes_to_try = [", United States", ", USA", ", US"]
        base_query = query.strip()

        for suffix in suffixes_to_try:
            if base_query.endswith(suffix):
                # Try without the suffix
                without_suffix = base_query[: -len(suffix)].strip()
                if without_suffix not in variations:
                    variations.append(without_suffix)
                break

        # For US locations, try different formats
        if "United States" in query or ", US" in query or ", USA" in query:
            parts = (
                base_query.replace(", United States", "")
                .replace(", USA", "")
                .replace(", US", "")
                .split(",")
            )
            if len(parts) >= 2:
                city = parts[0].strip()
                state = parts[1].strip()

                # Try "City, State" format
                city_state = f"{city}, {state}"
                if city_state not in variations:
                    variations.append(city_state)

                # Try "City, State, US" format
                city_state_us = f"{city}, {state}, US"
                if city_state_us not in variations:
                    variations.append(city_state_us)

                # Try just the city name
                if city not in variations:
                    variations.append(city)

        return variations

    def _geocode_query(self, query: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Make geocoding request with proper error handling."""
        try:
            # Use the new geocoding request method
            data = self._make_geocoding_request("geo/1.0/direct", {"q": query, "limit": limit})

            return data if data else []

        except Exception as e:
            if "Invalid API key" in str(e) or "Rate limit" in str(e):
                raise e
            raise Exception(f"Request failed: {str(e)}")

    def get_air_quality(self, lat: float, lon: float) -> Optional[AirQualityData]:
        """Get air quality data for coordinates."""
        cache_key = f"air_quality_{lat}_{lon}"

        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            self.logger.debug(f"📋 Using cached air quality data")
            return AirQualityData.from_dict(self._cache[cache_key]["data"])

        try:
            self.logger.info(f"🌬️ Fetching air quality for {lat}, {lon}")

            data = self._make_request("data/2.5/air_pollution", {"lat": lat, "lon": lon})

            if not data or "list" not in data or not data["list"]:
                self.logger.debug(f"🌬️ No air quality data available for coordinates {lat}, {lon}")
                return None

            pollution_data = data["list"][0]
            components = pollution_data["components"]

            air_quality = AirQualityData(
                aqi=pollution_data["main"]["aqi"],
                co=components.get("co", 0),
                no=components.get("no", 0),
                no2=components.get("no2", 0),
                o3=components.get("o3", 0),
                so2=components.get("so2", 0),
                pm2_5=components.get("pm2_5", 0),
                pm10=components.get("pm10", 0),
                nh3=components.get("nh3", 0),
                timestamp=datetime.now(),
            )

            # Cache the result
            self._cache[cache_key] = {
                "data": air_quality.to_dict(),
                "timestamp": datetime.now().isoformat(),
            }
            self._save_cache()

            self.logger.info(f"✅ Air quality data retrieved: AQI {air_quality.aqi}")
            return air_quality

        except Exception as e:
            # Handle specific air quality API errors more gracefully
            if "Location not found" in str(e) or "404" in str(e):
                self.logger.debug(f"🌬️ Air quality data not available for coordinates {lat}, {lon}")
            else:
                self.logger.warning(f"Air quality fetch failed: {e}")
            return None

    def get_astronomical_data(self, lat: float, lon: float) -> Optional[AstronomicalData]:
        """Get astronomical data for coordinates."""
        # This would typically use a separate astronomy API
        # For now, we'll simulate with basic sunrise/sunset from weather data
        try:
            data = self._make_request("weather", {"lat": lat, "lon": lon})

            if not data or "sys" not in data:
                return None

            sunrise = datetime.fromtimestamp(data["sys"]["sunrise"])
            sunset = datetime.fromtimestamp(data["sys"]["sunset"])
            day_length = sunset - sunrise

            # Simulate moon phase (in real app, use astronomy API)
            import random

            moon_phase = random.random()

            astronomical = AstronomicalData(
                sunrise=sunrise,
                sunset=sunset,
                moonrise=None,  # Would need astronomy API
                moonset=None,  # Would need astronomy API
                moon_phase=moon_phase,
                day_length=day_length,
            )

            return astronomical

        except Exception as e:
            self.logger.warning(f"Astronomical data fetch failed: {e}")
            return None

    def get_weather_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        """Get weather alerts for coordinates."""
        try:
            # This would use the One Call API alerts endpoint
            # For now, return empty list as alerts require special API access
            return []

        except Exception as e:
            self.logger.warning(f"Weather alerts fetch failed: {e}")
            return []

    def get_enhanced_weather(self, location: str) -> EnhancedWeatherData:
        """Get enhanced weather data with all additional information."""
        # Validate and clean location input
        if not location or not isinstance(location, str):
            raise ValueError("Location must be a non-empty string")

        location = location.strip()
        if len(location) < 2:
            raise ValueError("Location must be at least 2 characters long")

        cache_key = f"enhanced_{location.lower()}"

        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            self.logger.debug(f"📋 Using cached enhanced weather data for {location}")
            cached_data = self._cache[cache_key]["data"]

            # Reconstruct enhanced weather data
            weather_dict = cached_data["weather"].copy()
            # Convert location dict back to Location object
            if isinstance(weather_dict["location"], dict):
                weather_dict["location"] = Location(**weather_dict["location"])
            # Convert condition string back to WeatherCondition enum
            if isinstance(weather_dict["condition"], str):
                # Handle both enum string representation and direct value
                condition_str = weather_dict["condition"]
                if condition_str.startswith("WeatherCondition."):
                    # Extract the enum name (e.g., 'CLEAR' from 'WeatherCondition.CLEAR')
                    enum_name = condition_str.split(".")[-1]
                    weather_dict["condition"] = getattr(WeatherCondition, enum_name)
                else:
                    # Direct enum value (e.g., 'clear')
                    weather_dict["condition"] = WeatherCondition(condition_str)
            # Convert timestamp string back to datetime
            if isinstance(weather_dict["timestamp"], str):
                weather_dict["timestamp"] = datetime.fromisoformat(weather_dict["timestamp"])

            weather_data = EnhancedWeatherData(**weather_dict)
            if cached_data.get("air_quality"):
                weather_data.air_quality = AirQualityData.from_dict(cached_data["air_quality"])
            if cached_data.get("astronomical"):
                weather_data.astronomical = AstronomicalData.from_dict(cached_data["astronomical"])
            if cached_data.get("alerts"):
                weather_data.alerts = [
                    WeatherAlert.from_dict(alert) for alert in cached_data["alerts"]
                ]

            return weather_data

        # Fetch basic weather data first
        self.logger.info(f"🌤️ Fetching enhanced weather for {location}")

        data = self._make_request("weather", {"q": location})

        if not data:
            raise Exception("No weather data received")

        # Parse basic weather data
        location_obj = Location(
            name=data["name"],
            country=data["sys"]["country"],
            latitude=data["coord"]["lat"],
            longitude=data["coord"]["lon"],
        )

        condition = WeatherCondition.from_openweather(
            data["weather"][0]["main"], data["weather"][0]["description"]
        )

        weather_data = EnhancedWeatherData(
            location=location_obj,
            timestamp=datetime.now(),
            condition=condition,
            description=data["weather"][0]["description"].title(),
            temperature=round(data["main"]["temp"], 1),
            feels_like=round(data["main"]["feels_like"], 1),
            humidity=data["main"]["humidity"],
            pressure=data["main"]["pressure"],
            visibility=data.get("visibility", 0) // 1000 if data.get("visibility") else None,
            wind_speed=round(data["wind"]["speed"], 1) if "wind" in data else None,
            wind_direction=data["wind"].get("deg", 0) if "wind" in data else None,
            cloudiness=data["clouds"]["all"] if "clouds" in data else None,
            raw_data=data,
        )

        # Get coordinates for additional data
        lat = data["coord"]["lat"]
        lon = data["coord"]["lon"]

        # Fetch additional data
        weather_data.air_quality = self.get_air_quality(lat, lon)
        weather_data.astronomical = self.get_astronomical_data(lat, lon)
        weather_data.alerts = self.get_weather_alerts(lat, lon)

        # Cache the complete result
        cache_data = {
            "weather": asdict(weather_data),
            "air_quality": weather_data.air_quality.to_dict() if weather_data.air_quality else None,
            "astronomical": (
                weather_data.astronomical.to_dict() if weather_data.astronomical else None
            ),
            "alerts": (
                [alert.to_dict() for alert in weather_data.alerts] if weather_data.alerts else []
            ),
        }

        self._cache[cache_key] = {"data": cache_data, "timestamp": datetime.now().isoformat()}
        self._save_cache()

        self.logger.info(f"✅ Enhanced weather data retrieved for {location}")
        return weather_data

    def _get_wind_direction(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction."""
        if degrees is None:
            return "N"

        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]

        # Normalize degrees to 0-360 range
        degrees = degrees % 360

        # Calculate index (16 directions, so 360/16 = 22.5 degrees per direction)
        index = round(degrees / 22.5) % 16

        return directions[index]

    def get_weather(self, location: str) -> EnhancedWeatherData:
        """Get weather data - compatibility method that delegates to get_enhanced_weather."""
        return self.get_enhanced_weather(location)

    def get_current_weather(self, location: str = None) -> Dict[str, Any]:
        """Get current weather data in dictionary format for compatibility.

        Args:
            location: Location to get weather for. If None, uses default location.

        Returns:
            Dictionary containing current weather data
        """
        if location is None:
            location = "London"  # Default location

        try:
            enhanced_data = self.get_enhanced_weather(location)
            self.logger.debug(
                f"Enhanced data type: {type(enhanced_data)}, location type: {type(enhanced_data.location)}"
            )

            # Get forecast data
            forecast_data = self.get_forecast_data(location)

            # Convert to enhanced weather display format
            weather_dict = {
                "location": {
                    "name": enhanced_data.location.name,
                    "country": enhanced_data.location.country,
                },
                "current": {
                    "temp_c": enhanced_data.temperature,
                    "feelslike_c": enhanced_data.feels_like,
                    "humidity": enhanced_data.humidity,
                    "pressure_mb": enhanced_data.pressure,
                    "condition": {
                        "text": enhanced_data.description,
                        "code": enhanced_data.condition.value,
                    },
                    "wind_kph": (
                        enhanced_data.wind_speed * 3.6 if enhanced_data.wind_speed else 0
                    ),  # Convert m/s to km/h
                    "wind_dir": (
                        self._get_wind_direction(enhanced_data.wind_direction)
                        if enhanced_data.wind_direction
                        else "N"
                    ),
                    "vis_km": enhanced_data.visibility if enhanced_data.visibility else 0,
                    "cloud": enhanced_data.cloudiness if enhanced_data.cloudiness else 0,
                    "uv": 0,  # OpenWeatherMap doesn't provide UV in current weather
                },
                "timestamp": enhanced_data.timestamp.isoformat(),
                "air_quality": (
                    enhanced_data.air_quality.to_dict() if enhanced_data.air_quality else None
                ),
                "astronomical": (
                    enhanced_data.astronomical.to_dict() if enhanced_data.astronomical else None
                ),
            }

            # Add forecast data if available
            if forecast_data:
                weather_dict["forecast"] = forecast_data

            return weather_dict

        except Exception as e:
            self.logger.error(f"Failed to get current weather: {e}")
            # Return minimal fallback data
            return {
                "location": {"name": location, "country": ""},
                "current": {
                    "temp_c": 20.0,
                    "condition": {"text": "Weather data unavailable", "code": "unknown"},
                    "humidity": 0,
                    "pressure_mb": 0,
                    "wind_kph": 0,
                    "vis_km": 0,
                    "cloud": 0,
                },
                "timestamp": datetime.now().isoformat(),
            }

    def get_forecast_data(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Get forecast data from OpenWeatherMap API.

        Args:
            location: Location to get forecast for

        Returns:
            Dictionary containing forecast data in OpenWeatherMap format
        """
        try:
            # Check cache first
            cache_key = f"forecast_{location.lower()}"
            if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
                self.logger.debug(f"📋 Using cached forecast data for {location}")
                return self._cache[cache_key]["data"]

            # Fetch forecast data from API
            self.logger.info(f"🌤️ Fetching forecast data for {location}")

            forecast_data = self._make_request("forecast", {"q": location})

            if forecast_data:
                # Cache the forecast data
                self._cache[cache_key] = {"data": forecast_data, "timestamp": datetime.now()}
                self._save_cache()

                self.logger.debug(f"✅ Forecast data retrieved for {location}")
                return forecast_data
            else:
                self.logger.warning(f"No forecast data received for {location}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to get forecast data for {location}: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear enhanced weather cache."""
        self._cache.clear()
        if self._cache_file.exists():
            self._cache_file.unlink()
        self.logger.info("🗑️ Enhanced weather cache cleared")
