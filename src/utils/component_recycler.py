#!/usr/bin/env python3
"""
Component Recycler for Weather Dashboard
Implements object pooling and component recycling for memory optimization.
"""

import time
import threading
import weakref
from typing import Any, Dict, List, Optional, Type, Callable
from dataclasses import dataclass
from collections import defaultdict
import logging
import gc

@dataclass
class ComponentStats:
    """Statistics for a component type."""
    created_count: int = 0
    recycled_count: int = 0
    active_count: int = 0
    peak_count: int = 0
    total_memory_saved: int = 0
    last_cleanup: float = 0.0

class ComponentPool:
    """Pool for a specific component type."""
    
    def __init__(self, component_type: Type, max_size: int = 50,
                 factory_func: Optional[Callable[[], Any]] = None,
                 reset_func: Optional[Callable[[Any], None]] = None,
                 cleanup_interval: float = 300.0):
        """Initialize component pool."""
        self.component_type = component_type
        self.max_size = max_size
        self.factory_func = factory_func or component_type
        self.reset_func = reset_func
        self.cleanup_interval = cleanup_interval
        
        self._pool: List[Any] = []
        self._active_components: List[Any] = []
        self._stats = ComponentStats()
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
        
        self.logger = logging.getLogger(f"{__name__}.{component_type.__name__}")
    
    def acquire(self) -> Any:
        """Acquire a component from the pool."""
        with self._lock:
            # Try to reuse from pool
            if self._pool:
                component = self._pool.pop()
                self._active_components.append(component)
                self._stats.recycled_count += 1
                self._stats.active_count += 1
                
                self.logger.debug(f"Recycled {self.component_type.__name__} from pool")
                return component
            
            # Create new component
            try:
                component = self.factory_func()
                self._active_components.append(component)
                self._stats.created_count += 1
                self._stats.active_count += 1
                
                if self._stats.active_count > self._stats.peak_count:
                    self._stats.peak_count = self._stats.active_count
                
                self.logger.debug(f"Created new {self.component_type.__name__}")
                return component
                
            except Exception as e:
                self.logger.error(f"Failed to create {self.component_type.__name__}: {e}")
                raise
    
    def release(self, component: Any) -> bool:
        """Release a component back to the pool."""
        if component not in self._active_components:
            self.logger.warning(f"Attempting to release unknown component {type(component).__name__}")
            return False
        
        with self._lock:
            if component in self._active_components:
                self._active_components.remove(component)
                self._stats.active_count -= 1
            
            # Reset component state if reset function provided
            if self.reset_func:
                try:
                    self.reset_func(component)
                except Exception as e:
                    self.logger.warning(f"Failed to reset component: {e}")
                    return False
            
            # Add to pool if not full
            if len(self._pool) < self.max_size:
                self._pool.append(component)
                self.logger.debug(f"Released {self.component_type.__name__} to pool")
                return True
            else:
                # Pool is full, let component be garbage collected
                self.logger.debug(f"Pool full, discarding {self.component_type.__name__}")
                return False
    
    def cleanup(self, force: bool = False) -> int:
        """Clean up unused components from pool."""
        current_time = time.time()
        
        if not force and (current_time - self._last_cleanup) < self.cleanup_interval:
            return 0
        
        with self._lock:
            initial_size = len(self._pool)
            
            # Keep only half the components during cleanup
            keep_count = max(1, len(self._pool) // 2)
            self._pool = self._pool[:keep_count]
            
            cleaned_count = initial_size - len(self._pool)
            self._last_cleanup = current_time
            
            if cleaned_count > 0:
                self.logger.debug(f"Cleaned up {cleaned_count} {self.component_type.__name__} components")
            
            return cleaned_count
    
    def get_stats(self) -> ComponentStats:
        """Get pool statistics."""
        with self._lock:
            stats = ComponentStats(
                created_count=self._stats.created_count,
                recycled_count=self._stats.recycled_count,
                active_count=self._stats.active_count,
                peak_count=self._stats.peak_count,
                total_memory_saved=self._stats.total_memory_saved,
                last_cleanup=self._last_cleanup
            )
            return stats
    
    def clear(self) -> int:
        """Clear all components from pool."""
        with self._lock:
            cleared_count = len(self._pool)
            self._pool.clear()
            self.logger.debug(f"Cleared {cleared_count} {self.component_type.__name__} components")
            return cleared_count

class ComponentRecycler:
    """Main component recycling manager."""
    
    def __init__(self, global_cleanup_interval: float = 600.0):
        """Initialize the component recycler."""
        self._pools: Dict[Type, ComponentPool] = {}
        self._global_cleanup_interval = global_cleanup_interval
        self._last_global_cleanup = time.time()
        self._lock = threading.Lock()
        
        self.logger = logging.getLogger(__name__)
        
        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        self._cleanup_thread.start()
        
        # Track memory usage
        self._memory_tracker = MemoryTracker()
    
    def register_component_type(self, component_type: Type, max_pool_size: int = 50,
                               factory_func: Optional[Callable[[], Any]] = None,
                               reset_func: Optional[Callable[[Any], None]] = None,
                               cleanup_interval: float = 300.0) -> None:
        """Register a component type for recycling."""
        with self._lock:
            if component_type in self._pools:
                self.logger.warning(f"Component type {component_type.__name__} already registered")
                return
            
            pool = ComponentPool(
                component_type=component_type,
                max_size=max_pool_size,
                factory_func=factory_func,
                reset_func=reset_func,
                cleanup_interval=cleanup_interval
            )
            
            self._pools[component_type] = pool
            self.logger.info(f"Registered component type {component_type.__name__} for recycling")
    
    def acquire_component(self, component_type: Type) -> Any:
        """Acquire a component of the specified type."""
        if component_type not in self._pools:
            raise ValueError(f"Component type {component_type.__name__} not registered")
        
        component = self._pools[component_type].acquire()
        self._memory_tracker.track_acquisition(component_type)
        return component
    
    def release_component(self, component: Any) -> bool:
        """Release a component back to its pool."""
        component_type = type(component)
        
        if component_type not in self._pools:
            self.logger.warning(f"No pool found for component type {component_type.__name__}")
            return False
        
        success = self._pools[component_type].release(component)
        if success:
            self._memory_tracker.track_release(component_type)
        
        return success
    
    def get_component_stats(self, component_type: Optional[Type] = None) -> Dict[str, ComponentStats]:
        """Get statistics for component pools."""
        if component_type:
            if component_type in self._pools:
                return {component_type.__name__: self._pools[component_type].get_stats()}
            else:
                return {}
        
        return {
            pool_type.__name__: pool.get_stats()
            for pool_type, pool in self._pools.items()
        }
    
    def cleanup_pools(self, force: bool = False) -> Dict[str, int]:
        """Clean up all component pools."""
        cleanup_results = {}
        
        for component_type, pool in self._pools.items():
            cleaned = pool.cleanup(force)
            if cleaned > 0:
                cleanup_results[component_type.__name__] = cleaned
        
        if cleanup_results:
            self.logger.info(f"Pool cleanup completed: {cleanup_results}")
        
        return cleanup_results
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return self._memory_tracker.get_stats()
    
    def _background_cleanup(self) -> None:
        """Background thread for periodic cleanup."""
        while True:
            try:
                time.sleep(60)  # Check every minute
                
                current_time = time.time()
                if (current_time - self._last_global_cleanup) >= self._global_cleanup_interval:
                    self.cleanup_pools()
                    self._last_global_cleanup = current_time
                    
                    # Force garbage collection
                    gc.collect()
                    
            except Exception as e:
                self.logger.error(f"Background cleanup error: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the recycler and clean up all pools."""
        self.logger.info("Shutting down component recycler")
        
        # Clear all pools
        total_cleared = 0
        for component_type, pool in self._pools.items():
            cleared = pool.clear()
            total_cleared += cleared
        
        self.logger.info(f"Component recycler shutdown complete. Cleared {total_cleared} components.")

class MemoryTracker:
    """Tracks memory usage for component recycling."""
    
    def __init__(self):
        """Initialize memory tracker."""
        self._acquisitions: Dict[Type, int] = defaultdict(int)
        self._releases: Dict[Type, int] = defaultdict(int)
        self._peak_usage: Dict[Type, int] = defaultdict(int)
        self._current_usage: Dict[Type, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def track_acquisition(self, component_type: Type) -> None:
        """Track component acquisition."""
        with self._lock:
            self._acquisitions[component_type] += 1
            self._current_usage[component_type] += 1
            
            if self._current_usage[component_type] > self._peak_usage[component_type]:
                self._peak_usage[component_type] = self._current_usage[component_type]
    
    def track_release(self, component_type: Type) -> None:
        """Track component release."""
        with self._lock:
            self._releases[component_type] += 1
            self._current_usage[component_type] = max(0, self._current_usage[component_type] - 1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory tracking statistics."""
        with self._lock:
            return {
                'acquisitions': dict(self._acquisitions),
                'releases': dict(self._releases),
                'current_usage': dict(self._current_usage),
                'peak_usage': dict(self._peak_usage),
                'total_acquisitions': sum(self._acquisitions.values()),
                'total_releases': sum(self._releases.values()),
                'current_total': sum(self._current_usage.values()),
                'peak_total': sum(self._peak_usage.values())
            }

# Common reset functions for UI components
def reset_tkinter_widget(widget):
    """Reset function for Tkinter widgets."""
    try:
        # Clear text widgets
        if hasattr(widget, 'delete') and hasattr(widget, 'insert'):
            widget.delete(0, 'end')
        
        # Reset state
        if hasattr(widget, 'state'):
            widget.state(['!disabled', '!selected'])
        
        # Clear variables
        if hasattr(widget, 'set'):
            widget.set('')
            
    except Exception:
        pass  # Ignore reset errors

def reset_frame_widget(frame):
    """Reset function for Frame widgets."""
    try:
        # Clear all child widgets
        for child in frame.winfo_children():
            child.destroy()
    except Exception:
        pass  # Ignore reset errors