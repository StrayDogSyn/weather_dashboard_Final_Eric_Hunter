from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import threading
import logging
import webbrowser
from typing import Optional, Dict, Tuple, List
import math
import os
import customtkinter as ctk
from customtkinter import CTkImage
import tkinter as tk
from ...utils.timer_manager import TimerManager

class EnhancedStaticMapsComponent(ctk.CTkFrame):
    """Enhanced maps component with full functionality including browser launch and weather layers"""
    
    def __init__(self, parent, weather_service=None, config=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.weather_service = weather_service
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize timer manager
        self.timer_manager = TimerManager(parent.winfo_toplevel())
        
        # Map state
        self.center_lat = 40.7128  # Default NYC
        self.center_lng = -74.0060
        self.zoom_level = 11
        self.map_type = "roadmap"
        self.current_image = None
        self.weather_data = {}
        self.weather_layers = {
            'temperature': False,
            'precipitation': False,
            'wind': False,
            'pressure': False,
            'clouds': False
        }
        
        # Auto-refresh state - DISABLED for stability
        self.auto_refresh_enabled = False
        
        # API configuration
        self.api_key = self._get_api_key()
        
        # Create complete UI
        self._create_main_layout()
        
        # Load initial map after UI is ready
        self.after(100, self._update_map)
        
    def _get_api_key(self):
        """Get Google Maps API key from config"""
        try:
            if self.config and hasattr(self.config, 'get'):
                api_key = self.config.get('google_maps_api_key', '')
                if api_key and len(api_key) > 10:  # Basic validation
                    return api_key
            # Try environment variable as fallback
            return os.getenv('GOOGLE_MAPS_API_KEY', '')
        except Exception as e:
            self.logger.warning(f"Failed to get API key: {e}")
            return ''
    
    def _create_main_layout(self):
        """Create the complete UI layout with toolbar, sidebar, and map area"""
        
        # Top toolbar frame with search and browser button
        self.toolbar_frame = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.toolbar_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.toolbar_frame.grid_propagate(False)
        
        # Search section in toolbar
        self.search_frame = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # Location icon
        self.location_icon = ctk.CTkLabel(self.search_frame, text="📍", font=("Arial", 16))
        self.location_icon.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        # Search entry field
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Search for a location...",
            width=450
        )
        self.search_entry.grid(row=0, column=1, sticky="ew")
        self.search_entry.bind("<Return>", self._on_search)
        
        # Search button
        self.search_btn = ctk.CTkButton(
            self.search_frame,
            text="Search",
            width=80,
            command=self._search_location
        )
        self.search_btn.grid(row=0, column=2, padx=5, sticky="w")
        
        # Browser button - IMPORTANT FEATURE
        self.browser_btn = ctk.CTkButton(
            self.toolbar_frame,
            text="🌐 Open in Browser",
            width=140,
            command=self._open_in_browser,
            fg_color="#2B7A78"
        )
        self.browser_btn.grid(row=0, column=1, padx=10, sticky="e")
        
        # Main content area with sidebar and map
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        
        # Create left sidebar with all controls
        self._create_sidebar()
        
        # Map display area on the right
        self.map_container = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.map_container.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        
        # Map label for displaying the image
        self.map_label = ctk.CTkLabel(
            self.map_container,
            text="Loading map...",
            fg_color="transparent"
        )
        self.map_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Status bar at bottom
        self.status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_frame.grid(row=2, column=0, sticky="ew")
        self.status_frame.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=("Arial", 10)
        )
        self.status_label.grid(row=0, column=0, padx=10, sticky="w")
        
        # Configure grid weights
        self.grid_rowconfigure(0, weight=0)  # toolbar
        self.grid_rowconfigure(1, weight=1)  # content
        self.grid_rowconfigure(2, weight=0)  # status
        self.grid_columnconfigure(0, weight=1)
        
        # Configure content frame grid
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=0)  # sidebar
        self.content_frame.grid_columnconfigure(1, weight=1)  # map
        
        # Configure toolbar frame grid
        self.toolbar_frame.grid_columnconfigure(0, weight=1)  # search frame
        self.toolbar_frame.grid_columnconfigure(1, weight=0)  # browser button
        
        # Configure search frame grid
        self.search_frame.grid_columnconfigure(1, weight=1)  # search entry
        
        # Configure map container grid
        self.map_container.grid_rowconfigure(0, weight=1)
        self.map_container.grid_columnconfigure(0, weight=1)
        
        # Configure zoom frame grid
        self.zoom_frame.grid_columnconfigure(1, weight=1)  # zoom label
    
    def _create_sidebar(self):
        """Create left sidebar with map controls and weather layers"""
        self.sidebar = ctk.CTkFrame(self.content_frame, width=300, corner_radius=12)
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=15, pady=15)
        self.sidebar.grid_propagate(False)
        
        # Configure column weight for better layout
        self.sidebar.grid_columnconfigure(0, weight=1)
        
        # Map Controls Section
        self.controls_label = ctk.CTkLabel(
            self.sidebar,
            text="Map Controls",
            font=("Arial", 16, "bold")
        )
        self.controls_label.grid(row=0, column=0, pady=(20, 15), padx=10, sticky="ew")
        
        # Zoom controls
        self.zoom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.zoom_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=8)
        self.zoom_frame.grid_columnconfigure(1, weight=1)
        
        self.zoom_out_btn = ctk.CTkButton(
            self.zoom_frame,
            text="-",
            width=45,
            height=32,
            command=self._zoom_out
        )
        self.zoom_out_btn.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.zoom_label = ctk.CTkLabel(
            self.zoom_frame,
            text=f"Zoom: {self.zoom_level}",
            font=("Arial", 12)
        )
        self.zoom_label.grid(row=0, column=1, sticky="ew", padx=5)
        
        self.zoom_in_btn = ctk.CTkButton(
            self.zoom_frame,
            text="+",
            width=45,
            height=32,
            command=self._zoom_in
        )
        self.zoom_in_btn.grid(row=0, column=2, sticky="e", padx=(5, 0))
        
        # Map type selection
        self.map_type_label = ctk.CTkLabel(
            self.sidebar, 
            text="Map Type:",
            font=("Arial", 12, "bold")
        )
        self.map_type_label.grid(row=2, column=0, pady=(20, 8), padx=15, sticky="ew")
        
        self.map_type_var = ctk.StringVar(value=self.map_type)
        self.map_type_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["roadmap", "satellite", "hybrid", "terrain"],
            variable=self.map_type_var,
            command=self._on_map_type_change,
            height=35
        )
        self.map_type_menu.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        # Weather Layers Section
        self.weather_label = ctk.CTkLabel(
            self.sidebar,
            text="Weather Layers",
            font=("Arial", 16, "bold")
        )
        self.weather_label.grid(row=4, column=0, pady=(25, 15), padx=10, sticky="ew")
        
        # Weather layer checkboxes with proper grid layout
        self.weather_checkboxes = {}
        weather_options = [
            ("temperature", "🌡️ Temperature"),
            ("precipitation", "🌧️ Precipitation"),
            ("wind", "💨 Wind"),
            ("pressure", "📊 Pressure"),
            ("clouds", "☁️ Clouds")
        ]
        
        for i, (key, label) in enumerate(weather_options):
            checkbox = ctk.CTkCheckBox(
                self.sidebar,
                text=label,
                command=lambda k=key: self._toggle_weather_layer(k)
            )
            checkbox.grid(row=5+i, column=0, sticky="w", padx=20, pady=3)
            self.weather_checkboxes[key] = checkbox
        
        # Current location button
        self.current_location_btn = ctk.CTkButton(
            self.sidebar,
            text="📍 Current Location",
            command=self._get_current_location,
            height=35
        )
        self.current_location_btn.grid(row=10, column=0, sticky="ew", padx=15, pady=(25, 10))
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            self.sidebar,
            text="🔄 Refresh Map",
            command=self._refresh_map,
            height=35
        )
        self.refresh_btn.grid(row=11, column=0, sticky="ew", padx=15, pady=(5, 15))
    
    def _open_in_browser(self):
        """Open current map view in web browser"""
        try:
            # Build Google Maps URL with current position
            url = f"https://www.google.com/maps/@{self.center_lat},{self.center_lng},{self.zoom_level}z"
            
            # Add weather layer parameter if any layers active
            if any(self.weather_layers.values()):
                url += "/data=!5m1!1e1"
            
            webbrowser.open(url)
            self._update_status("Opened in browser", duration=2000)
            self.logger.info(f"Opened map in browser: {url}")
            
        except Exception as e:
            self.logger.error(f"Failed to open browser: {e}")
            self._update_status("Failed to open browser", error=True)
    
    def _update_status(self, message, error=False, duration=None):
        """Update status bar message"""
        self.status_label.configure(
            text=message,
            text_color="red" if error else "white"
        )
        
        if duration:
            self.after(duration, lambda: self.status_label.configure(text="Ready", text_color="white"))
    
    def _on_search(self, event):
        """Handle search entry return key"""
        self._search_location()
    
    def _search_location(self):
        """Search for a location and update map"""
        query = self.search_entry.get().strip()
        if not query:
            self._update_status("Please enter a location to search", error=True, duration=3000)
            return
        
        self._update_status("Searching...")
        
        # Disable search button during search
        self.search_btn.configure(state="disabled")
        
        # Run geocoding in background thread
        threading.Thread(
            target=self._geocode_location,
            args=(query,),
            daemon=True
        ).start()
    
    def _geocode_location(self, query):
        """Geocode location using Google Geocoding API"""
        try:
            if not self.api_key:
                self.after(0, lambda: self._update_status("API key required for search", error=True))
                return
            
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': query,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                lat, lng = location['lat'], location['lng']
                
                # Update map on main thread
                self.after(0, lambda: self._update_location(lat, lng, query))
            else:
                self.after(0, lambda: self._update_status("Location not found", error=True, duration=3000))
                self.after(0, lambda: self.search_btn.configure(state="normal"))
                
        except Exception as e:
            self.logger.error(f"Geocoding error: {e}")
            self.after(0, lambda: self._update_status("Search failed", error=True, duration=3000))
            self.after(0, lambda: self.search_btn.configure(state="normal"))
    
    def _update_location(self, lat, lng, location_name=None):
        """Update map center to new location"""
        self.center_lat = lat
        self.center_lng = lng
        
        if location_name:
            self._update_status(f"Found: {location_name}", duration=3000)
            # Clear search entry after successful search
            self.search_entry.delete(0, 'end')
        
        # Re-enable search button
        self.search_btn.configure(state="normal")
        
        self._update_map()
    
    def _zoom_in(self):
        """Zoom in on the map"""
        if self.zoom_level < 20:
            self.zoom_level += 1
            self.zoom_label.configure(text=f"Zoom: {self.zoom_level}")
            self._update_status(f"Zoomed in to level {self.zoom_level}", duration=1500)
            self._update_map()
        else:
            self._update_status("Maximum zoom level reached", error=True, duration=2000)
    
    def _zoom_out(self):
        """Zoom out on the map"""
        if self.zoom_level > 1:
            self.zoom_level -= 1
            self.zoom_label.configure(text=f"Zoom: {self.zoom_level}")
            self._update_status(f"Zoomed out to level {self.zoom_level}", duration=1500)
            self._update_map()
        else:
            self._update_status("Minimum zoom level reached", error=True, duration=2000)
    
    def _on_map_type_change(self, value):
        """Handle map type change"""
        self.map_type = value
        self._update_status(f"Changed to {value} view", duration=2000)
        self._update_map()
    
    def _toggle_weather_layer(self, layer_key):
        """Toggle weather layer on/off"""
        checkbox = self.weather_checkboxes[layer_key]
        self.weather_layers[layer_key] = checkbox.get()
        
        status = "enabled" if checkbox.get() else "disabled"
        layer_name = layer_key.replace('_', ' ').title()
        self._update_status(f"{layer_name} layer {status}", duration=2000)
        
        self._update_map()
    
    def _get_current_location(self):
        """Get user's current location (placeholder - would need geolocation API)"""
        self._update_status("Getting current location...")
        
        # Disable button during operation
        self.current_location_btn.configure(state="disabled")
        
        def _restore_location():
            # For demo, use a default location (New York City)
            self._update_location(40.7128, -74.0060, "New York City (Demo)")
            self._update_status("Using demo location - New York City", duration=3000)
            self.current_location_btn.configure(state="normal")
        
        # Simulate async operation
        self.after(500, _restore_location)
    
    def _update_map(self):
        """Update the map display with current settings and overlays"""
        def _fetch_and_display():
            try:
                # Show loading state
                self.after_idle(lambda: self.map_label.configure(text="Updating map..."))
                
                if not self.api_key:
                    # Show informative message when no API key
                    self._display_no_api_key_message()
                    return
                
                # Build the complete map URL
                url = self._build_enhanced_map_url()
                
                # Fetch map image
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # Convert to PIL Image
                img = Image.open(BytesIO(response.content))
                
                # Add weather overlays if any layers are active
                if any(self.weather_layers.values()) and self.weather_data:
                    img = self._draw_weather_overlays(img)
                
                # Add map attribution
                img = self._add_attribution(img)
                
                # Display the final image
                self._safe_display_image(img)
                
                # Update status
                self.after_idle(lambda: self._update_status("Map updated", duration=1000))
                
            except requests.HTTPError as e:
                self.logger.error(f"HTTP error fetching map: {e}")
                self._display_error_message("Map service unavailable")
            except requests.RequestException as e:
                self.logger.error(f"Network error fetching map: {e}")
                self._display_error_message("Network connection error")
            except Exception as e:
                self.logger.error(f"Failed to update map: {e}")
                self._display_error_message("Map update failed")
        
        # Run map update in background thread
        thread = threading.Thread(target=_fetch_and_display, daemon=True)
        thread.start()
    
    def _build_enhanced_map_url(self):
        """Build Google Static Maps API URL with all parameters"""
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        
        # Basic parameters
        params = {
            'center': f"{self.center_lat},{self.center_lng}",
            'zoom': self.zoom_level,
            'size': '640x480',
            'maptype': self.map_type,
            'format': 'png',
            'scale': 2,  # High DPI support
            'key': self.api_key
        }
        
        # Add weather markers if weather layers are active
        if any(self.weather_layers.values()) and self.weather_data:
            markers = self._build_weather_markers_enhanced()
            if markers:
                params['markers'] = markers
        
        # Build URL with parameters
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"
    
    def _display_no_api_key_message(self):
        """Display informative message when no API key is available"""
        try:
            # Create informative image
            width, height = 640, 480
            img = Image.new('RGB', (width, height), color='#f0f0f0')
            draw = ImageDraw.Draw(img)
            
            # Try to load a font
            try:
                font_large = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw message
            message = "Google Maps API Key Required"
            submessage = "Please configure your API key in settings"
            
            # Center the text
            bbox = draw.textbbox((0, 0), message, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2 - 20
            
            draw.text((x, y), message, fill='#666666', font=font_large)
            
            # Draw submessage
            bbox2 = draw.textbbox((0, 0), submessage, font=font_small)
            text_width2 = bbox2[2] - bbox2[0]
            x2 = (width - text_width2) // 2
            y2 = y + text_height + 10
            
            draw.text((x2, y2), submessage, fill='#999999', font=font_small)
            
            self._safe_display_image(img)
            self._update_status("API key required for maps")
            
        except Exception as e:
            self.logger.error(f"Failed to display no API key message: {e}")
            self._display_fallback_map()
    
    def _draw_weather_overlays(self, img):
        """Draw weather overlays on the map image"""
        try:
            # Create a copy to avoid modifying the original
            overlay_img = img.copy()
            draw = ImageDraw.Draw(overlay_img)
            
            # Draw weather data points
            for location, data in self.weather_data.items():
                if 'lat' in data and 'lon' in data:
                    # Convert lat/lon to pixel coordinates
                    x, y = self._lat_lon_to_pixels(
                        data['lat'], data['lon'], 
                        img.width, img.height
                    )
                    
                    # Draw temperature if temperature layer is active
                    if self.weather_layers.get('temperature', False):
                        temp = data.get('temperature', 0)
                        color = self._temp_to_color(temp)
                        draw.ellipse([x-8, y-8, x+8, y+8], fill=color, outline='white', width=2)
                        
                        # Add temperature text
                        try:
                            font = ImageFont.truetype("arial.ttf", 12)
                        except:
                            font = ImageFont.load_default()
                        
                        temp_text = f"{int(temp)}°"
                        bbox = draw.textbbox((0, 0), temp_text, font=font)
                        text_width = bbox[2] - bbox[0]
                        draw.text((x - text_width//2, y - 6), temp_text, fill='white', font=font)
            
            return overlay_img
            
        except Exception as e:
            self.logger.error(f"Failed to draw weather overlays: {e}")
            return img
    
    def _lat_lon_to_pixels(self, lat, lon, img_width, img_height):
        """Convert latitude/longitude to pixel coordinates on the map"""
        try:
            # Web Mercator projection (simplified)
            # This is an approximation for the static map bounds
            
            # Calculate the bounds of the current map view
            lat_rad = math.radians(self.center_lat)
            n = 2.0 ** self.zoom_level
            
            # Calculate pixel coordinates relative to map center
            lat_diff = lat - self.center_lat
            lon_diff = lon - self.center_lng
            
            # Convert to pixel offsets (approximate)
            x_offset = (lon_diff * img_width) / (360.0 / n)
            y_offset = -(lat_diff * img_height) / (180.0 / n)
            
            # Calculate final pixel coordinates
            x = int(img_width / 2 + x_offset)
            y = int(img_height / 2 + y_offset)
            
            return x, y
            
        except Exception as e:
            self.logger.error(f"Failed to convert coordinates: {e}")
            return img_width // 2, img_height // 2
    
    def _temp_to_color(self, temp):
        """Convert temperature to color for visualization"""
        if temp < -10:
            return '#0000FF'  # Blue for very cold
        elif temp < 0:
            return '#4169E1'  # Royal blue for cold
        elif temp < 10:
            return '#00CED1'  # Dark turquoise for cool
        elif temp < 20:
            return '#32CD32'  # Lime green for mild
        elif temp < 30:
            return '#FFD700'  # Gold for warm
        elif temp < 40:
            return '#FF8C00'  # Dark orange for hot
        else:
            return '#FF0000'  # Red for very hot
    
    def _add_attribution(self, img):
        """Add Google Maps attribution to the image"""
        try:
            # Convert to RGB mode to avoid color allocation issues
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create a copy to avoid modifying the original
            attributed_img = img.copy()
            draw = ImageDraw.Draw(attributed_img)
            
            # Attribution text
            attribution = "© Google Maps"
            
            try:
                font = ImageFont.truetype("arial.ttf", 10)
            except:
                font = ImageFont.load_default()
            
            # Position at bottom right
            bbox = draw.textbbox((0, 0), attribution, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = img.width - text_width - 5
            y = img.height - text_height - 5
            
            # Draw background rectangle
            draw.rectangle([x-2, y-1, x+text_width+2, y+text_height+1], 
                         fill='white', outline='gray')
            
            # Draw attribution text
            draw.text((x, y), attribution, fill='black', font=font)
            
            return attributed_img
            
        except Exception as e:
            self.logger.error(f"Failed to add attribution: {e}")
            return img
    
    def _safe_display_image(self, img):
        """Safely display image in the UI thread"""
        try:
            # Convert PIL image to CTkImage
            photo = CTkImage(light_image=img, dark_image=img, size=img.size)
            
            # Update in main thread
            self.after_idle(lambda: self._update_map_display(photo, img))
            
        except Exception as e:
            self.logger.error(f"Failed to display image safely: {e}")
            self.after_idle(lambda: self._display_fallback_map())
    
    def _update_map_display(self, photo, img):
        """Update the map display with new image"""
        try:
            self.map_label.configure(image=photo, text="")
            self.map_label.image = photo  # Keep reference
            self.current_image = img
            
        except Exception as e:
            self.logger.error(f"Failed to update map display: {e}")
            self._display_fallback_map()
    
    def _display_error_message(self, message):
        """Display error message on the map"""
        try:
            # Create error image
            width, height = 640, 480
            img = Image.new('RGB', (width, height), color='#ffebee')
            draw = ImageDraw.Draw(img)
            
            try:
                font_large = ImageFont.truetype("arial.ttf", 20)
                font_small = ImageFont.truetype("arial.ttf", 14)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw error icon (simple X)
            center_x, center_y = width // 2, height // 2 - 40
            draw.line([center_x-20, center_y-20, center_x+20, center_y+20], fill='#f44336', width=4)
            draw.line([center_x-20, center_y+20, center_x+20, center_y-20], fill='#f44336', width=4)
            
            # Draw error message
            bbox = draw.textbbox((0, 0), message, font=font_large)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = center_y + 40
            
            draw.text((x, y), message, fill='#d32f2f', font=font_large)
            
            # Draw retry message
            retry_msg = "Click refresh to try again"
            bbox2 = draw.textbbox((0, 0), retry_msg, font=font_small)
            text_width2 = bbox2[2] - bbox2[0]
            x2 = (width - text_width2) // 2
            y2 = y + 30
            
            draw.text((x2, y2), retry_msg, fill='#666666', font=font_small)
            
            self._safe_display_image(img)
            self._update_status(f"Error: {message}", error=True)
            
        except Exception as e:
            self.logger.error(f"Failed to display error message: {e}")
            self._display_fallback_map()
    
    def _build_weather_markers_enhanced(self):
        """Build enhanced weather markers for the map URL"""
        try:
            markers = []
            
            for location, data in self.weather_data.items():
                if 'lat' in data and 'lon' in data:
                    lat, lon = data['lat'], data['lon']
                    
                    # Create marker based on active weather layers
                    if self.weather_layers.get('temperature', False):
                        temp = data.get('temperature', 0)
                        color = 'red' if temp > 25 else 'blue' if temp < 10 else 'green'
                        label = str(int(temp))
                        marker = f"color:{color}|size:mid|label:{label}|{lat},{lon}"
                        markers.append(marker)
            
            return '|'.join(markers) if markers else None
            
        except Exception as e:
            self.logger.error(f"Failed to build weather markers: {e}")
            return None
    
    def _load_map_image(self):
        """Load map image from Google Static Maps API"""
        try:
            # Build Static Maps API URL
            base_url = "https://maps.googleapis.com/maps/api/staticmap"
            params = {
                'center': f"{self.center_lat},{self.center_lng}",
                'zoom': self.zoom_level,
                'size': '640x480',
                'maptype': self.map_type,
                'key': self.api_key
            }
            
            # Add weather layers if enabled
            if any(self.weather_layers.values()):
                # Add weather overlay markers
                self._add_weather_markers(params)
            
            response = requests.get(base_url, params=params, timeout=15)
            response.raise_for_status()
            
            # Load and display image
            image = Image.open(BytesIO(response.content))
            self.after(0, lambda: self._display_map_image(image))
            
        except Exception as e:
            self.logger.error(f"Failed to load map: {e}")
            self.after(0, lambda: self._display_fallback_map())
    
    def _add_weather_markers(self, params):
        """Add weather data markers to map parameters"""
        markers = []
        
        # Add center marker with weather info
        if self.weather_service:
            try:
                # Get weather data for current location
                weather_data = self.weather_service.get_current_weather(
                    self.center_lat, self.center_lng
                )
                
                if weather_data:
                    # Create weather marker
                    temp = weather_data.get('temperature', 'N/A')
                    marker = f"color:red|label:T|{self.center_lat},{self.center_lng}"
                    markers.append(marker)
                    
            except Exception as e:
                self.logger.warning(f"Failed to get weather data: {e}")
        
        if markers:
            params['markers'] = '|'.join(markers)
    
    def _display_map_image(self, image):
        """Display the loaded map image"""
        try:
            # Convert PIL image to CTkImage
            photo = CTkImage(light_image=image, dark_image=image, size=image.size)
            
            # Update map label
            self.map_label.configure(image=photo, text="")
            self.map_label.image = photo  # Keep reference
            
            self.current_image = image
            self._update_status("Map loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to display map: {e}")
            self._display_fallback_map()
    
    def _display_fallback_map(self):
        """Display attractive fallback when map can't be loaded"""
        try:
            # Create gradient image
            width = 640
            height = 480
            img = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(img)
            
            # Draw gradient
            for i in range(height):
                color = int(50 + (i / height) * 50)
                draw.line([(0, i), (width, i)], fill=(color, color, color + 20))
            
            # Add text
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            text = "Weather Map"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), text, fill=(255, 255, 255), font=font)
            
            # Add status message
            status = "Configure API key for interactive maps"
            try:
                small_font = ImageFont.truetype("arial.ttf", 12)
            except:
                small_font = ImageFont.load_default()
            
            status_bbox = draw.textbbox((0, 0), status, font=small_font)
            status_width = status_bbox[2] - status_bbox[0]
            status_x = (width - status_width) // 2
            
            draw.text((status_x, height - 50), status, fill=(200, 200, 200), font=small_font)
            
            self._display_map_image(img)
            
        except Exception as e:
            # Ultimate fallback - just text
            self.map_label.configure(
                text="Weather Map\n\nConfigure API key for interactive maps",
                image=""
            )
            self.logger.error(f"Fallback display failed: {e}")
    
    def set_location(self, lat, lng):
        """Set map location programmatically"""
        self._update_location(lat, lng)
    
    def get_current_location(self):
        """Get current map center location"""
        return self.center_lat, self.center_lng
    
    def update_weather_data(self, weather_data):
        """Update weather data for map display (compatibility method)"""
        try:
            if weather_data:
                self.weather_data = weather_data
                
                # Extract location from EnhancedWeatherData object
                if hasattr(weather_data, 'location'):
                    location = weather_data.location
                    if hasattr(location, 'latitude') and hasattr(location, 'longitude'):
                        self.center_lat = location.latitude
                        self.center_lng = location.longitude
                # Fallback for dictionary format
                elif isinstance(weather_data, dict):
                    if 'lat' in weather_data and 'lng' in weather_data:
                        self.center_lat = weather_data['lat']
                        self.center_lng = weather_data['lng']
                    elif 'coord' in weather_data:
                        coord = weather_data['coord']
                        if 'lat' in coord and 'lon' in coord:
                            self.center_lat = coord['lat']
                            self.center_lng = coord['lon']
                
                # Update map if weather layers are active
                if any(self.weather_layers.values()):
                    self._update_map()
                    
                self.logger.info("Weather data updated for enhanced maps")
                
        except Exception as e:
            self.logger.error(f"Failed to update weather data: {e}")
    
    def _refresh_map(self):
        """Refresh map with user feedback"""
        self._update_status("Refreshing map...")
        
        # Disable refresh button during operation
        self.refresh_btn.configure(state="disabled")
        
        def _complete_refresh():
            self._update_map()
            self._update_status("Map refreshed", duration=2000)
            self.refresh_btn.configure(state="normal")
        
        # Small delay to show feedback
        self.after(200, _complete_refresh)
    
    def refresh_weather_data(self):
        """Refresh weather data and update map"""
        if any(self.weather_layers.values()):
            self._refresh_map()
    
    def start_auto_refresh(self, interval_minutes: int = 1):
        """Disabled for stability.
        
        Args:
            interval_minutes: Refresh interval in minutes (default: 1)
        """
        self.logger.info("Map auto-refresh disabled for stability")
        return
    
    def stop_auto_refresh(self):
        """Stop auto-refresh."""
        if not self.auto_refresh_enabled:
            return
            
        self.auto_refresh_enabled = False
        self.timer_manager.cancel('map_refresh')
        self.logger.info("Auto-refresh stopped")
    
    def _safe_refresh(self):
        """Thread-safe refresh with widget existence check."""
        try:
            # Check if widget still exists
            if not self.winfo_exists():
                self.logger.warning("Widget destroyed, stopping auto-refresh")
                self.stop_auto_refresh()
                return
                
            # Check if any weather layers are active
            if any(self.weather_layers.values()):
                self._refresh_map()
            else:
                self.logger.debug("No weather layers active, skipping refresh")
                
        except tk.TclError as e:
            self.logger.warning(f"Widget destroyed during refresh: {e}")
            self.stop_auto_refresh()
        except Exception as e:
            self.logger.error(f"Error during auto-refresh: {e}")
    
    def cleanup(self):
        """Clean up resources including timers."""
        try:
            # Stop auto-refresh and cleanup timers
            self.stop_auto_refresh()
            
            if hasattr(self, 'timer_manager'):
                self.timer_manager.shutdown()
                
            if hasattr(self, 'current_image'):
                self.current_image = None
                
            self.logger.info("Enhanced static maps component cleaned up")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")