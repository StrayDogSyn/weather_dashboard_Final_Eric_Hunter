"""Chart controller for temperature graph business logic.

This module handles chart data processing, analytics calculation,
and chart configuration management.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

from .chart_models import (
    ChartConfig, TemperatureDataPoint, ChartAnalytics, 
    TimeRange, ChartType, ExportSettings
)


class ChartController:
    """Controller for managing temperature chart data and analytics."""

    def __init__(self, database_manager, config: Optional[ChartConfig] = None):
        self.database_manager = database_manager
        self.config = config or ChartConfig()
        self.logger = logging.getLogger(__name__)
        
        # Data cache
        self._data_cache: Dict[str, List[TemperatureDataPoint]] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=5)

    def get_temperature_data(self, time_range: TimeRange, location: Optional[str] = None) -> List[TemperatureDataPoint]:
        """Get temperature data for the specified time range."""
        cache_key = f"{time_range.value}_{location or 'default'}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return self._data_cache[cache_key]
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = self._calculate_start_date(time_range, end_date)
            
            # Fetch data from database
            raw_data = self._fetch_raw_data(start_date, end_date, location)
            
            # Convert to data points
            data_points = self._convert_to_data_points(raw_data)
            
            # Cache the data
            self._data_cache[cache_key] = data_points
            self._cache_expiry[cache_key] = datetime.now() + self._cache_duration
            
            return data_points
            
        except Exception as e:
            self.logger.error(f"Error fetching temperature data: {e}")
            return []

    def calculate_analytics(self, data_points: List[TemperatureDataPoint]) -> ChartAnalytics:
        """Calculate analytics for temperature data."""
        if not data_points:
            return ChartAnalytics(
                min_temperature=0, max_temperature=0, avg_temperature=0,
                temperature_trend="stable", data_points_count=0, time_span_hours=0
            )
        
        temperatures = [point.temperature for point in data_points]
        
        min_temp = min(temperatures)
        max_temp = max(temperatures)
        avg_temp = sum(temperatures) / len(temperatures)
        
        # Calculate trend
        trend = self._calculate_trend(data_points)
        
        # Calculate time span
        if len(data_points) > 1:
            time_span = (data_points[-1].timestamp - data_points[0].timestamp).total_seconds() / 3600
        else:
            time_span = 0
        
        return ChartAnalytics(
            min_temperature=min_temp,
            max_temperature=max_temp,
            avg_temperature=avg_temp,
            temperature_trend=trend,
            data_points_count=len(data_points),
            time_span_hours=time_span
        )

    def process_data_for_chart(self, data_points: List[TemperatureDataPoint], chart_type: ChartType) -> Dict[str, Any]:
        """Process data points for specific chart type."""
        if not data_points:
            return {'x': [], 'y': [], 'metadata': {}}
        
        timestamps = [point.timestamp for point in data_points]
        temperatures = [point.temperature for point in data_points]
        
        result = {
            'x': timestamps,
            'y': temperatures,
            'metadata': {
                'feels_like': [point.feels_like for point in data_points],
                'humidity': [point.humidity for point in data_points],
                'pressure': [point.pressure for point in data_points],
                'wind_speed': [point.wind_speed for point in data_points],
                'condition': [point.condition for point in data_points]
            }
        }
        
        # Chart-specific processing
        if chart_type == ChartType.CANDLESTICK:
            result.update(self._process_candlestick_data(data_points))
        elif chart_type == ChartType.BAR:
            result.update(self._process_bar_data(data_points))
        elif chart_type == ChartType.AREA:
            result.update(self._process_area_data(data_points))
        
        return result

    def get_data_summary(self, data_points: List[TemperatureDataPoint]) -> Dict[str, Any]:
        """Get summary statistics for data points."""
        if not data_points:
            return {}
        
        temperatures = [point.temperature for point in data_points]
        
        return {
            'count': len(data_points),
            'min': min(temperatures),
            'max': max(temperatures),
            'mean': np.mean(temperatures),
            'median': np.median(temperatures),
            'std': np.std(temperatures),
            'range': max(temperatures) - min(temperatures),
            'first_timestamp': data_points[0].timestamp,
            'last_timestamp': data_points[-1].timestamp
        }

    def filter_data_by_criteria(self, data_points: List[TemperatureDataPoint], criteria: Dict[str, Any]) -> List[TemperatureDataPoint]:
        """Filter data points by various criteria."""
        filtered = data_points.copy()
        
        # Temperature range filter
        if 'min_temp' in criteria:
            filtered = [p for p in filtered if p.temperature >= criteria['min_temp']]
        if 'max_temp' in criteria:
            filtered = [p for p in filtered if p.temperature <= criteria['max_temp']]
            
        # Time range filter
        if 'start_time' in criteria:
            filtered = [p for p in filtered if p.timestamp >= criteria['start_time']]
        if 'end_time' in criteria:
            filtered = [p for p in filtered if p.timestamp <= criteria['end_time']]
            
        # Condition filter
        if 'conditions' in criteria:
            conditions = criteria['conditions']
            filtered = [p for p in filtered if p.condition in conditions]
            
        return filtered

    def interpolate_missing_data(self, data_points: List[TemperatureDataPoint]) -> List[TemperatureDataPoint]:
        """Interpolate missing data points for smoother visualization."""
        if len(data_points) < 2:
            return data_points
        
        # Convert to pandas for easier interpolation
        df = pd.DataFrame([
            {
                'timestamp': point.timestamp,
                'temperature': point.temperature,
                'feels_like': point.feels_like,
                'humidity': point.humidity,
                'pressure': point.pressure
            }
            for point in data_points
        ])
        
        # Set timestamp as index and resample
        df.set_index('timestamp', inplace=True)
        df_resampled = df.resample('1H').mean()  # Hourly interpolation
        df_interpolated = df_resampled.interpolate(method='linear')
        
        # Convert back to data points
        interpolated_points = []
        for timestamp, row in df_interpolated.iterrows():
            point = TemperatureDataPoint(
                timestamp=timestamp,
                temperature=row['temperature'],
                feels_like=row['feels_like'],
                humidity=row['humidity'],
                pressure=row['pressure']
            )
            interpolated_points.append(point)
        
        return interpolated_points

    def export_data(self, data_points: List[TemperatureDataPoint], format: str = "csv") -> str:
        """Export data points to specified format."""
        if format.lower() == "csv":
            return self._export_to_csv(data_points)
        elif format.lower() == "json":
            return self._export_to_json(data_points)
        elif format.lower() == "excel":
            return self._export_to_excel(data_points)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        return (cache_key in self._data_cache and 
                cache_key in self._cache_expiry and
                datetime.now() < self._cache_expiry[cache_key])

    def _calculate_start_date(self, time_range: TimeRange, end_date: datetime) -> datetime:
        """Calculate start date based on time range."""
        if time_range == TimeRange.LAST_24_HOURS:
            return end_date - timedelta(hours=24)
        elif time_range == TimeRange.LAST_7_DAYS:
            return end_date - timedelta(days=7)
        elif time_range == TimeRange.LAST_30_DAYS:
            return end_date - timedelta(days=30)
        elif time_range == TimeRange.LAST_90_DAYS:
            return end_date - timedelta(days=90)
        else:
            return end_date - timedelta(days=7)  # Default

    def _fetch_raw_data(self, start_date: datetime, end_date: datetime, location: Optional[str]) -> List[Any]:
        """Fetch raw data from database."""
        try:
            # Calculate days between start and end date
            days_diff = (end_date - start_date).days
            days = max(1, days_diff)  # Ensure at least 1 day
            
            # Use database manager to fetch weather records
            location_name = location or "New York"  # Default city if location is None
            records = self.database_manager.get_weather_history(
                location=location_name,
                days=days
            )
            return records
        except Exception as e:
            self.logger.error(f"Error fetching raw data: {e}")
            return []

    def _convert_to_data_points(self, raw_data: List[Any]) -> List[TemperatureDataPoint]:
        """Convert raw database records to temperature data points."""
        data_points = []
        
        for record in raw_data:
            try:
                point = TemperatureDataPoint(
                    timestamp=record.timestamp if hasattr(record, 'timestamp') else datetime.now(),
                    temperature=record.temperature if hasattr(record, 'temperature') else 0,
                    feels_like=getattr(record, 'feels_like', None),
                    humidity=getattr(record, 'humidity', None),
                    pressure=getattr(record, 'pressure', None),
                    wind_speed=getattr(record, 'wind_speed', None),
                    condition=getattr(record, 'condition', None),
                    location=getattr(record, 'location', None)
                )
                data_points.append(point)
            except Exception as e:
                self.logger.warning(f"Error converting record to data point: {e}")
                continue
        
        return sorted(data_points, key=lambda x: x.timestamp)

    def _calculate_trend(self, data_points: List[TemperatureDataPoint]) -> str:
        """Calculate temperature trend from data points."""
        if len(data_points) < 2:
            return "stable"
        
        temperatures = [point.temperature for point in data_points]
        
        # Calculate linear regression slope
        x = np.arange(len(temperatures))
        y = np.array(temperatures)
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        # Determine trend based on slope
        if slope > 0.5:
            return "rising"
        elif slope < -0.5:
            return "falling"
        else:
            return "stable"

    def _process_candlestick_data(self, data_points: List[TemperatureDataPoint]) -> Dict[str, Any]:
        """Process data for candlestick chart."""
        # Group by day and calculate OHLC values
        daily_data = {}
        
        for point in data_points:
            date_key = point.timestamp.date()
            if date_key not in daily_data:
                daily_data[date_key] = []
            daily_data[date_key].append(point.temperature)
        
        dates, opens, highs, lows, closes = [], [], [], [], []
        
        for date, temps in daily_data.items():
            if temps:
                dates.append(date)
                opens.append(temps[0])
                closes.append(temps[-1])
                highs.append(max(temps))
                lows.append(min(temps))
        
        return {
            'dates': dates,
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'closes': closes
        }

    def _process_bar_data(self, data_points: List[TemperatureDataPoint]) -> Dict[str, Any]:
        """Process data for bar chart."""
        # Group by hour for bar chart
        hourly_avg = {}
        
        for point in data_points:
            hour_key = point.timestamp.replace(minute=0, second=0, microsecond=0)
            if hour_key not in hourly_avg:
                hourly_avg[hour_key] = []
            hourly_avg[hour_key].append(point.temperature)
        
        hours = sorted(hourly_avg.keys())
        avg_temps = [np.mean(hourly_avg[hour]) for hour in hours]
        
        return {
            'x_bar': hours,
            'y_bar': avg_temps
        }

    def _process_area_data(self, data_points: List[TemperatureDataPoint]) -> Dict[str, Any]:
        """Process data for area chart."""
        # Add baseline for area chart
        return {
            'baseline': 0,
            'alpha': 0.3
        }

    def _export_to_csv(self, data_points: List[TemperatureDataPoint]) -> str:
        """Export data to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Timestamp', 'Temperature', 'Feels Like', 'Humidity', 
            'Pressure', 'Wind Speed', 'Condition', 'Location'
        ])
        
        # Write data
        for point in data_points:
            writer.writerow([
                point.timestamp.isoformat(),
                point.temperature,
                point.feels_like,
                point.humidity,
                point.pressure,
                point.wind_speed,
                point.condition,
                point.location
            ])
        
        return output.getvalue()

    def _export_to_json(self, data_points: List[TemperatureDataPoint]) -> str:
        """Export data to JSON format."""
        import json
        
        data = [point.to_dict() for point in data_points]
        return json.dumps(data, indent=2, default=str)

    def _export_to_excel(self, data_points: List[TemperatureDataPoint]) -> str:
        """Export data to Excel format."""
        # This would require openpyxl library
        # For now, return CSV format as fallback
        return self._export_to_csv(data_points)