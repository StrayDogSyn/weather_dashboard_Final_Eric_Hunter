"""UI Data Transfer Objects

DTOs for user interface data structures and display formatting.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class DisplayMode(Enum):
    """UI display modes."""

    COMPACT = "compact"
    DETAILED = "detailed"
    CARD = "card"
    LIST = "list"
    GRID = "grid"


class AlertLevel(Enum):
    """UI alert levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class IconDTO:
    """Icon display DTO."""

    name: str
    source: str = "weather-icons"  # weather-icons, material-icons, fontawesome
    color: Optional[str] = None
    size: str = "medium"  # small, medium, large, xl

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "source": self.source, "color": self.color, "size": self.size}


@dataclass
class ColorSchemeDTO:
    """Color scheme DTO for UI theming."""

    primary: str
    secondary: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    accent: Optional[str] = None

    @classmethod
    def light_theme(cls) -> "ColorSchemeDTO":
        return cls(
            primary="#2196F3",
            secondary="#03DAC6",
            background="#FFFFFF",
            surface="#F5F5F5",
            text_primary="#212121",
            text_secondary="#757575",
            accent="#FF5722",
        )

    @classmethod
    def dark_theme(cls) -> "ColorSchemeDTO":
        return cls(
            primary="#BB86FC",
            secondary="#03DAC6",
            background="#121212",
            surface="#1E1E1E",
            text_primary="#FFFFFF",
            text_secondary="#B3B3B3",
            accent="#CF6679",
        )


@dataclass
class FormattedValueDTO:
    """Formatted value with unit and display options."""

    value: Union[int, float, str]
    unit: str
    formatted: str
    precision: int = 1
    show_unit: bool = True

    @classmethod
    def temperature(
        cls, celsius: float, unit: str = "°C", precision: int = 1
    ) -> "FormattedValueDTO":
        """Create temperature formatted value."""
        if unit == "°F":
            fahrenheit = (celsius * 9 / 5) + 32
            return cls(
                value=fahrenheit,
                unit=unit,
                formatted=f"{fahrenheit:.{precision}f}{unit}",
                precision=precision,
            )
        return cls(
            value=celsius,
            unit=unit,
            formatted=f"{celsius:.{precision}f}{unit}",
            precision=precision,
        )

    @classmethod
    def wind_speed(cls, mps: float, unit: str = "m/s", precision: int = 1) -> "FormattedValueDTO":
        """Create wind speed formatted value."""
        if unit == "km/h":
            kmh = mps * 3.6
            return cls(
                value=kmh, unit=unit, formatted=f"{kmh:.{precision}f} {unit}", precision=precision
            )
        elif unit == "mph":
            mph = mps * 2.237
            return cls(
                value=mph, unit=unit, formatted=f"{mph:.{precision}f} {unit}", precision=precision
            )
        return cls(
            value=mps, unit=unit, formatted=f"{mps:.{precision}f} {unit}", precision=precision
        )

    @classmethod
    def pressure(cls, hpa: float, unit: str = "hPa", precision: int = 0) -> "FormattedValueDTO":
        """Create pressure formatted value."""
        if unit == "inHg":
            inhg = hpa * 0.02953
            return cls(
                value=inhg, unit=unit, formatted=f"{inhg:.{precision}f} {unit}", precision=precision
            )
        return cls(
            value=hpa, unit=unit, formatted=f"{hpa:.{precision}f} {unit}", precision=precision
        )


