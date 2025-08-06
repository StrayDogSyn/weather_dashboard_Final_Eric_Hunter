import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Any
import threading
import asyncio
import math
import random
import logging

from ..components.glassmorphic.glass_panel import GlassPanel
from ...services.weather.weather_service import WeatherService
from ...services.logging_service import LoggingService

class GraphsTab(ctk.CTkFrame):
    """Interactive temperature graphs with glassmorphic design"""
    
    def __init__(self, parent, weather_service: WeatherService):
        super().__init__(parent, fg_color="transparent")
        self.weather_service = weather_service
        self.logger = LoggingService()
        self.historical_data = []
        self.current_location = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI components"""
        # Main container with glassmorphic effect
        self.container = GlassPanel(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            self.container,
            text="📊 Temperature Analytics",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        title_label.pack(pady=(20, 10))
        
        # Controls section
        self.create_controls()
        
        # Graph container
        self.create_graph_area()
        
        # Status bar
        self.create_status_bar()
        
        # Initial data load
        self.load_initial_data()
        
    def create_controls(self):
        """Create time range and display controls"""
        controls_frame = ctk.CTkFrame(
            self.container, 
            fg_color="#2a2a2a",
            corner_radius=10
        )
        controls_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        # Left side - Time range selector
        left_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True, padx=15, pady=15)
        
        range_label = ctk.CTkLabel(
            left_frame,
            text="Time Range:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cccccc"
        )
        range_label.pack(anchor="w")
        
        range_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        range_frame.pack(fill="x", pady=(5, 0))
        
        self.time_range = ctk.StringVar(value="24h")
        ranges = [("24 Hours", "24h"), ("7 Days", "7d"), ("30 Days", "30d")]
        
        for text, value in ranges:
            btn = ctk.CTkRadioButton(
                range_frame,
                text=text,
                variable=self.time_range,
                value=value,
                command=self.update_graph,
                fg_color="#00D4FF",
                hover_color="#0099cc",
                text_color="#cccccc"
            )
            btn.pack(side="left", padx=(0, 15))
        
        # Right side - Display options
        right_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        right_frame.pack(side="right", padx=15, pady=15)
        
        options_label = ctk.CTkLabel(
            right_frame,
            text="Display Options:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cccccc"
        )
        options_label.pack(anchor="w")
        
        options_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        options_frame.pack(fill="x", pady=(5, 0))
        
        self.show_precipitation = ctk.BooleanVar(value=True)
        precip_check = ctk.CTkCheckBox(
            options_frame,
            text="Precipitation",
            variable=self.show_precipitation,
            command=self.update_graph,
            fg_color="#00D4FF",
            hover_color="#0099cc",
            text_color="#cccccc"
        )
        precip_check.pack(side="top", anchor="w")
        
        self.show_humidity = ctk.BooleanVar(value=False)
        humidity_check = ctk.CTkCheckBox(
            options_frame,
            text="Humidity",
            variable=self.show_humidity,
            command=self.update_graph,
            fg_color="#00D4FF",
            hover_color="#0099cc",
            text_color="#cccccc"
        )
        humidity_check.pack(side="top", anchor="w", pady=(5, 0))
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            right_frame,
            text="🔄 Refresh",
            command=self.refresh_data,
            fg_color="#00D4FF",
            hover_color="#00B8E6",
            corner_radius=8,
            width=100
        )
        refresh_btn.pack(pady=(10, 0))
        
    def create_graph_area(self):
        """Create matplotlib graph with glassmorphic styling"""
        # Graph frame
        graph_frame = ctk.CTkFrame(
            self.container,
            fg_color="#1a1a1a",
            corner_radius=15
        )
        graph_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create figure with dark theme
        plt.style.use('dark_background')
        self.figure = Figure(figsize=(12, 7), facecolor='#0d0d0d')
        self.ax = self.figure.add_subplot(111)
        
        # Style the axes
        self.ax.set_facecolor('#1a1a1a')
        self.ax.spines['bottom'].set_color('#666666')
        self.ax.spines['left'].set_color('#666666')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.tick_params(colors='#999999', labelsize=10)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add interactivity
        self.add_interactivity()
        
        # Add custom toolbar
        self.create_custom_toolbar(graph_frame)
        
    def create_custom_toolbar(self, parent):
        """Create a custom styled toolbar"""
        toolbar_frame = ctk.CTkFrame(
            parent,
            fg_color="#2a2a2a",
            corner_radius=8,
            height=40
        )
        toolbar_frame.pack(fill="x", padx=10, pady=(0, 10))
        toolbar_frame.pack_propagate(False)
        
        # Zoom controls
        zoom_in_btn = ctk.CTkButton(
            toolbar_frame,
            text="🔍+",
            command=self.zoom_in,
            fg_color="transparent",
            hover_color="#404040",
            width=40,
            height=30
        )
        zoom_in_btn.pack(side="left", padx=5, pady=5)
        
        zoom_out_btn = ctk.CTkButton(
            toolbar_frame,
            text="🔍-",
            command=self.zoom_out,
            fg_color="transparent",
            hover_color="#FFFFFF1A",
            width=40,
            height=30
        )
        zoom_out_btn.pack(side="left", padx=5, pady=5)
        
        reset_btn = ctk.CTkButton(
            toolbar_frame,
            text="🏠",
            command=self.reset_zoom,
            fg_color="transparent",
            hover_color="#FFFFFF1A",
            width=40,
            height=30
        )
        reset_btn.pack(side="left", padx=5, pady=5)
        
        # Export button
        export_btn = ctk.CTkButton(
            toolbar_frame,
            text="💾 Export",
            command=self.export_graph,
            fg_color="#00D4FF33",
            hover_color="#0099cc",
            width=80,
            height=30
        )
        export_btn.pack(side="right", padx=5, pady=5)
        
    def create_status_bar(self):
        """Create status bar for data info"""
        self.status_frame = ctk.CTkFrame(
            self.container,
            fg_color="#2a2a2a",
            corner_radius=8,
            height=30
        )
        self.status_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Loading data...",
            font=ctk.CTkFont(size=12),
            text_color="#999999"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        self.data_count_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#00D4FF"
        )
        self.data_count_label.pack(side="right", padx=10, pady=5)
        
    def load_initial_data(self):
        """Load initial historical data"""
        try:
            # Generate sample data for demonstration
            self.generate_sample_data()
            self.update_graph()
            self.status_label.configure(text="Data loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading initial data: {e}")
            self.status_label.configure(text="Error loading data")
            
    def generate_sample_data(self):
        """Generate sample historical data for demonstration"""
        now = datetime.now()
        self.historical_data = []
        
        # Generate 30 days of sample data
        for i in range(720):  # 30 days * 24 hours
            timestamp = now - timedelta(hours=i)
            
            # Simulate temperature variation
            base_temp = 20 + 10 * np.sin(2 * np.pi * i / 24)  # Daily cycle
            seasonal_temp = 5 * np.sin(2 * np.pi * i / (24 * 365))  # Seasonal
            noise = np.random.normal(0, 2)  # Random variation
            temperature = base_temp + seasonal_temp + noise
            
            # Simulate precipitation
            precipitation = max(0, np.random.normal(0, 2)) if np.random.random() < 0.3 else 0
            
            # Simulate humidity
            humidity = max(30, min(90, 60 + np.random.normal(0, 15)))
            
            self.historical_data.append({
                'timestamp': timestamp,
                'temperature': round(temperature, 1),
                'precipitation': round(precipitation, 1),
                'humidity': round(humidity, 1)
            })
            
        # Sort by timestamp (oldest first)
        self.historical_data.sort(key=lambda x: x['timestamp'])
        
    def get_data_for_range(self, hours: int) -> List[Dict[str, Any]]:
        """Get data for specified time range"""
        if not self.historical_data:
            return []
            
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [d for d in self.historical_data if d['timestamp'] >= cutoff_time]
        
    def update_graph(self):
        """Update graph with current settings"""
        try:
            self.ax.clear()
            
            # Get data for selected range
            range_hours = {"24h": 24, "7d": 168, "30d": 720}[self.time_range.get()]
            data = self.get_data_for_range(range_hours)
            
            if not data:
                self.show_no_data_message()
                return
                
            # Extract data
            times = [d['timestamp'] for d in data]
            temps = [d['temperature'] for d in data]
            
            # Plot temperature line with gradient
            line = self.ax.plot(times, temps,
                               color='#00D4FF',
                               linewidth=2.5,
                               marker='o',
                               markersize=3,
                               markerfacecolor='#00D4FF',
                               markeredgecolor='#FFFFFF',
                               markeredgewidth=0.5,
                               label='Temperature (°C)',
                               alpha=0.9)[0]
            
            # Add gradient fill
            self.ax.fill_between(times, temps,
                                alpha=0.2,
                                color='#00D4FF',
                                interpolate=True)
            
            # Add precipitation if enabled
            if self.show_precipitation.get():
                self.add_precipitation_bars(data)
                
            # Add humidity if enabled
            if self.show_humidity.get():
                self.add_humidity_line(data)
            
            # Styling
            self.ax.set_xlabel('Time', color='#cccccc', fontsize=12)
            self.ax.set_ylabel('Temperature (°C)', color='#cccccc', fontsize=12)
            
            range_text = {"24h": "24 Hours", "7d": "7 Days", "30d": "30 Days"}[self.time_range.get()]
            self.ax.set_title(f'Temperature Trend - Last {range_text}',
                             color='#FFFFFF',
                             fontsize=16,
                             fontweight='bold',
                             pad=20)
            
            # Format time axis
            self.format_time_axis(range_hours)
            
            # Add grid
            self.ax.grid(True, alpha=0.15, linestyle='--', color='#FFFFFF')
            
            # Add min/max annotations
            self.annotate_extremes(times, temps)
            
            # Add legend if multiple series
            if self.show_precipitation.get() or self.show_humidity.get():
                self.ax.legend(loc='upper left', framealpha=0.8, facecolor='#1a1a1a')
            
            # Update status
            self.data_count_label.configure(text=f"{len(data)} data points")
            
            # Refresh canvas
            self.canvas.draw()
            
        except Exception as e:
            logging.error(f"Error updating graph: {e}")
            self.show_error_message(str(e))

    def load_historical_data(self):
        """Load historical weather data for graphing"""
        try:
            # Generate sample historical data for demonstration
            # In a real implementation, this would fetch from weather service
            now = datetime.now()
            self.historical_data = []
            
            for i in range(720):  # 30 days of hourly data
                timestamp = now - timedelta(hours=i)
                # Generate realistic temperature variation
                base_temp = 20 + 10 * math.sin(i * 2 * math.pi / 24)  # Daily cycle
                temp_variation = 5 * math.sin(i * 2 * math.pi / (24 * 7))  # Weekly cycle
                noise = random.uniform(-2, 2)  # Random variation
                temperature = base_temp + temp_variation + noise
                
                # Generate precipitation data
                precipitation = max(0, random.uniform(-1, 5) if random.random() < 0.2 else 0)
                
                self.historical_data.append({
                    'timestamp': timestamp,
                    'temperature': round(temperature, 1),
                    'precipitation': round(precipitation, 1)
                })
                
            # Sort by timestamp (oldest first)
            self.historical_data.sort(key=lambda x: x['timestamp'])
            
        except Exception as e:
            logging.error(f"Error loading historical data: {e}")
            self.historical_data = []

    def get_data_for_range(self, hours):
        """Get data for the specified time range"""
        if not self.historical_data:
            return []
            
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [d for d in self.historical_data if d['timestamp'] >= cutoff_time]

    def show_no_data_message(self):
        """Show message when no data is available"""
        self.ax.text(0.5, 0.5, 'No data available for selected range',
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=self.ax.transAxes,
                    color='#999999',
                    fontsize=14)
        self.ax.set_title('Temperature Graph', color='#FFFFFF', fontsize=16)
        self.canvas.draw()

    def add_precipitation_bars(self, data):
        """Add precipitation bars to the graph"""
        times = [d['timestamp'] for d in data]
        precip = [d.get('precipitation', 0) for d in data]
        
        # Create secondary y-axis for precipitation
        ax2 = self.ax.twinx()
        ax2.bar(times, precip, alpha=0.3, color='#00AAFF', width=0.02, label='Precipitation (mm)')
        ax2.set_ylabel('Precipitation (mm)', color='#cccccc')
        ax2.tick_params(colors='#999999')
        ax2.spines['right'].set_color('#666666')
        ax2.spines['top'].set_visible(False)

    def format_time_axis(self):
        """Format the time axis based on selected range"""
        range_value = self.time_range.get()
        
        if range_value == "24h":
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
        elif range_value == "7d":
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        else:  # 30d
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            
        # Rotate labels for better readability
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)
        self.figure.tight_layout()

    def annotate_extremes(self, times, temps):
        """Add annotations for min/max temperatures"""
        if not temps:
            return
            
        min_temp = min(temps)
        max_temp = max(temps)
        min_idx = temps.index(min_temp)
        max_idx = temps.index(max_temp)
        
        # Annotate minimum
        self.ax.annotate(f'Min: {min_temp}°C',
                        xy=(times[min_idx], min_temp),
                        xytext=(10, 10),
                        textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FF6B6B', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', color='#FF6B6B'),
                        color='white',
                        fontsize=10)
        
        # Annotate maximum
        self.ax.annotate(f'Max: {max_temp}°C',
                        xy=(times[max_idx], max_temp),
                        xytext=(10, -20),
                        textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FF9F43', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', color='#FF9F43'),
                        color='white',
                        fontsize=10)

    def create_custom_toolbar(self, parent):
        """Create custom toolbar with glassmorphic styling"""
        toolbar_frame = ctk.CTkFrame(
            parent,
            fg_color="#2a2a2a",
            corner_radius=10,
            height=40
        )
        toolbar_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Export button
        export_btn = ctk.CTkButton(
            toolbar_frame,
            text="📊 Export",
            width=80,
            height=30,
            fg_color="#00D4FF",
            hover_color="#0099cc",
            command=self.export_graph
        )
        export_btn.pack(side="left", padx=5, pady=5)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            toolbar_frame,
            text="🔄 Refresh",
            width=80,
            height=30,
            fg_color="#00D4FF",
            hover_color="#0099cc",
            command=self.refresh_data
        )
        refresh_btn.pack(side="left", padx=5, pady=5)
        
        # Info label
        info_label = ctk.CTkLabel(
            toolbar_frame,
            text="Interactive temperature visualization with historical data",
            text_color="#999999",
            font=("Arial", 11)
        )
        info_label.pack(side="right", padx=10, pady=5)

    def export_graph(self):
        """Export the current graph as PNG"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                title="Save Temperature Graph"
            )
            if filename:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight', 
                                  facecolor='#0d0d0d', edgecolor='none')
                logging.info(f"Graph exported to {filename}")
        except Exception as e:
            logging.error(f"Error exporting graph: {e}")

    def refresh_data(self):
        """Refresh the historical data and update graph"""
        try:
            self.load_historical_data()
            self.update_graph()
        except Exception as e:
            logging.error(f"Error refreshing data: {e}")
            self.show_error_message(str(e))
            
    def add_precipitation_bars(self, data: List[Dict[str, Any]]):
        """Add precipitation bars to the graph"""
        times = [d['timestamp'] for d in data]
        precip = [d.get('precipitation', 0) for d in data]
        
        if any(p > 0 for p in precip):
            # Create secondary y-axis for precipitation
            ax2 = self.ax.twinx()
            ax2.bar(times, precip,
                   alpha=0.4,
                   color='#4A90E2',
                   width=timedelta(hours=0.8),
                   label='Precipitation (mm)')
            
            ax2.set_ylabel('Precipitation (mm)', color='#4A90E2', fontsize=12)
            ax2.tick_params(axis='y', labelcolor='#4A90E2')
            ax2.spines['right'].set_color('#4A90E2')
            
    def add_humidity_line(self, data: List[Dict[str, Any]]):
        """Add humidity line to the graph"""
        times = [d['timestamp'] for d in data]
        humidity = [d.get('humidity', 0) for d in data]
        
        # Create secondary y-axis for humidity
        ax3 = self.ax.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        
        ax3.plot(times, humidity,
                color='#FFB84D',
                linewidth=1.5,
                linestyle='--',
                alpha=0.8,
                label='Humidity (%)')
        
        ax3.set_ylabel('Humidity (%)', color='#FFB84D', fontsize=12)
        ax3.tick_params(axis='y', labelcolor='#FFB84D')
        ax3.spines['right'].set_color('#FFB84D')
        ax3.set_ylim(0, 100)
        
    def format_time_axis(self, hours: int):
        """Format the time axis based on range"""
        if hours <= 24:
            # Hourly format for 24h
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
        elif hours <= 168:
            # Daily format for 7 days
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        else:
            # Weekly format for 30 days
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            
        # Rotate labels for better readability
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
    def annotate_extremes(self, times: List[datetime], temps: List[float]):
        """Add annotations for min/max temperatures"""
        if not temps:
            return
            
        min_temp = min(temps)
        max_temp = max(temps)
        min_idx = temps.index(min_temp)
        max_idx = temps.index(max_temp)
        
        # Annotate minimum
        self.ax.annotate(f'Min: {min_temp}°C',
                        xy=(times[min_idx], min_temp),
                        xytext=(10, 20),
                        textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FF6B6B', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', color='#FF6B6B'),
                        color='white',
                        fontsize=10)
        
        # Annotate maximum
        self.ax.annotate(f'Max: {max_temp}°C',
                        xy=(times[max_idx], max_temp),
                        xytext=(10, -30),
                        textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FF9500', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', color='#FF9500'),
                        color='white',
                        fontsize=10)
        
    def show_no_data_message(self):
        """Show message when no data is available"""
        self.ax.text(0.5, 0.5, 'No data available for selected range',
                    transform=self.ax.transAxes,
                    ha='center', va='center',
                    fontsize=16,
                    color='#999999',
                    bbox=dict(boxstyle='round,pad=1', facecolor='#2a2a2a'))
        self.canvas.draw()
        
    def show_error_message(self, error: str):
        """Show error message on graph"""
        self.ax.text(0.5, 0.5, f'Error loading data:\n{error}',
                    transform=self.ax.transAxes,
                    ha='center', va='center',
                    fontsize=14,
                    color='#FF6B6B',
                    bbox=dict(boxstyle='round,pad=1', facecolor='#FF6B6B1A'))
        self.canvas.draw()
        
    def refresh_data(self):
        """Refresh the data and update graph"""
        self.status_label.configure(text="Refreshing data...")
        try:
            # In a real implementation, this would fetch new data
            self.generate_sample_data()
            self.update_graph()
            self.status_label.configure(text="Data refreshed successfully")
        except Exception as e:
            self.logger.error(f"Error refreshing data: {e}")
            self.status_label.configure(text="Error refreshing data")
            
    def zoom_in(self):
        """Zoom in on the graph"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        
        self.ax.set_xlim(xlim[0] + x_range * 0.1, xlim[1] - x_range * 0.1)
        self.ax.set_ylim(ylim[0] + y_range * 0.1, ylim[1] - y_range * 0.1)
        
        self.canvas.draw()
        
    def zoom_out(self):
        """Zoom out on the graph"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        
        self.ax.set_xlim(xlim[0] - x_range * 0.1, xlim[1] + x_range * 0.1)
        self.ax.set_ylim(ylim[0] - y_range * 0.1, ylim[1] + y_range * 0.1)
        
        self.canvas.draw()
        
    def reset_zoom(self):
        """Reset zoom to show all data"""
        self.ax.relim()
        self.ax.autoscale()
        self.canvas.draw()
        
    def export_graph(self):
        """Export the current graph as PNG"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                title="Save Graph"
            )
            
            if filename:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight',
                                   facecolor='#0d0d0d', edgecolor='none')
                self.status_label.configure(text=f"Graph exported to {filename}")
        except Exception as e:
            self.logger.error(f"Error exporting graph: {e}")
            self.status_label.configure(text="Error exporting graph")
            
    def add_interactivity(self):
        """Add hover tooltips and click interactions"""
        self.annotation = self.ax.annotate('',
                                          xy=(0, 0),
                                          xytext=(20, 20),
                                          textcoords='offset points',
                                          bbox=dict(boxstyle='round',
                                                  fc='#000000CC',
                                                  ec='#00D4FF'),
                                          arrowprops=dict(arrowstyle='->',
                                                        color='#00D4FF',
                                                        lw=1),
                                          color='#FFFFFF',
                                          fontsize=10,
                                          visible=False)
        
        def on_hover(event):
            if event.inaxes == self.ax:
                # Find nearest data point
                for line in self.ax.lines:
                    cont, ind = line.contains(event)
                    if cont:
                        x, y = line.get_data()
                        idx = ind['ind'][0]
                        
                        # Show tooltip
                        self.annotation.xy = (x[idx], y[idx])
                        text = f'{y[idx]:.1f}°C\n{x[idx].strftime("%H:%M")}'
                        self.annotation.set_text(text)
                        self.annotation.set_visible(True)
                        self.canvas.draw_idle()
                        return
                
                # Hide tooltip if not hovering
                self.annotation.set_visible(False)
                self.canvas.draw_idle()
        
        self.canvas.mpl_connect('motion_notify_event', on_hover)
    
    def set_location(self, location: str):
        """Set the current location for data fetching"""
        self.current_location = location
        self.refresh_data()