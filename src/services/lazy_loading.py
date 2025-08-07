"""Lazy loading service for deferred initialization of services and widgets.

Provides lazy initialization patterns to improve startup performance.
"""

import threading
import time
import logging
import weakref
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Generic, Union
from functools import wraps
from dataclasses import dataclass
from abc import ABC, abstractmethod

T = TypeVar('T')


@dataclass
class LazyLoadStats:
    """Statistics for lazy loading."""
    total_objects: int = 0
    loaded_objects: int = 0
    total_load_time: float = 0.0
    average_load_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def update_load_time(self, load_time: float) -> None:
        """Update load time statistics."""
        self.total_load_time += load_time
        self.loaded_objects += 1
        self.average_load_time = self.total_load_time / self.loaded_objects


class LazyProxy(Generic[T]):
    """Proxy object for lazy loading."""
    
    def __init__(self, factory: Callable[[], T], name: str = ""):
        """
        Initialize lazy proxy.
        
        Args:
            factory: Factory function to create the object
            name: Optional name for debugging
        """
        self._factory = factory
        self._name = name or f"LazyProxy_{id(self)}"
        self._instance: Optional[T] = None
        self._lock = threading.RLock()
        self._load_time: Optional[float] = None
        self._logger = logging.getLogger(__name__)
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the lazy-loaded instance."""
        return getattr(self._get_instance(), name)
    
    def __call__(self, *args, **kwargs) -> Any:
        """Delegate calls to the lazy-loaded instance."""
        return self._get_instance()(*args, **kwargs)
    
    def __repr__(self) -> str:
        """String representation."""
        status = "loaded" if self._instance is not None else "unloaded"
        return f"LazyProxy({self._name}, {status})"
    
    def _get_instance(self) -> T:
        """Get the actual instance, loading if necessary."""
        if self._instance is None:
            with self._lock:
                if self._instance is None:  # Double-check locking
                    start_time = time.time()
                    try:
                        self._logger.debug(f"Loading lazy object: {self._name}")
                        self._instance = self._factory()
                        self._load_time = time.time() - start_time
                        self._logger.debug(f"Loaded {self._name} in {self._load_time:.3f}s")
                        
                        # Update global stats
                        lazy_service = get_lazy_service()
                        lazy_service._stats.update_load_time(self._load_time)
                        
                    except Exception as e:
                        self._logger.error(f"Failed to load {self._name}: {e}")
                        raise
        
        return self._instance
    
    @property
    def is_loaded(self) -> bool:
        """Check if the instance is loaded."""
        return self._instance is not None
    
    @property
    def load_time(self) -> Optional[float]:
        """Get load time in seconds."""
        return self._load_time
    
    def force_load(self) -> T:
        """Force loading of the instance."""
        return self._get_instance()
    
    def unload(self) -> None:
        """Unload the instance (for memory management)."""
        with self._lock:
            if self._instance is not None:
                self._logger.debug(f"Unloading lazy object: {self._name}")
                # Try to cleanup if the instance has a cleanup method
                if hasattr(self._instance, 'cleanup'):
                    try:
                        self._instance.cleanup()
                    except Exception as e:
                        self._logger.warning(f"Error during cleanup of {self._name}: {e}")
                
                self._instance = None
                self._load_time = None


class LazyContainer:
    """Container for lazy-loaded objects with dependency management."""
    
    def __init__(self, name: str = ""):
        """
        Initialize lazy container.
        
        Args:
            name: Container name for debugging
        """
        self._name = name or f"LazyContainer_{id(self)}"
        self._objects: Dict[str, LazyProxy] = {}
        self._dependencies: Dict[str, list] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
    
    def register(self, name: str, factory: Callable[[], Any], 
                dependencies: Optional[list] = None) -> LazyProxy:
        """Register a lazy object.
        
        Args:
            name: Object name
            factory: Factory function
            dependencies: List of dependency names
            
        Returns:
            Lazy proxy for the object
        """
        with self._lock:
            if name in self._objects:
                raise ValueError(f"Object '{name}' already registered")
            
            # Create enhanced factory that resolves dependencies
            def enhanced_factory():
                # Load dependencies first
                if dependencies:
                    for dep_name in dependencies:
                        if dep_name in self._objects:
                            self._objects[dep_name].force_load()
                        else:
                            self._logger.warning(f"Dependency '{dep_name}' not found for '{name}'")
                
                return factory()
            
            proxy = LazyProxy(enhanced_factory, f"{self._name}.{name}")
            self._objects[name] = proxy
            self._dependencies[name] = dependencies or []
            
            self._logger.debug(f"Registered lazy object: {name}")
            return proxy
    
    def get(self, name: str) -> Optional[LazyProxy]:
        """Get lazy object by name.
        
        Args:
            name: Object name
            
        Returns:
            Lazy proxy or None if not found
        """
        return self._objects.get(name)
    
    def get_loaded(self, name: str) -> Any:
        """Get loaded instance by name.
        
        Args:
            name: Object name
            
        Returns:
            Loaded instance
            
        Raises:
            KeyError: If object not found
        """
        if name not in self._objects:
            raise KeyError(f"Object '{name}' not found")
        
        return self._objects[name].force_load()
    
    def preload(self, names: Optional[list] = None) -> None:
        """Preload objects.
        
        Args:
            names: List of object names to preload (all if None)
        """
        with self._lock:
            objects_to_load = names or list(self._objects.keys())
            
            # Sort by dependency order
            sorted_objects = self._topological_sort(objects_to_load)
            
            for name in sorted_objects:
                if name in self._objects:
                    self._logger.debug(f"Preloading: {name}")
                    self._objects[name].force_load()
    
    def unload_all(self) -> None:
        """Unload all objects."""
        with self._lock:
            for proxy in self._objects.values():
                proxy.unload()
            self._logger.debug(f"Unloaded all objects in {self._name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get container statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total_objects = len(self._objects)
            loaded_objects = sum(1 for proxy in self._objects.values() if proxy.is_loaded)
            
            load_times = [proxy.load_time for proxy in self._objects.values() 
                         if proxy.load_time is not None]
            
            return {
                'container_name': self._name,
                'total_objects': total_objects,
                'loaded_objects': loaded_objects,
                'load_percentage': (loaded_objects / total_objects * 100) if total_objects > 0 else 0,
                'average_load_time': sum(load_times) / len(load_times) if load_times else 0,
                'total_load_time': sum(load_times),
                'object_names': list(self._objects.keys())
            }
    
    def _topological_sort(self, names: list) -> list:
        """Sort objects by dependency order.
        
        Args:
            names: List of object names
            
        Returns:
            Sorted list of names
        """
        # Simple topological sort
        visited = set()
        result = []
        
        def visit(name: str):
            if name in visited or name not in names:
                return
            
            visited.add(name)
            
            # Visit dependencies first
            for dep in self._dependencies.get(name, []):
                visit(dep)
            
            result.append(name)
        
        for name in names:
            visit(name)
        
        return result


class LazyService:
    """Service for managing lazy loading across the application."""
    
    def __init__(self):
        """Initialize lazy service."""
        self._containers: Dict[str, LazyContainer] = {}
        self._global_objects: Dict[str, LazyProxy] = {}
        self._stats = LazyLoadStats()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Create default containers
        self.services = self.create_container("services")
        self.widgets = self.create_container("widgets")
        self.managers = self.create_container("managers")
    
    def create_container(self, name: str) -> LazyContainer:
        """Create a new lazy container.
        
        Args:
            name: Container name
            
        Returns:
            Lazy container
        """
        with self._lock:
            if name in self._containers:
                raise ValueError(f"Container '{name}' already exists")
            
            container = LazyContainer(name)
            self._containers[name] = container
            self._logger.debug(f"Created lazy container: {name}")
            return container
    
    def get_container(self, name: str) -> Optional[LazyContainer]:
        """Get container by name.
        
        Args:
            name: Container name
            
        Returns:
            Lazy container or None if not found
        """
        return self._containers.get(name)
    
    def register_service(self, name: str, factory: Callable[[], Any],
                        dependencies: Optional[list] = None) -> LazyProxy:
        """Register a lazy service.
        
        Args:
            name: Service name
            factory: Factory function
            dependencies: List of dependency names
            
        Returns:
            Lazy proxy for the service
        """
        return self.services.register(name, factory, dependencies)
    
    def register_widget(self, name: str, factory: Callable[[], Any],
                       dependencies: Optional[list] = None) -> LazyProxy:
        """Register a lazy widget.
        
        Args:
            name: Widget name
            factory: Factory function
            dependencies: List of dependency names
            
        Returns:
            Lazy proxy for the widget
        """
        return self.widgets.register(name, factory, dependencies)
    
    def register_manager(self, name: str, factory: Callable[[], Any],
                        dependencies: Optional[list] = None) -> LazyProxy:
        """Register a lazy manager.
        
        Args:
            name: Manager name
            factory: Factory function
            dependencies: List of dependency names
            
        Returns:
            Lazy proxy for the manager
        """
        return self.managers.register(name, factory, dependencies)
    
    def get_service(self, name: str) -> Any:
        """Get loaded service instance.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
        """
        return self.services.get_loaded(name)
    
    def get_widget(self, name: str) -> Any:
        """Get loaded widget instance.
        
        Args:
            name: Widget name
            
        Returns:
            Widget instance
        """
        return self.widgets.get_loaded(name)
    
    def get_manager(self, name: str) -> Any:
        """Get loaded manager instance.
        
        Args:
            name: Manager name
            
        Returns:
            Manager instance
        """
        return self.managers.get_loaded(name)
    
    def preload_critical(self) -> None:
        """Preload critical services for better user experience."""
        critical_services = ['weather_service', 'cache_manager', 'theme_manager']
        
        for service_name in critical_services:
            service_proxy = self.services.get(service_name)
            if service_proxy:
                self._logger.debug(f"Preloading critical service: {service_name}")
                service_proxy.force_load()
    
    def cleanup_unused(self, max_idle_time: float = 3600) -> int:
        """Clean up unused lazy objects.
        
        Args:
            max_idle_time: Maximum idle time in seconds
            
        Returns:
            Number of objects cleaned up
        """
        cleaned_count = 0
        current_time = time.time()
        
        for container in self._containers.values():
            with container._lock:
                for name, proxy in list(container._objects.items()):
                    if (proxy.is_loaded and 
                        proxy.load_time and 
                        current_time - proxy.load_time > max_idle_time):
                        
                        # Check if object has been accessed recently
                        # This is a simple heuristic - in practice, you might want
                        # to track access times more precisely
                        proxy.unload()
                        cleaned_count += 1
                        self._logger.debug(f"Cleaned up unused object: {name}")
        
        return cleaned_count
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global lazy loading statistics.
        
        Returns:
            Dictionary with global statistics
        """
        container_stats = {}
        for name, container in self._containers.items():
            container_stats[name] = container.get_stats()
        
        return {
            'global_stats': {
                'total_objects': self._stats.total_objects,
                'loaded_objects': self._stats.loaded_objects,
                'total_load_time': self._stats.total_load_time,
                'average_load_time': self._stats.average_load_time,
                'cache_hits': self._stats.cache_hits,
                'cache_misses': self._stats.cache_misses
            },
            'containers': container_stats
        }


