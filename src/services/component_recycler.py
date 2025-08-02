"""Component Recycling System.

Provides memory-efficient component recycling for UI elements like forecast cards,
chart widgets, and other reusable components to prevent memory leaks and improve performance.
"""

import gc
import logging
import threading
import time
import weakref
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union
import tkinter as tk
from tkinter import ttk


T = TypeVar('T')


class ComponentType(Enum):
    """Types of recyclable components."""
    FORECAST_CARD = "forecast_card"
    CHART_WIDGET = "chart_widget"
    MAP_MARKER = "map_marker"
    DATA_PANEL = "data_panel"
    PROGRESS_BAR = "progress_bar"
    CUSTOM = "custom"


@dataclass
class ComponentPool:
    """Pool configuration for a component type."""
    component_type: ComponentType
    factory: Callable[[], Any]
    reset_func: Optional[Callable[[Any], None]] = None
    max_size: int = 50
    cleanup_func: Optional[Callable[[Any], None]] = None
    ttl_seconds: float = 300.0  # 5 minutes


@dataclass
class PooledComponent:
    """Wrapper for a pooled component."""
    instance: Any
    created_at: float
    last_used: float
    use_count: int = 0
    in_use: bool = False
    
    def mark_used(self) -> None:
        """Mark component as used."""
        self.last_used = time.time()
        self.use_count += 1
        self.in_use = True
    
    def mark_returned(self) -> None:
        """Mark component as returned to pool."""
        self.in_use = False
    
    def is_expired(self, ttl: float) -> bool:
        """Check if component has expired.
        
        Args:
            ttl: Time to live in seconds
            
        Returns:
            bool: True if expired
        """
        return time.time() - self.last_used > ttl