@dataclass
class CurrentWeatherDisplayDTO:
    """Current weather display DTO."""

    location_name: str
    temperature: FormattedValueDTO
    feels_like: FormattedValueDTO
    condition: str
    condition_description: str
    icon: IconDTO
    humidity: int
    wind_speed: FormattedValueDTO
    wind_direction: str
    pressure: FormattedValueDTO
    visibility: Optional[FormattedValueDTO] = None
    uv_index: Optional[float] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    last_updated: str = ""
    is_day: bool = True

    def to_compact_dict(self) -> Dict[str, Any]:
        """Convert to compact display format."""
        return {
            "location": self.location_name,
            "temperature": self.temperature.formatted,
            "condition": self.condition,
            "icon": self.icon.to_dict(),
            "is_day": self.is_day,
        }

    def to_detailed_dict(self) -> Dict[str, Any]:
        """Convert to detailed display format."""
        return {
            "location": self.location_name,
            "temperature": self.temperature.formatted,
            "feels_like": self.feels_like.formatted,
            "condition": self.condition,
            "description": self.condition_description,
            "icon": self.icon.to_dict(),
            "humidity": f"{self.humidity}%",
            "wind": f"{self.wind_speed.formatted} {self.wind_direction}",
            "pressure": self.pressure.formatted,
            "visibility": self.visibility.formatted if self.visibility else None,
            "uv_index": self.uv_index,
            "sunrise": self.sunrise,
            "sunset": self.sunset,
            "last_updated": self.last_updated,
            "is_day": self.is_day,
        }


@dataclass
class ForecastItemDisplayDTO:
    """Forecast item display DTO."""

    timestamp: datetime
    date_label: str
    time_label: str
    temperature: FormattedValueDTO
    condition: str
    icon: IconDTO
    temperature_range: Optional[str] = None  # For daily forecasts
    precipitation_chance: Optional[int] = None
    wind_speed: Optional[FormattedValueDTO] = None
    humidity: Optional[int] = None

    def to_hourly_dict(self) -> Dict[str, Any]:
        """Convert to hourly forecast display format."""
        return {
            "time": self.time_label,
            "temperature": self.temperature.formatted,
            "condition": self.condition,
            "icon": self.icon.to_dict(),
            "precipitation": f"{self.precipitation_chance}%" if self.precipitation_chance else None,
            "wind": self.wind_speed.formatted if self.wind_speed else None,
        }

    def to_daily_dict(self) -> Dict[str, Any]:
        """Convert to daily forecast display format."""
        return {
            "date": self.date_label,
            "temperature_range": self.temperature_range,
            "condition": self.condition,
            "icon": self.icon.to_dict(),
            "precipitation": f"{self.precipitation_chance}%" if self.precipitation_chance else None,
            "humidity": f"{self.humidity}%" if self.humidity else None,
        }


@dataclass
class ForecastDisplayDTO:
    """Forecast display DTO."""

    location_name: str
    hourly_forecasts: List[ForecastItemDisplayDTO] = field(default_factory=list)
    daily_forecasts: List[ForecastItemDisplayDTO] = field(default_factory=list)
    last_updated: str = ""

    def get_hourly_display(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly forecast display data."""
        return [item.to_hourly_dict() for item in self.hourly_forecasts[:hours]]

    def get_daily_display(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily forecast display data."""
        return [item.to_daily_dict() for item in self.daily_forecasts[:days]]


@dataclass
class WeatherAlertDisplayDTO:
    """Weather alert display DTO."""

    title: str
    description: str
    severity: str
    level: AlertLevel
    start_time: str
    end_time: str
    duration: str
    source: str
    icon: IconDTO
    color: str
    is_active: bool = True

    def to_banner_dict(self) -> Dict[str, Any]:
        """Convert to banner display format."""
        return {
            "title": self.title,
            "description": (
                self.description[:100] + "..." if len(self.description) > 100 else self.description
            ),
            "severity": self.severity,
            "level": self.level.value,
            "color": self.color,
            "icon": self.icon.to_dict(),
            "is_active": self.is_active,
        }

    def to_detailed_dict(self) -> Dict[str, Any]:
        """Convert to detailed display format."""
        return {
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "level": self.level.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "source": self.source,
            "color": self.color,
            "icon": self.icon.to_dict(),
            "is_active": self.is_active,
        }


@dataclass
class LocationDisplayDTO:
    """Location display DTO."""

    name: str
    display_name: str
    country: str
    state: Optional[str] = None
    coordinates: Optional[str] = None  # Formatted coordinates
    timezone: Optional[str] = None
    is_favorite: bool = False
    is_current: bool = False

    def to_search_result_dict(self) -> Dict[str, Any]:
        """Convert to search result display format."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "country": self.country,
            "state": self.state,
            "coordinates": self.coordinates,
            "is_favorite": self.is_favorite,
        }

    def to_favorite_dict(self) -> Dict[str, Any]:
        """Convert to favorite location display format."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "is_current": self.is_current,
            "timezone": self.timezone,
        }


