"""Forecast Display Component

Consolidated forecast display widget for weather data.
"""

from datetime import datetime
from typing import List, Dict, Optional, Callable
import customtkinter as ctk
from ..glassmorphic.base_frame import GlassmorphicFrame
from ..glassmorphic.glass_button import GlassButton


class ForecastDisplay(GlassmorphicFrame):
    """Unified forecast display component with glassmorphic styling."""

    def __init__(self, parent, display_type: str = "horizontal", days: int = 5, **kwargs):
        """Initialize forecast display.
        
        Args:
            parent: Parent widget
            display_type: Layout type ("horizontal" or "vertical")
            days: Number of forecast days to display
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.display_type = display_type
        self.days = days
        self.forecast_data: List[Dict] = []
        self.day_cards: List[ctk.CTkFrame] = []
        self.on_day_click: Optional[Callable] = None
        
        # Styling
        self.card_colors = {
            "bg": ("#1A1A1A", "#2A2A2A"),
            "hover": ("#2A2A2A", "#3A3A3A"),
            "text": ("#E0E0E0", "#FFFFFF"),
            "accent": "#00FF41"
        }
        
        # Weather icon mapping
        self.weather_icons = {
            "01d": "☀️", "01n": "🌙",
            "02d": "⛅", "02n": "☁️",
            "03d": "☁️", "03n": "☁️",
            "04d": "☁️", "04n": "☁️",
            "09d": "🌧️", "09n": "🌧️",
            "10d": "🌦️", "10n": "🌧️",
            "11d": "⛈️", "11n": "⛈️",
            "13d": "❄️", "13n": "❄️",
            "50d": "🌫️", "50n": "🌫️"
        }
        
        self._setup_layout()
    
    def _setup_layout(self):
        """Setup the forecast layout."""
        if self.display_type == "horizontal":
            self.grid_columnconfigure(tuple(range(self.days)), weight=1)
            self.grid_rowconfigure(0, weight=1)
        else:  # vertical
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(tuple(range(self.days)), weight=1)
        
        # Create placeholder cards
        for i in range(self.days):
            card = self._create_day_card(i)
            self.day_cards.append(card)
    
    def _create_day_card(self, index: int) -> ctk.CTkFrame:
        """Create a forecast day card.
        
        Args:
            index: Day index
            
        Returns:
            Created card frame
        """
        # Position based on layout type
        if self.display_type == "horizontal":
            row, col = 0, index
            sticky = "nsew"
            padx = (5, 5)
            pady = (10, 10)
        else:  # vertical
            row, col = index, 0
            sticky = "ew"
            padx = (10, 10)
            pady = (2, 2)
        
        # Create card frame
        card = ctk.CTkFrame(
            self,
            fg_color=self.card_colors["bg"],
            corner_radius=12,
            border_width=1,
            border_color=("#333333", "#555555")
        )
        card.grid(row=row, column=col, sticky=sticky, padx=padx, pady=pady)
        
        # Configure card grid
        if self.display_type == "horizontal":
            card.grid_columnconfigure(0, weight=1)
            card.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
        else:
            card.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
            card.grid_rowconfigure(0, weight=1)
        
        # Create card elements
        self._create_card_elements(card, index)
        
        # Bind click event
        card.bind("<Button-1>", lambda e, idx=index: self._on_card_click(idx))
        
        return card
    
    def _create_card_elements(self, card: ctk.CTkFrame, index: int):
        """Create elements within a day card.
        
        Args:
            card: Card frame
            index: Day index
        """
        if self.display_type == "horizontal":
            # Vertical layout within card
            # Day label
            day_label = ctk.CTkLabel(
                card,
                text="---",
                font=("Consolas", 12, "bold"),
                text_color=self.card_colors["text"]
            )
            day_label.grid(row=0, column=0, pady=(10, 5))
            
            # Weather icon
            icon_label = ctk.CTkLabel(
                card,
                text="🌤️",
                font=("Segoe UI Emoji", 24)
            )
            icon_label.grid(row=1, column=0, pady=5)
            
            # High temperature
            high_temp_label = ctk.CTkLabel(
                card,
                text="--°",
                font=("Consolas", 14, "bold"),
                text_color=self.card_colors["accent"]
            )
            high_temp_label.grid(row=2, column=0, pady=2)
            
            # Low temperature
            low_temp_label = ctk.CTkLabel(
                card,
                text="--°",
                font=("Consolas", 12),
                text_color=("#888888", "#AAAAAA")
            )
            low_temp_label.grid(row=3, column=0, pady=2)
            
            # Precipitation
            precip_label = ctk.CTkLabel(
                card,
                text="💧 --%",
                font=("Consolas", 10),
                text_color=("#6699FF", "#88BBFF")
            )
            precip_label.grid(row=4, column=0, pady=(2, 10))
            
        else:  # horizontal layout within card
            # Day label
            day_label = ctk.CTkLabel(
                card,
                text="---",
                font=("Consolas", 12, "bold"),
                text_color=self.card_colors["text"],
                width=60
            )
            day_label.grid(row=0, column=0, padx=(10, 5), pady=10)
            
            # Weather icon
            icon_label = ctk.CTkLabel(
                card,
                text="🌤️",
                font=("Segoe UI Emoji", 20),
                width=40
            )
            icon_label.grid(row=0, column=1, padx=5, pady=10)
            
            # Temperature range
            temp_frame = ctk.CTkFrame(card, fg_color="transparent")
            temp_frame.grid(row=0, column=2, padx=5, pady=10, sticky="ew")
            
            high_temp_label = ctk.CTkLabel(
                temp_frame,
                text="--°",
                font=("Consolas", 12, "bold"),
                text_color=self.card_colors["accent"]
            )
            high_temp_label.pack(side="left", padx=(0, 5))
            
            low_temp_label = ctk.CTkLabel(
                temp_frame,
                text="--°",
                font=("Consolas", 12),
                text_color=("#888888", "#AAAAAA")
            )
            low_temp_label.pack(side="left")
            
            # Precipitation
            precip_label = ctk.CTkLabel(
                card,
                text="💧 --%",
                font=("Consolas", 10),
                text_color=("#6699FF", "#88BBFF"),
                width=60
            )
            precip_label.grid(row=0, column=3, padx=5, pady=10)
            
            # Description
            desc_label = ctk.CTkLabel(
                card,
                text="---",
                font=("Consolas", 10),
                text_color=("#AAAAAA", "#CCCCCC"),
                width=80
            )
            desc_label.grid(row=0, column=4, padx=(5, 10), pady=10)
        
        # Store references to labels for updates
        card.day_label = day_label
        card.icon_label = icon_label
        card.high_temp_label = high_temp_label
        card.low_temp_label = low_temp_label
        card.precip_label = precip_label
        if self.display_type == "vertical":
            card.desc_label = desc_label
    
    def update_forecast(self, forecast_data: List[Dict]):
        """Update forecast data and display.
        
        Args:
            forecast_data: List of forecast day dictionaries
        """
        self.forecast_data = forecast_data[:self.days]
        
        for i, card in enumerate(self.day_cards):
            if i < len(self.forecast_data):
                self._update_card(card, self.forecast_data[i])
            else:
                self._clear_card(card)
    
    def _update_card(self, card: ctk.CTkFrame, day_data: Dict):
        """Update a single day card with data.
        
        Args:
            card: Card frame to update
            day_data: Day forecast data
        """
        try:
            # Extract data with defaults
            day_name = day_data.get("day", "---")
            icon_id = day_data.get("icon", "01d")
            high_temp = day_data.get("high_temp", 0)
            low_temp = day_data.get("low_temp", 0)
            precipitation = day_data.get("precipitation", 0)
            description = day_data.get("description", "---")
            
            # Update labels
            card.day_label.configure(text=day_name)
            card.icon_label.configure(text=self._get_weather_icon(icon_id))
            card.high_temp_label.configure(text=f"{high_temp:.0f}°")
            card.low_temp_label.configure(text=f"{low_temp:.0f}°")
            card.precip_label.configure(text=f"💧 {precipitation:.0f}%")
            
            if hasattr(card, "desc_label"):
                card.desc_label.configure(text=description.title())
            
        except Exception as e:
            print(f"Error updating forecast card: {e}")
            self._clear_card(card)
    
    def _clear_card(self, card: ctk.CTkFrame):
        """Clear a day card to show placeholder data.
        
        Args:
            card: Card frame to clear
        """
        try:
            card.day_label.configure(text="---")
            card.icon_label.configure(text="🌤️")
            card.high_temp_label.configure(text="--°")
            card.low_temp_label.configure(text="--°")
            card.precip_label.configure(text="💧 --%")
            
            if hasattr(card, "desc_label"):
                card.desc_label.configure(text="---")
                
        except Exception as e:
            print(f"Error clearing forecast card: {e}")
    
    def _get_weather_icon(self, icon_id: str) -> str:
        """Get weather emoji for icon ID.
        
        Args:
            icon_id: Weather icon ID
            
        Returns:
            Weather emoji
        """
        return self.weather_icons.get(icon_id, "🌤️")
    
    def _on_card_click(self, index: int):
        """Handle day card click.
        
        Args:
            index: Clicked day index
        """
        if self.on_day_click and index < len(self.forecast_data):
            self.on_day_click(index, self.forecast_data[index])
    
    def set_click_callback(self, callback: Callable[[int, Dict], None]):
        """Set callback for day card clicks.
        
        Args:
            callback: Function to call when day is clicked
        """
        self.on_day_click = callback
    
    def set_display_type(self, display_type: str):
        """Change display layout type.
        
        Args:
            display_type: New layout type ("horizontal" or "vertical")
        """
        if display_type != self.display_type:
            self.display_type = display_type
            
            # Clear existing cards
            for card in self.day_cards:
                card.destroy()
            self.day_cards.clear()
            
            # Recreate layout
            self._setup_layout()
            
            # Update with current data
            if self.forecast_data:
                self.update_forecast(self.forecast_data)
    
    def set_days_count(self, days: int):
        """Change number of forecast days to display.
        
        Args:
            days: Number of days to show
        """
        if days != self.days and days > 0:
            self.days = days
            
            # Clear existing cards
            for card in self.day_cards:
                card.destroy()
            self.day_cards.clear()
            
            # Recreate layout
            self._setup_layout()
            
            # Update with current data
            if self.forecast_data:
                self.update_forecast(self.forecast_data)