"""Advanced Weather Data Generator for Analytics Charts.

This module provides comprehensive weather data generation capabilities
for testing and demonstration of the analytics features.
"""

import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np


class WeatherDataGenerator:
    """Generate realistic weather data for analytics and testing."""

    def __init__(self):
        """Initialize the weather data generator."""
        self.base_temperature = 20  # Base temperature in Celsius
        self.seasonal_amplitude = 15  # Seasonal variation amplitude
        self.daily_amplitude = 8  # Daily variation amplitude
        self.noise_level = 2  # Random noise level

        # Weather patterns
        self.weather_patterns = {
            "sunny": {"temp_mod": 2, "humidity_mod": -10, "pressure_mod": 5},
            "cloudy": {"temp_mod": -1, "humidity_mod": 5, "pressure_mod": -2},
            "rainy": {"temp_mod": -3, "humidity_mod": 20, "pressure_mod": -8},
            "stormy": {"temp_mod": -5, "humidity_mod": 25, "pressure_mod": -15},
        }

    def generate_comprehensive_data(
        self, timeframe: str, location: str = "Default"
    ) -> Dict[str, Any]:
        """Generate comprehensive weather data for the specified timeframe."""
        # Determine time parameters
        time_params = self._get_time_parameters(timeframe)

        # Generate time series
        times = self._generate_time_series(time_params)

        # Generate weather metrics
        weather_data = self._generate_weather_metrics(times, location)

        # Add metadata
        weather_data.update(
            {
                "timeframe": timeframe,
                "location": location,
                "generated_at": datetime.now(),
                "data_points": len(times),
            }
        )

        return weather_data

    def _get_time_parameters(self, timeframe: str) -> Dict[str, int]:
        """Get time parameters for the specified timeframe."""
        timeframe_configs = {
            "24h": {"hours": 24, "interval": 1},
            "48h": {"hours": 48, "interval": 2},
            "7d": {"hours": 7 * 24, "interval": 6},
            "14d": {"hours": 14 * 24, "interval": 12},
            "30d": {"hours": 30 * 24, "interval": 24},
            "1y": {"hours": 365 * 24, "interval": 24 * 7},  # Weekly points
            "5d": {"hours": 120, "interval": 3},  # Default
        }

        return timeframe_configs.get(timeframe, timeframe_configs["5d"])

    def _generate_time_series(self, time_params: Dict[str, int]) -> List[datetime]:
        """Generate time series based on parameters."""
        now = datetime.now()
        hours = time_params["hours"]
        interval = time_params["interval"]

        return [now + timedelta(hours=i * interval) for i in range(hours // interval)]

    def _generate_weather_metrics(self, times: List[datetime], location: str) -> Dict[str, Any]:
        """Generate comprehensive weather metrics."""
        data = {
            "times": times,
            "temperature": [],
            "feels_like": [],
            "humidity": [],
            "pressure": [],
            "wind_speed": [],
            "wind_direction": [],
            "precipitation": [],
            "visibility": [],
            "uv_index": [],
            "cloud_cover": [],
            "dew_point": [],
            "weather_conditions": [],
            "air_quality_index": [],
        }

        # Location-based modifiers
        location_modifier = self._get_location_modifier(location)

        for i, time in enumerate(times):
            # Generate base weather metrics
            temp = self._generate_temperature(time, location_modifier)
            humidity = self._generate_humidity(temp, time)
            pressure = self._generate_pressure(time)

            # Weather condition for this time point
            condition = self._determine_weather_condition(temp, humidity, pressure)
            condition_mod = self.weather_patterns[condition]

            # Apply weather condition modifiers
            temp += condition_mod["temp_mod"]
            humidity += condition_mod["humidity_mod"]
            pressure += condition_mod["pressure_mod"]

            # Ensure realistic bounds
            humidity = max(0, min(100, humidity))
            pressure = max(950, min(1050, pressure))

            # Generate derived metrics
            feels_like = self._calculate_feels_like(temp, humidity)
            wind_speed = self._generate_wind_speed(condition)
            wind_direction = self._generate_wind_direction()
            precipitation = self._generate_precipitation(condition, humidity)
            visibility = self._generate_visibility(condition, precipitation)
            uv_index = self._generate_uv_index(time, condition)
            cloud_cover = self._generate_cloud_cover(condition)
            dew_point = self._calculate_dew_point(temp, humidity)
            aqi = self._generate_air_quality_index()

            # Store all metrics
            data["temperature"].append(round(temp, 1))
            data["feels_like"].append(round(feels_like, 1))
            data["humidity"].append(round(humidity, 1))
            data["pressure"].append(round(pressure, 1))
            data["wind_speed"].append(round(wind_speed, 1))
            data["wind_direction"].append(wind_direction)
            data["precipitation"].append(round(precipitation, 2))
            data["visibility"].append(round(visibility, 1))
            data["uv_index"].append(round(uv_index, 1))
            data["cloud_cover"].append(round(cloud_cover, 1))
            data["dew_point"].append(round(dew_point, 1))
            data["weather_conditions"].append(condition)
            data["air_quality_index"].append(aqi)

        return data

    def _get_location_modifier(self, location: str) -> Dict[str, float]:
        """Get location-based weather modifiers."""
        location_modifiers = {
            "Default": {"temp": 0, "humidity": 0, "pressure": 0},
            "Arctic": {"temp": -20, "humidity": -20, "pressure": 5},
            "Tropical": {"temp": 10, "humidity": 30, "pressure": -5},
            "Desert": {"temp": 15, "humidity": -40, "pressure": 0},
            "Coastal": {"temp": 5, "humidity": 15, "pressure": 2},
            "Mountain": {"temp": -10, "humidity": -10, "pressure": -20},
        }

        return location_modifiers.get(location, location_modifiers["Default"])

    def _generate_temperature(self, time: datetime, location_mod: Dict[str, float]) -> float:
        """Generate realistic temperature data."""
        # Seasonal component
        day_of_year = time.timetuple().tm_yday
        seasonal = self.seasonal_amplitude * math.sin(2 * math.pi * (day_of_year - 80) / 365)

        # Daily component
        hour_of_day = time.hour
        daily = self.daily_amplitude * math.sin(2 * math.pi * (hour_of_day - 6) / 24)

        # Random variation
        noise = np.random.normal(0, self.noise_level)

        # Combine components
        temperature = self.base_temperature + seasonal + daily + noise + location_mod["temp"]

        return temperature

    def _generate_humidity(self, temperature: float, time: datetime) -> float:
        """Generate humidity based on temperature and time."""
        # Base humidity inversely related to temperature
        base_humidity = 70 - (temperature - 20) * 1.5

        # Time-based variation (higher at night)
        hour_variation = 10 * math.sin(2 * math.pi * (time.hour + 6) / 24)

        # Random variation
        noise = np.random.normal(0, 8)

        return base_humidity + hour_variation + noise

    def _generate_pressure(self, time: datetime) -> float:
        """Generate atmospheric pressure."""
        # Base pressure with slight daily variation
        base_pressure = 1013.25
        daily_variation = 5 * math.sin(2 * math.pi * time.hour / 24)
        noise = np.random.normal(0, 8)

        return base_pressure + daily_variation + noise

    def _determine_weather_condition(self, temp: float, humidity: float, pressure: float) -> str:
        """Determine weather condition based on metrics."""
        if pressure < 1000 and humidity > 80:
            return "stormy"
        elif humidity > 85 and temp < 25:
            return "rainy"
        elif humidity > 70:
            return "cloudy"
        else:
            return "sunny"

    def _calculate_feels_like(self, temp: float, humidity: float) -> float:
        """Calculate feels-like temperature."""
        # Simplified heat index calculation
        if temp > 26.7:  # Above 80°F
            hi = temp + 0.5 * (humidity - 50) / 10
        else:
            hi = temp + np.random.normal(0, 1)

        return hi

    def _generate_wind_speed(self, condition: str) -> float:
        """Generate wind speed based on weather condition."""
        base_speeds = {"sunny": 5, "cloudy": 8, "rainy": 15, "stormy": 25}

        base = base_speeds[condition]
        return max(0, base + np.random.normal(0, base * 0.3))

    def _generate_wind_direction(self) -> int:
        """Generate wind direction in degrees."""
        return random.randint(0, 359)

    def _generate_precipitation(self, condition: str, humidity: float) -> float:
        """Generate precipitation amount."""
        if condition in ["rainy", "stormy"]:
            base_precip = 2 if condition == "rainy" else 8
            return max(0, base_precip * (humidity / 100) + np.random.exponential(1))
        elif condition == "cloudy" and humidity > 85:
            return max(0, np.random.exponential(0.5))
        else:
            return 0

    def _generate_visibility(self, condition: str, precipitation: float) -> float:
        """Generate visibility in kilometers."""
        base_visibility = {"sunny": 25, "cloudy": 15, "rainy": 8, "stormy": 3}

        visibility = base_visibility[condition]

        # Reduce visibility with precipitation
        if precipitation > 0:
            visibility *= max(0.2, 1 - precipitation / 10)

        return max(0.1, visibility + np.random.normal(0, 2))

    def _generate_uv_index(self, time: datetime, condition: str) -> float:
        """Generate UV index based on time and conditions."""
        # Base UV depends on hour (peak at noon)
        hour = time.hour
        if 6 <= hour <= 18:
            base_uv = 8 * math.sin(math.pi * (hour - 6) / 12)
        else:
            base_uv = 0

        # Reduce UV for cloudy/rainy conditions
        condition_multiplier = {"sunny": 1.0, "cloudy": 0.6, "rainy": 0.3, "stormy": 0.1}

        return max(0, base_uv * condition_multiplier[condition])

    def _generate_cloud_cover(self, condition: str) -> float:
        """Generate cloud cover percentage."""
        base_cover = {"sunny": 10, "cloudy": 70, "rainy": 90, "stormy": 95}

        cover = base_cover[condition] + np.random.normal(0, 10)
        return max(0, min(100, cover))

    def _calculate_dew_point(self, temp: float, humidity: float) -> float:
        """Calculate dew point temperature."""
        # Simplified Magnus formula
        a = 17.27
        b = 237.7

        alpha = ((a * temp) / (b + temp)) + math.log(humidity / 100)
        dew_point = (b * alpha) / (a - alpha)

        return dew_point

    def _generate_air_quality_index(self) -> int:
        """Generate air quality index (0-500 scale)."""
        # Most days have good to moderate air quality
        if random.random() < 0.7:
            return random.randint(0, 100)  # Good to moderate
        elif random.random() < 0.9:
            return random.randint(101, 150)  # Unhealthy for sensitive
        else:
            return random.randint(151, 300)  # Unhealthy to very unhealthy

    def generate_historical_comparison_data(
        self, timeframe: str, years_back: int = 5
    ) -> Dict[str, Any]:
        """Generate historical data for comparison analysis."""
        historical_data = {}

        for year in range(years_back):
            year_label = f"{datetime.now().year - year - 1}"

            # Adjust base temperature for historical variation
            original_base = self.base_temperature
            self.base_temperature += np.random.normal(0, 1)  # Year-to-year variation

            historical_data[year_label] = self.generate_comprehensive_data(timeframe, "Historical")

            # Restore original base
            self.base_temperature = original_base

        return historical_data

    def generate_multi_city_data(self, timeframe: str, cities: List[str]) -> Dict[str, Any]:
        """Generate data for multiple cities for comparison."""
        multi_city_data = {}

        for city in cities:
            multi_city_data[city] = self.generate_comprehensive_data(timeframe, city)

        return multi_city_data

    def generate_extreme_weather_events(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify and generate extreme weather events from data."""
        events = []
        temperatures = data["temperature"]
        precipitation = data["precipitation"]
        wind_speeds = data["wind_speed"]
        times = data["times"]

        # Temperature extremes
        temp_mean = np.mean(temperatures)
        temp_std = np.std(temperatures)

        for i, (temp, time) in enumerate(zip(temperatures, times)):
            if abs(temp - temp_mean) > 2 * temp_std:
                event_type = "Heat Wave" if temp > temp_mean else "Cold Snap"
                events.append(
                    {
                        "type": event_type,
                        "time": time,
                        "value": temp,
                        "severity": abs(temp - temp_mean) / temp_std,
                        "index": i,
                    }
                )

        # Precipitation extremes
        for i, (precip, time) in enumerate(zip(precipitation, times)):
            if precip > 10:  # Heavy rain threshold
                events.append(
                    {
                        "type": "Heavy Rain",
                        "time": time,
                        "value": precip,
                        "severity": precip / 10,
                        "index": i,
                    }
                )

        # Wind extremes
        for i, (wind, time) in enumerate(zip(wind_speeds, times)):
            if wind > 30:  # Strong wind threshold
                events.append(
                    {
                        "type": "Strong Winds",
                        "time": time,
                        "value": wind,
                        "severity": wind / 30,
                        "index": i,
                    }
                )

        return sorted(events, key=lambda x: x["severity"], reverse=True)

    def calculate_weather_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive weather statistics."""
        stats = {}

        # Temperature statistics
        temps = data["temperature"]
        stats["temperature"] = {
            "mean": np.mean(temps),
            "median": np.median(temps),
            "std": np.std(temps),
            "min": np.min(temps),
            "max": np.max(temps),
            "range": np.max(temps) - np.min(temps),
            "trend": self._calculate_trend(temps),
        }

        # Humidity statistics
        humidity = data["humidity"]
        stats["humidity"] = {
            "mean": np.mean(humidity),
            "median": np.median(humidity),
            "std": np.std(humidity),
            "min": np.min(humidity),
            "max": np.max(humidity),
        }

        # Pressure statistics
        pressure = data["pressure"]
        stats["pressure"] = {
            "mean": np.mean(pressure),
            "median": np.median(pressure),
            "std": np.std(pressure),
            "min": np.min(pressure),
            "max": np.max(pressure),
        }

        # Weather condition distribution
        conditions = data["weather_conditions"]
        condition_counts = {}
        for condition in conditions:
            condition_counts[condition] = condition_counts.get(condition, 0) + 1

        stats["conditions"] = condition_counts

        return stats

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values."""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
