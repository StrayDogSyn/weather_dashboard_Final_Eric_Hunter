"""Chart Configuration Mixin for Temperature Chart Component.

This module provides the ChartConfigMixin class that handles matplotlib setup,
styling configuration, and chart appearance settings.
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import numpy as np


class ChartConfigMixin:
    """Mixin for chart configuration and matplotlib setup."""
    
    def setup_matplotlib(self):
        """Configure matplotlib settings and create figure."""
        # Set matplotlib style
        plt.style.use('dark_background')
        
        # Create figure with custom styling
        self.fig, self.ax = plt.subplots(figsize=(12, 6), facecolor='#1a1a1a')
        self.ax.set_facecolor('#1a1a1a')
        
        # Configure chart appearance
        self._configure_chart_appearance()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Store canvas widget reference
        self.canvas_widget = self.canvas.get_tk_widget()
        
    def _configure_chart_appearance(self):
        """Configure the visual appearance of the chart."""
        # Remove default spines and ticks
        for spine in self.ax.spines.values():
            spine.set_visible(False)
            
        # Configure grid
        self.ax.grid(True, alpha=0.2, color='#00ff88', linestyle='-', linewidth=0.5)
        
        # Set labels and title styling
        self.ax.set_xlabel('Time', color='#00ff88', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Temperature (°C)', color='#00ff88', fontsize=12, fontweight='bold')
        
        # Configure tick parameters
        self.ax.tick_params(colors='#00ff88', labelsize=10)
        
        # Set background
        self.ax.patch.set_facecolor('#1a1a1a')
        
    def apply_glassmorphic_styling(self):
        """Apply glassmorphic styling to chart elements."""
        # Create glassmorphic background
        background = Rectangle(
            (0, 0), 1, 1,
            transform=self.ax.transAxes,
            facecolor='#1a1a1a',
            alpha=0.8,
            zorder=0
        )
        self.ax.add_patch(background)
        
        # Style spines with glassmorphic effect
        for spine in self.ax.spines.values():
            spine.set_color('#00ff88')
            spine.set_alpha(0.3)
            spine.set_linewidth(1)
            spine.set_visible(True)
            
    def configure_date_formatting(self, timeframe='24h'):
        """Configure date formatting based on timeframe."""
        if timeframe == '24h':
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
        elif timeframe == '7d':
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        elif timeframe == '30d':
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            
        # Rotate labels for better readability
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
    def set_chart_limits(self, x_data, y_data):
        """Set appropriate chart limits based on data."""
        if not x_data or not y_data:
            return
            
        # Set x-axis limits with padding
        x_min, x_max = min(x_data), max(x_data)
        x_padding = (x_max - x_min) * 0.02
        self.ax.set_xlim(x_min - x_padding, x_max + x_padding)
        
        # Set y-axis limits with padding
        y_min, y_max = min(y_data), max(y_data)
        y_range = y_max - y_min
        y_padding = max(y_range * 0.1, 2)  # Minimum 2-degree padding
        self.ax.set_ylim(y_min - y_padding, y_max + y_padding)
        
    def create_gradient_background(self, x_data, y_data):
        """Create gradient background for the chart."""
        if not x_data or not y_data:
            return
            
        # Create gradient effect
        y_min = self.ax.get_ylim()[0]
        
        # Fill area under the curve with gradient
        self.ax.fill_between(
            x_data, y_data, y_min,
            alpha=0.2,
            color='#00ff88',
            interpolate=True
        )
        
    def add_temperature_zones(self):
        """Add temperature zone indicators."""
        y_min, y_max = self.ax.get_ylim()
        
        # Cold zone (below 10°C)
        if y_min < 10:
            self.ax.axhspan(y_min, min(10, y_max), alpha=0.1, color='blue', zorder=0)
            
        # Comfortable zone (10-25°C)
        comfort_min = max(10, y_min)
        comfort_max = min(25, y_max)
        if comfort_min < comfort_max:
            self.ax.axhspan(comfort_min, comfort_max, alpha=0.1, color='green', zorder=0)
            
        # Hot zone (above 25°C)
        if y_max > 25:
            self.ax.axhspan(max(25, y_min), y_max, alpha=0.1, color='red', zorder=0)
            
    def configure_legend(self):
        """Configure chart legend with custom styling."""
        legend = self.ax.legend(
            loc='upper right',
            frameon=True,
            fancybox=True,
            shadow=True,
            framealpha=0.8,
            facecolor='#2a2a2a',
            edgecolor='#00ff88'
        )
        
        # Style legend text
        for text in legend.get_texts():
            text.set_color('#00ff88')
            text.set_fontsize(10)
            
    def refresh_chart_display(self):
        """Refresh the chart display."""
        self.fig.tight_layout()
        self.canvas.draw()