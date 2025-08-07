"""Chart optimization service for efficient matplotlib figure caching and rendering.

Provides chart caching, rendering optimization, and memory management.
"""

import io
import os
import time
import hashlib
import threading
import logging
import pickle
import gc
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Type
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps, lru_cache
from enum import Enum
import weakref

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    matplotlib = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


class ChartType(Enum):
    """Supported chart types."""
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    PIE = "pie"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    BOX = "box"
    AREA = "area"
    POLAR = "polar"
    CUSTOM = "custom"


class OutputFormat(Enum):
    """Chart output formats."""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    JPEG = "jpeg"
    WEBP = "webp"


@dataclass
class ChartStats:
    """Chart rendering statistics."""
    total_rendered: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_render_time: float = 0.0
    avg_render_time: float = 0.0
    memory_usage_mb: float = 0.0
    chart_type_counts: Dict[ChartType, int] = field(default_factory=lambda: defaultdict(int))
    format_counts: Dict[OutputFormat, int] = field(default_factory=lambda: defaultdict(int))
    figure_count: int = 0
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            return 0.0
        return (self.cache_hits / total_requests) * 100
    
    def update_rendering(self, chart_type: ChartType, output_format: OutputFormat,
                        render_time: float, from_cache: bool = False) -> None:
        """Update rendering statistics.
        
        Args:
            chart_type: Type of chart
            output_format: Output format
            render_time: Rendering time
            from_cache: Whether result came from cache
        """
        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            self.total_rendered += 1
            self.total_render_time += render_time
            self.avg_render_time = self.total_render_time / self.total_rendered
            self.chart_type_counts[chart_type] += 1
            self.format_counts[output_format] += 1


@dataclass
class ChartCacheEntry:
    """Chart cache entry."""
    chart_data: bytes
    format: OutputFormat
    size: Tuple[int, int]  # width, height in pixels
    chart_params: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    render_time: float = 0.0
    
    @property
    def size_mb(self) -> float:
        """Get size in MB."""
        return len(self.chart_data) / 1024 / 1024
    
    @property
    def age_seconds(self) -> float:
        """Get age in seconds."""
        return time.time() - self.timestamp
    
    def access(self) -> None:
        """Mark as accessed."""
        self.access_count += 1
        self.last_accessed = time.time()


