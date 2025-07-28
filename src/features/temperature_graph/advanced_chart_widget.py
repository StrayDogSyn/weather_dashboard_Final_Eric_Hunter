#!/usr/bin/env python3
"""
Advanced Interactive Temperature Chart Widget

A comprehensive glassmorphic temperature analytics component featuring:
- Interactive matplotlib charts with hover tooltips
- Multiple time range analysis with smooth transitions
- Chart type switching with glassmorphic controls
- Multi-city comparison with color-coded trend lines
- Weather event annotations and statistical indicators
- Professional export functionality

Author: Eric Hunter (Cortana Builder Agent)
Version: 3.0.0 (TRAE 2.0 Phase 3)
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Callable
import threading
import json
from pathlib import Path
from dataclasses import dataclass, asdict
import logging
from PIL import Image, ImageDraw, ImageFilter
import io
import base64

from .models import (
    ChartType, TimeRange, ChartConfig, TemperatureDataPoint, 
    ChartAnalytics, ExportSettings
)
from .chart_controller import ChartController
from ...ui.components.base_components import GlassFrame, GlassButton
from ...utils.logger import LoggerMixin


@dataclass
class WeatherEvent:
    """Weather event annotation data."""
    timestamp: datetime
    event_type: str  # 'extreme_heat', 'freezing', 'rain', 'storm'
    temperature: float
    description: str
    icon: str  # emoji
    severity: int  # 1-5 scale


@dataclass
class CityComparison:
    """Multi-city comparison data."""
    city_name: str
    data_points: List[TemperatureDataPoint]
    color: str
    line_style: str
    marker_style: str
    visible: bool = True


class GlassmorphicTooltip(ctk.CTkToplevel):
    """Glassmorphic tooltip window for chart interactions."""
    
    def __init__(self, parent, x: int, y: int, content: str):
        super().__init__(parent)
        
        # Configure window
        self.withdraw()  # Hide initially
        self.overrideredirect(True)  # Remove window decorations
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.95)
        
        # Glassmorphic styling
        self.configure(fg_color=("#FFFFFF33", "#000000AA"))
        
        # Content frame
        content_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=12,
            border_width=1,
            border_color=("#FFFFFF44", "#FFFFFF22")
        )
        content_frame.pack(padx=8, pady=8)
        
        # Content label
        self.content_label = ctk.CTkLabel(
            content_frame,
            text=content,
            font=("Segoe UI", 11),
            text_color=("#FFFFFF", "#E0E0E0"),
            justify="left"
        )
        self.content_label.pack(padx=12, pady=8)
        
        # Position tooltip
        self.geometry(f"+{x}+{y}")
        
        # Auto-hide timer
        self.after(3000, self.hide_tooltip)
    
    def update_content(self, content: str):
        """Update tooltip content."""
        self.content_label.configure(text=content)
    
    def show_tooltip(self):
        """Show tooltip with fade-in effect."""
        self.deiconify()
        self.lift()
    
    def hide_tooltip(self):
        """Hide tooltip."""
        try:
            self.destroy()
        except:
            pass


class AdvancedChartWidget(GlassFrame, LoggerMixin):
    """Advanced interactive temperature chart with glassmorphic design."""
    
    def __init__(self, parent, chart_controller: ChartController, **kwargs):
        super().__init__(parent, **kwargs)
        self.chart_controller = chart_controller
        self.config = chart_controller.config
        
        # Chart state
        self.current_data: List[TemperatureDataPoint] = []
        self.city_comparisons: Dict[str, CityComparison] = {}
        self.weather_events: List[WeatherEvent] = []
        self.analytics: Optional[ChartAnalytics] = None
        self.animation: Optional[FuncAnimation] = None
        self.tooltip: Optional[GlassmorphicTooltip] = None
        
        # Interactive state
        self.is_loading = False
        self.selected_range: Optional[Tuple[datetime, datetime]] = None
        self.hover_point: Optional[Tuple[float, float]] = None
        
        # Color palette for multi-city comparison
        self.city_colors = [
            '#4A90E2', '#50C878', '#FF6B6B', '#FFD93D', 
            '#9B59B6', '#E67E22', '#1ABC9C', '#E74C3C'
        ]
        self.color_index = 0
        
        self._setup_ui()
        self._setup_chart()
        self._setup_event_handlers()
        
        # Load initial data
        self.refresh_chart()
    
    def _setup_ui(self):
        """Setup glassmorphic UI components."""
        # Configure main frame
        self.configure(
            fg_color=("#FFFFFF11", "#000000AA"),
            corner_radius=20,
            border_width=2,
            border_color=("#FFFFFF33", "#FFFFFF11")
        )
        
        # Header frame with controls
        self.header_frame = GlassmorphicFrame(
            self,
            height=80,
            fg_color=("#FFFFFF08", "#000000CC"),
            corner_radius=15
        )
        self.header_frame.pack(fill="x", padx=15, pady=(15, 10))
        self.header_frame.pack_propagate(False)
        
        # Left controls
        left_controls = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        left_controls.pack(side="left", fill="y", padx=15, pady=10)
        
        # Time range selector
        ctk.CTkLabel(
            left_controls,
            text="Time Range:",
            font=("Segoe UI", 12, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        ).pack(side="left", padx=(0, 8))
        
        self.time_range_menu = ctk.CTkOptionMenu(
            left_controls,
            values=["24h", "7d", "30d", "90d", "custom"],
            command=self._on_time_range_change,
            width=100,
            height=32,
            corner_radius=8,
            fg_color=("#FFFFFF22", "#333333"),
            button_color=("#FFFFFF33", "#444444"),
            button_hover_color=("#FFFFFF44", "#555555"),
            dropdown_fg_color=("#FFFFFF22", "#333333")
        )
        self.time_range_menu.pack(side="left", padx=(0, 15))
        self.time_range_menu.set("7d")
        
        # Chart type selector
        ctk.CTkLabel(
            left_controls,
            text="Chart Type:",
            font=("Segoe UI", 12, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        ).pack(side="left", padx=(0, 8))
        
        self.chart_type_menu = ctk.CTkOptionMenu(
            left_controls,
            values=["Line", "Area", "Bar", "Scatter", "Candlestick"],
            command=self._on_chart_type_change,
            width=120,
            height=32,
            corner_radius=8,
            fg_color=("#FFFFFF22", "#333333"),
            button_color=("#FFFFFF33", "#444444"),
            button_hover_color=("#FFFFFF44", "#555555"),
            dropdown_fg_color=("#FFFFFF22", "#333333")
        )
        self.chart_type_menu.pack(side="left", padx=(0, 15))
        self.chart_type_menu.set("Line")
        
        # Right controls
        right_controls = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_controls.pack(side="right", fill="y", padx=15, pady=10)
        
        # Toggle switches
        self.annotations_switch = ctk.CTkSwitch(
            right_controls,
            text="Annotations",
            command=self._toggle_annotations,
            width=50,
            height=24,
            switch_width=40,
            switch_height=20,
            corner_radius=10,
            fg_color=("#FFFFFF22", "#333333"),
            progress_color=("#4A90E2", "#4A90E2"),
            button_color=("#FFFFFF", "#CCCCCC"),
            button_hover_color=("#F0F0F0", "#DDDDDD")
        )
        self.annotations_switch.pack(side="left", padx=(0, 10))
        self.annotations_switch.select()
        
        self.trends_switch = ctk.CTkSwitch(
            right_controls,
            text="Trends",
            command=self._toggle_trends,
            width=50,
            height=24,
            switch_width=40,
            switch_height=20,
            corner_radius=10,
            fg_color=("#FFFFFF22", "#333333"),
            progress_color=("#50C878", "#50C878"),
            button_color=("#FFFFFF", "#CCCCCC"),
            button_hover_color=("#F0F0F0", "#DDDDDD")
        )
        self.trends_switch.pack(side="left", padx=(0, 10))
        self.trends_switch.select()
        
        # Export button
        self.export_button = GlassmorphicButton(
            right_controls,
            text="📊 Export",
            command=self._show_export_dialog,
            width=80,
            height=32,
            corner_radius=8
        )
        self.export_button.pack(side="left", padx=(0, 10))
        
        # Refresh button
        self.refresh_button = GlassmorphicButton(
            right_controls,
            text="🔄 Refresh",
            command=self.refresh_chart,
            width=80,
            height=32,
            corner_radius=8
        )
        self.refresh_button.pack(side="left")
        
        # Chart container
        self.chart_container = GlassmorphicFrame(
            self,
            fg_color=("#FFFFFF05", "#000000DD"),
            corner_radius=15,
            border_width=1,
            border_color=("#FFFFFF22", "#FFFFFF11")
        )
        self.chart_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Loading overlay
        self.loading_overlay = GlassmorphicFrame(
            self.chart_container,
            fg_color=("#000000AA", "#000000CC"),
            corner_radius=15
        )
        
        self.loading_label = ctk.CTkLabel(
            self.loading_overlay,
            text="🔄 Loading chart data...",
            font=("Segoe UI", 16, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        )
        self.loading_label.pack(expand=True)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.loading_overlay,
            width=200,
            height=8,
            corner_radius=4,
            fg_color=("#FFFFFF22", "#333333"),
            progress_color=("#4A90E2", "#4A90E2")
        )
        self.progress_bar.pack(pady=(10, 0))
        self.progress_bar.set(0)
    
    def _setup_chart(self):
        """Setup matplotlib chart with glassmorphic theme."""
        # Configure matplotlib style
        plt.style.use('dark_background')
        
        # Create figure with glassmorphic styling
        self.fig, self.ax = plt.subplots(
            figsize=(12, 6),
            facecolor='#1a1a1a',
            edgecolor='none'
        )
        
        # Configure axes
        self.ax.set_facecolor('#2b2b2b')
        self.ax.grid(True, alpha=0.3, color='#444444', linewidth=0.5)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#666666')
        self.ax.spines['left'].set_color('#666666')
        
        # Configure ticks and labels
        self.ax.tick_params(colors='#CCCCCC', labelsize=10)
        self.ax.set_xlabel('Time', color='#CCCCCC', fontsize=12)
        self.ax.set_ylabel('Temperature (°C)', color='#CCCCCC', fontsize=12)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure canvas background
        self.canvas.get_tk_widget().configure(bg='#1a1a1a', highlightthickness=0)
        
        # Create custom toolbar
        self._create_custom_toolbar()
    
    def _create_custom_toolbar(self):
        """Create custom glassmorphic navigation toolbar."""
        toolbar_frame = GlassmorphicFrame(
            self.chart_container,
            height=40,
            fg_color=("#FFFFFF08", "#000000CC"),
            corner_radius=10
        )
        toolbar_frame.pack(fill="x", padx=10, pady=(0, 10))
        toolbar_frame.pack_propagate(False)
        
        # Zoom controls
        zoom_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        zoom_frame.pack(side="left", fill="y", padx=10, pady=5)
        
        self.zoom_in_btn = GlassmorphicButton(
            zoom_frame,
            text="🔍+",
            command=self._zoom_in,
            width=40,
            height=30,
            corner_radius=6
        )
        self.zoom_in_btn.pack(side="left", padx=(0, 5))
        
        self.zoom_out_btn = GlassmorphicButton(
            zoom_frame,
            text="🔍-",
            command=self._zoom_out,
            width=40,
            height=30,
            corner_radius=6
        )
        self.zoom_out_btn.pack(side="left", padx=(0, 5))
        
        self.reset_zoom_btn = GlassmorphicButton(
            zoom_frame,
            text="🏠",
            command=self._reset_zoom,
            width=40,
            height=30,
            corner_radius=6
        )
        self.reset_zoom_btn.pack(side="left")
        
        # Analytics display
        analytics_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        analytics_frame.pack(side="right", fill="y", padx=10, pady=5)
        
        self.analytics_label = ctk.CTkLabel(
            analytics_frame,
            text="Analytics: Loading...",
            font=("Segoe UI", 10),
            text_color=("#CCCCCC", "#AAAAAA")
        )
        self.analytics_label.pack(side="right")
    
    def _setup_event_handlers(self):
        """Setup interactive event handlers."""
        # Mouse events
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.canvas.mpl_connect('button_press_event', self._on_mouse_click)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('scroll_event', self._on_mouse_scroll)
        
        # Keyboard events
        self.canvas.mpl_connect('key_press_event', self._on_key_press)
        
        # Focus events
        self.canvas.get_tk_widget().bind('<Enter>', self._on_canvas_enter)
        self.canvas.get_tk_widget().bind('<Leave>', self._on_canvas_leave)
    
    def _on_time_range_change(self, value: str):
        """Handle time range selection change."""
        time_range_map = {
            "24h": TimeRange.LAST_24_HOURS,
            "7d": TimeRange.LAST_7_DAYS,
            "30d": TimeRange.LAST_30_DAYS,
            "90d": TimeRange.LAST_90_DAYS,
            "custom": TimeRange.CUSTOM
        }
        
        if value == "custom":
            self._show_custom_range_dialog()
        else:
            self.config.time_range = time_range_map[value]
            self.refresh_chart()
    
    def _on_chart_type_change(self, value: str):
        """Handle chart type selection change."""
        chart_type_map = {
            "Line": ChartType.LINE,
            "Area": ChartType.AREA,
            "Bar": ChartType.BAR,
            "Scatter": ChartType.SCATTER,
            "Candlestick": ChartType.CANDLESTICK
        }
        
        self.config.chart_type = chart_type_map[value]
        self._update_chart_display()
    
    def _toggle_annotations(self):
        """Toggle weather event annotations."""
        self.config.show_annotations = self.annotations_switch.get()
        self._update_chart_display()
    
    def _toggle_trends(self):
        """Toggle trend analysis display."""
        self.config.show_legend = self.trends_switch.get()
        self._update_chart_display()
    
    def _on_mouse_move(self, event):
        """Handle mouse movement for hover tooltips."""
        if event.inaxes != self.ax or not self.current_data:
            if self.tooltip:
                self.tooltip.hide_tooltip()
                self.tooltip = None
            return
        
        # Find nearest data point
        nearest_point = self._find_nearest_point(event.xdata, event.ydata)
        if nearest_point:
            self._show_hover_tooltip(event, nearest_point)
    
    def _on_mouse_click(self, event):
        """Handle mouse clicks for data point selection."""
        if event.inaxes != self.ax or not self.current_data:
            return
        
        if event.button == 1:  # Left click
            nearest_point = self._find_nearest_point(event.xdata, event.ydata)
            if nearest_point:
                self._show_data_point_popup(nearest_point)
        elif event.button == 3:  # Right click
            self._show_context_menu(event)
    
    def _on_mouse_release(self, event):
        """Handle mouse release for range selection."""
        pass  # Implement range selection logic
    
    def _on_mouse_scroll(self, event):
        """Handle mouse scroll for zooming."""
        if event.inaxes != self.ax:
            return
        
        scale_factor = 1.1 if event.step > 0 else 1/1.1
        self._zoom_at_point(event.xdata, event.ydata, scale_factor)
    
    def _on_key_press(self, event):
        """Handle keyboard shortcuts."""
        if event.key == 'r':
            self.refresh_chart()
        elif event.key == 'e':
            self._show_export_dialog()
        elif event.key == 'h':
            self._show_help_dialog()
        elif event.key == 'escape':
            self._reset_zoom()
    
    def _on_canvas_enter(self, event):
        """Handle mouse entering canvas."""
        self.canvas.get_tk_widget().focus_set()
    
    def _on_canvas_leave(self, event):
        """Handle mouse leaving canvas."""
        if self.tooltip:
            self.tooltip.hide_tooltip()
            self.tooltip = None
    
    def refresh_chart(self):
        """Refresh chart data and display."""
        if self.is_loading:
            return
        
        self.is_loading = True
        self._show_loading()
        
        # Run data loading in background thread
        thread = threading.Thread(target=self._load_chart_data)
        thread.daemon = True
        thread.start()
    
    def _load_chart_data(self):
        """Load chart data in background thread."""
        try:
            # Update progress
            self.after(0, lambda: self.progress_bar.set(0.2))
            
            # Fetch temperature data
            self.current_data = self.chart_controller.get_temperature_data(
                self.config.time_range
            )
            
            self.after(0, lambda: self.progress_bar.set(0.5))
            
            # Calculate analytics
            self.analytics = self.chart_controller.calculate_analytics(self.current_data)
            
            self.after(0, lambda: self.progress_bar.set(0.7))
            
            # Detect weather events
            self.weather_events = self._detect_weather_events(self.current_data)
            
            self.after(0, lambda: self.progress_bar.set(0.9))
            
            # Update UI on main thread
            self.after(0, self._update_chart_display)
            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(100, self._hide_loading)
            
        except Exception as e:
            self.logger.error(f"Error loading chart data: {e}")
            self.after(0, lambda: self._show_error(f"Failed to load data: {str(e)}"))
        finally:
            self.is_loading = False
    
    def _update_chart_display(self):
        """Update chart display with current data."""
        if not self.current_data:
            return
        
        # Clear previous plot
        self.ax.clear()
        
        # Reconfigure axes after clearing
        self.ax.set_facecolor('#2b2b2b')
        self.ax.grid(True, alpha=0.3, color='#444444', linewidth=0.5)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#666666')
        self.ax.spines['left'].set_color('#666666')
        self.ax.tick_params(colors='#CCCCCC', labelsize=10)
        
        # Process data for chart type
        chart_data = self.chart_controller.process_data_for_chart(
            self.current_data, self.config.chart_type
        )
        
        # Plot based on chart type
        if self.config.chart_type == ChartType.LINE:
            self._plot_line_chart(chart_data)
        elif self.config.chart_type == ChartType.AREA:
            self._plot_area_chart(chart_data)
        elif self.config.chart_type == ChartType.BAR:
            self._plot_bar_chart(chart_data)
        elif self.config.chart_type == ChartType.SCATTER:
            self._plot_scatter_chart(chart_data)
        elif self.config.chart_type == ChartType.CANDLESTICK:
            self._plot_candlestick_chart(chart_data)
        
        # Add weather event annotations
        if self.config.show_annotations:
            self._add_weather_annotations()
        
        # Add trend analysis
        if self.config.show_legend and self.analytics:
            self._add_trend_analysis()
        
        # Add multi-city comparisons
        self._plot_city_comparisons()
        
        # Format axes
        self._format_chart_axes()
        
        # Update analytics display
        self._update_analytics_display()
        
        # Refresh canvas
        self.canvas.draw()
    
    def _plot_line_chart(self, chart_data: Dict[str, Any]):
        """Plot line chart with gradient effects."""
        x_data = chart_data['x']
        y_data = chart_data['y']
        
        # Main temperature line
        line = self.ax.plot(
            x_data, y_data,
            color='#4A90E2',
            linewidth=3,
            marker='o',
            markersize=4,
            markerfacecolor='#4A90E2',
            markeredgecolor='#FFFFFF',
            markeredgewidth=1,
            alpha=0.9,
            label='Temperature'
        )[0]
        
        # Add feels-like line if available
        feels_like = chart_data['metadata'].get('feels_like')
        if feels_like and any(f is not None for f in feels_like):
            self.ax.plot(
                x_data, feels_like,
                color='#FF6B6B',
                linewidth=2,
                linestyle='--',
                alpha=0.7,
                label='Feels Like'
            )
    
    def _plot_area_chart(self, chart_data: Dict[str, Any]):
        """Plot area chart with gradient fill."""
        x_data = chart_data['x']
        y_data = chart_data['y']
        
        # Create gradient fill
        self.ax.fill_between(
            x_data, y_data,
            alpha=0.3,
            color='#4A90E2',
            label='Temperature Range'
        )
        
        # Add border line
        self.ax.plot(
            x_data, y_data,
            color='#4A90E2',
            linewidth=2,
            alpha=0.9
        )
    
    def _plot_bar_chart(self, chart_data: Dict[str, Any]):
        """Plot bar chart with glassmorphic styling."""
        x_data = chart_data['x']
        y_data = chart_data['y']
        
        # Calculate bar width based on data density
        if len(x_data) > 1:
            time_diff = (x_data[1] - x_data[0]).total_seconds() / 3600  # hours
            bar_width = time_diff * 0.8 / 24  # Fraction of day
        else:
            bar_width = 0.8
        
        bars = self.ax.bar(
            x_data, y_data,
            width=bar_width,
            color='#4A90E2',
            alpha=0.7,
            edgecolor='#FFFFFF',
            linewidth=1
        )
        
        # Add gradient effect to bars
        for bar in bars:
            bar.set_facecolor('#4A90E2')
            bar.set_alpha(0.7)
    
    def _plot_scatter_chart(self, chart_data: Dict[str, Any]):
        """Plot scatter chart with size variation."""
        x_data = chart_data['x']
        y_data = chart_data['y']
        
        # Vary point size based on humidity if available
        humidity = chart_data['metadata'].get('humidity', [])
        if humidity and any(h is not None for h in humidity):
            sizes = [max(20, h or 20) for h in humidity]
        else:
            sizes = [40] * len(x_data)
        
        scatter = self.ax.scatter(
            x_data, y_data,
            s=sizes,
            c=y_data,
            cmap='coolwarm',
            alpha=0.7,
            edgecolors='#FFFFFF',
            linewidth=1
        )
        
        # Add colorbar
        cbar = self.fig.colorbar(scatter, ax=self.ax, shrink=0.8)
        cbar.set_label('Temperature (°C)', color='#CCCCCC')
        cbar.ax.tick_params(colors='#CCCCCC')
    
    def _plot_candlestick_chart(self, chart_data: Dict[str, Any]):
        """Plot candlestick chart for temperature ranges."""
        # This would require OHLC data - simplified implementation
        x_data = chart_data['x']
        y_data = chart_data['y']
        feels_like = chart_data['metadata'].get('feels_like', y_data)
        
        for i, (x, temp, feels) in enumerate(zip(x_data, y_data, feels_like)):
            if feels is None:
                feels = temp
            
            high = max(temp, feels)
            low = min(temp, feels)
            
            # Draw candlestick
            color = '#50C878' if feels >= temp else '#FF6B6B'
            
            # Wick
            self.ax.plot([x, x], [low, high], color=color, linewidth=1, alpha=0.7)
            
            # Body
            body_height = abs(feels - temp)
            body_bottom = min(temp, feels)
            
            rect = plt.Rectangle(
                (x - timedelta(hours=0.4), body_bottom),
                timedelta(hours=0.8), body_height,
                facecolor=color, alpha=0.7, edgecolor='#FFFFFF', linewidth=0.5
            )
            self.ax.add_patch(rect)
    
    def _add_weather_annotations(self):
        """Add weather event annotations to chart."""
        for event in self.weather_events:
            self.ax.annotate(
                f"{event.icon} {event.description}",
                xy=(event.timestamp, event.temperature),
                xytext=(10, 20),
                textcoords='offset points',
                bbox=dict(
                    boxstyle='round,pad=0.3',
                    facecolor='#FFFFFF22',
                    edgecolor='#FFFFFF44',
                    alpha=0.8
                ),
                arrowprops=dict(
                    arrowstyle='->',
                    connectionstyle='arc3,rad=0.1',
                    color='#FFFFFF',
                    alpha=0.7
                ),
                fontsize=9,
                color='#FFFFFF'
            )
    
    def _add_trend_analysis(self):
        """Add trend analysis indicators."""
        if not self.analytics or len(self.current_data) < 2:
            return
        
        # Add trend arrow
        trend_color = {
            'rising': '#50C878',
            'falling': '#FF6B6B',
            'stable': '#FFD93D'
        }.get(self.analytics.temperature_trend, '#CCCCCC')
        
        trend_symbol = {
            'rising': '↗️',
            'falling': '↘️',
            'stable': '→'
        }.get(self.analytics.temperature_trend, '→')
        
        # Add trend indicator to chart
        self.ax.text(
            0.02, 0.98,
            f"{trend_symbol} Trend: {self.analytics.temperature_trend.title()}",
            transform=self.ax.transAxes,
            fontsize=12,
            color=trend_color,
            bbox=dict(
                boxstyle='round,pad=0.3',
                facecolor='#00000088',
                edgecolor=trend_color,
                alpha=0.8
            ),
            verticalalignment='top'
        )
        
        # Add statistical info
        stats_text = (
            f"Avg: {self.analytics.avg_temperature:.1f}°C\n"
            f"Range: {self.analytics.min_temperature:.1f}°C - {self.analytics.max_temperature:.1f}°C"
        )
        
        self.ax.text(
            0.02, 0.85,
            stats_text,
            transform=self.ax.transAxes,
            fontsize=10,
            color='#CCCCCC',
            bbox=dict(
                boxstyle='round,pad=0.3',
                facecolor='#00000088',
                edgecolor='#FFFFFF44',
                alpha=0.8
            ),
            verticalalignment='top'
        )
    
    def _plot_city_comparisons(self):
        """Plot multi-city comparison lines."""
        for city_name, comparison in self.city_comparisons.items():
            if not comparison.visible or not comparison.data_points:
                continue
            
            x_data = [point.timestamp for point in comparison.data_points]
            y_data = [point.temperature for point in comparison.data_points]
            
            self.ax.plot(
                x_data, y_data,
                color=comparison.color,
                linestyle=comparison.line_style,
                marker=comparison.marker_style,
                linewidth=2,
                markersize=3,
                alpha=0.8,
                label=city_name
            )
    
    def _format_chart_axes(self):
        """Format chart axes with proper labels and styling."""
        # Set title
        title = f"Temperature Analysis - {self.config.time_range.value.upper()}"
        self.ax.set_title(title, color='#FFFFFF', fontsize=14, fontweight='bold', pad=20)
        
        # Format x-axis (time)
        if self.current_data:
            time_span = (self.current_data[-1].timestamp - self.current_data[0].timestamp).days
            
            if time_span <= 1:
                # Hourly format for 24h view
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
            elif time_span <= 7:
                # Daily format for weekly view
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                self.ax.xaxis.set_major_locator(mdates.DayLocator())
            else:
                # Weekly format for monthly view
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                self.ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        
        # Rotate x-axis labels
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Set axis labels
        self.ax.set_xlabel('Time', color='#CCCCCC', fontsize=12)
        self.ax.set_ylabel('Temperature (°C)', color='#CCCCCC', fontsize=12)
        
        # Add legend if there are multiple series
        if self.city_comparisons or (self.config.show_legend and len(self.ax.get_lines()) > 1):
            legend = self.ax.legend(
                loc='upper right',
                frameon=True,
                fancybox=True,
                shadow=True,
                framealpha=0.8,
                facecolor='#00000088',
                edgecolor='#FFFFFF44'
            )
            legend.get_frame().set_facecolor('#00000088')
            for text in legend.get_texts():
                text.set_color('#CCCCCC')
        
        # Adjust layout
        self.fig.tight_layout()
    
    def _update_analytics_display(self):
        """Update analytics display in toolbar."""
        if self.analytics:
            analytics_text = (
                f"📊 {self.analytics.data_points_count} points | "
                f"Avg: {self.analytics.avg_temperature:.1f}°C | "
                f"Range: {self.analytics.max_temperature - self.analytics.min_temperature:.1f}°C | "
                f"Trend: {self.analytics.temperature_trend.title()}"
            )
        else:
            analytics_text = "📊 No data available"
        
        self.analytics_label.configure(text=analytics_text)
    
    def _detect_weather_events(self, data_points: List[TemperatureDataPoint]) -> List[WeatherEvent]:
        """Detect significant weather events in data."""
        events = []
        
        for point in data_points:
            # Extreme heat detection
            if point.temperature > 35:
                events.append(WeatherEvent(
                    timestamp=point.timestamp,
                    event_type='extreme_heat',
                    temperature=point.temperature,
                    description=f'Extreme Heat: {point.temperature:.1f}°C',
                    icon='🔥',
                    severity=5 if point.temperature > 40 else 4
                ))
            
            # Freezing detection
            elif point.temperature < 0:
                events.append(WeatherEvent(
                    timestamp=point.timestamp,
                    event_type='freezing',
                    temperature=point.temperature,
                    description=f'Freezing: {point.temperature:.1f}°C',
                    icon='❄️',
                    severity=4 if point.temperature < -10 else 3
                ))
            
            # Rain/storm detection based on condition
            if point.condition:
                condition_lower = point.condition.lower()
                if 'storm' in condition_lower or 'thunder' in condition_lower:
                    events.append(WeatherEvent(
                        timestamp=point.timestamp,
                        event_type='storm',
                        temperature=point.temperature,
                        description=f'Storm: {point.condition}',
                        icon='⛈️',
                        severity=4
                    ))
                elif 'rain' in condition_lower or 'drizzle' in condition_lower:
                    events.append(WeatherEvent(
                        timestamp=point.timestamp,
                        event_type='rain',
                        temperature=point.temperature,
                        description=f'Rain: {point.condition}',
                        icon='🌧️',
                        severity=2
                    ))
        
        return events
    
    def _find_nearest_point(self, x_coord: float, y_coord: float) -> Optional[TemperatureDataPoint]:
        """Find nearest data point to mouse coordinates."""
        if not self.current_data or x_coord is None or y_coord is None:
            return None
        
        # Convert x_coord to datetime
        try:
            target_time = mdates.num2date(x_coord)
        except:
            return None
        
        # Find closest point
        min_distance = float('inf')
        nearest_point = None
        
        for point in self.current_data:
            time_diff = abs((point.timestamp - target_time).total_seconds())
            temp_diff = abs(point.temperature - y_coord)
            
            # Weighted distance (time is more important)
            distance = time_diff / 3600 + temp_diff  # Normalize time to hours
            
            if distance < min_distance:
                min_distance = distance
                nearest_point = point
        
        # Only return if reasonably close
        return nearest_point if min_distance < 24 else None  # Within 24 hours
    
    def _show_hover_tooltip(self, event, data_point: TemperatureDataPoint):
        """Show hover tooltip for data point."""
        # Hide existing tooltip
        if self.tooltip:
            self.tooltip.hide_tooltip()
        
        # Create tooltip content
        content = (
            f"🕒 {data_point.timestamp.strftime('%Y-%m-%d %H:%M')}\n"
            f"🌡️ Temperature: {data_point.temperature:.1f}°C\n"
        )
        
        if data_point.feels_like is not None:
            content += f"🤔 Feels like: {data_point.feels_like:.1f}°C\n"
        
        if data_point.humidity is not None:
            content += f"💧 Humidity: {data_point.humidity:.0f}%\n"
        
        if data_point.condition:
            content += f"☁️ Condition: {data_point.condition}\n"
        
        if data_point.wind_speed is not None:
            content += f"💨 Wind: {data_point.wind_speed:.1f} km/h"
        
        # Calculate tooltip position
        canvas_widget = self.canvas.get_tk_widget()
        x = canvas_widget.winfo_rootx() + int(event.x) + 10
        y = canvas_widget.winfo_rooty() + int(event.y) - 10
        
        # Create and show tooltip
        self.tooltip = GlassmorphicTooltip(self, x, y, content.strip())
        self.tooltip.show_tooltip()
    
    def _show_data_point_popup(self, data_point: TemperatureDataPoint):
        """Show detailed popup for clicked data point."""
        popup = ctk.CTkToplevel(self)
        popup.title("Weather Data Details")
        popup.geometry("400x500")
        popup.configure(fg_color=("#1a1a1a", "#1a1a1a"))
        
        # Make popup modal
        popup.transient(self)
        popup.grab_set()
        
        # Center popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (500 // 2)
        popup.geometry(f"400x500+{x}+{y}")
        
        # Content frame
        content_frame = GlassmorphicFrame(
            popup,
            fg_color=("#FFFFFF11", "#000000AA"),
            corner_radius=15
        )
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text="🌡️ Weather Data Details",
            font=("Segoe UI", 18, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        )
        title_label.pack(pady=(20, 10))
        
        # Data display
        data_text = (
            f"📅 Date: {data_point.timestamp.strftime('%A, %B %d, %Y')}\n"
            f"🕒 Time: {data_point.timestamp.strftime('%H:%M:%S')}\n\n"
            f"🌡️ Temperature: {data_point.temperature:.1f}°C\n"
        )
        
        if data_point.feels_like is not None:
            data_text += f"🤔 Feels Like: {data_point.feels_like:.1f}°C\n"
        
        if data_point.humidity is not None:
            data_text += f"💧 Humidity: {data_point.humidity:.0f}%\n"
        
        if data_point.pressure is not None:
            data_text += f"📊 Pressure: {data_point.pressure:.1f} hPa\n"
        
        if data_point.wind_speed is not None:
            data_text += f"💨 Wind Speed: {data_point.wind_speed:.1f} km/h\n"
        
        if data_point.condition:
            data_text += f"☁️ Condition: {data_point.condition}\n"
        
        if data_point.location:
            data_text += f"📍 Location: {data_point.location}"
        
        data_label = ctk.CTkLabel(
            content_frame,
            text=data_text.strip(),
            font=("Segoe UI", 12),
            text_color=("#CCCCCC", "#AAAAAA"),
            justify="left"
        )
        data_label.pack(pady=20, padx=20)
        
        # Close button
        close_button = GlassmorphicButton(
            content_frame,
            text="Close",
            command=popup.destroy,
            width=100,
            height=35
        )
        close_button.pack(pady=(0, 20))
    
    def _show_loading(self):
        """Show loading overlay."""
        self.loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.progress_bar.set(0)
        
        # Animate progress bar
        def animate_progress():
            for i in range(20):
                if not self.is_loading:
                    break
                self.after(i * 50, lambda p=i*0.05: self.progress_bar.set(p))
        
        threading.Thread(target=animate_progress, daemon=True).start()
    
    def _hide_loading(self):
        """Hide loading overlay."""
        self.loading_overlay.place_forget()
    
    def _show_error(self, message: str):
        """Show error message."""
        self._hide_loading()
        
        error_popup = ctk.CTkToplevel(self)
        error_popup.title("Error")
        error_popup.geometry("400x200")
        error_popup.configure(fg_color=("#1a1a1a", "#1a1a1a"))
        
        # Center popup
        error_popup.update_idletasks()
        x = (error_popup.winfo_screenwidth() // 2) - (200)
        y = (error_popup.winfo_screenheight() // 2) - (100)
        error_popup.geometry(f"400x200+{x}+{y}")
        
        # Error content
        error_frame = GlassmorphicFrame(
            error_popup,
            fg_color=("#FF6B6B22", "#FF6B6B11"),
            corner_radius=15
        )
        error_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        error_label = ctk.CTkLabel(
            error_frame,
            text=f"❌ Error\n\n{message}",
            font=("Segoe UI", 12),
            text_color=("#FFFFFF", "#E0E0E0"),
            justify="center"
        )
        error_label.pack(expand=True)
        
        # Close button
        close_button = GlassmorphicButton(
            error_frame,
            text="Close",
            command=error_popup.destroy,
            width=80,
            height=30
        )
        close_button.pack(pady=(0, 10))
        
        # Auto-close after 5 seconds
        error_popup.after(5000, error_popup.destroy)
    
    def _zoom_in(self):
        """Zoom in on chart."""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        
        x_range = (xlim[1] - xlim[0]) * 0.8
        y_range = (ylim[1] - ylim[0]) * 0.8
        
        self.ax.set_xlim(x_center - x_range/2, x_center + x_range/2)
        self.ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
        self.canvas.draw()
    
    def _zoom_out(self):
        """Zoom out on chart."""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        
        x_range = (xlim[1] - xlim[0]) * 1.25
        y_range = (ylim[1] - ylim[0]) * 1.25
        
        self.ax.set_xlim(x_center - x_range/2, x_center + x_range/2)
        self.ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
        self.canvas.draw()
    
    def _reset_zoom(self):
        """Reset chart zoom to fit all data."""
        if self.current_data:
            self.ax.relim()
            self.ax.autoscale()
            self.canvas.draw()
    
    def _zoom_at_point(self, x: float, y: float, scale_factor: float):
        """Zoom at specific point."""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # Calculate new limits
        x_range = (xlim[1] - xlim[0]) / scale_factor
        y_range = (ylim[1] - ylim[0]) / scale_factor
        
        # Center on mouse position
        x_center = x if x is not None else (xlim[0] + xlim[1]) / 2
        y_center = y if y is not None else (ylim[0] + ylim[1]) / 2
        
        self.ax.set_xlim(x_center - x_range/2, x_center + x_range/2)
        self.ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
        self.canvas.draw()
    
    def _show_export_dialog(self):
        """Show export options dialog."""
        export_popup = ctk.CTkToplevel(self)
        export_popup.title("Export Chart")
        export_popup.geometry("500x400")
        export_popup.configure(fg_color=("#1a1a1a", "#1a1a1a"))
        
        # Make popup modal
        export_popup.transient(self)
        export_popup.grab_set()
        
        # Center popup
        export_popup.update_idletasks()
        x = (export_popup.winfo_screenwidth() // 2) - (250)
        y = (export_popup.winfo_screenheight() // 2) - (200)
        export_popup.geometry(f"500x400+{x}+{y}")
        
        # Content frame
        content_frame = GlassmorphicFrame(
            export_popup,
            fg_color=("#FFFFFF11", "#000000AA"),
            corner_radius=15
        )
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text="📊 Export Chart",
            font=("Segoe UI", 18, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        )
        title_label.pack(pady=(20, 20))
        
        # Export format selection
        format_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        format_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            format_frame,
            text="Format:",
            font=("Segoe UI", 12, "bold"),
            text_color=("#CCCCCC", "#AAAAAA")
        ).pack(side="left")
        
        format_var = ctk.StringVar(value="PNG")
        format_menu = ctk.CTkOptionMenu(
            format_frame,
            values=["PNG", "PDF", "SVG", "JPG", "CSV"],
            variable=format_var,
            width=120
        )
        format_menu.pack(side="right")
        
        # DPI selection
        dpi_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        dpi_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            dpi_frame,
            text="Quality (DPI):",
            font=("Segoe UI", 12, "bold"),
            text_color=("#CCCCCC", "#AAAAAA")
        ).pack(side="left")
        
        dpi_var = ctk.StringVar(value="300")
        dpi_menu = ctk.CTkOptionMenu(
            dpi_frame,
            values=["150", "300", "600", "1200"],
            variable=dpi_var,
            width=120
        )
        dpi_menu.pack(side="right")
        
        # Options
        options_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=20)
        
        transparent_var = ctk.BooleanVar()
        transparent_check = ctk.CTkCheckBox(
            options_frame,
            text="Transparent background",
            variable=transparent_var,
            text_color=("#CCCCCC", "#AAAAAA")
        )
        transparent_check.pack(anchor="w", pady=5)
        
        metadata_var = ctk.BooleanVar(value=True)
        metadata_check = ctk.CTkCheckBox(
            options_frame,
            text="Include metadata",
            variable=metadata_var,
            text_color=("#CCCCCC", "#AAAAAA")
        )
        metadata_check.pack(anchor="w", pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(20, 20))
        
        def export_chart():
            settings = ExportSettings(
                format=format_var.get().lower(),
                dpi=int(dpi_var.get()),
                transparent=transparent_var.get(),
                include_metadata=metadata_var.get()
            )
            
            # Perform export
            success = self._export_chart(settings)
            
            if success:
                export_popup.destroy()
                # Show success message
                self._show_success_message("Chart exported successfully!")
            else:
                # Show error message
                self._show_error("Failed to export chart")
        
        export_button = GlassmorphicButton(
            button_frame,
            text="📁 Export",
            command=export_chart,
            width=100,
            height=35
        )
        export_button.pack(side="right", padx=(10, 0))
        
        cancel_button = GlassmorphicButton(
            button_frame,
            text="Cancel",
            command=export_popup.destroy,
            width=100,
            height=35
        )
        cancel_button.pack(side="left")
    
    def _export_chart(self, settings: ExportSettings) -> bool:
        """Export chart with specified settings."""
        try:
            from tkinter import filedialog
            
            # Get save location
            file_types = {
                'png': [('PNG files', '*.png')],
                'pdf': [('PDF files', '*.pdf')],
                'svg': [('SVG files', '*.svg')],
                'jpg': [('JPEG files', '*.jpg')],
                'csv': [('CSV files', '*.csv')]
            }
            
            filename = filedialog.asksaveasfilename(
                defaultextension=f".{settings.format}",
                filetypes=file_types.get(settings.format, [('All files', '*.*')]),
                title="Save Chart"
            )
            
            if not filename:
                return False
            
            if settings.format == 'csv':
                # Export data as CSV
                self._export_csv(filename, settings)
            else:
                # Export chart as image
                self._export_image(filename, settings)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    def _export_csv(self, filename: str, settings: ExportSettings):
        """Export chart data as CSV."""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            headers = ['Timestamp', 'Temperature (°C)']
            if any(p.feels_like is not None for p in self.current_data):
                headers.append('Feels Like (°C)')
            if any(p.humidity is not None for p in self.current_data):
                headers.append('Humidity (%)')
            if any(p.pressure is not None for p in self.current_data):
                headers.append('Pressure (hPa)')
            if any(p.wind_speed is not None for p in self.current_data):
                headers.append('Wind Speed (km/h)')
            if any(p.condition for p in self.current_data):
                headers.append('Condition')
            
            writer.writerow(headers)
            
            # Write data
            for point in self.current_data:
                row = [point.timestamp.isoformat(), point.temperature]
                
                if 'Feels Like (°C)' in headers:
                    row.append(point.feels_like or '')
                if 'Humidity (%)' in headers:
                    row.append(point.humidity or '')
                if 'Pressure (hPa)' in headers:
                    row.append(point.pressure or '')
                if 'Wind Speed (km/h)' in headers:
                    row.append(point.wind_speed or '')
                if 'Condition' in headers:
                    row.append(point.condition or '')
                
                writer.writerow(row)
            
            # Add metadata if requested
            if settings.include_metadata and self.analytics:
                writer.writerow([])
                writer.writerow(['Analytics'])
                writer.writerow(['Data Points', self.analytics.data_points_count])
                writer.writerow(['Average Temperature', f"{self.analytics.avg_temperature:.2f}°C"])
                writer.writerow(['Min Temperature', f"{self.analytics.min_temperature:.2f}°C"])
                writer.writerow(['Max Temperature', f"{self.analytics.max_temperature:.2f}°C"])
                writer.writerow(['Temperature Trend', self.analytics.temperature_trend])
    
    def _export_image(self, filename: str, settings: ExportSettings):
        """Export chart as image."""
        # Save current figure settings
        original_facecolor = self.fig.get_facecolor()
        
        try:
            # Set transparent background if requested
            if settings.transparent:
                self.fig.patch.set_facecolor('none')
                self.ax.patch.set_facecolor('none')
            
            # Save figure
            self.fig.savefig(
                filename,
                dpi=settings.dpi,
                bbox_inches='tight',
                transparent=settings.transparent,
                facecolor='none' if settings.transparent else self.fig.get_facecolor(),
                edgecolor='none'
            )
            
        finally:
            # Restore original settings
            self.fig.patch.set_facecolor(original_facecolor)
            self.ax.patch.set_facecolor('#2b2b2b')
    
    def _show_success_message(self, message: str):
        """Show success message popup."""
        success_popup = ctk.CTkToplevel(self)
        success_popup.title("Success")
        success_popup.geometry("300x150")
        success_popup.configure(fg_color=("#1a1a1a", "#1a1a1a"))
        
        # Center popup
        success_popup.update_idletasks()
        x = (success_popup.winfo_screenwidth() // 2) - (150)
        y = (success_popup.winfo_screenheight() // 2) - (75)
        success_popup.geometry(f"300x150+{x}+{y}")
        
        # Success content
        success_frame = GlassmorphicFrame(
            success_popup,
            fg_color=("#50C87822", "#50C87811"),
            corner_radius=15
        )
        success_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        success_label = ctk.CTkLabel(
            success_frame,
            text=f"✅ Success\n\n{message}",
            font=("Segoe UI", 12),
            text_color=("#FFFFFF", "#E0E0E0"),
            justify="center"
        )
        success_label.pack(expand=True)
        
        # Auto-close after 3 seconds
        success_popup.after(3000, success_popup.destroy)
    
    def _show_custom_range_dialog(self):
        """Show custom time range selection dialog."""
        range_popup = ctk.CTkToplevel(self)
        range_popup.title("Custom Time Range")
        range_popup.geometry("400x300")
        range_popup.configure(fg_color=("#1a1a1a", "#1a1a1a"))
        
        # Make popup modal
        range_popup.transient(self)
        range_popup.grab_set()
        
        # Center popup
        range_popup.update_idletasks()
        x = (range_popup.winfo_screenwidth() // 2) - (200)
        y = (range_popup.winfo_screenheight() // 2) - (150)
        range_popup.geometry(f"400x300+{x}+{y}")
        
        # Content frame
        content_frame = GlassmorphicFrame(
            range_popup,
            fg_color=("#FFFFFF11", "#000000AA"),
            corner_radius=15
        )
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text="📅 Custom Time Range",
            font=("Segoe UI", 16, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        )
        title_label.pack(pady=(20, 20))
        
        # Date inputs (simplified - would need proper date picker)
        start_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        start_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            start_frame,
            text="Start Date (YYYY-MM-DD):",
            text_color=("#CCCCCC", "#AAAAAA")
        ).pack(anchor="w")
        
        start_entry = ctk.CTkEntry(
            start_frame,
            placeholder_text="2024-01-01",
            width=200
        )
        start_entry.pack(anchor="w", pady=(5, 0))
        
        end_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        end_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            end_frame,
            text="End Date (YYYY-MM-DD):",
            text_color=("#CCCCCC", "#AAAAAA")
        ).pack(anchor="w")
        
        end_entry = ctk.CTkEntry(
            end_frame,
            placeholder_text="2024-01-31",
            width=200
        )
        end_entry.pack(anchor="w", pady=(5, 0))
        
        # Buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(20, 20))
        
        def apply_range():
            try:
                start_date = datetime.strptime(start_entry.get(), "%Y-%m-%d")
                end_date = datetime.strptime(end_entry.get(), "%Y-%m-%d")
                
                if start_date >= end_date:
                    raise ValueError("Start date must be before end date")
                
                self.selected_range = (start_date, end_date)
                self.config.time_range = TimeRange.CUSTOM
                range_popup.destroy()
                self.refresh_chart()
                
            except ValueError as e:
                self._show_error(f"Invalid date range: {str(e)}")
        
        apply_button = GlassmorphicButton(
            button_frame,
            text="Apply",
            command=apply_range,
            width=80,
            height=35
        )
        apply_button.pack(side="right", padx=(10, 0))
        
        cancel_button = GlassmorphicButton(
            button_frame,
            text="Cancel",
            command=range_popup.destroy,
            width=80,
            height=35
        )
        cancel_button.pack(side="left")
    
    def _show_context_menu(self, event):
        """Show context menu on right click."""
        context_menu = ctk.CTkToplevel(self)
        context_menu.overrideredirect(True)
        context_menu.configure(fg_color=("#2b2b2b", "#2b2b2b"))
        
        # Position menu at mouse
        canvas_widget = self.canvas.get_tk_widget()
        x = canvas_widget.winfo_rootx() + int(event.x)
        y = canvas_widget.winfo_rooty() + int(event.y)
        context_menu.geometry(f"+{x}+{y}")
        
        # Menu items
        menu_frame = ctk.CTkFrame(
            context_menu,
            fg_color=("#FFFFFF22", "#333333"),
            corner_radius=8
        )
        menu_frame.pack(padx=2, pady=2)
        
        # Add city comparison
        add_city_btn = ctk.CTkButton(
            menu_frame,
            text="📍 Add City Comparison",
            command=lambda: [context_menu.destroy(), self._show_add_city_dialog()],
            width=180,
            height=30,
            corner_radius=6,
            fg_color="transparent",
            hover_color=("#FFFFFF33", "#444444")
        )
        add_city_btn.pack(padx=5, pady=2)
        
        # Export chart
        export_btn = ctk.CTkButton(
            menu_frame,
            text="📊 Export Chart",
            command=lambda: [context_menu.destroy(), self._show_export_dialog()],
            width=180,
            height=30,
            corner_radius=6,
            fg_color="transparent",
            hover_color=("#FFFFFF33", "#444444")
        )
        export_btn.pack(padx=5, pady=2)
        
        # Reset zoom
        reset_btn = ctk.CTkButton(
            menu_frame,
            text="🏠 Reset Zoom",
            command=lambda: [context_menu.destroy(), self._reset_zoom()],
            width=180,
            height=30,
            corner_radius=6,
            fg_color="transparent",
            hover_color=("#FFFFFF33", "#444444")
        )
        reset_btn.pack(padx=5, pady=2)
        
        # Auto-hide menu
        def hide_menu():
            try:
                context_menu.destroy()
            except:
                pass
        
        context_menu.after(5000, hide_menu)
        context_menu.bind('<FocusOut>', lambda e: hide_menu())
    
    def _show_add_city_dialog(self):
        """Show dialog to add city for comparison."""
        city_popup = ctk.CTkToplevel(self)
        city_popup.title("Add City Comparison")
        city_popup.geometry("350x200")
        city_popup.configure(fg_color=("#1a1a1a", "#1a1a1a"))
        
        # Make popup modal
        city_popup.transient(self)
        city_popup.grab_set()
        
        # Center popup
        city_popup.update_idletasks()
        x = (city_popup.winfo_screenwidth() // 2) - (175)
        y = (city_popup.winfo_screenheight() // 2) - (100)
        city_popup.geometry(f"350x200+{x}+{y}")
        
        # Content frame
        content_frame = GlassmorphicFrame(
            city_popup,
            fg_color=("#FFFFFF11", "#000000AA"),
            corner_radius=15
        )
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text="📍 Add City for Comparison",
            font=("Segoe UI", 14, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        )
        title_label.pack(pady=(15, 15))
        
        # City input
        city_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text="Enter city name (e.g., London, UK)",
            width=250,
            height=35
        )
        city_entry.pack(pady=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(15, 15))
        
        def add_city():
            city_name = city_entry.get().strip()
            if city_name:
                self._add_city_comparison(city_name)
                city_popup.destroy()
        
        add_button = GlassmorphicButton(
            button_frame,
            text="Add",
            command=add_city,
            width=80,
            height=35
        )
        add_button.pack(side="right", padx=(10, 0))
        
        cancel_button = GlassmorphicButton(
            button_frame,
            text="Cancel",
            command=city_popup.destroy,
            width=80,
            height=35
        )
        cancel_button.pack(side="left")
        
        # Focus on entry
        city_entry.focus()
    
    def _add_city_comparison(self, city_name: str):
        """Add city for temperature comparison."""
        try:
            # Get color for this city
            color = self.city_colors[self.color_index % len(self.city_colors)]
            self.color_index += 1
            
            # Create comparison data (mock data for demo)
            comparison_data = self._generate_mock_city_data(city_name)
            
            comparison = CityComparison(
                city_name=city_name,
                data_points=comparison_data,
                color=color,
                line_style='-',
                marker_style='o',
                visible=True
            )
            
            self.city_comparisons[city_name] = comparison
            self._update_chart_display()
            
            self._show_success_message(f"Added {city_name} for comparison")
            
        except Exception as e:
            self.logger.error(f"Failed to add city comparison: {e}")
            self._show_error(f"Failed to add city: {str(e)}")
    
    def _generate_mock_city_data(self, city_name: str) -> List[TemperatureDataPoint]:
        """Generate mock temperature data for city comparison."""
        # This would normally fetch real data from weather API
        import random
        
        data_points = []
        base_temp = random.uniform(-10, 35)  # Random base temperature
        
        for i, point in enumerate(self.current_data):
            # Add some variation to make it realistic
            temp_variation = random.uniform(-5, 5)
            seasonal_factor = np.sin(i * 0.1) * 3  # Seasonal variation
            
            mock_temp = base_temp + temp_variation + seasonal_factor
            
            data_points.append(TemperatureDataPoint(
                timestamp=point.timestamp,
                temperature=mock_temp,
                feels_like=mock_temp + random.uniform(-2, 2),
                humidity=random.uniform(30, 90),
                pressure=random.uniform(990, 1030),
                wind_speed=random.uniform(0, 25),
                condition=random.choice(['Clear', 'Cloudy', 'Partly Cloudy', 'Rain']),
                location=city_name
            ))
        
        return data_points
    
    def _show_help_dialog(self):
        """Show help dialog with keyboard shortcuts."""
        help_popup = ctk.CTkToplevel(self)
        help_popup.title("Chart Help")
        help_popup.geometry("500x400")
        help_popup.configure(fg_color=("#1a1a1a", "#1a1a1a"))
        
        # Center popup
        help_popup.update_idletasks()
        x = (help_popup.winfo_screenwidth() // 2) - (250)
        y = (help_popup.winfo_screenheight() // 2) - (200)
        help_popup.geometry(f"500x400+{x}+{y}")
        
        # Content frame
        content_frame = GlassmorphicFrame(
            help_popup,
            fg_color=("#FFFFFF11", "#000000AA"),
            corner_radius=15
        )
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text="❓ Chart Help & Shortcuts",
            font=("Segoe UI", 16, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        )
        title_label.pack(pady=(20, 20))
        
        # Help content
        help_text = """
