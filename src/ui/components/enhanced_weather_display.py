"""Enhanced Weather Display Component

Comprehensive weather data display with air quality, astronomical data, and alerts.
"""

import customtkinter as ctk
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import math

from ..theme import DataTerminalTheme


class EnhancedWeatherDisplay(ctk.CTkFrame):
    """Enhanced weather display with comprehensive data."""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Weather data
        self.current_weather: Optional[Dict[str, Any]] = None
        self.air_quality: Optional[Dict[str, Any]] = None
        self.astronomical: Optional[Dict[str, Any]] = None
        self.alerts: List[Dict[str, Any]] = []
        
        # Create UI
        self._create_weather_ui()
        
    def _create_weather_ui(self):
        """Create the enhanced weather display."""
        # Configure grid
        self.grid_columnconfigure((0, 1), weight=1)
        
        # Main weather card with enhanced styling
        self.main_weather_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_color=DataTerminalTheme.PRIMARY,
            border_width=2
        )
        self.main_weather_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.main_weather_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(self.main_weather_frame, fg_color="transparent")
        self.status_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 5))
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="🔄 Loading weather data...",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.status_indicator.pack(side="left")
        
        self.last_updated = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.last_updated.pack(side="right")
        
        # Current conditions section
        self._create_current_conditions()
        
        # Extended data section
        self.extended_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.extended_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        self.extended_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Air quality card
        self._create_air_quality_card()
        
        # Astronomical data card
        self._create_astronomical_card()
        
        # Weather details card
        self._create_weather_details_card()
        
        # Alerts section
        self._create_alerts_section()
        
    def _create_current_conditions(self):
        """Create enhanced current weather conditions display."""
        # Location and time with improved styling
        self.location_label = ctk.CTkLabel(
            self.main_weather_frame,
            text="🌍 Select a location to view weather",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        self.location_label.grid(row=1, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="w")
        
        self.time_label = ctk.CTkLabel(
            self.main_weather_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.time_label.grid(row=2, column=0, columnspan=3, padx=15, pady=(0, 15), sticky="w")
        
        # Temperature and condition with enhanced styling
        temp_frame = ctk.CTkFrame(self.main_weather_frame, fg_color="transparent")
        temp_frame.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        
        # Main temperature with gradient effect
        self.temp_label = ctk.CTkLabel(
            temp_frame,
            text="--°",
            font=ctk.CTkFont(size=52, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        self.temp_label.grid(row=0, column=0, sticky="w")
        
        # Feels like temperature inline
        self.feels_like_inline = ctk.CTkLabel(
            temp_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.feels_like_inline.grid(row=0, column=1, sticky="sw", padx=(10, 0), pady=(0, 8))
        
        # Weather condition with enhanced styling
        condition_frame = ctk.CTkFrame(temp_frame, fg_color="transparent")
        condition_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        
        self.condition_icon = ctk.CTkLabel(
            condition_frame,
            text="🌤️",
            font=ctk.CTkFont(size=20)
        )
        self.condition_icon.grid(row=0, column=0, sticky="w")
        
        self.condition_label = ctk.CTkLabel(
            condition_frame,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=DataTerminalTheme.TEXT
        )
        self.condition_label.grid(row=0, column=1, sticky="w", padx=(8, 0))
        
        # Weather icon (large) - enhanced
        self.weather_icon = ctk.CTkLabel(
            self.main_weather_frame,
            text="🌤️",
            font=ctk.CTkFont(size=72)
        )
        self.weather_icon.grid(row=3, column=1, padx=20, pady=10)
        
        # Quick stats with better organization
        stats_frame = ctk.CTkFrame(self.main_weather_frame, fg_color="transparent")
        stats_frame.grid(row=3, column=2, padx=20, pady=10, sticky="e")
        
        self.feels_like_label = ctk.CTkLabel(
            stats_frame,
            text="Feels like: --°",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=DataTerminalTheme.TEXT
        )
        self.feels_like_label.grid(row=0, column=0, sticky="e")
        
        self.humidity_label = ctk.CTkLabel(
            stats_frame,
            text="Humidity: --%",
            font=ctk.CTkFont(size=14),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.humidity_label.grid(row=1, column=0, sticky="e")
        
        self.wind_label = ctk.CTkLabel(
            stats_frame,
            text="Wind: -- km/h",
            font=ctk.CTkFont(size=14),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.wind_label.grid(row=2, column=0, sticky="e")
        
    def _create_air_quality_card(self):
        """Create air quality display card."""
        self.air_quality_frame = ctk.CTkFrame(
            self.extended_frame,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=8,
            border_color=DataTerminalTheme.BORDER,
            border_width=1
        )
        self.air_quality_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
        
        # Header
        aqi_header = ctk.CTkLabel(
            self.air_quality_frame,
            text="🌬️ Air Quality",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        aqi_header.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="w")
        
        # AQI value and description
        self.aqi_value_label = ctk.CTkLabel(
            self.air_quality_frame,
            text="AQI: --",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=DataTerminalTheme.TEXT
        )
        self.aqi_value_label.grid(row=1, column=0, padx=15, pady=5, sticky="w")
        
        self.aqi_status_label = ctk.CTkLabel(
            self.air_quality_frame,
            text="Loading...",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.aqi_status_label.grid(row=2, column=0, padx=15, pady=(0, 5), sticky="w")
        
        # AQI progress bar
        self.aqi_progress = ctk.CTkProgressBar(
            self.air_quality_frame,
            width=200,
            height=8,
            progress_color=DataTerminalTheme.PRIMARY
        )
        self.aqi_progress.grid(row=3, column=0, columnspan=2, padx=15, pady=(5, 10), sticky="ew")
        self.aqi_progress.set(0)
        
        # Health recommendation
        self.aqi_recommendation = ctk.CTkLabel(
            self.air_quality_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            wraplength=250
        )
        self.aqi_recommendation.grid(row=4, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        
    def _create_astronomical_card(self):
        """Create astronomical data display card."""
        self.astro_frame = ctk.CTkFrame(
            self.extended_frame,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=8,
            border_color=DataTerminalTheme.BORDER,
            border_width=1
        )
        self.astro_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Header
        astro_header = ctk.CTkLabel(
            self.astro_frame,
            text="🌅 Sun & Moon",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        astro_header.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="w")
        
        # Sunrise/Sunset
        self.sunrise_label = ctk.CTkLabel(
            self.astro_frame,
            text="🌅 Sunrise: --:--",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT
        )
        self.sunrise_label.grid(row=1, column=0, padx=15, pady=2, sticky="w")
        
        self.sunset_label = ctk.CTkLabel(
            self.astro_frame,
            text="🌇 Sunset: --:--",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT
        )
        self.sunset_label.grid(row=2, column=0, padx=15, pady=2, sticky="w")
        
        self.daylight_label = ctk.CTkLabel(
            self.astro_frame,
            text="☀️ Daylight: --h --m",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.daylight_label.grid(row=3, column=0, padx=15, pady=2, sticky="w")
        
        # Moon phase
        self.moon_phase_label = ctk.CTkLabel(
            self.astro_frame,
            text="🌙 Moon: Loading...",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT
        )
        self.moon_phase_label.grid(row=4, column=0, padx=15, pady=(10, 2), sticky="w")
        
        # Moon phase visual
        self.moon_visual = ctk.CTkLabel(
            self.astro_frame,
            text="🌑",
            font=ctk.CTkFont(size=32)
        )
        self.moon_visual.grid(row=1, column=1, rowspan=4, padx=15, pady=5)
        
    def _create_weather_details_card(self):
        """Create detailed weather information card."""
        self.details_frame = ctk.CTkFrame(
            self.extended_frame,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=8,
            border_color=DataTerminalTheme.BORDER,
            border_width=1
        )
        self.details_frame.grid(row=0, column=2, padx=(5, 0), pady=5, sticky="ew")
        
        # Header
        details_header = ctk.CTkLabel(
            self.details_frame,
            text="📊 Details",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        details_header.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="w")
        
        # Weather details
        self.pressure_label = ctk.CTkLabel(
            self.details_frame,
            text="🌡️ Pressure: -- hPa",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT
        )
        self.pressure_label.grid(row=1, column=0, padx=15, pady=2, sticky="w")
        
        self.visibility_label = ctk.CTkLabel(
            self.details_frame,
            text="👁️ Visibility: -- km",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT
        )
        self.visibility_label.grid(row=2, column=0, padx=15, pady=2, sticky="w")
        
        self.uv_index_label = ctk.CTkLabel(
            self.details_frame,
            text="☀️ UV Index: --",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT
        )
        self.uv_index_label.grid(row=3, column=0, padx=15, pady=2, sticky="w")
        
        self.dew_point_label = ctk.CTkLabel(
            self.details_frame,
            text="💧 Dew Point: --°",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT
        )
        self.dew_point_label.grid(row=4, column=0, padx=15, pady=2, sticky="w")
        
        self.wind_direction_label = ctk.CTkLabel(
            self.details_frame,
            text="🧭 Wind Dir: --",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.wind_direction_label.grid(row=5, column=0, padx=15, pady=(2, 15), sticky="w")
        
    def _create_alerts_section(self):
        """Create weather alerts section."""
        self.alerts_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=8,
            border_color="#FF6B6B",
            border_width=1
        )
        # Initially hidden
        
        # Alerts header
        alerts_header = ctk.CTkLabel(
            self.alerts_frame,
            text="⚠️ Weather Alerts",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FF6B6B"
        )
        alerts_header.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        # Alerts content (scrollable)
        self.alerts_content = ctk.CTkScrollableFrame(
            self.alerts_frame,
            fg_color="transparent",
            height=100
        )
        self.alerts_content.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        
    def update_weather_data(self, weather_data: Dict[str, Any]):
        """Update the display with new weather data."""
        # Check if weather_data is valid
        if isinstance(weather_data, str):
            print(f"Error: Weather data is a string: {weather_data}")
            return
        
        if not isinstance(weather_data, dict):
            print(f"Error: Weather data is not a dictionary: {type(weather_data)}")
            return
            
        self.current_weather = weather_data
        
        try:
            # Update location and time
            location = weather_data.get('location', {}).get('name', 'Unknown Location')
            country = weather_data.get('location', {}).get('country', '')
            if country:
                location += f", {country}"
            
            self.location_label.configure(text=location)
            
            # Update time
            current_time = datetime.now().strftime("%A, %B %d, %Y • %I:%M %p")
            self.time_label.configure(text=current_time)
            
            # Update current conditions
            current = weather_data.get('current', {})
            
            # Temperature
            temp = current.get('temp_c', 0)
            self.temp_label.configure(text=f"{temp:.1f}°")
            
            # Condition with icon
            condition = current.get('condition', {}).get('text', 'Unknown')
            icon = self._get_weather_icon(condition)
            self.condition_label.configure(text=condition)
            self.weather_icon.configure(text=icon)
            
            # Quick stats
            feels_like = current.get('feelslike_c', temp)
            self.feels_like_label.configure(text=f"Feels like: {feels_like:.1f}°")
            
            humidity = current.get('humidity', 0)
            self.humidity_label.configure(text=f"Humidity: {humidity}%")
            
            wind_kph = current.get('wind_kph', 0)
            wind_dir = current.get('wind_dir', '')
            self.wind_label.configure(text=f"Wind: {wind_kph:.1f} km/h {wind_dir}")
            
            # Update detailed weather
            self._update_weather_details(current)
            
            # Update astronomical data if available
            if 'astronomy' in weather_data:
                self._update_astronomical_data(weather_data['astronomy'])
            
            # Update air quality if available
            if 'air_quality' in weather_data:
                self._update_air_quality(weather_data['air_quality'])
            
            # Update alerts if available
            if 'alerts' in weather_data:
                self._update_alerts(weather_data['alerts'])
            
            # Update status indicator
            self.status_indicator.configure(text="✅ Weather data loaded")
            
            # Update last updated time
            update_time = datetime.now().strftime("%H:%M:%S")
            self.last_updated.configure(text=f"Last updated: {update_time}")
            
            # Update parent status if available
            if hasattr(self, 'parent') and hasattr(self.parent, 'update_status'):
                self.parent.update_status(f"Weather display updated for {location}", "success")
                
        except Exception as e:
            print(f"Error updating weather display: {e}")
            # Update parent status with error if available
            if hasattr(self, 'parent') and hasattr(self.parent, 'update_status'):
                self.parent.update_status("Error updating weather display", "error")
    
    def _update_weather_details(self, current: Dict[str, Any]):
        """Update detailed weather information."""
        # Pressure
        pressure = current.get('pressure_mb', 0)
        self.pressure_label.configure(text=f"🌡️ Pressure: {pressure:.0f} hPa")
        
        # Visibility
        visibility = current.get('vis_km', 0)
        self.visibility_label.configure(text=f"👁️ Visibility: {visibility:.1f} km")
        
        # UV Index
        uv = current.get('uv', 0)
        uv_color = self._get_uv_color(uv)
        self.uv_index_label.configure(
            text=f"☀️ UV Index: {uv:.0f} ({self._get_uv_description(uv)})",
            text_color=uv_color
        )
        
        # Dew point (calculated)
        temp = current.get('temp_c', 0)
        humidity = current.get('humidity', 0)
        dew_point = self._calculate_dew_point(temp, humidity)
        self.dew_point_label.configure(text=f"💧 Dew Point: {dew_point:.1f}°")
        
        # Wind direction
        wind_dir = current.get('wind_dir', '')
        wind_degree = current.get('wind_degree', 0)
        self.wind_direction_label.configure(text=f"🧭 Wind Dir: {wind_dir} ({wind_degree}°)")
    
    def _update_astronomical_data(self, astro_data: Dict[str, Any]):
        """Update astronomical information."""
        try:
            # Sunrise/Sunset
            sunrise = astro_data.get('sunrise', '--:--')
            sunset = astro_data.get('sunset', '--:--')
            
            self.sunrise_label.configure(text=f"🌅 Sunrise: {sunrise}")
            self.sunset_label.configure(text=f"🌇 Sunset: {sunset}")
            
            # Calculate daylight duration
            if sunrise != '--:--' and sunset != '--:--':
                try:
                    sunrise_time = datetime.strptime(sunrise, "%I:%M %p")
                    sunset_time = datetime.strptime(sunset, "%I:%M %p")
                    
                    # Handle sunset next day
                    if sunset_time < sunrise_time:
                        sunset_time += timedelta(days=1)
                    
                    daylight_duration = sunset_time - sunrise_time
                    hours = daylight_duration.seconds // 3600
                    minutes = (daylight_duration.seconds % 3600) // 60
                    
                    self.daylight_label.configure(text=f"☀️ Daylight: {hours}h {minutes}m")
                except:
                    self.daylight_label.configure(text="☀️ Daylight: --h --m")
            
            # Moon phase
            moon_phase = astro_data.get('moon_phase', 'Unknown')
            moon_illumination = astro_data.get('moon_illumination', 0)
            
            self.moon_phase_label.configure(text=f"🌙 {moon_phase} ({moon_illumination}%)")
            
            # Moon visual
            moon_emoji = self._get_moon_emoji(moon_phase)
            self.moon_visual.configure(text=moon_emoji)
            
        except Exception as e:
            print(f"Error updating astronomical data: {e}")
    
    def _update_air_quality(self, aqi_data: Dict[str, Any]):
        """Update air quality information."""
        try:
            # AQI value
            aqi = aqi_data.get('us-epa-index', 1)  # Default to 1 (Good)
            
            self.aqi_value_label.configure(text=f"AQI: {aqi}")
            
            # AQI status and color
            status, color = self._get_aqi_status(aqi)
            self.aqi_status_label.configure(text=status, text_color=color)
            
            # Progress bar (scale 1-5 to 0-1)
            progress = min(aqi / 5.0, 1.0)
            self.aqi_progress.set(progress)
            self.aqi_progress.configure(progress_color=color)
            
            # Health recommendation
            recommendation = self._get_aqi_recommendation(aqi)
            self.aqi_recommendation.configure(text=recommendation)
            
        except Exception as e:
            print(f"Error updating air quality: {e}")
    
    def _update_alerts(self, alerts_data: List[Dict[str, Any]]):
        """Update weather alerts."""
        self.alerts = alerts_data
        
        if alerts_data:
            # Show alerts frame
            self.alerts_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
            
            # Clear existing alerts
            for widget in self.alerts_content.winfo_children():
                widget.destroy()
            
            # Add alert items
            for i, alert in enumerate(alerts_data):
                self._create_alert_item(alert, i)
        else:
            # Hide alerts frame
            self.alerts_frame.grid_remove()
    
    def _create_alert_item(self, alert: Dict[str, Any], index: int):
        """Create an alert item."""
        alert_frame = ctk.CTkFrame(
            self.alerts_content,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=6
        )
        alert_frame.grid(row=index, column=0, padx=5, pady=2, sticky="ew")
        
        # Alert title
        title = alert.get('headline', 'Weather Alert')
        title_label = ctk.CTkLabel(
            alert_frame,
            text=f"⚠️ {title}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FF6B6B"
        )
        title_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Alert description
        desc = alert.get('desc', 'No description available')
        if len(desc) > 100:
            desc = desc[:100] + "..."
        
        desc_label = ctk.CTkLabel(
            alert_frame,
            text=desc,
            font=ctk.CTkFont(size=10),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            wraplength=400
        )
        desc_label.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
    
    def _get_weather_icon(self, condition: str) -> str:
        """Get weather icon emoji for condition."""
        condition_lower = condition.lower()
        
        if 'clear' in condition_lower or 'sunny' in condition_lower:
            return '☀️'
        elif 'partly cloudy' in condition_lower or 'partly sunny' in condition_lower:
            return '⛅'
        elif 'cloudy' in condition_lower or 'overcast' in condition_lower:
            return '☁️'
        elif 'rain' in condition_lower or 'drizzle' in condition_lower:
            return '🌧️'
        elif 'snow' in condition_lower:
            return '❄️'
        elif 'thunder' in condition_lower or 'storm' in condition_lower:
            return '⛈️'
        elif 'fog' in condition_lower or 'mist' in condition_lower:
            return '🌫️'
        else:
            return '🌤️'
    
    def _get_moon_emoji(self, phase: str) -> str:
        """Get moon emoji for phase."""
        phase_lower = phase.lower()
        
        if 'new' in phase_lower:
            return '🌑'
        elif 'waxing crescent' in phase_lower:
            return '🌒'
        elif 'first quarter' in phase_lower:
            return '🌓'
        elif 'waxing gibbous' in phase_lower:
            return '🌔'
        elif 'full' in phase_lower:
            return '🌕'
        elif 'waning gibbous' in phase_lower:
            return '🌖'
        elif 'last quarter' in phase_lower:
            return '🌗'
        elif 'waning crescent' in phase_lower:
            return '🌘'
        else:
            return '🌙'
    
    def _get_aqi_status(self, aqi: int) -> tuple[str, str]:
        """Get AQI status and color."""
        if aqi == 1:
            return "Good", "#00FF00"
        elif aqi == 2:
            return "Fair", "#FFFF00"
        elif aqi == 3:
            return "Moderate", "#FFA500"
        elif aqi == 4:
            return "Poor", "#FF6B6B"
        elif aqi == 5:
            return "Very Poor", "#8B0000"
        else:
            return "Unknown", DataTerminalTheme.TEXT_SECONDARY
    
    def _get_aqi_recommendation(self, aqi: int) -> str:
        """Get health recommendation for AQI."""
        recommendations = {
            1: "Air quality is satisfactory for most people.",
            2: "Unusually sensitive people should consider reducing outdoor activities.",
            3: "Sensitive groups should reduce outdoor activities.",
            4: "Everyone should reduce outdoor activities.",
            5: "Everyone should avoid outdoor activities."
        }
        return recommendations.get(aqi, "No recommendation available.")
    
    def _get_uv_color(self, uv: float) -> str:
        """Get color for UV index."""
        if uv <= 2:
            return "#00FF00"  # Green - Low
        elif uv <= 5:
            return "#FFFF00"  # Yellow - Moderate
        elif uv <= 7:
            return "#FFA500"  # Orange - High
        elif uv <= 10:
            return "#FF6B6B"  # Red - Very High
        else:
            return "#8B0000"  # Dark Red - Extreme
    
    def _get_uv_description(self, uv: float) -> str:
        """Get UV index description."""
        if uv <= 2:
            return "Low"
        elif uv <= 5:
            return "Moderate"
        elif uv <= 7:
            return "High"
        elif uv <= 10:
            return "Very High"
        else:
            return "Extreme"
    
    def _calculate_dew_point(self, temp: float, humidity: float) -> float:
        """Calculate dew point using Magnus formula."""
        try:
            a = 17.27
            b = 237.7
            alpha = ((a * temp) / (b + temp)) + math.log(humidity / 100.0)
            dew_point = (b * alpha) / (a - alpha)
            return dew_point
        except:
            return temp  # Fallback to temperature
    
    def show_loading_state(self):
        """Show loading state for weather data."""
        self.location_label.configure(text="Loading weather data...")
        self.temp_label.configure(text="--°")
        self.condition_label.configure(text="")
        self.weather_icon.configure(text="⏳")
        
        # Update status indicator
        self.status_indicator.configure(text="🔄 Loading weather data...")
        
        # Update parent status if available
        if hasattr(self, 'parent') and hasattr(self.parent, 'update_status'):
            self.parent.update_status("Loading weather data...", "info")
    
    def show_error_state(self, error_message: str):
        """Show error state."""
        self.location_label.configure(text="Error loading weather data")
        self.temp_label.configure(text="❌")
        self.condition_label.configure(text=error_message)
        self.weather_icon.configure(text="❌")
        
        # Update status indicator
        self.status_indicator.configure(text="❌ Error loading weather data")
        
        # Update parent status if available
        if hasattr(self, 'parent') and hasattr(self.parent, 'update_status'):
            self.parent.update_status(f"Weather error: {error_message}", "error")
    
    def update_location(self, location_data: dict):
        """Update the display with new location information."""
        try:
            # Update location label
            display_name = location_data.get('display', location_data.get('name', 'Unknown Location'))
            self.location_label.configure(text=f"📍 {display_name}")
            
            # Clear current weather data to force refresh
            self.current_weather = None
            
            # Show loading state while new data is fetched
            self.show_loading_state()
            
            # Store location data for future reference
            self.current_location = location_data
            
            # Update parent status if available
            if hasattr(self, 'parent') and hasattr(self.parent, 'update_status'):
                self.parent.update_status(f"Location updated to {display_name}", "info")
            
        except Exception as e:
            print(f"Error updating location in enhanced weather display: {e}")
            self.show_error_state("Failed to update location")
    
    def refresh_display(self):
        """Refresh the weather display with current data."""
        try:
            if hasattr(self, 'current_weather') and self.current_weather:
                self.update_weather_data(self.current_weather)
            else:
                self.show_loading_state()
        except Exception as e:
            print(f"Error refreshing weather display: {e}")
            self.show_error_state("Failed to refresh display")