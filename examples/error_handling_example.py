#!/usr/bin/env python3
"""
Error Handling and Reliability Patterns Example

This example demonstrates how to use the updated weather service
with comprehensive error handling and reliability patterns.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0
"""

import asyncio
import sys
import os
from typing import Optional, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.dependency_container import DependencyContainer
from core.interfaces import IWeatherService
from core.exceptions import (
    ExternalServiceError, NetworkError, TimeoutError, ValidationError,
    ErrorSeverity, ErrorCategory
)
from core.error_handling import ErrorContext, error_boundary
from core.logging_framework import StructuredLogger
from services.weather_service_impl import MockWeatherService


class WeatherApplicationExample:
    """Example application demonstrating error handling patterns."""
    
    def __init__(self):
        """Initialize the example application."""
        self._logger = StructuredLogger(
            name="WeatherApp",
            service_name="weather-app-example",
            service_version="1.0.0"
        )
        
        # Initialize dependency container
        self._container = DependencyContainer()
        
        # For this example, we'll use the mock service
        self._weather_service = MockWeatherService()
        
        self._logger.info("Weather application example initialized")
    
    def demonstrate_successful_weather_request(self) -> None:
        """Demonstrate a successful weather request."""
        self._logger.info("=== Demonstrating Successful Weather Request ===")
        
        try:
            with error_boundary(
                operation="get_weather_success",
                logger=self._logger,
                fallback_value=None
            ) as boundary:
                weather_data = self._weather_service.get_current_weather("New York")
                
                if weather_data:
                    self._logger.info(
                        "Successfully retrieved weather data",
                        extra={
                            "location": weather_data.location,
                            "temperature": weather_data.temperature,
                            "description": weather_data.description
                        }
                    )
                    print(f"Weather in {weather_data.location}: {weather_data.temperature}°C, {weather_data.description}")
                else:
                    print("No weather data available")
                    
        except Exception as e:
            self._logger.error(f"Unexpected error in successful request demo: {e}")
            print(f"Error: {e}")
    
    def demonstrate_error_handling(self) -> None:
        """Demonstrate error handling with simulated failures."""
        self._logger.info("=== Demonstrating Error Handling ===")
        
        # Enable failure simulation
        self._weather_service.set_should_fail(True)
        
        try:
            with error_boundary(
                operation="get_weather_with_errors",
                logger=self._logger,
                fallback_value=None
            ) as boundary:
                weather_data = self._weather_service.get_current_weather("London")
                
                if weather_data:
                    print(f"Weather in {weather_data.location}: {weather_data.temperature}°C")
                else:
                    print("No weather data available (fallback)")
                    
        except ExternalServiceError as e:
            self._logger.error(
                "External service error caught",
                extra={
                    "error_message": e.message,
                    "user_message": e.user_message,
                    "context": e.context,
                    "severity": e.severity.value
                }
            )
            print(f"Service Error: {e.user_message}")
            
        except Exception as e:
            self._logger.error(f"Unexpected error in error handling demo: {e}")
            print(f"Unexpected Error: {e}")
        
        # Disable failure simulation
        self._weather_service.set_should_fail(False)
    
    def demonstrate_validation_errors(self) -> None:
        """Demonstrate validation error handling."""
        self._logger.info("=== Demonstrating Validation Errors ===")
        
        # Test empty location
        try:
            weather_data = self._weather_service.get_current_weather("")
        except ValueError as e:
            self._logger.warning(
                "Validation error caught",
                extra={"error": str(e), "input": "empty_string"}
            )
            print(f"Validation Error: {e}")
        
        # Test invalid forecast days
        try:
            forecast_data = self._weather_service.get_forecast("Paris", days=20)
        except ValueError as e:
            self._logger.warning(
                "Validation error caught",
                extra={"error": str(e), "input": "days=20"}
            )
            print(f"Validation Error: {e}")
    
    def demonstrate_forecast_with_recovery(self) -> None:
        """Demonstrate forecast retrieval with error recovery."""
        self._logger.info("=== Demonstrating Forecast with Recovery ===")
        
        try:
            with error_boundary(
                operation="get_forecast",
                logger=self._logger,
                fallback_value=[]
            ) as boundary:
                forecast_data = self._weather_service.get_forecast("Tokyo", days=5)
                
                if forecast_data:
                    self._logger.info(
                        "Successfully retrieved forecast data",
                        extra={"location": "Tokyo", "days": len(forecast_data)}
                    )
                    print(f"5-day forecast for Tokyo:")
                    for i, day_data in enumerate(forecast_data[:3]):  # Show first 3 days
                        print(f"  Day {i+1}: {day_data.temperature}°C, {day_data.description}")
                else:
                    print("No forecast data available (using fallback)")
                    
        except Exception as e:
            self._logger.error(f"Error in forecast demo: {e}")
            print(f"Error: {e}")
    
    def demonstrate_connection_testing(self) -> None:
        """Demonstrate connection testing with reliability patterns."""
        self._logger.info("=== Demonstrating Connection Testing ===")
        
        try:
            # Test successful connection
            is_connected = self._weather_service.test_connection()
            
            if is_connected:
                self._logger.info("Weather service connection test passed")
                print("✓ Weather service is available")
            else:
                self._logger.warning("Weather service connection test failed")
                print("✗ Weather service is not available")
            
            # Test with simulated failure
            self._weather_service.set_should_fail(True)
            is_connected_fail = self._weather_service.test_connection()
            
            if not is_connected_fail:
                self._logger.info("Connection test correctly detected simulated failure")
                print("✓ Connection test correctly detected service failure")
            
            self._weather_service.set_should_fail(False)
            
        except Exception as e:
            self._logger.error(f"Error in connection test demo: {e}")
            print(f"Error: {e}")
    
    def demonstrate_provider_status(self) -> None:
        """Demonstrate provider status retrieval."""
        self._logger.info("=== Demonstrating Provider Status ===")
        
        try:
            status = self._weather_service.get_provider_status()
            
            self._logger.info(
                "Retrieved provider status",
                extra={"status": status}
            )
            
            print("Provider Status:")
            print(f"  Demo Mode: {status.get('demo_mode', 'Unknown')}")
            print(f"  Call Count: {status.get('call_count', 'Unknown')}")
            print(f"  Cache Enabled: {status.get('cache_enabled', 'Unknown')}")
            
            providers = status.get('providers', {})
            for provider_name, provider_info in providers.items():
                print(f"  Provider '{provider_name}': {provider_info}")
                
        except Exception as e:
            self._logger.error(f"Error in provider status demo: {e}")
            print(f"Error: {e}")
    
    def run_all_demonstrations(self) -> None:
        """Run all demonstration scenarios."""
        print("Weather Service Error Handling and Reliability Demonstration")
        print("=" * 60)
        
        try:
            self.demonstrate_successful_weather_request()
            print()
            
            self.demonstrate_error_handling()
            print()
            
            self.demonstrate_validation_errors()
            print()
            
            self.demonstrate_forecast_with_recovery()
            print()
            
            self.demonstrate_connection_testing()
            print()
            
            self.demonstrate_provider_status()
            print()
            
            print("All demonstrations completed successfully!")
            
        except Exception as e:
            self._logger.error(f"Critical error in demonstration: {e}")
            print(f"Critical Error: {e}")
        
        finally:
            self._logger.info("Weather application example completed")


def main():
    """Main entry point for the example."""
    app = WeatherApplicationExample()
    app.run_all_demonstrations()


if __name__ == "__main__":
    main()