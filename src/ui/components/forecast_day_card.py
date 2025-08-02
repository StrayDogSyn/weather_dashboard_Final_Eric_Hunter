import customtkinter as ctk
from typing import Optional, Callable
from datetime import datetime
from src.ui.theme import DataTerminalTheme
from src.ui.theme_manager import theme_manager


class ForecastDayCard(ctk.CTkFrame):
    """Enhanced forecast card widget for displaying daily weather information with interactive features."""
    
    def __init__(self, parent, day: str = "", date: str = "", icon: str = "", 
                 high: int = 0, low: int = 0, precipitation: float = 0.0, 
                 wind_speed: float = 0.0, temp_unit: str = "C", 
                 on_click: Optional[Callable] = None, **kwargs):
        """Initialize the enhanced forecast day card.
        
        Args:
            parent: Parent widget
            day: Day of the week (e.g., "Mon", "Tue")
            date: Date string (e.g., "Jan 15")
            icon: Weather icon identifier
            high: High temperature
            low: Low temperature
            precipitation: Precipitation probability (0-1)
            wind_speed: Wind speed in m/s
            temp_unit: Temperature unit ("C" or "F")
            on_click: Callback function for card click
        """
        # Set default styling with enhanced appearance
        current_theme = theme_manager.get_current_theme()
        default_kwargs = {
            "fg_color": current_theme.get("card", "#1A1A1A"),
            "corner_radius": 12,
            "border_width": 1,
            "border_color": current_theme.get("border", "#333333"),
            "width": 140,
            "height": 180,
            "cursor": "hand2" if on_click else "arrow"
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        # Data properties
        self.day = day
        self.date = date
        self.icon = icon
        self.high = high
        self.low = low
        self.precipitation = precipitation
        self.wind_speed = wind_speed
        self.temp_unit = temp_unit
        self.on_click = on_click
        
        # Animation and interaction state
        self._is_hovered = False
        self._original_fg_color = self.cget("fg_color")
        self._animation_id = None
        
        self._create_widgets()
        self._setup_interactions()
        
        # Subscribe to theme changes
        theme_manager.add_observer(self._on_theme_changed)
        
    def _create_widgets(self):
        """Create and layout the enhanced card widgets."""
        # Day label
        current_theme = theme_manager.get_current_theme()
        self.day_label = ctk.CTkLabel(
            self,
            text=self.day,
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=current_theme.get("text", "#E0E0E0")
        )
        self.day_label.pack(pady=(8, 2))
        
        # Date label
        self.date_label = ctk.CTkLabel(
            self,
            text=self.date,
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=current_theme.get("secondary", "#008F11")
        )
        self.date_label.pack(pady=(0, 5))
        
        # Weather icon
        icon_text = self._get_icon_emoji(self.icon)
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon_text,
            font=ctk.CTkFont(family="Consolas", size=28)
        )
        self.icon_label.pack(pady=3)
        
        # Temperature range with unit conversion
        temp_text = self._format_temperature()
        self.temp_label = ctk.CTkLabel(
            self,
            text=temp_text,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=current_theme.get("primary", "#00FF41")
        )
        self.temp_label.pack(pady=2)
        
        # Precipitation probability
        if self.precipitation > 0:
            precip_text = f"💧 {int(self.precipitation * 100)}%"
            self.precip_label = ctk.CTkLabel(
                self,
                text=precip_text,
                font=ctk.CTkFont(family="Consolas", size=9),
                text_color=current_theme.get("accent", "#00FF41")
            )
            self.precip_label.pack(pady=1)
        
        # Wind speed indicator
        if self.wind_speed > 0:
            wind_text = f"💨 {self.wind_speed:.1f} m/s"
            self.wind_label = ctk.CTkLabel(
                self,
                text=wind_text,
                font=ctk.CTkFont(family="Consolas", size=9),
                text_color=current_theme.get("secondary", "#008F11")
            )
            self.wind_label.pack(pady=(1, 8))
        else:
            # Add padding if no wind info
            ctk.CTkLabel(self, text="", height=8).pack()
        
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
    
    def _format_temperature(self) -> str:
        """Format temperature with proper unit conversion."""
        if self.temp_unit == "F":
            high_f = int((self.high * 9/5) + 32)
            low_f = int((self.low * 9/5) + 32)
            return f"{high_f}°F/{low_f}°F"
        else:
            return f"{self.high}°C/{self.low}°C"
    
    def _setup_interactions(self):
        """Setup mouse interactions and hover effects."""
        # Bind events to all widgets for consistent interaction
        widgets_to_bind = [self]
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                widgets_to_bind.append(child)
        
        for widget in widgets_to_bind:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            if self.on_click:
                widget.bind("<Button-1>", self._on_click)
    
    def _on_enter(self, event=None):
        """Handle mouse enter event with hover effect."""
        if not self._is_hovered:
            self._is_hovered = True
            self._animate_hover(True)
    
    def _on_leave(self, event=None):
        """Handle mouse leave event."""
        if self._is_hovered:
            self._is_hovered = False
            self._animate_hover(False)
    
    def _on_click(self, event=None):
        """Handle card click event."""
        if self.on_click:
            # Add click animation
            self._animate_click()
            self.on_click(self)
    
    def _animate_hover(self, entering: bool):
        """Animate hover effect with elevation shadow."""
        if self._animation_id:
            self.after_cancel(self._animation_id)
        
        if entering:
            # Hover in - add elevation effect
            current_theme = theme_manager.get_current_theme()
            self.configure(
                border_color=current_theme.get("accent", "#00FF41"),
                border_width=2
            )
            # Simulate elevation with slight color change
            hover_color = self._lighten_color(current_theme.get("card", "#1A1A1A"), 0.1)
            self.configure(fg_color=hover_color)
        else:
            # Hover out - restore original appearance
            current_theme = theme_manager.get_current_theme()
            self.configure(
                border_color=current_theme.get("border", "#333333"),
                border_width=1,
                fg_color=current_theme.get("card", "#1A1A1A")
            )
    
    def _animate_click(self):
        """Animate click effect."""
        # Quick scale effect simulation
        original_border = self.cget("border_width")
        self.configure(border_width=3)
        self._animation_id = self.after(100, lambda: self.configure(border_width=original_border))
    
    def _lighten_color(self, color: str, factor: float) -> str:
        """Lighten a color by a given factor."""
        try:
            # Simple color lightening - in a real implementation, 
            # you'd want proper color manipulation
            if color.startswith('#'):
                # Convert hex to RGB, lighten, convert back
                hex_color = color.lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                lightened = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
                return f"#{lightened[0]:02x}{lightened[1]:02x}{lightened[2]:02x}"
            return color
        except:
            return color
    
    def _on_theme_changed(self):
        """Handle theme change updates."""
        try:
            # Update colors
            current_theme = theme_manager.get_current_theme()
            self.configure(
                fg_color=current_theme.get("card", "#1A1A1A"),
                border_color=current_theme.get("border", "#333333")
            )
            
            # Update text colors
            if hasattr(self, 'day_label'):
                self.day_label.configure(text_color=current_theme.get("text", "#E0E0E0"))
            if hasattr(self, 'date_label'):
                self.date_label.configure(text_color=current_theme.get("secondary", "#008F11"))
            if hasattr(self, 'temp_label'):
                self.temp_label.configure(text_color=current_theme.get("primary", "#00FF41"))
            if hasattr(self, 'precip_label'):
                self.precip_label.configure(text_color=current_theme.get("accent", "#00FF41"))
            if hasattr(self, 'wind_label'):
                self.wind_label.configure(text_color=current_theme.get("secondary", "#008F11"))
        except Exception as e:
            pass  # Silently handle theme update errors
        
    def update_data(self, day: Optional[str] = None, date: Optional[str] = None,
                   icon: Optional[str] = None, high: Optional[int] = None, 
                   low: Optional[int] = None, precipitation: Optional[float] = None,
                   wind_speed: Optional[float] = None, temp_unit: Optional[str] = None):
        """Update the card data with enhanced parameters.
        
        Args:
            day: New day text
            date: New date text
            icon: New icon identifier
            high: New high temperature
            low: New low temperature
            precipitation: New precipitation probability
            wind_speed: New wind speed
            temp_unit: New temperature unit
        """
        if day is not None:
            self.day = day
            self.day_label.configure(text=day)
        
        if date is not None:
            self.date = date
            self.date_label.configure(text=date)
            
        if icon is not None:
            self.icon = icon
            icon_text = self._get_icon_emoji(icon)
            self.icon_label.configure(text=icon_text)
        
        if temp_unit is not None:
            self.temp_unit = temp_unit
            
        if high is not None or low is not None or temp_unit is not None:
            if high is not None:
                self.high = high
            if low is not None:
                self.low = low
            temp_text = self._format_temperature()
            self.temp_label.configure(text=temp_text)
        
        if precipitation is not None:
            self.precipitation = precipitation
            if hasattr(self, 'precip_label'):
                if precipitation > 0:
                    self.precip_label.configure(text=f"💧 {int(precipitation * 100)}%")
                else:
                    self.precip_label.configure(text="")
        
        if wind_speed is not None:
            self.wind_speed = wind_speed
            if hasattr(self, 'wind_label'):
                if wind_speed > 0:
                    self.wind_label.configure(text=f"💨 {wind_speed:.1f} m/s")
                else:
                    self.wind_label.configure(text="")
            
    def set_highlight(self, highlighted: bool = True):
        """Set the card highlight state.
        
        Args:
            highlighted: Whether to highlight the card
        """
        current_theme = theme_manager.get_current_theme()
        if highlighted:
            self.configure(border_color=current_theme.get("accent", "#00FF41"))
        else:
            self.configure(border_color=current_theme.get("border", "#333333"))
    
    def animate_in(self, delay: int = 0):
        """Animate card entrance with stagger effect.
        
        Args:
            delay: Delay in milliseconds before animation starts
        """
        # Start invisible
        original_fg = self.cget("fg_color")
        self.configure(fg_color="transparent")
        
        def show_card():
            self.configure(fg_color=original_fg)
            # Add a subtle scale-in effect by manipulating border
            self.configure(border_width=3)
            self.after(200, lambda: self.configure(border_width=1))
        
        self.after(delay, show_card)
    
    def destroy(self):
        """Clean up resources when destroying the widget."""
        # Remove theme observer
        try:
            theme_manager.remove_observer(self._on_theme_changed)
        except:
            pass
        
        # Cancel any pending animations
        if self._animation_id:
            self.after_cancel(self._animation_id)
        
        super().destroy()