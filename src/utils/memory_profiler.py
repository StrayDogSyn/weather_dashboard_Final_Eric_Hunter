"""Memory Profiling System

Advanced memory monitoring and profiling utilities for performance optimization.
Tracks memory usage, detects leaks, and provides optimization recommendations.
"""

import gc
import psutil
import time
import threading
import weakref
from typing import Dict, List, Callable, Any, Optional
from functools import wraps
from collections import defaultdict, deque
import logging
import tracemalloc
import sys

logger = logging.getLogger(__name__)

# Global memory profiler instance
_global_profiler = None

def get_global_profiler():
    """Get or create global memory profiler instance"""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = MemoryProfiler()
    return _global_profiler

class MemoryProfiler:
    """Comprehensive memory profiling and monitoring system"""
    
    def __init__(self, enable_tracemalloc: bool = True):
        self.baseline = self.get_memory_usage()
        self.peak_memory = self.baseline
        self.memory_history: deque = deque(maxlen=100)
        self.operation_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_memory': 0,
            'peak_memory': 0,
            'avg_memory': 0
        })
        self.active_operations: Dict[str, float] = {}
        self.memory_threshold = 50  # MB threshold for warnings
        self.leak_threshold = 10    # MB threshold for leak detection
        self.monitoring_enabled = True
        self._lock = threading.Lock()
        
        # Enable tracemalloc for detailed memory tracking
        if enable_tracemalloc and not tracemalloc.is_tracing():
            tracemalloc.start()
            
        # Start background monitoring
        self._start_monitoring()
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0
    
    def get_detailed_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            info = {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': memory_percent,
                'available_mb': psutil.virtual_memory().available / 1024 / 1024,
                'gc_objects': len(gc.get_objects()),
                'gc_collections': gc.get_stats()
            }
            
            # Add tracemalloc info if available
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                info.update({
                    'traced_current_mb': current / 1024 / 1024,
                    'traced_peak_mb': peak / 1024 / 1024
                })
                
            return info
        except Exception as e:
            logger.error(f"Failed to get detailed memory info: {e}")
            return {}
    
    def profile(self, operation_name: str, threshold_mb: Optional[float] = None):
        """Enhanced decorator to profile memory usage
        
        Args:
            operation_name: Name of the operation being profiled
            threshold_mb: Custom threshold for this operation (overrides default)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.monitoring_enabled:
                    return func(*args, **kwargs)
                    
                # Record start state
                start_time = time.time()
                before_memory = self.get_memory_usage()
                gc_before = len(gc.get_objects())
                
                # Track active operation
                with self._lock:
                    self.active_operations[operation_name] = start_time
                
                try:
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Record end state
                    after_memory = self.get_memory_usage()
                    gc_after = len(gc.get_objects())
                    elapsed_time = time.time() - start_time
                    
                    # Calculate metrics
                    memory_delta = after_memory - before_memory
                    gc_delta = gc_after - gc_before
                    
                    # Update statistics
                    with self._lock:
                        stats = self.operation_stats[operation_name]
                        stats['count'] += 1
                        stats['total_memory'] += memory_delta
                        stats['peak_memory'] = max(stats['peak_memory'], memory_delta)
                        stats['avg_memory'] = stats['total_memory'] / stats['count']
                        stats['last_execution'] = {
                            'memory_delta': memory_delta,
                            'gc_delta': gc_delta,
                            'execution_time': elapsed_time,
                            'timestamp': time.time()
                        }
                        
                        # Remove from active operations
                        self.active_operations.pop(operation_name, None)
                    
                    # Check thresholds
                    threshold = threshold_mb or self.memory_threshold
                    if abs(memory_delta) > threshold:
                        logger.warning(
                            f"{operation_name} memory change: {memory_delta:+.2f}MB "
                            f"(threshold: {threshold}MB, objects: {gc_delta:+d}, time: {elapsed_time:.3f}s)"
                        )
                    
                    # Update peak memory
                    self.peak_memory = max(self.peak_memory, after_memory)
                    
                    # Add to history
                    self.memory_history.append({
                        'timestamp': time.time(),
                        'operation': operation_name,
                        'memory_before': before_memory,
                        'memory_after': after_memory,
                        'memory_delta': memory_delta,
                        'gc_objects': gc_after
                    })
                    
                    return result
                    
                except Exception as e:
                    # Clean up on error
                    with self._lock:
                        self.active_operations.pop(operation_name, None)
                    raise e
                    
            return wrapper
        return decorator
    
    def detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks"""
        leaks = []
        
        with self._lock:
            for operation, stats in self.operation_stats.items():
                # Check for consistent memory growth
                if (stats['avg_memory'] > self.leak_threshold and 
                    stats['count'] > 5 and 
                    stats['avg_memory'] > 0):
                    
                    leaks.append({
                        'operation': operation,
                        'avg_memory_growth': stats['avg_memory'],
                        'peak_memory': stats['peak_memory'],
                        'execution_count': stats['count'],
                        'total_memory': stats['total_memory'],
                        'severity': 'high' if stats['avg_memory'] > self.leak_threshold * 2 else 'medium'
                    })
        
        return sorted(leaks, key=lambda x: x['avg_memory_growth'], reverse=True)
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory report"""
        current_memory = self.get_memory_usage()
        detailed_info = self.get_detailed_memory_info()
        leaks = self.detect_memory_leaks()
        
        # Calculate memory trend
        recent_history = list(self.memory_history)[-10:] if self.memory_history else []
        memory_trend = 'stable'
        if len(recent_history) >= 2:
            start_memory = recent_history[0]['memory_after']
            end_memory = recent_history[-1]['memory_after']
            change_percent = ((end_memory - start_memory) / start_memory) * 100
            
            if change_percent > 5:
                memory_trend = 'increasing'
            elif change_percent < -5:
                memory_trend = 'decreasing'
        
        # Top memory consumers
        top_consumers = sorted(
            [(op, stats) for op, stats in self.operation_stats.items()],
            key=lambda x: x[1]['avg_memory'],
            reverse=True
        )[:5]
        
        return {
            'current_memory_mb': current_memory,
            'baseline_memory_mb': self.baseline,
            'peak_memory_mb': self.peak_memory,
            'memory_growth_mb': current_memory - self.baseline,
            'memory_trend': memory_trend,
            'detailed_info': detailed_info,
            'potential_leaks': leaks,
            'top_consumers': [
                {
                    'operation': op,
                    'avg_memory': stats['avg_memory'],
                    'count': stats['count'],
                    'total_memory': stats['total_memory']
                }
                for op, stats in top_consumers
            ],
            'active_operations': list(self.active_operations.keys()),
            'total_operations': len(self.operation_stats),
            'monitoring_enabled': self.monitoring_enabled
        }
    
    def optimize_memory(self):
        """Perform memory optimization"""
        logger.info("Starting memory optimization...")
        
        # Force garbage collection
        before_gc = self.get_memory_usage()
        collected = gc.collect()
        after_gc = self.get_memory_usage()
        
        memory_freed = before_gc - after_gc
        
        logger.info(
            f"Memory optimization complete: "
            f"freed {memory_freed:.2f}MB, collected {collected} objects"
        )
        
        return {
            'memory_freed_mb': memory_freed,
            'objects_collected': collected,
            'memory_before': before_gc,
            'memory_after': after_gc
        }
    
    def _start_monitoring(self):
        """Start background memory monitoring"""
        def monitor():
            while self.monitoring_enabled:
                try:
                    current_memory = self.get_memory_usage()
                    
                    # Check for memory spikes
                    if current_memory > self.peak_memory * 1.5:  # 50% increase from peak
                        logger.warning(
                            f"Memory spike detected: {current_memory:.2f}MB "
                            f"(peak: {self.peak_memory:.2f}MB)"
                        )
                        
                        # Auto-optimize if memory is very high
                        if current_memory > 500:  # 500MB threshold
                            self.optimize_memory()
                    
                    time.sleep(30)  # Monitor every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Memory monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def enable_monitoring(self):
        """Enable memory monitoring"""
        self.monitoring_enabled = True
        logger.info("Memory monitoring enabled")
    
    def disable_monitoring(self):
        """Disable memory monitoring"""
        self.monitoring_enabled = False
        logger.info("Memory monitoring disabled")
    
    def reset_stats(self):
        """Reset all statistics"""
        with self._lock:
            self.operation_stats.clear()
            self.memory_history.clear()
            self.active_operations.clear()
            self.baseline = self.get_memory_usage()
            self.peak_memory = self.baseline
        
        logger.info("Memory profiler statistics reset")
    
    def get_tracemalloc_top(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top memory allocations from tracemalloc"""
        if not tracemalloc.is_tracing():
            return []
        
        try:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            return [
                {
                    'filename': stat.traceback.format()[0],
                    'size_mb': stat.size / 1024 / 1024,
                    'count': stat.count
                }
                for stat in top_stats[:limit]
            ]
        except Exception as e:
            logger.error(f"Failed to get tracemalloc stats: {e}")
            return []

# Global memory profiler instance
memory_profiler = MemoryProfiler()

# Convenience decorators
def profile_memory(operation_name: str, threshold_mb: float = 10.0):
    """Global decorator for memory profiling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            profiler = get_global_profiler()
            return profiler.profile(operation_name, threshold_mb)(func)(*args, **kwargs)
        return wrapper
    return decorator

def monitor_memory_usage(func: Callable) -> Callable:
    """Simple decorator to monitor memory usage of a function"""
    return memory_profiler.profile(func.__name__)(func)