"""Performance monitoring service for tracking optimization improvements.

Provides comprehensive monitoring of cache performance, memory usage, and system metrics.
"""

import time
import psutil
import threading
import logging
import json
import gc
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from functools import wraps
from enum import Enum
import weakref


class MetricType(Enum):
    """Performance metric types."""
    RESPONSE_TIME = "response_time"
    MEMORY_USAGE = "memory_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    API_CALLS = "api_calls"
    DATABASE_QUERIES = "database_queries"
    IMAGE_PROCESSING = "image_processing"
    CHART_RENDERING = "chart_rendering"
    UI_RENDERING = "ui_rendering"
    SYSTEM_RESOURCES = "system_resources"
    ERROR_RATE = "error_rate"


class PerformanceLevel(Enum):
    """Performance levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    category: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def age_seconds(self) -> float:
        """Get metric age in seconds."""
        return time.time() - self.timestamp


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_usage_percent: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    process_count: int = 0
    thread_count: int = 0
    timestamp: float = field(default_factory=time.time)
    
    @classmethod
    def collect(cls) -> 'SystemMetrics':
        """Collect current system metrics.
        
        Returns:
            Current system metrics
        """
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            # Process info
            process = psutil.Process()
            
            return cls(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_usage_percent=(disk.used / disk.total) * 100,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                process_count=len(psutil.pids()),
                thread_count=process.num_threads()
            )
        except Exception:
            return cls()


@dataclass
class PerformanceReport:
    """Performance analysis report."""
    start_time: float
    end_time: float
    duration_seconds: float
    
    # Cache performance
    cache_hit_rate: float = 0.0
    cache_memory_saved_mb: float = 0.0
    cache_response_time_improvement: float = 0.0
    
    # Memory optimization
    memory_usage_reduction_mb: float = 0.0
    memory_peak_reduction_percent: float = 0.0
    gc_collections_reduced: int = 0
    
    # API optimization
    api_calls_reduced: int = 0
    api_response_time_improvement: float = 0.0
    api_cost_savings: float = 0.0
    
    # Database optimization
    db_query_time_improvement: float = 0.0
    db_connection_pool_efficiency: float = 0.0
    db_cache_hit_rate: float = 0.0
    
    # Image processing
    image_processing_time_improvement: float = 0.0
    image_memory_savings_mb: float = 0.0
    image_cache_hit_rate: float = 0.0
    
    # Chart rendering
    chart_render_time_improvement: float = 0.0
    chart_memory_savings_mb: float = 0.0
    chart_cache_hit_rate: float = 0.0
    
    # UI performance
    ui_render_time_improvement: float = 0.0
    lazy_loading_time_saved: float = 0.0
    component_creation_improvement: float = 0.0
    
    # Overall metrics
    overall_performance_improvement: float = 0.0
    error_rate_reduction: float = 0.0
    user_experience_score: float = 0.0
    
    @property
    def performance_level(self) -> PerformanceLevel:
        """Get overall performance level.
        
        Returns:
            Performance level
        """
        if self.overall_performance_improvement >= 40:
            return PerformanceLevel.EXCELLENT
        elif self.overall_performance_improvement >= 25:
            return PerformanceLevel.GOOD
        elif self.overall_performance_improvement >= 10:
            return PerformanceLevel.FAIR
        elif self.overall_performance_improvement >= 0:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return asdict(self)


class PerformanceTracker:
    """Tracks performance metrics over time."""
    
    def __init__(self, max_metrics: int = 10000, retention_hours: float = 24.0):
        """
        Initialize performance tracker.
        
        Args:
            max_metrics: Maximum metrics to store
            retention_hours: How long to retain metrics
        """
        self.max_metrics = max_metrics
        self.retention_seconds = retention_hours * 3600
        
        self._metrics: Dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=max_metrics))
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Baseline metrics for comparison
        self._baseline_metrics: Dict[str, float] = {}
        
        # Performance thresholds
        self._thresholds = {
            MetricType.RESPONSE_TIME: {'good': 100, 'fair': 500, 'poor': 1000},  # ms
            MetricType.MEMORY_USAGE: {'good': 50, 'fair': 70, 'poor': 85},       # %
            MetricType.CACHE_HIT_RATE: {'good': 80, 'fair': 60, 'poor': 40},     # %
            MetricType.ERROR_RATE: {'good': 1, 'fair': 5, 'poor': 10},           # %
        }
    
    def record_metric(self, metric_type: MetricType, name: str, value: float,
                     unit: str = "", category: str = "", tags: Optional[Dict[str, str]] = None) -> None:
        """Record a performance metric.
        
        Args:
            metric_type: Type of metric
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            category: Metric category
            tags: Additional tags
        """
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            category=category,
            tags=tags or {}
        )
        
        with self._lock:
            self._metrics[metric_type].append(metric)
            
            # Clean up old metrics
            self._cleanup_old_metrics(metric_type)
    
    def _cleanup_old_metrics(self, metric_type: MetricType) -> None:
        """Clean up old metrics.
        
        Args:
            metric_type: Metric type to clean
        """
        current_time = time.time()
        metrics_deque = self._metrics[metric_type]
        
        # Remove metrics older than retention period
        while metrics_deque and current_time - metrics_deque[0].timestamp > self.retention_seconds:
            metrics_deque.popleft()
    
    def get_metrics(self, metric_type: MetricType, 
                   time_range_seconds: Optional[float] = None) -> List[PerformanceMetric]:
        """Get metrics of specified type.
        
        Args:
            metric_type: Type of metrics to retrieve
            time_range_seconds: Time range to filter (None for all)
            
        Returns:
            List of metrics
        """
        with self._lock:
            metrics = list(self._metrics[metric_type])
            
            if time_range_seconds is not None:
                cutoff_time = time.time() - time_range_seconds
                metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            
            return metrics
    
    def get_average(self, metric_type: MetricType, name: str,
                   time_range_seconds: Optional[float] = None) -> Optional[float]:
        """Get average value for a metric.
        
        Args:
            metric_type: Metric type
            name: Metric name
            time_range_seconds: Time range to consider
            
        Returns:
            Average value or None
        """
        metrics = self.get_metrics(metric_type, time_range_seconds)
        matching_metrics = [m for m in metrics if m.name == name]
        
        if not matching_metrics:
            return None
        
        return sum(m.value for m in matching_metrics) / len(matching_metrics)
    
    def get_percentile(self, metric_type: MetricType, name: str, percentile: float,
                      time_range_seconds: Optional[float] = None) -> Optional[float]:
        """Get percentile value for a metric.
        
        Args:
            metric_type: Metric type
            name: Metric name
            percentile: Percentile (0-100)
            time_range_seconds: Time range to consider
            
        Returns:
            Percentile value or None
        """
        metrics = self.get_metrics(metric_type, time_range_seconds)
        matching_metrics = [m for m in metrics if m.name == name]
        
        if not matching_metrics:
            return None
        
        values = sorted([m.value for m in matching_metrics])
        index = int((percentile / 100) * (len(values) - 1))
        return values[index]
    
    def set_baseline(self, name: str, value: float) -> None:
        """Set baseline metric for comparison.
        
        Args:
            name: Baseline name
            value: Baseline value
        """
        with self._lock:
            self._baseline_metrics[name] = value
    
    def get_improvement(self, name: str, current_value: float) -> float:
        """Get improvement percentage compared to baseline.
        
        Args:
            name: Metric name
            current_value: Current value
            
        Returns:
            Improvement percentage
        """
        with self._lock:
            baseline = self._baseline_metrics.get(name)
            if baseline is None or baseline == 0:
                return 0.0
            
            # For metrics where lower is better (response time, memory usage)
            if name in ['response_time', 'memory_usage', 'error_rate']:
                return ((baseline - current_value) / baseline) * 100
            else:
                # For metrics where higher is better (cache hit rate)
                return ((current_value - baseline) / baseline) * 100
    
    def get_performance_level(self, metric_type: MetricType, value: float) -> PerformanceLevel:
        """Get performance level for a metric value.
        
        Args:
            metric_type: Metric type
            value: Metric value
            
        Returns:
            Performance level
        """
        thresholds = self._thresholds.get(metric_type, {})
        
        if value <= thresholds.get('good', 0):
            return PerformanceLevel.EXCELLENT
        elif value <= thresholds.get('fair', 0):
            return PerformanceLevel.GOOD
        elif value <= thresholds.get('poor', 0):
            return PerformanceLevel.FAIR
        else:
            return PerformanceLevel.POOR
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics.
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            stats = {
                'total_metrics': sum(len(metrics) for metrics in self._metrics.values()),
                'metric_types': {mt.value: len(self._metrics[mt]) for mt in self._metrics},
                'retention_hours': self.retention_seconds / 3600,
                'baseline_metrics': self._baseline_metrics.copy()
            }
            
            # Recent performance summary
            recent_stats = {}
            for metric_type in MetricType:
                recent_metrics = self.get_metrics(metric_type, 3600)  # Last hour
                if recent_metrics:
                    values = [m.value for m in recent_metrics]
                    recent_stats[metric_type.value] = {
                        'count': len(values),
                        'avg': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values)
                    }
            
            stats['recent_performance'] = recent_stats
            return stats


class PerformanceMonitor:
    """Main performance monitoring service."""
    
    def __init__(self, monitoring_interval: float = 60.0):
        """
        Initialize performance monitor.
        
        Args:
            monitoring_interval: System monitoring interval in seconds
        """
        self.monitoring_interval = monitoring_interval
        
        self._tracker = PerformanceTracker()
        self._system_metrics_history: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Monitoring thread
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitoring_thread.start()
        
        # Performance optimization services
        self._cache_services = []
        self._optimization_services = []
        
        # Baseline collection
        self._baseline_collected = False
        self._baseline_collection_time = None
    
    def register_cache_service(self, service: Any) -> None:
        """Register a cache service for monitoring.
        
        Args:
            service: Cache service to monitor
        """
        self._cache_services.append(weakref.ref(service))
    
    def register_optimization_service(self, service: Any) -> None:
        """Register an optimization service for monitoring.
        
        Args:
            service: Optimization service to monitor
        """
        self._optimization_services.append(weakref.ref(service))
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                # Collect system metrics
                system_metrics = SystemMetrics.collect()
                
                with self._lock:
                    self._system_metrics_history.append(system_metrics)
                
                # Record system metrics
                self._tracker.record_metric(
                    MetricType.SYSTEM_RESOURCES, "cpu_percent", 
                    system_metrics.cpu_percent, "%"
                )
                self._tracker.record_metric(
                    MetricType.MEMORY_USAGE, "memory_percent", 
                    system_metrics.memory_percent, "%"
                )
                self._tracker.record_metric(
                    MetricType.MEMORY_USAGE, "memory_used_mb", 
                    system_metrics.memory_used_mb, "MB"
                )
                
                # Collect cache service metrics
                self._collect_cache_metrics()
                
                # Collect optimization service metrics
                self._collect_optimization_metrics()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self._logger.error(f"Error in performance monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_cache_metrics(self) -> None:
        """Collect metrics from cache services."""
        for cache_ref in self._cache_services[:]:
            cache_service = cache_ref()
            if cache_service is None:
                self._cache_services.remove(cache_ref)
                continue
            
            try:
                if hasattr(cache_service, 'get_stats'):
                    stats = cache_service.get_stats()
                    
                    # Record cache metrics
                    if 'hit_rate' in stats:
                        self._tracker.record_metric(
                            MetricType.CACHE_HIT_RATE, "cache_hit_rate",
                            stats['hit_rate'], "%"
                        )
                    
                    if 'memory_usage_mb' in stats:
                        self._tracker.record_metric(
                            MetricType.MEMORY_USAGE, "cache_memory_mb",
                            stats['memory_usage_mb'], "MB"
                        )
                    
            except Exception as e:
                self._logger.warning(f"Failed to collect cache metrics: {e}")
    
    def _collect_optimization_metrics(self) -> None:
        """Collect metrics from optimization services."""
        for opt_ref in self._optimization_services[:]:
            opt_service = opt_ref()
            if opt_service is None:
                self._optimization_services.remove(opt_ref)
                continue
            
            try:
                if hasattr(opt_service, 'get_stats'):
                    stats = opt_service.get_stats()
                    
                    # Record optimization metrics based on service type
                    service_name = opt_service.__class__.__name__.lower()
                    
                    if 'response_time' in stats:
                        self._tracker.record_metric(
                            MetricType.RESPONSE_TIME, f"{service_name}_response_time",
                            stats['response_time'], "ms"
                        )
                    
                    if 'memory_usage' in stats:
                        self._tracker.record_metric(
                            MetricType.MEMORY_USAGE, f"{service_name}_memory",
                            stats['memory_usage'], "MB"
                        )
                    
            except Exception as e:
                self._logger.warning(f"Failed to collect optimization metrics: {e}")
    
    def collect_baseline_metrics(self) -> None:
        """Collect baseline metrics for comparison."""
        if self._baseline_collected:
            return
        
        self._logger.info("Collecting baseline performance metrics...")
        
        # Collect system baseline
        system_metrics = SystemMetrics.collect()
        self._tracker.set_baseline("cpu_percent", system_metrics.cpu_percent)
        self._tracker.set_baseline("memory_percent", system_metrics.memory_percent)
        self._tracker.set_baseline("memory_used_mb", system_metrics.memory_used_mb)
        
        # Collect service baselines
        for cache_ref in self._cache_services:
            cache_service = cache_ref()
            if cache_service and hasattr(cache_service, 'get_stats'):
                try:
                    stats = cache_service.get_stats()
                    service_name = cache_service.__class__.__name__.lower()
                    
                    for key, value in stats.items():
                        if isinstance(value, (int, float)):
                            self._tracker.set_baseline(f"{service_name}_{key}", value)
                            
                except Exception as e:
                    self._logger.warning(f"Failed to collect baseline from cache service: {e}")
        
        self._baseline_collected = True
        self._baseline_collection_time = time.time()
        
        self._logger.info("Baseline metrics collected successfully")
    
    def record_operation_time(self, operation_name: str, duration_ms: float,
                            category: str = "", tags: Optional[Dict[str, str]] = None) -> None:
        """Record operation timing.
        
        Args:
            operation_name: Name of the operation
            duration_ms: Duration in milliseconds
            category: Operation category
            tags: Additional tags
        """
        self._tracker.record_metric(
            MetricType.RESPONSE_TIME, operation_name, duration_ms, "ms", category, tags
        )
    
    def record_memory_usage(self, component_name: str, memory_mb: float,
                          category: str = "", tags: Optional[Dict[str, str]] = None) -> None:
        """Record memory usage.
        
        Args:
            component_name: Name of the component
            memory_mb: Memory usage in MB
            category: Component category
            tags: Additional tags
        """
        self._tracker.record_metric(
            MetricType.MEMORY_USAGE, component_name, memory_mb, "MB", category, tags
        )
    
    def record_cache_performance(self, cache_name: str, hit_rate: float,
                               category: str = "", tags: Optional[Dict[str, str]] = None) -> None:
        """Record cache performance.
        
        Args:
            cache_name: Name of the cache
            hit_rate: Cache hit rate percentage
            category: Cache category
            tags: Additional tags
        """
        self._tracker.record_metric(
            MetricType.CACHE_HIT_RATE, cache_name, hit_rate, "%", category, tags
        )
    
    def record_api_call(self, api_name: str, response_time_ms: float, success: bool = True,
                       category: str = "", tags: Optional[Dict[str, str]] = None) -> None:
        """Record API call performance.
        
        Args:
            api_name: Name of the API
            response_time_ms: Response time in milliseconds
            success: Whether the call was successful
            category: API category
            tags: Additional tags
        """
        self._tracker.record_metric(
            MetricType.API_CALLS, f"{api_name}_response_time", response_time_ms, "ms", category, tags
        )
        
        if not success:
            self._tracker.record_metric(
                MetricType.ERROR_RATE, f"{api_name}_error", 1, "count", category, tags
            )
    
    def generate_performance_report(self, time_range_hours: float = 24.0) -> PerformanceReport:
        """Generate comprehensive performance report.
        
        Args:
            time_range_hours: Time range for the report
            
        Returns:
            Performance report
        """
        end_time = time.time()
        start_time = end_time - (time_range_hours * 3600)
        
        report = PerformanceReport(
            start_time=start_time,
            end_time=end_time,
            duration_seconds=time_range_hours * 3600
        )
        
        # Cache performance
        cache_hit_rates = self._tracker.get_metrics(MetricType.CACHE_HIT_RATE, time_range_hours * 3600)
        if cache_hit_rates:
            report.cache_hit_rate = sum(m.value for m in cache_hit_rates) / len(cache_hit_rates)
        
        # Memory optimization
        memory_metrics = self._tracker.get_metrics(MetricType.MEMORY_USAGE, time_range_hours * 3600)
        if memory_metrics:
            current_memory = self._tracker.get_average(MetricType.MEMORY_USAGE, "memory_percent", 3600)
            baseline_memory = self._tracker._baseline_metrics.get("memory_percent")
            
            if current_memory and baseline_memory:
                report.memory_usage_reduction_mb = baseline_memory - current_memory
                report.memory_peak_reduction_percent = ((baseline_memory - current_memory) / baseline_memory) * 100
        
        # API optimization
        api_metrics = self._tracker.get_metrics(MetricType.API_CALLS, time_range_hours * 3600)
        if api_metrics:
            response_times = [m.value for m in api_metrics if 'response_time' in m.name]
            if response_times:
                current_avg = sum(response_times) / len(response_times)
                baseline_avg = self._tracker._baseline_metrics.get("api_response_time")
                
                if baseline_avg:
                    report.api_response_time_improvement = ((baseline_avg - current_avg) / baseline_avg) * 100
        
        # Calculate overall performance improvement
        improvements = [
            report.cache_hit_rate,
            report.memory_peak_reduction_percent,
            report.api_response_time_improvement
        ]
        
        valid_improvements = [imp for imp in improvements if imp > 0]
        if valid_improvements:
            report.overall_performance_improvement = sum(valid_improvements) / len(valid_improvements)
        
        # User experience score (composite metric)
        ux_factors = [
            min(report.cache_hit_rate / 100, 1.0),  # Normalize to 0-1
            min(report.memory_peak_reduction_percent / 50, 1.0),  # 50% reduction = perfect
            min(report.api_response_time_improvement / 50, 1.0)   # 50% improvement = perfect
        ]
        
        report.user_experience_score = (sum(ux_factors) / len(ux_factors)) * 100
        
        return report
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time performance statistics.
        
        Returns:
            Real-time statistics
        """
        current_system = SystemMetrics.collect()
        
        # Recent metrics (last 5 minutes)
        recent_metrics = {}
        for metric_type in MetricType:
            metrics = self._tracker.get_metrics(metric_type, 300)  # 5 minutes
            if metrics:
                values = [m.value for m in metrics]
                recent_metrics[metric_type.value] = {
                    'current': values[-1] if values else 0,
                    'avg': sum(values) / len(values),
                    'trend': 'improving' if len(values) > 1 and values[-1] < values[0] else 'stable'
                }
        
        return {
            'timestamp': time.time(),
            'system_metrics': asdict(current_system),
            'recent_performance': recent_metrics,
            'baseline_collected': self._baseline_collected,
            'monitoring_active': self._monitoring_active,
            'registered_services': {
                'cache_services': len([ref for ref in self._cache_services if ref() is not None]),
                'optimization_services': len([ref for ref in self._optimization_services if ref() is not None])
            }
        }
    
    def optimize_monitoring(self) -> Dict[str, Any]:
        """Optimize monitoring performance.
        
        Returns:
            Optimization results
        """
        optimization_results = {
            'start_time': time.time(),
            'actions_taken': []
        }
        
        # Clean up dead service references
        initial_cache_count = len(self._cache_services)
        self._cache_services = [ref for ref in self._cache_services if ref() is not None]
        removed_cache = initial_cache_count - len(self._cache_services)
        
        initial_opt_count = len(self._optimization_services)
        self._optimization_services = [ref for ref in self._optimization_services if ref() is not None]
        removed_opt = initial_opt_count - len(self._optimization_services)
        
        if removed_cache > 0:
            optimization_results['actions_taken'].append(f"Cleaned up {removed_cache} dead cache service references")
        
        if removed_opt > 0:
            optimization_results['actions_taken'].append(f"Cleaned up {removed_opt} dead optimization service references")
        
        # Trigger garbage collection
        gc.collect()
        optimization_results['actions_taken'].append("Triggered garbage collection")
        
        optimization_results['end_time'] = time.time()
        optimization_results['duration'] = optimization_results['end_time'] - optimization_results['start_time']
        
        return optimization_results
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5.0)
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics.
        
        Returns:
            Comprehensive statistics
        """
        return {
            'tracker_stats': self._tracker.get_stats(),
            'real_time_stats': self.get_real_time_stats(),
            'system_metrics_history_count': len(self._system_metrics_history),
            'monitoring_interval': self.monitoring_interval,
            'baseline_collection_time': self._baseline_collection_time
        }


# Decorators for performance monitoring
def measure_performance(func: Callable) -> Callable:
    """Decorator to measure function performance and log slow operations.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function with performance measurement
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        if duration > 0.1:  # Log slow operations
            logger = logging.getLogger(__name__)
            logger.warning(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper


def monitor_performance(operation_name: str, category: str = ""):
    """Decorator to monitor operation performance.
    
    Args:
        operation_name: Name of the operation
        category: Operation category
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                monitor.record_operation_time(
                    operation_name=operation_name,
                    duration_ms=duration_ms,
                    category=category,
                    tags={'success': 'true'}
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                monitor.record_operation_time(
                    operation_name=operation_name,
                    duration_ms=duration_ms,
                    category=category,
                    tags={'success': 'false', 'error': str(e)}
                )
                
                raise
        
        return wrapper
    
    return decorator


def monitor_memory_usage(component_name: str, category: str = ""):
    """Decorator to monitor memory usage.
    
    Args:
        component_name: Name of the component
        category: Component category
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            
            # Get memory before
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            try:
                result = func(*args, **kwargs)
                
                # Get memory after
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_used = memory_after - memory_before
                
                monitor.record_memory_usage(
                    component_name=component_name,
                    memory_mb=memory_used,
                    category=category,
                    tags={'success': 'true'}
                )
                
                return result
                
            except Exception as e:
                # Still record memory usage on error
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_used = memory_after - memory_before
                
                monitor.record_memory_usage(
                    component_name=component_name,
                    memory_mb=memory_used,
                    category=category,
                    tags={'success': 'false', 'error': str(e)}
                )
                
                raise
        
        return wrapper
    
    return decorator


# Global performance monitor instance
_global_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance.
    
    Returns:
        Performance monitor instance
    """
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor