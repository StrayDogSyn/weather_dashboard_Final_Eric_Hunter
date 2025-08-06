"""Memory optimization service for efficient memory management.

Provides memory monitoring, cleanup, and optimization strategies.
"""

import gc
import sys
import time
import threading
import logging
import weakref
import psutil
import os
from typing import Any, Dict, List, Optional, Callable, Set, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps
import tracemalloc
from enum import Enum


class MemoryLevel(Enum):
    """Memory usage level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemoryStats:
    """Memory statistics."""
    total_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    used_memory_mb: float = 0.0
    memory_percent: float = 0.0
    process_memory_mb: float = 0.0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    object_counts: Dict[str, int] = field(default_factory=dict)
    weak_refs_count: int = 0
    cache_size_mb: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    @property
    def memory_level(self) -> MemoryLevel:
        """Determine memory usage level."""
        if self.memory_percent >= 90:
            return MemoryLevel.CRITICAL
        elif self.memory_percent >= 75:
            return MemoryLevel.HIGH
        elif self.memory_percent >= 50:
            return MemoryLevel.MEDIUM
        else:
            return MemoryLevel.LOW


class WeakRefManager:
    """Manager for weak references to prevent memory leaks."""
    
    def __init__(self):
        """Initialize weak reference manager."""
        self._weak_refs: Dict[str, weakref.ref] = {}
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
    
    def register(self, name: str, obj: Any, 
                callback: Optional[Callable] = None) -> weakref.ref:
        """Register an object with weak reference.
        
        Args:
            name: Reference name
            obj: Object to reference
            callback: Optional callback when object is garbage collected
            
        Returns:
            Weak reference
        """
        with self._lock:
            def cleanup_callback(ref):
                self._logger.debug(f"Object '{name}' was garbage collected")
                if name in self._weak_refs:
                    del self._weak_refs[name]
                
                # Call user callback
                if callback:
                    try:
                        callback(name, ref)
                    except Exception as e:
                        self._logger.error(f"Error in cleanup callback for '{name}': {e}")
                
                # Call registered callbacks
                for cb in self._callbacks.get(name, []):
                    try:
                        cb(name, ref)
                    except Exception as e:
                        self._logger.error(f"Error in registered callback for '{name}': {e}")
            
            weak_ref = weakref.ref(obj, cleanup_callback)
            self._weak_refs[name] = weak_ref
            
            return weak_ref
    
    def get(self, name: str) -> Optional[Any]:
        """Get object by name.
        
        Args:
            name: Reference name
            
        Returns:
            Object or None if garbage collected
        """
        with self._lock:
            if name in self._weak_refs:
                return self._weak_refs[name]()
            return None
    
    def add_callback(self, name: str, callback: Callable) -> None:
        """Add callback for when object is garbage collected.
        
        Args:
            name: Reference name
            callback: Callback function
        """
        with self._lock:
            self._callbacks[name].append(callback)
    
    def remove(self, name: str) -> bool:
        """Remove weak reference.
        
        Args:
            name: Reference name
            
        Returns:
            True if reference was removed
        """
        with self._lock:
            if name in self._weak_refs:
                del self._weak_refs[name]
                if name in self._callbacks:
                    del self._callbacks[name]
                return True
            return False
    
    def cleanup_dead_refs(self) -> int:
        """Clean up dead weak references.
        
        Returns:
            Number of dead references cleaned up
        """
        with self._lock:
            dead_refs = []
            for name, ref in self._weak_refs.items():
                if ref() is None:
                    dead_refs.append(name)
            
            for name in dead_refs:
                del self._weak_refs[name]
                if name in self._callbacks:
                    del self._callbacks[name]
            
            return len(dead_refs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get weak reference statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total_refs = len(self._weak_refs)
            alive_refs = sum(1 for ref in self._weak_refs.values() if ref() is not None)
            dead_refs = total_refs - alive_refs
            
            return {
                'total_refs': total_refs,
                'alive_refs': alive_refs,
                'dead_refs': dead_refs,
                'callback_count': sum(len(callbacks) for callbacks in self._callbacks.values())
            }


class ObjectTracker:
    """Tracker for monitoring object creation and destruction."""
    
    def __init__(self, max_history: int = 1000):
        """Initialize object tracker.
        
        Args:
            max_history: Maximum history entries to keep
        """
        self.max_history = max_history
        self._object_counts: Dict[str, int] = defaultdict(int)
        self._creation_history: deque = deque(maxlen=max_history)
        self._destruction_history: deque = deque(maxlen=max_history)
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
    
    def track_creation(self, obj_type: str, obj_id: Optional[str] = None) -> None:
        """Track object creation.
        
        Args:
            obj_type: Object type name
            obj_id: Optional object identifier
        """
        with self._lock:
            self._object_counts[obj_type] += 1
            self._creation_history.append({
                'type': obj_type,
                'id': obj_id,
                'timestamp': time.time(),
                'action': 'created'
            })
    
    def track_destruction(self, obj_type: str, obj_id: Optional[str] = None) -> None:
        """Track object destruction.
        
        Args:
            obj_type: Object type name
            obj_id: Optional object identifier
        """
        with self._lock:
            self._object_counts[obj_type] = max(0, self._object_counts[obj_type] - 1)
            self._destruction_history.append({
                'type': obj_type,
                'id': obj_id,
                'timestamp': time.time(),
                'action': 'destroyed'
            })
    
    def get_counts(self) -> Dict[str, int]:
        """Get current object counts.
        
        Returns:
            Dictionary with object counts by type
        """
        with self._lock:
            return dict(self._object_counts)
    
    def get_history(self, obj_type: Optional[str] = None, 
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Get object history.
        
        Args:
            obj_type: Filter by object type
            limit: Maximum number of entries
            
        Returns:
            List of history entries
        """
        with self._lock:
            # Combine creation and destruction history
            all_history = list(self._creation_history) + list(self._destruction_history)
            
            # Sort by timestamp
            all_history.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Filter by type if specified
            if obj_type:
                all_history = [entry for entry in all_history if entry['type'] == obj_type]
            
            return all_history[:limit]


