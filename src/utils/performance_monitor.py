"""Performance Monitor for Async Loading System.

Tracks and analyzes performance metrics for the async loading system
to help optimize startup times and identify bottlenecks.
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import json
from pathlib import Path


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def finish(self, success: bool = True, error: Optional[str] = None):
        """Mark the metric as finished."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'success': self.success,
            'error': self.error,
            'metadata': self.metadata
        }


class PerformanceMonitor:
    """Monitors and tracks performance metrics for async loading."""
    
    def __init__(self, enabled: bool = True):
        """Initialize the performance monitor.
        
        Args:
            enabled: Whether monitoring is enabled
        """
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)
        
        # Metrics storage
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.completed_metrics: List[PerformanceMetric] = []
        
        # Statistics
        self.session_start_time = time.time()
        self.total_loading_time = 0.0
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Performance thresholds (seconds)
        self.thresholds = {
            'critical_service': 5.0,
            'high_priority_service': 10.0,
            'normal_service': 15.0,
            'low_priority_service': 25.0,
            'total_startup': 30.0
        }
        
        if self.enabled:
            self.logger.info("Performance monitoring enabled")
    
    def start_metric(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start tracking a performance metric.
        
        Args:
            name: Name of the metric
            metadata: Optional metadata to store with the metric
            
        Returns:
            Metric ID for later reference
        """
        if not self.enabled:
            return name
        
        with self._lock:
            metric = PerformanceMetric(
                name=name,
                start_time=time.time(),
                metadata=metadata or {}
            )
            
            self.metrics[name] = metric
            self.logger.debug(f"Started tracking metric: {name}")
            
            return name
    
    def finish_metric(self, name: str, success: bool = True, error: Optional[str] = None):
        """Finish tracking a performance metric.
        
        Args:
            name: Name of the metric
            success: Whether the operation was successful
            error: Error message if operation failed
        """
        if not self.enabled:
            return
        
        with self._lock:
            if name not in self.metrics:
                self.logger.warning(f"Metric {name} not found for finishing")
                return
            
            metric = self.metrics[name]
            metric.finish(success=success, error=error)
            
            # Move to completed metrics
            self.completed_metrics.append(metric)
            del self.metrics[name]
            
            # Log performance
            if metric.duration:
                if success:
                    self.logger.info(f"Metric {name} completed in {metric.duration:.3f}s")
                else:
                    self.logger.warning(f"Metric {name} failed after {metric.duration:.3f}s: {error}")
                
                # Check against thresholds
                self._check_threshold(metric)
    
    def _check_threshold(self, metric: PerformanceMetric):
        """Check if metric exceeds performance thresholds.
        
        Args:
            metric: The completed metric to check
        """
        if not metric.duration:
            return
        
        # Determine threshold based on metric name
        threshold_key = None
        if 'critical' in metric.name.lower():
            threshold_key = 'critical_service'
        elif 'high' in metric.name.lower():
            threshold_key = 'high_priority_service'
        elif 'normal' in metric.name.lower():
            threshold_key = 'normal_service'
        elif 'low' in metric.name.lower():
            threshold_key = 'low_priority_service'
        elif 'startup' in metric.name.lower() or 'total' in metric.name.lower():
            threshold_key = 'total_startup'
        
        if threshold_key and threshold_key in self.thresholds:
            threshold = self.thresholds[threshold_key]
            if metric.duration > threshold:
                self.logger.warning(
                    f"Performance threshold exceeded: {metric.name} took {metric.duration:.3f}s "
                    f"(threshold: {threshold:.1f}s)"
                )
    
    def add_metadata(self, name: str, key: str, value: Any):
        """Add metadata to an active metric.
        
        Args:
            name: Name of the metric
            key: Metadata key
            value: Metadata value
        """
        if not self.enabled:
            return
        
        with self._lock:
            if name in self.metrics:
                self.metrics[name].metadata[key] = value
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """Get a summary of all performance metrics.
        
        Returns:
            Dictionary with performance summary
        """
        if not self.enabled:
            return {'enabled': False}
        
        with self._lock:
            # Calculate statistics
            total_metrics = len(self.completed_metrics)
            successful_metrics = sum(1 for m in self.completed_metrics if m.success)
            failed_metrics = total_metrics - successful_metrics
            
            # Calculate durations
            durations = [m.duration for m in self.completed_metrics if m.duration]
            avg_duration = sum(durations) / len(durations) if durations else 0
            max_duration = max(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            
            # Session time
            session_duration = time.time() - self.session_start_time
            
            # Group by category
            categories = defaultdict(list)
            for metric in self.completed_metrics:
                category = self._get_metric_category(metric.name)
                categories[category].append(metric)
            
            category_stats = {}
            for category, metrics in categories.items():
                cat_durations = [m.duration for m in metrics if m.duration]
                category_stats[category] = {
                    'count': len(metrics),
                    'avg_duration': sum(cat_durations) / len(cat_durations) if cat_durations else 0,
                    'total_duration': sum(cat_durations),
                    'success_rate': sum(1 for m in metrics if m.success) / len(metrics) if metrics else 0
                }
            
            return {
                'enabled': True,
                'session_duration': session_duration,
                'total_metrics': total_metrics,
                'successful_metrics': successful_metrics,
                'failed_metrics': failed_metrics,
                'success_rate': successful_metrics / total_metrics if total_metrics > 0 else 0,
                'avg_duration': avg_duration,
                'max_duration': max_duration,
                'min_duration': min_duration,
                'total_loading_time': sum(durations),
                'category_stats': category_stats,
                'active_metrics': len(self.metrics)
            }
    
    def _get_metric_category(self, name: str) -> str:
        """Get category for a metric based on its name.
        
        Args:
            name: Metric name
            
        Returns:
            Category string
        """
        name_lower = name.lower()
        
        if 'service' in name_lower:
            if 'critical' in name_lower:
                return 'critical_services'
            elif 'high' in name_lower:
                return 'high_priority_services'
            elif 'normal' in name_lower:
                return 'normal_services'
            elif 'low' in name_lower:
                return 'low_priority_services'
            else:
                return 'services'
        elif 'ui' in name_lower or 'skeleton' in name_lower:
            return 'ui_components'
        elif 'data' in name_lower or 'api' in name_lower:
            return 'data_loading'
        elif 'startup' in name_lower or 'initialization' in name_lower:
            return 'startup'
        else:
            return 'other'
    
    def get_slow_metrics(self, threshold: float = 5.0) -> List[PerformanceMetric]:
        """Get metrics that exceeded a duration threshold.
        
        Args:
            threshold: Duration threshold in seconds
            
        Returns:
            List of slow metrics
        """
        if not self.enabled:
            return []
        
        with self._lock:
            return [
                metric for metric in self.completed_metrics
                if metric.duration and metric.duration > threshold
            ]
    
    def get_failed_metrics(self) -> List[PerformanceMetric]:
        """Get metrics that failed.
        
        Returns:
            List of failed metrics
        """
        if not self.enabled:
            return []
        
        with self._lock:
            return [metric for metric in self.completed_metrics if not metric.success]
    
    def export_metrics(self, file_path: Optional[str] = None) -> str:
        """Export metrics to JSON file.
        
        Args:
            file_path: Optional file path, defaults to performance_metrics.json
            
        Returns:
            Path to the exported file
        """
        if not self.enabled:
            return ""
        
        if not file_path:
            file_path = f"performance_metrics_{int(time.time())}.json"
        
        with self._lock:
            export_data = {
                'session_info': {
                    'start_time': self.session_start_time,
                    'export_time': time.time(),
                    'session_duration': time.time() - self.session_start_time
                },
                'summary': self.get_metric_summary(),
                'metrics': [metric.to_dict() for metric in self.completed_metrics],
                'thresholds': self.thresholds
            }
            
            try:
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                self.logger.info(f"Performance metrics exported to {file_path}")
                return file_path
                
            except Exception as e:
                self.logger.error(f"Failed to export metrics: {e}")
                return ""
    
    def log_summary(self):
        """Log a performance summary."""
        if not self.enabled:
            return
        
        summary = self.get_metric_summary()
        
        self.logger.info("=== Performance Summary ===")
        self.logger.info(f"Session Duration: {summary['session_duration']:.2f}s")
        self.logger.info(f"Total Metrics: {summary['total_metrics']}")
        self.logger.info(f"Success Rate: {summary['success_rate']:.1%}")
        self.logger.info(f"Average Duration: {summary['avg_duration']:.3f}s")
        self.logger.info(f"Total Loading Time: {summary['total_loading_time']:.2f}s")
        
        # Log slow metrics
        slow_metrics = self.get_slow_metrics()
        if slow_metrics:
            self.logger.warning(f"Slow metrics ({len(slow_metrics)}):")
            for metric in slow_metrics[:5]:  # Show top 5
                self.logger.warning(f"  {metric.name}: {metric.duration:.3f}s")
        
        # Log failed metrics
        failed_metrics = self.get_failed_metrics()
        if failed_metrics:
            self.logger.error(f"Failed metrics ({len(failed_metrics)}):")
            for metric in failed_metrics[:5]:  # Show top 5
                self.logger.error(f"  {metric.name}: {metric.error}")
        
        self.logger.info("=== End Performance Summary ===")
    
    def cleanup(self):
        """Clean up resources."""
        if not self.enabled:
            return
        
        with self._lock:
            # Log final summary
            self.log_summary()
            
            # Clear metrics
            self.metrics.clear()
            self.completed_metrics.clear()
            
            self.logger.info("Performance monitor cleanup completed")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance.
    
    Returns:
        Global PerformanceMonitor instance
    """
    global _performance_monitor
    
    if _performance_monitor is None:
        import os
        enabled = os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true'
        _performance_monitor = PerformanceMonitor(enabled=enabled)
    
    return _performance_monitor


def start_metric(name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Start tracking a performance metric (convenience function).
    
    Args:
        name: Name of the metric
        metadata: Optional metadata
        
    Returns:
        Metric ID
    """
    return get_performance_monitor().start_metric(name, metadata)


def finish_metric(name: str, success: bool = True, error: Optional[str] = None):
    """Finish tracking a performance metric (convenience function).
    
    Args:
        name: Name of the metric
        success: Whether the operation was successful
        error: Error message if operation failed
    """
    get_performance_monitor().finish_metric(name, success, error)


def log_performance_summary():
    """Log performance summary (convenience function)."""
    get_performance_monitor().log_summary()