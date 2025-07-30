"""Chart Configuration Mixin for Temperature Chart Component.

This module provides the ChartConfigMixin class that handles matplotlib setup,
styling configuration, and chart appearance settings.
"""

import matplotlib.pyplot as plt
import matplotlib.patheffects
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import numpy as np


class ChartConfigMixin:
    """Mixin for chart configuration and matplotlib setup."""
    
    def setup_matplotlib(self):
        """Configure matplotlib settings with enhanced glassmorphic styling."""
        # Set matplotlib style
        plt.style.use('dark_background')
        
        # Create figure with enhanced glassmorphic styling
        self.fig, self.ax = plt.subplots(figsize=(12, 6), facecolor='#0a0a0a')
        self.ax.set_facecolor('#0a0a0a')
        
        # Configure enhanced chart appearance
        self._configure_chart_appearance()
        self.apply_glassmorphic_styling()
        
        # Create canvas with improved styling
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Store canvas widget reference
        self.canvas_widget = canvas_widget
        
        # Apply glassmorphic effects to canvas
        self._apply_canvas_effects()
        
    def _configure_chart_appearance(self):
        """Configure enhanced visual appearance with glassmorphic elements."""
        # Configure enhanced spines with glassmorphic effect
        for spine in self.ax.spines.values():
            spine.set_color('#00ff88')
            spine.set_alpha(0.4)
            spine.set_linewidth(1.5)
            spine.set_visible(True)
            
        # Configure enhanced grid with glassmorphic styling
        self.ax.grid(True, alpha=0.15, color='#00ff88', linestyle='--', linewidth=0.8)
        self.ax.set_axisbelow(True)
        
        # Enhanced labels with professional typography
        self.ax.set_xlabel('Time', color='#00ff88', fontsize=13, fontweight='bold', 
                          fontfamily='Segoe UI')
        self.ax.set_ylabel('Temperature (°C)', color='#00ff88', fontsize=13, 
                          fontweight='bold', fontfamily='Segoe UI')
        
        # Enhanced tick parameters
        self.ax.tick_params(colors='#00ff88', labelsize=11, width=1.2, length=6)
        
        # Set enhanced background with gradient effect
        self.ax.patch.set_facecolor('#0a0a0a')
        
        # Add subtle glow effect to axes
        self._add_axis_glow()
        
    def apply_glassmorphic_styling(self):
        """Apply enhanced glassmorphic styling to chart elements."""
        # Create multi-layered glassmorphic background
        # Base layer
        base_bg = Rectangle(
            (0, 0), 1, 1,
            transform=self.ax.transAxes,
            facecolor='#0a0a0a',
            alpha=0.9,
            zorder=0
        )
        self.ax.add_patch(base_bg)
        
        # Glassmorphic overlay with gradient effect
        overlay_bg = Rectangle(
            (0, 0), 1, 1,
            transform=self.ax.transAxes,
            facecolor='#1a1a1a',
            alpha=0.3,
            zorder=1
        )
        self.ax.add_patch(overlay_bg)
        
        # Enhanced spines with glassmorphic glow
        for spine in self.ax.spines.values():
            spine.set_color('#00ff88')
            spine.set_alpha(0.6)
            spine.set_linewidth(2)
            spine.set_visible(True)
            spine.set_capstyle('round')
            
        # Add subtle border glow effect
        self._add_border_glow()
            
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
        """Create enhanced gradient background with glassmorphic effects."""
        if not x_data or not y_data:
            return
            
        # Create multi-layer gradient effect
        y_min = self.ax.get_ylim()[0]
        
        # Primary gradient fill
        self.ax.fill_between(
            x_data, y_data, y_min,
            alpha=0.25,
            color='#00ff88',
            interpolate=True,
            zorder=2
        )
        
        # Secondary gradient for depth
        self.ax.fill_between(
            x_data, y_data, y_min,
            alpha=0.1,
            color='#ffffff',
            interpolate=True,
            zorder=1
        )
        
        # Add subtle glow effect along the curve
        self._add_curve_glow(x_data, y_data)
        
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
    
    def _apply_canvas_effects(self):
        """Apply glassmorphic effects to the canvas widget."""
        try:
            # Configure canvas background
            self.canvas_widget.configure(bg='#0a0a0a', highlightthickness=0)
            
            # Add subtle border effect
            self.canvas_widget.configure(relief='flat', bd=0)
            
        except Exception as e:
            print(f"Warning: Could not apply canvas effects: {e}")
    
    def _add_axis_glow(self):
        """Add subtle glow effect to chart axes."""
        try:
            # Add glow effect by drawing multiple lines with decreasing alpha
            for spine_name, spine in self.ax.spines.items():
                if spine.get_visible():
                    # Create glow layers
                    for i in range(3):
                        glow_alpha = 0.1 - (i * 0.03)
                        glow_width = spine.get_linewidth() + (i * 0.5)
                        
                        # Apply glow effect
                        spine.set_path_effects([
                            plt.matplotlib.patheffects.withStroke(
                                linewidth=glow_width, 
                                foreground='#00ff88', 
                                alpha=glow_alpha
                            )
                        ])
        except Exception as e:
            print(f"Warning: Could not add axis glow: {e}")
    
    def _add_border_glow(self):
        """Add subtle glow effect to chart borders."""
        try:
            # Create a subtle glow around the chart area
            glow_rect = Rectangle(
                (0, 0), 1, 1,
                transform=self.ax.transAxes,
                facecolor='none',
                edgecolor='#00ff88',
                linewidth=3,
                alpha=0.2,
                zorder=10
            )
            self.ax.add_patch(glow_rect)
            
        except Exception as e:
            print(f"Warning: Could not add border glow: {e}")
    
    def _add_curve_glow(self, x_data, y_data):
        """Add glow effect along the temperature curve."""
        try:
            if not x_data or not y_data:
                return
                
            # Create multiple glow layers for depth
            for i in range(3):
                glow_alpha = 0.15 - (i * 0.05)
                glow_width = 3 + (i * 2)
                
                # Plot glow line
                self.ax.plot(
                    x_data, y_data,
                    color='#00ff88',
                    linewidth=glow_width,
                    alpha=glow_alpha,
                    zorder=1
                )
                
        except Exception as e:
            print(f"Warning: Could not add curve glow: {e}")
            
    def refresh_chart_display(self):
        """Refresh the chart display."""
        self.fig.tight_layout()
        self.canvas.draw()