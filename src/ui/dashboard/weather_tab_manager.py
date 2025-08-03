"""Weather tab manager for handling all weather-related functionality."""

import logging
from datetime import datetime, timedelta

import customtkinter as ctk

from src.ui.components.forecast_day_card import ForecastDayCard
from src.ui.theme import DataTerminalTheme


class WeatherTabManager:
    """Manages the weather tab functionality and UI components."""

    def __init__(self, parent_dashboard, weather_tab):
        """Initialize the weather tab manager.

        Args:
            parent_dashboard: Reference to the main dashboard
            weather_tab: The weather tab frame
        """
        self.dashboard = parent_dashboard
        self.weather_tab = weather_tab
        self.logger = logging.getLogger(__name__)

        # Initialize state
        self.forecast_cards = []
        self.metric_labels = {}
        self.temp_chart = None
        self.temp_toggle_btn = None

        # Create weather tab content
        self._create_weather_tab_content()

    def _create_weather_tab_content(self):
        """Create enhanced weather tab with proper layout."""
        # Configure grid for 3-column layout with better proportions
        self.weather_tab.grid_columnconfigure(
            0, weight=1, minsize=350
        )  # Current weather
        self.weather_tab.grid_columnconfigure(
            1, weight=2, minsize=500
        )  # Forecast chart
        self.weather_tab.grid_columnconfigure(
            2, weight=1, minsize=300
        )  # Additional metrics
        self.weather_tab.grid_rowconfigure(0, weight=1)

        # Left column - Current weather card with glassmorphic styling
        self._create_current_weather_card()

        # Middle column - Forecast chart
        self._create_forecast_section()

        # Right column - Additional metrics and details
        self._create_additional_metrics_section()

    def _create_current_weather_card(self):
        """Create the current weather card."""
        self.weather_card = ctk.CTkFrame(
            self.weather_tab,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        self.weather_card.grid(
            row=0, column=0, sticky="nsew", padx=(15, 8), pady=15
        )

        # Weather icon and city
        self.city_label = ctk.CTkLabel(
            self.weather_card,
            text="Loading...",
            font=(DataTerminalTheme.FONT_FAMILY, 24, "bold"),
            text_color=DataTerminalTheme.TEXT,
        )
        self.city_label.pack(pady=(25, 8))

        # Large temperature display
        self.temp_label = ctk.CTkLabel(
            self.weather_card,
            text="--°C",
            font=(DataTerminalTheme.FONT_FAMILY, 60, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        self.temp_label.pack(pady=15)

        # Weather condition with icon
        self.condition_label = ctk.CTkLabel(
            self.weather_card,
            text="--",
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.condition_label.pack(pady=(0, 20))

        # Weather metrics grid
        self._create_weather_metrics()

        # Temperature conversion toggle
        self._create_temperature_toggle()

    def _create_weather_metrics(self):
        """Create weather metrics grid."""
        metrics_frame = ctk.CTkFrame(self.weather_card, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=20, pady=15)

        # Create metric cards
        metrics = [
            ("💧", "Humidity", "--"),
            ("💨", "Wind", "--"),
            ("🌡️", "Feels Like", "--"),
            ("👁️", "Visibility", "--"),
            ("🧭", "Pressure", "--"),
            ("☁️", "Cloudiness", "--"),
        ]

        for i, (icon, name, value) in enumerate(metrics):
            metric_card = ctk.CTkFrame(
                metrics_frame,
                fg_color=DataTerminalTheme.BACKGROUND,
                corner_radius=4,
                border_width=1,
                border_color=DataTerminalTheme.BORDER,
            )
            metric_card.pack(pady=1, fill="x")

            # Icon and name
            header_frame = ctk.CTkFrame(metric_card, fg_color="transparent")
            header_frame.pack(fill="x", padx=8, pady=(4, 1))

            icon_label = ctk.CTkLabel(
                header_frame, text=icon, font=(DataTerminalTheme.FONT_FAMILY, 10)
            )
            icon_label.pack(side="left")

            name_label = ctk.CTkLabel(
                header_frame,
                text=name,
                font=(DataTerminalTheme.FONT_FAMILY, 9),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
            )
            name_label.pack(side="left", padx=(3, 0))

            # Value
            value_label = ctk.CTkLabel(
                metric_card,
                text=value,
                font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
                text_color=DataTerminalTheme.PRIMARY,
            )
            value_label.pack(pady=(0, 4))

            # Store reference
            self.metric_labels[name.lower().replace(" ", "_")] = value_label

    def _create_temperature_toggle(self):
        """Create temperature unit toggle button."""
        toggle_frame = ctk.CTkFrame(
            self.weather_card,
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
            text="°C",
            width=55,
            height=28,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.HOVER,
            command=self._enhanced_toggle_temperature_unit,
        )
        self.temp_toggle_btn.pack(side="left", padx=(0, 12), pady=8)

        # Add micro-interactions to temperature toggle button
        if hasattr(self.dashboard, "micro_interactions"):
            self.dashboard.micro_interactions.add_hover_effect(self.temp_toggle_btn)
            self.dashboard.micro_interactions.add_click_effect(self.temp_toggle_btn)

    def _create_forecast_section(self):
        """Create forecast section with chart."""
        forecast_container = ctk.CTkFrame(
            self.weather_tab,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        forecast_container.grid(row=0, column=1, sticky="nsew", padx=8, pady=15)

        # Title
        forecast_title = ctk.CTkLabel(
            forecast_container,
            text="📊 Temperature Forecast",
            font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        forecast_title.pack(pady=(15, 10))

        # Import and create chart
        try:
            from src.ui.components.simple_temperature_chart import SimpleTemperatureChart

            self.temp_chart = SimpleTemperatureChart(
                forecast_container, fg_color=DataTerminalTheme.CARD_BG
            )
            self.temp_chart.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        except ImportError as e:
            self.logger.warning(f"Could not load temperature chart: {e}")
            # Create placeholder
            placeholder = ctk.CTkLabel(
                forecast_container,
                text="Temperature Chart\n(Chart component not available)",
                font=(DataTerminalTheme.FONT_FAMILY, 14),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
            )
            placeholder.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Add 5-day forecast cards below the chart
        self._create_forecast_cards(forecast_container)

    def _create_forecast_cards(self, parent):
        """Create 5-day forecast cards using enhanced ForecastDayCard component."""
        forecast_frame = ctk.CTkFrame(parent, fg_color="transparent")
        forecast_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Configure grid for equal distribution
        for i in range(5):
            forecast_frame.grid_columnconfigure(i, weight=1)

        # Create 5 enhanced forecast cards
        for i in range(5):
            # Calculate day and date
            forecast_date = datetime.now() + timedelta(days=i)
            day_name = forecast_date.strftime("%a")
            date_str = forecast_date.strftime("%m/%d")

            # Create enhanced forecast card with click handler
            try:
                day_card = ForecastDayCard(
                    forecast_frame,
                    day=day_name,
                    date=date_str,
                    icon="01d",  # Default sunny icon
                    high=22,
                    low=15,
                    precipitation=0.0,
                    wind_speed=0.0,
                    temp_unit=getattr(self.dashboard, "temp_unit", "C"),
                    on_click=self._on_forecast_card_click,
                )

                day_card.grid(row=0, column=i, padx=6, pady=3, sticky="ew")
                self.forecast_cards.append(day_card)

                # Add staggered animation
                if hasattr(day_card, "animate_in"):
                    day_card.animate_in(delay=i * 100)

            except Exception as e:
                self.logger.warning(f"Could not create forecast card {i}: {e}")
                # Create simple placeholder card
                placeholder_card = ctk.CTkFrame(
                    forecast_frame,
                    fg_color=DataTerminalTheme.CARD_BG,
                    corner_radius=8,
                    border_width=1,
                    border_color=DataTerminalTheme.BORDER,
                )
                placeholder_card.grid(row=0, column=i, padx=6, pady=3, sticky="ew")

                ctk.CTkLabel(
                    placeholder_card,
                    text=f"{day_name}\n{date_str}\n--°",
                    font=(DataTerminalTheme.FONT_FAMILY, 10),
                    text_color=DataTerminalTheme.TEXT,
                ).pack(pady=10)

                self.forecast_cards.append(placeholder_card)

    def _create_additional_metrics_section(self):
        """Create additional metrics section for the third column."""
        metrics_container = ctk.CTkFrame(
            self.weather_tab,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        metrics_container.grid(row=0, column=2, sticky="nsew", padx=(8, 15), pady=15)

        # Title
        metrics_title = ctk.CTkLabel(
            metrics_container,
            text="📈 Weather Details",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        metrics_title.pack(pady=(15, 10))

        # Air Quality Section
        self._create_air_quality_section(metrics_container)

        # Sun Times Section
        self._create_sun_times_section(metrics_container)

        # Weather Alerts Section
        self._create_weather_alerts_section(metrics_container)

    def _create_air_quality_section(self, parent):
        """Create air quality section."""
        air_quality_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        air_quality_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            air_quality_frame,
            text="🌬️ Air Quality",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(pady=(8, 3))

        self.air_quality_label = ctk.CTkLabel(
            air_quality_frame,
            text="Good (AQI: 45)",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.SUCCESS,
        )
        self.air_quality_label.pack(pady=(0, 8))

    def _create_sun_times_section(self, parent):
        """Create sun times section."""
        sun_times_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        sun_times_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            sun_times_frame,
            text="☀️ Sun Times",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(pady=(8, 5))

        self.sunrise_label = ctk.CTkLabel(
            sun_times_frame,
            text="🌅 Sunrise: 6:45 AM",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.sunrise_label.pack(pady=(0, 2))

        self.sunset_label = ctk.CTkLabel(
            sun_times_frame,
            text="🌇 Sunset: 7:30 PM",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.sunset_label.pack(pady=(0, 8))

    def _create_weather_alerts_section(self, parent):
        """Create weather alerts section."""
        alerts_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        alerts_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            alerts_frame,
            text="⚠️ Weather Alerts",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(pady=(8, 5))

        self.alerts_label = ctk.CTkLabel(
            alerts_frame,
            text="No active alerts",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.SUCCESS,
        )
        self.alerts_label.pack(pady=(0, 8))

    def _enhanced_toggle_temperature_unit(self):
        """Enhanced temperature unit toggle with animations."""
        try:
            # Get current unit
            current_unit = getattr(self.dashboard, "temp_unit", "C")
            new_unit = "F" if current_unit == "C" else "C"

            # Update dashboard unit
            self.dashboard.temp_unit = new_unit

            # Update button text with animation
            self.temp_toggle_btn.configure(text=f"°{new_unit}")

            # Add click animation if available
            if hasattr(self.dashboard, "micro_interactions"):
                self.dashboard.micro_interactions.add_click_effect(self.temp_toggle_btn)

            # Convert all temperatures
            if hasattr(self.dashboard, "_convert_all_temperatures"):
                self.dashboard._convert_all_temperatures(current_unit, new_unit)

            # Refresh weather display
            if hasattr(self.dashboard, "_refresh_weather_with_new_units"):
                self.dashboard._refresh_weather_with_new_units()

            self.logger.info(f"Temperature unit changed to {new_unit}")

        except Exception as e:
            self.logger.error(f"Error toggling temperature unit: {e}")

    def _on_forecast_card_click(self, card):
        """Handle forecast card click events."""
        try:
            # Find the card index
            card_index = None
            for i, forecast_card in enumerate(self.forecast_cards):
                if forecast_card == card:
                    card_index = i
                    break

            if card_index is not None:
                # Delegate to dashboard's hourly breakdown method
                if hasattr(self.dashboard, "_show_hourly_breakdown"):
                    self.dashboard._show_hourly_breakdown(card_index)
                else:
                    self.logger.warning("Hourly breakdown method not available")

        except Exception as e:
            self.logger.error(f"Error handling forecast card click: {e}")

    def update_weather_display(self, weather_data):
        """Update the weather display with new data."""
        try:
            if not weather_data:
                return

            # Update city label
            city_name = weather_data.get("name", "Unknown")
            self.city_label.configure(text=city_name)

            # Update temperature
            temp = weather_data.get("main", {}).get("temp", 0)
            temp_unit = getattr(self.dashboard, "temp_unit", "C")
            self.temp_label.configure(text=f"{temp:.0f}°{temp_unit}")

            # Update condition
            condition = weather_data.get("weather", [{}])[0].get("description", "--")
            self.condition_label.configure(text=condition.title())

            # Update metrics
            self._update_weather_metrics(weather_data)

            # Update forecast cards if available
            if hasattr(self.dashboard, "_update_forecast_cards"):
                self.dashboard._update_forecast_cards(weather_data)

            # Update temperature chart
            if self.temp_chart and hasattr(self.temp_chart, "update_data"):
                self.temp_chart.update_data(weather_data)

        except Exception as e:
            self.logger.error(f"Error updating weather display: {e}")

    def _update_weather_metrics(self, weather_data):
        """Update weather metrics display."""
        try:
            main_data = weather_data.get("main", {})
            wind_data = weather_data.get("wind", {})
            visibility = weather_data.get("visibility", 0) / 1000  # Convert to km
            clouds = weather_data.get("clouds", {}).get("all", 0)

            # Update humidity
            if "humidity" in self.metric_labels:
                humidity = main_data.get("humidity", 0)
                self.metric_labels["humidity"].configure(text=f"{humidity}%")

            # Update wind
            if "wind" in self.metric_labels:
                wind_speed = wind_data.get("speed", 0)
                wind_dir = wind_data.get("deg", 0)
                self.metric_labels["wind"].configure(text=f"{wind_speed:.1f} m/s {wind_dir}°")

            # Update feels like
            if "feels_like" in self.metric_labels:
                feels_like = main_data.get("feels_like", 0)
                temp_unit = getattr(self.dashboard, "temp_unit", "C")
                self.metric_labels["feels_like"].configure(text=f"{feels_like:.0f}°{temp_unit}")

            # Update visibility
            if "visibility" in self.metric_labels:
                self.metric_labels["visibility"].configure(text=f"{visibility:.1f} km")

            # Update pressure
            if "pressure" in self.metric_labels:
                pressure = main_data.get("pressure", 0)
                self.metric_labels["pressure"].configure(text=f"{pressure} hPa")

            # Update cloudiness
            if "cloudiness" in self.metric_labels:
                self.metric_labels["cloudiness"].configure(text=f"{clouds}%")

        except Exception as e:
            self.logger.error(f"Error updating weather metrics: {e}")

    def update_forecast_cards(self, forecast_data):
        """Update forecast cards with new data."""
        try:
            if not forecast_data or not self.forecast_cards:
                return

            # Parse forecast data and update cards
            daily_forecasts = self._parse_daily_forecasts(forecast_data)

            for i, (card, forecast) in enumerate(zip(self.forecast_cards, daily_forecasts)):
                if hasattr(card, "update_data"):
                    card.update_data(
                        high=forecast.get("high", 0),
                        low=forecast.get("low", 0),
                        icon=forecast.get("icon", "01d"),
                        precipitation=forecast.get("precipitation", 0),
                        wind_speed=forecast.get("wind_speed", 0),
                    )

        except Exception as e:
            self.logger.error(f"Error updating forecast cards: {e}")

    def _parse_daily_forecasts(self, forecast_data):
        """Parse forecast data into daily summaries."""
        try:
            daily_forecasts = []

            # Handle different forecast data formats
            if "list" in forecast_data:
                # OpenWeatherMap format
                forecast_list = forecast_data["list"]

                # Group by day and calculate daily highs/lows
                daily_data = {}
                for item in forecast_list:
                    date = datetime.fromtimestamp(item["dt"]).date()
                    if date not in daily_data:
                        daily_data[date] = {
                            "temps": [],
                            "conditions": [],
                            "precipitation": 0,
                            "wind_speeds": [],
                        }

                    daily_data[date]["temps"].append(item["main"]["temp"])
                    daily_data[date]["conditions"].append(item["weather"][0]["icon"])
                    daily_data[date]["wind_speeds"].append(item.get("wind", {}).get("speed", 0))

                    # Add precipitation if available
                    if "rain" in item:
                        daily_data[date]["precipitation"] += item["rain"].get("3h", 0)
                    if "snow" in item:
                        daily_data[date]["precipitation"] += item["snow"].get("3h", 0)

                # Convert to daily forecasts
                for date, data in sorted(daily_data.items())[:5]:
                    daily_forecasts.append(
                        {
                            "high": max(data["temps"]),
                            "low": min(data["temps"]),
                            "icon": data["conditions"][0] if data["conditions"] else "01d",
                            "precipitation": data["precipitation"],
                            "wind_speed": (
                                sum(data["wind_speeds"]) / len(data["wind_speeds"])
                                if data["wind_speeds"]
                                else 0
                            ),
                        }
                    )

            # Fill with placeholder data if not enough forecasts
            while len(daily_forecasts) < 5:
                daily_forecasts.append(
                    {"high": 20, "low": 10, "icon": "01d", "precipitation": 0, "wind_speed": 0}
                )

            return daily_forecasts[:5]

        except Exception as e:
            self.logger.error(f"Error parsing daily forecasts: {e}")
            # Return placeholder data
            return [{"high": 20, "low": 10, "icon": "01d", "precipitation": 0, "wind_speed": 0}] * 5