class ChartCache:
    """Cache for rendered charts."""
    
    def __init__(self, 
                 max_size_mb: float = 200.0,
                 max_entries: int = 1000,
                 ttl_seconds: float = 7200.0):  # 2 hours default
        """
        Initialize chart cache.
        
        Args:
            max_size_mb: Maximum cache size in MB
            max_entries: Maximum number of cache entries
            ttl_seconds: Time-to-live for cached charts
        """
        self.max_size_mb = max_size_mb
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        
        self._cache: Dict[str, ChartCacheEntry] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def _generate_key(self, chart_params: Dict[str, Any]) -> str:
        """Generate cache key for chart.
        
        Args:
            chart_params: Chart parameters
            
        Returns:
            Cache key
        """
        # Create a deterministic key from parameters
        # Convert numpy arrays to lists for hashing
        hashable_params = self._make_hashable(chart_params)
        
        key_str = str(hashable_params)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _make_hashable(self, obj: Any) -> Any:
        """Convert object to hashable form.
        
        Args:
            obj: Object to convert
            
        Returns:
            Hashable representation
        """
        if isinstance(obj, dict):
            return tuple(sorted((k, self._make_hashable(v)) for k, v in obj.items()))
        elif isinstance(obj, list):
            return tuple(self._make_hashable(item) for item in obj)
        elif isinstance(obj, tuple):
            return tuple(self._make_hashable(item) for item in obj)
        elif NUMPY_AVAILABLE and isinstance(obj, np.ndarray):
            return tuple(obj.flatten().tolist())
        elif hasattr(obj, '__dict__'):
            return self._make_hashable(obj.__dict__)
        else:
            return obj
    
    def get(self, chart_params: Dict[str, Any]) -> Optional[bytes]:
        """Get cached chart.
        
        Args:
            chart_params: Chart parameters
            
        Returns:
            Cached chart data or None
        """
        key = self._generate_key(chart_params)
        
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if entry is still valid
                if entry.age_seconds < self.ttl_seconds:
                    entry.access()
                    return entry.chart_data
                else:
                    # Remove expired entry
                    del self._cache[key]
        
        return None
    
    def set(self, chart_params: Dict[str, Any], chart_data: bytes, 
           format: OutputFormat, size: Tuple[int, int], render_time: float) -> None:
        """Cache rendered chart.
        
        Args:
            chart_params: Chart parameters
            chart_data: Rendered chart data
            format: Output format
            size: Chart size
            render_time: Time taken to render
        """
        key = self._generate_key(chart_params)
        
        entry = ChartCacheEntry(
            chart_data=chart_data,
            format=format,
            size=size,
            chart_params=chart_params,
            render_time=render_time
        )
        
        with self._lock:
            # Check if we need to make space
            self._ensure_space(entry.size_mb)
            
            self._cache[key] = entry
    
    def _ensure_space(self, required_mb: float) -> None:
        """Ensure there's enough space in cache.
        
        Args:
            required_mb: Required space in MB
        """
        current_size = self.get_size_mb()
        
        # Remove entries if cache is too full
        while (len(self._cache) >= self.max_entries or 
               current_size + required_mb > self.max_size_mb):
            
            if not self._cache:
                break
            
            # Find least recently used entry
            lru_key = min(self._cache.keys(), 
                         key=lambda k: self._cache[k].last_accessed)
            
            removed_entry = self._cache.pop(lru_key)
            current_size -= removed_entry.size_mb
    
    def get_size_mb(self) -> float:
        """Get current cache size in MB.
        
        Returns:
            Cache size in MB
        """
        with self._lock:
            return sum(entry.size_mb for entry in self._cache.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        with self._lock:
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            avg_render_time = sum(entry.render_time for entry in self._cache.values()) / len(self._cache) if self._cache else 0
            
            return {
                'entries': len(self._cache),
                'max_entries': self.max_entries,
                'size_mb': self.get_size_mb(),
                'max_size_mb': self.max_size_mb,
                'utilization_percent': (len(self._cache) / self.max_entries) * 100,
                'size_utilization_percent': (self.get_size_mb() / self.max_size_mb) * 100,
                'total_accesses': total_accesses,
                'avg_render_time': avg_render_time,
                'ttl_seconds': self.ttl_seconds
            }
    
    def clear(self) -> None:
        """Clear all cached charts."""
        with self._lock:
            self._cache.clear()
    
    def _cleanup_loop(self) -> None:
        """Cleanup expired entries periodically."""
        while True:
            try:
                time.sleep(600)  # Check every 10 minutes
                
                current_time = time.time()
                expired_keys = []
                
                with self._lock:
                    for key, entry in self._cache.items():
                        if entry.age_seconds > self.ttl_seconds:
                            expired_keys.append(key)
                
                # Remove expired entries
                if expired_keys:
                    with self._lock:
                        for key in expired_keys:
                            if key in self._cache:
                                del self._cache[key]
                    
                    self._logger.debug(f"Cleaned up {len(expired_keys)} expired chart cache entries")
                
            except Exception as e:
                self._logger.error(f"Error in chart cache cleanup: {e}")


class FigureManager:
    """Manager for matplotlib figures with memory optimization."""
    
    def __init__(self, max_figures: int = 50):
        """
        Initialize figure manager.
        
        Args:
            max_figures: Maximum number of figures to keep in memory
        """
        self.max_figures = max_figures
        self._figures: Dict[str, weakref.ref] = {}
        self._figure_queue = deque()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
    
    def create_figure(self, name: str, figsize: Tuple[float, float] = (10, 6), 
                     dpi: int = 100, **kwargs) -> 'matplotlib.figure.Figure':
        """Create a new figure.
        
        Args:
            name: Figure name
            figsize: Figure size in inches
            dpi: Dots per inch
            **kwargs: Additional figure arguments
            
        Returns:
            Matplotlib figure
        """
        if not MATPLOTLIB_AVAILABLE:
            raise RuntimeError("Matplotlib is required for chart rendering")
        
        # Clean up old figures if needed
        self._cleanup_figures()
        
        # Create new figure
        fig = plt.figure(figsize=figsize, dpi=dpi, **kwargs)
        
        # Register weak reference
        def cleanup_callback(ref):
            with self._lock:
                if name in self._figures:
                    del self._figures[name]
                if name in self._figure_queue:
                    self._figure_queue.remove(name)
            self._logger.debug(f"Figure '{name}' was garbage collected")
        
        with self._lock:
            self._figures[name] = weakref.ref(fig, cleanup_callback)
            self._figure_queue.append(name)
        
        return fig
    
    def get_figure(self, name: str) -> Optional['matplotlib.figure.Figure']:
        """Get figure by name.
        
        Args:
            name: Figure name
            
        Returns:
            Figure or None
        """
        with self._lock:
            if name in self._figures:
                fig = self._figures[name]()
                if fig is not None:
                    # Move to end of queue (most recently used)
                    if name in self._figure_queue:
                        self._figure_queue.remove(name)
                    self._figure_queue.append(name)
                    return fig
                else:
                    # Clean up dead reference
                    del self._figures[name]
        
        return None
    
    def close_figure(self, name: str) -> None:
        """Close and remove figure.
        
        Args:
            name: Figure name
        """
        with self._lock:
            if name in self._figures:
                fig = self._figures[name]()
                if fig is not None:
                    plt.close(fig)
                del self._figures[name]
            
            if name in self._figure_queue:
                self._figure_queue.remove(name)
    
    def _cleanup_figures(self) -> None:
        """Clean up old figures to stay within limits."""
        with self._lock:
            # Remove dead references
            dead_names = []
            for name, ref in self._figures.items():
                if ref() is None:
                    dead_names.append(name)
            
            for name in dead_names:
                del self._figures[name]
                if name in self._figure_queue:
                    self._figure_queue.remove(name)
            
            # Close oldest figures if over limit
            while len(self._figures) >= self.max_figures and self._figure_queue:
                oldest_name = self._figure_queue.popleft()
                if oldest_name in self._figures:
                    fig = self._figures[oldest_name]()
                    if fig is not None:
                        plt.close(fig)
                    del self._figures[oldest_name]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get figure manager statistics.
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            alive_figures = sum(1 for ref in self._figures.values() if ref() is not None)
            
            return {
                'total_figures': len(self._figures),
                'alive_figures': alive_figures,
                'max_figures': self.max_figures,
                'utilization_percent': (alive_figures / self.max_figures) * 100
            }
    
    def clear_all(self) -> None:
        """Close and clear all figures."""
        with self._lock:
            for name, ref in self._figures.items():
                fig = ref()
                if fig is not None:
                    plt.close(fig)
            
            self._figures.clear()
            self._figure_queue.clear()
            
            # Force garbage collection
            gc.collect()


class ChartRenderer:
    """Optimized chart renderer with caching."""
    
    def __init__(self, cache: Optional[ChartCache] = None,
                 figure_manager: Optional[FigureManager] = None):
        """
        Initialize chart renderer.
        
        Args:
            cache: Chart cache instance
            figure_manager: Figure manager instance
        """
        self._cache = cache or ChartCache()
        self._figure_manager = figure_manager or FigureManager()
        self._stats = ChartStats()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        if not MATPLOTLIB_AVAILABLE:
            self._logger.warning("Matplotlib not available, chart rendering will be limited")
    
    def _check_matplotlib_available(self) -> None:
        """Check if matplotlib is available."""
        if not MATPLOTLIB_AVAILABLE:
            raise RuntimeError("Matplotlib is required for chart rendering")
    
    def render_chart(self, chart_type: ChartType, data: Dict[str, Any],
                    style_params: Optional[Dict[str, Any]] = None,
                    output_format: OutputFormat = OutputFormat.PNG,
                    use_cache: bool = True) -> bytes:
        """Render chart with caching.
        
        Args:
            chart_type: Type of chart to render
            data: Chart data
            style_params: Style parameters
            output_format: Output format
            use_cache: Whether to use cache
            
        Returns:
            Rendered chart data
        """
        start_time = time.time()
        
        # Prepare chart parameters
        chart_params = {
            'chart_type': chart_type.value,
            'data': data,
            'style_params': style_params or {},
            'output_format': output_format.value
        }
        
        # Check cache first
        if use_cache:
            cached_data = self._cache.get(chart_params)
            if cached_data is not None:
                render_time = time.time() - start_time
                with self._lock:
                    self._stats.update_rendering(chart_type, output_format, render_time, from_cache=True)
                return cached_data
        
        try:
            # Render chart
            chart_data = self._render_chart_internal(chart_type, data, style_params, output_format)
            
            render_time = time.time() - start_time
            
            # Cache result
            if use_cache:
                # Estimate size (width, height) - this would be more accurate with actual figure
                estimated_size = (800, 600)  # Default size
                self._cache.set(chart_params, chart_data, output_format, estimated_size, render_time)
            
            with self._lock:
                self._stats.update_rendering(chart_type, output_format, render_time, from_cache=False)
            
            return chart_data
            
        except Exception as e:
            self._logger.error(f"Chart rendering failed: {e}")
            raise
    
    def _render_chart_internal(self, chart_type: ChartType, data: Dict[str, Any],
                              style_params: Optional[Dict[str, Any]],
                              output_format: OutputFormat) -> bytes:
        """Internal chart rendering method.
        
        Args:
            chart_type: Type of chart
            data: Chart data
            style_params: Style parameters
            output_format: Output format
            
        Returns:
            Rendered chart data
        """
        self._check_matplotlib_available()
        
        style_params = style_params or {}
        
        # Create figure
        figsize = style_params.get('figsize', (10, 6))
        dpi = style_params.get('dpi', 100)
        
        fig_name = f"chart_{int(time.time() * 1000000)}"
        fig = self._figure_manager.create_figure(fig_name, figsize=figsize, dpi=dpi)
        
        try:
            ax = fig.add_subplot(111)
            
            # Render based on chart type
            if chart_type == ChartType.LINE:
                self._render_line_chart(ax, data, style_params)
            elif chart_type == ChartType.BAR:
                self._render_bar_chart(ax, data, style_params)
            elif chart_type == ChartType.SCATTER:
                self._render_scatter_chart(ax, data, style_params)
            elif chart_type == ChartType.PIE:
                self._render_pie_chart(ax, data, style_params)
            elif chart_type == ChartType.HISTOGRAM:
                self._render_histogram(ax, data, style_params)
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            # Apply common styling
            self._apply_common_styling(ax, style_params)
            
            # Convert to bytes
            output = io.BytesIO()
            fig.savefig(output, format=output_format.value, 
                       bbox_inches='tight', dpi=dpi)
            chart_data = output.getvalue()
            
            return chart_data
            
        finally:
            # Clean up figure
            self._figure_manager.close_figure(fig_name)
    
    def _render_line_chart(self, ax, data: Dict[str, Any], style_params: Dict[str, Any]) -> None:
        """Render line chart.
        
        Args:
            ax: Matplotlib axes
            data: Chart data
            style_params: Style parameters
        """
        x_data = data.get('x', [])
        y_data = data.get('y', [])
        
        line_style = style_params.get('line_style', '-')
        line_width = style_params.get('line_width', 2)
        color = style_params.get('color', 'blue')
        
        ax.plot(x_data, y_data, linestyle=line_style, linewidth=line_width, color=color)
    
    def _render_bar_chart(self, ax, data: Dict[str, Any], style_params: Dict[str, Any]) -> None:
        """Render bar chart.
        
        Args:
            ax: Matplotlib axes
            data: Chart data
            style_params: Style parameters
        """
        x_data = data.get('x', [])
        y_data = data.get('y', [])
        
        color = style_params.get('color', 'blue')
        alpha = style_params.get('alpha', 0.7)
        
        ax.bar(x_data, y_data, color=color, alpha=alpha)
    
    def _render_scatter_chart(self, ax, data: Dict[str, Any], style_params: Dict[str, Any]) -> None:
        """Render scatter chart.
        
        Args:
            ax: Matplotlib axes
            data: Chart data
            style_params: Style parameters
        """
        x_data = data.get('x', [])
        y_data = data.get('y', [])
        
        color = style_params.get('color', 'blue')
        size = style_params.get('size', 50)
        alpha = style_params.get('alpha', 0.7)
        
        ax.scatter(x_data, y_data, c=color, s=size, alpha=alpha)
    
    def _render_pie_chart(self, ax, data: Dict[str, Any], style_params: Dict[str, Any]) -> None:
        """Render pie chart.
        
        Args:
            ax: Matplotlib axes
            data: Chart data
            style_params: Style parameters
        """
        values = data.get('values', [])
        labels = data.get('labels', [])
        
        colors = style_params.get('colors', None)
        autopct = style_params.get('autopct', '%1.1f%%')
        
        ax.pie(values, labels=labels, colors=colors, autopct=autopct)
    
    def _render_histogram(self, ax, data: Dict[str, Any], style_params: Dict[str, Any]) -> None:
        """Render histogram.
        
        Args:
            ax: Matplotlib axes
            data: Chart data
            style_params: Style parameters
        """
        values = data.get('values', [])
        bins = style_params.get('bins', 30)
        color = style_params.get('color', 'blue')
        alpha = style_params.get('alpha', 0.7)
        
        ax.hist(values, bins=bins, color=color, alpha=alpha)
    
    def _apply_common_styling(self, ax, style_params: Dict[str, Any]) -> None:
        """Apply common styling to chart.
        
        Args:
            ax: Matplotlib axes
            style_params: Style parameters
        """
        # Set title
        title = style_params.get('title')
        if title:
            ax.set_title(title, fontsize=style_params.get('title_fontsize', 14))
        
        # Set labels
        xlabel = style_params.get('xlabel')
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=style_params.get('label_fontsize', 12))
        
        ylabel = style_params.get('ylabel')
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=style_params.get('label_fontsize', 12))
        
        # Grid
        if style_params.get('grid', False):
            ax.grid(True, alpha=0.3)
        
        # Legend
        if style_params.get('legend', False):
            ax.legend()
    
    def get_stats(self) -> ChartStats:
        """Get rendering statistics.
        
        Returns:
            Chart rendering statistics
        """
        with self._lock:
            # Update memory usage and figure count
            self._stats.memory_usage_mb = self._cache.get_size_mb()
            figure_stats = self._figure_manager.get_stats()
            self._stats.figure_count = figure_stats['alive_figures']
            return self._stats
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        return self._cache.get_stats()
    
    def get_figure_stats(self) -> Dict[str, Any]:
        """Get figure manager statistics.
        
        Returns:
            Figure manager statistics
        """
        return self._figure_manager.get_stats()
    
    def clear_cache(self) -> None:
        """Clear chart cache."""
        self._cache.clear()
        self._logger.info("Chart cache cleared")
    
    def clear_figures(self) -> None:
        """Clear all figures."""
        self._figure_manager.clear_all()
        self._logger.info("All figures cleared")


