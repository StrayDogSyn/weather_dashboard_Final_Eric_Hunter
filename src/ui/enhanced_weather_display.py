"""Enhanced Weather Display - Extended UI Components

Displays comprehensive weather data including air quality, astronomy, and alerts.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from ..services.enhanced_weather_service import (
    EnhancedWeatherData, AirQualityData, AstronomicalData, WeatherAlert
)
from .weather_display import WeatherMetricCard


class AirQualityCard(tk.Frame):
    """Air quality display card."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger('weather_dashboard.air_quality_card')
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create air quality widgets."""
        # Title
        self.title_label = tk.Label(
            self,
            text="🌬️ AIR QUALITY",
            font=("Consolas", 12, "bold"),
            fg="#00FFAB",
            bg="#1a1a1a"
        )
        
        # AQI display
        self.aqi_frame = tk.Frame(self, bg="#1a1a1a")
        
        self.aqi_value_label = tk.Label(
            self.aqi_frame,
            text="--",
            font=("Consolas", 24, "bold"),
            fg="#FFFFFF",
            bg="#1a1a1a"
        )
        
        self.aqi_description_label = tk.Label(
            self.aqi_frame,
            text="No Data",
            font=("Consolas", 10),
            fg="#888888",
            bg="#1a1a1a"
        )
        
        # Health recommendation
        self.health_label = tk.Label(
            self,
            text="",
            font=("Consolas", 9),
            fg="#CCCCCC",
            bg="#1a1a1a",
            wraplength=200,
            justify="left"
        )
        
        # Pollutant details frame
        self.pollutants_frame = tk.Frame(self, bg="#1a1a1a")
        
        # Create pollutant labels
        self.pollutant_labels = {}
        pollutants = ['PM2.5', 'PM10', 'O₃', 'NO₂', 'SO₂', 'CO']
        
        for i, pollutant in enumerate(pollutants):
            frame = tk.Frame(self.pollutants_frame, bg="#1a1a1a")
            
            name_label = tk.Label(
                frame,
                text=pollutant,
                font=("Consolas", 8),
                fg="#888888",
                bg="#1a1a1a"
            )
            
            value_label = tk.Label(
                frame,
                text="--",
                font=("Consolas", 8, "bold"),
                fg="#00FFAB",
                bg="#1a1a1a"
            )
            
            name_label.pack(side="left")
            value_label.pack(side="right")
            
            self.pollutant_labels[pollutant.lower().replace('₃', '3').replace('₂', '2')] = value_label
            frame.grid(row=i//2, column=i%2, sticky="ew", padx=2, pady=1)
        
        # Configure grid weights
        self.pollutants_frame.grid_columnconfigure(0, weight=1)
        self.pollutants_frame.grid_columnconfigure(1, weight=1)
    
    def _setup_layout(self):
        """Setup widget layout."""
        self.title_label.pack(pady=(0, 10))
        
        self.aqi_frame.pack(pady=(0, 10))
        self.aqi_value_label.pack()
        self.aqi_description_label.pack()
        
        self.health_label.pack(pady=(0, 10), fill="x")
        self.pollutants_frame.pack(fill="x")
    
    def update_air_quality(self, air_quality: Optional[AirQualityData]):
        """Update air quality display."""
        if not air_quality:
            self.aqi_value_label.config(text="--")
            self.aqi_description_label.config(text="No Data")
            self.health_label.config(text="")
            
            for label in self.pollutant_labels.values():
                label.config(text="--")
            return
        
        # Update AQI
        self.aqi_value_label.config(text=str(air_quality.aqi))
        self.aqi_description_label.config(text=air_quality.get_aqi_description())
        
        # Color code AQI
        aqi_colors = {
            1: "#00E676",  # Good - Green
            2: "#FFEB3B",  # Fair - Yellow
            3: "#FF9800",  # Moderate - Orange
            4: "#F44336",  # Poor - Red
            5: "#9C27B0"   # Very Poor - Purple
        }
        color = aqi_colors.get(air_quality.aqi, "#FFFFFF")
        self.aqi_value_label.config(fg=color)
        
        # Update health recommendation
        self.health_label.config(text=air_quality.get_health_recommendation())
        
        # Update pollutant values
        pollutant_data = {
            'pm2.5': f"{air_quality.pm2_5:.1f}",
            'pm10': f"{air_quality.pm10:.1f}",
            'o3': f"{air_quality.o3:.1f}",
            'no2': f"{air_quality.no2:.1f}",
            'so2': f"{air_quality.so2:.1f}",
            'co': f"{air_quality.co:.0f}"
        }
        
        for pollutant, value in pollutant_data.items():
            if pollutant in self.pollutant_labels:
                self.pollutant_labels[pollutant].config(text=value)


class AstronomicalCard(tk.Frame):
    """Astronomical data display card."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger('weather_dashboard.astronomical_card')
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create astronomical widgets."""
        # Title
        self.title_label = tk.Label(
            self,
            text="🌅 ASTRONOMY",
            font=("Consolas", 12, "bold"),
            fg="#00FFAB",
            bg="#1a1a1a"
        )
        
        # Sun times frame
        self.sun_frame = tk.Frame(self, bg="#1a1a1a")
        
        # Sunrise
        self.sunrise_frame = tk.Frame(self.sun_frame, bg="#1a1a1a")
        tk.Label(
            self.sunrise_frame,
            text="🌅 Sunrise",
            font=("Consolas", 9),
            fg="#888888",
            bg="#1a1a1a"
        ).pack(side="left")
        
        self.sunrise_label = tk.Label(
            self.sunrise_frame,
            text="--:--",
            font=("Consolas", 9, "bold"),
            fg="#00FFAB",
            bg="#1a1a1a"
        )
        self.sunrise_label.pack(side="right")
        
        # Sunset
        self.sunset_frame = tk.Frame(self.sun_frame, bg="#1a1a1a")
        tk.Label(
            self.sunset_frame,
            text="🌇 Sunset",
            font=("Consolas", 9),
            fg="#888888",
            bg="#1a1a1a"
        ).pack(side="left")
        
        self.sunset_label = tk.Label(
            self.sunset_frame,
            text="--:--",
            font=("Consolas", 9, "bold"),
            fg="#00FFAB",
            bg="#1a1a1a"
        )
        self.sunset_label.pack(side="right")
        
        # Day length
        self.daylight_frame = tk.Frame(self.sun_frame, bg="#1a1a1a")
        tk.Label(
            self.daylight_frame,
            text="☀️ Daylight",
            font=("Consolas", 9),
            fg="#888888",
            bg="#1a1a1a"
        ).pack(side="left")
        
        self.daylight_label = tk.Label(
            self.daylight_frame,
            text="--h --m",
            font=("Consolas", 9, "bold"),
            fg="#00FFAB",
            bg="#1a1a1a"
        )
        self.daylight_label.pack(side="right")
        
        # Moon phase frame
        self.moon_frame = tk.Frame(self, bg="#1a1a1a")
        
        self.moon_emoji_label = tk.Label(
            self.moon_frame,
            text="🌑",
            font=("Consolas", 20),
            bg="#1a1a1a"
        )
        
        self.moon_phase_label = tk.Label(
            self.moon_frame,
            text="New Moon",
            font=("Consolas", 10, "bold"),
            fg="#FFFFFF",
            bg="#1a1a1a"
        )
    
    def _setup_layout(self):
        """Setup widget layout."""
        self.title_label.pack(pady=(0, 10))
        
        self.sun_frame.pack(fill="x", pady=(0, 10))
        self.sunrise_frame.pack(fill="x", pady=2)
        self.sunset_frame.pack(fill="x", pady=2)
        self.daylight_frame.pack(fill="x", pady=2)
        
        self.moon_frame.pack(pady=(10, 0))
        self.moon_emoji_label.pack()
        self.moon_phase_label.pack()
    
    def update_astronomical(self, astronomical: Optional[AstronomicalData]):
        """Update astronomical display."""
        if not astronomical:
            self.sunrise_label.config(text="--:--")
            self.sunset_label.config(text="--:--")
            self.daylight_label.config(text="--h --m")
            self.moon_emoji_label.config(text="🌑")
            self.moon_phase_label.config(text="No Data")
            return
        
        # Update sun times
        self.sunrise_label.config(text=astronomical.sunrise.strftime("%H:%M"))
        self.sunset_label.config(text=astronomical.sunset.strftime("%H:%M"))
        
        # Update day length
        hours = astronomical.day_length.seconds // 3600
        minutes = (astronomical.day_length.seconds % 3600) // 60
        self.daylight_label.config(text=f"{hours}h {minutes}m")
        
        # Update moon phase
        self.moon_emoji_label.config(text=astronomical.get_moon_phase_emoji())
        self.moon_phase_label.config(text=astronomical.get_moon_phase_name())


class WeatherAlertsCard(tk.Frame):
    """Weather alerts display card."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger('weather_dashboard.weather_alerts_card')
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create weather alerts widgets."""
        # Title
        self.title_label = tk.Label(
            self,
            text="⚠️ WEATHER ALERTS",
            font=("Consolas", 12, "bold"),
            fg="#00FFAB",
            bg="#1a1a1a"
        )
        
        # Alerts container with scrollbar
        self.alerts_container = tk.Frame(self, bg="#1a1a1a")
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(
            self.alerts_container,
            bg="#1a1a1a",
            highlightthickness=0,
            height=150
        )
        
        self.scrollbar = ttk.Scrollbar(
            self.alerts_container,
            orient="vertical",
            command=self.canvas.yview
        )
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#1a1a1a")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # No alerts message
        self.no_alerts_label = tk.Label(
            self.scrollable_frame,
            text="No active weather alerts",
            font=("Consolas", 10),
            fg="#888888",
            bg="#1a1a1a"
        )
    
    def _setup_layout(self):
        """Setup widget layout."""
        self.title_label.pack(pady=(0, 10))
        
        self.alerts_container.pack(fill="both", expand=True)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.no_alerts_label.pack(pady=20)
    
    def update_alerts(self, alerts: List[WeatherAlert]):
        """Update weather alerts display."""
        # Clear existing alerts
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not alerts:
            self.no_alerts_label = tk.Label(
                self.scrollable_frame,
                text="No active weather alerts",
                font=("Consolas", 10),
                fg="#888888",
                bg="#1a1a1a"
            )
            self.no_alerts_label.pack(pady=20)
            return
        
        # Display alerts
        for i, alert in enumerate(alerts):
            alert_frame = tk.Frame(
                self.scrollable_frame,
                bg="#2a2a2a",
                relief="solid",
                bd=1
            )
            alert_frame.pack(fill="x", padx=5, pady=2)
            
            # Alert header
            header_frame = tk.Frame(alert_frame, bg="#2a2a2a")
            header_frame.pack(fill="x", padx=5, pady=2)
            
            # Severity emoji and event
            tk.Label(
                header_frame,
                text=f"{alert.get_severity_emoji()} {alert.event}",
                font=("Consolas", 10, "bold"),
                fg=alert.get_severity_color(),
                bg="#2a2a2a"
            ).pack(side="left")
            
            # Time range
            time_text = f"{alert.start_time.strftime('%H:%M')} - {alert.end_time.strftime('%H:%M')}"
            tk.Label(
                header_frame,
                text=time_text,
                font=("Consolas", 8),
                fg="#888888",
                bg="#2a2a2a"
            ).pack(side="right")
            
            # Description
            if alert.description:
                desc_label = tk.Label(
                    alert_frame,
                    text=alert.description[:100] + "..." if len(alert.description) > 100 else alert.description,
                    font=("Consolas", 8),
                    fg="#CCCCCC",
                    bg="#2a2a2a",
                    wraplength=250,
                    justify="left"
                )
                desc_label.pack(fill="x", padx=5, pady=(0, 5))


class EnhancedWeatherDisplayFrame(tk.Frame):
    """Enhanced weather display with comprehensive data."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger('weather_dashboard.enhanced_weather_display')
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create enhanced weather display widgets."""
        # Main weather info (existing)
        self.main_weather_frame = tk.Frame(self, bg="#1a1a1a")
        
        # Location and temperature
        self.location_label = tk.Label(
            self.main_weather_frame,
            text="--",
            font=("Consolas", 16, "bold"),
            fg="#00FFAB",
            bg="#1a1a1a"
        )
        
        self.temperature_label = tk.Label(
            self.main_weather_frame,
            text="--°",
            font=("Consolas", 48, "bold"),
            fg="#FFFFFF",
            bg="#1a1a1a"
        )
        
        self.description_label = tk.Label(
            self.main_weather_frame,
            text="--",
            font=("Consolas", 12),
            fg="#888888",
            bg="#1a1a1a"
        )
        
        self.feels_like_label = tk.Label(
            self.main_weather_frame,
            text="Feels like --°",
            font=("Consolas", 10),
            fg="#CCCCCC",
            bg="#1a1a1a"
        )
        
        # Enhanced data container
        self.enhanced_container = tk.Frame(self, bg="#1a1a1a")
        
        # Left column - Air Quality
        self.left_column = tk.Frame(self.enhanced_container, bg="#1a1a1a")
        self.air_quality_card = AirQualityCard(self.left_column, bg="#1a1a1a")
        
        # Middle column - Astronomical
        self.middle_column = tk.Frame(self.enhanced_container, bg="#1a1a1a")
        self.astronomical_card = AstronomicalCard(self.middle_column, bg="#1a1a1a")
        
        # Right column - Alerts
        self.right_column = tk.Frame(self.enhanced_container, bg="#1a1a1a")
        self.alerts_card = WeatherAlertsCard(self.right_column, bg="#1a1a1a")
        
        # Basic metrics grid (existing functionality)
        self.metrics_frame = tk.Frame(self, bg="#1a1a1a")
        self.metrics_frame.grid_columnconfigure(0, weight=1)
        self.metrics_frame.grid_columnconfigure(1, weight=1)
        self.metrics_frame.grid_columnconfigure(2, weight=1)
        
        # Create metric cards
        self.metric_cards = {
            'humidity': WeatherMetricCard(self.metrics_frame, "💧", "Humidity", "%"),
            'pressure': WeatherMetricCard(self.metrics_frame, "🌡️", "Pressure", "hPa"),
            'visibility': WeatherMetricCard(self.metrics_frame, "👁️", "Visibility", "km"),
            'wind_speed': WeatherMetricCard(self.metrics_frame, "💨", "Wind Speed", "m/s"),
            'wind_direction': WeatherMetricCard(self.metrics_frame, "🧭", "Wind Dir", "°"),
            'cloudiness': WeatherMetricCard(self.metrics_frame, "☁️", "Cloudiness", "%"),
            'temp_min': WeatherMetricCard(self.metrics_frame, "🔽", "Min Temp", "°C"),
            'temp_max': WeatherMetricCard(self.metrics_frame, "🔼", "Max Temp", "°C"),
            'uv_index': WeatherMetricCard(self.metrics_frame, "☀️", "UV Index", "")
        }
        
        # Position metric cards in grid
        positions = [
            ('humidity', 0, 0), ('pressure', 0, 1), ('visibility', 0, 2),
            ('wind_speed', 1, 0), ('wind_direction', 1, 1), ('cloudiness', 1, 2),
            ('temp_min', 2, 0), ('temp_max', 2, 1), ('uv_index', 2, 2)
        ]
        
        for metric, row, col in positions:
            self.metric_cards[metric].grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
    
    def _setup_layout(self):
        """Setup enhanced weather display layout."""
        # Main weather info
        self.main_weather_frame.pack(pady=(0, 20))
        self.location_label.pack()
        self.temperature_label.pack()
        self.description_label.pack()
        self.feels_like_label.pack()
        
        # Enhanced data container
        self.enhanced_container.pack(fill="x", pady=(0, 20))
        
        # Configure columns
        self.enhanced_container.grid_columnconfigure(0, weight=1)
        self.enhanced_container.grid_columnconfigure(1, weight=1)
        self.enhanced_container.grid_columnconfigure(2, weight=1)
        
        # Pack enhanced cards
        self.left_column.grid(row=0, column=0, sticky="nsew", padx=5)
        self.air_quality_card.pack(fill="both", expand=True)
        
        self.middle_column.grid(row=0, column=1, sticky="nsew", padx=5)
        self.astronomical_card.pack(fill="both", expand=True)
        
        self.right_column.grid(row=0, column=2, sticky="nsew", padx=5)
        self.alerts_card.pack(fill="both", expand=True)
        
        # Basic metrics
        self.metrics_frame.pack(fill="x")
    
    def update_weather_display(self, weather_data: EnhancedWeatherData):
        """Update enhanced weather display with comprehensive data."""
        try:
            # Update main weather info
            location_text = f"{weather_data.city}, {weather_data.country}"
            self.location_label.config(text=location_text)
            self.temperature_label.config(text=f"{weather_data.temperature}°")
            self.description_label.config(text=weather_data.description)
            self.feels_like_label.config(text=f"Feels like {weather_data.feels_like}°")
            
            # Update basic metrics
            metrics_data = {
                'humidity': weather_data.humidity,
                'pressure': weather_data.pressure,
                'visibility': weather_data.visibility,
                'wind_speed': weather_data.wind_speed,
                'wind_direction': weather_data.wind_direction,
                'cloudiness': weather_data.clouds,
                'temp_min': weather_data.temp_min,
                'temp_max': weather_data.temp_max,
                'uv_index': getattr(weather_data, 'uv_index', 0)
            }
            
            for metric, value in metrics_data.items():
                if metric in self.metric_cards:
                    self.metric_cards[metric].update_value(value)
            
            # Update enhanced data
            self.air_quality_card.update_air_quality(weather_data.air_quality)
            self.astronomical_card.update_astronomical(weather_data.astronomical)
            self.alerts_card.update_alerts(weather_data.alerts or [])
            
            self.logger.info(f"✅ Enhanced weather display updated for {weather_data.city}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update enhanced weather display: {e}")
    
    def clear_display(self):
        """Clear enhanced weather display."""
        self.location_label.config(text="--")
        self.temperature_label.config(text="--°")
        self.description_label.config(text="--")
        self.feels_like_label.config(text="Feels like --°")
        
        # Clear metric cards
        for card in self.metric_cards.values():
            card.update_value("--")
        
        # Clear enhanced data
        self.air_quality_card.update_air_quality(None)
        self.astronomical_card.update_astronomical(None)
        self.alerts_card.update_alerts([])
        
        self.logger.info("🧹 Enhanced weather display cleared")