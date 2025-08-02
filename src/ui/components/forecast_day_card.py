import customtkinter as ctk
from typing import Optional
from src.ui.theme import DataTerminalTheme


class ForecastDayCard(ctk.CTkFrame):
    """A forecast card widget for displaying daily weather information."""
    
    def __init__(self, parent, day: str, icon: str, high: int, low: int, **kwargs):
        """Initialize the forecast day card.
        
        Args:
            parent: Parent widget
            day: Day of the week (e.g., "Mon", "Tue")
            icon: Weather icon identifier
            high: High temperature
            low: Low temperature
        """
        # Set default styling
        default_kwargs = {
            "fg_color": DataTerminalTheme.CARD_BG,
            "corner_radius": 8,
            "border_width": 1,
            "border_color": DataTerminalTheme.BORDER,
            "width": 120,
            "height": 140
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        self.day = day
        self.icon = icon
        self.high = high
        self.low = low
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create and layout the card widgets."""
        # Day label
        self.day_label = ctk.CTkLabel(
            self,
            text=self.day,
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            text_color=DataTerminalTheme.TEXT
        )
        self.day_label.pack(pady=(10, 5))
        
        # Weather icon (using emoji for now)
        icon_text = self._get_icon_emoji(self.icon)
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon_text,
            font=(DataTerminalTheme.FONT_FAMILY, 24)
        )
        self.icon_label.pack(pady=5)
        
        # Temperature range
        temp_text = f"{self.high}°/{self.low}°"
        self.temp_label = ctk.CTkLabel(
            self,
            text=temp_text,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT
        )
        self.temp_label.pack(pady=(5, 10))
        
    def _get_icon_emoji(self, icon_id: str) -> str:
        """Convert icon identifier to emoji.
        
        Args:
            icon_id: Weather icon identifier
            
        Returns:
            Emoji representation of the weather
        """
        icon_map = {
            "0": "☀️",  # Sunny
            "1": "🌤️",  # Partly cloudy
            "2": "⛅",  # Cloudy
            "3": "🌧️",  # Rainy
            "4": "⛈️",  # Stormy
            "5": "🌨️",  # Snowy
            "sunny": "☀️",
            "partly_cloudy": "🌤️",
            "cloudy": "⛅",
            "rainy": "🌧️",
            "stormy": "⛈️",
            "snowy": "🌨️",
            "clear": "☀️",
            "rain": "🌧️",
            "snow": "🌨️",
            "thunderstorm": "⛈️"
        }
        
        return icon_map.get(str(icon_id).lower(), "🌤️")
        
    def update_data(self, day: Optional[str] = None, icon: Optional[str] = None, 
                   high: Optional[int] = None, low: Optional[int] = None):
        """Update the card data.
        
        Args:
            day: New day text
            icon: New icon identifier
            high: New high temperature
            low: New low temperature
        """
        if day is not None:
            self.day = day
            self.day_label.configure(text=day)
            
        if icon is not None:
            self.icon = icon
            icon_text = self._get_icon_emoji(icon)
            self.icon_label.configure(text=icon_text)
            
        if high is not None or low is not None:
            if high is not None:
                self.high = high
            if low is not None:
                self.low = low
            temp_text = f"{self.high}°/{self.low}°"
            self.temp_label.configure(text=temp_text)
            
    def set_highlight(self, highlighted: bool = True):
        """Set the card highlight state.
        
        Args:
            highlighted: Whether to highlight the card
        """
        if highlighted:
            self.configure(border_color=DataTerminalTheme.ACCENT)
        else:
            self.configure(border_color=DataTerminalTheme.BORDER)