"""Temperature Chart Component for Weather Dashboard.

This module provides an interactive temperature chart with multiple timeframes,
smooth animations, and export capabilities using a modular mixin architecture."""

import customtkinter as ctk
import matplotlib
import matplotlib.pyplot as plt
from typing import List, Dict, Optional, Any

# Import chart mixins
from .chart import (
    ChartConfigMixin,
    ChartWidgetsMixin,
    ChartEventsMixin,
    ChartAnimationMixin,
    ChartDataMixin,
    ChartExportMixin
)
from ui.theme import DataTerminalTheme
from models.weather_models import ForecastData

# Configure matplotlib with safe fonts at module level
matplotlib.use('TkAgg')
plt.rcParams.update({
    'font.family': ['Segoe UI', 'Arial', 'DejaVu Sans', 'sans-serif'],
    'font.size': 10,
    'figure.facecolor': '#1a1a1a',
    'axes.facecolor': '#1a1a1a',
    'text.color': 'white',
    'axes.labelcolor': 'white',
    'xtick.color': 'white',
    'ytick.color': 'white',
    'axes.unicode_minus': False,  # Prevent unicode minus issues
    'svg.fonttype': 'none'  # Use system fonts
})


class TemperatureChart(ctk.CTkFrame, 
                       ChartConfigMixin,
                       ChartWidgetsMixin,
                       ChartEventsMixin,
                       ChartAnimationMixin,
                       ChartDataMixin,
                       ChartExportMixin):
    """Enhanced temperature chart with interactive features and glassmorphic styling."""
    
    def __init__(self, parent, **kwargs):
        """Initialize enhanced temperature chart."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("default"), **kwargs)
        
        # Initialize state
        self.current_timeframe = "24h"
        self.forecast_data = None
        
        # Initialize mixins - using actual available methods
        # Note: Mixins don't have _init_ methods, they're called during _create_ui()
        
        # Create UI and initialize chart
        self._create_ui()
        self._create_default_chart()
    
    def _create_ui(self):
        """Create the main UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create UI elements using mixins
        self.create_widgets()
        self.setup_layout()
        
        # Setup matplotlib and event handlers
        self.setup_matplotlib()
        self.setup_event_handlers()
     
     # Old methods removed - functionality moved to mixins
    
    # Widget creation moved to ChartWidgetsMixin
    
    # Timeframe button creation moved to ChartWidgetsMixin
    
    # Export button creation moved to ChartWidgetsMixin
    
    # Layout setup moved to ChartWidgetsMixin
    
    # Event handler setup moved to ChartEventsMixin
    
    def _create_default_chart(self) -> None:
        """Create initial chart with sample data."""
        # Generate sample data and create chart using mixins
        sample_data = self.generate_realistic_data(self.current_timeframe)
        self.update_data_storage(sample_data)
        self.refresh_chart_display()
    
    # Styling and trend methods moved to ChartConfigMixin
    
    # Public interface methods that delegate to mixins
    def update_forecast(self, forecast_data: List[ForecastData]):
        """Update chart with new forecast data."""
        self.forecast_data = forecast_data
        processed_data = self.process_forecast_data(forecast_data, self.current_timeframe)
        self.update_chart_data(*processed_data)
        self.animate_chart_update()
        
    def set_timeframe(self, timeframe: str):
        """Change the chart timeframe."""
        if timeframe != self.current_timeframe:
            self.current_timeframe = timeframe
            self.update_timeframe_buttons(timeframe)
            
            if self.forecast_data:
                self.update_forecast(self.forecast_data)
            else:
                sample_data = self.generate_realistic_data(timeframe)
                self.update_data_storage(sample_data)
                self.refresh_chart_display()
    
    def change_timeframe(self, timeframe: str):
        """Alias for set_timeframe to match mixin expectations."""
        self.set_timeframe(timeframe)
                
    def export_chart_png(self):
        """Export chart as PNG."""
        self.export_chart('png')
        
    def export_chart_pdf(self):
        """Export chart as PDF."""
        self.export_chart('pdf')
        
    def clear_chart(self):
        """Clear the chart display."""
        self.clear_chart_data()
        self.refresh_chart()
    
    # Event handlers moved to ChartEventsMixin
    def _on_timeframe_change(self, timeframe: str) -> None:
        """Handle timeframe change."""
        self.set_timeframe(timeframe)
    
    # Mouse event handlers moved to ChartEventsMixin
    
    # Size management moved to ChartConfigMixin
    def update_size(self, width, height):
        """Update chart size for responsive design."""
        # Calculate scale factor based on size
        scale = min(width / 800, height / 400)  # Base size 800x400
        self._update_chart_scale(scale, 1.0)
    
    # Export functionality moved to ChartExportMixin
    def export_chart(self, format_type: str = "png") -> None:
        """Export chart to PNG or PDF format."""
        # Call the parent ChartExportMixin method
        super().export_chart(format_type)