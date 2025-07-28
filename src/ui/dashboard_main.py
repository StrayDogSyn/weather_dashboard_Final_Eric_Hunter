#!/usr/bin/env python3
"""
Main Dashboard Framework

Core dashboard structure and initialization for the Hunter-themed weather dashboard.
Handles main UI setup, navigation, and 3D enhancements.

Author: Eric Hunter (Cortana Builder Agent)
Version: 3.0.0 (TRAE 2.0 Phase 3)
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
from .components.hunter_widgets import (
    Hunter3DButton,
    Hunter3DEntry,
    Hunter3DFrame
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

class DashboardMainFramework:
    """
    Core dashboard framework handling main UI structure, navigation, and theming.
    
    Responsibilities:
    - Main window setup and configuration
    - Header creation and branding
    - Tab view initialization
    - Navigation framework
    - 3D styling and enhancements
    - Theme application
    """
    
    def __init__(self, parent, weather_service, database, settings, github_service=None):
        self.parent = parent
        self.weather_service = weather_service
        self.database = database
        self.settings = settings
        self.github_service = github_service
        
        # Configure main window background
        if hasattr(parent, 'configure'):
            parent.configure(bg="#2F4F4F")  # Hunter dark slate background
        
        # Initialize core UI structure
        self._setup_main_container()
        self._create_header()
        self._create_tabview()
        self._create_navigation()
        
        # Apply styling enhancements
        self._apply_all_3d_enhancements()
    
    def _setup_main_container(self):
        """Setup main container with Hunter theme"""
        self.main_container = ctk.CTkFrame(
            self.parent,
            fg_color="#2F4F4F",  # Hunter dark slate
            corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True)
    
    def _create_header(self):
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
    
    def _create_tabview(self):
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
        
        # Add tabs (content will be handled by specific tab modules)
        self.tabview.add("Weather")
        self.tabview.add("Temperature Graph")
        self.tabview.add("Weather Journal")
        self.tabview.add("Activity Suggester")
        self.tabview.add("Team Collaboration")
        self.tabview.add("Settings")
    
    def _create_navigation(self):
        """Create navigation with CustomTkinter buttons"""
        # Navigation frame
        self.navigation_frame = HunterGlassFrame(self.main_container)
        self.navigation_frame.pack(fill="x", side="bottom", padx=20, pady=(10, 20))
        
        self._add_navigation_buttons()
        
        # Footer branding
        self.footer_label = HunterGlassLabel(
            self.navigation_frame,
            text=BRAND_NAME,
            font=("Segoe UI", 12, "normal"),
            text_color=("#C0C0C0", "#808080")
        )
        self.footer_label.pack(pady=10)
    
    def _add_navigation_buttons(self):
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
    
    def _enhance_navigation_buttons(self):
        """Apply 3D styling to existing navigation buttons"""
        # Apply 3D styling to existing navigation buttons
        if hasattr(self, 'weather_button'):
            self.weather_button.configure(
                border_width=3,
                corner_radius=8,
                border_color=("#355E3B", "#4A7C59"),
                hover_color=("#4A7C59", "#5D8F6A")
            )
        
        if hasattr(self, 'settings_button'):
            self.settings_button.configure(
                border_width=3,
                corner_radius=8,
                border_color=("#355E3B", "#4A7C59"),
                hover_color=("#4A7C59", "#5D8F6A")
            )
        
        if hasattr(self, 'about_button'):
            self.about_button.configure(
                border_width=3,
                corner_radius=8,
                border_color=("#355E3B", "#4A7C59"),
                hover_color=("#4A7C59", "#5D8F6A")
            )
    
    def _add_3d_status_panel(self):
        """Apply 3D styling to status elements"""
        # Apply enhanced styling to navigation frame
        if hasattr(self, 'navigation_frame'):
            self.navigation_frame.configure(
                border_width=2,
                corner_radius=8,
                border_color=("#2B2B2B", "#404040")
            )
        
        # Apply styling to main container
        if hasattr(self, 'main_container'):
            self.main_container.configure(
                border_width=1,
                corner_radius=10,
                border_color=("#355E3B", "#4A7C59")
            )
    
    def _apply_all_3d_enhancements(self):
        """Apply all 3D enhancements to interface"""
        self._enhance_navigation_buttons()
        self._add_3d_status_panel()
    
    def apply_weather_background_effect(self, condition):
        """Apply background effects based on weather"""
        weather_effects = {
            "clear": "#355E3B",           # Light hunter green
            "clouds": "#2F4F4F",          # Dark slate overlay
            "rain": "#2F4F4F",            # Heavy slate
            "storm": "#1C1C1C",           # Very dark
            "snow": "#C0C0C0",            # Silver
            "mist": "#2F4F4F"             # Misty slate
        }
        
        # Find matching condition
        effect_color = "#355E3B"  # Default
        for key, color in weather_effects.items():
            if key in condition.lower():
                effect_color = color
                break
        
        # Apply to main container
        if hasattr(self, 'main_container'):
            self.main_container.configure(fg_color=effect_color)
    
    def get_tab(self, tab_name: str):
        """Get a specific tab for content creation"""
        return self.tabview.tab(tab_name)
    
    def cleanup(self):
        """Cleanup resources"""
        pass