class ComponentRecycler:
    """Manages component recycling and memory optimization."""
    
    def __init__(self, cleanup_interval: float = 60.0):
        """Initialize component recycler.
        
        Args:
            cleanup_interval: Interval between cleanup cycles in seconds
        """
        self.logger = logging.getLogger(__name__)
        self.cleanup_interval = cleanup_interval
        
        # Component pools
        self.pools: Dict[ComponentType, ComponentPool] = {}
        self.available: Dict[ComponentType, deque] = defaultdict(deque)
        self.in_use: Dict[ComponentType, Set[PooledComponent]] = defaultdict(set)
        
        # Memory tracking
        self.total_created: Dict[ComponentType, int] = defaultdict(int)
        self.total_recycled: Dict[ComponentType, int] = defaultdict(int)
        self.peak_usage: Dict[ComponentType, int] = defaultdict(int)
        
        # Cleanup management
        self.cleanup_timer: Optional[threading.Timer] = None
        self.cleanup_lock = threading.RLock()
        self._shutdown = False
        
        # Weak references for automatic cleanup
        self.weak_refs: Set[weakref.ref] = set()
        
        # Start cleanup timer
        self._start_cleanup_timer()
    
    def register_pool(self, pool_config: ComponentPool) -> None:
        """Register a component pool.
        
        Args:
            pool_config: Pool configuration
        """
        self.pools[pool_config.component_type] = pool_config
        self.logger.info(f"📦 Registered pool for {pool_config.component_type.value} (max: {pool_config.max_size})")
    
    def get_component(self, component_type: ComponentType, **kwargs) -> Optional[Any]:
        """Get a component from the pool.
        
        Args:
            component_type: Type of component to get
            **kwargs: Additional arguments for component creation
            
        Returns:
            Optional[Any]: Component instance
        """
        if self._shutdown:
            return None
        
        pool_config = self.pools.get(component_type)
        if not pool_config:
            self.logger.error(f"No pool registered for {component_type.value}")
            return None
        
        with self.cleanup_lock:
            # Try to get from available pool
            available_queue = self.available[component_type]
            
            while available_queue:
                pooled_comp = available_queue.popleft()
                
                # Check if component is still valid
                if not pooled_comp.is_expired(pool_config.ttl_seconds):
                    # Reset component if needed
                    if pool_config.reset_func:
                        try:
                            pool_config.reset_func(pooled_comp.instance)
                        except Exception as e:
                            self.logger.error(f"Failed to reset {component_type.value}: {e}")
                            self._cleanup_component(pooled_comp, pool_config)
                            continue
                    
                    # Mark as in use
                    pooled_comp.mark_used()
                    self.in_use[component_type].add(pooled_comp)
                    self.total_recycled[component_type] += 1
                    
                    self.logger.debug(f"♻️ Recycled {component_type.value} (use count: {pooled_comp.use_count})")
                    return pooled_comp.instance
                else:
                    # Component expired, clean it up
                    self._cleanup_component(pooled_comp, pool_config)
            
            # No available components, create new one
            return self._create_new_component(component_type, pool_config, **kwargs)
    
    def _create_new_component(self, component_type: ComponentType, 
                            pool_config: ComponentPool, **kwargs) -> Optional[Any]:
        """Create a new component.
        
        Args:
            component_type: Type of component
            pool_config: Pool configuration
            **kwargs: Additional arguments
            
        Returns:
            Optional[Any]: New component instance
        """
        try:
            # Create new instance
            instance = pool_config.factory(**kwargs)
            
            # Create pooled wrapper
            pooled_comp = PooledComponent(
                instance=instance,
                created_at=time.time(),
                last_used=time.time()
            )
            pooled_comp.mark_used()
            
            # Track usage
            self.in_use[component_type].add(pooled_comp)
            self.total_created[component_type] += 1
            
            # Update peak usage
            current_usage = len(self.in_use[component_type])
            if current_usage > self.peak_usage[component_type]:
                self.peak_usage[component_type] = current_usage
            
            # Add weak reference for automatic cleanup
            weak_ref = weakref.ref(instance, self._on_component_deleted)
            self.weak_refs.add(weak_ref)
            
            self.logger.debug(f"🆕 Created new {component_type.value} (total: {self.total_created[component_type]})")
            return instance
            
        except Exception as e:
            self.logger.error(f"Failed to create {component_type.value}: {e}")
            return None
    
    def return_component(self, component_type: ComponentType, instance: Any) -> None:
        """Return a component to the pool.
        
        Args:
            component_type: Type of component
            instance: Component instance to return
        """
        if self._shutdown:
            return
        
        pool_config = self.pools.get(component_type)
        if not pool_config:
            return
        
        with self.cleanup_lock:
            # Find the pooled component
            pooled_comp = None
            for comp in self.in_use[component_type]:
                if comp.instance is instance:
                    pooled_comp = comp
                    break
            
            if not pooled_comp:
                self.logger.warning(f"Attempted to return unknown {component_type.value}")
                return
            
            # Remove from in-use set
            self.in_use[component_type].discard(pooled_comp)
            pooled_comp.mark_returned()
            
            # Check pool size limit
            available_queue = self.available[component_type]
            if len(available_queue) >= pool_config.max_size:
                # Pool is full, cleanup oldest component
                if available_queue:
                    oldest = available_queue.popleft()
                    self._cleanup_component(oldest, pool_config)
            
            # Add to available pool
            available_queue.append(pooled_comp)
            
            self.logger.debug(f"🔄 Returned {component_type.value} to pool (available: {len(available_queue)})")
    
    def _cleanup_component(self, pooled_comp: PooledComponent, pool_config: ComponentPool) -> None:
        """Clean up a component.
        
        Args:
            pooled_comp: Pooled component to clean up
            pool_config: Pool configuration
        """
        try:
            if pool_config.cleanup_func:
                pool_config.cleanup_func(pooled_comp.instance)
            
            # Handle matplotlib figures specifically
            if hasattr(pooled_comp.instance, 'figure'):
                import matplotlib.pyplot as plt
                plt.close(pooled_comp.instance.figure)
            
            # Handle tkinter widgets
            if isinstance(pooled_comp.instance, (tk.Widget, ttk.Widget)):
                try:
                    pooled_comp.instance.destroy()
                except tk.TclError:
                    pass  # Widget already destroyed
            
        except Exception as e:
            self.logger.error(f"Error cleaning up component: {e}")
    
    def _on_component_deleted(self, weak_ref: weakref.ref) -> None:
        """Handle component deletion via weak reference.
        
        Args:
            weak_ref: Weak reference to deleted component
        """
        self.weak_refs.discard(weak_ref)
    
    def _start_cleanup_timer(self) -> None:
        """Start the cleanup timer."""
        if not self._shutdown:
            self.cleanup_timer = threading.Timer(self.cleanup_interval, self._cleanup_expired)
            self.cleanup_timer.daemon = True
            self.cleanup_timer.start()
    
    def _cleanup_expired(self) -> None:
        """Clean up expired components."""
        if self._shutdown:
            return
        
        try:
            with self.cleanup_lock:
                total_cleaned = 0
                
                for component_type, pool_config in self.pools.items():
                    available_queue = self.available[component_type]
                    cleaned_count = 0
                    
                    # Clean expired components from available pool
                    new_queue = deque()
                    while available_queue:
                        pooled_comp = available_queue.popleft()
                        if pooled_comp.is_expired(pool_config.ttl_seconds):
                            self._cleanup_component(pooled_comp, pool_config)
                            cleaned_count += 1
                        else:
                            new_queue.append(pooled_comp)
                    
                    self.available[component_type] = new_queue
                    total_cleaned += cleaned_count
                    
                    if cleaned_count > 0:
                        self.logger.debug(f"🧹 Cleaned {cleaned_count} expired {component_type.value} components")
                
                if total_cleaned > 0:
                    # Force garbage collection
                    gc.collect()
                    self.logger.info(f"🗑️ Cleaned up {total_cleaned} expired components")
        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        finally:
            # Schedule next cleanup
            self._start_cleanup_timer()
    
    def force_cleanup(self, component_type: Optional[ComponentType] = None) -> int:
        """Force cleanup of components.
        
        Args:
            component_type: Specific component type to clean, or None for all
            
        Returns:
            int: Number of components cleaned
        """
        with self.cleanup_lock:
            total_cleaned = 0
            
            types_to_clean = [component_type] if component_type else list(self.pools.keys())
            
            for comp_type in types_to_clean:
                if comp_type not in self.pools:
                    continue
                
                pool_config = self.pools[comp_type]
                available_queue = self.available[comp_type]
                
                # Clean all available components
                while available_queue:
                    pooled_comp = available_queue.popleft()
                    self._cleanup_component(pooled_comp, pool_config)
                    total_cleaned += 1
            
            if total_cleaned > 0:
                gc.collect()
                self.logger.info(f"🧽 Force cleaned {total_cleaned} components")
            
            return total_cleaned
    
    def get_stats(self) -> Dict[str, Any]:
        """Get recycling statistics.
        
        Returns:
            Dict[str, Any]: Statistics data
        """
        with self.cleanup_lock:
            stats = {
                'pools': {},
                'total_created': sum(self.total_created.values()),
                'total_recycled': sum(self.total_recycled.values()),
                'memory_saved_ratio': 0.0
            }
            
            for component_type in self.pools:
                created = self.total_created[component_type]
                recycled = self.total_recycled[component_type]
                available = len(self.available[component_type])
                in_use = len(self.in_use[component_type])
                peak = self.peak_usage[component_type]
                
                stats['pools'][component_type.value] = {
                    'created': created,
                    'recycled': recycled,
                    'available': available,
                    'in_use': in_use,
                    'peak_usage': peak,
                    'recycle_ratio': recycled / max(created, 1)
                }
            
            # Calculate memory savings
            total_created = sum(self.total_created.values())
            total_recycled = sum(self.total_recycled.values())
            if total_created > 0:
                stats['memory_saved_ratio'] = total_recycled / total_created
            
            return stats
    
    def shutdown(self) -> None:
        """Shutdown the component recycler."""
        self.logger.info("🛑 Shutting down component recycler...")
        self._shutdown = True
        
        # Cancel cleanup timer
        if self.cleanup_timer:
            self.cleanup_timer.cancel()
        
        # Force cleanup all components
        total_cleaned = self.force_cleanup()
        
        # Clear weak references
        self.weak_refs.clear()
        
        # Clear all data structures
        self.pools.clear()
        self.available.clear()
        self.in_use.clear()
        
        self.logger.info(f"✅ Component recycler shutdown complete (cleaned {total_cleaned} components)")


# Convenience functions for common component types
def create_forecast_card_factory(parent_widget) -> Callable[[], Any]:
    """Create a factory function for forecast cards.
    
    Args:
        parent_widget: Parent widget for the cards
        
    Returns:
        Callable: Factory function
    """
    def factory():
        # This would create your actual forecast card widget
        # Placeholder implementation
        frame = ttk.Frame(parent_widget)
        return frame
    
    return factory


def reset_forecast_card(card_widget) -> None:
    """Reset a forecast card to default state.
    
    Args:
        card_widget: Card widget to reset
    """
    # Clear any data and reset to default state
    # Placeholder implementation
    for child in card_widget.winfo_children():
        child.destroy()


def cleanup_forecast_card(card_widget) -> None:
    """Clean up a forecast card.
    
    Args:
        card_widget: Card widget to clean up
    """
    try:
        card_widget.destroy()
    except tk.TclError:
        pass  # Already destroyed