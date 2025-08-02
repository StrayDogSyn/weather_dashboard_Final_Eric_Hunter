import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import List, Optional

import requests
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

from ..models.weather_models import LocationResult


class GeocodingService:
    """Service for geocoding, reverse geocoding, and location search."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.geolocator = Nominatim(user_agent="weather_dashboard_v1.0")
        self.cache = self.load_cache()
        self.cache_ttl = timedelta(hours=24)  # Cache for 24 hours

        # Regex patterns for different input types
        self.zip_patterns = {
            "US": re.compile(r"^\d{5}(-\d{4})?$"),  # 12345 or 12345-6789
            # SW1A 1AA
            "UK": re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$", re.IGNORECASE),
            # K1A 0A6
            "CA": re.compile(r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$", re.IGNORECASE),
        }

        self.coordinate_pattern = re.compile(r"^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$")

    def search_locations_advanced(self, query: str) -> List[LocationResult]:
        """Advanced location search supporting multiple formats."""
        query = query.strip()

        if not query:
            return []

        # Check cache first
        cache_key = f"search_{query.lower()}"
        cached_result = self.get_from_cache(cache_key)
        if cached_result:
            return [LocationResult(**item) for item in cached_result]

        results = []

        try:
            # Check if zip code
            if self.is_zip_code(query):
                results = self.geocode_zip(query)

            # Check if coordinates
            elif self.is_coordinates(query):
                results = self.reverse_geocode(query)

            # Standard city search with fuzzy matching
            else:
                results = self.search_cities_fuzzy(query)

            # Cache results
            if results:
                self.save_to_cache(cache_key, [result.__dict__ for result in results])

        except Exception as e:
            self.logger.error(f"Search error for '{query}': {e}")

        return results

    def is_zip_code(self, query: str) -> bool:
        """Check if query is a zip/postal code."""
        for pattern in self.zip_patterns.values():
            if pattern.match(query):
                return True
        return False

    def is_coordinates(self, query: str) -> bool:
        """Check if query is coordinates (lat,lon)."""
        return bool(self.coordinate_pattern.match(query))

    def geocode_zip(self, zip_code: str) -> List[LocationResult]:
        """Geocode a zip/postal code."""
        try:
            # Try different country contexts
            contexts = ["US", "GB", "CA", "AU"]

            for country in contexts:
                query = f"{zip_code}, {country}"
                location = self.geolocator.geocode(query, exactly_one=False, limit=3)

                if location:
                    results = []
                    locations = location if isinstance(location, list) else [location]

                    for loc in locations:
                        result = self.create_location_result(loc)
                        if result:
                            results.append(result)

                    if results:
                        return results

            return []

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            self.logger.error(f"Geocoding error for zip '{zip_code}': {e}")
            return []

    def reverse_geocode(self, coordinates: str) -> List[LocationResult]:
        """Reverse geocode coordinates."""
        try:
            match = self.coordinate_pattern.match(coordinates)
            if not match:
                return []

            lat, lon = float(match.group(1)), float(match.group(2))

            # Validate coordinate ranges
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return []

            location = self.geolocator.reverse(f"{lat}, {lon}", exactly_one=True)

            if location:
                result = self.create_location_result(location)
                return [result] if result else []

            return []

        except (ValueError, GeocoderTimedOut, GeocoderServiceError) as e:
            self.logger.error(f"Reverse geocoding error for '{coordinates}': {e}")
            return []

    def search_cities_fuzzy(self, query: str) -> List[LocationResult]:
        """Search cities with fuzzy matching."""
        try:
            # Search with different strategies
            strategies = [
                query,  # Exact query
                f"{query}, city",  # Add city context
                f"{query}*",  # Wildcard search
            ]

            all_results = []
            seen_locations = set()

            for search_query in strategies:
                try:
                    locations = self.geolocator.geocode(
                        search_query, exactly_one=False, limit=5, addressdetails=True
                    )

                    if locations:
                        locations = locations if isinstance(locations, list) else [locations]

                        for loc in locations:
                            # Avoid duplicates
                            location_key = f"{
                                loc.latitude:.4f},{
                                loc.longitude:.4f}"
                            if location_key not in seen_locations:
                                seen_locations.add(location_key)
                                result = self.create_location_result(loc)
                                if result and self.is_relevant_result(result, query):
                                    all_results.append(result)

                    # Stop if we have enough results
                    if len(all_results) >= 8:
                        break

                except (GeocoderTimedOut, GeocoderServiceError):
                    continue

            # Sort by relevance (exact matches first)
            all_results.sort(key=lambda x: self.calculate_relevance_score(x, query), reverse=True)

            return all_results[:8]

        except Exception as e:
            self.logger.error(f"City search error for '{query}': {e}")
            return []

    def create_location_result(self, location) -> Optional[LocationResult]:
        """Create LocationResult from geocoder result."""
        try:
            address = location.raw.get("address", {})

            # Extract location components
            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or address.get("county")
            )

            state = address.get("state") or address.get("province") or address.get("region")

            country = address.get("country", "")
            country_code = address.get("country_code", "").upper()

            # Create display name
            display_parts = []
            if city:
                display_parts.append(city)
            if state and state != city:
                display_parts.append(state)
            if country_code:
                display_parts.append(country_code)

            display_name = ", ".join(display_parts) if display_parts else location.address

            return LocationResult(
                name=city or location.address.split(",")[0],
                display_name=display_name,
                latitude=float(location.latitude),
                longitude=float(location.longitude),
                country=country,
                country_code=country_code,
                state=state,
                raw_address=location.address,
            )

        except Exception as e:
            self.logger.error(f"Error creating location result: {e}")
            return None

    def is_relevant_result(self, result: LocationResult, query: str) -> bool:
        """Check if result is relevant to the search query."""
        query_lower = query.lower()

        # Check if query matches any part of the location
        searchable_text = f"{
            result.name} {
            result.display_name} {
            result.raw_address}".lower()

        # Exact match gets highest priority
        if query_lower in searchable_text:
            return True

        # Check for partial matches
        query_words = query_lower.split()
        for word in query_words:
            if len(word) >= 3 and word in searchable_text:
                return True

        return False

    def calculate_relevance_score(self, result: LocationResult, query: str) -> float:
        """Calculate relevance score for sorting results."""
        query_lower = query.lower()
        score = 0.0

        # Exact name match
        if result.name.lower() == query_lower:
            score += 100

        # Name starts with query
        elif result.name.lower().startswith(query_lower):
            score += 80

        # Name contains query
        elif query_lower in result.name.lower():
            score += 60

        # Display name contains query
        elif query_lower in result.display_name.lower():
            score += 40

        # Address contains query
        elif query_lower in result.raw_address.lower():
            score += 20

        # Boost score for major cities (rough heuristic)
        major_cities = ["london", "paris", "tokyo", "new york", "los angeles", "chicago"]
        if result.name.lower() in major_cities:
            score += 10

        return score

    def get_current_location(self) -> Optional[LocationResult]:
        """Get current location using IP geolocation."""
        try:
            # Use a free IP geolocation service
            response = requests.get("http://ip-api.com/json/", timeout=5)
            data = response.json()

            if data.get("status") == "success":
                lat = data.get("lat")
                lon = data.get("lon")
                city = data.get("city")
                region = data.get("regionName")
                country = data.get("country")
                country_code = data.get("countryCode")

                if lat and lon:
                    display_name = f"{city}, {region}, {country_code}" if city else f"{country}"

                    return LocationResult(
                        name=city or country,
                        display_name=display_name,
                        latitude=float(lat),
                        longitude=float(lon),
                        country=country,
                        country_code=country_code,
                        state=region,
                        raw_address=display_name,
                    )

            return None

        except Exception as e:
            self.logger.error(f"Error getting current location: {e}")
            return None

    def load_cache(self) -> dict:
        """Load geocoding cache from file."""
        cache_file = os.path.join("cache", "geocoding_cache.json")

        try:
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading geocoding cache: {e}")

        return {}

    def save_cache(self):
        """Save geocoding cache to file."""
        cache_file = os.path.join("cache", "geocoding_cache.json")

        try:
            os.makedirs("cache", exist_ok=True)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving geocoding cache: {e}")

    def get_from_cache(self, key: str) -> Optional[dict]:
        """Get item from cache if not expired."""
        if key in self.cache:
            item = self.cache[key]
            timestamp = datetime.fromisoformat(item["timestamp"])

            if datetime.now() - timestamp < self.cache_ttl:
                return item["data"]
            else:
                # Remove expired item
                del self.cache[key]

        return None

    def save_to_cache(self, key: str, data: dict):
        """Save item to cache with timestamp."""
        self.cache[key] = {"data": data, "timestamp": datetime.now().isoformat()}

        # Clean up old cache entries periodically
        if len(self.cache) > 1000:
            self.cleanup_cache()

        # Save to file
        self.save_cache()

    def cleanup_cache(self):
        """Remove expired cache entries."""
        now = datetime.now()
        expired_keys = []

        for key, item in self.cache.items():
            timestamp = datetime.fromisoformat(item["timestamp"])
            if now - timestamp >= self.cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        self.logger.info(
            f"Cleaned up {
                len(expired_keys)} expired cache entries"
        )
