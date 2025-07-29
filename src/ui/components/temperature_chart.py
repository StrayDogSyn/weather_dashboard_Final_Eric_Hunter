"""Enhanced Temperature Chart Component

Professional interactive temperature chart with glassmorphic styling,
animations, and advanced visualization features.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import io
from PIL import Image, ImageFilter
import threading
import time

from ui.theme import DataTerminalTheme
from models.weather_models import ForecastData


class TemperatureChart(ctk.CTkFrame):
    """Enhanced temperature chart with interactive features and glassmorphic styling."""
    
    def __init__(self, parent, **kwargs):
        """Initialize enhanced temperature chart."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("default"), **kwargs)
        
        # Data storage
        self.forecast_data: Optional[List[ForecastData]] = None
        self.current_timeframe = "24h"
        self.animation_running = False
        self.hover_annotation = None
        self.trend_indicators = []
        
        # Animation properties
        self.animation_duration = 0.8  # seconds
        self.animation_fps = 60
        self.animation_frames = int(self.animation_duration * self.animation_fps)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._setup_matplotlib()
        self._create_widgets()
        self._setup_layout()
        self._setup_event_handlers()
        self._create_default_chart()
    
    def _setup_matplotlib(self) -> None:
        """Configure matplotlib with enhanced glassmorphic theme."""
        plt.style.use('dark_background')
        
        # Enhanced theme with glassmorphic effects
        theme_style = DataTerminalTheme.get_matplotlib_style()
        theme_style.update({
            'figure.facecolor': 'none',  # Transparent for glassmorphic effect
            'axes.facecolor': '#1E1E1E80',  # Semi-transparent background
            'axes.edgecolor': DataTerminalTheme.PRIMARY,
            'axes.linewidth': 2,
            'grid.linewidth': 0.8,
            'grid.alpha': 0.4,
            'lines.linewidth': 3,
            'lines.markersize': 8,
            'font.weight': 'bold'
        })
        plt.rcParams.update(theme_style)
    
    def _create_widgets(self) -> None:
        """Create all widgets with glassmorphic styling."""
        # Header with glassmorphic frame
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=("#1E1E1E", "#1E1E1E"),
            border_color=DataTerminalTheme.PRIMARY,
            border_width=1,
            corner_radius=DataTerminalTheme.RADIUS_LARGE
        )
        
        # Title with enhanced typography
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🌡️ INTERACTIVE TEMPERATURE ANALYSIS",
            font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        
        # Timeframe toggle buttons with glassmorphic styling
        self.timeframe_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent",
            corner_radius=0
        )
        
        self._create_timeframe_buttons()
        
        # Export controls frame
        self.export_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent",
            corner_radius=0
        )
        
        self._create_export_buttons()
        
        # Chart frame with glassmorphic background
        self.chart_frame = ctk.CTkFrame(
            self,
            fg_color=("#1E1E1E", "#1E1E1E"),
            border_color=DataTerminalTheme.BORDER,
            border_width=1,
            corner_radius=DataTerminalTheme.RADIUS_LARGE
        )
        
        # Create matplotlib figure with glassmorphic styling
        self.figure = Figure(
            figsize=(10, 6),
            facecolor='none',  # Transparent background
            edgecolor=DataTerminalTheme.PRIMARY,
            linewidth=2
        )
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1E1E1E80')  # Semi-transparent background
        
        # Create canvas with enhanced styling
        self.canvas = FigureCanvasTkAgg(self.figure, self.chart_frame)
        self.canvas.get_tk_widget().configure(
            bg=DataTerminalTheme.BACKGROUND,
            highlightthickness=0,
            relief='flat'
        )
        
        # Tooltip frame for hover effects
        self.tooltip_frame = ctk.CTkFrame(
            self.chart_frame,
            fg_color=("#000000", "#000000"),
            border_color=DataTerminalTheme.PRIMARY,
            border_width=2,
            corner_radius=DataTerminalTheme.RADIUS_MEDIUM
        )
        self.tooltip_frame.place_forget()  # Hidden by default
        
        self.tooltip_label = ctk.CTkLabel(
            self.tooltip_frame,
            text="",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.TEXT
        )
        self.tooltip_label.pack(padx=10, pady=5)
    
    def _create_timeframe_buttons(self) -> None:
        """Create glassmorphic timeframe toggle buttons."""
        self.timeframe_buttons = {}
        timeframes = ["24h", "7d", "30d"]
        
        for i, timeframe in enumerate(timeframes):
            is_active = timeframe == self.current_timeframe
            
            button = ctk.CTkButton(
                self.timeframe_frame,
                text=timeframe,
                width=70,
                height=35,
                corner_radius=DataTerminalTheme.RADIUS_LARGE,
                font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
                fg_color=DataTerminalTheme.PRIMARY if is_active else "transparent",
                text_color=DataTerminalTheme.BACKGROUND if is_active else DataTerminalTheme.PRIMARY,
                border_color=DataTerminalTheme.PRIMARY,
                border_width=2,
                hover_color=DataTerminalTheme.SUCCESS if is_active else DataTerminalTheme.HOVER,
                command=lambda tf=timeframe: self._on_timeframe_change(tf)
            )
            
            button.grid(row=0, column=i, padx=5, pady=5)
            self.timeframe_buttons[timeframe] = button
    
    def _create_export_buttons(self) -> None:
        """Create export functionality buttons."""
        # PNG Export button
        self.export_png_btn = ctk.CTkButton(
            self.export_frame,
            text="📊 PNG",
            width=80,
            height=30,
            corner_radius=DataTerminalTheme.RADIUS_MEDIUM,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            fg_color=DataTerminalTheme.INFO,
            hover_color="#0088CC",
            command=lambda: self.export_chart("png")
        )
        
        # PDF Export button
        self.export_pdf_btn = ctk.CTkButton(
            self.export_frame,
            text="📄 PDF",
            width=80,
            height=30,
            corner_radius=DataTerminalTheme.RADIUS_MEDIUM,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            fg_color=DataTerminalTheme.WARNING,
            hover_color="#CC9900",
            command=lambda: self.export_chart("pdf")
        )
        
        self.export_png_btn.grid(row=0, column=0, padx=5, pady=5)
        self.export_pdf_btn.grid(row=0, column=1, padx=5, pady=5)
    
    def _setup_layout(self) -> None:
        """Arrange widgets with enhanced spacing."""
        # Header layout
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        self.title_label.grid(row=0, column=0, columnspan=3, pady=(15, 10), sticky="w")
        self.timeframe_frame.grid(row=1, column=0, pady=(0, 15), sticky="w")
        self.export_frame.grid(row=1, column=2, pady=(0, 15), sticky="e")
        
        # Chart layout
        self.chart_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(0, weight=1)
        
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    
    def _setup_event_handlers(self) -> None:
        """Setup interactive event handlers."""
        # Mouse motion for hover tooltips
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)
        self.canvas.mpl_connect('button_press_event', self._on_mouse_click)
        self.canvas.mpl_connect('axes_leave_event', self._on_mouse_leave)
        
        # Resize handling for responsive design
        self.bind('<Configure>', self._on_resize)
    
    def _create_default_chart(self) -> None:
        """Create default chart with glassmorphic styling."""
        self.ax.clear()
        
        # Generate sample data with realistic temperature patterns
        hours = np.arange(24)
        base_temp = 20
        daily_variation = 8 * np.sin((hours - 6) * np.pi / 12)
        noise = np.random.normal(0, 1, 24)
        temperatures = base_temp + daily_variation + noise
        
        # Create gradient effect
        self._plot_temperature_with_gradient(hours, temperatures)
        
        # Enhanced styling
        self.ax.set_title(
            "Interactive Temperature Forecast",
            color=DataTerminalTheme.PRIMARY,
            fontsize=16,
            fontweight='bold',
            pad=25
        )
        
        self.ax.set_xlabel(
            "Time (Hours)",
            color=DataTerminalTheme.TEXT,
            fontsize=13,
            fontweight='bold'
        )
        
        self.ax.set_ylabel(
            "Temperature (°C)",
            color=DataTerminalTheme.TEXT,
            fontsize=13,
            fontweight='bold'
        )
        
        self._apply_glassmorphic_styling()
        
        # Add placeholder text
        self.ax.text(
            0.5, 0.95,
            "🌡️ Hover over data points for detailed information",
            transform=self.ax.transAxes,
            ha='center',
            va='top',
            color=DataTerminalTheme.TEXT_SECONDARY,
            fontsize=11,
            style='italic',
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor='#1E1E1E80',
                edgecolor=DataTerminalTheme.PRIMARY,
                alpha=0.8
            )
        )
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _plot_temperature_with_gradient(self, x_data: np.ndarray, y_data: np.ndarray) -> None:
        """Plot temperature data with gradient effects."""
        # Main temperature line with enhanced styling
        line = self.ax.plot(
            x_data, y_data,
            color=DataTerminalTheme.PRIMARY,
            linewidth=4,
            marker='o',
            markersize=8,
            markerfacecolor=DataTerminalTheme.PRIMARY,
            markeredgecolor=DataTerminalTheme.BACKGROUND,
            markeredgewidth=2,
            alpha=0.9,
            zorder=3
        )[0]
        
        # Gradient fill effect
        self.ax.fill_between(
            x_data, y_data,
            alpha=0.3,
            color=DataTerminalTheme.PRIMARY,
            zorder=1
        )
        
        # Add trend indicators
        self._add_trend_indicators(x_data, y_data)
        
        return line
    
    def _add_trend_indicators(self, x_data: np.ndarray, y_data: np.ndarray) -> None:
        """Add trend analysis indicators to the chart."""
        self.trend_indicators.clear()
        
        for i in range(1, len(y_data)):
            trend = y_data[i] - y_data[i-1]
            
            if abs(trend) > 0.5:  # Significant change threshold
                color = DataTerminalTheme.SUCCESS if trend > 0 else DataTerminalTheme.ERROR
                symbol = '▲' if trend > 0 else '▼'
                
                indicator = self.ax.annotate(
                    symbol,
                    (x_data[i], y_data[i]),
                    xytext=(0, 20 if trend > 0 else -30),
                    textcoords='offset points',
                    ha='center',
                    va='center',
                    color=color,
                    fontsize=12,
                    fontweight='bold',
                    alpha=0.8,
                    zorder=4
                )
                
                self.trend_indicators.append(indicator)
    
    def _apply_glassmorphic_styling(self) -> None:
        """Apply glassmorphic styling to the chart."""
        # Enhanced grid with glassmorphic effect
        self.ax.grid(
            True,
            color=DataTerminalTheme.CHART_GRID,
            alpha=0.4,
            linestyle='-',
            linewidth=1.2
        )
        
        # Glassmorphic spines
        for spine in self.ax.spines.values():
            spine.set_color(DataTerminalTheme.PRIMARY)
            spine.set_linewidth(2)
            spine.set_alpha(0.8)
        
        # Enhanced tick styling
        self.ax.tick_params(
            colors=DataTerminalTheme.TEXT,
            which='both',
            labelsize=11,
            width=2,
            length=6
        )
        
        # Enhanced spine styling with subtle glow effect
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        
        # Add subtle accent to bottom and left spines
        self.ax.spines['left'].set_visible(True)
        self.ax.spines['bottom'].set_visible(True)
        self.ax.spines['left'].set_color(DataTerminalTheme.PRIMARY)
        self.ax.spines['bottom'].set_color(DataTerminalTheme.PRIMARY)
        self.ax.spines['left'].set_linewidth(1.5)
        self.ax.spines['bottom'].set_linewidth(1.5)
        self.ax.spines['left'].set_alpha(0.6)
        self.ax.spines['bottom'].set_alpha(0.6)
    
    def _on_timeframe_change(self, timeframe: str) -> None:
        """Handle timeframe button clicks with smooth transitions."""
        if timeframe == self.current_timeframe or self.animation_running:
            return
        
        # Update button states
        for tf, button in self.timeframe_buttons.items():
            is_active = tf == timeframe
            button.configure(
                fg_color=DataTerminalTheme.PRIMARY if is_active else "transparent",
                text_color=DataTerminalTheme.BACKGROUND if is_active else DataTerminalTheme.PRIMARY
            )
        
        self.current_timeframe = timeframe
        self.update_timeframe(timeframe)
    
    def update_timeframe(self, timeframe: str) -> None:
        """Update chart with smooth transition animations."""
        if self.animation_running:
            return
        
        self.animation_running = True
        
        # Generate new data based on timeframe
        new_data = self._generate_timeframe_data(timeframe)
        
        # Start smooth transition animation
        self._animate_transition(new_data)
    
    def _generate_timeframe_data(self, timeframe: str) -> Dict[str, np.ndarray]:
        """Generate realistic data for different timeframes."""
        if timeframe == "24h":
            x_data = np.arange(24)
            base_temp = 18
            variation = 10 * np.sin((x_data - 6) * np.pi / 12)
            noise = np.random.normal(0, 1.5, 24)
            y_data = base_temp + variation + noise
            xlabel = "Hour"
            
        elif timeframe == "7d":
            x_data = np.arange(7)
            base_temp = 20
            variation = 8 * np.sin(x_data * np.pi / 3.5)
            noise = np.random.normal(0, 2, 7)
            y_data = base_temp + variation + noise
            xlabel = "Day"
            
        else:  # 30d
            x_data = np.arange(30)
            base_temp = 15
            seasonal = 12 * np.sin(x_data * np.pi / 15)
            weather_variation = 5 * np.sin(x_data * np.pi / 7)
            noise = np.random.normal(0, 3, 30)
            y_data = base_temp + seasonal + weather_variation + noise
            xlabel = "Day"
        
        return {
            'x_data': x_data,
            'y_data': y_data,
            'xlabel': xlabel
        }
    
    def _animate_transition(self, new_data: Dict[str, np.ndarray]) -> None:
        """Animate smooth transition between timeframes."""
        def animate_frame():
            try:
                # Clear and redraw with new data
                self.ax.clear()
                
                # Plot new data with enhanced styling
                self._plot_temperature_with_gradient(new_data['x_data'], new_data['y_data'])
                
                # Update labels and styling
                self.ax.set_title(
                    f"Temperature Forecast ({self.current_timeframe})",
                    color=DataTerminalTheme.PRIMARY,
                    fontsize=16,
                    fontweight='bold',
                    pad=25
                )
                
                self.ax.set_xlabel(
                    new_data['xlabel'],
                    color=DataTerminalTheme.TEXT,
                    fontsize=13,
                    fontweight='bold'
                )
                
                self.ax.set_ylabel(
                    "Temperature (°C)",
                    color=DataTerminalTheme.TEXT,
                    fontsize=13,
                    fontweight='bold'
                )
                
                self._apply_glassmorphic_styling()
                
                self.figure.tight_layout()
                self.canvas.draw()
                
            finally:
                self.animation_running = False
        
        # Use threading for smooth animation
        threading.Thread(target=animate_frame, daemon=True).start()
    
    def _on_mouse_motion(self, event) -> None:
        """Handle mouse motion for interactive tooltips."""
        if event.inaxes != self.ax or not hasattr(self.ax, 'lines') or not self.ax.lines:
            self._hide_tooltip()
            return
        
        try:
            # Find nearest data point
            line = self.ax.lines[0]
            xdata, ydata = line.get_data()
            
            if len(xdata) == 0:
                return
            
            # Convert datetime x-data to numeric for distance calculation
            if hasattr(xdata[0], 'timestamp'):  # datetime objects
                # Convert to matplotlib date numbers for calculation
                from matplotlib.dates import date2num
                x_numeric = np.array([date2num(x) for x in xdata])
            else:
                x_numeric = np.array(xdata)
            
            # Convert event coordinates if needed
            if event.xdata is None or event.ydata is None:
                self._hide_tooltip()
                return
            
            # Calculate distances using numeric coordinates
            y_numeric = np.array(ydata)
            distances = np.sqrt((x_numeric - event.xdata)**2 + (y_numeric - event.ydata)**2)
            nearest_idx = np.argmin(distances)
            
            # Show tooltip if close enough
            if distances[nearest_idx] < 2.0:  # Threshold for hover detection
                self._show_tooltip(event, xdata[nearest_idx], ydata[nearest_idx], nearest_idx)
            else:
                self._hide_tooltip()
                
        except Exception as e:
            # Silently handle errors to prevent spam
            self._hide_tooltip()
    
    def _show_tooltip(self, event, x_val: float, y_val: float, idx: int) -> None:
        """Show interactive tooltip with detailed information."""
        # Format tooltip content based on timeframe
        if self.current_timeframe == "24h":
            time_str = f"{int(x_val):02d}:00"
            detail = f"Hour {int(x_val)}"
        elif self.current_timeframe == "7d":
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            time_str = days[int(x_val) % 7]
            detail = f"Day {int(x_val) + 1}"
        else:  # 30d
            time_str = f"Day {int(x_val) + 1}"
            detail = f"Month progress: {int(x_val) + 1}/30"
        
        # Create rich tooltip content
        tooltip_text = (
            f"🌡️ {y_val:.1f}°C\n"
            f"⏰ {time_str}\n"
            f"📊 {detail}"
        )
        
        self.tooltip_label.configure(text=tooltip_text)
        
        # Position tooltip near cursor
        x_pos = event.x + 20
        y_pos = event.y - 60
        
        # Ensure tooltip stays within widget bounds
        widget_width = self.chart_frame.winfo_width()
        widget_height = self.chart_frame.winfo_height()
        
        if x_pos + 150 > widget_width:
            x_pos = event.x - 170
        if y_pos < 0:
            y_pos = event.y + 20
        
        self.tooltip_frame.place(x=x_pos, y=y_pos)
    
    def _hide_tooltip(self) -> None:
        """Hide the interactive tooltip."""
        self.tooltip_frame.place_forget()
    
    def _on_mouse_click(self, event) -> None:
        """Handle mouse clicks for additional interactions."""
        if event.inaxes == self.ax and event.dblclick:
            # Double-click to reset zoom
            self.ax.autoscale()
            self.canvas.draw()
    
    def _on_mouse_leave(self, event) -> None:
        """Handle mouse leaving the chart area."""
        self._hide_tooltip()
    
    def _on_resize(self, event) -> None:
        """Handle window resize for responsive design."""
        if hasattr(self, 'figure'):
            self.figure.tight_layout()
            self.canvas.draw()
    
    def update_size(self, width, height):
        """Update chart size for responsive design."""
        try:
            # Convert pixels to inches for matplotlib (assuming 100 DPI)
            width_inches = max(6, width / 100)
            height_inches = max(4, height / 100)
            
            # Update figure size
            self.figure.set_size_inches(width_inches, height_inches)
            
            # Update canvas widget size
            self.canvas.get_tk_widget().configure(width=int(width), height=int(height))
            
            # Adjust layout and redraw
            self.figure.tight_layout()
            self.canvas.draw()
            
            # Update font sizes based on chart size
            title_font_size = max(12, min(18, width // 80))
            label_font_size = max(10, min(14, width // 100))
            
            # Update title font size if chart has data
            if hasattr(self.ax, 'title') and self.ax.title:
                self.ax.title.set_fontsize(title_font_size)
            
            # Update axis label font sizes
            if hasattr(self.ax, 'xaxis'):
                self.ax.xaxis.label.set_fontsize(label_font_size)
            if hasattr(self.ax, 'yaxis'):
                self.ax.yaxis.label.set_fontsize(label_font_size)
            
            # Update tick label sizes
            self.ax.tick_params(labelsize=max(8, min(12, width // 120)))
            
            # Redraw with updated styling
            self.canvas.draw()
            
        except Exception as e:
            # Log error but don't crash the application
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error updating chart size: {e}")
    
    def export_chart(self, format_type: str = "png") -> None:
        """Export chart to PNG or PDF format."""
        try:
            from tkinter import filedialog
            
            # File dialog for save location
            if format_type.lower() == "png":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                    title="Export Chart as PNG"
                )
            else:  # PDF
                filename = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                    title="Export Chart as PDF"
                )
            
            if filename:
                # Save with high quality
                self.figure.savefig(
                    filename,
                    format=format_type.lower(),
                    dpi=300,
                    bbox_inches='tight',
                    facecolor='none' if format_type.lower() == 'png' else DataTerminalTheme.BACKGROUND,
                    edgecolor='none',
                    transparent=True if format_type.lower() == 'png' else False
                )
                
                # Show success message
                self._show_export_success(filename)
                
        except Exception as e:
            self._show_export_error(str(e))
    
    def _show_export_success(self, filename: str) -> None:
        """Show export success notification."""
        # Create temporary success indicator
        success_label = ctk.CTkLabel(
            self.header_frame,
            text=f"✅ Exported: {filename.split('/')[-1]}",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.SUCCESS
        )
        success_label.grid(row=0, column=1, padx=20)
        
        # Auto-hide after 3 seconds
        self.after(3000, success_label.destroy)
    
    def _show_export_error(self, error_msg: str) -> None:
        """Show export error notification."""
        error_label = ctk.CTkLabel(
            self.header_frame,
            text=f"❌ Export failed: {error_msg[:30]}...",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.ERROR
        )
        error_label.grid(row=0, column=1, padx=20)
        
        # Auto-hide after 5 seconds
        self.after(5000, error_label.destroy)
    
    def update_forecast(self, forecast_data: List[ForecastData]) -> None:
        """Update chart with new forecast data."""
        self.forecast_data = forecast_data
        
        if not forecast_data:
            self._create_default_chart()
            return
        
        # Extract data from forecast
        dates = [item.date for item in forecast_data]
        min_temps = [item.temp_min for item in forecast_data]
        max_temps = [item.temp_max for item in forecast_data]
        
        # Clear and redraw
        self.ax.clear()
        
        # Plot temperature range with enhanced styling
        self.ax.fill_between(
            dates, min_temps, max_temps,
            alpha=0.3,
            color=DataTerminalTheme.PRIMARY,
            label='Temperature Range',
            zorder=1
        )
        
        # Plot max temperature line
        self.ax.plot(
            dates, max_temps,
            color=DataTerminalTheme.PRIMARY,
            linewidth=4,
            marker='o',
            markersize=8,
            markerfacecolor=DataTerminalTheme.PRIMARY,
            markeredgecolor=DataTerminalTheme.BACKGROUND,
            markeredgewidth=2,
            label='Max Temperature',
            zorder=3
        )
        
        # Plot min temperature line
        self.ax.plot(
            dates, min_temps,
            color=DataTerminalTheme.CHART_SECONDARY,
            linewidth=4,
            marker='o',
            markersize=8,
            markerfacecolor=DataTerminalTheme.CHART_SECONDARY,
            markeredgecolor=DataTerminalTheme.BACKGROUND,
            markeredgewidth=2,
            label='Min Temperature',
            zorder=3
        )
        
        # Add trend indicators for real data
        self._add_trend_indicators(np.arange(len(max_temps)), np.array(max_temps))
        
        # Enhanced styling
        self.ax.set_title(
            f"Temperature Forecast ({len(forecast_data)} Days)",
            color=DataTerminalTheme.PRIMARY,
            fontsize=16,
            fontweight='bold',
            pad=25
        )
        
        self.ax.set_ylabel(
            "Temperature (°C)",
            color=DataTerminalTheme.TEXT,
            fontsize=13,
            fontweight='bold'
        )
        
        # Format x-axis for dates
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        
        # Add value labels with enhanced styling
        for i, (date, min_temp, max_temp) in enumerate(zip(dates, min_temps, max_temps)):
            self.ax.annotate(
                f'{max_temp}°',
                (date, max_temp),
                textcoords="offset points",
                xytext=(0, 15),
                ha='center',
                color=DataTerminalTheme.PRIMARY,
                fontsize=10,
                fontweight='bold',
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor='#1E1E1E80',
                    edgecolor=DataTerminalTheme.PRIMARY,
                    alpha=0.8
                )
            )
            
            self.ax.annotate(
                f'{min_temp}°',
                (date, min_temp),
                textcoords="offset points",
                xytext=(0, -20),
                ha='center',
                color=DataTerminalTheme.CHART_SECONDARY,
                fontsize=10,
                fontweight='bold',
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor='#1E1E1E80',
                    edgecolor=DataTerminalTheme.CHART_SECONDARY,
                    alpha=0.8
                )
            )
        
        self._apply_glassmorphic_styling()
        
        # Enhanced legend
        legend = self.ax.legend(
            loc='upper right',
            frameon=True,
            facecolor='#1E1E1E80',
            edgecolor=DataTerminalTheme.PRIMARY,
            fontsize=11,
            shadow=True
        )
        legend.get_frame().set_alpha(0.9)
        for text in legend.get_texts():
            text.set_color(DataTerminalTheme.TEXT)
            text.set_fontweight('bold')
        
        # Rotate x-axis labels
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def clear_chart(self) -> None:
        """Clear the chart and show default view."""
        self.forecast_data = None
        self._create_default_chart()