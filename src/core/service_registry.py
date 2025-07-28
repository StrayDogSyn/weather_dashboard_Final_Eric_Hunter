#!/usr/bin/env python3
"""
Service Registry for Dependency Injection

This module provides the service registry that configures and registers
all services for the dependency injection container. It demonstrates
how to set up a comprehensive service registration system.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0 (Dependency Injection Implementation)
"""

from typing import Dict, Any, Optional
from pathlib import Path

from .interfaces import (
    IWeatherService, IDatabase, ICacheService, IConfigurationService,
    ILoggingService, IGeminiService, IGitHubService, ISpotifyService,
    ServiceLifetime
)
from .dependency_container import DependencyContainer, get_container

# Import service implementations
from ..services.weather_service_impl import WeatherServiceImpl, MockWeatherService
from ..services.database_impl import DatabaseImpl, MockDatabase
from ..services.cache_service_impl import CacheServiceImpl, MockCacheService
from ..services.config_service_impl import ConfigurationServiceImpl, MockConfigurationService
from ..services.logging_service_impl import LoggingServiceImpl, MockLoggingService

# Import existing services for adaptation
from services.weather_service import WeatherService
from data.database import Database
from .config_manager import ConfigManager


class ServiceRegistry:
    """Service registry for configuring dependency injection.
    
    This class provides methods to register all application services
    with the dependency injection container, supporting both production
    and testing configurations.
    """
    
    def __init__(self, container: Optional[DependencyContainer] = None):
        """Initialize the service registry.
        
        Args:
            container: Optional dependency container (uses global if None)
        """
        self._container = container or get_container()
        self._is_configured = False
        self._configuration_mode = 'production'
    
    def configure_production_services(self, 
                                    config_path: Optional[str] = None,
                                    database_path: Optional[str] = None,
                                    cache_dir: Optional[str] = None) -> None:
        """Configure services for production environment.
        
        Args:
            config_path: Path to configuration file
            database_path: Path to database file
            cache_dir: Directory for cache files
        """
        self._configuration_mode = 'production'
        
        # Register configuration service first (other services depend on it)
        self._container.register_factory(
            IConfigurationService,
            lambda: ConfigurationServiceImpl(
                config_file_path=config_path
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register logging service (depends on configuration)
        self._container.register_factory(
            ILoggingService,
            lambda: LoggingServiceImpl(
                config_service=self._container.resolve(IConfigurationService)
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register cache service (depends on logging)
        self._container.register_factory(
            ICacheService,
            lambda: CacheServiceImpl(
                logger=self._container.resolve(ILoggingService),
                max_memory_entries=1000,
                default_ttl_seconds=3600,
                file_cache_dir=cache_dir or "cache",
                enable_file_cache=True
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register database service (depends on configuration and logging)
        self._container.register_factory(
            IDatabase,
            lambda: DatabaseImpl(
                config_service=self._container.resolve(IConfigurationService),
                logger_service=self._container.resolve(ILoggingService)
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register weather service (depends on configuration, logging, and cache)
        self._container.register_factory(
            IWeatherService,
            lambda: WeatherServiceImpl(
                config_service=self._container.resolve(IConfigurationService),
                cache_service=self._container.resolve(ICacheService),
                logger_service=self._container.resolve(ILoggingService)
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register external service interfaces (to be implemented)
        self._register_external_services()
        
        self._is_configured = True
        
        # Log successful configuration
        logger = self._container.resolve(ILoggingService)
        logger.info("Production services configured successfully",
                   config_path=config_path,
                   database_path=database_path,
                   cache_dir=cache_dir)
    
    def configure_testing_services(self) -> None:
        """Configure services for testing environment.
        
        This configuration uses mock implementations for all services,
        enabling isolated unit testing without external dependencies.
        """
        self._configuration_mode = 'testing'
        
        # Register mock configuration service
        self._container.register_factory(
            IConfigurationService,
            lambda: MockConfigurationService(),
            ServiceLifetime.SINGLETON
        )
        
        # Register mock logging service
        self._container.register_factory(
            ILoggingService,
            lambda: MockLoggingService(capture_logs=True),
            ServiceLifetime.SINGLETON
        )
        
        # Register mock cache service
        self._container.register_factory(
            ICacheService,
            lambda: MockCacheService(should_fail=False),
            ServiceLifetime.SINGLETON
        )
        
        # Register mock database service
        self._container.register_factory(
            IDatabase,
            lambda: MockDatabase(),
            ServiceLifetime.SINGLETON
        )
        
        # Register mock weather service
        self._container.register_factory(
            IWeatherService,
            lambda: MockWeatherService(),
            ServiceLifetime.SINGLETON
        )
        
        # Register mock external services
        self._register_mock_external_services()
        
        self._is_configured = True
        
        # Log successful configuration
        logger = self._container.resolve(ILoggingService)
        logger.info("Testing services configured successfully")
    
    def configure_development_services(self, 
                                     config_path: Optional[str] = None,
                                     use_mock_external: bool = True) -> None:
        """Configure services for development environment.
        
        Args:
            config_path: Path to configuration file
            use_mock_external: Whether to use mock external services
        """
        self._configuration_mode = 'development'
        
        # Register configuration service
        self._container.register_factory(
            IConfigurationService,
            lambda: ConfigurationServiceImpl(
                config_file_path=config_path
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register logging service with debug level
        self._container.register_factory(
            ILoggingService,
            lambda: LoggingServiceImpl(
                config_service=self._container.resolve(IConfigurationService)
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register cache service with shorter TTL for development
        self._container.register_factory(
            ICacheService,
            lambda: CacheServiceImpl(
                logger=self._container.resolve(ILoggingService),
                max_memory_entries=100,
                default_ttl_seconds=300,  # 5 minutes for development
                file_cache_dir="dev_cache",
                enable_file_cache=True
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register database service with development database
        self._container.register_factory(
            IDatabase,
            lambda: DatabaseImpl(
                config_service=self._container.resolve(IConfigurationService),
                logger_service=self._container.resolve(ILoggingService)
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register weather service
        self._container.register_factory(
            IWeatherService,
            lambda: WeatherServiceImpl(
                config_service=self._container.resolve(IConfigurationService),
                cache_service=self._container.resolve(ICacheService),
                logger_service=self._container.resolve(ILoggingService)
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register external services (mock or real based on parameter)
        if use_mock_external:
            self._register_mock_external_services()
        else:
            self._register_external_services()
        
        self._is_configured = True
        
        # Log successful configuration
        logger = self._container.resolve(ILoggingService)
        logger.info("Development services configured successfully",
                   use_mock_external=use_mock_external)
    
    def _register_external_services(self) -> None:
        """Register external service interfaces.
        
        Note: These are placeholder registrations. In a real implementation,
        you would register actual implementations of these services.
        """
        # Placeholder for Gemini service
        self._container.register_factory(
            IGeminiService,
            lambda: self._create_placeholder_service("GeminiService"),
            ServiceLifetime.TRANSIENT
        )
        
        # Placeholder for GitHub service
        self._container.register_factory(
            IGitHubService,
            lambda: self._create_placeholder_service("GitHubService"),
            ServiceLifetime.TRANSIENT
        )
        
        # Placeholder for Spotify service
        self._container.register_factory(
            ISpotifyService,
            lambda: self._create_placeholder_service("SpotifyService"),
            ServiceLifetime.TRANSIENT
        )
    
    def _register_mock_external_services(self) -> None:
        """Register mock external services for testing/development."""
        # Mock Gemini service
        self._container.register_factory(
            IGeminiService,
            lambda: MockExternalService("MockGeminiService"),
            ServiceLifetime.SINGLETON
        )
        
        # Mock GitHub service
        self._container.register_factory(
            IGitHubService,
            lambda: MockExternalService("MockGitHubService"),
            ServiceLifetime.SINGLETON
        )
        
        # Mock Spotify service
        self._container.register_factory(
            ISpotifyService,
            lambda: MockExternalService("MockSpotifyService"),
            ServiceLifetime.SINGLETON
        )
    
    def _create_placeholder_service(self, service_name: str) -> Any:
        """Create a placeholder service implementation.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Placeholder service instance
        """
        return PlaceholderService(service_name)
    
    def register_custom_service(self, 
                              interface_type: type,
                              implementation_factory: callable,
                              lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """Register a custom service with the container.
        
        Args:
            interface_type: Service interface type
            implementation_factory: Factory function to create service instance
            lifetime: Service lifetime
        """
        # Use register_factory for all custom services since we're dealing with factory functions
        # Note: SCOPED lifetime is treated as TRANSIENT since scoped isn't implemented
        if lifetime == ServiceLifetime.SCOPED:
            lifetime = ServiceLifetime.TRANSIENT
        
        self._container.register_factory(interface_type, implementation_factory, lifetime)
        
        # Log registration if logger available
        try:
            logger = self._container.resolve(ILoggingService)
            logger.info(f"Custom service registered: {interface_type.__name__}",
                       lifetime=lifetime.value)
        except:
            pass  # Logger may not be available yet
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about registered services.
        
        Returns:
            Dictionary containing service registration information
        """
        registrations = self._container.get_registrations()
        
        service_info = {
            'configuration_mode': self._configuration_mode,
            'is_configured': self._is_configured,
            'total_services': len(registrations),
            'services': {}
        }
        
        for interface_type, registration in registrations.items():
            service_info['services'][interface_type.__name__] = {
                'interface': interface_type.__name__,
                'lifetime': registration.lifetime.value,
                'is_resolved': registration.instance is not None
            }
        
        return service_info
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate that all required services are properly configured.
        
        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'service_status': {}
        }
        
        required_services = [
            IConfigurationService,
            ILoggingService,
            ICacheService,
            IDatabase,
            IWeatherService
        ]
        
        for service_type in required_services:
            service_name = service_type.__name__
            try:
                # Try to resolve the service
                service = self._container.resolve(service_type)
                validation_results['service_status'][service_name] = {
                    'registered': True,
                    'resolvable': True,
                    'type': type(service).__name__
                }
            except Exception as e:
                validation_results['is_valid'] = False
                validation_results['errors'].append(f"{service_name}: {str(e)}")
                validation_results['service_status'][service_name] = {
                    'registered': False,
                    'resolvable': False,
                    'error': str(e)
                }
        
        # Note: Circular dependency detection is handled during resolution
        # by the DependencyContainer's _resolution_stack mechanism
        
        return validation_results
    
    def reset_configuration(self) -> None:
        """Reset the service configuration."""
        self._container.clear()
        self._is_configured = False
        self._configuration_mode = 'production'
    
    @property
    def is_configured(self) -> bool:
        """Check if services are configured.
        
        Returns:
            True if services are configured, False otherwise
        """
        return self._is_configured
    
    @property
    def configuration_mode(self) -> str:
        """Get the current configuration mode.
        
        Returns:
            Current configuration mode
        """
        return self._configuration_mode


class PlaceholderService:
    """Placeholder service implementation for external services.
    
    This class provides a basic implementation that can be used
    when actual external service implementations are not available.
    """
    
    def __init__(self, service_name: str):
        """Initialize the placeholder service.
        
        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.is_placeholder = True
    
    def __getattr__(self, name: str) -> Any:
        """Handle method calls on placeholder service.
        
        Args:
            name: Method name
            
        Returns:
            Placeholder method that logs the call
        """
        def placeholder_method(*args, **kwargs):
            print(f"[{self.service_name}] Placeholder method called: {name}")
            return None
        
        return placeholder_method


class MockExternalService:
    """Mock external service implementation for testing.
    
    This class provides a mock implementation that can be used
    for testing external service integrations.
    """
    
    def __init__(self, service_name: str):
        """Initialize the mock external service.
        
        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.is_mock = True
        self.call_log = []
    
    def __getattr__(self, name: str) -> Any:
        """Handle method calls on mock service.
        
        Args:
            name: Method name
            
        Returns:
            Mock method that logs the call and returns mock data
        """
        def mock_method(*args, **kwargs):
            call_info = {
                'method': name,
                'args': args,
                'kwargs': kwargs,
                'timestamp': time.time()
            }
            self.call_log.append(call_info)
            
            print(f"[{self.service_name}] Mock method called: {name}")
            
            # Return mock data based on method name
            if 'get' in name.lower():
                return {'mock_data': True, 'service': self.service_name}
            elif 'create' in name.lower() or 'post' in name.lower():
                return {'success': True, 'id': 'mock_id_123'}
            elif 'update' in name.lower() or 'put' in name.lower():
                return {'success': True, 'updated': True}
            elif 'delete' in name.lower():
                return {'success': True, 'deleted': True}
            else:
                return True
        
        return mock_method
    
    def get_call_log(self) -> list:
        """Get the call log for testing.
        
        Returns:
            List of method calls made to this mock service
        """
        return self.call_log.copy()
    
    def clear_call_log(self) -> None:
        """Clear the call log."""
        self.call_log.clear()


# Global service registry instance
_global_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance.
    
    Returns:
        Global service registry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ServiceRegistry()
    return _global_registry


def set_service_registry(registry: ServiceRegistry) -> None:
    """Set the global service registry instance.
    
    Args:
        registry: Service registry instance to set as global
    """
    global _global_registry
    _global_registry = registry


def reset_service_registry() -> None:
    """Reset the global service registry."""
    global _global_registry
    if _global_registry:
        _global_registry.reset_configuration()
    _global_registry = None


# Convenience functions for common configurations
def configure_for_production(config_path: Optional[str] = None,
                           database_path: Optional[str] = None,
                           cache_dir: Optional[str] = None) -> ServiceRegistry:
    """Configure services for production environment.
    
    Args:
        config_path: Path to configuration file
        database_path: Path to database file
        cache_dir: Directory for cache files
        
    Returns:
        Configured service registry
    """
    registry = get_service_registry()
    registry.configure_production_services(config_path, database_path, cache_dir)
    return registry


def configure_for_testing() -> ServiceRegistry:
    """Configure services for testing environment.
    
    Returns:
        Configured service registry with mock services
    """
    registry = get_service_registry()
    registry.configure_testing_services()
    return registry


def configure_for_development(config_path: Optional[str] = None,
                            use_mock_external: bool = True) -> ServiceRegistry:
    """Configure services for development environment.
    
    Args:
        config_path: Path to configuration file
        use_mock_external: Whether to use mock external services
        
    Returns:
        Configured service registry
    """
    registry = get_service_registry()
    registry.configure_development_services(config_path, use_mock_external)
    return registry