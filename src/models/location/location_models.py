"""Location Data Models

Defines structured data classes for geographic location information.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Location:
    """Geographic location information."""

    name: str
    country: str
    state: Optional[str] = None
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: Optional[str] = None
    elevation: Optional[float] = None  # meters above sea level
    population: Optional[int] = None
    region: Optional[str] = None
    admin_area: Optional[str] = None

    def __str__(self) -> str:
        """String representation of location."""
        if self.state:
            return f"{self.name}, {self.state}, {self.country}"
        return f"{self.name}, {self.country}"

    @property
    def coordinates(self) -> tuple[float, float]:
        """Get coordinates as (lat, lon) tuple."""
        return (self.latitude, self.longitude)

    @property
    def display_name(self) -> str:
        """Get formatted display name."""
        parts = [self.name]
        if self.state:
            parts.append(self.state)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)

    @property
    def short_name(self) -> str:
        """Get short name for display."""
        if self.state:
            return f"{self.name}, {self.state}"
        return self.name

    def distance_to(self, other: "Location") -> float:
        """Calculate distance to another location in kilometers using Haversine formula."""
        import math

        # Convert latitude and longitude from degrees to radians
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in kilometers
        r = 6371
        return c * r

    def is_nearby(self, other: "Location", threshold_km: float = 50.0) -> bool:
        """Check if another location is nearby within threshold."""
        return self.distance_to(other) <= threshold_km

    @classmethod
    def from_openweather(cls, data: Dict[str, Any]) -> "Location":
        """Create Location from OpenWeather API response."""
        coord = data.get("coord", {})
        sys_data = data.get("sys", {})

        return cls(
            name=data.get("name", "Unknown"),
            country=sys_data.get("country", "Unknown"),
            latitude=coord.get("lat", 0.0),
            longitude=coord.get("lon", 0.0),
        )

    @classmethod
    def from_geocoding(cls, data: Dict[str, Any]) -> "Location":
        """Create Location from geocoding API response."""
        return cls(
            name=data.get("name", "Unknown"),
            country=data.get("country", "Unknown"),
            state=data.get("state"),
            latitude=data.get("lat", 0.0),
            longitude=data.get("lon", 0.0),
        )


@dataclass
class LocationResult:
    """Enhanced location result for search and geocoding."""

    name: str
    display_name: str
    latitude: float
    longitude: float
    country: str = ""
    country_code: str = ""
    state: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    postcode: Optional[str] = None
    raw_address: str = ""
    importance: Optional[float] = None  # Search result relevance score
    place_type: Optional[str] = None  # city, town, village, etc.
    bbox: Optional[tuple[float, float, float, float]] = (
        None  # Bounding box (min_lat, min_lon, max_lat, max_lon)
    )

    def __str__(self) -> str:
        """String representation of location result."""
        return self.display_name

    @property
    def coordinates(self) -> tuple[float, float]:
        """Get coordinates as (lat, lon) tuple."""
        return (self.latitude, self.longitude)

    @property
    def short_display(self) -> str:
        """Get short display name."""
        parts = [self.name]
        if self.state:
            parts.append(self.state)
        elif self.country:
            parts.append(self.country)
        return ", ".join(parts)

    def to_location(self) -> Location:
        """Convert to basic Location object."""
        return Location(
            name=self.name,
            country=self.country,
            state=self.state,
            latitude=self.latitude,
            longitude=self.longitude,
        )

    @classmethod
    def from_nominatim(cls, data: Dict[str, Any]) -> "LocationResult":
        """Create LocationResult from Nominatim geocoding response."""
        address = data.get("address", {})

        return cls(
            name=data.get("name", data.get("display_name", "Unknown")),
            display_name=data.get("display_name", "Unknown"),
            latitude=float(data.get("lat", 0.0)),
            longitude=float(data.get("lon", 0.0)),
            country=address.get("country", ""),
            country_code=address.get("country_code", ""),
            state=address.get("state"),
            city=address.get("city") or address.get("town") or address.get("village"),
            county=address.get("county"),
            postcode=address.get("postcode"),
            raw_address=data.get("display_name", ""),
            importance=data.get("importance"),
            place_type=data.get("type"),
        )


@dataclass
class LocationSearchQuery:
    """Location search query parameters."""

    query: str
    country_code: Optional[str] = None
    limit: int = 10
    language: str = "en"
    include_bbox: bool = False
    min_importance: Optional[float] = None

    def to_params(self) -> Dict[str, Any]:
        """Convert to API parameters dictionary."""
        params = {
            "q": self.query,
            "format": "json",
            "limit": self.limit,
            "accept-language": self.language,
            "addressdetails": 1,
        }

        if self.country_code:
            params["countrycodes"] = self.country_code

        if self.include_bbox:
            params["extratags"] = 1

        return params
