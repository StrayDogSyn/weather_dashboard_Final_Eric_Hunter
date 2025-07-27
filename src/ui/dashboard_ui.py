"""Enhanced Hunter Theme Dashboard UI

Glasmorphic weather dashboard with Hunter theme styling,
3D glass panels, and weather-responsive visual effects.
"""

import customtkinter as ctk
from typing import Dict, Any, Optional, Callable
from .components.hunter_glass import (
    HunterGlassButton,
    HunterGlassFrame,
    HunterGlassPanel,
    HunterGlassLabel,
    HunterGlassEntry,
    HunterColors
)

# Configure CustomTkinter globally
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Brand constant
BRAND_NAME = "CodeFront Weather Capstone"

class HunterTypography:
    """Hunter theme typography standards"""
    FONT_FAMILY = "Segoe UI"
    HEADER_FONT = (FONT_FAMILY, 24, "bold")
    BODY_FONT = (FONT_FAMILY, 12, "normal")
    BUTTON_FONT = (FONT_FAMILY, 12, "normal")
    
    PRIMARY_TEXT = "#C0C0C0"      # Hunter silver
    SECONDARY_TEXT = ("#C0C0C0", "#999999")  # Dimmed silver with dark variant
    ACCENT_TEXT = "#355E3B"       # Hunter green

class HunterDashboardUI:
    """
    Hunter-themed dashboard UI with dark slate, hunter green, and silver colors.
    
    Features:
    - Hunter theme color scheme
    - Weather display and controls
    - Modern dark interface
    - Responsive layout
    """
    
    def __init__(self, parent, weather_service, database, settings):
        self.parent = parent
        self.weather_service = weather_service
        self.database = database
        self.settings = settings
        
        # Configure main window background
        if hasattr(parent, 'configure'):
            parent.configure(bg="#2F4F4F")  # Hunter dark slate background
        
        # Initialize UI
        self.create_ui()
    
    def create_ui(self):
        """Create main UI structure with CustomTkinter"""
        # Main container using CustomTkinter frame
        self.main_container = ctk.CTkFrame(
            self.parent,
            fg_color="#2F4F4F",  # Hunter dark slate
            corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True)
        
        # Create UI sections
        self.create_header()
        self.create_main_content()
        self.create_navigation()
    
    def create_header(self):
        """Create header with Hunter glass styling"""
        # Header frame using Hunter glass component
        self.header_frame = HunterGlassFrame(self.main_container)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Main header label with CustomTkinter
        self.main_header = HunterGlassLabel(
            self.header_frame,
            text=BRAND_NAME,
            font=("Segoe UI", 24, "bold"),
            text_color="#C0C0C0"
        )
        self.main_header.pack(pady=20)
    
    def create_main_content(self):
        """Create CustomTkinter TabView with Hunter theme"""
        self.tabview = ctk.CTkTabview(
            self.main_container,
            fg_color="#2F4F4F",                 # Hunter dark slate
            segmented_button_fg_color="#355E3B", # Hunter green active
            segmented_button_selected_color="#355E3B", # Hunter green selected
            segmented_button_unselected_color="#1C1C1C", # Hunter black inactive
            text_color="#C0C0C0",               # Hunter silver text
            corner_radius=12,
            border_width=1,
            border_color=("#C0C0C0", "#808080")  # Semi-transparent silver
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add tabs
        self.tabview.add("Weather")
        self.tabview.add("Temperature Graph")
        self.tabview.add("Weather Journal")
        self.tabview.add("Activity Suggester")
        self.tabview.add("Team Collaboration")
        
        self.create_weather_tab()
        self.create_placeholder_tabs()
    
    def create_weather_tab(self):
        """Create main weather tab"""
        weather_tab = self.tabview.tab("Weather")
        
        # Main weather panel
        self.weather_panel = HunterGlassPanel(weather_tab)
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
        
        self.create_weather_display()
    
    def create_weather_display(self):
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
    
    def create_placeholder_tabs(self):
        """Add placeholder content for feature tabs"""
        tabs_content = {
            "Temperature Graph": "📊 Temperature Graph\n(Coming in Phase 3C)",
            "Weather Journal": "📝 Weather Journal\n(Coming in Phase 3C)",
            "Activity Suggester": "🤖 Activity Suggester\n(Coming in Phase 3C)",
            "Team Collaboration": "👥 Team Collaboration\n(Coming in Phase 3C)"
        }
        
        for tab_name, content_text in tabs_content.items():
            tab = self.tabview.tab(tab_name)
            placeholder = HunterGlassLabel(
                tab,
                text=content_text,
                font=("Segoe UI", 16, "normal"),
                text_color=("#C0C0C0", "#999999")
            )
            placeholder.pack(expand=True)
    
    def create_navigation(self):
        """Create navigation with CustomTkinter buttons"""
        # Navigation frame
        self.navigation_frame = HunterGlassFrame(self.main_container)
        self.navigation_frame.pack(fill="x", side="bottom", padx=20, pady=(10, 20))
        
        self.add_navigation_buttons()
        
        # Footer branding
        self.footer_label = HunterGlassLabel(
            self.navigation_frame,
            text=BRAND_NAME,
            font=("Segoe UI", 12, "normal"),
            text_color=("#C0C0C0", "#808080")
        )
        self.footer_label.pack(pady=10)
        
        # Note: We'll add navigation buttons in Part 3
    
    def add_navigation_buttons(self):
        """Add navigation buttons to existing navigation frame"""
        nav_buttons_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        nav_buttons_frame.pack(pady=10)
        
        # Create navigation buttons
        self.weather_button = HunterGlassButton(nav_buttons_frame, text="🌤️ Weather", width=120)
        self.weather_button.pack(side="left", padx=5)
        
        self.settings_button = HunterGlassButton(nav_buttons_frame, text="⚙️ Settings", width=120)
        self.settings_button.pack(side="left", padx=5)
        
        self.about_button = HunterGlassButton(nav_buttons_frame, text="ℹ️ About", width=120)
        self.about_button.pack(side="left", padx=5)
    
    # Methods removed that caused fg_color errors:
    # - apply_hunter_theme_to_tabview()
    # - style_hunter_button()
    # - update_navigation_buttons()
    # - apply_hunter_typography()
    # These methods tried to use fg_color on standard tkinter widgets
    # We're replacing them with proper CustomTkinter components
    
    def update_weather_display(self, weather_dict):
        """Update weather display with new data."""
        try:
            # Update temperature
            if hasattr(self, 'temp_label') and 'temperature' in weather_dict:
                temp = weather_dict['temperature']
                self.temp_label.configure(text=f"{temp}°C")
            
            # Update location
            if hasattr(self, 'location_label') and 'location' in weather_dict:
                location = weather_dict['location']
                self.location_label.configure(text=location)
            
            # Update condition
            if hasattr(self, 'condition_label') and 'condition' in weather_dict:
                condition = weather_dict['condition']
                self.condition_label.configure(text=condition)
            
            # Update status
            if hasattr(self, 'weather_status_label'):
                self.weather_status_label.configure(text="🌤️ Weather data updated successfully")
            
        except Exception as e:
            print(f"Error updating weather display: {e}")
    
    def cleanup(self):
        """Cleanup resources."""
        pass