🖱️ Mouse Controls:
• Hover over data points for detailed tooltips
• Left click on points for detailed popup
• Right click for context menu
• Scroll wheel to zoom in/out

⌨️ Keyboard Shortcuts:
• R - Refresh chart data
• E - Export chart
• H - Show this help dialog
• Escape - Reset zoom

🎛️ Interactive Features:
• Switch between chart types (Line, Area, Bar, etc.)
• Toggle weather event annotations
• Toggle trend analysis display
• Add multiple cities for comparison
• Export in various formats (PNG, PDF, CSV)

📊 Chart Types:
• Line - Standard temperature trend
• Area - Temperature range visualization
• Bar - Discrete temperature readings
• Scatter - Temperature vs. other metrics
• Candlestick - Temperature range analysis
        """
        
        help_label = ctk.CTkLabel(
            content_frame,
            text=help_text.strip(),
            font=("Segoe UI", 11),
            text_color=("#CCCCCC", "#AAAAAA"),
            justify="left"
        )
        help_label.pack(pady=10, padx=20)
        
        # Close button
        close_button = GlassmorphicButton(
            content_frame,
            text="Close",
            command=help_popup.destroy,
            width=100,
            height=35
        )
        close_button.pack(pady=(10, 20))
    
    def add_city_comparison(self, city_name: str, data_points: List[TemperatureDataPoint]):
        """Public method to add city comparison data."""
        color = self.city_colors[self.color_index % len(self.city_colors)]
        self.color_index += 1
        
        comparison = CityComparison(
            city_name=city_name,
            data_points=data_points,
            color=color,
            line_style='-',
            marker_style='o',
            visible=True
        )
        
        self.city_comparisons[city_name] = comparison
        self._update_chart_display()
    
    def remove_city_comparison(self, city_name: str):
        """Remove city from comparison."""
        if city_name in self.city_comparisons:
            del self.city_comparisons[city_name]
            self._update_chart_display()
    
    def toggle_city_visibility(self, city_name: str):
        """Toggle visibility of city comparison."""
        if city_name in self.city_comparisons:
            self.city_comparisons[city_name].visible = not self.city_comparisons[city_name].visible
            self._update_chart_display()
    
    def get_chart_analytics(self) -> Optional[ChartAnalytics]:
        """Get current chart analytics."""
        return self.analytics
    
    def set_chart_config(self, config: ChartConfig):
        """Update chart configuration."""
        self.config = config
        self.chart_controller.config = config
        self.refresh_chart()
    
    def update_current_weather(self, weather_data):
        """Update chart with current weather data."""
        try:
            # Extract temperature from weather data
            if hasattr(weather_data, 'temperature'):
                temp = weather_data.temperature
            elif hasattr(weather_data, 'temp'):
                temp = weather_data.temp
            else:
                temp = 20.0  # Default
            
            # Extract location
            if hasattr(weather_data, 'location'):
                location = weather_data.location
            elif hasattr(weather_data, 'city'):
                location = f"{weather_data.city}, {weather_data.country}"
            else:
                location = "Current Location"
            
            # Add current data point to chart
            current_time = datetime.now()
            
            # Update chart title with current location
            self.config.title = f"Temperature Trends - {location}"
            
            # Add annotation for current weather
            condition = "Clear"
            if hasattr(weather_data, 'condition'):
                condition = weather_data.condition
            elif hasattr(weather_data, 'description'):
                condition = weather_data.description
            
            # Create current weather data point
            current_point = TemperatureDataPoint(
                timestamp=current_time,
                temperature=temp,
                feels_like=getattr(weather_data, 'feels_like', temp),
                humidity=getattr(weather_data, 'humidity', 50),
                pressure=getattr(weather_data, 'pressure', 1013),
                wind_speed=getattr(weather_data, 'wind_speed', 0),
                condition=condition,
                location=location
            )
            
            # Add to current data if not empty
            if self.current_data:
                # Replace the last point if it's very recent (within 5 minutes)
                if (current_time - self.current_data[-1].timestamp).total_seconds() < 300:
                    self.current_data[-1] = current_point
                else:
                    self.current_data.append(current_point)
            
            # Refresh the chart with updated data
            self.refresh_chart()
            
            # Show success message
            self._show_success_message(f"Updated: {temp:.1f}°C in {location}")
            
        except Exception as e:
            self.logger.error(f"Error updating chart with weather data: {e}")
            self._show_error("Failed to update chart with weather data")