"""Thread-Safe Google Maps Widget for Weather Dashboard.

Provides a comprehensive Google Maps JavaScript API integration with:
- Thread-safe UI updates using SafeWidget base class
- Proper JavaScript-to-Python communication
- Asynchronous map updates without blocking UI
- Robust error handling and fallback mechanisms
"""

import json
import logging
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

try:
    import tkinterweb
import customtkinter as ctk
    TKINTERWEB_AVAILABLE = True
except ImportError:
    TKINTERWEB_AVAILABLE = False
    
try:
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False

from ..safe_widgets import SafeWidget
from ...services.weather import EnhancedWeatherService
from ...services.config.config_service import ConfigService
from .static_map_fallback import StaticMapFallback

class ThreadSafeGoogleMapsWidget(SafeWidget, ctk.CTkFrame):
    """Thread-safe Google Maps widget with comprehensive error handling."""

    def __init__(self, parent, weather_service: EnhancedWeatherService, 
                 config_service: ConfigService, **kwargs):
        # Initialize both parent classes
        SafeWidget.__init__(self)
        ctk.CTkFrame.__init__(self, parent, **kwargs)
        
        self.weather_service = weather_service
        self.config_service = config_service
        self.logger = logging.getLogger(__name__)
        
        # Thread-safe state management
        self._initialization_lock = threading.Lock()
        self._is_initialized = False
        self._is_destroyed = False
        self._pending_operations = []
        
        # Map state
        self.api_key = self._get_api_key_safely()
        self.current_location = (40.7128, -74.0060)  # Default to NYC
        self.current_zoom = 8
        self.active_layers = set()
        
        # Enhanced map state management
        self._current_location = {'lat': 40.7128, 'lng': -74.0060}  # Default to NYC
        self._current_zoom = 10
        self._current_map_type = 'roadmap'
        self._search_debounce_timer = None
        
        # Click handler callbacks
        self._click_handlers: List[Callable] = []
        
        # Initialize weather overlay system
        self.weather_overlay = None
        if weather_service:
            try:
                # Import here to avoid circular imports
                from .weather_map_overlay import WeatherMapOverlay, WeatherPoint
                self.weather_overlay = WeatherMapOverlay(self, weather_service, self.logger)
                self.logger.info("Weather overlay system initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize weather overlay: {e}")
        
        # WebView components
        self.webview_container = None
        self.map_webview = None
        self.webview_window = None
        
        # File management
        self.temp_dir = Path(tempfile.gettempdir()) / "thread_safe_maps"
        self.current_map_file = None
        
        # JavaScript communication
        self._js_callbacks = {}
        self._message_queue = []
        self._communication_ready = False
        
        # Error handling
        self._error_count = 0
        self._max_retries = 3
        self._fallback_active = False
        
        self.logger.info("ThreadSafeGoogleMapsWidget initializing...")
        
        # Start safe initialization
        self.safe_after_idle(self._initialize_widget)
    
    def _get_api_key_safely(self) -> str:
        """Safely retrieve Google Maps API key with fallbacks."""
        try:
            if self.config_service:
                api_key = self.config_service.get_setting("api.google_maps_api_key")
                if api_key and api_key.strip():
                    return api_key.strip()
            
            # Fallback to environment variable
            env_key = os.getenv("GOOGLE_MAPS_API_KEY")
            if env_key and env_key.strip():
                return env_key.strip()
            
            self.logger.warning("No Google Maps API key found. Using demo mode.")
            return "demo_key"
            
        except Exception as e:
            self.logger.error(f"Error retrieving API key: {e}")
            return "demo_key"
    
    def _initialize_widget(self):
        """Thread-safe widget initialization."""
        with self._initialization_lock:
            if self._is_initialized or self._is_destroyed:
                return
            
            try:
                self._setup_ui_components()
                self._setup_temp_directory()
                self._initialize_webview()
                self._is_initialized = True
                
                # Process any pending operations
                self._process_pending_operations()
                
                self.logger.info("ThreadSafeGoogleMapsWidget initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize widget: {e}")
                self._show_initialization_error(str(e))
    
    def _setup_ui_components(self):
        """Set up the UI components safely."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create header with controls
        self._create_header()
        
        # Create main map container
        self._create_map_container()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create the header with map controls."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🗺️ Google Maps - Weather View",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Controls frame
        controls_frame = ctk.CTkFrame(header_frame)
        controls_frame.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Search entry
        self.search_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="Search location...",
            width=200
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self._safe_search_location())
        
        # Search button
        search_btn = ctk.CTkButton(
            controls_frame,
            text="🔍",
            width=30,
            command=self._safe_search_location
        )
        search_btn.pack(side="left", padx=2)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄",
            width=30,
            command=self._safe_refresh_map
        )
        refresh_btn.pack(side="left", padx=2)
        
        # Current location button
        location_btn = ctk.CTkButton(
            controls_frame,
            text="📍",
            width=30,
            command=self._safe_go_to_current_location
        )
        location_btn.pack(side="left", padx=2)
    
    def _create_map_container(self):
        """Create the main map container."""
        self.webview_container = ctk.CTkFrame(self, fg_color="white")
        self.webview_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.webview_container.grid_columnconfigure(0, weight=1)
        self.webview_container.grid_rowconfigure(0, weight=1)
        
        # Initially show loading message
        self.loading_label = ctk.CTkLabel(
            self.webview_container,
            text="🔄 Initializing Google Maps...",
            font=ctk.CTkFont(size=14)
        )
        self.loading_label.grid(row=0, column=0, sticky="nsew")
    
    def _create_status_bar(self):
        """Create the status bar."""
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Layer controls
        layers_frame = ctk.CTkFrame(status_frame)
        layers_frame.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Weather layer toggles
        self.layer_vars = {}
        layer_names = ["Temperature", "Precipitation", "Wind", "Clouds"]
        
        for i, layer in enumerate(layer_names):
            var = ctk.BooleanVar()
            self.layer_vars[layer.lower()] = var
            
            checkbox = ctk.CTkCheckBox(
                layers_frame,
                text=layer,
                variable=var,
                command=lambda l=layer.lower(): self._safe_toggle_layer(l)
            )
            checkbox.pack(side="left", padx=5)
    
    def _setup_temp_directory(self):
        """Set up temporary directory for HTML files."""
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Temp directory ready: {self.temp_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create temp directory: {e}")
            # Use system temp as fallback
            self.temp_dir = Path(tempfile.gettempdir())
    
    def _initialize_webview(self):
        """Initialize the webview component with proper error handling."""
        if not TKINTERWEB_AVAILABLE:
            self.logger.warning("tkinterweb not available, using static fallback")
            self._initialize_static_fallback()
            return
        
        try:
            # Create the HTML frame
            self.map_webview = tkinterweb.HtmlFrame(
                self.webview_container,
                messages_enabled=True
            )
            self.map_webview.grid(row=0, column=0, sticky="nsew")
            
            # Set up JavaScript communication
            self._setup_js_communication()
            
            # Load initial map
            self.safe_after(1000, self._load_initial_map)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize webview: {e}")
            self._initialize_static_fallback()
    
    def _setup_js_communication(self):
        """Set up JavaScript-to-Python communication."""
        if not self.map_webview:
            return
        
        try:
            # Register message handler - check if method exists
            if hasattr(self.map_webview, 'add_message_handler'):
                self.map_webview.add_message_handler(self._handle_js_message)
            elif hasattr(self.map_webview, 'bind'):
                # Alternative approach for tkinterweb
                self.map_webview.bind('<Button-1>', self._handle_map_click)
            
            # Register common callbacks
            self._js_callbacks.update({
                'map_ready': self._on_map_ready,
                'location_changed': self._on_location_changed,
                'layer_toggled': self._on_layer_toggled,
                'error_occurred': self._on_js_error
            })
            
            self.logger.info("JavaScript communication set up")
            
        except Exception as e:
            self.logger.error(f"Failed to set up JS communication: {e}")
    
    def _handle_js_message(self, message):
        """Handle messages from JavaScript (thread-safe)."""
        def _process_message():
            try:
                if isinstance(message, str):
                    data = json.loads(message)
                else:
                    data = message
                
                callback_name = data.get('type')
                callback_data = data.get('data', {})
                
                if callback_name in self._js_callbacks:
                    self._js_callbacks[callback_name](callback_data)
                else:
                    self.logger.warning(f"Unknown JS message type: {callback_name}")
                    
            except Exception as e:
                self.logger.error(f"Error processing JS message: {e}")
        
        # Process message on main thread
        self.safe_after_idle(_process_message)
    
    def _handle_map_click(self, event):
        """Handle map click events (fallback for tkinterweb)."""
        try:
            # Basic click handling for tkinterweb compatibility
            self.logger.debug(f"Map clicked at coordinates: {event.x}, {event.y}")
        except Exception as e:
            self.logger.error(f"Error handling map click: {e}")
    
    def _load_initial_map(self):
        """Load the initial Google Maps view."""
        if self._is_destroyed:
            return
        
        try:
            self._update_status("Loading Google Maps...")
            
            # Create HTML file
            html_content = self._generate_map_html()
            self.current_map_file = self.temp_dir / f"map_{int(time.time())}.html"
            
            with open(self.current_map_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Load in webview
            if self.map_webview:
                self.map_webview.load_file(str(self.current_map_file))
                
                # Hide loading label
                if hasattr(self, 'loading_label'):
                    self.loading_label.grid_remove()
                
                self._update_status("Google Maps loaded")
                
                # Set up map ready check
                self.safe_after(3000, self._check_map_ready)
            
        except Exception as e:
            self.logger.error(f"Failed to load initial map: {e}")
            self._handle_map_error(str(e))
    
    def _generate_map_html(self) -> str:
        """Generate the HTML content for Google Maps."""
        # Get active weather layers
        active_layers = [layer for layer, var in self.layer_vars.items() if var.get()]
        weather_overlays = self._generate_weather_overlays(active_layers)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Google Maps Weather</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                html, body {{
                    height: 100%;
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                }}
                #map {{
                    height: 100%;
                    width: 100%;
                }}
                .weather-info {{
                    background: white;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    font-size: 14px;
                    max-width: 300px;
                }}
                .loading {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                    text-align: center;
                    z-index: 1000;
                }}
            </style>
        </head>
        <body>
            <div id="loading" class="loading">
                <div>🗺️ Loading Google Maps...</div>
                <div style="margin-top: 10px; font-size: 12px; color: #666;">
                    Please wait while we initialize the map...
                </div>
            </div>
            <div id="map"></div>
            
            <script>
                let map;
                let markers = [];
                let weatherLayers = {{}};
                
                // Communication with Python
                function sendMessage(type, data) {{
                    try {{
                        const message = JSON.stringify({{ type: type, data: data }});
                        if (window.tkinter_web) {{
                            window.tkinter_web.send_message(message);
                        }}
                    }} catch (error) {{
                        console.error('Failed to send message:', error);
                    }}
                }}
                
                function initMap() {{
                    try {{
                        // Hide loading indicator
                        const loading = document.getElementById('loading');
                        if (loading) loading.style.display = 'none';
                        
                        // Initialize map
                        map = new google.maps.Map(document.getElementById('map'), {{
                            center: {{ lat: {self.current_location[0]}, lng: {self.current_location[1]} }},
                            zoom: {self.current_zoom},
                            mapTypeId: 'roadmap'
                        }});
                        
                        // Add weather overlays
                        {weather_overlays}
                        
                        // Set up event listeners
                        map.addListener('center_changed', function() {{
                            const center = map.getCenter();
                            sendMessage('location_changed', {{
                                lat: center.lat(),
                                lng: center.lng(),
                                zoom: map.getZoom()
                            }});
                        }});
                        
                        // Notify Python that map is ready
                        sendMessage('map_ready', {{ status: 'initialized' }});
                        
                    }} catch (error) {{
                        console.error('Map initialization error:', error);
                        sendMessage('error_occurred', {{ error: error.message }});
                        document.getElementById('loading').innerHTML = 
                            '<div>⚠️ Google Maps Error</div><div style="font-size: 12px; margin-top: 10px;">' + 
                            error.message + '</div>';
                    }}
                }}
                
                function handleApiError() {{
                    document.getElementById('loading').innerHTML = 
                        '<div>⚠️ Google Maps API Error</div><div style="font-size: 12px; margin-top: 10px;">' +
                        'Please check your API key and internet connection</div>';
                    sendMessage('error_occurred', {{ error: 'API load failed' }});
                }}
                
                // Weather layer functions
                function toggleWeatherLayer(layerType, enabled) {{
                    if (enabled && !weatherLayers[layerType]) {{
                        // Add layer logic here
                        sendMessage('layer_toggled', {{ layer: layerType, enabled: true }});
                    }} else if (!enabled && weatherLayers[layerType]) {{
                        // Remove layer logic here
                        sendMessage('layer_toggled', {{ layer: layerType, enabled: false }});
                    }}
                }}
            </script>
            
            <script async defer 
                src="https://maps.googleapis.com/maps/api/js?key={self.api_key}&callback=initMap&libraries=geometry"
                onerror="handleApiError()">
            </script>
        </body>
        </html>
        """
    
    def _generate_weather_overlays(self, active_layers: List[str]) -> str:
        """Generate JavaScript code for weather overlays."""
        overlays = []
        
        for layer in active_layers:
            if layer == 'temperature':
                overlays.append("""
                    weatherLayers.temperature = new google.maps.ImageMapType({
                        getTileUrl: function(coord, zoom) {
                            return `https://tile.openweathermap.org/map/temp_new/${zoom}/${coord.x}/${coord.y}.png?appid=YOUR_API_KEY`;
                        },
                        tileSize: new google.maps.Size(256, 256),
                        maxZoom: 18,
                        minZoom: 0,
                        name: 'Temperature'
                    });
                    map.overlayMapTypes.push(weatherLayers.temperature);
                """)
            
            elif layer == 'precipitation':
                overlays.append("""
                    weatherLayers.precipitation = new google.maps.ImageMapType({
                        getTileUrl: function(coord, zoom) {
                            return `https://tile.openweathermap.org/map/precipitation_new/${zoom}/${coord.x}/${coord.y}.png?appid=YOUR_API_KEY`;
                        },
                        tileSize: new google.maps.Size(256, 256),
                        maxZoom: 18,
                        minZoom: 0,
                        name: 'Precipitation'
                    });
                    map.overlayMapTypes.push(weatherLayers.precipitation);
                """)
        
        return '\n'.join(overlays)
    
    # JavaScript callback handlers (all thread-safe)
    def _on_map_ready(self, data):
        """Handle map ready callback."""
        self._communication_ready = True
        self._update_status("Google Maps ready")
        self.logger.info("Google Maps initialized successfully")
    
    def _on_location_changed(self, data):
        """Handle location change callback."""
        try:
            self.current_location = (data['lat'], data['lng'])
            self.current_zoom = data['zoom']
            self.logger.debug(f"Location changed: {self.current_location}, zoom: {self.current_zoom}")
        except KeyError as e:
            self.logger.error(f"Invalid location data: {e}")
    
    def _on_layer_toggled(self, data):
        """Handle layer toggle callback."""
        try:
            layer = data['layer']
            enabled = data['enabled']
            self.logger.info(f"Layer {layer} {'enabled' if enabled else 'disabled'}")
        except KeyError as e:
            self.logger.error(f"Invalid layer data: {e}")
    
    def _on_js_error(self, data):
        """Handle JavaScript error callback."""
        error_msg = data.get('error', 'Unknown JavaScript error')
        self.logger.error(f"JavaScript error: {error_msg}")
        self._handle_map_error(f"JavaScript error: {error_msg}")
    
    # Thread-safe public methods
    def _safe_search_location(self):
        """Thread-safe location search."""
        def _search():
            try:
                location = self.search_entry.get().strip()
                if not location:
                    return
                
                self._update_status(f"Searching for {location}...")
                # Implement geocoding here
                self.logger.info(f"Searching for location: {location}")
                
            except Exception as e:
                self.logger.error(f"Search error: {e}")
                self._update_status("Search failed")
        
        self.safe_after_idle(_search)
    
    def _safe_refresh_map(self):
        """Thread-safe map refresh."""
        def _refresh():
            try:
                if self._is_destroyed:
                    return
                
                self._update_status("Refreshing map...")
                
                # Regenerate HTML and reload
                html_content = self._generate_map_html()
                if self.current_map_file:
                    with open(self.current_map_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    if self.map_webview:
                        self.map_webview.load_file(str(self.current_map_file))
                
                self._update_status("Map refreshed")
                
            except Exception as e:
                self.logger.error(f"Refresh error: {e}")
                self._update_status("Refresh failed")
        
        self.safe_after_idle(_refresh)
    
    def _safe_go_to_current_location(self):
        """Thread-safe current location navigation."""
        def _go_to_location():
            try:
                # Implement geolocation here
                self._update_status("Getting current location...")
                self.logger.info("Navigating to current location")
                
            except Exception as e:
                self.logger.error(f"Location error: {e}")
                self._update_status("Location unavailable")
        
        self.safe_after_idle(_go_to_location)
    
    def _safe_toggle_layer(self, layer_name: str):
        """Thread-safe layer toggle."""
        def _toggle():
            try:
                enabled = self.layer_vars[layer_name].get()
                
                if self._communication_ready and self.map_webview:
                    # Send command to JavaScript
                    js_code = f"toggleWeatherLayer('{layer_name}', {str(enabled).lower()});"
                    self.map_webview.evaluate_js(js_code)
                
                self.logger.info(f"Layer {layer_name} {'enabled' if enabled else 'disabled'}")
                
            except Exception as e:
                self.logger.error(f"Layer toggle error: {e}")
        
        self.safe_after_idle(_toggle)
    
    # Error handling and fallback methods
    def _handle_map_error(self, error_msg: str):
        """Handle map errors with appropriate fallbacks."""
        self._error_count += 1
        
        if self._error_count <= self._max_retries and not self._fallback_active:
            self.logger.warning(f"Map error (attempt {self._error_count}): {error_msg}")
            self._update_status(f"Retrying... ({self._error_count}/{self._max_retries})")
            self.safe_after(2000, self._load_initial_map)
        else:
            self.logger.error(f"Map failed after {self._max_retries} attempts: {error_msg}")
            self._show_fallback_map(error_msg)
    
    def _show_fallback_map(self, error_msg: str):
        """Show fallback content when maps fail."""
        self._fallback_active = True
        
        # Clear existing content
        for widget in self.webview_container.winfo_children():
            widget.destroy()
        
        # Create fallback content
        fallback_frame = ctk.CTkFrame(self.webview_container)
        fallback_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        fallback_frame.grid_columnconfigure(0, weight=1)
        
        # Error message
        error_label = ctk.CTkLabel(
            fallback_frame,
            text="🗺️ Google Maps Unavailable",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        error_label.grid(row=0, column=0, pady=10)
        
        details_label = ctk.CTkLabel(
            fallback_frame,
            text=f"Error: {error_msg}\n\nPlease check your internet connection and API key.",
            font=ctk.CTkFont(size=12),
            wraplength=400
        )
        details_label.grid(row=1, column=0, pady=10)
        
        # Retry button
        retry_btn = ctk.CTkButton(
            fallback_frame,
            text="🔄 Retry",
            command=self._retry_initialization
        )
        retry_btn.grid(row=2, column=0, pady=10)
        
        self._update_status("Maps unavailable - using fallback")
    
    def _show_webview_unavailable(self):
        """Show message when webview is unavailable."""
        for widget in self.webview_container.winfo_children():
            widget.destroy()
        
        unavailable_label = ctk.CTkLabel(
            self.webview_container,
            text="🗺️ Google Maps\n\nWebView component unavailable.\nPlease install tkinterweb for full functionality.",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        unavailable_label.grid(row=0, column=0, sticky="nsew")
        
        self._update_status("WebView unavailable")
    
    def _show_webview_error(self, error_msg: str):
        """Show webview initialization error."""
        for widget in self.webview_container.winfo_children():
            widget.destroy()
        
        error_label = ctk.CTkLabel(
            self.webview_container,
            text=f"🗺️ Google Maps\n\nWebView Error: {error_msg}\n\nUsing fallback display.",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        error_label.grid(row=0, column=0, sticky="nsew")
        
        self._update_status(f"WebView error: {error_msg}")
    
    def _show_initialization_error(self, error_msg: str):
        """Show initialization error."""
        for widget in self.webview_container.winfo_children():
            widget.destroy()
        
        error_label = ctk.CTkLabel(
            self.webview_container,
            text=f"🗺️ Google Maps\n\nInitialization Error: {error_msg}\n\nPlease try refreshing.",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        error_label.grid(row=0, column=0, sticky="nsew")
        
        self._update_status(f"Initialization error: {error_msg}")
    
    def _retry_initialization(self):
        """Retry widget initialization."""
        self._error_count = 0
        self._fallback_active = False
        self._is_initialized = False
        
        # Clear container
        for widget in self.webview_container.winfo_children():
            widget.destroy()
        
        # Show loading message
        self.loading_label = ctk.CTkLabel(
            self.webview_container,
            text="🔄 Retrying initialization...",
            font=ctk.CTkFont(size=14)
        )
        self.loading_label.grid(row=0, column=0, sticky="nsew")
        
        # Restart initialization
        self.safe_after(1000, self._initialize_widget)
    
    def _check_map_ready(self):
        """Check if map is ready and functional."""
        if self._communication_ready:
            self.logger.info("Map communication verified")
            return
        
        # For demo purposes, assume map is ready after timeout
        self.logger.info("Map assumed ready for demo (communication fallback)")
        self._communication_ready = True
        self._update_status("Google Maps ready (demo mode)")
        
        # Process any pending operations
        self._process_pending_operations()
    
    def _update_status(self, message: str):
        """Thread-safe status update."""
        def _update():
            try:
                if not self._is_destroyed and hasattr(self, 'status_label'):
                    if self.status_label.winfo_exists():
                        self.status_label.configure(text=message)
            except Exception:
                pass  # Widget may have been destroyed
        
        self.safe_after_idle(_update)

    def _process_pending_operations(self):
        """Process any operations that were queued during initialization."""
        while self._pending_operations:
            try:
                operation = self._pending_operations.pop(0)
                operation()
            except Exception as e:
                self.logger.error(f"Error processing pending operation: {e}")
    
    # Public API methods
    def update_location(self, lat: float, lng: float, zoom: int = None):
        """Update map location (thread-safe)."""
        def _update():
            if not self._is_initialized:
                self._pending_operations.append(lambda: self.update_location(lat, lng, zoom))
                return
            
            self.current_location = (lat, lng)
            self._current_location = {'lat': lat, 'lng': lng}
            if zoom is not None:
                self.current_zoom = zoom
                self._current_zoom = zoom
            
            # Handle static fallback
            if self._fallback_active and hasattr(self, 'static_map'):
                self.static_map.set_location(lat, lng, zoom)
                self.logger.info(f"Static map location updated to ({lat}, {lng}) zoom {zoom or self.current_zoom}")
                return
            
            if self._communication_ready and self.map_webview:
                zoom_level = zoom or self.current_zoom
                js_code = f"""
                if (window.map) {{
                    window.map.setCenter({{lat: {lat}, lng: {lng}}});
                    window.map.setZoom({zoom_level});
                    
                    // Trigger location change event
                    if (window.onLocationChange) {{
                        window.onLocationChange({lat}, {lng}, {zoom_level});
                    }}
                }}
                """
                
                try:
                    self.map_webview.evaluate_js(js_code)
                    self.logger.info(f"Location updated to ({lat}, {lng}) zoom {zoom_level}")
                except Exception as e:
                    self.logger.error(f"Failed to update map location: {e}")
        
        self.safe_after_idle(_update)
    
    def toggle_weather_layer(self, layer_name: str, enabled: bool):
        """Toggle weather layer (thread-safe)."""
        def _toggle():
            if layer_name in self.layer_vars:
                self.layer_vars[layer_name].set(enabled)
                self._safe_toggle_layer(layer_name)
            
            # Also update weather overlay if available
            if self.weather_overlay:
                self.weather_overlay.toggle_layer(layer_name, enabled)
                self.logger.info(f"Weather layer {layer_name} {'enabled' if enabled else 'disabled'}")
            else:
                self.logger.warning("Weather overlay not available")
        
        self.safe_after_idle(_toggle)
    
    def set_layer_opacity(self, layer_type: str, opacity: float):
        """Set weather layer opacity.
        
        Args:
            layer_type: Type of weather layer
            opacity: Opacity value (0.0 to 1.0)
        """
        if self.weather_overlay:
            self.weather_overlay.set_layer_opacity(layer_type, opacity)
    
    def update_weather_data(self, layer_type: str, weather_data: List[Dict]):
        """Update weather data for visualization.
        
        Args:
            layer_type: Type of weather layer
            weather_data: List of weather data dictionaries
        """
        # Handle static fallback
        if self._fallback_active and hasattr(self, 'static_map'):
            self.static_map.update_weather_data({layer_type: weather_data})
            self.logger.info(f"Static map weather data updated for {layer_type}")
            return
        
        if not self.weather_overlay:
            return
        
        # Convert weather data to WeatherPoint objects
        weather_points = []
        for data in weather_data:
            try:
                # Import here to avoid circular imports
                from .weather_map_overlay import WeatherPoint
                point = WeatherPoint(
                    lat=data.get('lat', 0),
                    lng=data.get('lng', 0),
                    temperature=data.get('temperature'),
                    precipitation=data.get('precipitation'),
                    wind_speed=data.get('wind_speed'),
                    wind_direction=data.get('wind_direction'),
                    pressure=data.get('pressure'),
                    humidity=data.get('humidity'),
                    cloud_cover=data.get('cloud_cover'),
                    visibility=data.get('visibility'),
                    timestamp=datetime.now()
                )
                weather_points.append(point)
            except Exception as e:
                self.logger.error(f"Error converting weather data point: {e}")
        
        self.weather_overlay.update_weather_data(layer_type, weather_points)
    
    def search_location(self, query: str, callback: Optional[Callable] = None):
        """Search for a location with debouncing.
        
        Args:
            query: Search query string
            callback: Optional callback for search results
        """
        # Cancel previous search timer
        if self._search_debounce_timer:
            self._search_debounce_timer.cancel()
        
        def _perform_search():
            try:
                # Use geocoding service if available
                if hasattr(self.weather_service, 'geocoding_service'):
                    results = self.weather_service.geocoding_service.geocode(query)
                    if results and callback:
                        self.safe_after_idle(lambda: callback(results))
                else:
                    self.logger.warning("Geocoding service not available")
            except Exception as e:
                self.logger.error(f"Location search failed: {e}")
        
        # Debounce search with 500ms delay
        self._search_debounce_timer = threading.Timer(0.5, _perform_search)
        self._search_debounce_timer.start()
    
    def add_click_handler(self, handler: Callable):
        """Add a click handler for map interactions.
        
        Args:
            handler: Function to call with (lat, lng) on map click
        """
        self._click_handlers.append(handler)
    
    def remove_click_handler(self, handler: Callable):
        """Remove a click handler.
        
        Args:
            handler: Handler function to remove
        """
        if handler in self._click_handlers:
            self._click_handlers.remove(handler)
    
    def set_map_style(self, style_type: str):
        """Change map style/type.
        
        Args:
            style_type: Map style ('roadmap', 'satellite', 'terrain', 'hybrid')
        """
        def _update_style():
            try:
                self._current_map_type = style_type
                js_code = f"""
                if (window.map) {{
                    window.map.setMapTypeId('{style_type}');
                }}
                """
                if self._communication_ready and self.map_webview:
                    self.map_webview.evaluate_js(js_code)
                    self.logger.info(f"Map style changed to {style_type}")
            except Exception as e:
                self.logger.error(f"Map style change failed: {e}")
        
        self.safe_after_idle(_update_style)
    
    def get_current_location(self):
        """Get current map center location.
        
        Returns:
            Dictionary with 'lat', 'lng', and 'zoom' keys
        """
        return {
            'lat': self._current_location['lat'],
            'lng': self._current_location['lng'],
            'zoom': self._current_zoom
        }
    
    def center_on_user_location(self):
        """Center map on user's current location using geolocation."""
        def _center_on_user():
            try:
                js_code = """
                if (navigator.geolocation && window.map) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            var lat = position.coords.latitude;
                            var lng = position.coords.longitude;
                            window.map.setCenter({lat: lat, lng: lng});
                            window.map.setZoom(15);
                            
                            // Add marker for user location
                            if (window.userLocationMarker) {
                                window.userLocationMarker.setMap(null);
                            }
                            window.userLocationMarker = new google.maps.Marker({
                                position: {lat: lat, lng: lng},
                                map: window.map,
                                title: 'Your Location',
                                icon: {
                                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="%234285F4"><circle cx="12" cy="12" r="8" stroke="white" stroke-width="2"/></svg>'),
                                    scaledSize: new google.maps.Size(24, 24)
                                }
                            });
                        },
                        function(error) {
                            console.error('Geolocation error:', error);
                        }
                    );
                } else {
                    console.error('Geolocation not supported');
                }
                """
                if self._communication_ready and self.map_webview:
                    self.map_webview.evaluate_js(js_code)
            except Exception as e:
                self.logger.error(f"User location centering failed: {e}")
        
        self.safe_after_idle(_center_on_user)
    
    def bind_event(self, event_type: str, callback: Callable):
        """Bind event handler for map interactions."""
        try:
            if event_type == 'click':
                self._click_handlers.append(callback)
            self.logger.debug(f"Event handler bound for {event_type}")
        except Exception as e:
            self.logger.error(f"Failed to bind event {event_type}: {e}")
    
    def set_center(self, lat: float, lng: float, zoom: int = None):
        """Set map center to specified coordinates."""
        try:
            self._current_location = {'lat': lat, 'lng': lng}
            if zoom is not None:
                self._current_zoom = zoom
            
            # Update map if initialized
            if self._communication_ready and self.map_webview:
                js_code = f"""
                if (window.map) {{
                    window.map.setCenter({{lat: {lat}, lng: {lng}}});
                    {f'window.map.setZoom({zoom});' if zoom is not None else ''}
                }}
                """
                self.map_webview.evaluate_js(js_code)
            
            self.logger.debug(f"Map center set to ({lat}, {lng})")
        except Exception as e:
            self.logger.error(f"Failed to set map center: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self._is_destroyed = True
            
            # Cancel all pending callbacks
            self.cleanup_after_callbacks()
            
            # Clean up temporary files
            if self.current_map_file and self.current_map_file.exists():
                try:
                    self.current_map_file.unlink()
                except Exception:
                    pass
            
            # Clean up temp directory if empty
            try:
                if self.temp_dir.exists() and not any(self.temp_dir.iterdir()):
                    self.temp_dir.rmdir()
            except Exception:
                pass
            
            self.logger.info("ThreadSafeGoogleMapsWidget cleaned up")

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def _initialize_static_fallback(self):
        """Initialize static map fallback when webview fails."""
        try:
            self.logger.info("Initializing static map fallback for demo")
            
            # Clear webview container
            for widget in self.webview_container.winfo_children():
                widget.destroy()
            
            # Create static map fallback
            self.static_map = StaticMapFallback(self.webview_container)
            self.static_map.grid(row=0, column=0, sticky="nsew")
            
            # Set fallback flag
            self._fallback_active = True
            self._communication_ready = True  # Assume ready for demo
            
            # Update status
            self._update_status("Static Map Ready (Demo Mode)")
            
            # Set default location if available
            if hasattr(self, 'current_location') and self.current_location:
                self.static_map.set_location(
                    self.current_location[0], 
                    self.current_location[1], 
                    self.current_zoom
                )
            
            self.logger.info("Static map fallback initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize static fallback: {e}")
            self._update_status("Map initialization failed")
    
    def destroy(self):
        """Destroy widget and clean up."""
        self.cleanup()
        super().destroy()