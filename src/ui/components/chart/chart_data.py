"""Chart Data Mixin for Temperature Chart Component.

This module provides the ChartDataMixin class that handles data processing,
generation, and transformation for the temperature chart.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
import random
import math


class ChartDataMixin:
    """Mixin for chart data processing and generation."""
    
    def __init__(self):
        """Initialize data storage."""
        self.temperature_data = []
        self.dates = []
        self.temperatures = []
        self.humidity_data = []
        self.wind_data = []
        self.pressure_data = []
        
    def generate_realistic_data(self, timeframe: str) -> Dict[str, List]:
        """Generate realistic temperature data for different timeframes."""
        if timeframe == '24h':
            return self._generate_24h_data()
        elif timeframe == '7d':
            return self._generate_7d_data()
        elif timeframe == '30d':
            return self._generate_30d_data()
        else:
            return self._generate_24h_data()
            
    def _generate_24h_data(self) -> Dict[str, List]:
        """Generate 24-hour temperature data with realistic patterns."""
        now = datetime.now()
        dates = []
        temperatures = []
        humidity = []
        wind = []
        
        # Base temperature with daily variation
        base_temp = 20 + random.uniform(-5, 10)
        
        for i in range(24):
            # Create hourly timestamps
            timestamp = now - timedelta(hours=23-i)
            dates.append(timestamp)
            
            # Temperature follows daily pattern
            hour_angle = (i / 24) * 2 * math.pi
            daily_variation = 8 * math.sin(hour_angle - math.pi/2)  # Peak at 2 PM
            noise = random.uniform(-2, 2)
            temp = base_temp + daily_variation + noise
            temperatures.append(round(temp, 1))
            
            # Humidity inversely related to temperature
            humid = max(30, min(90, 70 - (temp - base_temp) * 2 + random.uniform(-10, 10)))
            humidity.append(round(humid))
            
            # Wind with some randomness
            wind_speed = max(0, 15 + random.uniform(-8, 12))
            wind.append(round(wind_speed, 1))
            
        return {
            'dates': dates,
            'temperatures': temperatures,
            'humidity': humidity,
            'wind': wind
        }
        
    def _generate_7d_data(self) -> Dict[str, List]:
        """Generate 7-day temperature data with weather patterns."""
        now = datetime.now()
        dates = []
        temperatures = []
        humidity = []
        wind = []
        
        # Base temperature with weekly trend
        base_temp = 18 + random.uniform(-3, 8)
        
        for i in range(7 * 4):  # 4 points per day
            # Create 6-hour intervals
            timestamp = now - timedelta(hours=(7*4-1-i)*6)
            dates.append(timestamp)
            
            # Day of week effect
            day = i // 4
            hour_in_day = (i % 4) * 6
            
            # Daily temperature pattern
            daily_pattern = 6 * math.sin((hour_in_day / 24) * 2 * math.pi - math.pi/2)
            
            # Weekly weather pattern (simulate weather fronts)
            weekly_pattern = 5 * math.sin((day / 7) * 2 * math.pi)
            
            # Random weather events
            weather_noise = random.uniform(-3, 3)
            
            temp = base_temp + daily_pattern + weekly_pattern + weather_noise
            temperatures.append(round(temp, 1))
            
            # Humidity with weather correlation
            humid = max(25, min(95, 60 + weekly_pattern * 3 + random.uniform(-15, 15)))
            humidity.append(round(humid))
            
            # Wind patterns
            wind_speed = max(0, 12 + weekly_pattern + random.uniform(-6, 10))
            wind.append(round(wind_speed, 1))
            
        return {
            'dates': dates,
            'temperatures': temperatures,
            'humidity': humidity,
            'wind': wind
        }
        
    def _generate_30d_data(self) -> Dict[str, List]:
        """Generate 30-day temperature data with seasonal trends."""
        now = datetime.now()
        dates = []
        temperatures = []
        humidity = []
        wind = []
        
        # Base temperature with seasonal variation
        month = now.month
        seasonal_base = self._get_seasonal_temperature(month)
        
        for i in range(30):
            # Daily timestamps
            timestamp = now - timedelta(days=29-i)
            dates.append(timestamp)
            
            # Seasonal trend
            seasonal_variation = 3 * math.sin((i / 30) * 2 * math.pi)
            
            # Weather systems (multi-day patterns)
            weather_system = 8 * math.sin((i / 5) * 2 * math.pi + random.uniform(0, math.pi))
            
            # Daily variation
            daily_noise = random.uniform(-4, 4)
            
            temp = seasonal_base + seasonal_variation + weather_system + daily_noise
            temperatures.append(round(temp, 1))
            
            # Humidity with seasonal patterns
            seasonal_humidity = self._get_seasonal_humidity(month)
            humid = max(20, min(100, seasonal_humidity + weather_system + random.uniform(-20, 20)))
            humidity.append(round(humid))
            
            # Wind with weather system correlation
            wind_speed = max(0, 10 + abs(weather_system) + random.uniform(-5, 8))
            wind.append(round(wind_speed, 1))
            
        return {
            'dates': dates,
            'temperatures': temperatures,
            'humidity': humidity,
            'wind': wind
        }
        
    def _get_seasonal_temperature(self, month: int) -> float:
        """Get base temperature for the season."""
        # Northern hemisphere seasonal pattern
        seasonal_temps = {
            1: 2,   # January
            2: 4,   # February
            3: 8,   # March
            4: 14,  # April
            5: 19,  # May
            6: 24,  # June
            7: 27,  # July
            8: 26,  # August
            9: 22,  # September
            10: 16, # October
            11: 9,  # November
            12: 4   # December
        }
        return seasonal_temps.get(month, 15)
        
    def _get_seasonal_humidity(self, month: int) -> float:
        """Get base humidity for the season."""
        # Seasonal humidity patterns
        seasonal_humidity = {
            1: 65,  # January
            2: 60,  # February
            3: 55,  # March
            4: 50,  # April
            5: 55,  # May
            6: 60,  # June
            7: 65,  # July
            8: 70,  # August
            9: 65,  # September
            10: 60, # October
            11: 70, # November
            12: 70  # December
        }
        return seasonal_humidity.get(month, 60)
        
    def process_forecast_data(self, forecast_data: Dict[str, Any]) -> Dict[str, List]:
        """Process real forecast data into chart format."""
        processed_data = {
            'dates': [],
            'temperatures': [],
            'humidity': [],
            'wind': [],
            'pressure': []
        }
        
        try:
            # Extract data based on forecast structure
            if 'list' in forecast_data:
                # OpenWeatherMap format
                for item in forecast_data['list']:
                    # Parse timestamp
                    timestamp = datetime.fromtimestamp(item['dt'])
                    processed_data['dates'].append(timestamp)
                    
                    # Temperature
                    temp = item['main']['temp'] - 273.15  # Convert from Kelvin
                    processed_data['temperatures'].append(round(temp, 1))
                    
                    # Humidity
                    humidity = item['main']['humidity']
                    processed_data['humidity'].append(humidity)
                    
                    # Wind
                    wind_speed = item.get('wind', {}).get('speed', 0) * 3.6  # m/s to km/h
                    processed_data['wind'].append(round(wind_speed, 1))
                    
                    # Pressure
                    pressure = item['main']['pressure']
                    processed_data['pressure'].append(pressure)
                    
            elif 'daily' in forecast_data:
                # Alternative format
                for item in forecast_data['daily']:
                    timestamp = datetime.fromtimestamp(item['dt'])
                    processed_data['dates'].append(timestamp)
                    
                    temp = item['temp']['day']
                    processed_data['temperatures'].append(round(temp, 1))
                    
                    humidity = item['humidity']
                    processed_data['humidity'].append(humidity)
                    
                    wind_speed = item['wind_speed'] * 3.6
                    processed_data['wind'].append(round(wind_speed, 1))
                    
                    pressure = item['pressure']
                    processed_data['pressure'].append(pressure)
                    
        except (KeyError, TypeError, ValueError) as e:
            print(f"Error processing forecast data: {e}")
            # Return empty data on error
            return {
                'dates': [],
                'temperatures': [],
                'humidity': [],
                'wind': [],
                'pressure': []
            }
            
        return processed_data
        
    def smooth_data(self, data: List[float], window_size: int = 3) -> List[float]:
        """Apply smoothing to temperature data."""
        if len(data) < window_size:
            return data
            
        smoothed = []
        half_window = window_size // 2
        
        for i in range(len(data)):
            start_idx = max(0, i - half_window)
            end_idx = min(len(data), i + half_window + 1)
            
            window_data = data[start_idx:end_idx]
            smoothed_value = sum(window_data) / len(window_data)
            smoothed.append(round(smoothed_value, 1))
            
        return smoothed
        
    def calculate_temperature_trends(self, temperatures: List[float], dates: List[datetime]) -> Dict[str, Any]:
        """Calculate temperature trends and statistics."""
        if not temperatures or len(temperatures) < 2:
            return {}
            
        # Basic statistics
        min_temp = min(temperatures)
        max_temp = max(temperatures)
        avg_temp = sum(temperatures) / len(temperatures)
        
        # Temperature range
        temp_range = max_temp - min_temp
        
        # Trend calculation (simple linear regression)
        n = len(temperatures)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = sum(x_values) / n
        y_mean = avg_temp
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, temperatures))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Trend direction
        if slope > 0.1:
            trend_direction = "increasing"
        elif slope < -0.1:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
            
        return {
            'min_temperature': round(min_temp, 1),
            'max_temperature': round(max_temp, 1),
            'average_temperature': round(avg_temp, 1),
            'temperature_range': round(temp_range, 1),
            'trend_slope': round(slope, 3),
            'trend_direction': trend_direction,
            'data_points': n
        }
        
    def filter_data_by_timeframe(self, data: Dict[str, List], timeframe: str) -> Dict[str, List]:
        """Filter data to match the specified timeframe."""
        if not data or 'dates' not in data:
            return data
            
        now = datetime.now()
        
        if timeframe == '24h':
            cutoff = now - timedelta(hours=24)
        elif timeframe == '7d':
            cutoff = now - timedelta(days=7)
        elif timeframe == '30d':
            cutoff = now - timedelta(days=30)
        else:
            return data
            
        # Filter all data arrays based on date cutoff
        filtered_data = {}
        
        for key, values in data.items():
            if key == 'dates':
                filtered_indices = [i for i, date in enumerate(values) if date >= cutoff]
                filtered_data[key] = [values[i] for i in filtered_indices]
            else:
                # Filter other arrays using the same indices
                if 'dates' in filtered_data:
                    filtered_indices = [i for i, date in enumerate(data['dates']) if date >= cutoff]
                    if len(values) == len(data['dates']):
                        filtered_data[key] = [values[i] for i in filtered_indices]
                    else:
                        filtered_data[key] = values
                else:
                    filtered_data[key] = values
                    
        return filtered_data
        
    def interpolate_missing_data(self, temperatures: List[float], dates: List[datetime]) -> Tuple[List[float], List[datetime]]:
        """Interpolate missing temperature data points."""
        if not temperatures or not dates:
            return temperatures, dates
            
        # Find gaps in data
        interpolated_temps = temperatures.copy()
        interpolated_dates = dates.copy()
        
        # Simple linear interpolation for None values
        for i in range(len(interpolated_temps)):
            if interpolated_temps[i] is None:
                # Find previous and next valid values
                prev_idx = i - 1
                next_idx = i + 1
                
                while prev_idx >= 0 and interpolated_temps[prev_idx] is None:
                    prev_idx -= 1
                    
                while next_idx < len(interpolated_temps) and interpolated_temps[next_idx] is None:
                    next_idx += 1
                    
                # Interpolate if we have valid neighbors
                if prev_idx >= 0 and next_idx < len(interpolated_temps):
                    prev_temp = interpolated_temps[prev_idx]
                    next_temp = interpolated_temps[next_idx]
                    
                    # Linear interpolation
                    ratio = (i - prev_idx) / (next_idx - prev_idx)
                    interpolated_temp = prev_temp + (next_temp - prev_temp) * ratio
                    interpolated_temps[i] = round(interpolated_temp, 1)
                    
        return interpolated_temps, interpolated_dates
        
    def update_data_storage(self, new_data: Dict[str, List]):
        """Update internal data storage with new data."""
        self.dates = new_data.get('dates', [])
        self.temperatures = new_data.get('temperatures', [])
        self.humidity_data = new_data.get('humidity', [])
        self.wind_data = new_data.get('wind', [])
        self.pressure_data = new_data.get('pressure', [])
        
        # Store complete data structure
        self.temperature_data = new_data
        
    def get_current_data(self) -> Dict[str, List]:
        """Get current data storage."""
        return {
            'dates': self.dates,
            'temperatures': self.temperatures,
            'humidity': self.humidity_data,
            'wind': self.wind_data,
            'pressure': self.pressure_data
        }