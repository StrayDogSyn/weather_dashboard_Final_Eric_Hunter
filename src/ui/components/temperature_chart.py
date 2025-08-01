"""Advanced Temperature Analytics Chart Component for Weather Dashboard.

This module provides a comprehensive weather analytics system with interactive
visualization capabilities, multiple chart types, advanced data analysis,
and real-time updates using matplotlib and customtkinter."""

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
from .chart.chart_analytics import ChartAnalyticsMixin
from .chart.chart_interactive import ChartInteractiveMixin
from ..theme import DataTerminalTheme
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
                       ChartExportMixin,
                       ChartAnalyticsMixin,
                       ChartInteractiveMixin):
    """Advanced weather analytics chart with comprehensive interactive features."""
    
    def __init__(self, parent, **kwargs):
        """Initialize enhanced temperature chart."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("default"), **kwargs)
        
        # Initialize state
        self.current_timeframe = "24h"
        self.forecast_data = None
        
        # Initialize mixin components
        self.__init_analytics__()
        self.__init_interactive__()
        
        # Create UI and initialize chart
        self._create_ui()
        self._setup_analytics_ui()
        self._setup_interactive_features()
        
        # Set up callbacks
        self.set_callbacks(
            on_data_point_click=self._handle_data_point_click,
            on_zoom_change=self._handle_zoom_change,
            on_real_time_update=self._handle_real_time_update
        )
        
        self._create_default_chart()
    
    def _create_ui(self):
        """Create the main UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Chart frame with enhanced styling and header
        self.chart_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            border_color=DataTerminalTheme.PRIMARY,
            border_width=2,
            corner_radius=12
        )
        self.chart_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.chart_frame.grid_rowconfigure(2, weight=1)
        self.chart_frame.grid_columnconfigure(0, weight=1)
        
        # Chart header with controls
        self.header_frame = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        self.chart_title = ctk.CTkLabel(
            self.header_frame,
            text="📊 Temperature Trends",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        self.chart_title.grid(row=0, column=0, sticky="w")
        
        # Chart controls
        self.controls_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.controls_frame.grid(row=0, column=1, sticky="e")
        
        self.time_range_var = ctk.StringVar(value="24h")
        self.time_range_menu = ctk.CTkOptionMenu(
            self.controls_frame,
            values=["6h", "12h", "24h", "48h", "7d"],
            variable=self.time_range_var,
            command=self._on_time_range_change,
            width=80,
            height=28
        )
        self.time_range_menu.pack(side="right", padx=(10, 0))
        
        # Create UI elements using mixins
        self.create_widgets()
        self.setup_layout()
        
        # Setup matplotlib and event handlers
        self.setup_matplotlib()
        self.setup_event_handlers()
        
    def _setup_analytics_ui(self):
        """Setup analytics control interface."""
        # Create analytics controls
        self.create_analytics_controls()
        
        # Create interactive controls
        self.create_interactive_controls()
        
        # Layout analytics components
        self._layout_analytics_components()
        
    def _layout_analytics_components(self):
        """Layout analytics and interactive components."""
        # Analytics controls frame
        analytics_main_frame = ctk.CTkFrame(self, fg_color="transparent")
        analytics_main_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        analytics_main_frame.grid_columnconfigure(0, weight=1)
        
        # Chart type and metrics row
        chart_controls_frame = ctk.CTkFrame(analytics_main_frame, fg_color="transparent")
        chart_controls_frame.grid(row=0, column=0, sticky="ew", pady=2)
        chart_controls_frame.grid_columnconfigure(2, weight=1)
        
        # Chart type selector
        chart_type_label = ctk.CTkLabel(
            chart_controls_frame,
            text="Chart Type:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff88"
        )
        chart_type_label.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        if hasattr(self, 'chart_type_frame'):
            self.chart_type_frame.grid(row=0, column=1, padx=5, sticky="w")
        
        # Enhanced timeframe selector
        timeframe_label = ctk.CTkLabel(
            chart_controls_frame,
            text="Timeframe:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff88"
        )
        timeframe_label.grid(row=0, column=3, padx=(20, 5), sticky="w")
        
        if hasattr(self, 'enhanced_timeframe_frame'):
            self.enhanced_timeframe_frame.grid(row=0, column=4, padx=5, sticky="w")
        
        # Metrics selection row
        metrics_frame = ctk.CTkFrame(analytics_main_frame, fg_color="transparent")
        metrics_frame.grid(row=1, column=0, sticky="ew", pady=2)
        
        metrics_label = ctk.CTkLabel(
            metrics_frame,
            text="Metrics:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff88"
        )
        metrics_label.grid(row=0, column=0, padx=(0, 10), sticky="nw")
        
        if hasattr(self, 'metrics_frame'):
            self.metrics_frame.grid(row=0, column=1, sticky="w")
        
        # Analysis options row
        analysis_controls_frame = ctk.CTkFrame(analytics_main_frame, fg_color="transparent")
        analysis_controls_frame.grid(row=2, column=0, sticky="ew", pady=2)
        
        analysis_label = ctk.CTkLabel(
            analysis_controls_frame,
            text="Analysis:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff88"
        )
        analysis_label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        if hasattr(self, 'analysis_frame'):
            self.analysis_frame.grid(row=0, column=1, sticky="w")
        
        # Comparison tools
        if hasattr(self, 'comparison_frame'):
            self.comparison_frame.grid(row=0, column=2, padx=(20, 0), sticky="w")
        
        # Interactive controls frame
        interactive_main_frame = ctk.CTkFrame(self, fg_color="transparent")
        interactive_main_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        interactive_main_frame.grid_columnconfigure(0, weight=1)
        
        # Interactive controls row
        interactive_controls_frame = ctk.CTkFrame(interactive_main_frame, fg_color="transparent")
        interactive_controls_frame.grid(row=0, column=0, sticky="ew")
        
        # Zoom controls
        zoom_label = ctk.CTkLabel(
            interactive_controls_frame,
            text="Zoom:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff88"
        )
        zoom_label.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        if hasattr(self, 'zoom_frame'):
            self.zoom_frame.grid(row=0, column=1, padx=5, sticky="w")
        
        # Real-time controls
        realtime_label = ctk.CTkLabel(
            interactive_controls_frame,
            text="Updates:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff88"
        )
        realtime_label.grid(row=0, column=2, padx=(20, 5), sticky="w")
        
        if hasattr(self, 'realtime_frame'):
            self.realtime_frame.grid(row=0, column=3, padx=5, sticky="w")
        
        # Export and view controls
        export_view_frame = ctk.CTkFrame(interactive_main_frame, fg_color="transparent")
        export_view_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # Export controls
        export_label = ctk.CTkLabel(
            export_view_frame,
            text="Export:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff88"
        )
        export_label.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        if hasattr(self, 'export_frame'):
            self.export_frame.grid(row=0, column=1, padx=5, sticky="w")
        
        # View controls
        view_label = ctk.CTkLabel(
            export_view_frame,
            text="View:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff88"
        )
        view_label.grid(row=0, column=2, padx=(20, 5), sticky="w")
        
        if hasattr(self, 'view_frame'):
            self.view_frame.grid(row=0, column=3, padx=5, sticky="w")
     
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
    def update_forecast(self, forecast_data):
        """Update chart with new forecast data.
        
        Args:
            forecast_data: Can be List[ForecastData], Dict[str, Any], or str
        """
        try:
            self.forecast_data = forecast_data
            
            # Handle different input types
            if isinstance(forecast_data, str):
                # If it's a string, generate sample data
                print(f"Warning: Received string forecast data: {forecast_data[:100]}...")
                processed_data = self.generate_realistic_data(self.current_timeframe)
            elif isinstance(forecast_data, dict):
                # If it's a dictionary, process it directly
                processed_data = self.process_forecast_data(forecast_data)
            elif isinstance(forecast_data, list):
                # If it's a list of ForecastData objects, convert to dict format
                if forecast_data and hasattr(forecast_data[0], 'hourly_forecasts'):
                    # Convert ForecastData objects to dict format
                    dict_data = self._convert_forecast_objects_to_dict(forecast_data)
                    processed_data = self.process_forecast_data(dict_data)
                else:
                    # Assume it's already processed data
                    processed_data = forecast_data
            else:
                # Fallback to sample data
                print(f"Warning: Unknown forecast data type: {type(forecast_data)}")
                processed_data = self.generate_realistic_data(self.current_timeframe)
            
            # Update hover data for interactive features
            if hasattr(self, 'update_hover_data'):
                self.update_hover_data({
                    'temperature': {
                        'times': processed_data.get('dates', processed_data.get('times', [])),
                        'values': processed_data.get('temperatures', [])
                    }
                })
            
            self.update_data_storage(processed_data)
            
            # Use advanced chart creation if available
            if hasattr(self, 'create_advanced_chart'):
                self.create_advanced_chart(processed_data)
            else:
                self.refresh_chart_display()
                
        except Exception as e:
            print(f"Error updating forecast data: {e}")
            # Fallback to sample data
            processed_data = self.generate_realistic_data(self.current_timeframe)
            self.update_data_storage(processed_data)
            self.refresh_chart_display()
        
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
    
    def update_timeframe(self, timeframe: str):
        """Update chart timeframe - alias for set_timeframe."""
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
    def _on_time_range_change(self, value: str):
        """Handle time range selection change."""
        self.current_time_range = value
        if hasattr(self, 'forecast_data') and self.forecast_data:
            self.update_chart_data(self.forecast_data)
    
    def update_chart_data(self, forecast_data: Dict[str, Any]):
        """Update chart with new forecast data, enhanced filtering, and status feedback."""
        try:
            # Update parent status if available
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("Updating temperature chart...", "loading")
            
            self.forecast_data = forecast_data  # Store for time range changes
            
            # Filter data based on selected time range
            filtered_data = self._filter_data_by_range(forecast_data, self.time_range_var.get())
            
            if not filtered_data:
                if hasattr(self.parent, 'update_status'):
                    self.parent.update_status("No chart data available", "warning")
                return
            
            self.update_data_storage(filtered_data)
            self.refresh_chart_display()
            
            # Update chart title with data info
            if 'location' in forecast_data:
                location_name = forecast_data['location'].get('name', 'Unknown')
                self.chart_title.configure(text=f"📊 {location_name} - Temperature Trends")
            
            # Update parent status with success
            if hasattr(self.parent, 'update_status'):
                range_text = self.time_range_var.get()
                self.parent.update_status(f"Chart updated ({range_text} view)", "success")
            
        except Exception as e:
            print(f"Error updating chart: {e}")
            # Update parent status with error
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("Error updating temperature chart", "error")
    
    def _filter_data_by_range(self, data: Dict[str, Any], time_range: str) -> Dict[str, Any]:
        """Filter forecast data based on selected time range."""
        if 'forecast' not in data or 'forecastday' not in data['forecast']:
            return data
        
        # Time range mapping to hours
        range_hours = {
            '6h': 6,
            '12h': 12,
            '24h': 24,
            '48h': 48,
            '7d': 168  # 7 days * 24 hours
        }
        
        max_hours = range_hours.get(time_range, 24)
        
        # Filter forecast data
        filtered_data = data.copy()
        forecast_days = data['forecast']['forecastday']
        
        if time_range in ['6h', '12h', '24h']:
            # For short ranges, use hourly data from first day
            if forecast_days and 'hour' in forecast_days[0]:
                filtered_hours = forecast_days[0]['hour'][:max_hours]
                filtered_data['forecast'] = {
                    'forecastday': [{
                        **forecast_days[0],
                        'hour': filtered_hours
                    }]
                }
        elif time_range == '48h':
            # Use first 2 days
            filtered_data['forecast']['forecastday'] = forecast_days[:2]
        else:
            # Use all available days for 7d
            filtered_data['forecast']['forecastday'] = forecast_days
        
        return filtered_data
        
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
    
    def update_location(self, location_data: dict):
        """Update chart with new location information."""
        try:
            # Store location data for future reference
            self.current_location = location_data
            
            # Clear existing data
            self.clear_data()
            
            # Update chart title with new location
            display_name = location_data.get('display', location_data.get('name', 'Unknown Location'))
            self.chart_title = f"Temperature Trends - {display_name}"
            
            # Refresh chart display
            self.refresh_chart_display()
            
            print(f"Temperature chart updated for location: {display_name}")
            
        except Exception as e:
            print(f"Error updating temperature chart location: {e}")
    
    def clear_data(self):
        """Clear all chart data."""
        try:
            # Clear forecast data
            self.forecast_data = None
            
            # Clear stored data
            if hasattr(self, 'data_storage'):
                self.data_storage.clear()
            
            # Clear chart display
            self.clear_chart_data()
            
            # Generate placeholder data for the current timeframe
            placeholder_data = self.generate_realistic_data(self.current_timeframe)
            self.update_data_storage(placeholder_data)
            
        except Exception as e:
            print(f"Error clearing temperature chart data: {e}")
    
    def refresh(self):
        """Refresh the chart display."""
        try:
            if hasattr(self, 'forecast_data') and self.forecast_data:
                # Refresh with existing forecast data
                self.update_forecast(self.forecast_data)
            else:
                # Generate sample data for current timeframe
                sample_data = self.generate_realistic_data(self.current_timeframe)
                self.update_data_storage(sample_data)
                self.refresh_chart_display()
        except Exception as e:
            print(f"Error refreshing temperature chart: {e}")
            
    # Analytics callback handlers
    def _handle_data_point_click(self, point_data: Dict[str, Any]):
        """Handle data point click events."""
        print(f"Data point clicked: {point_data}")
        # Could trigger detailed view, annotation, or other actions
        
    def _handle_zoom_change(self, x_range: tuple, y_range: tuple):
        """Handle zoom change events."""
        print(f"Zoom changed - X: {x_range}, Y: {y_range}")
        # Could update related charts or trigger data loading
        
    def _handle_real_time_update(self):
        """Handle real-time update requests."""
        print("Real-time update requested")
        # Could trigger data refresh from weather service
        if hasattr(self, 'parent') and hasattr(self.parent, 'refresh_weather_data'):
            try:
                self.parent.refresh_weather_data()
            except Exception as e:
                print(f"Error during real-time update: {e}")
    
    def _convert_forecast_objects_to_dict(self, forecast_objects):
        """Convert ForecastData objects to dictionary format for processing.
        
        Args:
            forecast_objects: List of ForecastData objects
            
        Returns:
            Dict with 'list' key containing forecast entries
        """
        try:
            forecast_list = []
            
            for forecast_obj in forecast_objects:
                if hasattr(forecast_obj, 'hourly_forecasts'):
                    for hourly in forecast_obj.hourly_forecasts:
                        entry = {
                            'dt': int(hourly.timestamp.timestamp()),
                            'main': {
                                'temp': hourly.temperature + 273.15,  # Convert to Kelvin
                                'feels_like': getattr(hourly, 'feels_like', hourly.temperature) + 273.15,
                                'humidity': getattr(hourly, 'humidity', 60),
                                'pressure': getattr(hourly, 'pressure', 1013)
                            },
                            'wind': {
                                'speed': getattr(hourly, 'wind_speed', 0) / 3.6  # Convert km/h to m/s
                            },
                            'weather': [{
                                'main': getattr(hourly, 'condition', 'Clear')
                            }]
                        }
                        forecast_list.append(entry)
            
            return {'list': forecast_list}
            
        except Exception as e:
            print(f"Error converting forecast objects: {e}")
            return {'list': []}