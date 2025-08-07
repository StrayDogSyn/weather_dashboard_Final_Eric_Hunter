"""
Weather Controls Panel

Provides a glassmorphic UI panel for weather layer controls and map tools.
Includes thread-safe state management and visual feedback.
"""

import logging
import threading
from typing import Dict, Callable, Optional, Any
from datetime import datetime
import customtkinter as ctk

from ..safe_widgets import SafeWidget


class WeatherControlsPanel(SafeWidget, ctk.CTkFrame):
    """Thread-safe weather controls panel with glassmorphic styling."""
    
    def __init__(self, parent, maps_widget, **kwargs):
        """Initialize the weather controls panel.
        
        Args:
            parent: Parent widget
            maps_widget: Thread-safe maps widget instance
            **kwargs: Additional frame arguments
        """
        # Initialize SafeWidget first
        SafeWidget.__init__(self)
        
        # Set default styling for glassmorphic effect
        default_kwargs = {
            'fg_color': ('#F0F0F0', '#2B2B2B'),
            'border_width': 1,
            'border_color': ('#E0E0E0', '#404040'),
            'corner_radius': 15
        }
        default_kwargs.update(kwargs)
        
        # Initialize CTkFrame
        ctk.CTkFrame.__init__(self, parent, **default_kwargs)
        
        self.maps_widget = maps_widget
        self.logger = logging.getLogger(__name__)
        
        # Thread-safe state management
        self._lock = threading.RLock()
        self._layer_states: Dict[str, bool] = {
            'temperature': False,
            'precipitation': False,
            'wind': False,
            'pressure': False,
            'clouds': False
        }
        self._layer_opacities: Dict[str, float] = {
            'temperature': 0.6,
            'precipitation': 0.6,
            'wind': 0.6,
            'pressure': 0.6,
            'clouds': 0.6
        }
        
        # UI components
        self.layer_checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        self.opacity_sliders: Dict[str, ctk.CTkSlider] = {}
        self.tool_buttons: Dict[str, ctk.CTkButton] = {}
        self.status_labels: Dict[str, ctk.CTkLabel] = {}
        
        # Tool states
        self._measurement_enabled = False
        self._current_map_style = 'roadmap'
        
        # Update callbacks
        self._update_callbacks: Dict[str, Callable] = {}
        
        self._setup_ui()
        self.logger.info("Weather controls panel initialized")
    
    def _setup_ui(self):
        """Set up the user interface components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Create main sections
        self._create_header()
        self._create_weather_layers_section()
        self._create_map_tools_section()
        self._create_status_section()
    
    def _create_header(self):
        """Create the panel header."""
        header_frame = ctk.CTkFrame(
            self,
            fg_color='transparent',
            height=50
        )
        header_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Weather & Map Controls",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#2E2E2E", "#FFFFFF")
        )
        title_label.grid(row=0, column=0, sticky='w')
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            header_frame,
            text="⟳",
            width=30,
            height=30,
            font=ctk.CTkFont(size=16),
            command=self._refresh_all_layers,
            fg_color=("#4A90E2", "#357ABD"),
            hover_color=("#357ABD", "#2E5F8A")
        )
        refresh_btn.grid(row=0, column=1, sticky='e')
    
    def _create_weather_layers_section(self):
        """Create the weather layers control section."""
        layers_frame = ctk.CTkFrame(
            self,
            fg_color=('#F8F8F8', '#1E1E1E'),
            corner_radius=10
        )
        layers_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        layers_frame.grid_columnconfigure(0, weight=1)
        
        # Section title
        section_title = ctk.CTkLabel(
            layers_frame,
            text="Weather Layers",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#2E2E2E", "#FFFFFF")
        )
        section_title.grid(row=0, column=0, sticky='w', padx=15, pady=(10, 5))
        
        # Layer controls
        layer_configs = [
            ('temperature', '🌡️ Temperature', '#FF6B6B'),
            ('precipitation', '🌧️ Precipitation', '#4ECDC4'),
            ('wind', '💨 Wind Speed', '#45B7D1'),
            ('pressure', '📊 Pressure', '#96CEB4'),
            ('clouds', '☁️ Cloud Cover', '#FFEAA7')
        ]
        
        for i, (layer_type, label, color) in enumerate(layer_configs):
            self._create_layer_control(layers_frame, i + 1, layer_type, label, color)
    
    def _create_layer_control(self, parent, row: int, layer_type: str, label: str, color: str):
        """Create a control row for a weather layer.
        
        Args:
            parent: Parent frame
            row: Grid row number
            layer_type: Type of weather layer
            label: Display label
            color: Layer color
        """
        control_frame = ctk.CTkFrame(parent, fg_color='transparent')
        control_frame.grid(row=row, column=0, sticky='ew', padx=15, pady=2)
        control_frame.grid_columnconfigure(1, weight=1)
        
        # Checkbox
        checkbox = ctk.CTkCheckBox(
            control_frame,
            text=label,
            font=ctk.CTkFont(size=12),
            command=lambda: self._toggle_layer(layer_type),
            checkbox_width=18,
            checkbox_height=18,
            checkmark_color=color,
            border_color=color,
            hover_color=color
        )
        checkbox.grid(row=0, column=0, sticky='w', pady=5)
        self.layer_checkboxes[layer_type] = checkbox
        
        # Opacity slider
        opacity_slider = ctk.CTkSlider(
            control_frame,
            from_=0.1,
            to=1.0,
            number_of_steps=9,
            command=lambda value: self._update_opacity(layer_type, value),
            width=100,
            height=16,
            button_color=color,
            progress_color=color
        )
        opacity_slider.set(self._layer_opacities[layer_type])
        opacity_slider.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        self.opacity_sliders[layer_type] = opacity_slider
        
        # Status indicator
        status_label = ctk.CTkLabel(
            control_frame,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=("#CCCCCC", "#666666"),
            width=20
        )
        status_label.grid(row=0, column=2, padx=(5, 0), pady=5)
        self.status_labels[layer_type] = status_label
    
    def _create_map_tools_section(self):
        """Create the map tools section."""
        tools_frame = ctk.CTkFrame(
            self,
            fg_color=('#F8F8F8', '#1E1E1E'),
            corner_radius=10
        )
        tools_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=5)
        tools_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Section title
        section_title = ctk.CTkLabel(
            tools_frame,
            text="Map Tools",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#2E2E2E", "#FFFFFF")
        )
        section_title.grid(row=0, column=0, columnspan=2, sticky='w', padx=15, pady=(10, 5))
        
        # Tool buttons
        tool_configs = [
            ('location', '📍 Current Location', self._center_on_location),
            ('refresh', '🔄 Refresh Map', self._refresh_map),
            ('measure', '📏 Measure Distance', self._toggle_measurement),
            ('style', '🗺️ Map Style', self._cycle_map_style)
        ]
        
        for i, (tool_id, label, command) in enumerate(tool_configs):
            row = (i // 2) + 1
            col = i % 2
            
            button = ctk.CTkButton(
                tools_frame,
                text=label,
                command=command,
                font=ctk.CTkFont(size=11),
                height=32,
                fg_color=("#4A90E2", "#357ABD"),
                hover_color=("#357ABD", "#2E5F8A")
            )
            button.grid(row=row, column=col, sticky='ew', padx=(15, 5) if col == 0 else (5, 15), pady=2)
            self.tool_buttons[tool_id] = button
    
    def _create_status_section(self):
        """Create the status display section."""
        status_frame = ctk.CTkFrame(
            self,
            fg_color=('#F8F8F8', '#1E1E1E'),
            corner_radius=10,
            height=60
        )
        status_frame.grid(row=3, column=0, sticky='ew', padx=10, pady=(5, 10))
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Status label
        self.main_status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#AAAAAA")
        )
        self.main_status_label.grid(row=0, column=0, padx=15, pady=10)
        
        # Last update time
        self.last_update_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=ctk.CTkFont(size=9),
            text_color=("#888888", "#777777")
        )
        self.last_update_label.grid(row=1, column=0, padx=15, pady=(0, 10))
    
    def _toggle_layer(self, layer_type: str):
        """Toggle a weather layer on/off.
        
        Args:
            layer_type: Type of weather layer
        """
        def _safe_toggle():
            try:
                with self._lock:
                    enabled = self.layer_checkboxes[layer_type].get()
                    self._layer_states[layer_type] = enabled
                
                # Update maps widget
                if self.maps_widget:
                    self.maps_widget.toggle_weather_layer(layer_type, enabled)
                
                # Update visual feedback
                self._update_layer_status(layer_type, enabled)
                
                # Update main status
                active_count = sum(self._layer_states.values())
                self._update_main_status(f"{active_count} layer(s) active")
                
                self.logger.info(f"Layer {layer_type} {'enabled' if enabled else 'disabled'}")
                
            except Exception as e:
                self.logger.error(f"Layer toggle error: {e}")
                self._update_main_status(f"Error: {e}")
        
        self.safe_after_idle(_safe_toggle)
    
    def _update_opacity(self, layer_type: str, opacity: float):
        """Update layer opacity.
        
        Args:
            layer_type: Type of weather layer
            opacity: New opacity value
        """
        def _safe_update_opacity():
            try:
                with self._lock:
                    self._layer_opacities[layer_type] = opacity
                
                # Update maps widget
                if self.maps_widget:
                    self.maps_widget.set_layer_opacity(layer_type, opacity)
                
                self.logger.debug(f"Layer {layer_type} opacity set to {opacity:.1f}")
                
            except Exception as e:
                self.logger.error(f"Opacity update error: {e}")
        
        self.safe_after_idle(_safe_update_opacity)
    
    def _update_layer_status(self, layer_type: str, enabled: bool):
        """Update visual status indicator for a layer.
        
        Args:
            layer_type: Type of weather layer
            enabled: Whether the layer is enabled
        """
        if layer_type in self.status_labels:
            color = "#4CAF50" if enabled else "#CCCCCC"  # Green if enabled, gray if disabled
            self.status_labels[layer_type].configure(text_color=color)
    
    def _update_main_status(self, message: str):
        """Update the main status message.
        
        Args:
            message: Status message to display
        """
        self.main_status_label.configure(text=message)
        self.last_update_label.configure(text=f"Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    def _refresh_all_layers(self):
        """Refresh all active weather layers."""
        def _safe_refresh():
            try:
                if self.maps_widget and hasattr(self.maps_widget, 'weather_overlay'):
                    if self.maps_widget.weather_overlay:
                        self.maps_widget.weather_overlay.refresh_all_layers()
                        self._update_main_status("Layers refreshed")
                    else:
                        self._update_main_status("Weather overlay not available")
                else:
                    self._update_main_status("Maps widget not available")
                    
            except Exception as e:
                self.logger.error(f"Refresh error: {e}")
                self._update_main_status(f"Refresh failed: {e}")
        
        self.safe_after_idle(_safe_refresh)
    
    def _center_on_location(self):
        """Center map on user's current location."""
        def _safe_center():
            try:
                if self.maps_widget:
                    self.maps_widget.center_on_user_location()
                    self._update_main_status("Centering on your location...")
                else:
                    self._update_main_status("Maps widget not available")
                    
            except Exception as e:
                self.logger.error(f"Location centering error: {e}")
                self._update_main_status(f"Location error: {e}")
        
        self.safe_after_idle(_safe_center)
    
    def _refresh_map(self):
        """Refresh the entire map."""
        def _safe_refresh_map():
            try:
                if self.maps_widget:
                    # Call the map's refresh method
                    if hasattr(self.maps_widget, '_safe_refresh_map'):
                        self.maps_widget._safe_refresh_map()
                    self._update_main_status("Map refreshed")
                else:
                    self._update_main_status("Maps widget not available")
                    
            except Exception as e:
                self.logger.error(f"Map refresh error: {e}")
                self._update_main_status(f"Refresh failed: {e}")
        
        self.safe_after_idle(_safe_refresh_map)
    
    def _toggle_measurement(self):
        """Toggle distance measurement tool."""
        def _safe_toggle_measurement():
            try:
                self._measurement_enabled = not self._measurement_enabled
                
                if self.maps_widget:
                    # Enable/disable measurement tool
                    if hasattr(self.maps_widget, 'enable_distance_measurement'):
                        self.maps_widget.enable_distance_measurement(self._measurement_enabled)
                
                # Update button text
                button_text = "📏 Stop Measuring" if self._measurement_enabled else "📏 Measure Distance"
                self.tool_buttons['measure'].configure(text=button_text)
                
                status_text = "Measurement tool enabled" if self._measurement_enabled else "Measurement tool disabled"
                self._update_main_status(status_text)
                
            except Exception as e:
                self.logger.error(f"Measurement toggle error: {e}")
                self._update_main_status(f"Measurement error: {e}")
        
        self.safe_after_idle(_safe_toggle_measurement)
    
    def _cycle_map_style(self):
        """Cycle through different map styles."""
        def _safe_cycle_style():
            try:
                styles = ['roadmap', 'satellite', 'terrain', 'hybrid']
                current_index = styles.index(self._current_map_style)
                next_index = (current_index + 1) % len(styles)
                self._current_map_style = styles[next_index]
                
                if self.maps_widget:
                    self.maps_widget.set_map_style(self._current_map_style)
                
                self._update_main_status(f"Map style: {self._current_map_style.title()}")
                
            except Exception as e:
                self.logger.error(f"Map style change error: {e}")
                self._update_main_status(f"Style change failed: {e}")
        
        self.safe_after_idle(_safe_cycle_style)
    
    def update_weather_data_status(self, layer_type: str, point_count: int):
        """Update status when weather data is received.
        
        Args:
            layer_type: Type of weather layer
            point_count: Number of data points received
        """
        def _safe_update_status():
            self._update_main_status(f"{layer_type.title()}: {point_count} data points")
        
        self.safe_after_idle(_safe_update_status)
    
    def set_layer_enabled(self, layer_type: str, enabled: bool):
        """Programmatically set layer enabled state.
        
        Args:
            layer_type: Type of weather layer
            enabled: Whether to enable the layer
        """
        def _safe_set_enabled():
            if layer_type in self.layer_checkboxes:
                self.layer_checkboxes[layer_type].select() if enabled else self.layer_checkboxes[layer_type].deselect()
                with self._lock:
                    self._layer_states[layer_type] = enabled
                self._update_layer_status(layer_type, enabled)
        
        self.safe_after_idle(_safe_set_enabled)
    
    def get_layer_states(self) -> Dict[str, bool]:
        """Get current layer states.
        
        Returns:
            Dictionary mapping layer types to their enabled status
        """
        with self._lock:
            return self._layer_states.copy()
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up weather controls panel")
        
        # Cancel any pending timers
        self.safe_after_cancel()
        
        # Clear references
        self.layer_checkboxes.clear()
        self.opacity_sliders.clear()
        self.tool_buttons.clear()
        self.status_labels.clear()
        self._update_callbacks.clear()