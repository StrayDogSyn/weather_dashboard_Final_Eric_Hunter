"""
Weather Map Overlay System

Provides thread-safe weather data visualization for Google Maps integration.
Handles weather layer generation, smooth transitions, and JavaScript bridge communication.
"""

import json
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WeatherPoint:
    """Represents a weather data point with coordinates and values."""
    lat: float
    lng: float
    temperature: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    pressure: Optional[float] = None
    humidity: Optional[float] = None
    cloud_cover: Optional[float] = None
    visibility: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class WeatherLayerConfig:
    """Configuration for weather layer visualization."""
    enabled: bool = False
    opacity: float = 0.6
    color_scheme: str = "default"
    animation_duration: int = 1000
    update_interval: int = 300000  # 5 minutes
    gradient_stops: List[Tuple[float, str]] = None
    min_zoom: int = 3
    max_zoom: int = 18


class WeatherMapOverlay:
    """Thread-safe weather overlay system for Google Maps."""
    
    def __init__(self, maps_widget, weather_service, logger=None):
        """Initialize the weather overlay system.
        
        Args:
            maps_widget: The thread-safe maps widget instance
            weather_service: Weather data service
            logger: Optional logger instance
        """
        self.maps_widget = maps_widget
        self.weather_service = weather_service
        self.logger = logger or logging.getLogger(__name__)
        
        # Thread-safe state management
        self._lock = threading.RLock()
        self._weather_data: Dict[str, List[WeatherPoint]] = {}
        self._layer_configs: Dict[str, WeatherLayerConfig] = {
            'temperature': WeatherLayerConfig(
                gradient_stops=[
                    (0.0, '#0000FF'),  # Blue (cold)
                    (0.25, '#00FFFF'), # Cyan
                    (0.5, '#00FF00'),  # Green
                    (0.75, '#FFFF00'), # Yellow
                    (1.0, '#FF0000')   # Red (hot)
                ]
            ),
            'precipitation': WeatherLayerConfig(
                gradient_stops=[
                    (0.0, 'rgba(255,255,255,0)'),  # Transparent
                    (0.3, '#87CEEB'),              # Sky blue
                    (0.6, '#4169E1'),              # Royal blue
                    (1.0, '#000080')               # Navy blue
                ]
            ),
            'wind': WeatherLayerConfig(
                gradient_stops=[
                    (0.0, '#90EE90'),  # Light green
                    (0.5, '#FFD700'),  # Gold
                    (1.0, '#FF4500')   # Orange red
                ]
            ),
            'pressure': WeatherLayerConfig(
                gradient_stops=[
                    (0.0, '#800080'),  # Purple (low)
                    (0.5, '#FFFFFF'),  # White (normal)
                    (1.0, '#FF0000')   # Red (high)
                ]
            ),
            'clouds': WeatherLayerConfig(
                gradient_stops=[
                    (0.0, 'rgba(255,255,255,0)'),  # Clear
                    (0.5, '#D3D3D3'),              # Light gray
                    (1.0, '#696969')               # Dark gray
                ]
            )
        }
        
        # Active layers tracking
        self._active_layers: set = set()
        self._update_callbacks: List[callable] = []
        
        self.logger.info("Weather map overlay system initialized")
    
    def register_update_callback(self, callback: callable):
        """Register a callback for weather data updates."""
        with self._lock:
            self._update_callbacks.append(callback)
    
    def update_weather_data(self, layer_type: str, weather_points: List[WeatherPoint]):
        """Update weather data for a specific layer type.
        
        Args:
            layer_type: Type of weather layer ('temperature', 'precipitation', etc.)
            weather_points: List of weather data points
        """
        with self._lock:
            self._weather_data[layer_type] = weather_points
            
        # Trigger update if layer is active
        if layer_type in self._active_layers:
            self._safe_update_layer(layer_type)
        
        # Notify callbacks
        for callback in self._update_callbacks:
            try:
                callback(layer_type, len(weather_points))
            except Exception as e:
                self.logger.error(f"Update callback error: {e}")
    
    def toggle_layer(self, layer_type: str, enabled: bool):
        """Toggle a weather layer on/off.
        
        Args:
            layer_type: Type of weather layer
            enabled: Whether to enable or disable the layer
        """
        with self._lock:
            config = self._layer_configs.get(layer_type)
            if not config:
                self.logger.warning(f"Unknown layer type: {layer_type}")
                return
            
            config.enabled = enabled
            
            if enabled:
                self._active_layers.add(layer_type)
                self._safe_update_layer(layer_type)
            else:
                self._active_layers.discard(layer_type)
                self._safe_remove_layer(layer_type)
    
    def set_layer_opacity(self, layer_type: str, opacity: float):
        """Set the opacity for a weather layer.
        
        Args:
            layer_type: Type of weather layer
            opacity: Opacity value (0.0 to 1.0)
        """
        with self._lock:
            config = self._layer_configs.get(layer_type)
            if config:
                config.opacity = max(0.0, min(1.0, opacity))
                if layer_type in self._active_layers:
                    self._safe_update_layer(layer_type)
    
    def _safe_update_layer(self, layer_type: str):
        """Safely update a weather layer using the thread-safe bridge."""
        def _update():
            try:
                overlay_js = self._generate_weather_overlay_js(layer_type)
                if overlay_js:
                    self.maps_widget.execute_javascript(overlay_js)
            except Exception as e:
                self.logger.error(f"Layer update error for {layer_type}: {e}")
        
        self.maps_widget.safe_after_idle(_update)
    
    def _safe_remove_layer(self, layer_type: str):
        """Safely remove a weather layer."""
        def _remove():
            try:
                remove_js = f"""
                if (window.weatherLayers && window.weatherLayers['{layer_type}']) {{
                    window.weatherLayers['{layer_type}'].setMap(null);
                    delete window.weatherLayers['{layer_type}'];
                }}
                """
                self.maps_widget.execute_javascript(remove_js)
            except Exception as e:
                self.logger.error(f"Layer removal error for {layer_type}: {e}")
        
        self.maps_widget.safe_after_idle(_remove)
    
    def _generate_weather_overlay_js(self, layer_type: str) -> Optional[str]:
        """Generate JavaScript code for weather overlay visualization.
        
        Args:
            layer_type: Type of weather layer
            
        Returns:
            JavaScript code string or None if no data available
        """
        with self._lock:
            weather_points = self._weather_data.get(layer_type, [])
            config = self._layer_configs.get(layer_type)
            
            if not weather_points or not config:
                return None
            
            # Generate heatmap data
            heatmap_data = self._generate_heatmap_data(layer_type, weather_points)
            
            if not heatmap_data:
                return None
            
            # Create JavaScript for heatmap layer
            js_code = f"""
            (function() {{
                // Initialize weather layers object if not exists
                if (!window.weatherLayers) {{
                    window.weatherLayers = {{}};
                }}
                
                // Remove existing layer
                if (window.weatherLayers['{layer_type}']) {{
                    window.weatherLayers['{layer_type}'].setMap(null);
                }}
                
                // Create heatmap data
                var heatmapData = {json.dumps(heatmap_data)};
                
                // Convert to Google Maps LatLng objects
                var points = heatmapData.map(function(point) {{
                    return {{
                        location: new google.maps.LatLng(point.lat, point.lng),
                        weight: point.weight
                    }};
                }});
                
                // Create heatmap layer
                var heatmap = new google.maps.visualization.HeatmapLayer({{
                    data: points,
                    map: window.map,
                    radius: 20,
                    opacity: {config.opacity},
                    gradient: {json.dumps(self._get_gradient_colors(config))}
                }});
                
                // Store layer reference
                window.weatherLayers['{layer_type}'] = heatmap;
                
                // Add smooth transition effect
                heatmap.setOptions({{
                    opacity: 0
                }});
                
                setTimeout(function() {{
                    heatmap.setOptions({{
                        opacity: {config.opacity}
                    }});
                }}, 100);
                
                console.log('Weather layer {layer_type} updated with', points.length, 'points');
            }})();
            """
            
            return js_code
    
    def _generate_heatmap_data(self, layer_type: str, weather_points: List[WeatherPoint]) -> List[Dict]:
        """Generate heatmap data points from weather data.
        
        Args:
            layer_type: Type of weather layer
            weather_points: List of weather data points
            
        Returns:
            List of heatmap data points with lat, lng, and weight
        """
        heatmap_data = []
        
        # Get value range for normalization
        values = []
        for point in weather_points:
            value = self._get_point_value(point, layer_type)
            if value is not None:
                values.append(value)
        
        if not values:
            return heatmap_data
        
        min_val, max_val = min(values), max(values)
        value_range = max_val - min_val if max_val != min_val else 1
        
        # Generate normalized heatmap points
        for point in weather_points:
            value = self._get_point_value(point, layer_type)
            if value is not None:
                # Normalize value to 0-1 range
                normalized_weight = (value - min_val) / value_range
                
                heatmap_data.append({
                    'lat': point.lat,
                    'lng': point.lng,
                    'weight': max(0.1, normalized_weight)  # Minimum weight for visibility
                })
        
        return heatmap_data
    
    def _get_point_value(self, point: WeatherPoint, layer_type: str) -> Optional[float]:
        """Extract the appropriate value from a weather point based on layer type.
        
        Args:
            point: Weather data point
            layer_type: Type of weather layer
            
        Returns:
            Numeric value or None if not available
        """
        value_map = {
            'temperature': point.temperature,
            'precipitation': point.precipitation,
            'wind': point.wind_speed,
            'pressure': point.pressure,
            'clouds': point.cloud_cover
        }
        
        return value_map.get(layer_type)
    
    def _get_gradient_colors(self, config: WeatherLayerConfig) -> List[str]:
        """Get gradient colors for heatmap visualization.
        
        Args:
            config: Layer configuration
            
        Returns:
            List of color strings for gradient
        """
        if config.gradient_stops:
            return [color for _, color in config.gradient_stops]
        
        # Default gradient
        return ['rgba(0,255,255,0)', 'rgba(0,255,255,1)', 'rgba(0,191,255,1)',
                'rgba(0,127,255,1)', 'rgba(0,63,255,1)', 'rgba(0,0,255,1)',
                'rgba(0,0,223,1)', 'rgba(0,0,191,1)', 'rgba(0,0,159,1)',
                'rgba(0,0,127,1)', 'rgba(63,0,91,1)', 'rgba(127,0,63,1)',
                'rgba(191,0,31,1)', 'rgba(255,0,0,1)']
    
    def refresh_all_layers(self):
        """Refresh all active weather layers."""
        with self._lock:
            active_layers = list(self._active_layers)
        
        for layer_type in active_layers:
            self._safe_update_layer(layer_type)
    
    def clear_all_layers(self):
        """Clear all weather layers from the map."""
        with self._lock:
            active_layers = list(self._active_layers)
            self._active_layers.clear()
        
        for layer_type in active_layers:
            self._safe_remove_layer(layer_type)
    
    def get_layer_status(self) -> Dict[str, bool]:
        """Get the current status of all weather layers.
        
        Returns:
            Dictionary mapping layer types to their enabled status
        """
        with self._lock:
            return {layer_type: config.enabled 
                   for layer_type, config in self._layer_configs.items()}
    
    def cleanup(self):
        """Clean up resources and clear all layers."""
        self.logger.info("Cleaning up weather overlay system")
        self.clear_all_layers()
        
        with self._lock:
            self._weather_data.clear()
            self._update_callbacks.clear()