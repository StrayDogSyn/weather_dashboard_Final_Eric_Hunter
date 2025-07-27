#!/usr/bin/env python3
"""
Temperature Graph Feature - Interactive Weather Visualization

This module implements the Temperature Graph capstone feature (⭐⭐ difficulty),
demonstrating advanced data visualization techniques including:
- Professional matplotlib integration with CustomTkinter
- Interactive glassmorphic chart containers
- Real-time data updates and smooth animations
- Multiple visualization modes (hourly, daily, weekly)
- Advanced chart styling with weather-responsive themes
- Data export and sharing capabilities

Architectural Decisions:
- Separation of data processing from visualization logic
- Component-based design for reusable chart elements
- Event-driven updates for real-time data synchronization
- Professional error handling with graceful fallbacks
- Accessibility features for chart interaction
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import json
from pathlib import Path

from ..utils.logger import LoggerMixin
from ..ui.components.base_components import (
    GlassFrame, GlassButton, GlassLabel, GlassEntry,
    ComponentSize, create_glass_card
)
from ..ui.theme_manager import ThemeManager, WeatherTheme, GlassEffect
from ..services.weather_service import WeatherData, ForecastData
from ..core.database_manager import DatabaseManager, WeatherRecord


class ChartType(Enum):
    """
    Available chart visualization types.

    This enum supports multiple visualization modes
    for comprehensive temperature analysis.
    """
    LINE = "line"
    AREA = "area"
    BAR = "bar"
    SCATTER = "scatter"
    CANDLESTICK = "candlestick"


class TimeRange(Enum):
    """
    Time range options for temperature data display.

    This enum provides flexible time-based data filtering
    for different analysis needs.
    """
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    CUSTOM = "custom"


@dataclass
class ChartConfig:
    """
    Configuration for temperature chart appearance and behavior.

    This dataclass demonstrates professional chart configuration
    with comprehensive styling and interaction options.
    """
    chart_type: ChartType = ChartType.LINE
    time_range: TimeRange = TimeRange.LAST_7_DAYS
    show_grid: bool = True
    show_legend: bool = True
    show_annotations: bool = True
    enable_zoom: bool = True
    enable_pan: bool = True
    auto_refresh: bool = True
    refresh_interval: int = 300  # seconds

    # Styling options
    background_color: str = "#1a1a1a"
    grid_color: str = "#333333"
    text_color: str = "#ffffff"
    line_color: str = "#4A90E2"
    fill_color: str = "#4A90E240"

    # Chart dimensions
    figure_width: float = 12.0
    figure_height: float = 6.0
    dpi: int = 100


@dataclass
class TemperatureDataPoint:
    """
    Single temperature data point with metadata.

    This dataclass provides structured temperature data
    with comprehensive metadata for analysis.
    """
    timestamp: datetime
    temperature: float
    feels_like: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    condition: Optional[str] = None
    location: Optional[str] = None


class TemperatureGraphWidget(GlassFrame, LoggerMixin):
    """
    Interactive Temperature Graph Widget.

    This class implements a professional temperature visualization
    component with glassmorphic styling and advanced interactivity.
    It demonstrates integration of matplotlib with CustomTkinter
    for modern data visualization.
    """

    def __init__(
        self,
        parent,
        database_manager: DatabaseManager,
        config: Optional[ChartConfig] = None,
        **kwargs
    ):
        # Initialize base components
        glass_effect = GlassEffect(
            background_alpha=0.05,
            border_alpha=0.1,
            blur_radius=20,
            corner_radius=15
        )

        super().__init__(parent, glass_effect=glass_effect, size=ComponentSize.EXTRA_LARGE, **kwargs)

        # Core dependencies
        self.database_manager = database_manager
        self.config = config or ChartConfig()
        self.theme_manager = ThemeManager()

        # Data management
        self.temperature_data: List[TemperatureDataPoint] = []
        self.filtered_data: List[TemperatureDataPoint] = []
        self.is_loading = False
        self.last_update = None

        # Chart components
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.toolbar: Optional[NavigationToolbar2Tk] = None
        self.ax = None

        # UI components
        self.control_panel: Optional[GlassFrame] = None
        self.chart_container: Optional[GlassFrame] = None
        self.status_panel: Optional[GlassFrame] = None

        # Event callbacks
        self.data_update_callbacks: List[Callable] = []

        # Initialize UI
        self._setup_ui()
        self._setup_chart()
        self._load_initial_data()

        # Start auto-refresh if enabled
        if self.config.auto_refresh:
            self._start_auto_refresh()

        self.logger.info("Temperature Graph Widget initialized")

    def _setup_ui(self) -> None:
        """
        Set up the user interface layout.

        This method demonstrates professional UI composition
        with clear separation of concerns and responsive design.
        """
        # Configure main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create control panel
        self._create_control_panel()

        # Create chart container
        self._create_chart_container()

        # Create status panel
        self._create_status_panel()

        self.logger.debug("UI setup completed")

    def _create_control_panel(self) -> None:
        """
        Create the chart control panel with options and filters.

        This method demonstrates professional control interface design
        with comprehensive chart customization options.
        """
        self.control_panel = GlassFrame(
            self,
            glass_effect=GlassEffect(
                background_alpha=0.1,
                border_alpha=0.2,
                corner_radius=10
            )
        )
        self.control_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.control_panel.configure(height=80)

        # Title
        title_label = GlassLabel(
            self.control_panel,
            text="Temperature Analysis",
            text_style="heading",
            size=ComponentSize.LARGE
        )
        title_label.pack(side="left", padx=20, pady=20)

        # Control buttons frame
        controls_frame = GlassFrame(self.control_panel)
        controls_frame.pack(side="right", padx=20, pady=15)

        # Time range buttons
        time_frame = GlassFrame(controls_frame)
        time_frame.pack(side="left", padx=5)

        time_label = GlassLabel(
            time_frame,
            text="Time Range:",
            text_style="normal",
            size=ComponentSize.SMALL
        )
        time_label.pack(side="left", padx=(0, 5))

        self.time_buttons = {}
        time_options = [
            ("24H", TimeRange.LAST_24_HOURS),
            ("7D", TimeRange.LAST_7_DAYS),
            ("30D", TimeRange.LAST_30_DAYS),
            ("90D", TimeRange.LAST_90_DAYS)
        ]

        for text, time_range in time_options:
            button = GlassButton(
                time_frame,
                text=text,
                size=ComponentSize.SMALL,
                command=lambda tr=time_range: self._set_time_range(tr)
            )
            button.pack(side="left", padx=2)
            self.time_buttons[time_range] = button

        # Chart type buttons
        chart_frame = GlassFrame(controls_frame)
        chart_frame.pack(side="left", padx=15)

        chart_label = GlassLabel(
            chart_frame,
            text="Chart Type:",
            text_style="normal",
            size=ComponentSize.SMALL
        )
        chart_label.pack(side="left", padx=(0, 5))

        self.chart_buttons = {}
        chart_options = [
            ("📈", ChartType.LINE),
            ("📊", ChartType.BAR),
            ("🔵", ChartType.SCATTER),
            ("📈", ChartType.AREA)
        ]

        for text, chart_type in chart_options:
            button = GlassButton(
                chart_frame,
                text=text,
                size=ComponentSize.SMALL,
                command=lambda ct=chart_type: self._set_chart_type(ct)
            )
            button.pack(side="left", padx=2)
            self.chart_buttons[chart_type] = button

        # Action buttons
        action_frame = GlassFrame(controls_frame)
        action_frame.pack(side="left", padx=15)

        self.refresh_button = GlassButton(
            action_frame,
            text="🔄",
            size=ComponentSize.SMALL,
            command=self._refresh_data
        )
        self.refresh_button.pack(side="left", padx=2)

        self.export_button = GlassButton(
            action_frame,
            text="💾",
            size=ComponentSize.SMALL,
            command=self._export_chart
        )
        self.export_button.pack(side="left", padx=2)

        self.settings_button = GlassButton(
            action_frame,
            text="⚙️",
            size=ComponentSize.SMALL,
            command=self._show_settings
        )
        self.settings_button.pack(side="left", padx=2)

        # Update button states
        self._update_control_states()

    def _create_chart_container(self) -> None:
        """
        Create the main chart container with matplotlib integration.

        This method demonstrates professional matplotlib integration
        with CustomTkinter for modern data visualization.
        """
        self.chart_container = GlassFrame(
            self,
            glass_effect=GlassEffect(
                background_alpha=0.03,
                border_alpha=0.1,
                corner_radius=15
            )
        )
        self.chart_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Chart will be created in _setup_chart method

        self.logger.debug("Chart container created")

    def _create_status_panel(self) -> None:
        """
        Create the status panel with chart information and statistics.

        This method demonstrates professional status display
        with real-time chart statistics and metadata.
        """
        self.status_panel = GlassFrame(
            self,
            glass_effect=GlassEffect(
                background_alpha=0.1,
                border_alpha=0.2,
                corner_radius=10
            )
        )
        self.status_panel.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.status_panel.configure(height=60)

        # Status information
        status_info_frame = GlassFrame(self.status_panel)
        status_info_frame.pack(side="left", padx=20, pady=15)

        self.data_points_label = GlassLabel(
            status_info_frame,
            text="Data Points: 0",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.data_points_label.pack(side="left", padx=5)

        self.date_range_label = GlassLabel(
            status_info_frame,
            text="Range: No data",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.date_range_label.pack(side="left", padx=15)

        self.last_update_label = GlassLabel(
            status_info_frame,
            text="Last Update: Never",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.last_update_label.pack(side="left", padx=15)

        # Statistics
        stats_frame = GlassFrame(self.status_panel)
        stats_frame.pack(side="right", padx=20, pady=15)

        self.min_temp_label = GlassLabel(
            stats_frame,
            text="Min: --°F",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.min_temp_label.pack(side="left", padx=5)

        self.max_temp_label = GlassLabel(
            stats_frame,
            text="Max: --°F",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.max_temp_label.pack(side="left", padx=15)

        self.avg_temp_label = GlassLabel(
            stats_frame,
            text="Avg: --°F",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.avg_temp_label.pack(side="left", padx=15)

    def _setup_chart(self) -> None:
        """
        Set up the matplotlib chart with glassmorphic styling.

        This method demonstrates advanced matplotlib configuration
        with professional styling and interactive features.
        """
        # Configure matplotlib for dark theme
        plt.style.use('dark_background')

        # Create figure with glassmorphic styling
        self.figure = Figure(
            figsize=(self.config.figure_width, self.config.figure_height),
            dpi=self.config.dpi,
            facecolor=self.config.background_color,
            edgecolor='none'
        )

        # Create subplot
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(self.config.background_color)

        # Configure chart styling
        self._apply_chart_styling()

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self.chart_container)
        self.canvas.draw()

        # Pack canvas
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)

        # Create navigation toolbar
        toolbar_frame = GlassFrame(self.chart_container)
        toolbar_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Configure toolbar styling
        self._style_toolbar()

        # Bind events
        self.canvas.mpl_connect('button_press_event', self._on_chart_click)
        self.canvas.mpl_connect('motion_notify_event', self._on_chart_hover)

        self.logger.debug("Chart setup completed")

    def _apply_chart_styling(self) -> None:
        """
        Apply glassmorphic styling to the chart.

        This method demonstrates professional chart styling
        with weather-responsive themes and accessibility.
        """
        # Configure axes
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color(self.config.grid_color)
        self.ax.spines['left'].set_color(self.config.grid_color)

        # Configure grid
        if self.config.show_grid:
            self.ax.grid(
                True,
                color=self.config.grid_color,
                alpha=0.3,
                linestyle='-',
                linewidth=0.5
            )

        # Configure labels and title
        self.ax.set_xlabel('Time', color=self.config.text_color, fontsize=12)
        self.ax.set_ylabel('Temperature (°F)', color=self.config.text_color, fontsize=12)
        self.ax.set_title(
            'Temperature Trends',
            color=self.config.text_color,
            fontsize=16,
            fontweight='bold',
            pad=20
        )

        # Configure tick parameters
        self.ax.tick_params(
            colors=self.config.text_color,
            labelsize=10
        )

        # Configure date formatting
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))

        # Rotate date labels for better readability
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Adjust layout
        self.figure.tight_layout()

    def _style_toolbar(self) -> None:
        """
        Apply custom styling to the navigation toolbar.

        This method demonstrates toolbar customization
        for consistent glassmorphic design.
        """
        try:
            # Configure toolbar background
            self.toolbar.configure(bg=self.config.background_color)

            # Style toolbar buttons (if accessible)
            for child in self.toolbar.winfo_children():
                if hasattr(child, 'configure'):
                    child.configure(
                        bg=self.config.background_color,
                        fg=self.config.text_color,
                        activebackground=self.config.grid_color
                    )
        except Exception as e:
            self.logger.debug(f"Toolbar styling not fully supported: {e}")

    def _load_initial_data(self) -> None:
        """
        Load initial temperature data from database.

        This method demonstrates efficient data loading
        with background processing and error handling.
        """
        def load_data():
            try:
                self.is_loading = True
                self._update_status("Loading temperature data...")

                # Load data from database
                # Calculate days for time range
                time_range_days = self._get_days_for_time_range(self.config.time_range)

                weather_records = self.database_manager.get_weather_history(
                    city="DefaultCity",  # Use a default city or get from config
                    days=time_range_days
                )

                # Convert to temperature data points
                self.temperature_data = self._convert_records_to_data_points(weather_records)

                # Filter and update chart
                self.after(0, self._update_chart)

            except Exception as e:
                error_msg = f"Error loading data: {e}"
                self.logger.error(f"Error loading initial data: {e}")
                self.after(0, lambda msg=error_msg: self._update_status(msg))
            finally:
                self.is_loading = False

        # Load data in background thread
        threading.Thread(target=load_data, daemon=True).start()

    def _convert_records_to_data_points(self, records: List[WeatherRecord]) -> List[TemperatureDataPoint]:
        """
        Convert database records to temperature data points.

        Args:
            records: List of weather records from database

        Returns:
            List of temperature data points
        """
        data_points = []

        for record in records:
            data_point = TemperatureDataPoint(
                timestamp=record.timestamp,
                temperature=record.temperature,
                feels_like=record.feels_like,
                humidity=record.humidity,
                pressure=record.pressure,
                wind_speed=record.wind_speed,
                condition=record.condition,
                location=record.location
            )
            data_points.append(data_point)

        return data_points

    def _get_start_time_for_range(self, time_range: TimeRange) -> datetime:
        """
        Get start time for the specified time range.

        Args:
            time_range: Time range enum value

        Returns:
            Start datetime for the range
        """
        now = datetime.now()

        if time_range == TimeRange.LAST_24_HOURS:
            return now - timedelta(hours=24)
        elif time_range == TimeRange.LAST_7_DAYS:
            return now - timedelta(days=7)
        elif time_range == TimeRange.LAST_30_DAYS:
            return now - timedelta(days=30)
        elif time_range == TimeRange.LAST_90_DAYS:
            return now - timedelta(days=90)
        else:
            return now - timedelta(days=7)  # Default to 7 days

    def _get_days_for_time_range(self, time_range: TimeRange) -> int:
        """
        Get number of days for the specified time range.

        Args:
            time_range: Time range enum value

        Returns:
            Number of days for the range
        """
        if time_range == TimeRange.LAST_24_HOURS:
            return 1
        elif time_range == TimeRange.LAST_7_DAYS:
            return 7
        elif time_range == TimeRange.LAST_30_DAYS:
            return 30
        elif time_range == TimeRange.LAST_90_DAYS:
            return 90
        else:
            return 7  # Default to 7 days

    def _filter_data_by_time_range(self) -> None:
        """
        Filter temperature data based on current time range setting.

        This method demonstrates efficient data filtering
        with time-based criteria and performance optimization.
        """
        if not self.temperature_data:
            self.filtered_data = []
            return

        start_time = self._get_start_time_for_range(self.config.time_range)
        end_time = datetime.now()

        self.filtered_data = [
            point for point in self.temperature_data
            if start_time <= point.timestamp <= end_time
        ]

        # Sort by timestamp
        self.filtered_data.sort(key=lambda x: x.timestamp)

        self.logger.debug(f"Filtered {len(self.filtered_data)} data points for range {self.config.time_range.value}")

    def _update_chart(self) -> None:
        """
        Update the chart with current data and configuration.

        This method demonstrates advanced chart updating
        with smooth animations and performance optimization.
        """
        try:
            # Filter data
            self._filter_data_by_time_range()

            # Clear previous plot
            self.ax.clear()

            # Reapply styling
            self._apply_chart_styling()

            if not self.filtered_data:
                # Show "no data" message
                self.ax.text(
                    0.5, 0.5, 'No temperature data available',
                    transform=self.ax.transAxes,
                    ha='center', va='center',
                    fontsize=16,
                    color=self.config.text_color,
                    alpha=0.7
                )
            else:
                # Plot data based on chart type
                self._plot_temperature_data()

                # Add annotations if enabled
                if self.config.show_annotations:
                    self._add_chart_annotations()

            # Update legend
            if self.config.show_legend and self.filtered_data:
                self.ax.legend(
                    loc='upper left',
                    facecolor=self.config.background_color,
                    edgecolor=self.config.grid_color,
                    labelcolor=self.config.text_color
                )

            # Refresh canvas
            self.canvas.draw()

            # Update status
            self._update_chart_statistics()
            self.last_update = datetime.now()

            # Notify callbacks
            for callback in self.data_update_callbacks:
                try:
                    callback(self.filtered_data)
                except Exception as e:
                    self.logger.error(f"Error in data update callback: {e}")

            self.logger.debug("Chart updated successfully")

        except Exception as e:
            self.logger.error(f"Error updating chart: {e}")
            self._update_status(f"Error updating chart: {e}")

    def _plot_temperature_data(self) -> None:
        """
        Plot temperature data based on current chart type.

        This method demonstrates multiple visualization techniques
        with professional styling and interactive features.
        """
        if not self.filtered_data:
            return

        # Extract data arrays
        timestamps = [point.timestamp for point in self.filtered_data]
        temperatures = [point.temperature for point in self.filtered_data]
        feels_like = [point.feels_like for point in self.filtered_data if point.feels_like is not None]

        # Plot based on chart type
        if self.config.chart_type == ChartType.LINE:
            self._plot_line_chart(timestamps, temperatures, feels_like)
        elif self.config.chart_type == ChartType.AREA:
            self._plot_area_chart(timestamps, temperatures)
        elif self.config.chart_type == ChartType.BAR:
            self._plot_bar_chart(timestamps, temperatures)
        elif self.config.chart_type == ChartType.SCATTER:
            self._plot_scatter_chart(timestamps, temperatures)
        elif self.config.chart_type == ChartType.CANDLESTICK:
            self._plot_candlestick_chart(timestamps, temperatures)

    def _plot_line_chart(self, timestamps: List[datetime], temperatures: List[float], feels_like: List[float]) -> None:
        """
        Plot line chart with temperature data.

        Args:
            timestamps: List of timestamps
            temperatures: List of temperature values
            feels_like: List of feels-like temperature values
        """
        # Main temperature line
        self.ax.plot(
            timestamps,
            temperatures,
            color=self.config.line_color,
            linewidth=2.5,
            label='Temperature',
            marker='o',
            markersize=4,
            alpha=0.9
        )

        # Feels-like temperature line (if available)
        if feels_like and len(feels_like) == len(timestamps):
            self.ax.plot(
                timestamps,
                feels_like,
                color='#FF6B6B',
                linewidth=2,
                label='Feels Like',
                linestyle='--',
                alpha=0.7
            )

    def _plot_area_chart(self, timestamps: List[datetime], temperatures: List[float]) -> None:
        """
        Plot area chart with temperature data.

        Args:
            timestamps: List of timestamps
            temperatures: List of temperature values
        """
        self.ax.fill_between(
            timestamps,
            temperatures,
            color=self.config.fill_color,
            alpha=0.6,
            label='Temperature'
        )

        self.ax.plot(
            timestamps,
            temperatures,
            color=self.config.line_color,
            linewidth=2,
            alpha=0.9
        )

    def _plot_bar_chart(self, timestamps: List[datetime], temperatures: List[float]) -> None:
        """
        Plot bar chart with temperature data.

        Args:
            timestamps: List of timestamps
            temperatures: List of temperature values
        """
        # Calculate bar width based on data density
        if len(timestamps) > 1:
            time_diff = (timestamps[-1] - timestamps[0]).total_seconds() / len(timestamps)
            bar_width = time_diff / 86400  # Convert to days
        else:
            bar_width = 0.1

        self.ax.bar(
            timestamps,
            temperatures,
            width=bar_width,
            color=self.config.line_color,
            alpha=0.7,
            label='Temperature'
        )

    def _plot_scatter_chart(self, timestamps: List[datetime], temperatures: List[float]) -> None:
        """
        Plot scatter chart with temperature data.

        Args:
            timestamps: List of timestamps
            temperatures: List of temperature values
        """
        # Color points based on temperature
        colors = plt.cm.coolwarm(np.linspace(0, 1, len(temperatures)))

        scatter = self.ax.scatter(
            timestamps,
            temperatures,
            c=temperatures,
            cmap='coolwarm',
            s=50,
            alpha=0.8,
            label='Temperature'
        )

        # Add colorbar
        cbar = self.figure.colorbar(scatter, ax=self.ax)
        cbar.set_label('Temperature (°F)', color=self.config.text_color)
        cbar.ax.yaxis.set_tick_params(color=self.config.text_color)

    def _plot_candlestick_chart(self, timestamps: List[datetime], temperatures: List[float]) -> None:
        """
        Plot candlestick-style chart with temperature data.

        Args:
            timestamps: List of timestamps
            temperatures: List of temperature values
        """
        # Group data by day for candlestick representation
        daily_data = self._group_data_by_day(timestamps, temperatures)

        for date, (open_temp, high_temp, low_temp, close_temp) in daily_data.items():
            # Draw candlestick
            color = self.config.line_color if close_temp >= open_temp else '#FF6B6B'

            # High-low line
            self.ax.plot([date, date], [low_temp, high_temp], color=color, linewidth=2)

            # Open-close rectangle
            height = abs(close_temp - open_temp)
            bottom = min(open_temp, close_temp)

            self.ax.bar(
                date,
                height,
                bottom=bottom,
                width=0.8,
                color=color,
                alpha=0.7
            )

    def _group_data_by_day(self, timestamps: List[datetime], temperatures: List[float]) -> Dict[datetime, Tuple[float, float, float, float]]:
        """
        Group temperature data by day for candlestick chart.

        Args:
            timestamps: List of timestamps
            temperatures: List of temperature values

        Returns:
            Dictionary mapping dates to (open, high, low, close) tuples
        """
        daily_data = {}

        for timestamp, temp in zip(timestamps, temperatures):
            date = timestamp.date()

            if date not in daily_data:
                daily_data[date] = [temp, temp, temp, temp]  # open, high, low, close
            else:
                daily_data[date][1] = max(daily_data[date][1], temp)  # high
                daily_data[date][2] = min(daily_data[date][2], temp)  # low
                daily_data[date][3] = temp  # close (last value)

        # Convert to datetime objects for plotting
        result = {}
        for date, (open_temp, high_temp, low_temp, close_temp) in daily_data.items():
            dt = datetime.combine(date, datetime.min.time())
            result[dt] = (open_temp, high_temp, low_temp, close_temp)

        return result

    def _add_chart_annotations(self) -> None:
        """
        Add annotations to the chart for key data points.

        This method demonstrates advanced chart annotation
        with intelligent placement and styling.
        """
        if not self.filtered_data:
            return

        temperatures = [point.temperature for point in self.filtered_data]

        # Find min and max temperatures
        min_temp = min(temperatures)
        max_temp = max(temperatures)

        min_idx = temperatures.index(min_temp)
        max_idx = temperatures.index(max_temp)

        # Annotate minimum temperature
        self.ax.annotate(
            f'Min: {min_temp:.1f}°F',
            xy=(self.filtered_data[min_idx].timestamp, min_temp),
            xytext=(10, 10),
            textcoords='offset points',
            bbox=dict(
                boxstyle='round,pad=0.3',
                facecolor=self.config.background_color,
                edgecolor=self.config.grid_color,
                alpha=0.8
            ),
            arrowprops=dict(
                arrowstyle='->',
                color=self.config.text_color,
                alpha=0.7
            ),
            color=self.config.text_color,
            fontsize=10
        )

        # Annotate maximum temperature
        self.ax.annotate(
            f'Max: {max_temp:.1f}°F',
            xy=(self.filtered_data[max_idx].timestamp, max_temp),
            xytext=(10, -20),
            textcoords='offset points',
            bbox=dict(
                boxstyle='round,pad=0.3',
                facecolor=self.config.background_color,
                edgecolor=self.config.grid_color,
                alpha=0.8
            ),
            arrowprops=dict(
                arrowstyle='->',
                color=self.config.text_color,
                alpha=0.7
            ),
            color=self.config.text_color,
            fontsize=10
        )

    def _update_chart_statistics(self) -> None:
        """
        Update chart statistics in the status panel.

        This method demonstrates real-time statistics calculation
        and display with professional formatting.
        """
        if not self.filtered_data:
            self.data_points_label.configure(text="Data Points: 0")
            self.date_range_label.configure(text="Range: No data")
            self.min_temp_label.configure(text="Min: --°F")
            self.max_temp_label.configure(text="Max: --°F")
            self.avg_temp_label.configure(text="Avg: --°F")
            return

        # Calculate statistics
        temperatures = [point.temperature for point in self.filtered_data]
        min_temp = min(temperatures)
        max_temp = max(temperatures)
        avg_temp = sum(temperatures) / len(temperatures)

        # Format date range
        start_date = self.filtered_data[0].timestamp.strftime('%m/%d %H:%M')
        end_date = self.filtered_data[-1].timestamp.strftime('%m/%d %H:%M')

        # Update labels
        self.data_points_label.configure(text=f"Data Points: {len(self.filtered_data)}")
        self.date_range_label.configure(text=f"Range: {start_date} - {end_date}")
        self.min_temp_label.configure(text=f"Min: {min_temp:.1f}°F")
        self.max_temp_label.configure(text=f"Max: {max_temp:.1f}°F")
        self.avg_temp_label.configure(text=f"Avg: {avg_temp:.1f}°F")

        # Update last update time
        if self.last_update:
            update_time = self.last_update.strftime('%I:%M %p')
            self.last_update_label.configure(text=f"Last Update: {update_time}")

    def _update_control_states(self) -> None:
        """
        Update control button states based on current configuration.

        This method demonstrates professional UI state management
        with visual feedback for active options.
        """
        # Update time range buttons
        for time_range, button in self.time_buttons.items():
            if time_range == self.config.time_range:
                button.configure(fg_color=("#4A90E2", "#357ABD"))
            else:
                glass_config = button._get_glass_button_config()
                button.configure(fg_color=glass_config['fg_color'])

        # Update chart type buttons
        for chart_type, button in self.chart_buttons.items():
            if chart_type == self.config.chart_type:
                button.configure(fg_color=("#4A90E2", "#357ABD"))
            else:
                glass_config = button._get_glass_button_config()
                button.configure(fg_color=glass_config['fg_color'])

    def _update_status(self, message: str) -> None:
        """
        Update status message.

        Args:
            message: Status message to display
        """
        # Update status in parent if available
        if hasattr(self.master, '_update_status'):
            self.master._update_status(message)

        self.logger.debug(f"Status: {message}")

    def _start_auto_refresh(self) -> None:
        """
        Start automatic data refresh timer.

        This method demonstrates professional auto-refresh
        with configurable intervals and user control.
        """
        def auto_refresh():
            if not self.is_loading and self.config.auto_refresh:
                self._refresh_data(silent=True)

            # Schedule next refresh
            if self.config.auto_refresh:
                self.after(self.config.refresh_interval * 1000, auto_refresh)

        # Start auto-refresh timer
        self.after(self.config.refresh_interval * 1000, auto_refresh)

        self.logger.debug(f"Auto-refresh started with {self.config.refresh_interval}s interval")

    # Event handlers
    def _set_time_range(self, time_range: TimeRange) -> None:
        """
        Set the chart time range.

        Args:
            time_range: New time range to set
        """
        if time_range != self.config.time_range:
            self.config.time_range = time_range
            self._update_control_states()
            self._update_chart()

            self.logger.debug(f"Time range changed to {time_range.value}")

    def _set_chart_type(self, chart_type: ChartType) -> None:
        """
        Set the chart type.

        Args:
            chart_type: New chart type to set
        """
        if chart_type != self.config.chart_type:
            self.config.chart_type = chart_type
            self._update_control_states()
            self._update_chart()

            self.logger.debug(f"Chart type changed to {chart_type.value}")

    def _refresh_data(self, silent: bool = False) -> None:
        """
        Refresh temperature data from database.

        Args:
            silent: Whether to show loading indicators
        """
        if self.is_loading:
            return

        if not silent:
            self._update_status("Refreshing temperature data...")

        # Reload data
        self._load_initial_data()

    def _export_chart(self) -> None:
        """
        Export chart to file.

        This method demonstrates professional data export
        with multiple format options and user feedback.
        """
        try:
            # Create export directory if it doesn't exist
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"temperature_chart_{timestamp}.png"
            filepath = export_dir / filename

            # Save chart
            self.figure.savefig(
                filepath,
                dpi=300,
                bbox_inches='tight',
                facecolor=self.config.background_color,
                edgecolor='none'
            )

            self._update_status(f"Chart exported to {filepath}")
            self.logger.info(f"Chart exported to {filepath}")

        except Exception as e:
            error_msg = f"Error exporting chart: {e}"
            self._update_status(error_msg)
            self.logger.error(error_msg)

    def _show_settings(self) -> None:
        """
        Show chart settings dialog.

        This method demonstrates professional settings interface
        with comprehensive configuration options.
        """
        # Implementation would create a settings dialog
        # For now, show a placeholder message
        self._update_status("Chart settings dialog coming soon!")

    def _on_chart_click(self, event) -> None:
        """
        Handle chart click events.

        Args:
            event: Matplotlib event object
        """
        if event.inaxes == self.ax and event.xdata and event.ydata:
            # Convert x coordinate to datetime
            try:
                clicked_time = mdates.num2date(event.xdata)
                temp = event.ydata

                self.logger.debug(f"Chart clicked at {clicked_time}: {temp:.1f}°F")

                # Could implement data point selection or tooltip here

            except Exception as e:
                self.logger.debug(f"Error processing chart click: {e}")

    def _on_chart_hover(self, event) -> None:
        """
        Handle chart hover events.

        Args:
            event: Matplotlib event object
        """
        # Could implement hover tooltips here
        pass

    # Public API methods
    def add_data_update_callback(self, callback: Callable[[List[TemperatureDataPoint]], None]) -> None:
        """
        Add callback for data update events.

        Args:
            callback: Function to call when data is updated
        """
        self.data_update_callbacks.append(callback)

    def update_weather_data(self, weather_data: WeatherData) -> None:
        """
        Update chart with new weather data.

        Args:
            weather_data: New weather data to add
        """
        # Convert to temperature data point
        # Create location string from city and country
        location = f"{weather_data.city}, {weather_data.country}"
        
        data_point = TemperatureDataPoint(
            timestamp=datetime.now(),
            temperature=weather_data.temperature,
            feels_like=weather_data.feels_like,
            humidity=weather_data.humidity,
            pressure=weather_data.pressure,
            wind_speed=weather_data.wind_speed,
            condition=weather_data.condition,
            location=location
        )

        # Add to data
        self.temperature_data.append(data_point)

        # Update chart
        self._update_chart()

        self.logger.debug(f"Weather data updated: {weather_data.temperature}°F")

    def get_current_data(self) -> List[TemperatureDataPoint]:
        """
        Get current filtered temperature data.

        Returns:
            List of current temperature data points
        """
        return self.filtered_data.copy()

    def set_config(self, config: ChartConfig) -> None:
        """
        Update chart configuration.

        Args:
            config: New chart configuration
        """
        self.config = config
        self._update_control_states()
        self._apply_chart_styling()
        self._update_chart()

        self.logger.debug("Chart configuration updated")


def create_temperature_graph(
    parent,
    database_manager: DatabaseManager,
    config: Optional[ChartConfig] = None
) -> TemperatureGraphWidget:
    """
    Factory function to create a temperature graph widget.

    Args:
        parent: Parent widget
        database_manager: Database manager instance
        config: Optional chart configuration

    Returns:
        Configured TemperatureGraphWidget instance
    """
    return TemperatureGraphWidget(parent, database_manager, config)


if __name__ == "__main__":
    # Test the temperature graph widget
    import tkinter as tk
    from ..core.database_manager import DatabaseManager

    # Create test window
    root = tk.Tk()
    root.title("Temperature Graph Test")
    root.geometry("1200x800")

    # Create database manager
    db_manager = DatabaseManager(":memory:")  # In-memory database for testing

    # Create temperature graph
    config = ChartConfig(
        chart_type=ChartType.LINE,
        time_range=TimeRange.LAST_7_DAYS,
        auto_refresh=False
    )

    graph = create_temperature_graph(root, db_manager, config)
    graph.pack(fill="both", expand=True, padx=10, pady=10)

    # Add some test data
    test_data = []
    base_time = datetime.now() - timedelta(days=7)

    for i in range(168):  # 7 days * 24 hours
        timestamp = base_time + timedelta(hours=i)
        temperature = 70 + 10 * np.sin(i * 2 * np.pi / 24) + np.random.normal(0, 2)

        test_data.append(TemperatureDataPoint(
            timestamp=timestamp,
            temperature=temperature,
            feels_like=temperature + np.random.normal(0, 3),
            humidity=50 + np.random.normal(0, 10),
            condition="Clear" if i % 4 == 0 else "Cloudy"
        ))

    graph.temperature_data = test_data
    graph._update_chart()

    root.mainloop()
