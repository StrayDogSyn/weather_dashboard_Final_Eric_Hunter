import json
import os
from typing import Dict, Any, Callable, Optional
import customtkinter as ctk
from src.config.app_config import AppConfig


class ThemeManager:
    """Manages multiple themes for the weather dashboard with live switching capability."""
    
    THEMES = {
        "matrix": {
            "name": "Matrix",
            "bg": "#0A0A0A",
            "card": "#1A1A1A",
            "primary": "#00FF41",
            "secondary": "#008F11",
            "text": "#E0E0E0",
            "accent": "#00FF41",
            "error": "#FF0040",
            "chart_color": "#00FF41",
            "chart_bg": "#0D0D0D"
        },
        "cyberpunk": {
            "name": "Cyberpunk 2077",
            "bg": "#0F0F23",
            "card": "#1A1A3E",
            "primary": "#FF006E",
            "secondary": "#00F5FF",
            "text": "#F5F5F5",
            "accent": "#FFBE0B",
            "error": "#FB5607",
            "chart_color": "#FF006E",
            "chart_bg": "#16163A"
        },
        "arctic": {
            "name": "Arctic Terminal",
            "bg": "#0A0E27",
            "card": "#151B3C",
            "primary": "#00D9FF",
            "secondary": "#0096FF",
            "text": "#E8F4FD",
            "accent": "#41EAD4",
            "error": "#FF6B6B",
            "chart_color": "#00D9FF",
            "chart_bg": "#0F1430"
        },
        "solar": {
            "name": "Solar Flare",
            "bg": "#1A0F0A",
            "card": "#2D1810",
            "primary": "#FFA500",
            "secondary": "#FF6B35",
            "text": "#FFF5E6",
            "accent": "#FFD700",
            "error": "#DC143C",
            "chart_color": "#FFA500",
            "chart_bg": "#251208"
        },
        "terminal": {
            "name": "Classic Terminal",
            "bg": "#000000",
            "card": "#0A0A0A",
            "primary": "#00FF00",
            "secondary": "#00AA00",
            "text": "#00FF00",
            "accent": "#00FF00",
            "error": "#FF0000",
            "chart_color": "#00FF00",
            "chart_bg": "#000000"
        },
        "midnight": {
            "name": "Midnight Purple",
            "bg": "#0D0221",
            "card": "#1A0B3E",
            "primary": "#BD00FF",
            "secondary": "#7209B7",
            "text": "#E0B1FF",
            "accent": "#F72585",
            "error": "FF006E",
            "chart_color": "#BD00FF",
            "chart_bg": "#0A0119"
        }
    }
    
    def __init__(self):
        self.current_theme = "matrix"  # Default theme
        self.observers = []  # For notifying components of theme changes
        self.config_path = os.path.join("config", "theme_config.json")
        self._load_saved_theme()
    
    def add_observer(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback to be notified when theme changes."""
        self.observers.append(callback)
    
    def remove_observer(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove a theme change observer."""
        if callback in self.observers:
            self.observers.remove(callback)
    
    def _notify_observers(self, theme_data: Dict[str, Any]):
        """Notify all observers of theme change."""
        for callback in self.observers:
            try:
                callback(theme_data)
            except Exception as e:
                print(f"Error notifying theme observer: {e}")
    
    def get_current_theme(self) -> Dict[str, Any]:
        """Get the current theme data."""
        return self.THEMES.get(self.current_theme, self.THEMES["matrix"])
    
    def get_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """Get theme data by name."""
        return self.THEMES.get(theme_name)
    
    def apply_theme(self, theme_name: str, app=None):
        """Apply a theme to the application."""
        theme = self.THEMES.get(theme_name)
        if not theme:
            print(f"Theme '{theme_name}' not found")
            return False
        
        self.current_theme = theme_name
        
        # Update the DataTerminalTheme class if it exists
        self._update_data_terminal_theme(theme)
        
        # Update all UI elements if app is provided
        if app:
            self._update_colors(app, theme)
            self._update_charts(app, theme)
        
        # Save preference
        self._save_preference(theme_name)
        
        # Notify observers
        self._notify_observers(theme)
        
        return True
    
    def _update_data_terminal_theme(self, theme: Dict[str, Any]):
        """Update the DataTerminalTheme class with new colors."""
        try:
            from src.ui.theme import DataTerminalTheme
            DataTerminalTheme.set_active_theme(theme)
        except ImportError:
            print("DataTerminalTheme not found, skipping theme update")
    
    def _update_colors(self, app, theme: Dict[str, Any]):
        """Update all UI element colors."""
        try:
            # Update main window background
            if hasattr(app, 'configure'):
                app.configure(fg_color=theme["bg"])
            
            # Update all frames and widgets recursively
            self._update_widget_colors(app, theme)
            
        except Exception as e:
            print(f"Error updating colors: {e}")
    
    def _update_widget_colors(self, widget, theme: Dict[str, Any]):
        """Recursively update widget colors."""
        try:
            # Update current widget if it's a CTk widget
            if isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
                widget.configure(fg_color=theme["card"])
            elif isinstance(widget, ctk.CTkLabel):
                widget.configure(text_color=theme["text"])
            elif isinstance(widget, ctk.CTkButton):
                widget.configure(
                    fg_color=theme["primary"],
                    hover_color=theme["secondary"],
                    text_color=theme["text"]
                )
            elif isinstance(widget, ctk.CTkEntry):
                widget.configure(
                    fg_color=theme["card"],
                    text_color=theme["text"],
                    border_color=theme["primary"]
                )
            
            # Recursively update children
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    self._update_widget_colors(child, theme)
                    
        except Exception as e:
            print(f"Error updating widget colors: {e}")
    
    def _update_charts(self, app, theme: Dict[str, Any]):
        """Update chart colors."""
        try:
            # Update temperature chart if it exists
            if hasattr(app, 'temp_chart'):
                app.temp_chart.update_theme(theme)
            
            # Update any matplotlib charts
            import matplotlib.pyplot as plt
            plt.style.use('dark_background')
            plt.rcParams['figure.facecolor'] = theme["chart_bg"]
            plt.rcParams['axes.facecolor'] = theme["chart_bg"]
            plt.rcParams['text.color'] = theme["text"]
            plt.rcParams['axes.labelcolor'] = theme["text"]
            plt.rcParams['xtick.color'] = theme["text"]
            plt.rcParams['ytick.color'] = theme["text"]
            
        except Exception as e:
            print(f"Error updating charts: {e}")
    
    def _save_preference(self, theme_name: str):
        """Save theme preference to config file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            config = {"current_theme": theme_name}
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving theme preference: {e}")
    
    def _load_saved_theme(self):
        """Load saved theme preference."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    saved_theme = config.get("current_theme", "matrix")
                    if saved_theme in self.THEMES:
                        self.current_theme = saved_theme
        except Exception as e:
            print(f"Error loading theme preference: {e}")
    
    def get_theme_list(self) -> list:
        """Get list of available theme names."""
        return list(self.THEMES.keys())
    
    def get_theme_display_names(self) -> Dict[str, str]:
        """Get mapping of theme keys to display names."""
        return {key: theme["name"] for key, theme in self.THEMES.items()}


# Global theme manager instance
theme_manager = ThemeManager()