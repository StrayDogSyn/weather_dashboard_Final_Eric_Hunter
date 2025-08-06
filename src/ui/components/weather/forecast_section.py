"""Forecast Section Component.

Reusable component for displaying weather forecast with chart and cards.
"""

from datetime import datetime, timedelta

from src.ui.components.forecast_day_card import ForecastDayCard
from src.ui.safe_widgets import SafeCTkFrame, SafeCTkLabel
from src.ui.theme import DataTerminalTheme

class ForecastSection(SafeCTkFrame):
    """Reusable forecast section component with chart and cards."""

    def __init__(self, parent, temp_unit="C", on_card_click=None, **kwargs):
        """Initialize forecast section.

        Args:
            parent: Parent widget
            temp_unit: Temperature unit (C or F)
            on_card_click: Callback for forecast card clicks
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
        self.on_card_click = on_card_click

        # UI components
        self.temp_chart = None
        self.forecast_cards = []

        self._create_ui()

    def _create_ui(self):
        """Create the forecast section UI components."""
        # Title
        forecast_title = SafeCTkLabel(
            self,
            text="📊 Temperature Forecast",
            font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        forecast_title.pack(pady=(15, 10))

        # Import and create chart
        try:
            from src.ui.components.simple_temperature_chart import SimpleTemperatureChart

            self.temp_chart = SimpleTemperatureChart(self, fg_color=DataTerminalTheme.CARD_BG)
            self.temp_chart.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        except ImportError:
            # Fallback if chart component is not available
            chart_placeholder = SafeCTkLabel(
                self,
                text="Temperature Chart\n(Chart component not available)",
                font=(DataTerminalTheme.FONT_FAMILY, 14),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                height=200,
            )
            chart_placeholder.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Add 5-day forecast cards below the chart
        self._create_forecast_cards()

    def _create_forecast_cards(self):
        """Create 5-day forecast cards using enhanced ForecastDayCard component."""
        forecast_frame = SafeCTkFrame(self, fg_color="transparent")
        forecast_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Configure grid for equal distribution
        for i in range(5):
            forecast_frame.grid_columnconfigure(i, weight=1)

        # Store forecast cards for later updates
        self.forecast_cards = []

        # Create 5 enhanced forecast cards
        for i in range(5):
            # Calculate day and date
            forecast_date = datetime.now() + timedelta(days=i)
            day_name = forecast_date.strftime("%a")
            date_str = forecast_date.strftime("%m/%d")

            # Create enhanced forecast card with click handler
            day_card = ForecastDayCard(
                forecast_frame,
                day=day_name,
                date=date_str,
                icon="01d",  # Default sunny icon
                high=22,
                low=15,
                precipitation=0.0,
                wind_speed=0.0,
                temp_unit=self.temp_unit,
                on_click=self._on_forecast_card_click,
            )

            day_card.grid(row=0, column=i, padx=6, pady=3, sticky="ew")
            self.forecast_cards.append(day_card)

            # Add staggered animation
            try:
                day_card.animate_in(delay=i * 100)
            except AttributeError:
                # Animation method not available

                pass

    def _on_forecast_card_click(self, card):
        """Handle forecast card click.

        Args:
            card: The clicked forecast card
        """
        if self.on_card_click:
            self.on_card_click(card)

    def update_forecast_data(self, weather_data):
        """Update forecast section with new weather data.

        Args:
            weather_data: Dictionary containing weather and forecast information
        """
        if not weather_data:
            return

        # Update temperature chart
        if self.temp_chart and hasattr(self.temp_chart, "update_chart"):
            try:
                self.temp_chart.update_chart(weather_data)
            except Exception as e:
                print(f"Error updating temperature chart: {e}")

        # Update forecast cards
        self._update_forecast_cards(weather_data)

    def _update_forecast_cards(self, weather_data):
        """Update forecast cards with new data.

        Args:
            weather_data: Dictionary containing forecast information
        """
        forecast_data = weather_data.get("forecast", [])

        if forecast_data:
            self._update_cards_with_forecast_data(forecast_data)
        else:
            # Use sample data if no forecast available
            base_temp = weather_data.get("temperature", 20)
            self._update_cards_with_sample_data(base_temp)

    def _update_cards_with_forecast_data(self, forecast_data):
        """Update cards with actual forecast data.

        Args:
            forecast_data: List of forecast data for multiple days
        """
        daily_forecasts = self._parse_daily_forecasts(forecast_data)

        for i, card in enumerate(self.forecast_cards):
            if i < len(daily_forecasts):
                day_data = daily_forecasts[i]
                card.update_data(
                    icon=day_data.get("icon", "01d"),
                    high=day_data.get("high", 22),
                    low=day_data.get("low", 15),
                    precipitation=day_data.get("precipitation", 0.0),
                    wind_speed=day_data.get("wind_speed", 0.0),
                )

    def _update_cards_with_sample_data(self, base_temp):
        """Update cards with sample data when forecast is unavailable.

        Args:
            base_temp: Base temperature for generating sample data
        """
        import random

        for i, card in enumerate(self.forecast_cards):
            # Generate sample data with some variation
            temp_variation = random.randint(-5, 5)
            high_temp = base_temp + temp_variation + random.randint(2, 8)
            low_temp = base_temp + temp_variation - random.randint(2, 6)

            card.update_data(
                icon="01d",  # Default sunny
                high=high_temp,
                low=low_temp,
                precipitation=random.uniform(0, 30),
                wind_speed=random.uniform(5, 25),
            )

    def _parse_daily_forecasts(self, forecast_data):
        """Parse forecast data into daily summaries.

        Args:
            forecast_data: Raw forecast data

        Returns:
            List of daily forecast dictionaries
        """
        daily_forecasts = []

        # Group forecast data by day and extract daily highs/lows
        current_date = None
        daily_temps = []
        daily_conditions = []

        for item in forecast_data[:40]:  # Limit to reasonable number of items
            try:
                # Extract date from timestamp
                if "dt" in item:
                    item_date = datetime.fromtimestamp(item["dt"]).date()
                elif "time" in item:
                    item_date = datetime.fromisoformat(item["time"]).date()
                else:
                    continue

                # If new day, process previous day's data
                if current_date and item_date != current_date:
                    if daily_temps:
                        daily_forecasts.append(
                            {
                                "high": max(daily_temps),
                                "low": min(daily_temps),
                                "icon": daily_conditions[0] if daily_conditions else "01d",
                                "precipitation": 0.0,  # Could be calculated from data
                                "wind_speed": 10.0,  # Could be calculated from data
                            }
                        )
                    daily_temps = []
                    daily_conditions = []

                current_date = item_date

                # Extract temperature
                if "main" in item and "temp" in item["main"]:
                    daily_temps.append(item["main"]["temp"])
                elif "temperature" in item:
                    daily_temps.append(item["temperature"])

                # Extract weather condition
                if "weather" in item and item["weather"]:
                    daily_conditions.append(item["weather"][0].get("icon", "01d"))

            except (KeyError, ValueError, TypeError):
                continue

        # Process last day
        if daily_temps:
            daily_forecasts.append(
                {
                    "high": max(daily_temps),
                    "low": min(daily_temps),
                    "icon": daily_conditions[0] if daily_conditions else "01d",
                    "precipitation": 0.0,
                    "wind_speed": 10.0,
                }
            )

        return daily_forecasts[:5]  # Return only 5 days

    def update_temperature_unit(self, new_unit):
        """Update temperature unit for all forecast cards.

        Args:
            new_unit: New temperature unit (C or F)
        """
        self.temp_unit = new_unit

        for card in self.forecast_cards:
            if hasattr(card, "update_temperature_unit"):
                card.update_temperature_unit(new_unit)
