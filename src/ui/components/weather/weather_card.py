"""Weather Card Component

Unified weather card component for displaying current weather and forecast data.
"""

from typing import Callable, Optional
import customtkinter as ctk
from ..glassmorphic.base_frame import GlassmorphicFrame
from ...safe_widgets import SafeCTkLabel, SafeCTkButton
from ...theme_manager import theme_manager


class WeatherCard(GlassmorphicFrame):
    """Unified weather card for current weather and forecast display."""

    def __init__(
        self,
        parent,
        card_type: str = "current",  # "current" or "forecast"
        width: int = 200,
        height: int = 250,
        on_click: Optional[Callable] = None,
        **kwargs
    ):
        """Initialize weather card.
        
        Args:
            parent: Parent widget
            card_type: Type of card ("current" or "forecast")
            width: Card width
            height: Card height
            on_click: Callback for card click
            **kwargs: Additional frame arguments
        """
        self.card_type = card_type
        self.on_click = on_click
        
        # Weather data properties
        self.city = ""
        self.temperature = 0
        self.condition = ""
        self.icon = ""
        self.temp_unit = "C"
        
        # Forecast-specific properties
        self.day = ""
        self.date = ""
        self.high_temp = 0
        self.low_temp = 0
        self.precipitation = 0.0
        self.wind_speed = 0.0
        
        # Animation and interaction state
        self._is_hovered = False
        self._original_fg_color = None
        self.scheduled_calls = set()
        
        # Get current theme
        current_theme = theme_manager.get_current_theme()
        theme_colors = {
            "glass_bg": current_theme.get("card", "#1A1A1A"),
            "glass_border": current_theme.get("border", "#333333"),
            "glass_highlight": current_theme.get("primary", "#00FF41"),
        }
        
        card_kwargs = {
            "width": width,
            "height": height,
            "cursor": "hand2" if on_click else "arrow",
        }
        card_kwargs.update(kwargs)
        
        super().__init__(parent, theme_colors=theme_colors, **card_kwargs)
        
        # Store original color for animations
        self._original_fg_color = self.cget("fg_color")
        
        # UI components (will be created based on card type)
        self.main_label = None
        self.secondary_label = None
        self.icon_label = None
        self.temp_label = None
        self.condition_label = None
        self.details_labels = []
        
        self._create_widgets()
        self._setup_interactions()
        
        # Subscribe to theme changes
        theme_manager.add_observer(self._on_theme_changed)
    
    def _create_widgets(self):
        """Create widgets based on card type."""
        if self.card_type == "current":
            self._create_current_weather_widgets()
        else:
            self._create_forecast_widgets()
    
    def _create_current_weather_widgets(self):
        """Create widgets for current weather display."""
        current_theme = theme_manager.get_current_theme()
        
        # City name
        self.main_label = SafeCTkLabel(
            self,
            text="Loading...",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color=current_theme.get("text", "#E0E0E0"),
        )
        self.main_label.pack(pady=(20, 8))
        
        # Weather icon
        self.icon_label = SafeCTkLabel(
            self,
            text="🌤️",
            font=ctk.CTkFont(family="Consolas", size=48)
        )
        self.icon_label.pack(pady=10)
        
        # Temperature
        self.temp_label = SafeCTkLabel(
            self,
            text="--°C",
            font=ctk.CTkFont(family="Consolas", size=32, weight="bold"),
            text_color=current_theme.get("primary", "#00FF41"),
        )
        self.temp_label.pack(pady=8)
        
        # Condition
        self.condition_label = SafeCTkLabel(
            self,
            text="--",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=current_theme.get("secondary", "#008F11"),
        )
        self.condition_label.pack(pady=(0, 20))
    
    def _create_forecast_widgets(self):
        """Create widgets for forecast display."""
        current_theme = theme_manager.get_current_theme()
        
        # Day label
        self.main_label = SafeCTkLabel(
            self,
            text=self.day or "Day",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=current_theme.get("text", "#E0E0E0"),
        )
        self.main_label.pack(pady=(8, 2))
        
        # Date label
        self.secondary_label = SafeCTkLabel(
            self,
            text=self.date or "Date",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=current_theme.get("secondary", "#008F11"),
        )
        self.secondary_label.pack(pady=(0, 5))
        
        # Weather icon
        self.icon_label = SafeCTkLabel(
            self,
            text=self._get_icon_emoji(self.icon),
            font=ctk.CTkFont(family="Consolas", size=28)
        )
        self.icon_label.pack(pady=3)
        
        # Temperature range
        self.temp_label = SafeCTkLabel(
            self,
            text=self._format_temperature_range(),
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=current_theme.get("primary", "#00FF41"),
        )
        self.temp_label.pack(pady=2)
        
        # Additional details
        self._create_forecast_details()
    
    def _create_forecast_details(self):
        """Create additional forecast details."""
        current_theme = theme_manager.get_current_theme()
        
        # Precipitation
        if self.precipitation > 0:
            precip_label = SafeCTkLabel(
                self,
                text=f"💧 {int(self.precipitation * 100)}%",
                font=ctk.CTkFont(family="Consolas", size=9),
                text_color=current_theme.get("accent", "#00FF41"),
            )
            precip_label.pack(pady=1)
            self.details_labels.append(precip_label)
        
        # Wind speed
        if self.wind_speed > 0:
            wind_label = SafeCTkLabel(
                self,
                text=f"💨 {self.wind_speed:.1f} m/s",
                font=ctk.CTkFont(family="Consolas", size=9),
                text_color=current_theme.get("secondary", "#008F11"),
            )
            wind_label.pack(pady=(1, 8))
            self.details_labels.append(wind_label)
    
    def _setup_interactions(self):
        """Setup hover and click interactions."""
        if self.on_click:
            self.bind("<Button-1>", lambda e: self.on_click())
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """Handle mouse enter event."""
        self._is_hovered = True
        # Lighten the card slightly
        current_theme = theme_manager.get_current_theme()
        hover_color = self._lighten_color(current_theme.get("card", "#1A1A1A"))
        self.configure(fg_color=hover_color)
    
    def _on_leave(self, event):
        """Handle mouse leave event."""
        self._is_hovered = False
        # Reset to original color
        self.configure(fg_color=self._original_fg_color)
    
    def _lighten_color(self, color: str, factor: float = 0.1) -> str:
        """Lighten a color by a given factor."""
        try:
            color = color.lstrip("#")
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return color
    
    def _get_icon_emoji(self, icon_id: str) -> str:
        """Convert icon identifier to emoji."""
        icon_map = {
            "0": "☀️", "sunny": "☀️", "clear": "☀️",
            "1": "🌤️", "partly_cloudy": "🌤️",
            "2": "⛅", "cloudy": "⛅",
            "3": "🌧️", "rainy": "🌧️", "rain": "🌧️",
            "4": "⛈️", "stormy": "⛈️", "thunderstorm": "⛈️",
            "5": "🌨️", "snowy": "🌨️", "snow": "🌨️",
        }
        return icon_map.get(str(icon_id).lower(), "🌤️")
    
    def _format_temperature_range(self) -> str:
        """Format temperature range for forecast cards."""
        if self.card_type == "forecast":
            return f"{self.high_temp}°/{self.low_temp}°{self.temp_unit}"
        else:
            return f"{self.temperature}°{self.temp_unit}"
    
    def update_current_weather(self, city: str, temperature: int, condition: str, icon: str, temp_unit: str = "C"):
        """Update current weather data."""
        self.city = city
        self.temperature = temperature
        self.condition = condition
        self.icon = icon
        self.temp_unit = temp_unit
        
        if self.card_type == "current":
            if self.main_label:
                self.main_label.configure(text=city)
            if self.temp_label:
                self.temp_label.configure(text=f"{temperature}°{temp_unit}")
            if self.condition_label:
                self.condition_label.configure(text=condition)
            if self.icon_label:
                self.icon_label.configure(text=self._get_icon_emoji(icon))
    
    def update_forecast_data(self, day: str, date: str, icon: str, high: int, low: int, 
                           precipitation: float = 0.0, wind_speed: float = 0.0, temp_unit: str = "C"):
        """Update forecast data."""
        self.day = day
        self.date = date
        self.icon = icon
        self.high_temp = high
        self.low_temp = low
        self.precipitation = precipitation
        self.wind_speed = wind_speed
        self.temp_unit = temp_unit
        
        if self.card_type == "forecast":
            if self.main_label:
                self.main_label.configure(text=day)
            if self.secondary_label:
                self.secondary_label.configure(text=date)
            if self.temp_label:
                self.temp_label.configure(text=self._format_temperature_range())
            if self.icon_label:
                self.icon_label.configure(text=self._get_icon_emoji(icon))
    
    def _on_theme_changed(self):
        """Handle theme change events."""
        current_theme = theme_manager.get_current_theme()
        
        # Update theme colors
        self.theme_colors.update({
            "glass_bg": current_theme.get("card", "#1A1A1A"),
            "glass_border": current_theme.get("border", "#333333"),
            "glass_highlight": current_theme.get("primary", "#00FF41"),
        })
        
        # Reapply glass effect
        self.apply_glass_effect()
        self._original_fg_color = self.cget("fg_color")
    
    def safe_after(self, delay_ms: int, callback, *args):
        """Safely schedule an after() call with error handling."""
        try:
            if not self.winfo_exists():
                return None
            
            if args:
                call_id = self.after(delay_ms, callback, *args)
            else:
                call_id = self.after(delay_ms, callback)
            self.scheduled_calls.add(call_id)
            return call_id
        except Exception as e:
            print(f"Error scheduling after() call: {e}")
            return None
    
    def destroy(self):
        """Clean up scheduled calls when destroying card."""
        # Cancel all scheduled calls
        for call_id in self.scheduled_calls.copy():
            try:
                self.after_cancel(call_id)
            except Exception:
                pass
        self.scheduled_calls.clear()
        
        # Unsubscribe from theme changes
        try:
            theme_manager.remove_observer(self._on_theme_changed)
        except Exception:
            pass
        
        super().destroy()