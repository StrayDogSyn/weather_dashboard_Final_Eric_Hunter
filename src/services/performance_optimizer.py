import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import gc
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    timestamp: datetime
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    rss_mb: float
    vms_mb: float
    percent: float
    available_mb: float
    timestamp: datetime

class PerformanceOptimizer:
    """Comprehensive performance monitoring and optimization"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.memory_snapshots: deque = deque(maxlen=max_history)
        self.performance_alerts: List[Dict] = []
        self.optimization_suggestions: List[str] = []
        
        # Thresholds
        self.memory_threshold_mb = 500
        self.cpu_threshold_percent = 80
        self.response_time_threshold_ms = 1000
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self._lock = threading.Lock()
        
        # Performance counters
        self.operation_counts = defaultdict(int)
        self.operation_times = defaultdict(list)
        
        # Start monitoring
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start background performance monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                self._check_performance_alerts()
                time.sleep(5)  # Monitor every 5 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # Memory metrics
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            memory_snapshot = MemorySnapshot(
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=process.memory_percent(),
                available_mb=system_memory.available / 1024 / 1024,
                timestamp=datetime.now()
            )
            
            with self._lock:
                self.memory_snapshots.append(memory_snapshot)
            
            # CPU metrics
            cpu_percent = process.cpu_percent()
            self.record_metric("cpu_usage_percent", cpu_percent, "system")
            
            # Thread count
            thread_count = threading.active_count()
            self.record_metric("thread_count", thread_count, "system")
            
            # File descriptors (on Unix systems)
            try:
                fd_count = process.num_fds() if hasattr(process, 'num_fds') else 0
                self.record_metric("file_descriptors", fd_count, "system")
            except:
                pass
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def record_metric(self, name: str, value: float, category: str = "general", 
                     metadata: Optional[Dict] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            category=category,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics_history[name].append(metric)
    
    def time_operation(self, operation_name: str):
        """Context manager for timing operations"""
        return OperationTimer(self, operation_name)
    
    def record_operation_time(self, operation_name: str, duration_ms: float):
        """Record operation timing"""
        with self._lock:
            self.operation_counts[operation_name] += 1
            self.operation_times[operation_name].append(duration_ms)
            
            # Keep only recent times
            if len(self.operation_times[operation_name]) > 100:
                self.operation_times[operation_name] = self.operation_times[operation_name][-100:]
        
        # Record as metric
        self.record_metric(f"{operation_name}_duration_ms", duration_ms, "timing")
        
        # Check for performance issues
        if duration_ms > self.response_time_threshold_ms:
            self._add_alert(f"Slow operation: {operation_name} took {duration_ms:.1f}ms")
    
    def _check_performance_alerts(self):
        """Check for performance issues and generate alerts"""
        try:
            # Check memory usage
            if self.memory_snapshots:
                latest_memory = self.memory_snapshots[-1]
                if latest_memory.rss_mb > self.memory_threshold_mb:
                    self._add_alert(f"High memory usage: {latest_memory.rss_mb:.1f}MB")
            
            # Check CPU usage
            cpu_metrics = self.metrics_history.get("cpu_usage_percent")
            if cpu_metrics and len(cpu_metrics) >= 3:
                recent_cpu = [m.value for m in list(cpu_metrics)[-3:]]
                avg_cpu = sum(recent_cpu) / len(recent_cpu)
                if avg_cpu > self.cpu_threshold_percent:
                    self._add_alert(f"High CPU usage: {avg_cpu:.1f}%")
            
            # Check for memory leaks
            self._check_memory_trends()
            
        except Exception as e:
            logger.error(f"Error checking performance alerts: {e}")
    
    def _check_memory_trends(self):
        """Check for memory leak patterns"""
        if len(self.memory_snapshots) < 10:
            return
        
        recent_snapshots = list(self.memory_snapshots)[-10:]
        memory_values = [s.rss_mb for s in recent_snapshots]
        
        # Simple trend detection
        if len(memory_values) >= 5:
            first_half = memory_values[:len(memory_values)//2]
            second_half = memory_values[len(memory_values)//2:]
            
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            
            growth_rate = (avg_second - avg_first) / avg_first * 100
            
            if growth_rate > 20:  # 20% growth
                self._add_alert(f"Potential memory leak detected: {growth_rate:.1f}% growth")
                self.optimization_suggestions.append("Consider running garbage collection")
    
    def _add_alert(self, message: str):
        """Add performance alert"""
        alert = {
            'message': message,
            'timestamp': datetime.now(),
            'severity': 'warning'
        }
        
        with self._lock:
            self.performance_alerts.append(alert)
            # Keep only recent alerts
            if len(self.performance_alerts) > 50:
                self.performance_alerts = self.performance_alerts[-50:]
        
        logger.warning(f"Performance alert: {message}")
    
    def optimize_memory(self):
        """Perform memory optimization"""
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Record optimization
            self.record_metric("gc_objects_collected", collected, "optimization")
            
            logger.info(f"Memory optimization: collected {collected} objects")
            return collected
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return 0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self._lock:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'memory': self._get_memory_summary(),
                'operations': self._get_operations_summary(),
                'alerts': len(self.performance_alerts),
                'recent_alerts': self.performance_alerts[-5:] if self.performance_alerts else [],
                'suggestions': self.optimization_suggestions[-5:] if self.optimization_suggestions else [],
                'system': self._get_system_summary()
            }
        
        return summary
    
    def _get_memory_summary(self) -> Dict[str, Any]:
        """Get memory usage summary"""
        if not self.memory_snapshots:
            return {}
        
        latest = self.memory_snapshots[-1]
        recent_snapshots = list(self.memory_snapshots)[-10:]
        
        return {
            'current_mb': latest.rss_mb,
            'current_percent': latest.percent,
            'available_mb': latest.available_mb,
            'peak_mb': max(s.rss_mb for s in recent_snapshots),
            'average_mb': sum(s.rss_mb for s in recent_snapshots) / len(recent_snapshots)
        }
    
    def _get_operations_summary(self) -> Dict[str, Any]:
        """Get operations performance summary"""
        operations = {}
        
        for op_name, times in self.operation_times.items():
            if times:
                operations[op_name] = {
                    'count': self.operation_counts[op_name],
                    'avg_ms': sum(times) / len(times),
                    'min_ms': min(times),
                    'max_ms': max(times),
                    'recent_avg_ms': sum(times[-10:]) / min(len(times), 10)
                }
        
        return operations
    
    def _get_system_summary(self) -> Dict[str, Any]:
        """Get system metrics summary"""
        try:
            process = psutil.Process()
            return {
                'cpu_percent': process.cpu_percent(),
                'thread_count': threading.active_count(),
                'python_version': sys.version,
                'platform': sys.platform
            }
        except Exception as e:
            logger.error(f"Failed to get system summary: {e}")
            return {}
    
    def export_metrics(self, filepath: str):
        """Export performance metrics to file"""
        try:
            import json
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'summary': self.get_performance_summary(),
                'metrics_count': {name: len(metrics) for name, metrics in self.metrics_history.items()},
                'memory_snapshots_count': len(self.memory_snapshots)
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Performance metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")

class OperationTimer:
    """Context manager for timing operations"""
    
    def __init__(self, optimizer: PerformanceOptimizer, operation_name: str):
        self.optimizer = optimizer
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.optimizer.record_operation_time(self.operation_name, duration_ms)

# Global instance
_global_optimizer = None

def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = PerformanceOptimizer()
    return _global_optimizer

def time_operation(operation_name: str):
    """Decorator for timing function calls"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            optimizer = get_performance_optimizer()
            with optimizer.time_operation(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator