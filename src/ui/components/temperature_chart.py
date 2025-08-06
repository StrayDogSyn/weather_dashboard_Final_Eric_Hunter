"""Enhanced Temperature Chart Component with Glassmorphic Styling."""

import tkinter as tk
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np

try:
    from src.ui.components.glassmorphic.glass_panel import GlassmorphicFrame
except ImportError:
    # Fallback if glassmorphic components not available
    import customtkinter as ctk
    GlassmorphicFrame = ctk.CTkFrame


class TemperatureChart(GlassmorphicFrame):
    """Enhanced temperature chart with glassmorphic styling and gradient fill."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Chart configuration
        self.figure = None
        self.canvas = None
        self.ax = None
        self.current_data = []
        self.timeframe = "24h"
        
        # Styling configuration
        self.colors = {
            'background': '#0d0d0d',
            'panel_bg': '#1a1a1a',
            'primary': '#00D4FF',
            'secondary': '#FF6B6B',
            'accent': '#4ECDC4',
            'text': '#FFFFFF',
            'grid': '#666666',
            'border': '#444444'
        }
        
        self.setup_chart()
        self.setup_controls()
        
    def setup_chart(self):
        """Initialize the matplotlib chart with glassmorphic styling."""
        # Create figure with dark background
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.figure.patch.set_facecolor(self.colors['background'])
        
        # Create main subplot
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(self.colors['panel_bg'])
        
        # Style the axes
        self.style_axes()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add initial placeholder
        self.show_placeholder()
        
    def setup_controls(self):
        """Setup chart control buttons."""
        try:
            from src.ui.components.glassmorphic.glass_button import GlassButton
            button_class = GlassButton
        except ImportError:
            import customtkinter as ctk
            button_class = ctk.CTkButton
            
        # Controls frame
        try:
            # Try to get background color from parent
            bg_color = self._fg_color if hasattr(self, '_fg_color') else '#2b2b2b'
        except:
            bg_color = '#2b2b2b'
        
        controls_frame = tk.Frame(self, bg=bg_color)
        controls_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Timeframe buttons
        timeframes = [("1H", "1h"), ("6H", "6h"), ("24H", "24h"), ("7D", "7d")]
        
        for i, (label, value) in enumerate(timeframes):
            btn = button_class(
                controls_frame,
                text=label,
                width=60,
                height=30,
                command=lambda v=value: self.set_timeframe(v)
            )
            btn.pack(side="left", padx=5)
            
        # Refresh button
        refresh_btn = button_class(
            controls_frame,
            text="🔄",
            width=40,
            height=30,
            command=self.refresh_chart
        )
        refresh_btn.pack(side="right", padx=5)
        
    def style_axes(self):
        """Apply glassmorphic styling to chart axes."""
        # Remove top and right spines
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        # Style remaining spines
        self.ax.spines['bottom'].set_color(self.colors['grid'])
        self.ax.spines['left'].set_color(self.colors['grid'])
        self.ax.spines['bottom'].set_linewidth(1)
        self.ax.spines['left'].set_linewidth(1)
        
        # Style ticks and labels
        self.ax.tick_params(
            colors=self.colors['text'],
            which='both',
            direction='out',
            length=4,
            width=1
        )
        
        # Grid styling
        self.ax.grid(
            True,
            alpha=0.2,
            color=self.colors['text'],
            linestyle='-',
            linewidth=0.5
        )
        
        # Labels styling
        self.ax.set_xlabel('Time', color=self.colors['text'], fontsize=10)
        self.ax.set_ylabel('Temperature (°C)', color=self.colors['text'], fontsize=10)
        
    def update_chart(self, weather_data: List[Dict], timeframe: str = "24h"):
        """Update chart with new weather data."""
        self.current_data = weather_data
        self.timeframe = timeframe
        
        if not weather_data:
            self.show_placeholder()
            return
            
        # Clear previous plot
        self.ax.clear()
        self.style_axes()
        
        # Process data
        times, temps, conditions = self.process_data(weather_data)
        
        if not times or not temps:
            self.show_placeholder()
            return
            
        # Create gradient fill
        self.plot_temperature_gradient(times, temps)
        
        # Plot main temperature line
        line = self.ax.plot(
            times, temps,
            color=self.colors['primary'],
            linewidth=3,
            marker='o',
            markersize=6,
            markerfacecolor=self.colors['primary'],
            markeredgecolor='white',
            markeredgewidth=1,
            alpha=0.9,
            label='Temperature'
        )[0]
        
        # Add glow effect
        self.add_glow_effect(times, temps)
        
        # Annotate extremes
        self.annotate_extremes(times, temps)
        
        # Add weather condition indicators
        self.add_condition_indicators(times, temps, conditions)
        
        # Format axes
        self.format_time_axis(times)
        self.format_temperature_axis(temps)
        
        # Add title
        self.ax.set_title(
            f'Temperature Trend ({timeframe.upper()})',
            color=self.colors['text'],
            fontsize=14,
            fontweight='bold',
            pad=20
        )
        
        # Add legend
        self.ax.legend(
            loc='upper right',
            frameon=False,
            labelcolor=self.colors['text']
        )
        
        # Refresh canvas
        self.canvas.draw()
        
    def process_data(self, weather_data: List[Dict]) -> Tuple[List, List, List]:
        """Process weather data for plotting."""
        times = []
        temps = []
        conditions = []
        
        for data in weather_data:
            try:
                # Parse time
                if 'time' in data:
                    if isinstance(data['time'], str):
                        time_obj = datetime.fromisoformat(data['time'].replace('Z', '+00:00'))
                    else:
                        time_obj = data['time']
                elif 'timestamp' in data:
                    if isinstance(data['timestamp'], str):
                        time_obj = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                    else:
                        time_obj = data['timestamp']
                else:
                    continue
                    
                # Parse temperature
                temp = data.get('temperature', data.get('temp'))
                if temp is not None:
                    times.append(time_obj)
                    temps.append(float(temp))
                    conditions.append(data.get('condition', data.get('weather', 'unknown')))
                    
            except (ValueError, TypeError) as e:
                print(f"Error processing weather data point: {e}")
                continue
                
        return times, temps, conditions
        
    def plot_temperature_gradient(self, times, temps):
        """Create gradient fill under the temperature line."""
        if len(times) < 2:
            return
            
        # Create gradient colors based on temperature
        min_temp = min(temps)
        max_temp = max(temps)
        temp_range = max_temp - min_temp if max_temp != min_temp else 1
        
        # Create color map
        colors = []
        for temp in temps:
            # Normalize temperature to 0-1 range
            normalized = (temp - min_temp) / temp_range
            
            # Create color based on temperature
            if normalized < 0.3:
                # Cold - blue tones
                color = (0.2, 0.6, 1.0, 0.4)
            elif normalized < 0.7:
                # Moderate - cyan tones
                color = (0.3, 0.8, 0.9, 0.4)
            else:
                # Warm - orange/red tones
                color = (1.0, 0.4, 0.2, 0.4)
                
            colors.append(color)
            
        # Fill area under curve with gradient
        self.ax.fill_between(
            times, temps,
            alpha=0.3,
            color=self.colors['primary'],
            interpolate=True
        )
        
        # Add additional gradient layers for depth
        for i in range(3):
            alpha = 0.1 - (i * 0.03)
            offset = (max(temps) - min(temps)) * 0.1 * (i + 1)
            
            self.ax.fill_between(
                times,
                [t - offset for t in temps],
                alpha=alpha,
                color=self.colors['primary']
            )
            
    def add_glow_effect(self, times, temps):
        """Add glow effect to the temperature line."""
        # Create multiple lines with decreasing alpha for glow effect
        glow_widths = [8, 6, 4, 2]
        glow_alphas = [0.1, 0.15, 0.2, 0.3]
        
        for width, alpha in zip(glow_widths, glow_alphas):
            self.ax.plot(
                times, temps,
                color=self.colors['primary'],
                linewidth=width,
                alpha=alpha,
                solid_capstyle='round'
            )
            
    def annotate_extremes(self, times, temps):
        """Annotate minimum and maximum temperature points."""
        if not temps:
            return
            
        min_idx = temps.index(min(temps))
        max_idx = temps.index(max(temps))
        
        # Annotate minimum
        self.ax.annotate(
            f'{temps[min_idx]:.1f}°C',
            xy=(times[min_idx], temps[min_idx]),
            xytext=(10, -20),
            textcoords='offset points',
            bbox=dict(
                boxstyle='round,pad=0.3',
                facecolor=self.colors['secondary'],
                alpha=0.8,
                edgecolor='none'
            ),
            arrowprops=dict(
                arrowstyle='->',
                connectionstyle='arc3,rad=0',
                color=self.colors['secondary'],
                alpha=0.8
            ),
            color='white',
            fontsize=9,
            fontweight='bold'
        )
        
        # Annotate maximum
        self.ax.annotate(
            f'{temps[max_idx]:.1f}°C',
            xy=(times[max_idx], temps[max_idx]),
            xytext=(10, 20),
            textcoords='offset points',
            bbox=dict(
                boxstyle='round,pad=0.3',
                facecolor=self.colors['accent'],
                alpha=0.8,
                edgecolor='none'
            ),
            arrowprops=dict(
                arrowstyle='->',
                connectionstyle='arc3,rad=0',
                color=self.colors['accent'],
                alpha=0.8
            ),
            color='white',
            fontsize=9,
            fontweight='bold'
        )
        
    def add_condition_indicators(self, times, temps, conditions):
        """Add weather condition indicators to the chart."""
        condition_icons = {
            'sunny': '☀️',
            'clear': '☀️',
            'cloudy': '☁️',
            'overcast': '☁️',
            'rainy': '🌧️',
            'rain': '🌧️',
            'snowy': '❄️',
            'snow': '❄️',
            'stormy': '⛈️',
            'thunderstorm': '⛈️',
            'foggy': '🌫️',
            'fog': '🌫️',
            'windy': '💨'
        }
        
        # Add condition indicators at key points
        step = max(1, len(times) // 6)  # Show max 6 indicators
        
        for i in range(0, len(times), step):
            if i < len(conditions):
                condition = conditions[i].lower()
                icon = None
                
                for key, emoji in condition_icons.items():
                    if key in condition:
                        icon = emoji
                        break
                        
                if icon:
                    self.ax.text(
                        times[i], temps[i] + (max(temps) - min(temps)) * 0.05,
                        icon,
                        fontsize=12,
                        ha='center',
                        va='bottom',
                        alpha=0.8
                    )
                    
    def format_time_axis(self, times):
        """Format the time axis based on timeframe."""
        if not times:
            return
            
        if self.timeframe in ['1h', '6h']:
            # Show hours and minutes
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        elif self.timeframe == '24h':
            # Show hours
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
        else:
            # Show days
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            
        # Rotate labels for better readability
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
    def format_temperature_axis(self, temps):
        """Format the temperature axis."""
        if not temps:
            return
            
        # Set reasonable y-axis limits with padding
        temp_range = max(temps) - min(temps)
        padding = max(2, temp_range * 0.1)
        
        self.ax.set_ylim(
            min(temps) - padding,
            max(temps) + padding
        )
        
        # Add temperature unit to y-axis
        self.ax.set_ylabel('Temperature (°C)', color=self.colors['text'], fontsize=10)
        
    def show_placeholder(self):
        """Show placeholder when no data is available."""
        self.ax.clear()
        self.style_axes()
        
        self.ax.text(
            0.5, 0.5,
            'No temperature data available\nSelect a location to view temperature trends',
            transform=self.ax.transAxes,
            ha='center',
            va='center',
            color=self.colors['text'],
            fontsize=12,
            alpha=0.7
        )
        
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.canvas.draw()
        
    def set_timeframe(self, timeframe: str):
        """Set the chart timeframe and refresh."""
        self.timeframe = timeframe
        if self.current_data:
            self.update_chart(self.current_data, timeframe)
            
    def refresh_chart(self):
        """Refresh the chart with current data."""
        if self.current_data:
            self.update_chart(self.current_data, self.timeframe)
            
    def export_chart(self, filename: str = None):
        """Export chart as image."""
        if not filename:
            from datetime import datetime
            filename = f"temperature_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
        try:
            self.figure.savefig(
                filename,
                dpi=300,
                bbox_inches='tight',
                facecolor=self.colors['background'],
                edgecolor='none'
            )
            print(f"Chart exported to {filename}")
            return True
        except Exception as e:
            print(f"Error exporting chart: {e}")
            return False
            
    def get_chart_stats(self) -> Dict:
        """Get statistics about the current chart data."""
        if not self.current_data:
            return {}
            
        times, temps, conditions = self.process_data(self.current_data)
        
        if not temps:
            return {}
            
        return {
            'data_points': len(temps),
            'min_temperature': min(temps),
            'max_temperature': max(temps),
            'avg_temperature': sum(temps) / len(temps),
            'temperature_range': max(temps) - min(temps),
            'timeframe': self.timeframe,
            'conditions': list(set(conditions)) if conditions else []
        }
    
    def update_theme(self, theme_data: Dict):
        """Update chart colors based on theme data."""
        try:
            # Update color scheme
            self.colors.update({
                'background': theme_data.get('chart_bg', '#0d0d0d'),
                'panel_bg': theme_data.get('card', '#1a1a1a'),
                'primary': theme_data.get('primary', '#00D4FF'),
                'secondary': theme_data.get('secondary', '#FF6B6B'),
                'accent': theme_data.get('accent', '#4ECDC4'),
                'text': theme_data.get('text', '#FFFFFF'),
                'grid': theme_data.get('secondary', '#666666'),
                'border': theme_data.get('border', '#444444')
            })
            
            # Update figure background
            if self.figure:
                self.figure.patch.set_facecolor(self.colors['background'])
            
            # Update axes styling
            if self.ax:
                self.ax.set_facecolor(self.colors['panel_bg'])
                self.style_axes()
            
            # Refresh chart with new colors
            if self.current_data:
                self.update_chart(self.current_data, self.timeframe)
            else:
                self.show_placeholder()
                
        except Exception as e:
            print(f"Error updating chart theme: {e}")