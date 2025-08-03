#!/usr/bin/env python3
"""
Startup Optimizer for Weather Dashboard
Implements lazy loading and progressive enhancement for optimal startup performance.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ComponentPriority(Enum):
    """Priority levels for component loading."""

    CRITICAL = 1  # Must load first (core services)
    HIGH = 2  # Important UI components
    MEDIUM = 3  # Secondary features
    LOW = 4  # Nice-to-have features
    BACKGROUND = 5  # Load in background


@dataclass
class ComponentConfig:
    """Configuration for a loadable component."""

    name: str
    priority: ComponentPriority
    loader_func: Callable[[], Any]
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 10.0
    retry_count: int = 2
    cache_result: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadResult:
    """Result of component loading."""

    component_name: str
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    load_time: float = 0.0
    from_cache: bool = False


class StartupOptimizer:
    """Manages progressive loading and startup optimization."""

    def __init__(self):
        """Initialize the startup optimizer."""
        self.components: Dict[str, ComponentConfig] = {}
        self.loaded_components: Dict[str, LoadResult] = {}
        self.loading_queue: List[str] = []
        self.is_loading = False

        self._cache: Dict[str, Any] = {}
        self._performance_stats = {
            "total_load_time": 0.0,
            "components_loaded": 0,
            "components_failed": 0,
            "cache_hits": 0,
            "parallel_loads": 0,
        }

        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

    def register_component(
        self,
        name: str,
        priority: ComponentPriority,
        loader_func: Callable[[], Any],
        dependencies: Optional[List[str]] = None,
        timeout: float = 10.0,
        retry_count: int = 2,
        cache_result: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a component for progressive loading."""
        config = ComponentConfig(
            name=name,
            priority=priority,
            loader_func=loader_func,
            dependencies=dependencies or [],
            timeout=timeout,
            retry_count=retry_count,
            cache_result=cache_result,
            metadata=metadata or {},
        )

        with self._lock:
            self.components[name] = config
            self.logger.debug(
                f"Registered component '{name}' with priority {priority.name}"
            )

    def start_progressive_loading(
        self,
        on_component_loaded: Optional[Callable[[str, bool], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        """Start progressive loading of all registered components."""
        if self.is_loading:
            self.logger.warning("Progressive loading already in progress")
            return

        self.is_loading = True
        start_time = time.time()

        def loading_worker():
            try:
                self._execute_progressive_loading(on_component_loaded)

                # Update performance stats
                self._performance_stats["total_load_time"] = (
                    time.time() - start_time
                )

                if on_complete:
                    on_complete()

            except Exception as e:
                self.logger.error(f"Progressive loading failed: {e}")
            finally:
                self.is_loading = False

        # Start loading in background thread
        loading_thread = threading.Thread(target=loading_worker, daemon=True)
        loading_thread.start()

    def _execute_progressive_loading(
        self, on_component_loaded: Optional[Callable[[str, bool], None]] = None
    ) -> None:
        """Execute the progressive loading process."""
        # Sort components by priority and dependencies
        load_order = self._calculate_load_order()

        self.logger.info(
            f"Starting progressive loading of {len(load_order)} components"
        )

        # Load components in priority order
        for priority_group in load_order:
            self._load_priority_group(priority_group, on_component_loaded)

    def _calculate_load_order(self) -> List[List[str]]:
        """Calculate the optimal loading order based on priorities and dependencies."""
        # Group by priority
        priority_groups = {}
        for name, config in self.components.items():
            priority = config.priority.value
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(name)

        # Sort each group by dependencies
        ordered_groups = []
        for priority in sorted(priority_groups.keys()):
            group = priority_groups[priority]
            ordered_group = self._resolve_dependencies(group)
            ordered_groups.append(ordered_group)

        return ordered_groups

    def _resolve_dependencies(self, component_names: List[str]) -> List[str]:
        """Resolve dependencies within a priority group."""
        resolved = []
        remaining = component_names.copy()
        max_iterations = len(component_names) * 2  # Prevent infinite loops
        iteration = 0

        while remaining and iteration < max_iterations:
            iteration += 1
            # Find components with no unresolved dependencies
            ready = []
            for name in remaining:
                config = self.components[name]
                deps_satisfied = all(
                    dep in self.loaded_components
                    or dep in resolved
                    or dep not in self.components
                    for dep in config.dependencies
                )
                if deps_satisfied:
                    ready.append(name)

            if not ready:
                # Check if dependencies are in other priority groups that should be loaded first
                unmet_deps = set()
                for name in remaining:
                    config = self.components[name]
                    for dep in config.dependencies:
                        if (
                            dep not in self.loaded_components
                            and dep not in resolved
                            and dep in self.components
                        ):
                            dep_priority = self.components[dep].priority.value
                            current_priority = config.priority.value
                            if dep_priority <= current_priority:
                                unmet_deps.add(dep)

                if unmet_deps:
                    self.logger.debug(
                        f"Dependencies {list(unmet_deps)} will be loaded in "
                        f"earlier priority groups"
                    )
                    # Load remaining components anyway since dependencies will be satisfied later
                    ready = remaining
                else:
                    # True circular dependency within same priority
                    self.logger.warning(
                        f"Circular dependencies detected within priority group: "
                        f"{remaining}"
                    )
                    ready = remaining  # Load anyway

            resolved.extend(ready)
            for name in ready:
                remaining.remove(name)

        return resolved

    def _load_priority_group(
        self,
        component_names: List[str],
        on_component_loaded: Optional[Callable[[str, bool], None]] = None,
    ) -> None:
        """Load a group of components with the same priority."""
        if not component_names:
            return

        # For critical and high priority, load sequentially
        # For medium and below, load in parallel
        first_component = self.components[component_names[0]]

        if first_component.priority in [
            ComponentPriority.CRITICAL,
            ComponentPriority.HIGH,
        ]:
            self._load_sequential(component_names, on_component_loaded)
        else:
            self._load_parallel(component_names, on_component_loaded)

    def _load_sequential(
        self,
        component_names: List[str],
        on_component_loaded: Optional[Callable[[str, bool], None]] = None,
    ) -> None:
        """Load components sequentially."""
        for name in component_names:
            result = self._load_component(name)

            if on_component_loaded:
                on_component_loaded(name, result.success)

    def _load_parallel(
        self,
        component_names: List[str],
        on_component_loaded: Optional[Callable[[str, bool], None]] = None,
    ) -> None:
        """Load components in parallel."""
        threads = []
        results = {}

        def load_worker(name):
            results[name] = self._load_component(name)

        # Start all loading threads
        for name in component_names:
            thread = threading.Thread(target=load_worker, args=(name,), daemon=True)
            thread.start()
            threads.append(thread)

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Notify completion
        if on_component_loaded:
            for name in component_names:
                result = results.get(name)
                if result:
                    on_component_loaded(name, result.success)

        self._performance_stats["parallel_loads"] += len(component_names)

    def _load_component(self, name: str) -> LoadResult:
        """Load a single component with caching and error handling."""
        config = self.components[name]
        start_time = time.time()

        # Check cache first
        if config.cache_result and name in self._cache:
            self.logger.debug(f"Loading '{name}' from cache")
            result = LoadResult(
                component_name=name,
                success=True,
                result=self._cache[name],
                load_time=0.0,
                from_cache=True,
            )
            self.loaded_components[name] = result
            self._performance_stats["cache_hits"] += 1
            return result

        # Load component with retries
        last_error = None
        for attempt in range(config.retry_count + 1):
            try:
                self.logger.debug(f"Loading component '{name}' (attempt {attempt + 1})")

                # Execute loader with timeout
                component_result = self._execute_with_timeout(config.loader_func, config.timeout)

                # Cache result if successful
                if config.cache_result:
                    self._cache[name] = component_result

                load_time = time.time() - start_time
                result = LoadResult(
                    component_name=name, success=True, result=component_result, load_time=load_time
                )

                self.loaded_components[name] = result
                self._performance_stats["components_loaded"] += 1

                self.logger.info(f"✓ Component '{name}' loaded successfully in {load_time:.2f}s")
                return result

            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Failed to load component '{name}' (attempt {attempt + 1}): {e}"
                )

                if attempt < config.retry_count:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff

        # All attempts failed
        load_time = time.time() - start_time
        result = LoadResult(
            component_name=name, success=False, error=last_error, load_time=load_time
        )

        self.loaded_components[name] = result
        self._performance_stats["components_failed"] += 1

        self.logger.error(
            f"✗ Component '{name}' failed to load after "
            f"{config.retry_count + 1} attempts"
        )
        return result

    def _execute_with_timeout(self, func: Callable[[], Any], timeout: float) -> Any:
        """Execute a function with timeout."""
        result = [None]
        exception = [None]

        def worker():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            raise TimeoutError(f"Component loading timed out after {timeout}s")

        if exception[0]:
            raise exception[0]

        return result[0]

    def get_component_result(self, name: str) -> Optional[Any]:
        """Get the result of a loaded component."""
        if name in self.loaded_components:
            result = self.loaded_components[name]
            return result.result if result.success else None
        return None

    def is_component_loaded(self, name: str) -> bool:
        """Check if a component has been successfully loaded."""
        return name in self.loaded_components and self.loaded_components[name].success

    def get_loading_status(self) -> Dict[str, Any]:
        """Get current loading status."""
        total_components = len(self.components)
        loaded_count = len([r for r in self.loaded_components.values() if r.success])
        failed_count = len([r for r in self.loaded_components.values() if not r.success])

        return {
            "is_loading": self.is_loading,
            "total_components": total_components,
            "loaded_count": loaded_count,
            "failed_count": failed_count,
            "progress_percent": (
                (loaded_count / total_components * 100) if total_components > 0 else 0
            ),
            "components": {
                name: {
                    "loaded": result.success,
                    "load_time": result.load_time,
                    "from_cache": result.from_cache,
                    "error": str(result.error) if result.error else None,
                }
                for name, result in self.loaded_components.items()
            },
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self._performance_stats.copy()

    def preload_component(self, name: str) -> bool:
        """Preload a specific component immediately."""
        if name not in self.components:
            self.logger.error(f"Component '{name}' not registered")
            return False

        if self.is_component_loaded(name):
            self.logger.debug(f"Component '{name}' already loaded")
            return True

        result = self._load_component(name)
        return result.success

    def invalidate_cache(self, component_name: Optional[str] = None) -> None:
        """Invalidate cached component results."""
        with self._lock:
            if component_name:
                self._cache.pop(component_name, None)
                self.loaded_components.pop(component_name, None)
                self.logger.debug(
                    f"Invalidated cache for component '{component_name}'"
                )
            else:
                self._cache.clear()
                self.loaded_components.clear()
                self.logger.debug("Invalidated all component cache")

    def shutdown(self) -> None:
        """Shutdown the optimizer and clean up resources."""
        self.is_loading = False
        self._cache.clear()
        self.loaded_components.clear()
        self.logger.info("Startup optimizer shutdown complete")
