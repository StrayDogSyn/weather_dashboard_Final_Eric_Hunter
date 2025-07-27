"""Enhanced Hunter Theme Dashboard UI

Glasmorphic weather dashboard with Hunter theme styling,
3D glass panels, and weather-responsive visual effects.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable
import os

from .themes.hunter_glass import HunterGlassTheme

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
        """Create the main layout structure."""
        # Create main container
        self.main_frame = tk.Frame(
            self.root,
            bg=self.theme.HUNTER_BLACK
        )
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create title
        title_label = tk.Label(
            self.main_frame,
            text="Hunter Weather Dashboard",
            font=("Arial", 24, "bold"),
            fg=self.theme.HUNTER_SILVER,
            bg=self.theme.HUNTER_BLACK
        )
        title_label.pack(pady=(0, 20))
    
    def _create_weather_panel(self):
        """Create weather display panel."""
        # Weather frame
        weather_frame = tk.Frame(
            self.main_frame,
            bg=self.theme.HUNTER_DARK_SLATE,
            relief="raised",
            bd=2
        )
        weather_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Weather title
        weather_title = tk.Label(
            weather_frame,
            text="Current Weather",
            font=("Arial", 18, "bold"),
            fg=self.theme.HUNTER_GREEN,
            bg=self.theme.HUNTER_DARK_SLATE
        )
        weather_title.pack(pady=10)
        
        # Location input
        location_frame = tk.Frame(weather_frame, bg=self.theme.HUNTER_DARK_SLATE)
        location_frame.pack(pady=10)
        
        tk.Label(
            location_frame,
            text="Location:",
            fg=self.theme.HUNTER_SILVER,
            bg=self.theme.HUNTER_DARK_SLATE
        ).pack(side="left", padx=(0, 10))
        
        self.location_entry = tk.Entry(
            location_frame,
            bg=self.theme.HUNTER_BLACK,
            fg=self.theme.HUNTER_SILVER,
            insertbackground=self.theme.HUNTER_SILVER
        )
        self.location_entry.pack(side="left", padx=(0, 10))
        
        update_btn = tk.Button(
            location_frame,
            text="Update",
            command=self._update_weather,
            bg=self.theme.HUNTER_GREEN,
            fg=self.theme.HUNTER_BLACK,
            font=("Arial", 10, "bold")
        )
        update_btn.pack(side="left")
        
        # Weather display
        self.weather_display = tk.Label(
            weather_frame,
            text="No weather data",
            font=("Arial", 14),
            fg=self.theme.HUNTER_SILVER,
            bg=self.theme.HUNTER_DARK_SLATE
        )
        self.weather_display.pack(pady=20)
    
    def _create_navigation_panel(self):
        """Create navigation panel."""
        nav_frame = tk.Frame(
            self.main_frame,
            bg=self.theme.HUNTER_DARK_SLATE,
            relief="raised",
            bd=2
        )
        nav_frame.pack(fill="x", pady=10)
        
        nav_title = tk.Label(
            nav_frame,
            text="Navigation",
            font=("Arial", 16, "bold"),
            fg=self.theme.HUNTER_GREEN,
            bg=self.theme.HUNTER_DARK_SLATE
        )
        nav_title.pack(pady=10)
        
        # Navigation buttons
        button_frame = tk.Frame(nav_frame, bg=self.theme.HUNTER_DARK_SLATE)
        button_frame.pack(pady=10)
        
        buttons = ["Weather", "Settings", "About"]
        for btn_text in buttons:
            btn = tk.Button(
                button_frame,
                text=btn_text,
                bg=self.theme.HUNTER_GREEN,
                fg=self.theme.HUNTER_BLACK,
                font=("Arial", 10, "bold"),
                width=10
            )
            btn.pack(side="left", padx=5)
    
    def _create_navigation(self):
        """Create navigation with 3D glass buttons"""
        nav_frame = tk.Frame(self.header_frame, bg=HunterColors.GLASS_HUNTER_PRIMARY)
        nav_frame.pack(fill='x', padx=15, pady=10)
        
        # Title
        title_label = HunterGlassLabel(
            nav_frame,
            text="🌦️ Hunter Weather Dashboard",
            style='primary'
        )
        title_label.configure(font=('Segoe UI', 16, 'bold'))
        title_label.pack(side='left')
        
        # Navigation buttons
        button_frame = tk.Frame(nav_frame, bg=HunterColors.GLASS_HUNTER_PRIMARY)
        button_frame.pack(side='right')
        
        self.nav_buttons = {}
        nav_items = [
            ("Weather", "weather", "🌤️"),
            ("Journal", "journal", "📝"),
            ("Activities", "activities", "🎯"),
            ("Team", "team", "👥"),
            ("Settings", "settings", "⚙️")
        ]
        
        for text, tab_id, icon in nav_items:
            btn = HunterGlassButton(
                button_frame,
                text=f"{icon} {text}",
                command=lambda t=tab_id: self._switch_tab(t)
            )
            btn.pack(side='left', padx=5)
            self.nav_buttons[tab_id] = btn
            
            # Add animation manager
            self.animation_managers[f"nav_{tab_id}"] = AnimationManager(btn)
    
    def _create_content_panels(self):
        """Create content panels for different tabs"""
        self.content_panels = {}
        
        # Weather panel
        self.content_panels['weather'] = self._create_weather_panel()
        
        # Journal panel
        self.content_panels['journal'] = self._create_journal_panel()
        
        # Activities panel
        self.content_panels['activities'] = self._create_activities_panel()
        
        # Team panel
        self.content_panels['team'] = self._create_team_panel()
        
        # Settings panel
        self.content_panels['settings'] = self._create_settings_panel()
        
        # Show default panel
        self._switch_tab('weather')
    
    def _create_weather_panel(self) -> HunterGlassPanel:
        """Create weather information panel"""
        panel = HunterGlassPanel(self.content_frame, glass_opacity=0.3)
        
        # Current weather section
        current_frame = HunterGlassPanel(panel, glass_opacity=0.4)
        current_frame.pack(fill='x', padx=20, pady=10)
        current_frame.add_glass_effect()
        
        # Weather display
        self.weather_display = HunterGlassLabel(
            current_frame,
            text="🌤️ Loading weather data...",
            style='primary'
        )
        self.weather_display.configure(font=('Segoe UI', 14))
        self.weather_display.pack(pady=20)
        
        # Location input
        location_frame = tk.Frame(current_frame, bg=HunterColors.GLASS_HUNTER_PRIMARY)
        location_frame.pack(pady=10)
        
        HunterGlassLabel(
            location_frame,
            text="📍 Location:",
            style='accent'
        ).pack(side='left', padx=(0, 10))
        
        self.location_entry = HunterGlassEntry(location_frame, width=30)
        self.location_entry.pack(side='left', padx=(0, 10))
        
        update_btn = HunterGlassButton(
            location_frame,
            text="🔄 Update",
            command=self._update_weather
        )
        update_btn.pack(side='left')
        
        # Weather details grid
        details_frame = HunterGlassPanel(panel, glass_opacity=0.35)
        details_frame.pack(fill='both', expand=True, padx=20, pady=10)
        details_frame.add_glass_effect()
        
        self.weather_details = {}
        detail_items = [
            ("Temperature", "temp", "🌡️"),
            ("Humidity", "humidity", "💧"),
            ("Wind Speed", "wind", "💨"),
            ("Pressure", "pressure", "📊")
        ]
        
        for i, (label, key, icon) in enumerate(detail_items):
            row = i // 2
            col = i % 2
            
            detail_frame = tk.Frame(details_frame, bg=HunterColors.GLASS_HUNTER_ACCENT)
            detail_frame.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
            HunterGlassLabel(
                detail_frame,
                text=f"{icon} {label}:",
                style='accent'
            ).pack(anchor='w')
            
            self.weather_details[key] = HunterGlassLabel(
                detail_frame,
                text="--",
                style='primary'
            )
            self.weather_details[key].pack(anchor='w')
        
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_columnconfigure(1, weight=1)
        
        return panel
    
    def _create_journal_panel(self) -> HunterGlassPanel:
        """Create weather journal panel"""
        panel = HunterGlassPanel(self.content_frame, glass_opacity=0.3)
        
        HunterGlassLabel(
            panel,
            text="📝 Weather Journal",
            style='primary'
        ).pack(pady=20)
        
        HunterGlassLabel(
            panel,
            text="Journal functionality coming soon...",
            style='accent'
        ).pack(pady=10)
        
        return panel
    
    def _create_activities_panel(self) -> HunterGlassPanel:
        """Create activities suggestion panel"""
        panel = HunterGlassPanel(self.content_frame, glass_opacity=0.3)
        
        HunterGlassLabel(
            panel,
            text="🎯 Activity Suggestions",
            style='primary'
        ).pack(pady=20)
        
        HunterGlassLabel(
            panel,
            text="AI-powered activity suggestions coming soon...",
            style='accent'
        ).pack(pady=10)
        
        return panel
    
    def _create_team_panel(self) -> HunterGlassPanel:
        """Create team collaboration panel"""
        panel = HunterGlassPanel(self.content_frame, glass_opacity=0.3)
        
        HunterGlassLabel(
            panel,
            text="👥 Team Collaboration",
            style='primary'
        ).pack(pady=20)
        
        HunterGlassLabel(
            panel,
            text="Team features coming soon...",
            style='accent'
        ).pack(pady=10)
        
        return panel
    
    def _create_settings_panel(self) -> HunterGlassPanel:
        """Create settings panel"""
        panel = HunterGlassPanel(self.content_frame, glass_opacity=0.3)
        
        HunterGlassLabel(
            panel,
            text="⚙️ Settings",
            style='primary'
        ).pack(pady=20)
        
        HunterGlassLabel(
            panel,
            text="Configuration options coming soon...",
            style='accent'
        ).pack(pady=10)
        
        return panel
    
    def _switch_tab(self, tab_id: str):
        """Switch between content tabs with animation"""
        # Hide current panel
        if self.current_tab in self.content_panels:
            self.content_panels[self.current_tab].pack_forget()
        
        # Show new panel
        if tab_id in self.content_panels:
            self.content_panels[tab_id].pack(fill='both', expand=True, padx=20, pady=20)
            self.current_tab = tab_id
        
        # Update button states
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == tab_id:
                btn.configure(bg=HunterColors.HUNTER_GREEN)
            else:
                btn._apply_raised_state()
    
    def _update_weather(self):
        """Update weather data"""
        location = self.location_entry.get().strip()
        if location and self.weather_callback:
            self.weather_callback(location)
    
    def update_weather_display(self, weather_data: Dict[str, Any]):
        """Update weather display with new data"""
        self.weather_data = weather_data
        
        # Update main display
        condition = weather_data.get('condition', 'Unknown')
        location = weather_data.get('location', 'Unknown')
        self.weather_display.configure(
            text=f"🌤️ {condition} in {location}"
        )
        
        # Update details
        detail_mapping = {
            'temp': f"{weather_data.get('temperature', '--')}°C",
            'humidity': f"{weather_data.get('humidity', '--')}%",
            'wind': f"{weather_data.get('wind_speed', '--')} km/h",
            'pressure': f"{weather_data.get('pressure', '--')} hPa"
        }
        
        for key, value in detail_mapping.items():
            if key in self.weather_details:
                self.weather_details[key].configure(text=value)
        
        # Update background gradient
        self._update_background_gradient()
    
    def _apply_hunter_theme(self):
        """Apply Hunter theme styling to all components"""
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure(
            'Hunter.TFrame',
            background=HunterColors.GLASS_HUNTER_PRIMARY,
            borderwidth=1,
            relief='flat'
        )
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize events"""
        self.root.after_idle(self._update_background_gradient)
    
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