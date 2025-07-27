"""Enhanced Hunter Theme Dashboard UI

Glasmorphic weather dashboard with Hunter theme styling,
3D glass panels, and weather-responsive visual effects.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable
from .themes.hunter_glass import HunterGlassTheme
from .components.hunter_glass import (
    HunterGlassButton, HunterGlassPanel, HunterGlassLabel, 
    HunterGlassEntry, HunterColors, AnimationManager
)

class HunterDashboardUI:
    """
    Hunter-themed dashboard UI with dark slate, hunter green, and silver colors.
    
    Features:
    - Hunter theme color scheme
    - Weather display and controls
    - Modern dark interface
    - Responsive layout
    """
    
    def __init__(self, root: tk.Tk, weather_callback: Optional[Callable] = None):
        self.root = root
        self.weather_callback = weather_callback
        self.theme = HunterGlassTheme()
        
        # UI state
        self.current_weather = None
        self.content_frames = {}
        self.weather_labels = {}
        
        # Setup UI
        self._setup_main_window()
        self._create_main_layout()
        self._create_weather_panel()
        self._create_navigation_panel()
    
    def _setup_main_window(self):
        """Configure the main window with Hunter theme styling."""
        self.root.configure(bg=self.theme.HUNTER_BLACK)
        self.root.title("Hunter Weather Dashboard")
        
        # Set window properties
        self.root.resizable(True, True)
        self.root.minsize(1000, 700)
        
        # Center window on screen
        self.root.update_idletasks()
        width = 1200
        height = 800
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_main_layout(self):
        """Create the main layout structure with Hunter glass components"""
        # Create main container with glass panel
        self.main_frame = HunterGlassPanel(
            self.root,
            glass_opacity=0.2
        )
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create title with glass label
        title_label = HunterGlassLabel(
            self.main_frame,
            text="Hunter Weather Dashboard",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=(0, 20))
    
    def _create_weather_panel(self):
        """Create weather information display panel with Hunter glass components"""
        # Weather info frame with glass effect
        weather_frame = HunterGlassPanel(
            self.main_frame,
            glass_opacity=0.3
        )
        weather_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Weather display label with glass styling
        self.weather_label = HunterGlassLabel(
            weather_frame,
            text="🌤️ Weather data will appear here",
            font=("Arial", 14),
            style='primary'
        )
        self.weather_label.pack(pady=20)
        
        # Location input frame
        input_frame = HunterGlassPanel(
            weather_frame,
            glass_opacity=0.4
        )
        input_frame.pack(pady=10, padx=20, fill='x')
        
        # Location entry with glass styling
        HunterGlassLabel(
            input_frame,
            text="📍 Location:",
            font=("Arial", 12),
            style='accent'
        ).pack(side="left", padx=(10, 10))
        
        self.location_entry = HunterGlassEntry(
            input_frame,
            placeholder="Enter city name...",
            width=25
        )
        self.location_entry.pack(side="left", padx=(0, 10))
        
        # Update button with 3D glass effects
        update_btn = HunterGlassButton(
            input_frame,
            text="🔄 Update Weather",
            command=self._update_weather,
            width=140,
            height=35
        )
        update_btn.pack(side="left", padx=5)
        update_btn.add_3d_effects()
        
        # Weather display
        self.weather_display = HunterGlassLabel(
            weather_frame,
            text="No weather data",
            font=("Arial", 14),
            style='secondary'
        )
        self.weather_display.pack(pady=20)
    
    def _create_navigation_panel(self):
        """Create navigation panel with Hunter glass components"""
        nav_frame = HunterGlassPanel(
            self.main_frame,
            glass_opacity=0.4
        )
        nav_frame.pack(fill="x", pady=10)
        
        nav_title = HunterGlassLabel(
            nav_frame,
            text="🌦️ Hunter Weather Dashboard",
            font=("Arial", 16, "bold"),
            style='primary'
        )
        nav_title.pack(pady=10)
        
        # Navigation buttons with 3D glass effects
        button_frame = HunterGlassPanel(
            nav_frame,
            glass_opacity=0.2
        )
        button_frame.pack(fill='x', padx=20, pady=10)
        
        buttons = [
            ("🌤️ Weather", lambda: print("Weather clicked")),
            ("⚙️ Settings", lambda: print("Settings clicked")),
            ("ℹ️ About", lambda: print("About clicked"))
        ]
        for text, command in buttons:
            btn = HunterGlassButton(
                button_frame,
                text=text,
                command=command,
                width=120,
                height=40
            )
            btn.pack(side="left", padx=5)
            btn.add_3d_effects()
    

    
    def _update_weather(self):
        """Update weather data."""
        location = self.location_entry.get().strip()
        if location and self.weather_callback:
            self.weather_callback(location)
    
    def update_weather_display(self, weather_data: Dict[str, Any]):
        """Update weather display with new data."""
        condition = weather_data.get('condition', 'Unknown')
        location = weather_data.get('location', 'Unknown')
        temperature = weather_data.get('temperature', '--')
        
        display_text = f"{condition} in {location}\nTemperature: {temperature}°C"
        self.weather_display.configure(text=display_text)
    
    def cleanup(self):
        """Cleanup resources."""
        pass