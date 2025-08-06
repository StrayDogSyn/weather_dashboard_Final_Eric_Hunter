"""Current Weather Card Component.

Reusable component for displaying current weather information.
"""


from src.ui.components import MicroInteractions
from src.ui.theme import DataTerminalTheme
import customtkinter as ctk


class CurrentWeatherCard(ctk.CTkFrame):
    """Reusable current weather card component."""

    def __init__(self, parent, temp_unit="C", on_temp_toggle=None, **kwargs):
        """Initialize current weather card.

        Args:
            parent: Parent widget
            temp_unit: Temperature unit (C or F)
            on_temp_toggle: Callback for temperature unit toggle
            **kwargs: Additional frame arguments
        """
        super().__init__(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
            **kwargs,
        )

        self.temp_unit = temp_unit
        self.on_temp_toggle = on_temp_toggle
        self.micro_interactions = MicroInteractions()

        # UI components
        self.city_label = None
        self.temp_label = None
        self.condition_label = None
        self.temp_toggle_btn = None

        self._create_ui()

    def _create_ui(self):
        """Create the weather card UI components."""
        # Weather icon and city
        self.city_label = ctk.CTkLabel(
            self,
            text="Loading...",
            font=(DataTerminalTheme.FONT_FAMILY, 24, "bold"),
            text_color=DataTerminalTheme.TEXT,
        )
        self.city_label.pack(pady=(25, 8))

        # Large temperature display
        self.temp_label = ctk.CTkLabel(
            self,
            text="--°C",
            font=(DataTerminalTheme.FONT_FAMILY, 60, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        self.temp_label.pack(pady=15)

        # Weather condition with icon
        self.condition_label = ctk.CTkLabel(
            self,
            text="--",
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.condition_label.pack(pady=(0, 20))

        # Temperature conversion toggle button
        self._create_temperature_toggle()

    def _create_temperature_toggle(self):
        """Create temperature unit toggle button."""
        toggle_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=6,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        toggle_frame.pack(fill="x", padx=15, pady=(15, 20))

        toggle_label = ctk.CTkLabel(
            toggle_frame,
            text="Temperature Unit:",
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        toggle_label.pack(side="left", padx=(12, 8), pady=8)

        self.temp_toggle_btn = ctk.CTkButton(
            toggle_frame,
            text=f"°{self.temp_unit}",
            width=55,
            height=28,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.HOVER,
            command=self._on_temp_toggle_clicked,
        )
        self.temp_toggle_btn.pack(side="left", padx=(0, 12), pady=8)

        # Add micro-interactions to temperature toggle button
        self.micro_interactions.add_hover_effect(self.temp_toggle_btn)
        self.micro_interactions.add_click_effect(self.temp_toggle_btn)

    def _on_temp_toggle_clicked(self):
        """Handle temperature toggle button click."""
        if self.on_temp_toggle:
            self.on_temp_toggle()

    def update_weather_data(self, weather_data):
        """Update the weather card with new data.

        Args:
            weather_data: Dictionary containing weather information
        """
        if not weather_data:
            return

        # Update city
        city = weather_data.get("city", "Unknown Location")
        self.city_label.configure(text=city)

        # Update temperature
        temp = weather_data.get("temperature", "--")
        if temp != "--":
            temp_text = f"{temp}°{self.temp_unit}"
        else:
            temp_text = f"--°{self.temp_unit}"
        self.temp_label.configure(text=temp_text)

        # Update condition
        condition = weather_data.get("condition", "--")
        self.condition_label.configure(text=condition)

    def update_temperature_unit(self, new_unit):
        """Update the temperature unit display.

        Args:
            new_unit: New temperature unit (C or F)
        """
        self.temp_unit = new_unit
        self.temp_toggle_btn.configure(text=f"°{new_unit}")

        # Update temperature display if we have current data
        current_temp_text = self.temp_label.cget("text")
        if current_temp_text and current_temp_text != f"--°{new_unit}":
            # Extract temperature value and update unit
            try:
                temp_value = current_temp_text.split("°")[0]
                self.temp_label.configure(text=f"{temp_value}°{new_unit}")
            except (IndexError, ValueError):
                pass
