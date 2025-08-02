"""Weather Alert Data Models

Defines structured data classes for weather alerts and warnings.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class AlertSeverity(Enum):
    """Weather alert severity levels."""

    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"

    @property
    def level(self) -> int:
        """Get numeric severity level (1-4)."""
        severity_map = {self.MINOR: 1, self.MODERATE: 2, self.SEVERE: 3, self.EXTREME: 4}
        return severity_map.get(self, 1)

    @property
    def color(self) -> str:
        """Get color code for severity level."""
        color_map = {
            self.MINOR: "#FFD700",  # Gold
            self.MODERATE: "#FF8C00",  # Dark Orange
            self.SEVERE: "#FF4500",  # Orange Red
            self.EXTREME: "#DC143C",  # Crimson
        }
        return color_map.get(self, "#FFD700")


class AlertType(Enum):
    """Types of weather alerts."""

    TORNADO = "tornado"
    SEVERE_THUNDERSTORM = "severe_thunderstorm"
    FLASH_FLOOD = "flash_flood"
    FLOOD = "flood"
    WINTER_STORM = "winter_storm"
    BLIZZARD = "blizzard"
    ICE_STORM = "ice_storm"
    HIGH_WIND = "high_wind"
    HEAT = "heat"
    COLD = "cold"
    FOG = "fog"
    DUST_STORM = "dust_storm"
    FIRE_WEATHER = "fire_weather"
    COASTAL_FLOOD = "coastal_flood"
    HURRICANE = "hurricane"
    TROPICAL_STORM = "tropical_storm"
    OTHER = "other"


@dataclass
class WeatherAlert:
    """Weather alert/warning information."""

    title: str
    description: str
    severity: str  # "minor", "moderate", "severe", "extreme"
    start_time: datetime
    end_time: datetime
    source: str = "Unknown"
    alert_type: Optional[AlertType] = None
    areas: list[str] = None
    instructions: Optional[str] = None
    urgency: Optional[str] = None  # "immediate", "expected", "future", "past"
    certainty: Optional[str] = None  # "observed", "likely", "possible", "unlikely"

    def __post_init__(self):
        """Initialize computed fields after dataclass creation."""
        if self.areas is None:
            self.areas = []

    @property
    def is_active(self) -> bool:
        """Check if alert is currently active."""
        now = datetime.now()
        return self.start_time <= now <= self.end_time

    @property
    def severity_level(self) -> int:
        """Get numeric severity level (1-4)."""
        severity_map = {"minor": 1, "moderate": 2, "severe": 3, "extreme": 4}
        return severity_map.get(self.severity.lower(), 1)

    @property
    def severity_enum(self) -> AlertSeverity:
        """Get severity as enum."""
        try:
            return AlertSeverity(self.severity.lower())
        except ValueError:
            return AlertSeverity.MINOR

    @property
    def duration_hours(self) -> float:
        """Get alert duration in hours."""
        duration = self.end_time - self.start_time
        return duration.total_seconds() / 3600

    @property
    def time_remaining_hours(self) -> Optional[float]:
        """Get remaining time in hours, None if expired."""
        if not self.is_active:
            return None

        now = datetime.now()
        if now > self.end_time:
            return 0.0

        remaining = self.end_time - now
        return remaining.total_seconds() / 3600

    @property
    def is_urgent(self) -> bool:
        """Check if alert requires immediate attention."""
        return (
            self.urgency == "immediate"
            or self.severity_level >= 3
            or (self.time_remaining_hours is not None and self.time_remaining_hours < 2)
        )

    def get_display_title(self) -> str:
        """Get formatted title for display."""
        severity_prefix = {"minor": "⚠️", "moderate": "🟡", "severe": "🟠", "extreme": "🔴"}
        prefix = severity_prefix.get(self.severity.lower(), "⚠️")
        return f"{prefix} {self.title}"

    def get_short_description(self, max_length: int = 100) -> str:
        """Get truncated description for display."""
        if len(self.description) <= max_length:
            return self.description
        return self.description[: max_length - 3] + "..."

    @classmethod
    def from_openweather(cls, alert_data: dict) -> "WeatherAlert":
        """Create WeatherAlert from OpenWeather API alert data."""
        return cls(
            title=alert_data.get("event", "Weather Alert"),
            description=alert_data.get("description", ""),
            severity="moderate",  # OpenWeather doesn't provide severity
            start_time=datetime.fromtimestamp(alert_data.get("start", 0)),
            end_time=datetime.fromtimestamp(alert_data.get("end", 0)),
            source=alert_data.get("sender_name", "OpenWeather"),
            areas=alert_data.get("tags", []),
        )
