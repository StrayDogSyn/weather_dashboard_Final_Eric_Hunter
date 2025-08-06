"""Static map fallback for demo purposes."""

import logging

class StaticMapFallback(ttk.Frame):
    """A static map fallback widget for demo purposes."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.current_location = (40.7128, -74.0060)  # Default to NYC
        self.current_zoom = 10
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the static map UI."""
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            self.main_frame, 
            text="Weather Map (Demo Mode)",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # Map placeholder with weather info
        self.map_canvas = tk.Canvas(
            self.main_frame,
            bg='#2c3e50',
            height=400,
            relief=tk.RAISED,
            bd=2
        )
        self.map_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Draw static map representation
        self._draw_static_map()
        
        # Controls frame
        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Location info
        self.location_label = ttk.Label(
            controls_frame,
            text=f"Location: {self.current_location[0]:.4f}, {self.current_location[1]:.4f}",
            font=('Arial', 10)
        )
        self.location_label.pack(side=tk.LEFT)
        
        # Demo buttons
        ttk.Button(
            controls_frame,
            text="Refresh Map",
            command=self._refresh_map
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            controls_frame,
            text="Center on Location",
            command=self._center_on_location
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
    def _draw_static_map(self):
        """Draw a static representation of a map with weather data."""
        self.map_canvas.delete("all")
        
        width = self.map_canvas.winfo_width() or 600
        height = self.map_canvas.winfo_height() or 400
        
        # Draw background gradient
        for i in range(height):
            color_intensity = int(255 * (1 - i / height))
            color = f"#{color_intensity:02x}{color_intensity:02x}{255:02x}"
            self.map_canvas.create_line(0, i, width, i, fill=color)
        
        # Draw grid lines (like map coordinates)
        for i in range(0, width, 50):
            self.map_canvas.create_line(i, 0, i, height, fill="#34495e", width=1)
        for i in range(0, height, 50):
            self.map_canvas.create_line(0, i, width, i, fill="#34495e", width=1)
        
        # Draw weather stations (demo data)
        stations = [
            (width * 0.3, height * 0.4, "72°F", "Sunny"),
            (width * 0.7, height * 0.3, "68°F", "Cloudy"),
            (width * 0.5, height * 0.6, "75°F", "Partly Cloudy"),
            (width * 0.2, height * 0.7, "70°F", "Rain"),
            (width * 0.8, height * 0.5, "73°F", "Clear")
        ]
        
        for x, y, temp, condition in stations:
            # Draw station marker
            self.map_canvas.create_oval(
                x-8, y-8, x+8, y+8,
                fill="#e74c3c", outline="#c0392b", width=2
            )
            
            # Draw temperature label
            self.map_canvas.create_text(
                x, y-20, text=temp,
                fill="white", font=('Arial', 10, 'bold')
            )
            
            # Draw condition label
            self.map_canvas.create_text(
                x, y+20, text=condition,
                fill="white", font=('Arial', 8)
            )
        
        # Draw current location marker
        center_x, center_y = width // 2, height // 2
        self.map_canvas.create_oval(
            center_x-12, center_y-12, center_x+12, center_y+12,
            fill="#f39c12", outline="#e67e22", width=3
        )
        self.map_canvas.create_text(
            center_x, center_y, text="📍",
            fill="white", font=('Arial', 12)
        )
        
        # Add title overlay
        self.map_canvas.create_text(
            width // 2, 30,
            text="Interactive Weather Map (Demo)",
            fill="white", font=('Arial', 16, 'bold')
        )
        
        # Add demo notice
        self.map_canvas.create_text(
            width // 2, height - 20,
            text="Demo Mode: Showing sample weather data",
            fill="#ecf0f1", font=('Arial', 10, 'italic')
        )
    
    def _refresh_map(self):
        """Refresh the static map display."""
        self.logger.info("Refreshing static map display")
        self.after(100, self._draw_static_map)  # Small delay for visual feedback
    
    def _center_on_location(self):
        """Center map on current location (demo)."""
        self.logger.info(f"Centering on location: {self.current_location}")
        self._refresh_map()
    
    def set_location(self, lat: float, lng: float, zoom: Optional[int] = None):
        """Set the current location (for compatibility with GoogleMapsWidget)."""
        self.current_location = (lat, lng)
        if zoom is not None:
            self.current_zoom = zoom
        
        self.location_label.configure(
            text=f"Location: {lat:.4f}, {lng:.4f}"
        )
        self._refresh_map()
    
    def add_weather_layer(self, layer_type: str, enabled: bool = True):
        """Add weather layer (demo compatibility method)."""
        self.logger.info(f"Demo: {layer_type} layer {'enabled' if enabled else 'disabled'}")
    
    def update_weather_data(self, weather_data: dict):
        """Update weather data display (demo compatibility method)."""
        self.logger.info("Demo: Weather data updated")
        self._refresh_map()