# Decorators for lazy loading
def lazy_property(func: Callable) -> property:
    """Decorator for lazy properties.
    
    Args:
        func: Property getter function
        
    Returns:
        Lazy property
    """
    attr_name = f'_lazy_{func.__name__}'
    
    @wraps(func)
    def getter(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    
    return property(getter)


def lazy_init(dependencies: Optional[list] = None):
    """Decorator for lazy initialization.
    
    Args:
        dependencies: List of dependency names
        
    Returns:
        Decorator function
    """
    def decorator(cls: Type[T]) -> Type[T]:
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            # Store initialization parameters
            self._lazy_init_args = args
            self._lazy_init_kwargs = kwargs
            self._lazy_initialized = False
            self._lazy_lock = threading.RLock()
            
            # Load dependencies if specified
            if dependencies:
                lazy_service = get_lazy_service()
                for dep_name in dependencies:
                    try:
                        lazy_service.get_service(dep_name)
                    except KeyError:
                        pass  # Dependency not found, continue
        
        def ensure_initialized(self):
            if not self._lazy_initialized:
                with self._lazy_lock:
                    if not self._lazy_initialized:
                        original_init(self, *self._lazy_init_args, **self._lazy_init_kwargs)
                        self._lazy_initialized = True
        
        # Wrap all methods to ensure initialization
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if callable(attr) and not attr_name.startswith('_'):
                def make_wrapper(method):
                    @wraps(method)
                    def wrapper(self, *args, **kwargs):
                        ensure_initialized(self)
                        return method(self, *args, **kwargs)
                    return wrapper
                
                setattr(cls, attr_name, make_wrapper(attr))
        
        cls.__init__ = new_init
        cls._ensure_initialized = ensure_initialized
        
        return cls
    
    return decorator


# Global lazy service instance
_global_lazy_service = None


def get_lazy_service() -> LazyService:
    """Get global lazy service instance."""
    global _global_lazy_service
    if _global_lazy_service is None:
        _global_lazy_service = LazyService()
    return _global_lazy_service


def lazy(factory: Callable[[], T], name: str = "") -> LazyProxy[T]:
    """Create a lazy proxy for an object.
    
    Args:
        factory: Factory function to create the object
        name: Optional name for debugging
        
    Returns:
        Lazy proxy
    """
    return LazyProxy(factory, name)