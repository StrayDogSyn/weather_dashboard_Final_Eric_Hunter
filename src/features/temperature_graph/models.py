"""Data models and configuration for temperature graph feature.

This module contains all data structures, enums, and configuration classes
used by the temperature graph visualization system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class ChartType(Enum):
    """Available chart visualization types.

    This enum supports multiple visualization modes
    for comprehensive temperature analysis.
    """
    LINE = "line"
    AREA = "area"
    BAR = "bar"
    SCATTER = "scatter"
    CANDLESTICK = "candlestick"


class TimeRange(Enum):
    """Time range options for temperature data display.

    This enum provides flexible time-based data filtering
    for different analysis needs.
    """
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    CUSTOM = "custom"


@dataclass
class ChartConfig:
    """Configuration for temperature chart appearance and behavior.

    This dataclass demonstrates professional chart configuration
    with comprehensive styling and interaction options.
    """
    chart_type: ChartType = ChartType.LINE
    time_range: TimeRange = TimeRange.LAST_7_DAYS
    show_grid: bool = True
    show_legend: bool = True
    show_annotations: bool = True
    enable_zoom: bool = True
    enable_pan: bool = True
    auto_refresh: bool = True
    refresh_interval: int = 300  # seconds

    # Styling options
    background_color: str = "#1a1a1a"
    grid_color: str = "#333333"
    text_color: str = "#ffffff"
    line_color: str = "#4A90E2"
    fill_color: str = "#B8D4F0"

    # Chart dimensions
    figure_width: float = 12.0
    figure_height: float = 6.0
    dpi: int = 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'chart_type': self.chart_type.value,
            'time_range': self.time_range.value,
            'show_grid': self.show_grid,
            'show_legend': self.show_legend,
            'show_annotations': self.show_annotations,
            'enable_zoom': self.enable_zoom,
            'enable_pan': self.enable_pan,
            'auto_refresh': self.auto_refresh,
            'refresh_interval': self.refresh_interval,
            'background_color': self.background_color,
            'grid_color': self.grid_color,
            'text_color': self.text_color,
            'line_color': self.line_color,
            'fill_color': self.fill_color,
            'figure_width': self.figure_width,
            'figure_height': self.figure_height,
            'dpi': self.dpi
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChartConfig':
        """Create from dictionary."""
        return cls(
            chart_type=ChartType(data.get('chart_type', ChartType.LINE.value)),
            time_range=TimeRange(data.get('time_range', TimeRange.LAST_7_DAYS.value)),
            show_grid=data.get('show_grid', True),
            show_legend=data.get('show_legend', True),
            show_annotations=data.get('show_annotations', True),
            enable_zoom=data.get('enable_zoom', True),
            enable_pan=data.get('enable_pan', True),
            auto_refresh=data.get('auto_refresh', True),
            refresh_interval=data.get('refresh_interval', 300),
            background_color=data.get('background_color', "#1a1a1a"),
            grid_color=data.get('grid_color', "#333333"),
            text_color=data.get('text_color', "#ffffff"),
            line_color=data.get('line_color', "#4A90E2"),
            fill_color=data.get('fill_color', "#B8D4F0"),
            figure_width=data.get('figure_width', 12.0),
            figure_height=data.get('figure_height', 6.0),
            dpi=data.get('dpi', 100)
        )


@dataclass
class TemperatureDataPoint:
    """Single temperature data point with metadata.

    This dataclass provides structured temperature data
    with comprehensive metadata for analysis.
    """
    timestamp: datetime
    temperature: float
    feels_like: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    condition: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'wind_speed': self.wind_speed,
            'condition': self.condition,
            'location': self.location
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemperatureDataPoint':
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            temperature=data['temperature'],
            feels_like=data.get('feels_like'),
            humidity=data.get('humidity'),
            pressure=data.get('pressure'),
            wind_speed=data.get('wind_speed'),
            condition=data.get('condition'),
            location=data.get('location')
        )


@dataclass
class ChartAnalytics:
    """Analytics data for temperature charts."""
    min_temperature: float
    max_temperature: float
    avg_temperature: float
    temperature_trend: str  # "rising", "falling", "stable"
    data_points_count: int
    time_span_hours: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'min_temperature': self.min_temperature,
            'max_temperature': self.max_temperature,
            'avg_temperature': self.avg_temperature,
            'temperature_trend': self.temperature_trend,
            'data_points_count': self.data_points_count,
            'time_span_hours': self.time_span_hours
        }


@dataclass
class ExportSettings:
    """Settings for chart export functionality."""
    format: str = "png"  # png, pdf, svg, jpg
    dpi: int = 300
    transparent: bool = False
    include_metadata: bool = True
    watermark: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'format': self.format,
            'dpi': self.dpi,
            'transparent': self.transparent,
            'include_metadata': self.include_metadata,
            'watermark': self.watermark
        }