@dataclass
class ChartDataDTO:
    """Chart data DTO for weather visualizations."""

    labels: List[str]
    datasets: List[Dict[str, Any]]
    chart_type: str = "line"  # line, bar, area, scatter
    title: str = ""
    x_axis_label: str = ""
    y_axis_label: str = ""

    @classmethod
    def temperature_chart(
        cls, timestamps: List[str], temperatures: List[float], unit: str = "°C"
    ) -> "ChartDataDTO":
        """Create temperature chart data."""
        return cls(
            labels=timestamps,
            datasets=[
                {
                    "label": f"Temperature ({unit})",
                    "data": temperatures,
                    "borderColor": "#FF6B6B",
                    "backgroundColor": "rgba(255, 107, 107, 0.1)",
                    "fill": True,
                }
            ],
            chart_type="line",
            title="Temperature Trend",
            x_axis_label="Time",
            y_axis_label=f"Temperature ({unit})",
        )

    @classmethod
    def precipitation_chart(
        cls, timestamps: List[str], precipitation: List[float]
    ) -> "ChartDataDTO":
        """Create precipitation chart data."""
        return cls(
            labels=timestamps,
            datasets=[
                {
                    "label": "Precipitation (%)",
                    "data": precipitation,
                    "borderColor": "#4ECDC4",
                    "backgroundColor": "rgba(78, 205, 196, 0.3)",
                    "fill": True,
                }
            ],
            chart_type="bar",
            title="Precipitation Probability",
            x_axis_label="Time",
            y_axis_label="Precipitation (%)",
        )


@dataclass
class NotificationDTO:
    """Notification display DTO."""

    id: str
    title: str
    message: str
    level: AlertLevel
    timestamp: datetime
    is_read: bool = False
    is_persistent: bool = False
    action_label: Optional[str] = None
    action_url: Optional[str] = None
    icon: Optional[IconDTO] = None

    def to_toast_dict(self) -> Dict[str, Any]:
        """Convert to toast notification format."""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "level": self.level.value,
            "timestamp": self.timestamp.isoformat(),
            "icon": self.icon.to_dict() if self.icon else None,
            "action_label": self.action_label,
            "action_url": self.action_url,
        }

    def to_list_item_dict(self) -> Dict[str, Any]:
        """Convert to notification list item format."""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message[:100] + "..." if len(self.message) > 100 else self.message,
            "level": self.level.value,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M"),
            "is_read": self.is_read,
            "is_persistent": self.is_persistent,
            "icon": self.icon.to_dict() if self.icon else None,
        }


