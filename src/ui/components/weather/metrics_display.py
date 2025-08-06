"""Weather Metrics Display Component.

Reusable component for displaying weather metrics like humidity, wind, pressure, etc.
"""


from src.ui.theme import DataTerminalTheme
import customtkinter as ctk


class MetricsDisplay(ctk.CTkFrame):
    """Reusable weather metrics display component."""

    def __init__(self, parent, temp_unit="C", **kwargs):
        """Initialize metrics display.

        Args:
            parent: Parent widget
            temp_unit: Temperature unit (C or F)
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.temp_unit = temp_unit
        self.metric_labels = {}

        self._create_ui()

    def _create_ui(self):
        """Create the metrics display UI."""
        # Define metrics with icons and default values
        metrics = [
            ("💧", "Humidity", "--"),
            ("💨", "Wind", "--"),
            ("🌡️", "Feels Like", "--"),
            ("👁️", "Visibility", "--"),
            ("🧭", "Pressure", "--"),
            ("☁️", "Cloudiness", "--"),
        ]

        # Create metric cards
        for i, (icon, name, value) in enumerate(metrics):
            metric_card = self._create_metric_card(icon, name, value)
            metric_card.pack(pady=1, fill="x")

    def _create_metric_card(self, icon, name, value):
        """Create a single metric card.

        Args:
            icon: Emoji icon for the metric
            name: Display name of the metric
            value: Initial value to display

        Returns:
            CTkFrame: The created metric card
        """
        metric_card = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=4,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )

        # Header with icon and name
        header_frame = ctk.CTkFrame(metric_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=8, pady=(4, 1))

        icon_label = ctk.CTkLabel(header_frame, text=icon, font=(DataTerminalTheme.FONT_FAMILY, 10))
        icon_label.pack(side="left")

        name_label = ctk.CTkLabel(
            header_frame,
            text=name,
            font=(DataTerminalTheme.FONT_FAMILY, 9),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        name_label.pack(side="left", padx=(3, 0))

        # Value label
        value_label = ctk.CTkLabel(
            metric_card,
            text=value,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        value_label.pack(pady=(0, 4))

        # Store reference for updates
        metric_key = name.lower().replace(" ", "_")
        self.metric_labels[metric_key] = value_label

        return metric_card

    def update_metrics(self, weather_data):
        """Update all metrics with new weather data.

        Args:
            weather_data: Dictionary containing weather information
        """
        if not weather_data:
            return

        # Update individual metrics
        self._update_humidity(weather_data)
        self._update_wind(weather_data)
        self._update_feels_like(weather_data)
        self._update_visibility(weather_data)
        self._update_pressure(weather_data)
        self._update_cloudiness(weather_data)

    def _update_humidity(self, weather_data):
        """Update humidity metric.

        Args:
            weather_data: Weather data dictionary
        """
        humidity = weather_data.get("humidity")
        if humidity is not None:
            self._set_metric_value("humidity", f"{humidity}%")
        else:
            self._set_metric_value("humidity", "--")

    def _update_wind(self, weather_data):
        """Update wind metric.

        Args:
            weather_data: Weather data dictionary
        """
        wind_speed = weather_data.get("wind_speed")
        wind_direction = weather_data.get("wind_direction")

        if wind_speed is not None:
            wind_text = f"{wind_speed:.1f} m/s"
            if wind_direction is not None:
                wind_text += f" {self._get_wind_direction(wind_direction)}"
            self._set_metric_value("wind", wind_text)
        else:
            self._set_metric_value("wind", "--")

    def _update_feels_like(self, weather_data):
        """Update feels like temperature metric.

        Args:
            weather_data: Weather data dictionary
        """
        feels_like = weather_data.get("feels_like")
        if feels_like is not None:
            temp_text = f"{feels_like:.1f}°{self.temp_unit}"
            self._set_metric_value("feels_like", temp_text)
        else:
            self._set_metric_value("feels_like", "--")

    def _update_visibility(self, weather_data):
        """Update visibility metric.

        Args:
            weather_data: Weather data dictionary
        """
        visibility = weather_data.get("visibility")
        if visibility is not None:
            # Convert meters to kilometers
            visibility_km = visibility / 1000
            self._set_metric_value("visibility", f"{visibility_km:.1f} km")
        else:
            self._set_metric_value("visibility", "--")

    def _update_pressure(self, weather_data):
        """Update pressure metric.

        Args:
            weather_data: Weather data dictionary
        """
        pressure = weather_data.get("pressure")
        if pressure is not None:
            self._set_metric_value("pressure", f"{pressure} hPa")
        else:
            self._set_metric_value("pressure", "--")

    def _update_cloudiness(self, weather_data):
        """Update cloudiness metric.

        Args:
            weather_data: Weather data dictionary
        """
        cloudiness = weather_data.get("cloudiness")
        if cloudiness is not None:
            self._set_metric_value("cloudiness", f"{cloudiness}%")
        else:
            self._set_metric_value("cloudiness", "--")

    def _set_metric_value(self, metric_key, value):
        """Set the value for a specific metric.

        Args:
            metric_key: Key identifying the metric
            value: New value to display
        """
        if metric_key in self.metric_labels:
            self.metric_labels[metric_key].configure(text=value)

    def _get_wind_direction(self, degrees):
        """Convert wind direction degrees to compass direction.

        Args:
            degrees: Wind direction in degrees

        Returns:
            str: Compass direction (N, NE, E, etc.)
        """
        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]

        # Calculate index based on degrees
        index = round(degrees / 22.5) % 16
        return directions[index]

    def update_temperature_unit(self, new_unit):
        """Update temperature unit and refresh feels like display.

        Args:
            new_unit: New temperature unit (C or F)
        """
        self.temp_unit = new_unit

        # Note: This would typically trigger a refresh of the feels like temperature
        # The parent component should call update_metrics with converted data

    def reset_metrics(self):
        """Reset all metrics to default values."""
        for metric_key in self.metric_labels:
            self._set_metric_value(metric_key, "--")

    def get_metric_value(self, metric_key):
        """Get the current value of a specific metric.

        Args:
            metric_key: Key identifying the metric

        Returns:
            str: Current metric value or None if not found
        """
        if metric_key in self.metric_labels:
            return self.metric_labels[metric_key].cget("text")
        return None

    def set_custom_metric(self, metric_key, icon, name, value):
        """Add or update a custom metric.

        Args:
            metric_key: Unique key for the metric
            icon: Emoji icon for the metric
            name: Display name
            value: Initial value
        """
        # Check if metric already exists
        if metric_key in self.metric_labels:
            self._set_metric_value(metric_key, value)
        else:
            # Create new metric card
            metric_card = self._create_metric_card(icon, name, value)
            metric_card.pack(pady=1, fill="x")

    def remove_metric(self, metric_key):
        """Remove a metric from the display.

        Args:
            metric_key: Key identifying the metric to remove
        """
        if metric_key in self.metric_labels:
            # Find and destroy the parent card
            label = self.metric_labels[metric_key]
            card = label.master.master  # label -> metric_card
            card.destroy()
            del self.metric_labels[metric_key]
