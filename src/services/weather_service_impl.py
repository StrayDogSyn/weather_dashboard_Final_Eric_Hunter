#!/usr/bin/env python3
"""
Weather Service Implementation for Dependency Injection

This module provides the concrete implementation of IWeatherService interface,
adapting the existing WeatherService to work with the dependency injection system.
It demonstrates how to bridge existing code with new DI patterns.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0 (Dependency Injection Implementation)
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.interfaces import IWeatherService, WeatherDataDTO, IConfigurationService, ICacheService, ILoggingService
from .weather_service import WeatherService, WeatherData, WeatherProvider
from ..core.config_manager import ConfigManager


class WeatherServiceImpl(IWeatherService):
    """Implementation of IWeatherService using the existing WeatherService.
    
    This adapter class bridges the existing WeatherService with the new
    dependency injection interface, demonstrating how to integrate legacy
    code with modern DI patterns.
    """
    
    def __init__(self, 
                 config_service: IConfigurationService,
                 cache_service: Optional[ICacheService] = None,
                 logger_service: Optional[ILoggingService] = None):
        """Initialize the weather service implementation.
        
        Args:
            config_service: Configuration service for API keys and settings
            cache_service: Optional cache service for weather data
            logger_service: Optional logging service
        """
        self._config_service = config_service
        self._cache_service = cache_service
        self._logger_service = logger_service
        
        # Create ConfigManager from our configuration service
        self._config_manager = self._create_config_manager()
        
        # Initialize the underlying weather service
        self._weather_service = None
        self._service_lock = asyncio.Lock()
        
        self._log_info("WeatherServiceImpl initialized")
    
    def _create_config_manager(self) -> ConfigManager:
        """Create a ConfigManager from the configuration service.
        
        Returns:
            Configured ConfigManager instance
        """
        # This would typically map from our config service to the legacy ConfigManager
        # For now, we'll use the existing ConfigManager
        return ConfigManager()
    
    def _log_info(self, message: str, **kwargs) -> None:
        """Log an info message if logger service is available."""
        if self._logger_service:
            self._logger_service.info(message, **kwargs)
    
    def _log_error(self, message: str, **kwargs) -> None:
        """Log an error message if logger service is available."""
        if self._logger_service:
            self._logger_service.error(message, **kwargs)
    
    def _log_warning(self, message: str, **kwargs) -> None:
        """Log a warning message if logger service is available."""
        if self._logger_service:
            self._logger_service.warning(message, **kwargs)
    
    async def _get_weather_service(self) -> WeatherService:
        """Get or create the underlying weather service instance.
        
        Returns:
            WeatherService instance
        """
        if self._weather_service is None:
            async with self._service_lock:
                if self._weather_service is None:
                    self._weather_service = WeatherService(self._config_manager)
                    await self._weather_service.__aenter__()
        
        return self._weather_service
    
    def _convert_to_dto(self, weather_data: WeatherData) -> WeatherDataDTO:
        """Convert WeatherData to WeatherDataDTO.
        
        Args:
            weather_data: Internal weather data object
            
        Returns:
            Weather data DTO for interface compliance
        """
        return WeatherDataDTO(
            location=f"{weather_data.city}, {weather_data.country}",
            temperature=weather_data.temperature,
            feels_like=weather_data.feels_like,
            humidity=weather_data.humidity,
            pressure=weather_data.pressure,
            description=weather_data.description,
            icon=weather_data.icon_code,
            wind_speed=weather_data.wind_speed,
            wind_direction=weather_data.wind_direction,
            visibility=weather_data.visibility,
            uv_index=weather_data.uv_index,
            timestamp=weather_data.timestamp
        )
    
    def get_current_weather(self, location: str, use_cache: bool = True) -> Optional[WeatherDataDTO]:
        """Get current weather data for a location.
        
        Args:
            location: Location name or coordinates
            use_cache: Whether to use cached data if available
            
        Returns:
            Weather data or None if unavailable
        """
        try:
            # Run the async method synchronously
            return asyncio.run(self._async_get_current_weather(location, use_cache))
        except Exception as e:
            self._log_error(f"Error getting current weather for {location}: {e}")
            return None
    
    async def _async_get_current_weather(self, location: str, use_cache: bool = True) -> Optional[WeatherDataDTO]:
        """Async implementation of get_current_weather.
        
        Args:
            location: Location name or coordinates
            use_cache: Whether to use cached data if available
            
        Returns:
            Weather data or None if unavailable
        """
        try:
            weather_service = await self._get_weather_service()
            weather_data = await weather_service.get_current_weather(location, use_cache)
            
            if weather_data:
                dto = self._convert_to_dto(weather_data)
                self._log_info(f"Successfully retrieved weather for {location}")
                return dto
            else:
                self._log_warning(f"No weather data available for {location}")
                return None
                
        except Exception as e:
            self._log_error(f"Error in async get_current_weather for {location}: {e}")
            return None
    
    def get_forecast(self, location: str, days: int = 5) -> List[WeatherDataDTO]:
        """Get weather forecast for a location.
        
        Args:
            location: Location name or coordinates
            days: Number of days to forecast
            
        Returns:
            List of forecast data
        """
        try:
            return asyncio.run(self._async_get_forecast(location, days))
        except Exception as e:
            self._log_error(f"Error getting forecast for {location}: {e}")
            return []
    
    async def _async_get_forecast(self, location: str, days: int = 5) -> List[WeatherDataDTO]:
        """Async implementation of get_forecast.
        
        Args:
            location: Location name or coordinates
            days: Number of days to forecast
            
        Returns:
            List of forecast data
        """
        try:
            # For now, we'll generate mock forecast data based on current weather
            # In a real implementation, this would call a forecast API
            current_weather = await self._async_get_current_weather(location, True)
            
            if not current_weather:
                return []
            
            forecast_data = []
            for i in range(days):
                # Create forecast data based on current weather with some variation
                forecast_dto = WeatherDataDTO(
                    location=current_weather.location,
                    temperature=current_weather.temperature + (i * 0.5),  # Slight variation
                    feels_like=current_weather.feels_like + (i * 0.5),
                    humidity=max(30, min(90, current_weather.humidity + (i * 2))),
                    pressure=current_weather.pressure + (i * 0.1),
                    description=current_weather.description,
                    icon=current_weather.icon,
                    wind_speed=current_weather.wind_speed + (i * 0.2),
                    wind_direction=current_weather.wind_direction,
                    visibility=current_weather.visibility,
                    uv_index=current_weather.uv_index,
                    timestamp=datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
                )
                forecast_data.append(forecast_dto)
            
            self._log_info(f"Generated {days}-day forecast for {location}")
            return forecast_data
            
        except Exception as e:
            self._log_error(f"Error in async get_forecast for {location}: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test if the weather service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            return asyncio.run(self._async_test_connection())
        except Exception as e:
            self._log_error(f"Error testing connection: {e}")
            return False
    
    async def _async_test_connection(self) -> bool:
        """Async implementation of test_connection.
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            weather_service = await self._get_weather_service()
            
            # Try to get weather for a known location
            test_weather = await weather_service.get_current_weather("London", use_cache=False)
            
            if test_weather:
                self._log_info("Weather service connection test successful")
                return True
            else:
                self._log_warning("Weather service connection test failed - no data returned")
                return False
                
        except Exception as e:
            self._log_error(f"Weather service connection test failed: {e}")
            return False
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of weather data providers.
        
        Returns:
            Dictionary containing provider status information
        """
        try:
            return asyncio.run(self._async_get_provider_status())
        except Exception as e:
            self._log_error(f"Error getting provider status: {e}")
            return {}
    
    async def _async_get_provider_status(self) -> Dict[str, Any]:
        """Async implementation of get_provider_status.
        
        Returns:
            Dictionary containing provider status information
        """
        try:
            weather_service = await self._get_weather_service()
            status = weather_service.get_provider_status()
            
            # Add additional status information
            enhanced_status = {
                'providers': status,
                'demo_mode': weather_service.demo_mode,
                'cache_enabled': self._cache_service is not None,
                'last_check': datetime.now().isoformat()
            }
            
            self._log_info("Retrieved provider status")
            return enhanced_status
            
        except Exception as e:
            self._log_error(f"Error in async get_provider_status: {e}")
            return {}
    
    async def dispose(self) -> None:
        """Dispose of resources."""
        if self._weather_service:
            try:
                await self._weather_service.__aexit__(None, None, None)
                self._log_info("WeatherServiceImpl disposed")
            except Exception as e:
                self._log_error(f"Error disposing WeatherServiceImpl: {e}")
            finally:
                self._weather_service = None
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        if self._weather_service:
            try:
                # Try to clean up if possible
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.dispose())
            except Exception:
                pass  # Ignore errors during cleanup


class MockWeatherService(IWeatherService):
    """Mock weather service implementation for testing.
    
    This class provides a mock implementation of IWeatherService
    that can be used for unit testing and development scenarios
    where real weather data is not needed.
    """
    
    def __init__(self, logger_service: Optional[ILoggingService] = None):
        """Initialize the mock weather service.
        
        Args:
            logger_service: Optional logging service
        """
        self._logger_service = logger_service
        self._call_count = 0
        self._should_fail = False
        
        self._log_info("MockWeatherService initialized")
    
    def _log_info(self, message: str, **kwargs) -> None:
        """Log an info message if logger service is available."""
        if self._logger_service:
            self._logger_service.info(message, **kwargs)
    
    def set_should_fail(self, should_fail: bool) -> None:
        """Set whether the service should simulate failures.
        
        Args:
            should_fail: Whether to simulate failures
        """
        self._should_fail = should_fail
    
    def get_call_count(self) -> int:
        """Get the number of times the service has been called.
        
        Returns:
            Number of service calls
        """
        return self._call_count
    
    def get_current_weather(self, location: str, use_cache: bool = True) -> Optional[WeatherDataDTO]:
        """Get mock current weather data.
        
        Args:
            location: Location name or coordinates
            use_cache: Whether to use cached data if available
            
        Returns:
            Mock weather data or None if simulating failure
        """
        self._call_count += 1
        
        if self._should_fail:
            self._log_info(f"MockWeatherService simulating failure for {location}")
            return None
        
        # Generate consistent mock data based on location
        import hashlib
        location_hash = int(hashlib.md5(location.lower().encode()).hexdigest()[:8], 16)
        
        mock_data = WeatherDataDTO(
            location=location.title(),
            temperature=20.0 + (location_hash % 20),
            feels_like=22.0 + (location_hash % 20),
            humidity=50 + (location_hash % 40),
            pressure=1013.25 + (location_hash % 50),
            description="Mock weather condition",
            icon="01d",
            wind_speed=10.0 + (location_hash % 15),
            wind_direction=location_hash % 360,
            visibility=10.0,
            uv_index=5.0,
            timestamp=datetime.now()
        )
        
        self._log_info(f"MockWeatherService returning data for {location}")
        return mock_data
    
    def get_forecast(self, location: str, days: int = 5) -> List[WeatherDataDTO]:
        """Get mock weather forecast.
        
        Args:
            location: Location name or coordinates
            days: Number of days to forecast
            
        Returns:
            List of mock forecast data
        """
        self._call_count += 1
        
        if self._should_fail:
            self._log_info(f"MockWeatherService simulating forecast failure for {location}")
            return []
        
        current_weather = self.get_current_weather(location, use_cache=False)
        if not current_weather:
            return []
        
        forecast_data = []
        for i in range(days):
            forecast_dto = WeatherDataDTO(
                location=current_weather.location,
                temperature=current_weather.temperature + i,
                feels_like=current_weather.feels_like + i,
                humidity=current_weather.humidity,
                pressure=current_weather.pressure,
                description=current_weather.description,
                icon=current_weather.icon,
                wind_speed=current_weather.wind_speed,
                wind_direction=current_weather.wind_direction,
                visibility=current_weather.visibility,
                uv_index=current_weather.uv_index,
                timestamp=datetime.now()
            )
            forecast_data.append(forecast_dto)
        
        self._log_info(f"MockWeatherService returning {days}-day forecast for {location}")
        return forecast_data
    
    def test_connection(self) -> bool:
        """Test mock connection.
        
        Returns:
            True unless simulating failure
        """
        self._call_count += 1
        result = not self._should_fail
        self._log_info(f"MockWeatherService connection test: {result}")
        return result
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get mock provider status.
        
        Returns:
            Mock provider status information
        """
        self._call_count += 1
        
        status = {
            'providers': {
                'mock': {
                    'enabled': True,
                    'has_api_key': True,
                    'base_url': 'mock://weather.service'
                }
            },
            'demo_mode': True,
            'cache_enabled': False,
            'last_check': datetime.now().isoformat(),
            'call_count': self._call_count,
            'should_fail': self._should_fail
        }
        
        self._log_info("MockWeatherService returning provider status")
        return status