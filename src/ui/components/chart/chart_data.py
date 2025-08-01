"""Enhanced Chart Data Mixin for Advanced Weather Analytics.

This mixin handles comprehensive data processing, storage, and management
for the weather analytics system, including forecast data processing,
historical data management, and advanced analytics data preparation.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
import random
import math
from utils.safe_math import safe_divide, safe_average
try:
    from .chart_data_generator import WeatherDataGenerator
except ImportError:
    # Fallback if data generator is not available
    WeatherDataGenerator = None


class ChartDataMixin:
    """Enhanced mixin for comprehensive weather data operations."""
    
    def __init__(self):
        """Initialize enhanced data storage and generator."""
        self.temperature_data = []
        self.dates = []
        self.temperatures = []
        self.humidity_data = []
        self.wind_data = []
        self.pressure_data = []
        self.historical_data = {}
        self.multi_city_data = {}
        self.statistics_cache = {}
        self.extreme_events = []
        
        # Initialize data generator if available
        if WeatherDataGenerator:
            self.data_generator = WeatherDataGenerator()
        else:
            self.data_generator = None
        
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
        """Process real forecast data into enhanced chart format."""
        processed_data = {
            'dates': [],
            'temperatures': [],
            'humidity': [],
            'wind': [],
            'pressure': [],
            'feels_like': [],
            'weather_conditions': [],
            'precipitation': [],
            'visibility': [],
            'uv_index': [],
            'cloud_cover': []
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
                    
                    # Feels like temperature
                    feels_like = item['main'].get('feels_like', item['main']['temp']) - 273.15
                    processed_data['feels_like'].append(round(feels_like, 1))
                    
                    # Humidity
                    humidity = item['main']['humidity']
                    processed_data['humidity'].append(humidity)
                    
                    # Wind
                    wind_speed = item.get('wind', {}).get('speed', 0) * 3.6  # m/s to km/h
                    processed_data['wind'].append(round(wind_speed, 1))
                    
                    # Pressure
                    pressure = item['main']['pressure']
                    processed_data['pressure'].append(pressure)
                    
                    # Weather conditions
                    weather = item.get('weather', [{}])[0]
                    processed_data['weather_conditions'].append(weather.get('main', 'Clear'))
                    
                    # Additional metrics with defaults
                    processed_data['precipitation'].append(item.get('rain', {}).get('3h', 0))
                    processed_data['visibility'].append(item.get('visibility', 10000) / 1000)  # Convert to km
                    processed_data['uv_index'].append(item.get('uvi', 3))
                    processed_data['cloud_cover'].append(item.get('clouds', {}).get('all', 30))
                    
            elif 'daily' in forecast_data:
                # Alternative format
                for item in forecast_data['daily']:
                    timestamp = datetime.fromtimestamp(item['dt'])
                    processed_data['dates'].append(timestamp)
                    
                    temp = item['temp']['day']
                    processed_data['temperatures'].append(round(temp, 1))
                    
                    feels_like = item.get('feels_like', {}).get('day', temp)
                    processed_data['feels_like'].append(round(feels_like, 1))
                    
                    humidity = item['humidity']
                    processed_data['humidity'].append(humidity)
                    
                    wind_speed = item['wind_speed'] * 3.6
                    processed_data['wind'].append(round(wind_speed, 1))
                    
                    pressure = item['pressure']
                    processed_data['pressure'].append(pressure)
                    
                    weather = item.get('weather', [{}])[0]
                    processed_data['weather_conditions'].append(weather.get('main', 'Clear'))
                    
                    processed_data['precipitation'].append(item.get('rain', 0))
                    processed_data['visibility'].append(15)  # Default visibility
                    processed_data['uv_index'].append(item.get('uvi', 3))
                    processed_data['cloud_cover'].append(item.get('clouds', 30))
                    
        except (KeyError, TypeError, ValueError) as e:
            print(f"Error processing forecast data: {e}")
            # Return empty data on error
            return {
                'dates': [],
                'temperatures': [],
                'humidity': [],
                'wind': [],
                'pressure': [],
                'feels_like': [],
                'weather_conditions': [],
                'precipitation': [],
                'visibility': [],
                'uv_index': [],
                'cloud_cover': []
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
            if window_data:  # Check if window_data is not empty
                smoothed_value = sum(window_data) / len(window_data)
                smoothed.append(round(smoothed_value, 1))
            else:
                smoothed.append(data[i] if i < len(data) else 0)  # Use original value or 0 as fallback
            
        return smoothed
        
    def calculate_temperature_trends(self, temperatures: List[float], dates: List[datetime]) -> Dict[str, Any]:
        """Calculate temperature trends and statistics."""
        if not temperatures or len(temperatures) < 2:
            return {}
            
        # Basic statistics
        min_temp = min(temperatures)
        max_temp = max(temperatures)
        avg_temp = safe_average(temperatures)
        
        # Temperature range
        temp_range = max_temp - min_temp
        
        # Trend calculation (simple linear regression)
        n = len(temperatures)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = safe_divide(sum(x_values), n)
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
                    
                    # Linear interpolation with division safety
                    try:
                        denominator = next_idx - prev_idx
                        numerator = i - prev_idx
                        logger.debug(f"Interpolation division: {numerator} ({type(numerator)}) / {denominator} ({type(denominator)})")
                        
                        if denominator == 0 or denominator is None or numerator is None:
                            logger.error(f"Invalid interpolation values: numerator={numerator}, denominator={denominator}")
                            # Use previous temperature as fallback
                            interpolated_temps[i] = prev_temp
                        else:
                            ratio = numerator / denominator
                            interpolated_temp = prev_temp + (next_temp - prev_temp) * ratio
                            interpolated_temps[i] = round(interpolated_temp, 1)
                    except Exception as e:
                        logger.exception(f"Error in interpolation division: {e}")
                        interpolated_temps[i] = prev_temp  # Fallback to previous temperature
                    
        return interpolated_temps, interpolated_dates
        
    def update_data_storage(self, new_data: Dict[str, List]):
        """Update comprehensive data storage with new data."""
        self.dates = new_data.get('dates', [])
        self.temperatures = new_data.get('temperatures', [])
        self.humidity_data = new_data.get('humidity', [])
        self.wind_data = new_data.get('wind', [])
        self.pressure_data = new_data.get('pressure', [])
        
        # Store complete data structure
        self.temperature_data = new_data
        
        # Generate and cache statistics
        if self.temperatures:
            self.statistics_cache['current'] = self.calculate_temperature_trends(self.temperatures, self.dates)
        
        # Identify extreme weather events
        self.extreme_events = self._identify_extreme_events(new_data)
        
    def get_current_data(self) -> Dict[str, List]:
        """Get comprehensive current data storage."""
        return {
            'dates': self.dates,
            'temperatures': self.temperatures,
            'humidity': self.humidity_data,
            'wind': self.wind_data,
            'pressure': self.pressure_data,
            'feels_like': self.temperature_data.get('feels_like', []),
            'weather_conditions': self.temperature_data.get('weather_conditions', []),
            'precipitation': self.temperature_data.get('precipitation', []),
            'visibility': self.temperature_data.get('visibility', []),
            'uv_index': self.temperature_data.get('uv_index', []),
            'cloud_cover': self.temperature_data.get('cloud_cover', [])
        }
        
    def get_statistics(self, metric: str = 'temperature') -> Dict[str, Any]:
        """Get statistics for a specific metric."""
        if metric == 'temperature':
            return self.statistics_cache.get('current', {})
        
        # Calculate statistics for other metrics
        data = getattr(self, f'{metric}_data', [])
        if not data:
            return {}
        
        return {
            'min': min(data),
            'max': max(data),
            'average': safe_average(data),
            'range': max(data) - min(data) if data else 0
        }
        
    def get_extreme_events(self) -> List[Dict[str, Any]]:
        """Get identified extreme weather events."""
        return self.extreme_events
        
    def _identify_extreme_events(self, data: Dict[str, List]) -> List[Dict[str, Any]]:
        """Identify extreme weather events in the data."""
        events = []
        
        temperatures = data.get('temperatures', [])
        wind_speeds = data.get('wind', [])
        precipitation = data.get('precipitation', [])
        dates = data.get('dates', [])
        
        for i, (temp, wind, precip, date) in enumerate(zip(temperatures, wind_speeds, precipitation, dates)):
            # Extreme temperature events
            if temp > 35:
                events.append({
                    'type': 'extreme_heat',
                    'value': temp,
                    'date': date,
                    'description': f'Extreme heat: {temp}°C'
                })
            elif temp < -10:
                events.append({
                    'type': 'extreme_cold',
                    'value': temp,
                    'date': date,
                    'description': f'Extreme cold: {temp}°C'
                })
            
            # High wind events
            if wind > 50:
                events.append({
                    'type': 'high_wind',
                    'value': wind,
                    'date': date,
                    'description': f'High wind: {wind} km/h'
                })
            
            # Heavy precipitation events
            if precip > 10:
                events.append({
                    'type': 'heavy_rain',
                    'value': precip,
                    'date': date,
                    'description': f'Heavy precipitation: {precip} mm'
                })
        
        return events
    
    def generate_sample_data(self, timeframe: str) -> Dict[str, Any]:
        """Generate sample data for the specified timeframe."""
        if self.data_generator:
            return self.data_generator.generate_comprehensive_data(timeframe)
        else:
            # Fallback to existing realistic data generation
            return self.generate_realistic_data(timeframe)
    
    def get_extreme_events_for_metric(self, metric: str) -> List[Dict[str, Any]]:
        """Get extreme events filtered by metric type."""
        metric_event_types = {
            'temperature': ['extreme_heat', 'extreme_cold'],
            'wind_speed': ['high_wind'],
            'precipitation': ['heavy_rain'],
            'pressure': ['low_pressure', 'high_pressure']
        }
        
        event_types = metric_event_types.get(metric, [])
        return [event for event in self.extreme_events if event['type'] in event_types]
    
    def calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend information for a series of values."""
        if len(values) < 2:
            return {'direction': 'stable', 'slope': 0, 'correlation': 0}
        
        # Simple linear trend calculation
        x = list(range(len(values)))
        n = len(values)
        
        # Calculate slope using least squares
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        # Determine trend direction
        if abs(slope) < 0.1:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        # Calculate correlation coefficient
        mean_x = sum_x / n
        mean_y = sum_y / n
        
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((values[i] - mean_y) ** 2 for i in range(n))
        
        correlation = numerator / (denominator_x * denominator_y) ** 0.5 if denominator_x * denominator_y > 0 else 0
        
        return {
            'direction': direction,
            'slope': slope,
            'correlation': correlation
        }
    
    def get_metric_unit(self, metric: str) -> str:
        """Get the unit for a specific metric."""
        units = {
            'temperature': '°C',
            'feels_like': '°C',
            'humidity': '%',
            'pressure': 'hPa',
            'wind_speed': 'km/h',
            'precipitation': 'mm',
            'visibility': 'km',
            'uv_index': 'index',
            'cloud_cover': '%',
            'dew_point': '°C'
        }
        return units.get(metric, '')
    
    def get_historical_data(self, timeframe: str, city: str = None) -> Dict[str, Any]:
        """Get historical data for comparison."""
        cache_key = f"historical_{timeframe}_{city or 'default'}"
        
        if cache_key not in self.historical_data:
            if self.data_generator:
                # Generate historical data using data generator
                self.historical_data[cache_key] = self.data_generator.generate_historical_comparison_data(timeframe)
            else:
                # Fallback to modified current data
                current_data = self.generate_realistic_data(timeframe)
                # Modify temperatures slightly for historical comparison
                historical_data = current_data.copy()
                if 'temperatures' in historical_data:
                    historical_data['temperatures'] = [t - 2 + (i % 3) for i, t in enumerate(historical_data['temperatures'])]
                self.historical_data[cache_key] = historical_data
        
        return self.historical_data[cache_key]
    
    def get_multi_city_data(self, cities: List[str], timeframe: str) -> Dict[str, Any]:
        """Get multi-city data for comparison."""
        cache_key = f"multi_city_{'_'.join(cities)}_{timeframe}"
        
        if cache_key not in self.multi_city_data:
            if self.data_generator:
                # Generate multi-city data using data generator
                self.multi_city_data[cache_key] = self.data_generator.generate_multi_city_data(cities, timeframe)
            else:
                # Fallback to generate data for each city
                base_data = self.generate_realistic_data(timeframe)
                multi_city_data = {'cities': {}}
                
                for i, city in enumerate(cities):
                    city_data = base_data.copy()
                    # Vary temperatures by city
                    if 'temperatures' in city_data:
                        offset = (i - len(cities)//2) * 3  # Temperature offset per city
                        city_data['temperatures'] = [t + offset for t in city_data['temperatures']]
                    multi_city_data['cities'][city] = city_data
                
                self.multi_city_data[cache_key] = multi_city_data
        
        return self.multi_city_data[cache_key]
    
    def clear_cache(self, cache_type: str = 'all'):
        """Clear specific or all data caches."""
        if cache_type == 'all' or cache_type == 'historical':
            self.historical_data.clear()
        if cache_type == 'all' or cache_type == 'multi_city':
            self.multi_city_data.clear()
        if cache_type == 'all' or cache_type == 'statistics':
            self.statistics_cache.clear()
        if cache_type == 'all' or cache_type == 'events':
            self.extreme_events.clear()