class MemoryOptimizer:
    """Service for memory optimization and monitoring."""
    
    def __init__(self, 
                 monitoring_interval: float = 30.0,
                 cleanup_threshold: float = 75.0,
                 critical_threshold: float = 90.0):
        """
        Initialize memory optimizer.
        
        Args:
            monitoring_interval: Monitoring interval in seconds
            cleanup_threshold: Memory percentage to trigger cleanup
            critical_threshold: Memory percentage for critical actions
        """
        self.monitoring_interval = monitoring_interval
        self.cleanup_threshold = cleanup_threshold
        self.critical_threshold = critical_threshold
        
        self._weak_ref_manager = WeakRefManager()
        self._object_tracker = ObjectTracker()
        self._cleanup_callbacks: List[Callable] = []
        self._memory_history: deque = deque(maxlen=100)
        
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Enable tracemalloc for detailed memory tracking
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # Start monitoring
        self.start_monitoring()
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics.
        
        Returns:
            Memory statistics
        """
        # System memory
        memory = psutil.virtual_memory()
        
        # Process memory
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Garbage collection stats
        gc_stats = {i: gc.get_count()[i] for i in range(3)}
        
        # Object counts
        object_counts = self._object_tracker.get_counts()
        
        # Weak references
        weak_ref_stats = self._weak_ref_manager.get_stats()
        
        # Cache size (estimate)
        cache_size = self._estimate_cache_size()
        
        return MemoryStats(
            total_memory_mb=memory.total / 1024 / 1024,
            available_memory_mb=memory.available / 1024 / 1024,
            used_memory_mb=memory.used / 1024 / 1024,
            memory_percent=memory.percent,
            process_memory_mb=process_memory,
            gc_collections=gc_stats,
            object_counts=object_counts,
            weak_refs_count=weak_ref_stats['total_refs'],
            cache_size_mb=cache_size
        )
    
    def register_cleanup_callback(self, callback: Callable[[MemoryLevel], None]) -> None:
        """Register cleanup callback.
        
        Args:
            callback: Callback function that takes memory level
        """
        with self._lock:
            self._cleanup_callbacks.append(callback)
    
    def register_weak_ref(self, name: str, obj: Any, 
                         callback: Optional[Callable] = None) -> weakref.ref:
        """Register weak reference.
        
        Args:
            name: Reference name
            obj: Object to reference
            callback: Optional cleanup callback
            
        Returns:
            Weak reference
        """
        return self._weak_ref_manager.register(name, obj, callback)
    
    def track_object_creation(self, obj_type: str, obj_id: Optional[str] = None) -> None:
        """Track object creation.
        
        Args:
            obj_type: Object type name
            obj_id: Optional object identifier
        """
        self._object_tracker.track_creation(obj_type, obj_id)
    
    def track_object_destruction(self, obj_type: str, obj_id: Optional[str] = None) -> None:
        """Track object destruction.
        
        Args:
            obj_type: Object type name
            obj_id: Optional object identifier
        """
        self._object_tracker.track_destruction(obj_type, obj_id)
    
    def force_cleanup(self, level: Optional[MemoryLevel] = None) -> Dict[str, Any]:
        """Force memory cleanup.
        
        Args:
            level: Cleanup level (auto-detect if None)
            
        Returns:
            Dictionary with cleanup results
        """
        if level is None:
            stats = self.get_memory_stats()
            level = stats.memory_level
        
        self._logger.info(f"Starting memory cleanup (level: {level.value})")
        
        cleanup_results = {
            'level': level.value,
            'start_time': time.time(),
            'actions_taken': []
        }
        
        # Clean up dead weak references
        dead_refs = self._weak_ref_manager.cleanup_dead_refs()
        if dead_refs > 0:
            cleanup_results['actions_taken'].append(f"Cleaned {dead_refs} dead weak references")
        
        # Run garbage collection
        if level in (MemoryLevel.HIGH, MemoryLevel.CRITICAL):
            collected = gc.collect()
            cleanup_results['actions_taken'].append(f"Garbage collection freed {collected} objects")
        
        # Call cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback(level)
                cleanup_results['actions_taken'].append(f"Executed cleanup callback: {callback.__name__}")
            except Exception as e:
                self._logger.error(f"Error in cleanup callback: {e}")
        
        # Critical level actions
        if level == MemoryLevel.CRITICAL:
            # Force aggressive garbage collection
            for i in range(3):
                collected = gc.collect()
                if collected == 0:
                    break
            
            cleanup_results['actions_taken'].append("Performed aggressive garbage collection")
        
        cleanup_results['end_time'] = time.time()
        cleanup_results['duration'] = cleanup_results['end_time'] - cleanup_results['start_time']
        
        self._logger.info(f"Memory cleanup completed in {cleanup_results['duration']:.2f}s")
        return cleanup_results
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage.
        
        Returns:
            Dictionary with optimization results
        """
        start_stats = self.get_memory_stats()
        
        optimization_results = {
            'start_memory_mb': start_stats.process_memory_mb,
            'start_memory_percent': start_stats.memory_percent,
            'optimizations': []
        }
        
        # Clean up based on current memory level
        cleanup_result = self.force_cleanup(start_stats.memory_level)
        optimization_results['optimizations'].append(cleanup_result)
        
        # Get final stats
        end_stats = self.get_memory_stats()
        optimization_results['end_memory_mb'] = end_stats.process_memory_mb
        optimization_results['end_memory_percent'] = end_stats.memory_percent
        optimization_results['memory_saved_mb'] = start_stats.process_memory_mb - end_stats.process_memory_mb
        
        return optimization_results
    
    def start_monitoring(self) -> None:
        """Start memory monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitoring_thread.start()
        self._logger.info("Memory monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)
        self._logger.info("Memory monitoring stopped")
    
    def get_memory_history(self, limit: int = 50) -> List[MemoryStats]:
        """Get memory usage history.
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of memory statistics
        """
        with self._lock:
            return list(self._memory_history)[-limit:]
    
    def _monitoring_loop(self) -> None:
        """Memory monitoring loop."""
        while self._monitoring_active:
            try:
                stats = self.get_memory_stats()
                
                # Store in history
                with self._lock:
                    self._memory_history.append(stats)
                
                # Check if cleanup is needed
                if stats.memory_percent >= self.critical_threshold:
                    self._logger.warning(f"Critical memory usage: {stats.memory_percent:.1f}%")
                    self.force_cleanup(MemoryLevel.CRITICAL)
                elif stats.memory_percent >= self.cleanup_threshold:
                    self._logger.info(f"High memory usage: {stats.memory_percent:.1f}%")
                    self.force_cleanup(MemoryLevel.HIGH)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self._logger.error(f"Error in memory monitoring: {e}")
                time.sleep(self.monitoring_interval)
    
    def _estimate_cache_size(self) -> float:
        """Estimate cache size in MB.
        
        Returns:
            Estimated cache size in MB
        """
        try:
            # This is a rough estimation
            # In practice, you'd want to integrate with your cache services
            from .cache import get_cache_manager
            
            cache_manager = get_cache_manager()
            stats = cache_manager.get_stats()
            
            memory_info = stats.get('memory_cache_info', {})
            file_info = stats.get('file_cache_info', {})
            
            memory_size = memory_info.get('total_size_mb', 0)
            file_size = file_info.get('total_size_mb', 0)
            
            return memory_size + file_size
            
        except Exception:
            return 0.0


# Decorators for memory optimization
def track_memory(obj_type: str):
    """Decorator to track object creation/destruction.
    
    Args:
        obj_type: Object type name
        
    Returns:
        Decorator function
    """
    def decorator(cls):
        original_init = cls.__init__
        original_del = getattr(cls, '__del__', None)
        
        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            optimizer = get_memory_optimizer()
            optimizer.track_object_creation(obj_type, str(id(self)))
            return original_init(self, *args, **kwargs)
        
        def new_del(self):
            optimizer = get_memory_optimizer()
            optimizer.track_object_destruction(obj_type, str(id(self)))
            if original_del:
                return original_del(self)
        
        cls.__init__ = new_init
        cls.__del__ = new_del
        
        return cls
    
    return decorator


def memory_efficient(cleanup_callback: Optional[Callable] = None):
    """Decorator for memory-efficient functions.
    
    Args:
        cleanup_callback: Optional cleanup callback
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check memory before execution
            optimizer = get_memory_optimizer()
            start_stats = optimizer.get_memory_stats()
            
            if start_stats.memory_level in (MemoryLevel.HIGH, MemoryLevel.CRITICAL):
                optimizer.force_cleanup(start_stats.memory_level)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Cleanup after execution if callback provided
                if cleanup_callback:
                    try:
                        cleanup_callback()
                    except Exception as e:
                        logging.getLogger(__name__).error(f"Error in cleanup callback: {e}")
        
        return wrapper
    
    return decorator


# Global memory optimizer instance
_global_memory_optimizer = None


def get_memory_optimizer() -> MemoryOptimizer:
    """Get global memory optimizer instance."""
    global _global_memory_optimizer
    if _global_memory_optimizer is None:
        _global_memory_optimizer = MemoryOptimizer()
    return _global_memory_optimizer