class ChartOptimizer:
    """Service for chart optimization and management."""
    
    def __init__(self, 
                 cache_size_mb: float = 200.0,
                 max_cache_entries: int = 1000,
                 cache_ttl: float = 7200.0,
                 max_figures: int = 50):
        """
        Initialize chart optimizer.
        
        Args:
            cache_size_mb: Maximum cache size in MB
            max_cache_entries: Maximum cache entries
            cache_ttl: Cache time-to-live in seconds
            max_figures: Maximum figures in memory
        """
        self._cache = ChartCache(
            max_size_mb=cache_size_mb,
            max_entries=max_cache_entries,
            ttl_seconds=cache_ttl
        )
        
        self._figure_manager = FigureManager(max_figures=max_figures)
        self._renderer = ChartRenderer(self._cache, self._figure_manager)
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
    
    def create_weather_chart(self, chart_type: str, weather_data: Dict[str, Any],
                           style_options: Optional[Dict[str, Any]] = None) -> bytes:
        """Create weather-specific chart.
        
        Args:
            chart_type: Type of weather chart
            weather_data: Weather data
            style_options: Style options
            
        Returns:
            Chart image data
        """
        # Map weather chart types to ChartType enum
        chart_type_mapping = {
            'temperature_line': ChartType.LINE,
            'precipitation_bar': ChartType.BAR,
            'humidity_area': ChartType.AREA,
            'wind_scatter': ChartType.SCATTER,
            'forecast_line': ChartType.LINE
        }
        
        chart_enum = chart_type_mapping.get(chart_type, ChartType.LINE)
        
        # Apply weather-specific styling
        default_style = {
            'figsize': (12, 6),
            'dpi': 100,
            'grid': True,
            'title_fontsize': 16,
            'label_fontsize': 12
        }
        
        if style_options:
            default_style.update(style_options)
        
        return self._renderer.render_chart(
            chart_type=chart_enum,
            data=weather_data,
            style_params=default_style,
            output_format=OutputFormat.PNG
        )
    
    def preload_common_charts(self, chart_configs: List[Dict[str, Any]]) -> None:
        """Preload common chart configurations.
        
        Args:
            chart_configs: List of chart configurations
        """
        for config in chart_configs:
            try:
                chart_type = ChartType(config.get('type', 'line'))
                data = config.get('data', {})
                style_params = config.get('style', {})
                
                # Render and cache
                self._renderer.render_chart(
                    chart_type=chart_type,
                    data=data,
                    style_params=style_params
                )
                
            except Exception as e:
                self._logger.warning(f"Failed to preload chart config: {e}")
    
    def cleanup_memory(self) -> Dict[str, Any]:
        """Clean up chart memory.
        
        Returns:
            Cleanup results
        """
        cleanup_results = {
            'start_time': time.time(),
            'actions_taken': []
        }
        
        # Get stats before cleanup
        cache_stats_before = self._cache.get_stats()
        figure_stats_before = self._figure_manager.get_stats()
        
        # Clear figures if memory usage is high
        if figure_stats_before['utilization_percent'] > 80:
            self._figure_manager.clear_all()
            cleanup_results['actions_taken'].append("Cleared all figures due to high memory usage")
        
        # Clear cache if memory usage is high
        if cache_stats_before['size_utilization_percent'] > 80:
            self._cache.clear()
            cleanup_results['actions_taken'].append("Cleared chart cache due to high memory usage")
        
        # Force garbage collection
        gc.collect()
        cleanup_results['actions_taken'].append("Forced garbage collection")
        
        cleanup_results['end_time'] = time.time()
        cleanup_results['duration'] = cleanup_results['end_time'] - cleanup_results['start_time']
        
        return cleanup_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive chart optimization statistics.
        
        Returns:
            Statistics dictionary
        """
        rendering_stats = self._renderer.get_stats()
        cache_stats = self._cache.get_stats()
        figure_stats = self._figure_manager.get_stats()
        
        return {
            'rendering_stats': {
                'total_rendered': rendering_stats.total_rendered,
                'cache_hit_rate': rendering_stats.cache_hit_rate,
                'avg_render_time': rendering_stats.avg_render_time,
                'chart_type_counts': dict(rendering_stats.chart_type_counts),
                'format_counts': dict(rendering_stats.format_counts)
            },
            'cache_stats': cache_stats,
            'figure_stats': figure_stats,
            'memory_stats': {
                'memory_usage_mb': rendering_stats.memory_usage_mb,
                'figure_count': rendering_stats.figure_count
            }
        }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Optimize chart rendering performance.
        
        Returns:
            Optimization results
        """
        optimization_results = {
            'start_time': time.time(),
            'actions_taken': []
        }
        
        # Clean up memory
        cleanup_result = self.cleanup_memory()
        optimization_results['actions_taken'].extend(cleanup_result['actions_taken'])
        
        # Set matplotlib to use optimal backend
        if MATPLOTLIB_AVAILABLE:
            matplotlib.use('Agg')
            optimization_results['actions_taken'].append("Set matplotlib to use Agg backend")
        
        optimization_results['end_time'] = time.time()
        optimization_results['duration'] = optimization_results['end_time'] - optimization_results['start_time']
        
        return optimization_results


# Decorators for chart optimization
def cached_chart(cache_ttl: float = 7200.0):
    """Decorator for caching chart rendering.
    
    Args:
        cache_ttl: Cache time-to-live
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would integrate with the chart optimizer
            # For now, just execute the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def memory_efficient_chart(max_figures: int = 10):
    """Decorator for memory-efficient chart rendering.
    
    Args:
        max_figures: Maximum figures to keep in memory
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would manage figure memory
            # For now, just execute the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Global chart optimizer instance
_global_chart_optimizer = None


def get_chart_optimizer() -> ChartOptimizer:
    """Get global chart optimizer instance.
    
    Returns:
        Chart optimizer instance
    """
    global _global_chart_optimizer
    if _global_chart_optimizer is None:
        _global_chart_optimizer = ChartOptimizer()
    return _global_chart_optimizer