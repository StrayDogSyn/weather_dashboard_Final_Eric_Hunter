#!/usr/bin/env python3
"""
Temperature Graph Feature Package

Advanced temperature visualization and analytics components.
Refactored into modular components for better maintainability.

Author: Eric Hunter (Cortana Builder Agent)
Version: 3.0.0 (TRAE 2.0 Phase 3)
"""

# Main chart widget (new modular implementation)
from .chart_widget import AdvancedChartWidget

# Component modules
from .chart_models import WeatherEvent, CityComparison, GlassmorphicTooltip
from .chart_ui_components import ChartUIComponents
from .chart_interactions import ChartInteractionHandler
from .chart_analytics import ChartAnalyticsEngine, ChartAnalytics, ExportSettings

# Backward compatibility - import from original file if it exists
try:
    from .advanced_chart_widget import AdvancedChartWidget as LegacyAdvancedChartWidget
    # Provide alias for backward compatibility
    AdvancedChartWidgetLegacy = LegacyAdvancedChartWidget
except ImportError:
    # Original file has been replaced, use new implementation
    AdvancedChartWidgetLegacy = AdvancedChartWidget

__all__ = [
    # Main widget
    'AdvancedChartWidget',
    
    # Component classes
    'ChartUIComponents',
    'ChartInteractionHandler', 
    'ChartAnalyticsEngine',
    
    # Data models
    'WeatherEvent',
    'CityComparison',
    'GlassmorphicTooltip',
    'ChartAnalytics',
    'ExportSettings',
    
    # Backward compatibility
    'AdvancedChartWidgetLegacy'
]