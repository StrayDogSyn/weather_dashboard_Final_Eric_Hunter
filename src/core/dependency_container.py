#!/usr/bin/env python3
"""
Dependency Injection Container Implementation

This module provides a comprehensive dependency injection container that supports
singleton, transient, and scoped service lifetimes. It enables loose coupling
and improves testability throughout the application.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0 (Dependency Injection Implementation)
"""

import inspect
import threading
from typing import Dict, Any, Type, TypeVar, Callable, Optional, get_type_hints
from dataclasses import dataclass
from .interfaces import IDependencyContainer, ServiceLifetime


T = TypeVar('T')


@dataclass
class ServiceRegistration:
    """Service registration information."""
    interface_type: Type
    implementation_type: Optional[Type]
    instance: Optional[Any]
    lifetime: ServiceLifetime
    factory: Optional[Callable[[], Any]]


class DependencyResolutionError(Exception):
    """Exception raised when dependency resolution fails."""
    pass


class CircularDependencyError(DependencyResolutionError):
    """Exception raised when circular dependencies are detected."""
    pass


class DependencyContainer(IDependencyContainer):
    """Dependency injection container implementation.
    
    This container supports:
    - Singleton: One instance per container lifetime
    - Transient: New instance every time
    - Scoped: One instance per scope (future enhancement)
    - Instance: Pre-created instance
    - Factory: Custom factory function
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceRegistration] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._resolution_stack: set = set()
    
    def register_singleton(self, interface_type: Type, implementation_type: Type) -> None:
        """Register a singleton service.
        
        Args:
            interface_type: Interface type
            implementation_type: Implementation type
        """
        with self._lock:
            self._validate_registration(interface_type, implementation_type)
            self._services[interface_type] = ServiceRegistration(
                interface_type=interface_type,
                implementation_type=implementation_type,
                instance=None,
                lifetime=ServiceLifetime.SINGLETON,
                factory=None
            )
    
    def register_transient(self, interface_type: Type, implementation_type: Type) -> None:
        """Register a transient service.
        
        Args:
            interface_type: Interface type
            implementation_type: Implementation type
        """
        with self._lock:
            self._validate_registration(interface_type, implementation_type)
            self._services[interface_type] = ServiceRegistration(
                interface_type=interface_type,
                implementation_type=implementation_type,
                instance=None,
                lifetime=ServiceLifetime.TRANSIENT,
                factory=None
            )
    
    def register_instance(self, interface_type: Type, instance: Any) -> None:
        """Register a specific instance.
        
        Args:
            interface_type: Interface type
            instance: Instance to register
        """
        with self._lock:
            if not isinstance(instance, interface_type):
                raise ValueError(f"Instance must implement {interface_type.__name__}")
            
            self._services[interface_type] = ServiceRegistration(
                interface_type=interface_type,
                implementation_type=None,
                instance=instance,
                lifetime=ServiceLifetime.SINGLETON,
                factory=None
            )
            self._singletons[interface_type] = instance
    
    def register_factory(self, interface_type: Type, factory: Callable[[], Any], 
                        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """Register a factory function for creating instances.
        
        Args:
            interface_type: Interface type
            factory: Factory function that creates instances
            lifetime: Service lifetime
        """
        with self._lock:
            self._services[interface_type] = ServiceRegistration(
                interface_type=interface_type,
                implementation_type=None,
                instance=None,
                lifetime=lifetime,
                factory=factory
            )
    
    def resolve(self, interface_type: Type[T]) -> T:
        """Resolve a service instance.
        
        Args:
            interface_type: Interface type to resolve
            
        Returns:
            Service instance
            
        Raises:
            DependencyResolutionError: If service cannot be resolved
            CircularDependencyError: If circular dependency detected
        """
        with self._lock:
            return self._resolve_internal(interface_type)
    
    def _resolve_internal(self, interface_type: Type[T]) -> T:
        """Internal resolution method with circular dependency detection."""
        # Check for circular dependencies
        if interface_type in self._resolution_stack:
            cycle = " -> ".join([t.__name__ for t in self._resolution_stack]) + f" -> {interface_type.__name__}"
            raise CircularDependencyError(f"Circular dependency detected: {cycle}")
        
        # Check if service is registered
        if interface_type not in self._services:
            raise DependencyResolutionError(f"Service {interface_type.__name__} is not registered")
        
        registration = self._services[interface_type]
        
        # Handle pre-registered instance
        if registration.instance is not None:
            return registration.instance
        
        # Handle singleton lifetime
        if registration.lifetime == ServiceLifetime.SINGLETON:
            if interface_type in self._singletons:
                return self._singletons[interface_type]
        
        # Add to resolution stack for circular dependency detection
        self._resolution_stack.add(interface_type)
        
        try:
            # Create instance
            if registration.factory is not None:
                instance = registration.factory()
            else:
                instance = self._create_instance(registration.implementation_type)
            
            # Store singleton
            if registration.lifetime == ServiceLifetime.SINGLETON:
                self._singletons[interface_type] = instance
            
            return instance
        
        finally:
            # Remove from resolution stack
            self._resolution_stack.discard(interface_type)
    
    def _create_instance(self, implementation_type: Type) -> Any:
        """Create an instance with dependency injection.
        
        Args:
            implementation_type: Type to instantiate
            
        Returns:
            Created instance with dependencies injected
        """
        # Get constructor signature
        constructor = implementation_type.__init__
        signature = inspect.signature(constructor)
        
        # Get type hints for parameters
        type_hints = get_type_hints(constructor)
        
        # Resolve constructor parameters
        kwargs = {}
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
            
            # Get parameter type from type hints
            param_type = type_hints.get(param_name)
            if param_type is None:
                # Try to get from annotation
                param_type = param.annotation
            
            if param_type == inspect.Parameter.empty:
                # No type annotation, check if has default value
                if param.default != inspect.Parameter.empty:
                    continue
                else:
                    raise DependencyResolutionError(
                        f"Cannot resolve parameter '{param_name}' for {implementation_type.__name__}: "
                        f"No type annotation and no default value"
                    )
            
            # Resolve dependency
            try:
                dependency = self._resolve_internal(param_type)
                kwargs[param_name] = dependency
            except DependencyResolutionError:
                # Check if parameter has default value
                if param.default != inspect.Parameter.empty:
                    continue
                else:
                    raise DependencyResolutionError(
                        f"Cannot resolve dependency '{param_type.__name__}' for parameter '{param_name}' "
                        f"in {implementation_type.__name__}"
                    )
        
        # Create instance
        return implementation_type(**kwargs)
    
    def _validate_registration(self, interface_type: Type, implementation_type: Type) -> None:
        """Validate service registration.
        
        Args:
            interface_type: Interface type
            implementation_type: Implementation type
            
        Raises:
            ValueError: If registration is invalid
        """
        if not inspect.isclass(implementation_type):
            raise ValueError(f"Implementation type must be a class, got {type(implementation_type)}")
        
        if not issubclass(implementation_type, interface_type):
            raise ValueError(
                f"Implementation {implementation_type.__name__} must implement "
                f"interface {interface_type.__name__}"
            )
    
    def is_registered(self, interface_type: Type) -> bool:
        """Check if a service is registered.
        
        Args:
            interface_type: Interface type to check
            
        Returns:
            True if registered, False otherwise
        """
        with self._lock:
            return interface_type in self._services
    
    def get_registration_info(self, interface_type: Type) -> Optional[ServiceRegistration]:
        """Get registration information for a service.
        
        Args:
            interface_type: Interface type
            
        Returns:
            Service registration info or None if not registered
        """
        with self._lock:
            return self._services.get(interface_type)
    
    def get_registered_services(self) -> Dict[Type, ServiceRegistration]:
        """Get all registered services.
        
        Returns:
            Dictionary of registered services
        """
        with self._lock:
            return self._services.copy()
    
    def clear(self) -> None:
        """Clear all registrations and singletons."""
        with self._lock:
            self._services.clear()
            self._singletons.clear()
            self._resolution_stack.clear()
    
    def create_scope(self) -> 'ScopedContainer':
        """Create a scoped container (future enhancement).
        
        Returns:
            Scoped container instance
        """
        return ScopedContainer(self)


class ScopedContainer(DependencyContainer):
    """Scoped dependency container for request/operation-specific lifetimes.
    
    This is a future enhancement for handling scoped services that live
    for the duration of a specific operation or request.
    """
    
    def __init__(self, parent_container: DependencyContainer):
        super().__init__()
        self._parent = parent_container
        self._scoped_instances: Dict[Type, Any] = {}
    
    def _resolve_internal(self, interface_type: Type[T]) -> T:
        """Resolve with scoped lifetime support."""
        # Check if we have a scoped instance
        if interface_type in self._scoped_instances:
            return self._scoped_instances[interface_type]
        
        # Check if registered in this scope
        if interface_type in self._services:
            registration = self._services[interface_type]
            if registration.lifetime == ServiceLifetime.SCOPED:
                instance = super()._resolve_internal(interface_type)
                self._scoped_instances[interface_type] = instance
                return instance
        
        # Delegate to parent container
        return self._parent._resolve_internal(interface_type)
    
    def dispose(self) -> None:
        """Dispose scoped instances."""
        for instance in self._scoped_instances.values():
            if hasattr(instance, 'dispose'):
                try:
                    instance.dispose()
                except Exception:
                    pass  # Log error in production
        
        self._scoped_instances.clear()


# Global container instance
_global_container: Optional[DependencyContainer] = None
_container_lock = threading.Lock()


def get_container() -> DependencyContainer:
    """Get the global dependency container instance.
    
    Returns:
        Global dependency container
    """
    global _global_container
    
    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = DependencyContainer()
    
    return _global_container


def set_container(container: DependencyContainer) -> None:
    """Set the global dependency container instance.
    
    Args:
        container: Container instance to set as global
    """
    global _global_container
    
    with _container_lock:
        _global_container = container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _global_container
    
    with _container_lock:
        if _global_container is not None:
            _global_container.clear()
        _global_container = None