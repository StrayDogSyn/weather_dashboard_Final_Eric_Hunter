"""UI Components Package

This package contains reusable UI components for the weather dashboard.
Components are organized into logical groups and accessible through a centralized factory.
"""

# Core component systems
from .component_factory import ComponentFactory, get_factory
from .component_factory import (
    create_frame, create_button, create_label, create_entry
)

# Animation and loading components
from .animation_manager import AnimationManager, LoadingSkeleton, MicroInteractions
from .common.loading_spinner import LoadingSpinner, ShimmerLoader

# Glassmorphic components (consolidated)
from .glassmorphic import GlassmorphicFrame, GlassButton, GlassPanel

# Common UI components (consolidated)
from .common import (
    HeaderComponent, SearchBar, StatusBarComponent,
    ErrorDisplay, InlineErrorDisplay
)

# Weather-specific components (consolidated)
from .weather import (
    WeatherCard,
    TemperatureChart,
    ForecastDisplay,
    CurrentWeatherCard,
    ForecastSection,
    MetricsDisplay
)

# Error and status management
from .error_manager import ErrorCard, ErrorLevel, ErrorManager, NotificationToast
from .status_manager import StatusMessageManager, StatusType, TooltipManager

# Legacy components (maintained for backward compatibility)
from .visual_polish import (
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

# Layout components (removed - module not found)

__all__ = [
    # Core component factory
    "ComponentFactory",
    "get_factory",
    "create_frame",
    "create_button",
    "create_label",
    "create_entry",
    
    # Consolidated glassmorphic components
    "GlassmorphicFrame",
    "GlassButton",
    "GlassPanel",
    
    # Consolidated common components
    "HeaderComponent",
    "SearchBar",
    "StatusBarComponent",
    "ErrorDisplay",
    "InlineErrorDisplay",
    "LoadingSpinner",
    "ShimmerLoader",
    
    # Consolidated weather components
    "WeatherCard",
    "ForecastPanel",
    "WeatherEffectsPanel",
    
    # Layout components (removed - module not found)
    
    # Animation and loading
    "AnimationManager",
    "MicroInteractions",
    "LoadingSkeleton",
    
    # Error and status management
    "StatusMessageManager",
    "ErrorManager",
    "ErrorCard",
    "NotificationToast",
    "ErrorLevel",
    "TooltipManager",
    "StatusType",
    
    # Legacy components (backward compatibility)
    "VisualPolishManager",
    "ShadowSystem",
    "KeyboardShortcuts",
    "SpacingGrid",
    "WeatherBackgroundManager",
    "ParticleSystem",
    "TemperatureGradient",
]
