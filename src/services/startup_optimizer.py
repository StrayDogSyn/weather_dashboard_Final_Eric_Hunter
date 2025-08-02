"""Startup Optimization Module.

Provides lazy loading, progressive enhancement, and startup performance optimizations
for the weather dashboard application.
"""

import asyncio
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
import weakref


class ComponentPriority(Enum):
    """Component loading priorities."""
    CRITICAL = 0      # Must load immediately (UI skeleton, core weather)
    HIGH = 1          # Load within 500ms (current weather, basic controls)
    MEDIUM = 2        # Load within 1s (forecast, charts)
    LOW = 3           # Load within 2s (ML panel, advanced features)
    DEFERRED = 4      # Load on demand (maps, settings)


@dataclass
class ComponentConfig:
    """Configuration for a lazy-loaded component."""
    name: str
    priority: ComponentPriority
    loader: Callable[[], Any]
    dependencies: List[str] = None
    cache_key: Optional[str] = None
    preload_data: bool = False
    skeleton_ui: Optional[Callable[[], Any]] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class StartupOptimizer:
    """Manages startup optimization and progressive loading."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize startup optimizer.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Component management
        self.components: Dict[str, ComponentConfig] = {}
        self.loaded_components: Set[str] = set()
        self.loading_components: Set[str] = set()
        self.component_instances: Dict[str, Any] = {}
        
        # Performance tracking
        self.start_time = time.time()
        self.load_times: Dict[str, float] = {}
        self.skeleton_shown_time: Optional[float] = None
        self.interactive_time: Optional[float] = None
        
        # Callbacks
        self.progress_callbacks: List[Callable[[str, float], None]] = []
        self.completion_callbacks: List[Callable[[str, Any], None]] = []
        
        # Cache integration
        self.cache_manager = None
        
        # Shutdown flag
        self._shutdown = False
    
    def set_cache_manager(self, cache_manager) -> None:
        """Set cache manager for data preloading."""
        self.cache_manager = cache_manager
    
    def register_component(self, config: ComponentConfig) -> None:
        """Register a component for lazy loading.
        
        Args:
            config: Component configuration
        """
        self.components[config.name] = config
        self.logger.debug(f"Registered component: {config.name} (priority: {config.priority.name})")
    
    def register_progress_callback(self, callback: Callable[[str, float], None]) -> None:
        """Register a progress callback.
        
        Args:
            callback: Function to call with (component_name, progress)
        """
        self.progress_callbacks.append(callback)
    
    def register_completion_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Register a completion callback.
        
        Args:
            callback: Function to call with (component_name, instance)
        """
        self.completion_callbacks.append(callback)
    
    async def start_progressive_loading(self) -> None:
        """Start progressive loading of components."""
        self.logger.info("🚀 Starting progressive loading...")
        self.start_time = time.time()
        
        # Load components by priority
        for priority in ComponentPriority:
            await self._load_priority_group(priority)
            
            # Mark interactive time after HIGH priority components
            if priority == ComponentPriority.HIGH and self.interactive_time is None:
                self.interactive_time = time.time() - self.start_time
                self.logger.info(f"⚡ Interactive in {self.interactive_time:.2f}s")
    
    async def _load_priority_group(self, priority: ComponentPriority) -> None:
        """Load all components of a given priority.
        
        Args:
            priority: Priority level to load
        """
        components_to_load = [
            config for config in self.components.values()
            if config.priority == priority and config.name not in self.loaded_components
        ]
        
        if not components_to_load:
            return
        
        self.logger.info(f"📦 Loading {priority.name} priority components ({len(components_to_load)} items)")
        
        # Show skeleton UI for critical components
        if priority == ComponentPriority.CRITICAL:
            await self._show_skeleton_ui(components_to_load)
        
        # Load components concurrently within priority group
        tasks = []
        for config in components_to_load:
            if self._can_load_component(config):
                task = asyncio.create_task(self._load_component(config))
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _show_skeleton_ui(self, components: List[ComponentConfig]) -> None:
        """Show skeleton UI for components.
        
        Args:
            components: Components to show skeleton for
        """
        for config in components:
            if config.skeleton_ui:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor, config.skeleton_ui
                    )
                except Exception as e:
                    self.logger.error(f"Failed to show skeleton for {config.name}: {e}")
        
        if self.skeleton_shown_time is None:
            self.skeleton_shown_time = time.time() - self.start_time
            self.logger.info(f"💀 Skeleton UI shown in {self.skeleton_shown_time:.2f}s")
    
    def _can_load_component(self, config: ComponentConfig) -> bool:
        """Check if component dependencies are satisfied.
        
        Args:
            config: Component configuration
            
        Returns:
            bool: True if component can be loaded
        """
        if config.name in self.loading_components or config.name in self.loaded_components:
            return False
        
        # Check dependencies
        for dep in config.dependencies:
            if dep not in self.loaded_components:
                return False
        
        return True
    
    async def _load_component(self, config: ComponentConfig) -> Optional[Any]:
        """Load a single component.
        
        Args:
            config: Component configuration
            
        Returns:
            Optional[Any]: Loaded component instance
        """
        if self._shutdown:
            return None
        
        component_name = config.name
        self.loading_components.add(component_name)
        
        try:
            start_time = time.time()
            
            # Try to load from cache first
            instance = None
            if config.cache_key and self.cache_manager:
                instance = self.cache_manager.get(config.cache_key)
                if instance:
                    self.logger.debug(f"📋 Loaded {component_name} from cache")
            
            # Load component if not cached
            if instance is None:
                self._report_progress(component_name, 0.1)
                
                # Preload data if needed
                if config.preload_data and self.cache_manager:
                    await self._preload_component_data(config)
                
                self._report_progress(component_name, 0.3)
                
                # Load the actual component
                instance = await asyncio.get_event_loop().run_in_executor(
                    self.executor, config.loader
                )
                
                self._report_progress(component_name, 0.8)
                
                # Cache the instance if configured
                if config.cache_key and self.cache_manager and instance:
                    self.cache_manager.set(
                        config.cache_key, 
                        instance, 
                        ttl=3600,  # 1 hour
                        tags=['component', 'startup']
                    )
            
            # Store instance and mark as loaded
            if instance:
                self.component_instances[component_name] = instance
                self.loaded_components.add(component_name)
                
                load_time = time.time() - start_time
                self.load_times[component_name] = load_time
                
                self._report_progress(component_name, 1.0)
                self._report_completion(component_name, instance)
                
                self.logger.info(f"✅ Loaded {component_name} in {load_time:.2f}s")
                
                return instance
            else:
                self.logger.warning(f"⚠️ Failed to load {component_name}: No instance returned")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to load {component_name}: {e}")
        finally:
            self.loading_components.discard(component_name)
        
        return None
    
    async def _preload_component_data(self, config: ComponentConfig) -> None:
        """Preload data for a component.
        
        Args:
            config: Component configuration
        """
        try:
            # This would be customized based on component needs
            # For now, just a placeholder
            await asyncio.sleep(0.01)  # Simulate data loading
        except Exception as e:
            self.logger.error(f"Failed to preload data for {config.name}: {e}")
    
    def _report_progress(self, component_name: str, progress: float) -> None:
        """Report loading progress.
        
        Args:
            component_name: Name of component
            progress: Progress value (0.0 to 1.0)
        """
        for callback in self.progress_callbacks:
            try:
                callback(component_name, progress)
            except Exception as e:
                self.logger.error(f"Progress callback error: {e}")
    
    def _report_completion(self, component_name: str, instance: Any) -> None:
        """Report component completion.
        
        Args:
            component_name: Name of component
            instance: Loaded component instance
        """
        for callback in self.completion_callbacks:
            try:
                callback(component_name, instance)
            except Exception as e:
                self.logger.error(f"Completion callback error: {e}")
    
    def get_component(self, name: str) -> Optional[Any]:
        """Get a loaded component instance.
        
        Args:
            name: Component name
            
        Returns:
            Optional[Any]: Component instance if loaded
        """
        return self.component_instances.get(name)
    
    async def load_component_on_demand(self, name: str) -> Optional[Any]:
        """Load a component on demand.
        
        Args:
            name: Component name
            
        Returns:
            Optional[Any]: Loaded component instance
        """
        if name in self.loaded_components:
            return self.component_instances.get(name)
        
        config = self.components.get(name)
        if not config:
            self.logger.error(f"Unknown component: {name}")
            return None
        
        return await self._load_component(config)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics.
        
        Returns:
            Dict[str, Any]: Performance data
        """
        current_time = time.time() - self.start_time
        
        return {
            'total_time': current_time,
            'skeleton_time': self.skeleton_shown_time,
            'interactive_time': self.interactive_time,
            'loaded_components': len(self.loaded_components),
            'total_components': len(self.components),
            'load_times': self.load_times.copy(),
            'average_load_time': sum(self.load_times.values()) / len(self.load_times) if self.load_times else 0,
            'target_met': (self.interactive_time or current_time) < 2.0
        }
    
    def shutdown(self) -> None:
        """Shutdown the startup optimizer."""
        self.logger.info("🛑 Shutting down startup optimizer...")
        self._shutdown = True
        
        # Cancel any pending loads
        self.loading_components.clear()
        
        # Shutdown executor
        self.executor.shutdown(wait=False)
        
        # Clear callbacks
        self.progress_callbacks.clear()
        self.completion_callbacks.clear()
        
        self.logger.info("✅ Startup optimizer shutdown complete")