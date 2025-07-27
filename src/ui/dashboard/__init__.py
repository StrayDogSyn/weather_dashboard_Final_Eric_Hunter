"""Dashboard UI Package.

This package provides the main dashboard interface with modular components
and professional layout management.
"""

from .models import (
    DashboardSection,
    DashboardConfig,
    DashboardState,
    NavigationItem,
)
from .dashboard_controller import DashboardController

__all__ = [
    'DashboardSection',
    'DashboardConfig',
    'DashboardState',
    'NavigationItem',
    'DashboardController',
]