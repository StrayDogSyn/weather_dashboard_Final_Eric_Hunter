"""UI Package - Modern Weather Dashboard Interface

Contains all user interface components and styling for the weather dashboard.
"""

# Component imports
from .components.glassmorphic import GlassmorphicFrame, GlassButton, GlassPanel
from .components.weather import WeatherCard, TemperatureChart, ForecastDisplay
from .components.common import LoadingSpinner, ShimmerLoader, ProgressSpinner, ErrorDisplay, InlineErrorDisplay

# Layout imports
from .layouts import MainLayout, TabManager

# Theme imports
from .themes import GlassmorphicTheme, ThemeManager

# Legacy imports for backward compatibility
from .professional_weather_dashboard import ProfessionalWeatherDashboard
from .theme_manager import ThemeManager as LegacyThemeManager
from .safe_widgets import SafeWidget

__version__ = "3.5"
__author__ = "E. Hunter Petross - Justice Through Code Tech Pathways"

__all__ = [
    # Glassmorphic components
    "GlassmorphicFrame",
    "GlassButton", 
    "GlassPanel",
    
    # Weather components
    "WeatherCard",
    "TemperatureChart",
    "ForecastDisplay",
    
    # Common components
    "LoadingSpinner",
    "ShimmerLoader",
    "ProgressSpinner",
    "ErrorDisplay",
    "InlineErrorDisplay",
    
    # Layouts
    "MainLayout",
    "TabManager",
    
    # Themes
    "GlassmorphicTheme",
    "ThemeManager",
    
    # Legacy components
    "ProfessionalWeatherDashboard",
    "LegacyThemeManager",
    "SafeWidget"
]
