#!/usr/bin/env python3
"""
Application Controller - Main Orchestration Layer

This module implements the main application controller that demonstrates
advanced architectural patterns including:
- Service layer architecture with dependency injection
- Event-driven communication between components
- Centralized state management
- Professional error handling and recovery
- Resource lifecycle management
"""

import asyncio
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path

from ..utils.logger import LoggerMixin, ContextLogger, get_logger
from .config_manager import ConfigManager
from .database_manager import DatabaseManager


@dataclass
class AppState:
    """
    Centralized application state management.

    This class demonstrates professional state management patterns
    including immutable updates and change tracking.
    """

    # Current weather data
    current_weather: Optional[Dict[str, Any]] = None
    weather_last_updated: Optional[datetime] = None

    # User preferences
    selected_city: str = "London"
    temperature_unit: str = "celsius"  # celsius, fahrenheit
    theme_mode: str = "auto"  # light, dark, auto

    # Application status
    is_online: bool = True
    last_api_error: Optional[str] = None
    api_rate_limit_reset: Optional[datetime] = None

    # Feature states
    features_enabled: Dict[str, bool] = field(default_factory=lambda: {
        "temperature_graph": True,
        "weather_journal": True,
        "activity_suggester": True,
        "team_collaboration": True,
        "spotify_integration": False,
        "ai_poetry": False
    })

    # Performance metrics
    startup_time: Optional[datetime] = None
    last_refresh_duration: Optional[float] = None
    total_api_calls: int = 0

    def copy_with_updates(self, **kwargs) -> 'AppState':
        """
        Create a new AppState instance with updated values.

        This method implements immutable state updates, a professional
        pattern for state management that prevents accidental mutations.
        """
        # Create a copy of current state
        current_dict = {
            'current_weather': self.current_weather,
            'weather_last_updated': self.weather_last_updated,
            'selected_city': self.selected_city,
            'temperature_unit': self.temperature_unit,
            'theme_mode': self.theme_mode,
            'is_online': self.is_online,
            'last_api_error': self.last_api_error,
            'api_rate_limit_reset': self.api_rate_limit_reset,
            'features_enabled': self.features_enabled.copy(),
            'startup_time': self.startup_time,
            'last_refresh_duration': self.last_refresh_duration,
            'total_api_calls': self.total_api_calls
        }

        # Apply updates
        current_dict.update(kwargs)

        return AppState(**current_dict)


class EventBus(LoggerMixin):
    """
    Event-driven communication system.

    This class implements the Observer pattern for loose coupling
    between application components, demonstrating professional
    event-driven architecture.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            self._subscribers[event_type].append(callback)
            self.logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from subscribers
        """
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                    self.logger.debug(f"Unsubscribed from event: {event_type}")
                except ValueError:
                    self.logger.warning(f"Callback not found for event: {event_type}")

    def emit(self, event_type: str, data: Any = None) -> None:
        """
        Emit an event to all subscribers.

        Args:
            event_type: Type of event to emit
            data: Event data to pass to subscribers
        """
        event_info = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now(),
            'thread_id': threading.get_ident()
        }

        # Store event in history
        with self._lock:
            self._event_history.append(event_info)
            # Keep only last 1000 events
            if len(self._event_history) > 1000:
                self._event_history = self._event_history[-1000:]

        # Notify subscribers
        subscribers = self._subscribers.get(event_type, [])

        if subscribers:
            self.logger.debug(f"Emitting event: {event_type} to {len(subscribers)} subscribers")

            for callback in subscribers[:]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error in event callback for {event_type}: {e}")
        else:
            self.logger.debug(f"No subscribers for event: {event_type}")

    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent event history.

        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        with self._lock:
            events = self._event_history[-limit:]

            if event_type:
                events = [e for e in events if e['type'] == event_type]

            return events


class ServiceRegistry(LoggerMixin):
    """
    Service registry for dependency injection.

    This class implements a service locator pattern that enables
    loose coupling and testability through dependency injection.
    """

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def register_service(self, name: str, service: Any) -> None:
        """
        Register a service instance.

        Args:
            name: Service name
            service: Service instance
        """
        with self._lock:
            self._services[name] = service
            self.logger.debug(f"Registered service: {name}")

    def register_factory(self, name: str, factory: Callable) -> None:
        """
        Register a service factory function.

        Args:
            name: Service name
            factory: Function that creates service instances
        """
        with self._lock:
            self._factories[name] = factory
            self.logger.debug(f"Registered factory: {name}")

    def register_singleton(self, name: str, factory: Callable) -> None:
        """
        Register a singleton service factory.

        Args:
            name: Service name
            factory: Function that creates the singleton instance
        """
        with self._lock:
            self._factories[name] = factory
            self.logger.debug(f"Registered singleton factory: {name}")

    def get_service(self, name: str) -> Any:
        """
        Get a service instance.

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            KeyError: If service is not registered
        """
        with self._lock:
            # Check for direct service registration
            if name in self._services:
                return self._services[name]

            # Check for singleton
            if name in self._singletons:
                return self._singletons[name]

            # Check for factory
            if name in self._factories:
                service = self._factories[name]()

                # Store as singleton if it was registered as one
                if name not in self._services:
                    self._singletons[name] = service

                return service

            raise KeyError(f"Service not registered: {name}")

    def has_service(self, name: str) -> bool:
        """
        Check if a service is registered.

        Args:
            name: Service name

        Returns:
            True if service is registered
        """
        with self._lock:
            return (name in self._services or
                   name in self._factories or
                   name in self._singletons)

    def list_services(self) -> List[str]:
        """
        Get list of all registered service names.

        Returns:
            List of service names
        """
        with self._lock:
            return list(set(
                list(self._services.keys()) +
                list(self._factories.keys()) +
                list(self._singletons.keys())
            ))


