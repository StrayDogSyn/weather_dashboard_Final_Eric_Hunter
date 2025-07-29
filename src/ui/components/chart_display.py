"""Chart Display Component

Displays weather charts using matplotlib with Data Terminal styling.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
from matplotlib.figure import Figure
import numpy as np
from typing import List, Optional
from datetime import datetime, timedelta

from ..theme import DataTerminalTheme
from ...services.weather_service import ForecastData


class ChartDisplayFrame(ctk.CTkFrame):
    """Chart display component with matplotlib integration."""
    
    def __init__(self, parent, **kwargs):
        """Initialize chart display."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("default"), **kwargs)
        
        self.forecast_data: Optional[List[ForecastData]] = None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._setup_matplotlib()
        self._create_widgets()
        self._setup_layout()
        self._create_default_chart()
    
    def _setup_matplotlib(self) -> None:
        """Configure matplotlib with Data Terminal theme."""
        # Apply custom style
        plt.style.use('dark_background')
        
        # Update rcParams with our theme
        theme_style = DataTerminalTheme.get_matplotlib_style()
        plt.rcParams.update(theme_style)
    
    def _create_widgets(self) -> None:
        """Create all widgets."""
        # Header
        self.header_frame = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="📊 TEMPERATURE FORECAST",
            **DataTerminalTheme.get_label_style("subtitle")
        )
        
        self.chart_type_var = ctk.StringVar(value="temperature")
        self.chart_selector = ctk.CTkSegmentedButton(
            self.header_frame,
            values=["temperature", "humidity", "wind"],
            variable=self.chart_type_var,
            command=self._on_chart_type_change,
            fg_color=DataTerminalTheme.ACCENT,
            selected_color=DataTerminalTheme.PRIMARY,
            selected_hover_color=DataTerminalTheme.SUCCESS,
            unselected_color=DataTerminalTheme.CARD_BG,
            unselected_hover_color=DataTerminalTheme.HOVER,
            text_color=DataTerminalTheme.TEXT,
            font=DataTerminalTheme.get_font(DataTerminalTheme.FONT_SIZE_SMALL)
        )
        
        # Chart frame
        self.chart_frame = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        # Create matplotlib figure
        self.figure = Figure(
            figsize=(8, 6),
            facecolor=DataTerminalTheme.BACKGROUND,
            edgecolor=DataTerminalTheme.BORDER
        )
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(DataTerminalTheme.CARD_BG)
        
        # Create canvas
        self.canvas = FigureCanvasTkinter(self.figure, self.chart_frame)
        self.canvas.get_tk_widget().configure(
            bg=DataTerminalTheme.BACKGROUND,
            highlightthickness=0
        )
    
    def _setup_layout(self) -> None:
        """Arrange widgets."""
        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        self.title_label.grid(row=0, column=0, pady=5, sticky="w")
        self.chart_selector.grid(row=1, column=0, pady=(5, 0), sticky="ew")
        
        # Chart
        self.chart_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(0, weight=1)
        
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
    
    def _create_default_chart(self) -> None:
        """Create default chart when no data is available."""
        self.ax.clear()
        
        # Create sample data for demonstration
        x = np.linspace(0, 4, 5)
        y = [20, 22, 25, 23, 21]
        
        # Plot with theme colors
        self.ax.plot(
            x, y,
            color=DataTerminalTheme.PRIMARY,
            linewidth=3,
            marker='o',
            markersize=8,
            markerfacecolor=DataTerminalTheme.PRIMARY,
            markeredgecolor=DataTerminalTheme.BACKGROUND,
            markeredgewidth=2
        )
        
        # Fill area under curve
        self.ax.fill_between(
            x, y,
            alpha=0.3,
            color=DataTerminalTheme.PRIMARY
        )
        
        # Styling
        self.ax.set_title(
            "Temperature Forecast",
            color=DataTerminalTheme.TEXT,
            fontsize=14,
            fontweight='bold',
            pad=20
        )
        
        self.ax.set_xlabel(
            "Days",
            color=DataTerminalTheme.TEXT,
            fontsize=12
        )
        
        self.ax.set_ylabel(
            "Temperature (°C)",
            color=DataTerminalTheme.TEXT,
            fontsize=12
        )
        
        # Grid
        self.ax.grid(
            True,
            color=DataTerminalTheme.CHART_GRID,
            alpha=0.3,
            linestyle='-',
            linewidth=0.5
        )
        
        # Spines
        for spine in self.ax.spines.values():
            spine.set_color(DataTerminalTheme.BORDER)
            spine.set_linewidth(1)
        
        # Tick colors
        self.ax.tick_params(
            colors=DataTerminalTheme.TEXT,
            which='both'
        )
        
        # Add placeholder text
        self.ax.text(
            0.5, 0.95,
            "Select a city to view forecast data",
            transform=self.ax.transAxes,
            ha='center',
            va='top',
            color=DataTerminalTheme.TEXT_SECONDARY,
            fontsize=10,
            style='italic'
        )
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _on_chart_type_change(self, value: str) -> None:
        """Handle chart type selection change."""
        if self.forecast_data:
            self._update_chart(value)
    
    def update_forecast(self, forecast_data: List[ForecastData]) -> None:
        """Update chart with new forecast data."""
        self.forecast_data = forecast_data
        chart_type = self.chart_type_var.get()
        self._update_chart(chart_type)
    
    def _update_chart(self, chart_type: str) -> None:
        """Update chart based on type and data."""
        if not self.forecast_data:
            self._create_default_chart()
            return
        
        self.ax.clear()
        
        # Prepare data
        dates = [item.date for item in self.forecast_data]
        
        if chart_type == "temperature":
            self._create_temperature_chart(dates)
        elif chart_type == "humidity":
            self._create_humidity_chart(dates)
        elif chart_type == "wind":
            self._create_wind_chart(dates)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _create_temperature_chart(self, dates: List[datetime]) -> None:
        """Create temperature forecast chart."""
        min_temps = [item.temp_min for item in self.forecast_data]
        max_temps = [item.temp_max for item in self.forecast_data]
        
        # Plot temperature range
        self.ax.fill_between(
            dates, min_temps, max_temps,
            alpha=0.3,
            color=DataTerminalTheme.PRIMARY,
            label='Temperature Range'
        )
        
        # Plot min and max lines
        self.ax.plot(
            dates, max_temps,
            color=DataTerminalTheme.PRIMARY,
            linewidth=3,
            marker='o',
            markersize=6,
            label='Max Temperature'
        )
        
        self.ax.plot(
            dates, min_temps,
            color=DataTerminalTheme.CHART_SECONDARY,
            linewidth=3,
            marker='o',
            markersize=6,
            label='Min Temperature'
        )
        
        # Styling
        self.ax.set_title(
            "Temperature Forecast (5 Days)",
            color=DataTerminalTheme.TEXT,
            fontsize=14,
            fontweight='bold',
            pad=20
        )
        
        self.ax.set_ylabel(
            "Temperature (°C)",
            color=DataTerminalTheme.TEXT,
            fontsize=12
        )
        
        # Format x-axis
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        
        # Add value labels
        for i, (date, min_temp, max_temp) in enumerate(zip(dates, min_temps, max_temps)):
            self.ax.annotate(
                f'{max_temp}°',
                (date, max_temp),
                textcoords="offset points",
                xytext=(0, 10),
                ha='center',
                color=DataTerminalTheme.PRIMARY,
                fontsize=9,
                fontweight='bold'
            )
            
            self.ax.annotate(
                f'{min_temp}°',
                (date, min_temp),
                textcoords="offset points",
                xytext=(0, -15),
                ha='center',
                color=DataTerminalTheme.CHART_SECONDARY,
                fontsize=9,
                fontweight='bold'
            )
        
        self._apply_common_styling()
        
        # Legend
        legend = self.ax.legend(
            loc='upper right',
            frameon=True,
            facecolor=DataTerminalTheme.CARD_BG,
            edgecolor=DataTerminalTheme.BORDER,
            fontsize=10
        )
        legend.get_frame().set_alpha(0.9)
        for text in legend.get_texts():
            text.set_color(DataTerminalTheme.TEXT)
    
    def _create_humidity_chart(self, dates: List[datetime]) -> None:
        """Create humidity forecast chart."""
        humidity_values = [item.humidity for item in self.forecast_data]
        
        # Bar chart for humidity
        bars = self.ax.bar(
            dates, humidity_values,
            color=DataTerminalTheme.INFO,
            alpha=0.7,
            edgecolor=DataTerminalTheme.PRIMARY,
            linewidth=2
        )
        
        # Add value labels on bars
        for bar, humidity in zip(bars, humidity_values):
            height = bar.get_height()
            self.ax.annotate(
                f'{humidity}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center',
                va='bottom',
                color=DataTerminalTheme.TEXT,
                fontsize=10,
                fontweight='bold'
            )
        
        # Styling
        self.ax.set_title(
            "Humidity Forecast (5 Days)",
            color=DataTerminalTheme.TEXT,
            fontsize=14,
            fontweight='bold',
            pad=20
        )
        
        self.ax.set_ylabel(
            "Humidity (%)",
            color=DataTerminalTheme.TEXT,
            fontsize=12
        )
        
        self.ax.set_ylim(0, 100)
        
        # Format x-axis
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        
        self._apply_common_styling()
    
    def _create_wind_chart(self, dates: List[datetime]) -> None:
        """Create wind speed forecast chart."""
        wind_speeds = [item.wind_speed for item in self.forecast_data]
        
        # Line chart for wind speed
        self.ax.plot(
            dates, wind_speeds,
            color=DataTerminalTheme.WARNING,
            linewidth=4,
            marker='s',
            markersize=8,
            markerfacecolor=DataTerminalTheme.WARNING,
            markeredgecolor=DataTerminalTheme.BACKGROUND,
            markeredgewidth=2
        )
        
        # Fill area under curve
        self.ax.fill_between(
            dates, wind_speeds,
            alpha=0.3,
            color=DataTerminalTheme.WARNING
        )
        
        # Add value labels
        for date, wind_speed in zip(dates, wind_speeds):
            self.ax.annotate(
                f'{wind_speed} m/s',
                (date, wind_speed),
                textcoords="offset points",
                xytext=(0, 15),
                ha='center',
                color=DataTerminalTheme.WARNING,
                fontsize=9,
                fontweight='bold'
            )
        
        # Styling
        self.ax.set_title(
            "Wind Speed Forecast (5 Days)",
            color=DataTerminalTheme.TEXT,
            fontsize=14,
            fontweight='bold',
            pad=20
        )
        
        self.ax.set_ylabel(
            "Wind Speed (m/s)",
            color=DataTerminalTheme.TEXT,
            fontsize=12
        )
        
        # Format x-axis
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        
        self._apply_common_styling()
    
    def _apply_common_styling(self) -> None:
        """Apply common styling to all charts."""
        # Grid
        self.ax.grid(
            True,
            color=DataTerminalTheme.CHART_GRID,
            alpha=0.3,
            linestyle='-',
            linewidth=0.5
        )
        
        # Spines
        for spine in self.ax.spines.values():
            spine.set_color(DataTerminalTheme.BORDER)
            spine.set_linewidth(1)
        
        # Tick colors
        self.ax.tick_params(
            colors=DataTerminalTheme.TEXT,
            which='both'
        )
        
        # X-axis label
        self.ax.set_xlabel(
            "Date",
            color=DataTerminalTheme.TEXT,
            fontsize=12
        )
        
        # Rotate x-axis labels for better readability
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def clear_chart(self) -> None:
        """Clear the chart and show default view."""
        self.forecast_data = None
        self._create_default_chart()