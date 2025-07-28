#!/usr/bin/env python3
"""
Dependency Injection Testing Example

This module demonstrates how the dependency injection refactoring enables
easy testing with mock services, showcasing the before/after testing benefits.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Optional, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import dependency injection infrastructure
from src.core.interfaces import (
    IWeatherService, IDatabase, ICacheService, IConfigurationService,
    ILoggingService, WeatherDataDTO
)
from src.core.dependency_container import get_container, reset_container
from src.core.service_registry import configure_for_testing, get_service_registry
from main import WeatherDashboardApp


class TestDependencyInjectionBenefits(unittest.TestCase):
    """
    Test class demonstrating the testing benefits of dependency injection.
    
    BEFORE: Testing was difficult due to tight coupling:
    - Real services were instantiated during tests
    - Network calls were made, making tests slow and unreliable
    - Hard to simulate error conditions
    - Difficult to test edge cases
    
    AFTER: Testing is easy with dependency injection:
    - Mock services are automatically injected
    - No network calls during tests
    - Easy to simulate any scenario
    - Tests are fast and reliable
    """
    
    def setUp(self):
        """Setup test environment with dependency injection.
        
        This method demonstrates how easy it is to setup tests
        with dependency injection - just configure for testing
        and all services are automatically mocked.
        """
        # Reset container to ensure clean state
        reset_container()
        
        # Configure for testing - this automatically sets up all mock services
        configure_for_testing()
        
        # Create application instance with testing environment
        self.app = WeatherDashboardApp(environment='testing')
        
        # Get references to injected mock services for test verification
        self.mock_weather_service = self.app.container.resolve(IWeatherService)
        self.mock_database = self.app.container.resolve(IDatabase)
        self.mock_cache_service = self.app.container.resolve(ICacheService)
        self.mock_logger = self.app.container.resolve(ILoggingService)
        self.mock_config_service = self.app.container.resolve(IConfigurationService)
    
    def tearDown(self):
        """Clean up after each test."""
        reset_container()
    
    def test_weather_service_injection(self):
        """Test that weather service is properly injected and mockable.
        
        ✅ BENEFIT: Easy to verify that the correct service is injected
        and that it's a mock service suitable for testing.
        """
        # Verify that the injected service is the mock implementation
        self.assertIsNotNone(self.mock_weather_service)
        self.assertTrue(hasattr(self.mock_weather_service, '_is_mock'))
        
        # Verify that the service implements the interface
        self.assertIsInstance(self.mock_weather_service, IWeatherService)
    
    def test_get_weather_success_scenario(self):
        """Test successful weather retrieval with predictable mock data.
        
        ✅ BENEFIT: Tests are fast and reliable because they use mock data
        instead of making real API calls.
        """
        # The mock weather service returns predictable test data
        # No real API calls are made during testing
        
        # This would have been impossible to test reliably before DI
        # because it would make real API calls
        weather_data = self.mock_weather_service.get_current_weather("London")
        
        # Verify mock data is returned
        self.assertIsNotNone(weather_data)
        self.assertEqual(weather_data.location, "London")
        self.assertEqual(weather_data.temperature, 20.0)  # Predictable mock data
        self.assertEqual(weather_data.condition, "Sunny")
    
    def test_get_weather_error_scenario(self):
        """Test weather service error handling with simulated failures.
        
        ✅ BENEFIT: Easy to simulate error conditions without relying on
        actual API failures or network issues.
        """
        # Configure mock to simulate an error
        self.mock_weather_service.should_fail = True
        
        # Test error handling
        try:
            weather_data = self.mock_weather_service.get_current_weather("InvalidLocation")
            self.assertIsNone(weather_data)
        except Exception as e:
            # Verify that the expected error is raised
            self.assertIn("Mock weather service error", str(e))
    
    def test_database_integration_with_mocks(self):
        """Test database operations with mock database.
        
        ✅ BENEFIT: Database tests don't require actual database setup
        and are isolated from database state.
        """
        # Create test weather data
        test_weather = WeatherDataDTO(
            location="TestCity",
            temperature=25.0,
            condition="Cloudy",
            humidity=60,
            wind_speed=10.0,
            timestamp="2024-01-01T12:00:00Z"
        )
        
        # Test saving data (uses mock database)
        result = self.mock_database.save_weather_data(test_weather)
        self.assertTrue(result)
        
        # Test retrieving data (uses mock database)
        recent_data = self.mock_database.get_recent_weather_data(limit=5)
        self.assertIsInstance(recent_data, list)
        self.assertGreater(len(recent_data), 0)
    
    def test_caching_behavior_with_mock_cache(self):
        """Test caching behavior with mock cache service.
        
        ✅ BENEFIT: Cache behavior can be tested without setting up
        actual cache infrastructure.
        """
        # Test cache operations
        cache_key = "test_weather_london"
        test_data = {"temperature": 22.0, "condition": "Rainy"}
        
        # Test cache set operation
        result = self.mock_cache_service.set(cache_key, test_data, ttl=300)
        self.assertTrue(result)
        
        # Test cache get operation
        cached_data = self.mock_cache_service.get(cache_key)
        self.assertEqual(cached_data, test_data)
        
        # Test cache miss
        missing_data = self.mock_cache_service.get("nonexistent_key")
        self.assertIsNone(missing_data)
    
    def test_logging_integration_with_mock_logger(self):
        """Test logging integration with mock logger.
        
        ✅ BENEFIT: Logging behavior can be verified without creating
        actual log files or configuring logging infrastructure.
        """
        # Test different log levels
        self.mock_logger.info("Test info message", extra_field="test_value")
        self.mock_logger.warning("Test warning message")
        self.mock_logger.error("Test error message", error_code=500)
        
        # Verify that logging calls were made (mock logger tracks calls)
        self.assertTrue(hasattr(self.mock_logger, 'log_calls'))
        self.assertGreater(len(self.mock_logger.log_calls), 0)
    
    def test_configuration_service_with_mock_config(self):
        """Test configuration service with mock configuration.
        
        ✅ BENEFIT: Configuration tests don't require actual config files
        and can test various configuration scenarios.
        """
        # Test getting configuration values
        api_key = self.mock_config_service.get_setting("weather.api_key")
        self.assertEqual(api_key, "mock_api_key")
        
        # Test setting configuration values
        self.mock_config_service.set_setting("app.theme", "dark")
        theme = self.mock_config_service.get_setting("app.theme")
        self.assertEqual(theme, "dark")
        
        # Test getting all settings
        all_settings = self.mock_config_service.get_all_settings()
        self.assertIsInstance(all_settings, dict)
        self.assertIn("weather", all_settings)
    
    def test_service_lifetime_management(self):
        """Test that service lifetimes are properly managed.
        
        ✅ BENEFIT: Can verify that singleton services are reused
        and transient services are created fresh.
        """
        container = self.app.container
        
        # Test singleton services (should be same instance)
        weather_service1 = container.resolve(IWeatherService)
        weather_service2 = container.resolve(IWeatherService)
        self.assertIs(weather_service1, weather_service2)  # Same instance
        
        # Test that all core services are singletons
        database1 = container.resolve(IDatabase)
        database2 = container.resolve(IDatabase)
        self.assertIs(database1, database2)  # Same instance
        
        cache1 = container.resolve(ICacheService)
        cache2 = container.resolve(ICacheService)
        self.assertIs(cache1, cache2)  # Same instance
    
    def test_service_registry_validation(self):
        """Test that service registry properly validates configuration.
        
        ✅ BENEFIT: Can verify that all required services are registered
        and properly configured.
        """
        service_registry = get_service_registry()
        
        # Validate that all services are properly registered
        validation_result = service_registry.validate_configuration()
        
        self.assertTrue(validation_result['is_valid'])
        self.assertEqual(len(validation_result['errors']), 0)
        self.assertGreater(len(validation_result['registered_services']), 0)
    
    def test_environment_specific_configuration(self):
        """Test that different environments have different configurations.
        
        ✅ BENEFIT: Can verify that environment-specific service
        registration works correctly.
        """
        # Current app is configured for testing
        self.assertEqual(self.app.environment, 'testing')
        
        # Verify that mock services are used in testing environment
        self.assertTrue(hasattr(self.mock_weather_service, '_is_mock'))
        self.assertTrue(hasattr(self.mock_database, '_is_mock'))
        self.assertTrue(hasattr(self.mock_cache_service, '_is_mock'))


class TestDependencyInjectionPerformance(unittest.TestCase):
    """Test performance benefits of dependency injection.
    
    ✅ BENEFIT: Tests run much faster because they don't make
    real network calls or access real databases.
    """
    
    def setUp(self):
        reset_container()
        configure_for_testing()
        self.app = WeatherDashboardApp(environment='testing')
    
    def tearDown(self):
        reset_container()
    
    def test_fast_weather_operations(self):
        """Test that weather operations are fast with mock services.
        
        ✅ BENEFIT: Tests complete in milliseconds instead of seconds
        because no real API calls are made.
        """
        import time
        
        start_time = time.time()
        
        # Perform multiple weather operations
        for location in ["London", "Paris", "Tokyo", "New York", "Sydney"]:
            weather_data = self.app._weather_service.get_current_weather(location)
            self.assertIsNotNone(weather_data)
            self.assertEqual(weather_data.location, location)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete very quickly with mock services
        self.assertLess(execution_time, 0.1)  # Less than 100ms
    
    def test_fast_database_operations(self):
        """Test that database operations are fast with mock database.
        
        ✅ BENEFIT: Database tests don't require actual database I/O.
        """
        import time
        
        start_time = time.time()
        
        # Perform multiple database operations
        for i in range(10):
            test_weather = WeatherDataDTO(
                location=f"TestCity{i}",
                temperature=20.0 + i,
                condition="Sunny",
                humidity=50 + i,
                wind_speed=5.0 + i,
                timestamp=f"2024-01-0{i+1}T12:00:00Z"
            )
            result = self.app._database.save_weather_data(test_weather)
            self.assertTrue(result)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete very quickly with mock database
        self.assertLess(execution_time, 0.05)  # Less than 50ms


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)