"""Service Factory and Dependency Injection Container

Centralized service instantiation and dependency management
following the Dependency Injection pattern.
"""

from typing import Dict, Type, Any, Optional, TypeVar, Generic
from abc import ABC, abstractmethod
import logging

T = TypeVar('T')


class ServiceContainer:
    """Dependency injection container for managing services."""
    
    def __init__(self):
        """Initialize the service container."""
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register a singleton service instance.
        
        Args:
            service_type: The service type/interface
            instance: The service instance
        """
        key = service_type.__name__
        self._singletons[key] = instance
        self.logger.debug(f"Registered singleton: {key}")
    
    def register_factory(self, service_type: Type[T], factory: callable) -> None:
        """Register a factory function for creating service instances.
        
        Args:
            service_type: The service type/interface
            factory: Factory function that creates the service
        """
        key = service_type.__name__
        self._factories[key] = factory
        self.logger.debug(f"Registered factory: {key}")
    
    def get(self, service_type: Type[T]) -> Optional[T]:
        """Get a service instance.
        
        Args:
            service_type: The service type to retrieve
            
        Returns:
            Service instance or None if not found
        """
        key = service_type.__name__
        
        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]
        
        # Check factories
        if key in self._factories:
            try:
                instance = self._factories[key]()
                self.logger.debug(f"Created instance from factory: {key}")
                return instance
            except Exception as e:
                self.logger.error(f"Failed to create instance from factory {key}: {e}")
                return None
        
        self.logger.warning(f"Service not found: {key}")
        return None
    
    def has(self, service_type: Type[T]) -> bool:
        """Check if a service is registered.
        
        Args:
            service_type: The service type to check
            
        Returns:
            True if service is registered, False otherwise
        """
        key = service_type.__name__
        return key in self._singletons or key in self._factories
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._singletons.clear()
        self._factories.clear()
        self.logger.debug("Service container cleared")


class ServiceFactory:
    """Factory for creating and configuring services."""
    
    def __init__(self, container: ServiceContainer):
        """Initialize the service factory.
        
        Args:
            container: The dependency injection container
        """
        self.container = container
        self.logger = logging.getLogger(__name__)
    
    def create_weather_service(self, config_service=None):
        """Create a weather service instance.
        
        Args:
            config_service: Configuration service instance
            
        Returns:
            Weather service instance
        """
        from services.enhanced_weather_service import EnhancedWeatherService
        from services.config_service import ConfigService
        
        if config_service is None:
            config_service = self.container.get(ConfigService) or ConfigService()
        
        return EnhancedWeatherService(config_service)
    
    def create_logging_service(self):
        """Create a logging service instance.
        
        Returns:
            Logging service instance
        """
        from services.logging_service import LoggingService
        return LoggingService()
    
    def create_config_service(self):
        """Create a configuration service instance.
        
        Returns:
            Configuration service instance
        """
        from services.config_service import ConfigService
        return ConfigService()
    
    def setup_default_services(self) -> None:
        """Setup default service registrations."""
        from services.config_service import ConfigService
        from services.logging_service import LoggingService
        from interfaces.weather_service_interface import IWeatherService
        
        # Register factories
        self.container.register_factory(ConfigService, self.create_config_service)
        self.container.register_factory(LoggingService, self.create_logging_service)
        self.container.register_factory(IWeatherService, self.create_weather_service)
        
        self.logger.info("Default services registered")


# Global service container instance
_container = ServiceContainer()
_factory = ServiceFactory(_container)


def get_service_container() -> ServiceContainer:
    """Get the global service container.
    
    Returns:
        Global service container instance
    """
    return _container


def get_service_factory() -> ServiceFactory:
    """Get the global service factory.
    
    Returns:
        Global service factory instance
    """
    return _factory


def initialize_services() -> None:
    """Initialize default services in the container."""
    _factory.setup_default_services()