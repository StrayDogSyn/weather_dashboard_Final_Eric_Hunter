"""Async Service Manager for Weather Dashboard.

Coordinates the initialization of all services using the AsyncLoader
to optimize startup time and provide better user experience.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import time

from .async_loader import AsyncLoader, LoadingTask, LoadingPriority, LoadingResult


class AsyncServiceManager:
    """Manages async initialization of all weather dashboard services."""
    
    def __init__(self, config_service=None, progress_callback: Optional[Callable] = None):
        """Initialize the service manager.
        
        Args:
            config_service: Configuration service instance
            progress_callback: Optional callback for progress updates
        """
        self.logger = logging.getLogger(__name__)
        self.config_service = config_service
        self.progress_callback = progress_callback
        
        # Service instances
        self.services: Dict[str, Any] = {}
        self.initialization_results: Dict[str, LoadingResult] = {}
        
        # Async loader
        self.loader = AsyncLoader(max_workers=6, cache_enabled=True)
        
        # Add progress callback
        if progress_callback:
            self.loader.add_progress_callback(self._on_progress_update)
        
        # Service initialization status
        self.is_initialized = False
        self.initialization_time = 0.0
        
        self.logger.info("AsyncServiceManager initialized")
    
    def _on_progress_update(self, task_name: str, progress: float):
        """Handle progress updates from the async loader.
        
        Args:
            task_name: Name of the task
            progress: Progress percentage (0.0 to 1.0)
        """
        if self.progress_callback:
            try:
                self.progress_callback(task_name, progress)
            except Exception as e:
                self.logger.error(f"Progress callback failed: {e}")
    
    def _setup_loading_tasks(self):
        """Setup all loading tasks with proper priorities and dependencies."""
        # Critical services (must load first)
        self.loader.add_task(LoadingTask(
            name="config_service",
            func=self._init_config_service,
            priority=LoadingPriority.CRITICAL,
            timeout=10.0,
            cache_key="config_service"
        ))
        
        self.loader.add_task(LoadingTask(
            name="logging_service",
            func=self._init_logging_service,
            priority=LoadingPriority.CRITICAL,
            timeout=5.0,
            cache_key="logging_service"
        ))
        
        # High priority services (core functionality)
        self.loader.add_task(LoadingTask(
            name="weather_service",
            func=self._init_weather_service,
            priority=LoadingPriority.HIGH,
            timeout=15.0,
            dependencies=["config_service"],
            cache_key="weather_service"
        ))
        
        self.loader.add_task(LoadingTask(
            name="geocoding_service",
            func=self._init_geocoding_service,
            priority=LoadingPriority.HIGH,
            timeout=10.0,
            dependencies=["config_service"],
            cache_key="geocoding_service"
        ))
        
        self.loader.add_task(LoadingTask(
            name="cache_service",
            func=self._init_cache_service,
            priority=LoadingPriority.HIGH,
            timeout=8.0,
            dependencies=["config_service"],
            cache_key="cache_service"
        ))
        
        # Normal priority services
        self.loader.add_task(LoadingTask(
            name="data_service",
            func=self._init_data_service,
            priority=LoadingPriority.NORMAL,
            timeout=12.0,
            dependencies=["config_service", "cache_service"],
            cache_key="data_service"
        ))
        
        self.loader.add_task(LoadingTask(
            name="maps_service",
            func=self._init_maps_service,
            priority=LoadingPriority.NORMAL,
            timeout=10.0,
            dependencies=["config_service"],
            cache_key="maps_service"
        ))
        
        # Low priority services (can be loaded later)
        self.loader.add_task(LoadingTask(
            name="activity_suggestions",
            func=self._init_activity_suggestions,
            priority=LoadingPriority.LOW,
            timeout=20.0,
            dependencies=["weather_service"],
            retry_count=2,  # Reduce retries for non-critical service
            cache_key="activity_suggestions"
        ))
        
        self.loader.add_task(LoadingTask(
            name="notification_service",
            func=self._init_notification_service,
            priority=LoadingPriority.LOW,
            timeout=8.0,
            dependencies=["config_service"],
            cache_key="notification_service"
        ))
        
        # Deferred services (load only when needed)
        self.loader.add_task(LoadingTask(
            name="export_service",
            func=self._init_export_service,
            priority=LoadingPriority.DEFERRED,
            timeout=5.0,
            dependencies=["config_service"],
            cache_key="export_service"
        ))
    
    # Service initialization methods
    def _init_config_service(self):
        """Initialize configuration service."""
        try:
            if self.config_service:
                self.logger.info("Using provided config service")
                return self.config_service
            
            from .config.config_service import ConfigService
            service = ConfigService()
            self.logger.info("Config service initialized")
            return service
        except Exception as e:
            self.logger.error(f"Failed to initialize config service: {e}")
            raise
    
    def _init_logging_service(self):
        """Initialize logging service."""
        try:
            # Logging is already initialized in main.py
            self.logger.info("Logging service verified")
            return True
        except Exception as e:
            self.logger.error(f"Failed to verify logging service: {e}")
            raise
    
    def _init_weather_service(self):
        """Initialize enhanced weather service."""
        try:
            from .weather.enhanced_weather_service import EnhancedWeatherService
            
            config_service = self.services.get('config_service')
            if not config_service:
                raise Exception("Config service not available")
            
            service = EnhancedWeatherService(config_service)
            self.logger.info("Weather service initialized")
            return service
        except Exception as e:
            self.logger.error(f"Failed to initialize weather service: {e}")
            raise
    
    def _init_geocoding_service(self):
        """Initialize geocoding service."""
        try:
            from .geocoding_service import GeocodingService
            
            config_service = self.services.get('config_service')
            if not config_service:
                raise Exception("Config service not available")
            
            service = GeocodingService(config_service)
            self.logger.info("Geocoding service initialized")
            return service
        except Exception as e:
            self.logger.error(f"Failed to initialize geocoding service: {e}")
            raise
    
    def _init_cache_service(self):
        """Initialize cache service."""
        try:
            from .cache.cache_service import CacheService
            
            config_service = self.services.get('config_service')
            if not config_service:
                raise Exception("Config service not available")
            
            service = CacheService(config_service)
            self.logger.info("Cache service initialized")
            return service
        except Exception as e:
            self.logger.error(f"Failed to initialize cache service: {e}")
            raise
    
    def _init_data_service(self):
        """Initialize data service."""
        try:
            from .data_service import DataService
            
            config_service = self.services.get('config_service')
            cache_service = self.services.get('cache_service')
            
            if not config_service:
                raise Exception("Config service not available")
            
            service = DataService(config_service, cache_service)
            self.logger.info("Data service initialized")
            return service
        except Exception as e:
            self.logger.error(f"Failed to initialize data service: {e}")
            raise
    
    def _init_maps_service(self):
        """Initialize maps service."""
        try:
            from .google_maps_service import GoogleMapsService
            
            config_service = self.services.get('config_service')
            if not config_service:
                raise Exception("Config service not available")
            
            service = GoogleMapsService(config_service)
            self.logger.info("Maps service initialized")
            return service
        except Exception as e:
            self.logger.error(f"Failed to initialize maps service: {e}")
            raise
    
    def _init_activity_suggestions(self):
        """Initialize activity suggestions service."""
        try:
            from .activity_suggestions import ActivitySuggestions
            
            weather_service = self.services.get('weather_service')
            if not weather_service:
                raise Exception("Weather service not available")
            
            service = ActivitySuggestions(weather_service)
            self.logger.info("Activity suggestions service initialized")
            return service
        except Exception as e:
            self.logger.warning(f"Failed to initialize activity suggestions: {e}")
            # Return None for non-critical service
            return None
    
    def _init_notification_service(self):
        """Initialize notification service."""
        try:
            # Placeholder for notification service
            self.logger.info("Notification service initialized (placeholder)")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize notification service: {e}")
            raise
    
    def _init_export_service(self):
        """Initialize export service."""
        try:
            # Placeholder for export service
            self.logger.info("Export service initialized (placeholder)")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize export service: {e}")
            raise
    
    async def initialize_all_services(self) -> Dict[str, LoadingResult]:
        """Initialize all services asynchronously.
        
        Returns:
            Dictionary of service initialization results
        """
        start_time = time.time()
        
        try:
            self.logger.info("Starting async service initialization")
            
            # Setup loading tasks
            self._setup_loading_tasks()
            
            # Execute all tasks with priority handling
            results = await self.loader.load_with_priorities()
            
            # Store successful services
            for task_name, result in results.items():
                if result.success and result.data is not None:
                    self.services[task_name] = result.data
                    self.logger.info(f"Service {task_name} loaded successfully")
                else:
                    self.logger.warning(f"Service {task_name} failed to load: {result.error}")
            
            self.initialization_results = results
            self.initialization_time = time.time() - start_time
            self.is_initialized = True
            
            # Log summary
            successful_services = sum(1 for r in results.values() if r.success)
            total_services = len(results)
            
            self.logger.info(
                f"Service initialization completed: {successful_services}/{total_services} "
                f"services loaded in {self.initialization_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            raise
    
    async def initialize_critical_services(self) -> Dict[str, LoadingResult]:
        """Initialize only critical services for fast startup.
        
        Returns:
            Dictionary of critical service initialization results
        """
        try:
            self.logger.info("Starting critical service initialization")
            
            # Setup only critical tasks
            critical_tasks = {
                "config_service": self._init_config_service,
                "logging_service": self._init_logging_service,
                "weather_service": self._init_weather_service,
            }
            
            results = await self.loader.load_parallel(critical_tasks)
            
            # Store successful services
            for task_name, result in results.items():
                if result is not None:
                    self.services[task_name] = result
                    self.logger.info(f"Critical service {task_name} loaded")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Critical service initialization failed: {e}")
            raise
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service instance by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance or None if not available
        """
        return self.services.get(service_name)
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if a service is available.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if service is available and loaded
        """
        return service_name in self.services and self.services[service_name] is not None
    
    def get_initialization_summary(self) -> Dict[str, Any]:
        """Get a summary of the initialization process.
        
        Returns:
            Dictionary with initialization statistics
        """
        if not self.initialization_results:
            return {"status": "not_initialized"}
        
        successful = sum(1 for r in self.initialization_results.values() if r.success)
        failed = len(self.initialization_results) - successful
        
        return {
            "status": "completed" if self.is_initialized else "in_progress",
            "total_services": len(self.initialization_results),
            "successful_services": successful,
            "failed_services": failed,
            "initialization_time": self.initialization_time,
            "cache_stats": self.loader.get_cache_stats(),
            "services": list(self.services.keys())
        }
    
    def cleanup(self):
        """Clean up resources and services."""
        try:
            # Cleanup async loader
            if self.loader:
                self.loader.cleanup()
            
            # Cleanup services that have cleanup methods
            for service_name, service in self.services.items():
                if hasattr(service, 'cleanup'):
                    try:
                        service.cleanup()
                        self.logger.info(f"Cleaned up service: {service_name}")
                    except Exception as e:
                        self.logger.error(f"Error cleaning up {service_name}: {e}")
            
            self.services.clear()
            self.initialization_results.clear()
            
            self.logger.info("AsyncServiceManager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore cleanup errors during destruction