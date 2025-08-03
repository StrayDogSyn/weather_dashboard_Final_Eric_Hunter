"""Interactive Weather Maps Widget.

Provides a comprehensive weather mapping interface using Folium maps
embedded in tkinter via tkinterweb.
"""

import asyncio
import logging
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
import tkinterweb

from ...services.enhanced_weather_service import EnhancedWeatherService
from ...services.maps_service import WeatherMapsService
from ...ui.theme import DataTerminalTheme


class InteractiveWeatherMapsWidget(ctk.CTkFrame):
    """Interactive weather maps widget with Folium integration."""

    def __init__(self, parent, weather_service: EnhancedWeatherService, **kwargs):
        super().__init__(parent, **kwargs)

        self.weather_service = weather_service
        self.logger = logging.getLogger(__name__)

        # Initialize maps service
        api_key = getattr(weather_service, "api_key", "demo_key")
        self.maps_service = WeatherMapsService(api_key)

        # Current map state
        self.current_location = (40.7128, -74.0060)  # Default to NYC
        self.current_zoom = 8
        self.active_layers = set()
        self.update_interval = 600  # 10 minutes
        self._destroyed = False
        self._scheduled_tasks = []

        # Temporary file for map HTML
        self.temp_dir = Path(tempfile.gettempdir()) / "weather_maps"
        self.temp_dir.mkdir(exist_ok=True)
        self.current_map_file = None

        # Setup UI
        self._setup_ui()

        # Start auto-update timer
        self._start_auto_update()

        # Load initial map
        self._load_initial_map()

    def _setup_ui(self):
        """Setup the user interface."""
        self.configure(
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )

        # Create main layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Left control panel
        self._create_control_panel()

        # Right map display
        self._create_map_display()

        # Bottom status bar
        self._create_status_bar()

    def _create_control_panel(self):
        """Create left control panel."""
        self.control_panel = ctk.CTkScrollableFrame(
            self, width=300, fg_color=DataTerminalTheme.CARD_BG, corner_radius=8
        )
        self.control_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(10, 5), pady=10)

        # Title
        title_label = ctk.CTkLabel(
            self.control_panel,
            text="🗺️ Weather Maps",
            font=(DataTerminalTheme.FONT_FAMILY, 20, "bold"),
            text_color=DataTerminalTheme.ACCENT,
        )
        title_label.pack(pady=(10, 20))

        # Location section
        self._create_location_section()

        # Layer controls
        self._create_layer_controls()

        # Map tools
        self._create_map_tools()

        # Weather stations
        self._create_weather_stations_section()

        # Severe weather
        self._create_severe_weather_section()

        # Settings
        self._create_settings_section()

    def _create_location_section(self):
        """Create location input section."""
        location_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        location_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            location_frame,
            text="📍 Location",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(anchor="w", pady=(0, 5))

        # Location entry
        self.location_entry = ctk.CTkEntry(
            location_frame,
            placeholder_text="Enter city or coordinates...",
            height=35,
            fg_color=DataTerminalTheme.BACKGROUND,
            text_color=DataTerminalTheme.TEXT,
            border_color=DataTerminalTheme.BORDER,
        )
        self.location_entry.pack(fill="x", pady=(0, 5))
        self.location_entry.bind("<Return>", lambda e: self._search_location())

        # Location buttons
        location_buttons_frame = ctk.CTkFrame(location_frame, fg_color="transparent")
        location_buttons_frame.pack(fill="x")

        search_btn = ctk.CTkButton(
            location_buttons_frame,
            text="Search",
            command=self._search_location,
            width=80,
            height=30,
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.SUCCESS,
        )
        search_btn.pack(side="left", padx=(0, 5))

        current_btn = ctk.CTkButton(
            location_buttons_frame,
            text="Current",
            command=self._go_to_current_location,
            width=80,
            height=30,
            fg_color=DataTerminalTheme.SUCCESS,
            hover_color=DataTerminalTheme.PRIMARY,
        )
        current_btn.pack(side="left")

    def _create_layer_controls(self):
        """Create weather layer controls."""
        layers_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        layers_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            layers_frame,
            text="🌡️ Weather Layers",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(anchor="w", pady=(0, 10))

        # Layer checkboxes
        self.layer_vars = {}
        layers = [
            ("temperature", "🌡️ Temperature", True),
            ("precipitation", "🌧️ Precipitation", False),
            ("wind", "💨 Wind Speed", False),
            ("pressure", "📊 Pressure", False),
            ("clouds", "☁️ Clouds", False),
        ]

        for layer_id, label, default in layers:
            var = ctk.BooleanVar(value=default)
            self.layer_vars[layer_id] = var
            if default:
                self.active_layers.add(layer_id)

            checkbox = ctk.CTkCheckBox(
                layers_frame,
                text=label,
                variable=var,
                command=lambda lid=layer_id: self._toggle_layer(lid),
                text_color=DataTerminalTheme.TEXT,
                fg_color=DataTerminalTheme.PRIMARY,
                hover_color=DataTerminalTheme.SUCCESS,
            )
            checkbox.pack(anchor="w", pady=2)

    def _create_map_tools(self):
        """Create map interaction tools."""
        tools_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        tools_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            tools_frame,
            text="🛠️ Map Tools",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(anchor="w", pady=(0, 10))

        # Tool buttons
        tools = [
            ("🎯 Zoom to Fit", self._zoom_to_fit),
            ("📏 Measure Distance", self._enable_measurement),
            ("✏️ Draw Region", self._enable_drawing),
            ("🔄 Refresh Map", self._refresh_map),
        ]

        for text, command in tools:
            btn = ctk.CTkButton(
                tools_frame,
                text=text,
                command=command,
                height=30,
                fg_color=DataTerminalTheme.SUCCESS,
                hover_color=DataTerminalTheme.PRIMARY,
                text_color=DataTerminalTheme.TEXT,
            )
            btn.pack(fill="x", pady=2)

    def _create_weather_stations_section(self):
        """Create weather stations section."""
        stations_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        stations_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            stations_frame,
            text="🏢 Weather Stations",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(anchor="w", pady=(0, 10))

        # Show stations checkbox
        self.show_stations_var = ctk.BooleanVar(value=True)
        stations_checkbox = ctk.CTkCheckBox(
            stations_frame,
            text="Show Nearby Stations",
            variable=self.show_stations_var,
            command=self._toggle_weather_stations,
            text_color=DataTerminalTheme.TEXT,
            fg_color=DataTerminalTheme.PRIMARY,
        )
        stations_checkbox.pack(anchor="w", pady=2)

        # Station radius
        radius_frame = ctk.CTkFrame(stations_frame, fg_color="transparent")
        radius_frame.pack(fill="x", pady=(5, 0))

        ctk.CTkLabel(
            radius_frame, text="Search Radius (km):", text_color=DataTerminalTheme.TEXT_SECONDARY
        ).pack(anchor="w")

        self.station_radius_var = ctk.StringVar(value="50")
        radius_entry = ctk.CTkEntry(
            radius_frame,
            textvariable=self.station_radius_var,
            width=100,
            height=25,
            fg_color=DataTerminalTheme.BACKGROUND,
        )
        radius_entry.pack(anchor="w", pady=(2, 0))

    def _create_severe_weather_section(self):
        """Create severe weather alerts section."""
        alerts_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        alerts_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            alerts_frame,
            text="⚠️ Severe Weather",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(anchor="w", pady=(0, 10))

        # Alert types
        alert_types = [
            ("alerts", "🚨 Active Alerts", True),
            ("storms", "🌪️ Storm Tracking", False),
            ("extreme_temp", "🔥 Extreme Temperatures", False),
            ("wildfire", "🔥 Wildfire Smoke", False),
        ]

        self.alert_vars = {}
        for alert_id, label, default in alert_types:
            var = ctk.BooleanVar(value=default)
            self.alert_vars[alert_id] = var

            checkbox = ctk.CTkCheckBox(
                alerts_frame,
                text=label,
                variable=var,
                command=lambda aid=alert_id: self._toggle_alert_layer(aid),
                text_color=DataTerminalTheme.TEXT,
                fg_color=DataTerminalTheme.ERROR,
                hover_color=DataTerminalTheme.WARNING,
            )
            checkbox.pack(anchor="w", pady=2)

    def _create_settings_section(self):
        """Create settings section."""
        settings_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        settings_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            settings_frame,
            text="⚙️ Settings",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(anchor="w", pady=(0, 10))

        # Auto-update
        self.auto_update_var = ctk.BooleanVar(value=True)
        auto_update_checkbox = ctk.CTkCheckBox(
            settings_frame,
            text="Auto-update (10 min)",
            variable=self.auto_update_var,
            command=self._toggle_auto_update,
            text_color=DataTerminalTheme.TEXT,
            fg_color=DataTerminalTheme.PRIMARY,
        )
        auto_update_checkbox.pack(anchor="w", pady=2)

        # Cache tiles
        self.cache_tiles_var = ctk.BooleanVar(value=True)
        cache_checkbox = ctk.CTkCheckBox(
            settings_frame,
            text="Cache Tiles (Offline)",
            variable=self.cache_tiles_var,
            text_color=DataTerminalTheme.TEXT,
            fg_color=DataTerminalTheme.PRIMARY,
        )
        cache_checkbox.pack(anchor="w", pady=2)

    def _create_map_display(self):
        """Create map display area."""
        map_frame = ctk.CTkFrame(self, fg_color=DataTerminalTheme.CARD_BG, corner_radius=8)
        map_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(10, 5))
        map_frame.grid_columnconfigure(0, weight=1)
        map_frame.grid_rowconfigure(0, weight=1)

        # Map title
        map_title = ctk.CTkLabel(
            map_frame,
            text="Interactive Weather Map",
            font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
            text_color=DataTerminalTheme.ACCENT,
        )
        map_title.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        # Web view for map
        try:
            self.map_webview = tkinterweb.HtmlFrame(map_frame, messages_enabled=False)
            self.map_webview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
            map_frame.grid_rowconfigure(1, weight=1)
        except Exception as e:
            self.logger.error(f"Failed to create web view: {e}")
            # Fallback to label
            self.map_webview = ctk.CTkLabel(
                map_frame,
                text="Map display not available\nPlease check tkinterweb installation",
                text_color=DataTerminalTheme.ERROR,
            )
            self.map_webview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = ctk.CTkFrame(
            self, height=30, fg_color=DataTerminalTheme.CARD_BG, corner_radius=8
        )
        self.status_bar.grid(row=1, column=1, sticky="ew", padx=(5, 10), pady=(5, 10))

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready - Click on map for weather data",
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        # Last update time
        self.last_update_label = ctk.CTkLabel(
            self.status_bar,
            text="",
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
        )
        self.last_update_label.pack(side="right", padx=10, pady=5)

    def _load_initial_map(self):
        """Load initial map."""
        threading.Thread(target=self._load_map_async, daemon=True).start()

    def _load_map_async(self):
        """Load map asynchronously."""
        try:
            # Check if widget is destroyed
            if self._destroyed:
                return

            self._update_status("Loading map...")

            # Create comprehensive weather map
            map_obj = self.maps_service.create_comprehensive_weather_map(
                center_lat=self.current_location[0],
                center_lon=self.current_location[1],
                zoom=self.current_zoom,
                include_all_layers=False,  # We'll add layers based on user selection
            )

            # Check if widget is destroyed before continuing
            if self._destroyed:
                return

            # Add selected layers
            if "temperature" in self.active_layers:
                map_obj = self.maps_service.add_temperature_layer(map_obj)

            # Add weather stations if enabled
            if self.show_stations_var.get():
                stations = asyncio.run(
                    self.maps_service.get_weather_stations(
                        self.current_location[0],
                        self.current_location[1],
                        int(self.station_radius_var.get()),
                    )
                )
                map_obj = self.maps_service.add_weather_stations_layer(map_obj, stations)

            # Add weather alerts if enabled
            if self.alert_vars.get("alerts", ctk.BooleanVar()).get():
                alerts = asyncio.run(
                    self.maps_service.get_weather_alerts(
                        self.current_location[0], self.current_location[1]
                    )
                )
                map_obj = self.maps_service.add_weather_alerts_layer(map_obj, alerts)

            # Check if widget is destroyed before saving
            if self._destroyed:
                return

            # Save map to temporary file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"weather_map_{timestamp}.html"
            self.current_map_file = self.maps_service.save_map(map_obj, filename)

            # Load in web view only if not destroyed
            if not self._destroyed:
                self._safe_after(0, self._display_map)

        except Exception as e:
            self.logger.error(f"Failed to load map: {e}")
            if not self._destroyed:
                error_msg = str(e)
                self._safe_after(0, lambda: self._update_status(f"Error loading map: {error_msg}"))

    def _display_map(self):
        """Display map in web view."""
        try:
            if self._destroyed:
                return

            if self.current_map_file and os.path.exists(self.current_map_file):
                if hasattr(self.map_webview, "load_file"):
                    # Check if file is readable and has content
                    with open(self.current_map_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        if len(content) > 100:  # Basic check for valid HTML content
                            self.map_webview.load_file(self.current_map_file)
                            self._update_status("Map loaded successfully")
                            self._update_last_update_time()
                        else:
                            self._show_fallback_map("Generated map file is empty or corrupted")
                else:
                    self._show_fallback_map("Web view not available")
            else:
                self._show_fallback_map("Map file not found")

        except Exception as e:
            self.logger.error(f"Failed to display map: {e}")
            self._show_fallback_map(f"Error displaying map: {e}")

    def _show_fallback_map(self, error_msg: str):
        """Show fallback content when map cannot be displayed."""
        try:
            if hasattr(self.map_webview, "load_html"):
                fallback_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Weather Map</title>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                            color: white;
                            margin: 0;
                            padding: 20px;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            min-height: 100vh;
                            text-align: center;
                        }}
                        .container {{
                            background: rgba(255, 255, 255, 0.1);
                            padding: 30px;
                            border-radius: 15px;
                            backdrop-filter: blur(10px);
                            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                        }}
                        h1 {{ color: #00d4ff; margin-bottom: 20px; }}
                        .error {{ color: #ff6b6b; margin: 15px 0; }}
                        .info {{ color: #4ecdc4; margin: 10px 0; }}
                        .location {{ color: #ffe66d; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🗺️ Weather Map</h1>
                        <div class="error">⚠️ {error_msg}</div>
                        <div class="info">📍 Current Location:</div>
                        <div class="location">{self.current_location[0]:.4f}, {self.current_location[1]:.4f}</div>
                        <div class="info">🔄 Attempting to reload map...</div>
                    </div>
                </body>
                </html>
                """
                self.map_webview.load_html(fallback_html)
            self._update_status(f"Map error: {error_msg}")
        except Exception as e:
            self.logger.error(f"Failed to show fallback map: {e}")
            self._update_status(f"Critical map error: {e}")

    def _search_location(self):
        """Search for location and update map."""
        location = self.location_entry.get().strip()
        if not location:
            return

        threading.Thread(target=self._search_location_async, args=(location,), daemon=True).start()

    def _search_location_async(self, location: str):
        """Search location asynchronously."""
        try:
            if self._destroyed:
                return

            self._update_status(f"Searching for {location}...")

            coords = asyncio.run(self.maps_service.geocode_location(location))
            if coords and not self._destroyed:
                self.current_location = coords
                self._safe_after(0, self._refresh_map)
                self._safe_after(0, lambda: self._update_status(f"Found {location}"))
            elif not self._destroyed:
                self._safe_after(0, lambda: self._update_status(f"Location '{location}' not found"))

        except Exception as e:
            self.logger.error(f"Failed to search location: {e}")
            if not self._destroyed:
                error_msg = str(e)
                self._safe_after(0, lambda: self._update_status(f"Search error: {error_msg}"))

    def _go_to_current_location(self):
        """Go to current GPS location."""
        # In a real implementation, this would use GPS
        # For now, we'll use a default location
        self.current_location = (40.7128, -74.0060)  # NYC
        self._refresh_map()
        self._update_status("Moved to current location")

    def _toggle_layer(self, layer_id: str):
        """Toggle weather layer."""
        if self.layer_vars[layer_id].get():
            self.active_layers.add(layer_id)
        else:
            self.active_layers.discard(layer_id)

        self._refresh_map()

    def _toggle_alert_layer(self, alert_id: str):
        """Toggle alert layer."""
        self._refresh_map()

    def _toggle_weather_stations(self):
        """Toggle weather stations display."""
        self._refresh_map()

    def _toggle_auto_update(self):
        """Toggle auto-update."""
        if self.auto_update_var.get():
            self._start_auto_update()

    def _zoom_to_fit(self):
        """Zoom to fit all data."""
        self._update_status("Zooming to fit data...")
        # Implementation would adjust zoom level

    def _enable_measurement(self):
        """Enable measurement tools."""
        self._update_status("Measurement tools enabled - check map")

    def _enable_drawing(self):
        """Enable drawing tools."""
        self._update_status("Drawing tools enabled - check map")

    def _refresh_map(self):
        """Refresh the map with current settings."""
        threading.Thread(target=self._load_map_async, daemon=True).start()

    def _start_auto_update(self):
        """Start auto-update timer."""
        if hasattr(self, "auto_update_var") and self.auto_update_var.get() and not self._destroyed:
            task_id = self._safe_after(self.update_interval * 1000, self._auto_update)
            if task_id:
                self._scheduled_tasks.append(task_id)

    def _auto_update(self):
        """Auto-update map data."""
        if self._destroyed:
            return

        if hasattr(self, "auto_update_var") and self.auto_update_var.get():
            self._refresh_map()
            self._start_auto_update()

    def _update_status(self, message: str):
        """Update status bar message."""
        try:
            if (
                not self._destroyed
                and hasattr(self, "status_label")
                and self.status_label.winfo_exists()
            ):
                self.status_label.configure(text=message)
        except Exception:
            # Widget no longer exists
            self._destroyed = True

    def _update_last_update_time(self):
        """Update last update time."""
        try:
            if (
                not self._destroyed
                and hasattr(self, "last_update_label")
                and self.last_update_label.winfo_exists()
            ):
                current_time = datetime.now().strftime("%H:%M:%S")
                self.last_update_label.configure(text=f"Updated: {current_time}")
        except Exception:
            # Widget no longer exists
            self._destroyed = True

    def _safe_after(self, delay, callback):
        """Safely schedule a callback, checking if widget still exists."""
        try:
            if not self._destroyed and self.winfo_exists():
                return self.after(delay, callback)
        except Exception:
            # Widget no longer exists
            self._destroyed = True
        return None

    def cleanup(self):
        """Cleanup resources."""
        try:
            self._destroyed = True

            # Cancel all scheduled tasks
            for task_id in self._scheduled_tasks:
                try:
                    self.after_cancel(task_id)
                except Exception:
                    pass
            self._scheduled_tasks.clear()

            # Clean up temporary files
            if self.current_map_file and os.path.exists(self.current_map_file):
                os.remove(self.current_map_file)

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

    def destroy(self):
        """Override destroy to ensure cleanup."""
        self.cleanup()
        super().destroy()
