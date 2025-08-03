"""UI Components Package

This package contains reusable UI components for the weather dashboard.
"""

from .animation_manager import AnimationManager, LoadingSkeleton, MicroInteractions, ShimmerEffect

# from .weather_card import WeatherCard  # Module not found
# from .forecast_panel import ForecastPanel  # Module not found
# from .chart_panel import ChartPanel  # Module not found
from .city_comparison_panel import CityComparisonPanel
from .common import HeaderComponent, SearchBar, StatusBarComponent
from .error_manager import ErrorCard, ErrorLevel, ErrorManager, NotificationToast
from .ml_comparison_panel import MLComparisonPanel
from .status_manager import StatusMessageManager, StatusType, TooltipManager
from .visual_polish import (
    GlassMorphism,
    KeyboardShortcuts,
    ShadowSystem,
    SpacingGrid,
    VisualPolishManager,
)
from .weather_effects import (
    ParticleSystem,
    TemperatureGradient,
    WeatherBackgroundManager,
)

__all__ = [
    # 'WeatherCard',  # Module not found
    # 'ForecastPanel',  # Module not found
    # 'ChartPanel',  # Module not found
    "CityComparisonPanel",
    "MLComparisonPanel",
    "AnimationManager",
    "ShimmerEffect",
    "MicroInteractions",
    "LoadingSkeleton",
    "WeatherBackgroundManager",
    "ParticleSystem",
    "TemperatureGradient",
    "StatusMessageManager",
    "ErrorManager",
    "ErrorCard",
    "NotificationToast",
    "ErrorLevel",
    "TooltipManager",
    "StatusType",
    "VisualPolishManager",
    "GlassMorphism",
    "ShadowSystem",
    "KeyboardShortcuts",
    "SpacingGrid",
    "HeaderComponent",
    "StatusBarComponent",
    "SearchBar",
]
