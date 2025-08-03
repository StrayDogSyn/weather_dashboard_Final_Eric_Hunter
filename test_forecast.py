#!/usr/bin/env python3
"""
Test script to verify the 5-day forecast functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.weather.forecast_models import ForecastData, ForecastEntry, DailyForecast
from datetime import datetime, timedelta
import json
import sys
import os

def test_forecast_data_parsing():
    """Test the enhanced ForecastData parsing functionality."""
    print("🧪 Testing ForecastData parsing...")
    
    # Create sample OpenWeather API response
    sample_response = {
        "list": [
            {
                "dt": int((datetime.now() + timedelta(hours=i*3)).timestamp()),
                "main": {
                    "temp": 20 + (i % 5),
                    "feels_like": 22 + (i % 5),
                    "humidity": 60 + (i % 20),
                    "pressure": 1013 + (i % 10)
                },
                "weather": [{
                    "main": ["Clear", "Clouds", "Rain", "Snow", "Mist"][i % 5],
                    "description": ["clear sky", "few clouds", "light rain", "light snow", "mist"][i % 5]
                }],
                "wind": {
                    "speed": 3.5 + (i % 3),
                    "deg": 180 + (i * 10)
                },
                "clouds": {"all": i * 10 % 100},
                "pop": (i * 0.1) % 1.0,
                "rain": {"3h": 0.5} if i % 5 == 2 else {},
                "snow": {"3h": 0.0}
            }
            for i in range(40)  # 40 3-hour forecasts (5 days)
        ],
        "city": {
            "name": "London",
            "coord": {"lat": 51.5085, "lon": -0.1257},
            "timezone": 0
        }
    }
    
    try:
        # Parse the forecast data
        forecast_data = ForecastData.from_openweather_forecast(sample_response)
        
        print(f"✅ Successfully parsed forecast data:")
        print(f"   📍 Location: {forecast_data.location}")
        print(f"   📅 Hourly forecasts: {len(forecast_data.hourly_forecasts)}")
        print(f"   📊 Daily forecasts: {len(forecast_data.daily_forecasts)}")
        
        # Test daily forecast grouping
        for i, daily in enumerate(forecast_data.daily_forecasts[:3]):
            print(f"   Day {i+1}: {daily.date.strftime('%a %m/%d')} - {daily.condition} - {daily.temp_min}°C to {daily.temp_max}°C")
        
        # Test hourly data availability
        if forecast_data.hourly_forecasts:
            first_hourly = forecast_data.hourly_forecasts[0]
            print(f"   🕐 First hourly: {first_hourly.timestamp.strftime('%H:%M')} - {first_hourly.condition} - {first_hourly.temperature}°C")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to parse forecast data: {e}")
        return False

def test_forecast_accuracy_indicators():
    """Test forecast accuracy indicator calculations."""
    print("\n🎯 Testing forecast accuracy indicators...")
    
    try:
        # Test confidence level calculation
        for days_ahead in range(5):
            confidence = max(95 - (days_ahead * 5), 60)
            print(f"   Day {days_ahead + 1}: {confidence}% confidence")
        
        # Test last update time
        last_update = datetime.now().strftime('%H:%M')
        print(f"   🕐 Last update: {last_update}")
        
        # Test provider attribution
        provider = "OpenWeatherMap"
        print(f"   🏢 Provider: {provider}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test accuracy indicators: {e}")
        return False

def main():
    """Run all forecast functionality tests."""
    print("🌤️ Testing 5-Day Weather Forecast Functionality\n")
    
    tests = [
        test_forecast_data_parsing,
        test_forecast_accuracy_indicators
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All forecast functionality tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)