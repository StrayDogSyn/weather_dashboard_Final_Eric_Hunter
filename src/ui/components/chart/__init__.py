"""Chart Package for Temperature Chart Component.

This package provides a modular temperature chart implementation using mixins
for better separation of concerns and maintainability.
"""

from .chart_config import ChartConfigMixin
from .chart_widgets import ChartWidgetsMixin
from .chart_events import ChartEventsMixin
from .chart_animation import ChartAnimationMixin
from .chart_data import ChartDataMixin
from .chart_export import ChartExportMixin

__all__ = [
    'ChartConfigMixin',
    'ChartWidgetsMixin', 
    'ChartEventsMixin',
    'ChartAnimationMixin',
    'ChartDataMixin',
    'ChartExportMixin'
]

__version__ = '1.0.0'
__author__ = 'Weather Dashboard Team'
__description__ = 'Modular temperature chart component with mixin architecture'