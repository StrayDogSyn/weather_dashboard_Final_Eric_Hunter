import threading
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class WeatherDataCollector:
    """Collect and store historical weather data"""
    
    def __init__(self, weather_service, db_service):
        self.weather_service = weather_service
        self.db_service = db_service
        self.collection_interval = 300  # 5 minutes
        self.timer = None
        
    def start_collection(self):
        """Start automatic data collection"""
        self.collect_data()
        
    def collect_data(self):
        """Collect current weather data"""
        try:
            weather = self.weather_service.get_current_weather()
            
            data_point = {
                'timestamp': datetime.now(),
                'temperature': weather.temperature,
                'humidity': weather.humidity,
                'pressure': weather.pressure,
                'wind_speed': weather.wind_speed,
                'precipitation': weather.precipitation,
                'condition': weather.condition
            }
            
            self.db_service.save_weather_data(data_point)
            logger.info(f"Collected weather data: {weather.temperature}°C")
            
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
        
        # Schedule next collection
        self.timer = threading.Timer(self.collection_interval, self.collect_data)
        self.timer.daemon = True
        self.timer.start()
    
    def stop_collection(self):
        """Stop automatic data collection"""
        if self.timer:
            self.timer.cancel()
            self.timer = None
            logger.info("Weather data collection stopped")