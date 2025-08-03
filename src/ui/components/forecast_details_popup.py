"""Forecast Details Popup Component

Provides detailed forecast information in a popup window when a forecast card is clicked.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import customtkinter as ctk

from ..themes.data_terminal_theme import DataTerminalTheme


class ForecastDetailsPopup:
    """Popup window showing detailed forecast information for a specific day."""

    def __init__(self, parent, forecast_data: Dict[str, Any], hourly_data: Optional[List] = None):
        """Initialize the forecast details popup.

        Args:
            parent: Parent window
            forecast_data: Daily forecast data
            hourly_data: Optional hourly forecast data for the day
        """
        self.parent = parent
        self.forecast_data = forecast_data
        self.hourly_data = hourly_data or []

        # Create popup window
        self.popup = ctk.CTkToplevel(parent)
        self.popup.title(
            f"Forecast Details - {forecast_data.get('day', 'Day')} {forecast_data.get('date', '')}"
        )
        self.popup.geometry("600x700")
        self.popup.resizable(False, False)

        # Configure popup styling
        self.popup.configure(fg_color=DataTerminalTheme.BG_PRIMARY)

        # Center the popup
        self._center_popup()

        # Make popup modal
        self.popup.transient(parent)
        self.popup.grab_set()

        # Create UI elements
        self._create_ui()

        # Bind close events
        self.popup.protocol("WM_DELETE_WINDOW", self.close)
        self.popup.bind("<Escape>", lambda e: self.close())

    def _center_popup(self):
        """Center the popup window on the parent."""
        self.popup.update_idletasks()

        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Calculate popup position
        popup_width = 600
        popup_height = 700
        x = parent_x + (parent_width - popup_width) // 2
        y = parent_y + (parent_height - popup_height) // 2

        self.popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

    def _create_ui(self):
        """Create the popup UI elements."""
        # Main container with scrollable frame
        main_frame = ctk.CTkScrollableFrame(
            self.popup,
            fg_color="transparent",
            scrollbar_button_color=DataTerminalTheme.ACCENT_PRIMARY,
            scrollbar_button_hover_color=DataTerminalTheme.ACCENT_SECONDARY,
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header section
        self._create_header(main_frame)

        # Overview section
        self._create_overview(main_frame)

        # Temperature curve section
        self._create_temperature_section(main_frame)

        # Hourly breakdown section
        self._create_hourly_section(main_frame)

        # Additional details section
        self._create_details_section(main_frame)

        # Forecast accuracy section
        self._create_accuracy_section(main_frame)

        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            command=self.close,
            fg_color=DataTerminalTheme.ACCENT_PRIMARY,
            hover_color=DataTerminalTheme.ACCENT_SECONDARY,
            height=40,
            font=("Consolas", 14, "bold"),
        )
        close_btn.pack(pady=(20, 0))

    def _create_header(self, parent):
        """Create the header section with day, date, and main weather info."""
        header_frame = ctk.CTkFrame(parent, fg_color=DataTerminalTheme.CARD_BG, corner_radius=12)
        header_frame.pack(fill="x", pady=(0, 15))

        # Day and date
        day_label = ctk.CTkLabel(
            header_frame,
            text=f"{self.forecast_data.get('day', 'Day')}, {self.forecast_data.get('date', '--/--')}",
            font=("Consolas", 24, "bold"),
            text_color=DataTerminalTheme.TEXT_PRIMARY,
        )
        day_label.pack(pady=(20, 5))

        # Weather description
        desc_label = ctk.CTkLabel(
            header_frame,
            text=self.forecast_data.get("description", "Unknown"),
            font=("Consolas", 16),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        desc_label.pack(pady=(0, 20))

    def _create_overview(self, parent):
        """Create the overview section with key metrics."""
        overview_frame = ctk.CTkFrame(parent, fg_color=DataTerminalTheme.CARD_BG, corner_radius=12)
        overview_frame.pack(fill="x", pady=(0, 15))

        # Title
        title_label = ctk.CTkLabel(
            overview_frame,
            text="📊 Overview",
            font=("Consolas", 18, "bold"),
            text_color=DataTerminalTheme.ACCENT_PRIMARY,
        )
        title_label.pack(pady=(15, 10))

        # Metrics grid
        metrics_frame = ctk.CTkFrame(overview_frame, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Configure grid
        for i in range(2):
            metrics_frame.grid_columnconfigure(i, weight=1)

        # Temperature range
        temp_frame = ctk.CTkFrame(
            metrics_frame, fg_color=DataTerminalTheme.BG_SECONDARY, corner_radius=8
        )
        temp_frame.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")

        ctk.CTkLabel(
            temp_frame,
            text="🌡️ Temperature",
            font=("Consolas", 12, "bold"),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        ).pack(pady=(10, 5))

        temp_text = f"{self.forecast_data.get('high_temp', '--')}° / {self.forecast_data.get('low_temp', '--')}°"
        ctk.CTkLabel(
            temp_frame,
            text=temp_text,
            font=("Consolas", 16, "bold"),
            text_color=DataTerminalTheme.TEXT_PRIMARY,
        ).pack(pady=(0, 10))

        # Precipitation
        precip_frame = ctk.CTkFrame(
            metrics_frame, fg_color=DataTerminalTheme.BG_SECONDARY, corner_radius=8
        )
        precip_frame.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")

        ctk.CTkLabel(
            precip_frame,
            text="🌧️ Precipitation",
            font=("Consolas", 12, "bold"),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        ).pack(pady=(10, 5))

        precip_prob = self.forecast_data.get("precipitation", 0.0)
        precip_text = (
            f"{int(precip_prob * 100)}%" if isinstance(precip_prob, float) else f"{precip_prob}%"
        )
        ctk.CTkLabel(
            precip_frame,
            text=precip_text,
            font=("Consolas", 16, "bold"),
            text_color=DataTerminalTheme.TEXT_PRIMARY,
        ).pack(pady=(0, 10))

        # Humidity
        humidity_frame = ctk.CTkFrame(
            metrics_frame, fg_color=DataTerminalTheme.BG_SECONDARY, corner_radius=8
        )
        humidity_frame.grid(row=1, column=0, padx=(0, 10), pady=5, sticky="ew")

        ctk.CTkLabel(
            humidity_frame,
            text="💧 Humidity",
            font=("Consolas", 12, "bold"),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        ).pack(pady=(10, 5))

        humidity = self.forecast_data.get("humidity", 0)
        ctk.CTkLabel(
            humidity_frame,
            text=f"{humidity}%",
            font=("Consolas", 16, "bold"),
            text_color=DataTerminalTheme.TEXT_PRIMARY,
        ).pack(pady=(0, 10))

        # Wind
        wind_frame = ctk.CTkFrame(
            metrics_frame, fg_color=DataTerminalTheme.BG_SECONDARY, corner_radius=8
        )
        wind_frame.grid(row=1, column=1, padx=(10, 0), pady=5, sticky="ew")

        ctk.CTkLabel(
            wind_frame,
            text="💨 Wind Speed",
            font=("Consolas", 12, "bold"),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        ).pack(pady=(10, 5))

        wind_speed = self.forecast_data.get("wind_speed", 0.0)
        ctk.CTkLabel(
            wind_frame,
            text=f"{wind_speed:.1f} m/s",
            font=("Consolas", 16, "bold"),
            text_color=DataTerminalTheme.TEXT_PRIMARY,
        ).pack(pady=(0, 10))

    def _create_temperature_section(self, parent):
        """Create temperature curve visualization section."""
        temp_frame = ctk.CTkFrame(parent, fg_color=DataTerminalTheme.CARD_BG, corner_radius=12)
        temp_frame.pack(fill="x", pady=(0, 15))

        # Title
        title_label = ctk.CTkLabel(
            temp_frame,
            text="📈 Temperature Trend",
            font=("Consolas", 18, "bold"),
            text_color=DataTerminalTheme.ACCENT_PRIMARY,
        )
        title_label.pack(pady=(15, 10))

        # Simple temperature visualization (text-based for now)
        if self.hourly_data:
            self._create_hourly_temp_chart(temp_frame)
        else:
            # Fallback to daily high/low
            temp_info = ctk.CTkLabel(
                temp_frame,
                text=f"High: {self.forecast_data.get('high_temp', '--')}° | Low: {self.forecast_data.get('low_temp', '--')}°",
                font=("Consolas", 14),
                text_color=DataTerminalTheme.TEXT_PRIMARY,
            )
            temp_info.pack(pady=(0, 15))

    def _create_hourly_temp_chart(self, parent):
        """Create a simple text-based hourly temperature chart."""
        chart_frame = ctk.CTkFrame(parent, fg_color=DataTerminalTheme.BG_SECONDARY, corner_radius=8)
        chart_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Sample hourly temperatures (would be replaced with real data)
        hours = ["6AM", "9AM", "12PM", "3PM", "6PM", "9PM"]
        temps = [15, 18, 22, 25, 23, 19]  # Sample data

        chart_text = "Time:  " + "  ".join(f"{h:>5}" for h in hours) + "\n"
        chart_text += "Temp:  " + "  ".join(f"{t:>3}°" for t in temps)

        chart_label = ctk.CTkLabel(
            chart_frame,
            text=chart_text,
            font=("Consolas", 12),
            text_color=DataTerminalTheme.TEXT_PRIMARY,
            justify="left",
        )
        chart_label.pack(pady=15)

    def _create_hourly_section(self, parent):
        """Create hourly breakdown section."""
        hourly_frame = ctk.CTkFrame(parent, fg_color=DataTerminalTheme.CARD_BG, corner_radius=12)
        hourly_frame.pack(fill="x", pady=(0, 15))

        # Title
        title_label = ctk.CTkLabel(
            hourly_frame,
            text="⏰ Hourly Breakdown",
            font=("Consolas", 18, "bold"),
            text_color=DataTerminalTheme.ACCENT_PRIMARY,
        )
        title_label.pack(pady=(15, 10))

        # Hourly data (sample for now)
        hourly_container = ctk.CTkFrame(hourly_frame, fg_color="transparent")
        hourly_container.pack(fill="x", padx=20, pady=(0, 15))

        # Sample hourly entries
        sample_hours = [
            {"time": "6:00 AM", "temp": 15, "condition": "Clear", "precip": 0},
            {"time": "12:00 PM", "temp": 22, "condition": "Sunny", "precip": 0},
            {"time": "6:00 PM", "temp": 19, "condition": "Partly Cloudy", "precip": 10},
        ]

        for hour_data in sample_hours:
            hour_frame = ctk.CTkFrame(
                hourly_container, fg_color=DataTerminalTheme.BG_SECONDARY, corner_radius=6
            )
            hour_frame.pack(fill="x", pady=2)

            hour_text = f"{hour_data['time']:>10} | {hour_data['temp']:>3}° | {hour_data['condition']:>15} | {hour_data['precip']:>3}%"
            hour_label = ctk.CTkLabel(
                hour_frame,
                text=hour_text,
                font=("Consolas", 11),
                text_color=DataTerminalTheme.TEXT_PRIMARY,
            )
            hour_label.pack(pady=8)

    def _create_details_section(self, parent):
        """Create additional details section."""
        details_frame = ctk.CTkFrame(parent, fg_color=DataTerminalTheme.CARD_BG, corner_radius=12)
        details_frame.pack(fill="x", pady=(0, 15))

        # Title
        title_label = ctk.CTkLabel(
            details_frame,
            text="🌅 Additional Details",
            font=("Consolas", 18, "bold"),
            text_color=DataTerminalTheme.ACCENT_PRIMARY,
        )
        title_label.pack(pady=(15, 10))

        # Details grid
        details_container = ctk.CTkFrame(details_frame, fg_color="transparent")
        details_container.pack(fill="x", padx=20, pady=(0, 15))

        # Sample details
        details = [
            ("🌅 Sunrise", "6:30 AM"),
            ("🌇 Sunset", "7:45 PM"),
            ("☀️ UV Index", "6 (High)"),
            ("👁️ Visibility", "10 km"),
            ("🌪️ Pressure", "1013 hPa"),
            ("🌡️ Feels Like", f"{self.forecast_data.get('high_temp', 22)}°"),
        ]

        for i, (label, value) in enumerate(details):
            detail_frame = ctk.CTkFrame(
                details_container, fg_color=DataTerminalTheme.BG_SECONDARY, corner_radius=6
            )
            detail_frame.pack(fill="x", pady=2)

            detail_text = f"{label:>15} | {value}"
            detail_label = ctk.CTkLabel(
                detail_frame,
                text=detail_text,
                font=("Consolas", 12),
                text_color=DataTerminalTheme.TEXT_PRIMARY,
            )
            detail_label.pack(pady=8)

    def _create_accuracy_section(self, parent):
        """Create forecast accuracy indicators section."""
        accuracy_frame = ctk.CTkFrame(parent, fg_color=DataTerminalTheme.CARD_BG, corner_radius=12)
        accuracy_frame.pack(fill="x", pady=(0, 15))

        # Title
        title_label = ctk.CTkLabel(
            accuracy_frame,
            text="🎯 Forecast Accuracy",
            font=("Consolas", 18, "bold"),
            text_color=DataTerminalTheme.ACCENT_PRIMARY,
        )
        title_label.pack(pady=(15, 10))

        # Accuracy info
        accuracy_container = ctk.CTkFrame(accuracy_frame, fg_color="transparent")
        accuracy_container.pack(fill="x", padx=20, pady=(0, 15))

        # Calculate confidence based on time distance
        now = datetime.now()
        forecast_date = datetime.strptime(self.forecast_data.get("date", "01/01"), "%m/%d")
        days_ahead = (forecast_date.replace(year=now.year) - now).days

        if days_ahead <= 1:
            confidence = "95%"
            confidence_color = DataTerminalTheme.SUCCESS
        elif days_ahead <= 3:
            confidence = "85%"
            confidence_color = DataTerminalTheme.WARNING
        else:
            confidence = "70%"
            confidence_color = DataTerminalTheme.ERROR

        accuracy_info = [
            ("🎯 Confidence Level", confidence, confidence_color),
            ("🕐 Last Update", "2 hours ago", DataTerminalTheme.TEXT_PRIMARY),
            ("🌐 Provider", "OpenWeatherMap", DataTerminalTheme.TEXT_PRIMARY),
            ("📊 Model Run", "06:00 UTC", DataTerminalTheme.TEXT_PRIMARY),
        ]

        for label, value, color in accuracy_info:
            info_frame = ctk.CTkFrame(
                accuracy_container, fg_color=DataTerminalTheme.BG_SECONDARY, corner_radius=6
            )
            info_frame.pack(fill="x", pady=2)

            info_text = f"{label:>18} | {value}"
            info_label = ctk.CTkLabel(
                info_frame, text=info_text, font=("Consolas", 12), text_color=color
            )
            info_label.pack(pady=8)

    def close(self):
        """Close the popup window."""
        try:
            self.popup.grab_release()
            self.popup.destroy()
        except Exception:
            pass  # Window might already be destroyed
