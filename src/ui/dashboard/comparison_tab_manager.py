"""Comparison Tab Manager for Weather Dashboard.

Handles team collaboration and city comparison functionality.
"""

from src.ui.components.city_comparison_panel import CityComparisonPanel
from src.ui.components.ml_comparison_panel import MLComparisonPanel


class ComparisonTabManager:
    """Manages comparison tab functionality and UI components."""

    def __init__(self, parent_tab, weather_service, github_service):
        """Initialize comparison tab manager.

        Args:
            parent_tab: Parent tab widget
            weather_service: Weather service instance
            github_service: GitHub service instance
        """
        self.parent_tab = parent_tab
        self.weather_service = weather_service
        self.github_service = github_service

        # UI components
        self.city_comparison_panel = None

    def create_comparison_tab(self):
        """Create team collaboration and city comparison tab."""
        self._create_comparison_tab_content()

    def _create_comparison_tab_content(self):
        """Create the team collaboration and city comparison functionality."""
        # Create the city comparison panel
        self.city_comparison_panel = CityComparisonPanel(
            self.parent_tab,
            weather_service=self.weather_service,
            github_service=self.github_service,
        )
        self.city_comparison_panel.pack(fill="both", expand=True)


class MLComparisonTabManager:
    """Manages ML-powered comparison and analysis tab."""

    def __init__(self, parent_tab, weather_service, github_service):
        """Initialize ML comparison tab manager.

        Args:
            parent_tab: Parent tab widget
            weather_service: Weather service instance
            github_service: GitHub service instance
        """
        self.parent_tab = parent_tab
        self.weather_service = weather_service
        self.github_service = github_service

        # UI components
        self.ml_comparison_panel = None

    def create_ml_comparison_tab(self):
        """Create ML-powered comparison and analysis tab."""
        self._create_ml_comparison_tab_content()

    def _create_ml_comparison_tab_content(self):
        """Create the ML-powered comparison and analysis functionality."""
        # Create the ML comparison panel
        self.ml_comparison_panel = MLComparisonPanel(
            self.parent_tab,
            weather_service=self.weather_service,
            github_service=self.github_service,
        )
        self.ml_comparison_panel.pack(fill="both", expand=True)
