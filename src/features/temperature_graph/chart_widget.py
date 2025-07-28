#!/usr/bin/env python3
"""
Advanced Temperature Chart Widget - Core Implementation

Main chart widget that integrates all temperature graph components including
UI controls, interactions, analytics, and data visualization.

Author: Eric Hunter (Cortana Builder Agent)
Version: 3.0.0 (TRAE 2.0 Phase 3)
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
import threading
import json
from pathlib import Path
from dataclasses import dataclass

# Core imports
from .chart_models import TemperatureDataPoint, ChartType, TimeRange, ChartConfig
from ...ui.components.glass import GlassFrame, GlassButton
from ...utils.logger import LoggerMixin
from .chart_controller import ChartController

# Component imports
from .chart_models import WeatherEvent, CityComparison, GlassmorphicTooltip
from .chart_ui_components import ChartUIComponents
from .chart_interactions import ChartInteractionHandler
from .chart_analytics import ChartAnalyticsEngine, ChartAnalytics, ExportSettings


class AdvancedChartWidget(ctk.CTkFrame, LoggerMixin):
    """Advanced glassmorphic temperature analytics chart widget."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Core properties
        self.current_data: List[TemperatureDataPoint] = []
        self.chart_config = ChartConfig()
        self.weather_events: List[WeatherEvent] = []
        self.city_comparisons: List[CityComparison] = []
        
        # Chart components
        self.fig = None
        self.ax = None
        self.canvas = None
        self.loading_overlay = None
        self.progress_bar = None
        
        # Component handlers
        self.ui_components = ChartUIComponents(self)
        self.interaction_handler = ChartInteractionHandler(self)
        self.analytics_engine = ChartAnalyticsEngine(self)
        
        # Chart controller
        self.chart_controller = ChartController()
        
        # Callbacks
        self.on_data_updated: Optional[Callable] = None
        self.on_export_completed: Optional[Callable] = None
        
        # Initialize UI
        self._setup_ui()
        self._setup_chart()
        self._setup_event_handlers()
        
        # Load initial data
        self._load_initial_data()
    
    def _setup_ui(self):
        """Setup the main UI structure."""
        try:
            self.configure(
                fg_color=("#F8F8F8", "#2A2A2A"),
                corner_radius=15,
                border_width=1,
                border_color=("#E0E0E0", "#404040")
            )
            
            # Setup UI components
            self.ui_components.setup_header_controls()
            self.ui_components.setup_chart_container()
            
        except Exception as e:
            self.logger.error(f"Error setting up UI: {e}")
    
    def _setup_chart(self):
        """Setup matplotlib chart with glassmorphic styling."""
        try:
            # Configure matplotlib for glassmorphic theme
            plt.style.use('dark_background')
            
            # Create figure and axis
            self.fig, self.ax = plt.subplots(figsize=(12, 6), facecolor='none')
            self.ax.set_facecolor('none')
            
            # Glassmorphic styling
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['bottom'].set_color('#FFFFFF40')
            self.ax.spines['left'].set_color('#FFFFFF40')
            
            self.ax.tick_params(colors='#FFFFFF80', which='both')
            self.ax.xaxis.label.set_color('#FFFFFF80')
            self.ax.yaxis.label.set_color('#FFFFFF80')
            
            # Grid styling
            self.ax.grid(True, alpha=0.2, color='#FFFFFF', linestyle='-', linewidth=0.5)
            
            # Create canvas
            self.canvas = FigureCanvasTkAgg(self.fig, self.ui_components.chart_container)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # Setup custom toolbar
            self.ui_components.setup_custom_toolbar()
            
        except Exception as e:
            self.logger.error(f"Error setting up chart: {e}")
    
    def _setup_event_handlers(self):
        """Setup event handlers for interactions."""
        try:
            self.interaction_handler.setup_event_handlers()
        except Exception as e:
            self.logger.error(f"Error setting up event handlers: {e}")
    
    def _load_initial_data(self):
        """Load initial temperature data."""
        try:
            # Show loading state
            self._show_loading(True)
            
            # Load data in background thread
            def load_data():
                try:
                    # Generate initial mock data
                    mock_data = self._generate_mock_data()
                    
                    # Schedule UI update on main thread
                    def update_ui():
                        self._on_data_loaded(mock_data)
                    
                    self.after(0, update_ui)
                    
                except Exception as e:
                    self.logger.error(f"Error loading initial data: {e}")
                    
                    def hide_loading():
                        self._show_loading(False)
                    
                    self.after(0, hide_loading)
            
            threading.Thread(target=load_data, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error initiating data load: {e}")
    
    def _on_data_loaded(self, data: List[TemperatureDataPoint]):
        """Handle data loading completion."""
        try:
            self.current_data = data
            self._update_chart()
            self._show_loading(False)
            
            if self.on_data_updated:
                self.on_data_updated(data)
                
        except Exception as e:
            self.logger.error(f"Error handling loaded data: {e}")
    
    def _show_loading(self, show: bool):
        """Show or hide loading overlay."""
        try:
            if show:
                if not self.loading_overlay:
                    self.ui_components.show_loading_overlay()
            else:
                if self.loading_overlay:
                    self.ui_components.hide_loading_overlay()
                    
        except Exception as e:
            self.logger.error(f"Error toggling loading state: {e}")
    
    def _update_chart(self):
        """Update chart with current data and configuration."""
        if not self.current_data or not self.ax:
            return
        
        try:
            # Clear previous plot
            self.ax.clear()
            
            # Reapply styling after clear
            self._apply_chart_styling()
            
            # Prepare data
            timestamps = [point.timestamp for point in self.current_data]
            temperatures = [point.temperature for point in self.current_data]
            feels_like = [point.feels_like for point in self.current_data]
            
            # Plot based on chart type
            if self.chart_config.chart_type == ChartType.LINE:
                self._plot_line_chart(timestamps, temperatures, feels_like)
            elif self.chart_config.chart_type == ChartType.AREA:
                self._plot_area_chart(timestamps, temperatures, feels_like)
            elif self.chart_config.chart_type == ChartType.BAR:
                self._plot_bar_chart(timestamps, temperatures)
            elif self.chart_config.chart_type == ChartType.SCATTER:
                self._plot_scatter_chart(timestamps, temperatures)
            
            # Add annotations if enabled
            if self.chart_config.show_annotations:
                self._add_annotations()
            
            # Add trend line if enabled
            if self.chart_config.show_trends:
                self._add_trend_line(timestamps, temperatures)
            
            # Add weather events
            self._add_weather_events()
            
            # Add city comparisons
            self._add_city_comparisons()
            
            # Format axes
            self._format_axes(timestamps)
            
            # Update canvas
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error updating chart: {e}")
    
    def _apply_chart_styling(self):
        """Apply glassmorphic styling to chart."""
        self.ax.set_facecolor('none')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#FFFFFF40')
        self.ax.spines['left'].set_color('#FFFFFF40')
        self.ax.tick_params(colors='#FFFFFF80', which='both')
        self.ax.grid(True, alpha=0.2, color='#FFFFFF', linestyle='-', linewidth=0.5)
    
    def _plot_line_chart(self, timestamps, temperatures, feels_like):
        """Plot line chart."""
        self.ax.plot(timestamps, temperatures, 
                    color='#00D4FF', linewidth=2.5, label='Temperature', alpha=0.9)
        
        if self.chart_config.show_feels_like:
            self.ax.plot(timestamps, feels_like, 
                        color='#FF6B6B', linewidth=2, label='Feels Like', alpha=0.7, linestyle='--')
    
    def _plot_area_chart(self, timestamps, temperatures, feels_like):
        """Plot area chart."""
        self.ax.fill_between(timestamps, temperatures, alpha=0.6, color='#00D4FF', label='Temperature')
        
        if self.chart_config.show_feels_like:
            self.ax.fill_between(timestamps, feels_like, alpha=0.4, color='#FF6B6B', label='Feels Like')
    
    def _plot_bar_chart(self, timestamps, temperatures):
        """Plot bar chart."""
        self.ax.bar(timestamps, temperatures, color='#00D4FF', alpha=0.7, label='Temperature')
    
    def _plot_scatter_chart(self, timestamps, temperatures):
        """Plot scatter chart."""
        self.ax.scatter(timestamps, temperatures, color='#00D4FF', alpha=0.8, s=50, label='Temperature')
    
    def _add_annotations(self):
        """Add temperature annotations to chart."""
        try:
            if not self.current_data:
                return
            
            # Find min and max points
            min_point = min(self.current_data, key=lambda p: p.temperature)
            max_point = max(self.current_data, key=lambda p: p.temperature)
            
            # Annotate min point
            self.ax.annotate(f'Min: {min_point.temperature:.1f}°C',
                           xy=(min_point.timestamp, min_point.temperature),
                           xytext=(10, 10), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='#FF6B6B', alpha=0.7),
                           arrowprops=dict(arrowstyle='->', color='#FF6B6B'),
                           color='white', fontsize=9)
            
            # Annotate max point
            self.ax.annotate(f'Max: {max_point.temperature:.1f}°C',
                           xy=(max_point.timestamp, max_point.temperature),
                           xytext=(10, -20), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='#00D4FF', alpha=0.7),
                           arrowprops=dict(arrowstyle='->', color='#00D4FF'),
                           color='white', fontsize=9)
            
        except Exception as e:
            self.logger.error(f"Error adding annotations: {e}")
    
    def _add_trend_line(self, timestamps, temperatures):
        """Add trend line to chart."""
        try:
            if len(timestamps) < 2:
                return
            
            # Convert timestamps to numeric values for regression
            x_numeric = mdates.date2num(timestamps)
            
            # Calculate linear regression
            coeffs = np.polyfit(x_numeric, temperatures, 1)
            trend_line = np.poly1d(coeffs)
            
            # Plot trend line
            self.ax.plot(timestamps, trend_line(x_numeric),
                        color='#FFD700', linewidth=2, linestyle=':', 
                        label='Trend', alpha=0.8)
            
        except Exception as e:
            self.logger.error(f"Error adding trend line: {e}")
    
    def _add_weather_events(self):
        """Add weather event markers to chart."""
        try:
            for event in self.weather_events:
                if event.is_visible:
                    self.ax.axvline(x=event.timestamp, color=event.color, 
                                  linestyle='--', alpha=0.7, linewidth=2)
                    
                    # Add event label
                    self.ax.text(event.timestamp, self.ax.get_ylim()[1] * 0.9,
                               event.description, rotation=90, 
                               verticalalignment='top', color=event.color,
                               fontsize=8, alpha=0.8)
        except Exception as e:
            self.logger.error(f"Error adding weather events: {e}")
    
    def _add_city_comparisons(self):
        """Add city comparison data to chart."""
        try:
            for comparison in self.city_comparisons:
                if comparison.is_visible and comparison.data:
                    timestamps = [point.timestamp for point in comparison.data]
                    temperatures = [point.temperature for point in comparison.data]
                    
                    self.ax.plot(timestamps, temperatures,
                               color=comparison.color, linewidth=2,
                               label=comparison.city_name, alpha=0.7,
                               linestyle='-.')
        except Exception as e:
            self.logger.error(f"Error adding city comparisons: {e}")
    
    def _format_axes(self, timestamps):
        """Format chart axes."""
        try:
            # Set labels
            self.ax.set_xlabel('Time', color='#FFFFFF80', fontsize=12)
            self.ax.set_ylabel('Temperature (°C)', color='#FFFFFF80', fontsize=12)
            
            # Format x-axis based on time range
            if timestamps:
                time_span = max(timestamps) - min(timestamps)
                
                if time_span.days > 7:
                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                    self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                elif time_span.days > 1:
                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
                    self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
                else:
                    self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                    self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            
            # Rotate x-axis labels
            plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Add legend if there are multiple series
            handles, labels = self.ax.get_legend_handles_labels()
            if len(handles) > 1:
                self.ax.legend(loc='upper left', framealpha=0.8, 
                             facecolor='#2A2A2A', edgecolor='#404040')
            
        except Exception as e:
            self.logger.error(f"Error formatting axes: {e}")
    
    def _generate_mock_data(self) -> List[TemperatureDataPoint]:
        """Generate mock temperature data for demonstration."""
        try:
            data = []
            base_time = datetime.now() - timedelta(hours=24)
            
            for i in range(48):  # 48 hours of data
                timestamp = base_time + timedelta(hours=i)
                
                # Generate realistic temperature variation
                base_temp = 20 + 10 * np.sin(i * np.pi / 12)  # Daily cycle
                noise = np.random.normal(0, 2)  # Random variation
                temperature = base_temp + noise
                
                feels_like = temperature + np.random.normal(0, 1)
                humidity = max(30, min(90, 60 + np.random.normal(0, 15)))
                wind_speed = max(0, np.random.exponential(3))
                pressure = 1013 + np.random.normal(0, 10)
                
                conditions = ['Clear', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Rain']
                condition = np.random.choice(conditions, p=[0.3, 0.3, 0.2, 0.15, 0.05])
                
                point = TemperatureDataPoint(
                    timestamp=timestamp,
                    temperature=round(temperature, 1),
                    feels_like=round(feels_like, 1),
                    humidity=round(humidity, 1),
                    wind_speed=round(wind_speed, 1),
                    pressure=round(pressure, 1),
                    condition=condition,
                    location="Demo City"
                )
                
                data.append(point)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error generating mock data: {e}")
            return []
    
    # Public API methods
    
    def update_data(self, data: List[TemperatureDataPoint]):
        """Update chart with new temperature data."""
        try:
            self.current_data = data
            self._update_chart()
            
            if self.on_data_updated:
                self.on_data_updated(data)
                
        except Exception as e:
            self.logger.error(f"Error updating data: {e}")
    
    def set_chart_config(self, config: ChartConfig):
        """Update chart configuration."""
        try:
            self.chart_config = config
            self._update_chart()
        except Exception as e:
            self.logger.error(f"Error setting chart config: {e}")
    
    def refresh_chart(self):
        """Refresh chart data and display."""
        try:
            self._show_loading(True)
            
            def refresh_data():
                try:
                    # In a real implementation, this would fetch fresh data
                    # For now, regenerate mock data
                    new_data = self._generate_mock_data()
                    
                    def update_ui():
                        self._on_data_loaded(new_data)
                    
                    self.after(0, update_ui)
                except Exception as e:
                    self.logger.error(f"Error refreshing data: {e}")
                    
                    def hide_loading():
                        self._show_loading(False)
                    
                    self.after(0, hide_loading)
            
            threading.Thread(target=refresh_data, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error refreshing chart: {e}")
    
    def export_chart(self, export_path: str, settings: Optional[ExportSettings] = None) -> bool:
        """Export chart to file."""
        try:
            success = self.analytics_engine.export_chart(export_path, settings)
            
            if success and self.on_export_completed:
                self.on_export_completed(export_path)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error exporting chart: {e}")
            return False
    
    def get_analytics(self) -> Optional[ChartAnalytics]:
        """Get analytics for current data."""
        try:
            if not self.current_data:
                return None
            
            return self.analytics_engine.calculate_analytics(self.current_data)
            
        except Exception as e:
            self.logger.error(f"Error getting analytics: {e}")
            return None
    
    def add_weather_event(self, event: WeatherEvent):
        """Add weather event marker to chart."""
        try:
            self.weather_events.append(event)
            self._update_chart()
        except Exception as e:
            self.logger.error(f"Error adding weather event: {e}")
    
    def add_city_comparison(self, comparison: CityComparison):
        """Add city comparison data to chart."""
        try:
            self.city_comparisons.append(comparison)
            self._update_chart()
        except Exception as e:
            self.logger.error(f"Error adding city comparison: {e}")
    
    def _show_export_dialog(self):
        """Show export configuration dialog."""
        self.analytics_engine.show_export_dialog()
    
    def _show_help_dialog(self):
        """Show help dialog with keyboard shortcuts."""
        try:
            help_dialog = ctk.CTkToplevel(self)
            help_dialog.title("Chart Help")
            help_dialog.geometry("500x400")
            help_dialog.configure(fg_color=("#1a1a1a", "#1a1a1a"))
            
            # Center dialog
            help_dialog.update_idletasks()
            x = (help_dialog.winfo_screenwidth() // 2) - 250
            y = (help_dialog.winfo_screenheight() // 2) - 200
            help_dialog.geometry(f"500x400+{x}+{y}")
            
            # Content
            content_frame = ctk.CTkScrollableFrame(
                help_dialog,
                fg_color=("#F8F8F8", "#2A2A2A"),
                corner_radius=15
            )
            content_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title_label = ctk.CTkLabel(
                content_frame,
                text="🔧 Chart Controls & Shortcuts",
                font=("Segoe UI", 18, "bold"),
                text_color=("#FFFFFF", "#E0E0E0")
            )
            title_label.pack(pady=(20, 30))
            
            # Help content
            help_text = """⌨️ KEYBOARD SHORTCUTS:
• R - Refresh chart data
• E - Export chart
• H - Show this help dialog
• ESC - Reset zoom
• Arrow Keys - Pan chart
• + / - - Zoom in/out

🖱️ MOUSE CONTROLS:
• Left Click - Select data point
• Right Click - Context menu
• Scroll - Zoom in/out
• Drag - Select area to zoom

🎛️ CHART CONTROLS:
• Time Range - Select data period
• Chart Type - Change visualization
• Annotations - Toggle min/max markers
• Trends - Show/hide trend line
• Export - Save chart and data
• Refresh - Update with latest data

📊 FEATURES:
• Interactive tooltips on hover
• Multi-city comparisons
• Weather event markers
• Analytics and statistics
• Multiple export formats"""
            
            help_label = ctk.CTkLabel(
                content_frame,
                text=help_text,
                font=("Segoe UI", 12),
                text_color=("#CCCCCC", "#AAAAAA"),
                justify="left"
            )
            help_label.pack(pady=10, padx=20)
            
            # Close button
            close_button = ctk.CTkButton(
                content_frame,
                text="Close",
                command=help_dialog.destroy,
                width=100,
                height=35
            )
            close_button.pack(pady=(20, 20))
            
        except Exception as e:
            self.logger.error(f"Error showing help dialog: {e}")