@dataclass
class DashboardLayoutDTO:
    """Dashboard layout configuration DTO."""

    widgets: List[Dict[str, Any]] = field(default_factory=list)
    columns: int = 12
    row_height: int = 60
    margin: List[int] = field(default_factory=lambda: [10, 10])
    container_padding: List[int] = field(default_factory=lambda: [10, 10])
    is_draggable: bool = True
    is_resizable: bool = True

    def add_widget(
        self,
        widget_type: str,
        x: int,
        y: int,
        w: int,
        h: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a widget to the layout."""
        widget = {
            "i": f"{widget_type}_{len(self.widgets)}",
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "type": widget_type,
            "config": config or {},
        }
        self.widgets.append(widget)

    @classmethod
    def default_layout(cls) -> "DashboardLayoutDTO":
        """Create default dashboard layout."""
        layout = cls()

        # Current weather widget
        layout.add_widget(
            "current_weather", 0, 0, 6, 4, {"show_details": True, "display_mode": "detailed"}
        )

        # Forecast widget
        layout.add_widget("forecast", 6, 0, 6, 4, {"forecast_type": "hourly", "hours": 12})

        # Alerts widget
        layout.add_widget("alerts", 0, 4, 12, 2, {"show_inactive": False})

        # Chart widget
        layout.add_widget("temperature_chart", 0, 6, 12, 4, {"chart_type": "line", "hours": 24})

        return layout


@dataclass
class WeatherDashboardDTO:
    """Complete weather dashboard DTO."""

    current_weather: Optional[CurrentWeatherDisplayDTO] = None
    forecast: Optional[ForecastDisplayDTO] = None
    alerts: List[WeatherAlertDisplayDTO] = field(default_factory=list)
    charts: List[ChartDataDTO] = field(default_factory=list)
    notifications: List[NotificationDTO] = field(default_factory=list)
    layout: Optional[DashboardLayoutDTO] = None
    theme: ColorSchemeDTO = field(default_factory=ColorSchemeDTO.light_theme)
    last_updated: datetime = field(default_factory=datetime.now)
    is_loading: bool = False
    error_message: Optional[str] = None

    def to_display_dict(self, display_mode: DisplayMode = DisplayMode.DETAILED) -> Dict[str, Any]:
        """Convert to display dictionary."""
        result = {
            "last_updated": self.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
            "is_loading": self.is_loading,
            "error_message": self.error_message,
            "theme": {
                "primary": self.theme.primary,
                "secondary": self.theme.secondary,
                "background": self.theme.background,
                "surface": self.theme.surface,
                "text_primary": self.theme.text_primary,
                "text_secondary": self.theme.text_secondary,
                "accent": self.theme.accent,
            },
        }

        if self.current_weather:
            if display_mode == DisplayMode.COMPACT:
                result["current_weather"] = self.current_weather.to_compact_dict()
            else:
                result["current_weather"] = self.current_weather.to_detailed_dict()

        if self.forecast:
            result["forecast"] = {
                "hourly": self.forecast.get_hourly_display(),
                "daily": self.forecast.get_daily_display(),
            }

        if self.alerts:
            if display_mode == DisplayMode.COMPACT:
                result["alerts"] = [alert.to_banner_dict() for alert in self.alerts[:3]]
            else:
                result["alerts"] = [alert.to_detailed_dict() for alert in self.alerts]

        if self.charts:
            result["charts"] = [
                {
                    "labels": chart.labels,
                    "datasets": chart.datasets,
                    "type": chart.chart_type,
                    "title": chart.title,
                    "x_axis_label": chart.x_axis_label,
                    "y_axis_label": chart.y_axis_label,
                }
                for chart in self.charts
            ]

        if self.notifications:
            result["notifications"] = [
                notif.to_toast_dict() for notif in self.notifications if not notif.is_read
            ]

        if self.layout:
            result["layout"] = {
                "widgets": self.layout.widgets,
                "columns": self.layout.columns,
                "row_height": self.layout.row_height,
                "margin": self.layout.margin,
                "container_padding": self.layout.container_padding,
                "is_draggable": self.layout.is_draggable,
                "is_resizable": self.layout.is_resizable,
            }

        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get dashboard summary for quick overview."""
        summary = {
            "has_current_weather": self.current_weather is not None,
            "has_forecast": self.forecast is not None,
            "alert_count": len([alert for alert in self.alerts if alert.is_active]),
            "notification_count": len([notif for notif in self.notifications if not notif.is_read]),
            "last_updated": self.last_updated.strftime("%H:%M"),
            "is_loading": self.is_loading,
            "has_error": self.error_message is not None,
        }

        if self.current_weather:
            summary["current_temperature"] = self.current_weather.temperature.formatted
            summary["current_condition"] = self.current_weather.condition
            summary["location"] = self.current_weather.location_name

        return summary
