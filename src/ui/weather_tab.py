#!/usr/bin/env python3
"""
Weather Tab Module

Handles the main weather display tab with location input, weather data display,
and weather service integration.

Author: Eric Hunter (Cortana Builder Agent)
Version: 3.0.0 (TRAE 2.0 Phase 3)
"""

import customtkinter as ctk
from typing import Dict, Any, Optional
from .components.hunter_glass import (
    HunterGlassButton,
    HunterGlassFrame,
    HunterGlassPanel,
    HunterGlassLabel,
    HunterGlassEntry
)

class WeatherTabManager:
    """
    Manages the weather tab functionality including location input,
    weather data display, and service integration.
    
    Responsibilities:
    - Weather display UI creation
    - Location input handling
    - Weather service integration
    - Weather data updates
    - Loading and error states
    - Placeholder text management
    """
    
    def __init__(self, tab_frame, weather_service, parent_dashboard):
        self.tab_frame = tab_frame
        self.weather_service = weather_service
        self.parent_dashboard = parent_dashboard
        self.current_weather_data = None
        
        # Create weather tab UI
        self._create_weather_ui()
        self._setup_weather_integration()
        self._initialize_weather_features()
    
    def _create_weather_ui(self):
        """Create main weather tab UI"""
        # Main weather panel
        self.weather_panel = HunterGlassPanel(self.tab_frame)
        self.weather_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status label
        self.weather_status_label = HunterGlassLabel(
            self.weather_panel,
            text="🌤️ Weather data will appear here",
            font=("Segoe UI", 14, "normal")
        )
        self.weather_status_label.pack(pady=20)
        
        # Location input frame
        self.location_frame = HunterGlassFrame(self.weather_panel)
        self.location_frame.pack(fill="x", padx=20, pady=10)
        
        # Location label and entry
        location_label = HunterGlassLabel(self.location_frame, text="Location:")
        location_label.pack(side="left", padx=(10, 5))
        
        self.location_entry = HunterGlassEntry(
            self.location_frame,
            placeholder_text="Enter city name...",
            width=200
        )
        self.location_entry.pack(side="left", padx=5)
        
        # Update button
        self.update_button = HunterGlassButton(
            self.location_frame,
            text="🔄 Update Weather",
            width=150
        )
        self.update_button.pack(side="left", padx=10)
        
        self._create_weather_display()
        self._enhance_location_input()
    
    def _create_weather_display(self):
        """Create weather data display"""
        # Weather display frame
        self.weather_display_frame = HunterGlassFrame(self.weather_panel)
        self.weather_display_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Temperature display
        self.temp_label = HunterGlassLabel(
            self.weather_display_frame,
            text="--°C",
            font=("Segoe UI", 48, "bold")
        )
        self.temp_label.pack(pady=20)
        
        # Location display
        self.location_label = HunterGlassLabel(
            self.weather_display_frame,
            text="Unknown Location",
            font=("Segoe UI", 18, "normal")
        )
        self.location_label.pack(pady=5)
        
        # Condition display
        self.condition_label = HunterGlassLabel(
            self.weather_display_frame,
            text="",
            font=("Segoe UI", 14, "normal"),
            text_color="#355E3B"
        )
        self.condition_label.pack(pady=5)
        
        self._add_3d_weather_panel()
    
    def _enhance_location_input(self):
        """Apply 3D styling to location input elements"""
        # Apply 3D border styling to existing location entry
        if hasattr(self, 'location_entry'):
            self.location_entry.configure(
                border_width=3,
                corner_radius=8,
                border_color=("#2B2B2B", "#404040")
            )
        
        # Apply 3D styling to update button
        if hasattr(self, 'update_button'):
            self.update_button.configure(
                border_width=3,
                corner_radius=8,
                border_color=("#355E3B", "#4A7C59"),
                hover_color=("#4A7C59", "#5D8F6A")
            )
    
    def _add_3d_weather_panel(self):
        """Apply 3D styling to weather display frame"""
        # Apply 3D styling to existing weather display frame
        if hasattr(self, 'weather_display_frame'):
            self.weather_display_frame.configure(
                border_width=3,
                corner_radius=12,
                border_color=("#2B2B2B", "#404040"),
                fg_color=("#1A1A1A", "#2D2D2D")
            )
        
        # Apply enhanced styling to location frame
        if hasattr(self, 'location_frame'):
            self.location_frame.configure(
                border_width=2,
                corner_radius=8,
                border_color=("#355E3B", "#4A7C59")
            )
    
    def _setup_weather_integration(self):
        """Connect weather service with debug"""
        
        def handle_weather_update():
            city = self.location_entry.get().strip()
            if not city or city == "Enter city name...":
                self.show_error_state("Enter city name")
                return
                
            self.show_loading_state(city)
            
            try:
                # Try different method names
                if hasattr(self.weather_service, 'get_weather'):
                    weather_data = self.weather_service.get_weather(city)
                elif hasattr(self.weather_service, 'get_current_weather'):
                    weather_data = self.weather_service.get_current_weather(city)
                else:
                    raise AttributeError("No weather method found")
                    
                if weather_data:
                    self.update_weather_display(weather_data)
                    self.show_success_state()
                else:
                    self.show_error_state("No data returned")
                    
            except Exception as e:
                self.show_error_state(f"Error: {str(e)[:25]}")
        
        def clear_placeholder_on_focus(event=None):
            """Clear placeholder text when user clicks on input field"""
            current_text = self.location_entry.get()
            if current_text == "Enter city name...":
                self.location_entry.delete(0, 'end')
        
        def restore_placeholder_on_focus_out(event=None):
            """Restore placeholder text if field is empty when focus is lost"""
            current_text = self.location_entry.get().strip()
            if not current_text:
                self.location_entry.delete(0, 'end')
                self.location_entry.insert(0, "Enter city name...")
        
        def clear_placeholder_on_key(event=None):
            """Clear placeholder text when user starts typing"""
            current_text = self.location_entry.get()
            if current_text == "Enter city name...":
                self.location_entry.delete(0, 'end')
        
        self.update_button.configure(command=handle_weather_update)
        self.location_entry.bind("<Return>", lambda e: handle_weather_update())
        
        # Add event handlers for automatic placeholder clearing
        self.location_entry.bind("<FocusIn>", clear_placeholder_on_focus)
        self.location_entry.bind("<FocusOut>", restore_placeholder_on_focus_out)
        self.location_entry.bind("<KeyPress>", clear_placeholder_on_key)
    
    def show_loading_state(self, city):
        """Show loading with 3D styling"""
        self.weather_status_label.configure(
            text=f"🔄 Fetching weather for {city}...",
            text_color="#C0C0C0"
        )
        self.update_button.configure(
            state="disabled",
            text="Loading...",
            fg_color="#2F4F4F"
        )
        if hasattr(self.parent_dashboard, 'parent'):
            self.parent_dashboard.parent.update()
    
    def show_success_state(self):
        """Show success with proper clearing"""
        self.weather_status_label.configure(
            text="✅ Weather updated",
            text_color="#4A7C59"
        )
        self.update_button.configure(
            state="normal",
            text="🔄 Update Weather",
            fg_color="#355E3B"
        )
        if hasattr(self.parent_dashboard, 'parent'):
            self.parent_dashboard.parent.after(2000, lambda: self.weather_status_label.configure(text=""))
    
    def show_error_state(self, error_message):
        """Show error state"""
        self.weather_status_label.configure(
            text=f"❌ {error_message}",
            text_color="#FF6B6B"
        )
        self.update_button.configure(
            state="normal",
            text="🔄 Update Weather",
            fg_color="#355E3B"
        )
        if hasattr(self.parent_dashboard, 'parent'):
            self.parent_dashboard.parent.after(5000, lambda: self.weather_status_label.configure(text=""))
    
    def debug_weather_data(self, weather_data):
        """Debug weather data structure"""
        print("=== Weather Data Debug ===")
        print(f"Type: {type(weather_data)}")
        if hasattr(weather_data, '__dict__'):
            for attr, value in weather_data.__dict__.items():
                print(f"{attr}: {value}")
        print("========================")
    
    def update_weather_display(self, weather_data):
        """Update weather display with robust data handling"""
        
        # Debug first to see actual data structure
        self.debug_weather_data(weather_data)
        
        # Temperature (usually works)
        if hasattr(weather_data, 'temperature'):
            temp = weather_data.temperature
        elif hasattr(weather_data, 'temp'):
            temp = weather_data.temp
        else:
            temp = 0.0
            
        self.temp_label.configure(text=f"{temp:.1f}°C")
        
        # Location (usually works)
        if hasattr(weather_data, 'location'):
            location = weather_data.location
        elif hasattr(weather_data, 'city'):
            location = f"{weather_data.city}, {weather_data.country}"
        else:
            location = "Unknown Location"
            
        self.location_label.configure(text=location)
        
        # Weather condition - try multiple possible attributes
        condition = "Clear"  # Default
        possible_attrs = ['condition', 'description', 'weather', 'main', 'summary']
        
        for attr in possible_attrs:
            if hasattr(weather_data, attr):
                value = getattr(weather_data, attr)
                if value and str(value).strip():
                    condition = str(value).title()
                    break
        
        self.condition_label.configure(
            text=condition,
            text_color="#355E3B"  # Ensure visible color
        )
        
        # Apply background effect through parent dashboard
        if hasattr(self.parent_dashboard, 'apply_weather_background_effect'):
            self.parent_dashboard.apply_weather_background_effect(condition)
        
        # Update entry field
        if hasattr(weather_data, 'location'):
            self.location_entry.delete(0, 'end')
            self.location_entry.insert(0, weather_data.location.split(',')[0])
        
        # Store current weather data
        self.current_weather_data = weather_data
        
        # Update advanced chart widget if available
        if hasattr(self.parent_dashboard, 'advanced_chart'):
            try:
                self.parent_dashboard.advanced_chart.update_current_weather(weather_data)
            except Exception as e:
                print(f"Failed to update chart: {e}")
    
    def update_weather_display_with_data(self, weather_data):
        """Legacy method - redirects to new robust method"""
        self.update_weather_display(weather_data)
    
    def _initialize_weather_features(self):
        """Initialize weather integration"""
        # Set placeholder
        self.location_entry.delete(0, 'end')
        self.location_entry.insert(0, "Enter city name...")
    
    def test_weather_functionality(self):
        """Quick test of weather functionality"""
        self.location_entry.delete(0, 'end')
        self.location_entry.insert(0, "London")
        # Then click Update Weather button or press Enter
    
    def get_current_weather_data(self):
        """Get current weather data"""
        return self.current_weather_data
    
    def cleanup(self):
        """Cleanup resources"""
        self.current_weather_data = None