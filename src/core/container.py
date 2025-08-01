"""Dependency Injection Container

Provides a centralized service container for managing dependencies
with singleton pattern and lazy loading support.
"""

import logging
from threading import Lock
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

T = TypeVar("T")


class ServiceLifetime:
    """Service lifetime constants."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ServiceDescriptor:
    """Describes how a service should be created and managed."""

    def __init__(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[[], T], T],
        lifetime: str = ServiceLifetime.SINGLETON,
    ):
        """Initialize service descriptor.

        Args:
            service_type: The service interface or abstract class
            implementation: The concrete implementation, factory function, or instance
            lifetime: Service lifetime (singleton, transient, scoped)
        """
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.instance: Optional[T] = None


class ServiceContainer:
    """Dependency injection container with singleton pattern.

    Provides service registration, resolution, and lifecycle management
    with thread-safe operations and lazy loading.
    """

    _instance: Optional["ServiceContainer"] = None
    _lock = Lock()

    def __new__(cls) -> "ServiceContainer":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the service container."""
        if not hasattr(self, "_initialized"):
            self._services: Dict[Type, ServiceDescriptor] = {}
            self._instances: Dict[Type, Any] = {}
            self._creation_lock = Lock()
            self._logger = logging.getLogger(__name__)
            self._initialized = True
            self._logger.info("Service container initialized")

    def register_singleton(
        self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]
    ) -> "ServiceContainer":
        """Register a service as singleton.

        Args:
            service_type: The service interface or abstract class
            implementation: The concrete implementation or factory function

        Returns:
            Self for method chaining
        """
        return self._register(service_type, implementation, ServiceLifetime.SINGLETON)

    def register_transient(
        self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]
    ) -> "ServiceContainer":
        """Register a service as transient (new instance each time).

        Args:
            service_type: The service interface or abstract class
            implementation: The concrete implementation or factory function

        Returns:
            Self for method chaining
        """
        return self._register(service_type, implementation, ServiceLifetime.TRANSIENT)

    def register_instance(self, service_type: Type[T], instance: T) -> "ServiceContainer":
        """Register a service instance.

        Args:
            service_type: The service interface or abstract class
            instance: The service instance

        Returns:
            Self for method chaining
        """
        descriptor = ServiceDescriptor(service_type, instance, ServiceLifetime.SINGLETON)
        descriptor.instance = instance
        self._services[service_type] = descriptor
        self._instances[service_type] = instance
        self._logger.debug(f"Registered instance for {service_type.__name__}")
        return self

    def _register(
        self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]], lifetime: str
    ) -> "ServiceContainer":
        """Internal method to register a service.

        Args:
            service_type: The service interface or abstract class
            implementation: The concrete implementation or factory function
            lifetime: Service lifetime

        Returns:
            Self for method chaining
        """
        descriptor = ServiceDescriptor(service_type, implementation, lifetime)
        self._services[service_type] = descriptor
        self._logger.debug(f"Registered {lifetime} service {service_type.__name__}")
        return self

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance.

        Args:
            service_type: The service type to resolve

        Returns:
            Service instance

        Raises:
            ValueError: If service is not registered
            RuntimeError: If service creation fails
        """
        if service_type not in self._services:
            raise ValueError(f"Service {service_type.__name__} is not registered")

        descriptor = self._services[service_type]

        # Return existing instance for singletons
        if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor.instance is not None:
            return descriptor.instance

        # Create new instance with thread safety
        with self._creation_lock:
            # Double-check for singletons
            if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor.instance is not None:
                return descriptor.instance

            try:
                instance = self._create_instance(descriptor)

                # Store singleton instances
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    descriptor.instance = instance
                    self._instances[service_type] = instance

                self._logger.debug(f"Created instance of {service_type.__name__}")
                return instance

            except Exception as e:
                self._logger.error(f"Failed to create instance of {service_type.__name__}: {e}")
                raise RuntimeError(f"Failed to create service {service_type.__name__}: {e}") from e

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a service instance from descriptor.

        Args:
            descriptor: Service descriptor

        Returns:
            Service instance
        """
        implementation = descriptor.implementation

        # If it's already an instance, return it
        if not callable(implementation) and not isinstance(implementation, type):
            return implementation

        # If it's a callable (factory function), call it
        if callable(implementation) and not isinstance(implementation, type):
            return implementation()

        # If it's a class, instantiate it
        if isinstance(implementation, type):
            return implementation()

        raise ValueError(f"Invalid implementation type for {descriptor.service_type.__name__}")

    def is_registered(self, service_type: Type) -> bool:
        """Check if a service is registered.

        Args:
            service_type: The service type to check

        Returns:
            True if service is registered, False otherwise
        """
        return service_type in self._services

    def get_registered_services(self) -> Dict[Type, str]:
        """Get all registered services and their lifetimes.

        Returns:
            Dictionary mapping service types to their lifetimes
        """
        return {
            service_type: descriptor.lifetime for service_type, descriptor in self._services.items()
        }

    def clear(self) -> None:
        """Clear all registered services and instances."""
        with self._creation_lock:
            self._services.clear()
            self._instances.clear()
            self._logger.info("Service container cleared")

    def dispose(self) -> None:
        """Dispose of all services that implement IDisposable."""
        with self._creation_lock:
            for instance in self._instances.values():
                if hasattr(instance, "dispose") and callable(getattr(instance, "dispose")):
                    try:
                        instance.dispose()
                    except Exception as e:
                        self._logger.error(
                            f"Error disposing service {type(instance).__name__}: {e}"
                        )

            self.clear()
            self._logger.info("Service container disposed")


# Global container instance
container = ServiceContainer()