class AppController(LoggerMixin):
    """
    Main application controller.

    This class orchestrates the entire application, demonstrating
    professional architecture patterns including:
    - Service layer coordination
    - State management
    - Event-driven communication
    - Resource lifecycle management
    - Error handling and recovery
    """

    def __init__(self):
        self._state = AppState(startup_time=datetime.now())
        self._event_bus = EventBus()
        self._service_registry = ServiceRegistry()
        self._background_tasks: List[threading.Thread] = []
        self._shutdown_event = threading.Event()
        self._state_lock = threading.Lock()

        # Initialize core services
        self._initialize_core_services()

        # Set up event subscriptions
        self._setup_event_subscriptions()

        self.logger.info("Application controller initialized")

    def _initialize_core_services(self) -> None:
        """
        Initialize core application services.

        This method demonstrates dependency injection setup
        and service registration patterns.
        """
        try:
            # Register core services
            self._service_registry.register_singleton(
                "config_manager",
                lambda: ConfigManager()
            )

            self._service_registry.register_singleton(
                "database_manager",
                lambda: DatabaseManager()
            )

            # Register the event bus and service registry themselves
            self._service_registry.register_service("event_bus", self._event_bus)
            self._service_registry.register_service("service_registry", self._service_registry)

            self.logger.info("Core services initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize core services: {e}")
            raise

    def _setup_event_subscriptions(self) -> None:
        """
        Set up event subscriptions for application coordination.

        This method demonstrates how components can communicate
        through events without tight coupling.
        """
        # Subscribe to weather data updates
        self._event_bus.subscribe("weather_data_updated", self._on_weather_data_updated)
        self._event_bus.subscribe("weather_api_error", self._on_weather_api_error)

        # Subscribe to user preference changes
        self._event_bus.subscribe("city_changed", self._on_city_changed)
        self._event_bus.subscribe("theme_changed", self._on_theme_changed)

        # Subscribe to application events
        self._event_bus.subscribe("feature_toggled", self._on_feature_toggled)
        self._event_bus.subscribe("api_rate_limit_hit", self._on_api_rate_limit_hit)

        self.logger.debug("Event subscriptions configured")

    def get_state(self) -> AppState:
        """
        Get current application state.

        Returns:
            Current application state (immutable copy)
        """
        with self._state_lock:
            return self._state

    def update_state(self, **kwargs) -> None:
        """
        Update application state.

        This method implements thread-safe state updates and
        emits change events for reactive UI updates.

        Args:
            **kwargs: State updates to apply
        """
        with self._state_lock:
            old_state = self._state
            self._state = self._state.copy_with_updates(**kwargs)

            # Emit state change event
            self._event_bus.emit("state_changed", {
                'old_state': old_state,
                'new_state': self._state,
                'changes': kwargs
            })

            self.logger.debug(f"State updated: {list(kwargs.keys())}")

    def get_service(self, name: str) -> Any:
        """
        Get a registered service.

        Args:
            name: Service name

        Returns:
            Service instance
        """
        return self._service_registry.get_service(name)

    def emit_event(self, event_type: str, data: Any = None) -> None:
        """
        Emit an application event.

        Args:
            event_type: Type of event
            data: Event data
        """
        self._event_bus.emit(event_type, data)

    def subscribe_to_event(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to an application event.

        Args:
            event_type: Type of event
            callback: Callback function
        """
        self._event_bus.subscribe(event_type, callback)

    def start_background_task(self, target: Callable, name: str = None, **kwargs) -> threading.Thread:
        """
        Start a background task.

        Args:
            target: Function to run in background
            name: Thread name
            **kwargs: Additional arguments for target function

        Returns:
            Thread instance
        """
        thread = threading.Thread(
            target=target,
            name=name or f"background_task_{len(self._background_tasks)}",
            kwargs=kwargs,
            daemon=True
        )

        self._background_tasks.append(thread)
        thread.start()

        self.logger.info(f"Started background task: {thread.name}")
        return thread

    def shutdown(self) -> None:
        """
        Gracefully shutdown the application.

        This method demonstrates proper resource cleanup and
        graceful shutdown patterns.
        """
        self.logger.info("Starting application shutdown")

        # Signal shutdown to background tasks
        self._shutdown_event.set()

        # Emit shutdown event
        self._event_bus.emit("application_shutdown")

        # Wait for background tasks to complete
        for thread in self._background_tasks:
            if thread.is_alive():
                self.logger.debug(f"Waiting for thread: {thread.name}")
                thread.join(timeout=5.0)

                if thread.is_alive():
                    self.logger.warning(f"Thread did not shutdown gracefully: {thread.name}")

        # Cleanup services
        try:
            if self._service_registry.has_service("database_manager"):
                db_manager = self._service_registry.get_service("database_manager")
                db_manager.close()
        except Exception as e:
            self.logger.error(f"Error during service cleanup: {e}")

        self.logger.info("Application shutdown complete")

    # Event handlers
    def _on_weather_data_updated(self, data: Dict[str, Any]) -> None:
        """
        Handle weather data updates.

        Args:
            data: Weather data
        """
        self.update_state(
            current_weather=data,
            weather_last_updated=datetime.now(),
            is_online=True,
            last_api_error=None,
            total_api_calls=self._state.total_api_calls + 1
        )

    def _on_weather_api_error(self, error_data: Dict[str, Any]) -> None:
        """
        Handle weather API errors.

        Args:
            error_data: Error information
        """
        self.update_state(
            last_api_error=error_data.get('message', 'Unknown API error'),
            is_online=False
        )

    def _on_city_changed(self, city: str) -> None:
        """
        Handle city selection changes.

        Args:
            city: New city name
        """
        self.update_state(selected_city=city)

        # Trigger weather data refresh
        self._event_bus.emit("refresh_weather_requested", {'city': city})

    def _on_theme_changed(self, theme: str) -> None:
        """
        Handle theme changes.

        Args:
            theme: New theme name
        """
        self.update_state(theme_mode=theme)

    def _on_feature_toggled(self, feature_data: Dict[str, Any]) -> None:
        """
        Handle feature toggle events.

        Args:
            feature_data: Feature toggle information
        """
        feature_name = feature_data.get('feature')
        enabled = feature_data.get('enabled', False)

        if feature_name:
            new_features = self._state.features_enabled.copy()
            new_features[feature_name] = enabled
            self.update_state(features_enabled=new_features)

    def _on_api_rate_limit_hit(self, limit_data: Dict[str, Any]) -> None:
        """
        Handle API rate limit events.

        Args:
            limit_data: Rate limit information
        """
        reset_time = limit_data.get('reset_time')
        if reset_time:
            self.update_state(api_rate_limit_reset=reset_time)

    def get_application_info(self) -> Dict[str, Any]:
        """
        Get comprehensive application information.

        Returns:
            Application information dictionary
        """
        state = self.get_state()
        uptime = datetime.now() - state.startup_time if state.startup_time else timedelta(0)

        return {
            'version': '1.0.0',
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime).split('.')[0],  # Remove microseconds
            'state': {
                'selected_city': state.selected_city,
                'temperature_unit': state.temperature_unit,
                'theme_mode': state.theme_mode,
                'is_online': state.is_online,
                'features_enabled': state.features_enabled,
                'total_api_calls': state.total_api_calls,
                'last_refresh_duration': state.last_refresh_duration
            },
            'services': self._service_registry.list_services(),
            'background_tasks': len([t for t in self._background_tasks if t.is_alive()]),
            'recent_events': len(self._event_bus.get_event_history(limit=50))
        }


# Global application controller instance
_app_controller: Optional[AppController] = None


def get_app_controller() -> AppController:
    """
    Get the global application controller instance.

    This function implements the singleton pattern for the main
    application controller, ensuring consistent state management
    throughout the application.

    Returns:
        Application controller instance
    """
    global _app_controller

    if _app_controller is None:
        _app_controller = AppController()

    return _app_controller


def initialize_application() -> AppController:
    """
    Initialize the application with all core services.

    This function demonstrates the application bootstrap process
    including service initialization and configuration.

    Returns:
        Initialized application controller
    """
    logger = get_logger(__name__)

    with ContextLogger(logger, "application initialization"):
        # Get or create application controller
        app_controller = get_app_controller()

        # Initialize database
        db_manager = app_controller.get_service("database_manager")
        db_manager.initialize_database()

        # Load configuration
        config_manager = app_controller.get_service("config_manager")
        config = config_manager.get_config()

        # Update initial state based on configuration
        app_controller.update_state(
            selected_city=config.app.default_city,
            temperature_unit=config.app.temperature_unit,
            theme_mode=config.ui.theme_mode
        )

        logger.info("Application initialized successfully")
        return app_controller


if __name__ == "__main__":
    # Test the application controller
    from ..utils.logger import setup_logging

    setup_logging(log_level="DEBUG")

    app = initialize_application()

    # Test event system
    def test_event_handler(data):
        print(f"Received test event: {data}")

    app.subscribe_to_event("test_event", test_event_handler)
    app.emit_event("test_event", {"message": "Hello, World!"})

    # Print application info
    import json
    print(json.dumps(app.get_application_info(), indent=2, default=str))

    # Cleanup
    app.shutdown()
