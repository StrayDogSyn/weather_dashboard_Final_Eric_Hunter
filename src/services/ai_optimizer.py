"""AI response optimization service for efficient API response caching and management.

Provides caching for AI services like Gemini, Spotify, and other external APIs.
"""

import json
import time
import hashlib
import threading
import logging
import pickle
import gzip
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Type
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps, lru_cache
from enum import Enum
import weakref


class AIServiceType(Enum):
    """Supported AI service types."""
    GEMINI = "gemini"
    SPOTIFY = "spotify"
    OPENAI = "openai"
    WEATHER_AI = "weather_ai"
    CUSTOM = "custom"


class ResponseType(Enum):
    """AI response types."""
    TEXT_GENERATION = "text_generation"
    MUSIC_RECOMMENDATION = "music_recommendation"
    WEATHER_ANALYSIS = "weather_analysis"
    IMAGE_ANALYSIS = "image_analysis"
    SEARCH_RESULTS = "search_results"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    CUSTOM = "custom"


class CacheStrategy(Enum):
    """Cache strategies for different response types."""
    AGGRESSIVE = "aggressive"  # Long TTL, high compression
    MODERATE = "moderate"     # Medium TTL, medium compression
    CONSERVATIVE = "conservative"  # Short TTL, low compression
    DYNAMIC = "dynamic"       # TTL based on content analysis


@dataclass
class AIResponseStats:
    """AI response statistics."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    total_api_cost: float = 0.0
    service_counts: Dict[AIServiceType, int] = field(default_factory=lambda: defaultdict(int))
    response_type_counts: Dict[ResponseType, int] = field(default_factory=lambda: defaultdict(int))
    compression_savings_mb: float = 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            return 0.0
        return (self.cache_hits / total_requests) * 100
    
    @property
    def cost_savings(self) -> float:
        """Calculate cost savings from caching."""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * self.total_api_cost
    
    def update_request(self, service_type: AIServiceType, response_type: ResponseType,
                      response_time: float, api_cost: float = 0.0, from_cache: bool = False) -> None:
        """Update request statistics.
        
        Args:
            service_type: AI service type
            response_type: Response type
            response_time: Response time
            api_cost: API cost
            from_cache: Whether response came from cache
        """
        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            self.total_requests += 1
            self.total_response_time += response_time
            self.avg_response_time = self.total_response_time / self.total_requests
            self.total_api_cost += api_cost
            self.service_counts[service_type] += 1
            self.response_type_counts[response_type] += 1


@dataclass
class AIResponseEntry:
    """AI response cache entry."""
    response_data: bytes  # Compressed response data
    service_type: AIServiceType
    response_type: ResponseType
    request_params: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    ttl_seconds: float = 3600.0
    api_cost: float = 0.0
    compression_ratio: float = 1.0
    
    @property
    def size_mb(self) -> float:
        """Get size in MB."""
        return len(self.response_data) / 1024 / 1024
    
    @property
    def age_seconds(self) -> float:
        """Get age in seconds."""
        return time.time() - self.timestamp
    
    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return self.age_seconds > self.ttl_seconds
    
    def access(self) -> None:
        """Mark as accessed."""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def get_decompressed_data(self) -> Any:
        """Get decompressed response data.
        
        Returns:
            Decompressed response data
        """
        try:
            decompressed = gzip.decompress(self.response_data)
            return pickle.loads(decompressed)
        except Exception:
            # Fallback to non-compressed data
            return pickle.loads(self.response_data)


class AIResponseCache:
    """Cache for AI service responses."""
    
    def __init__(self, 
                 max_size_mb: float = 500.0,
                 max_entries: int = 10000,
                 default_ttl: float = 3600.0,
                 compression_enabled: bool = True):
        """
        Initialize AI response cache.
        
        Args:
            max_size_mb: Maximum cache size in MB
            max_entries: Maximum number of cache entries
            default_ttl: Default time-to-live for cached responses
            compression_enabled: Whether to enable compression
        """
        self.max_size_mb = max_size_mb
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.compression_enabled = compression_enabled
        
        self._cache: Dict[str, AIResponseEntry] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # TTL strategies for different response types
        self._ttl_strategies = {
            ResponseType.TEXT_GENERATION: 1800.0,      # 30 minutes
            ResponseType.MUSIC_RECOMMENDATION: 7200.0,  # 2 hours
            ResponseType.WEATHER_ANALYSIS: 900.0,       # 15 minutes
            ResponseType.IMAGE_ANALYSIS: 3600.0,        # 1 hour
            ResponseType.SEARCH_RESULTS: 600.0,         # 10 minutes
            ResponseType.TRANSLATION: 86400.0,          # 24 hours
            ResponseType.SUMMARIZATION: 3600.0,         # 1 hour
        }
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def _generate_key(self, service_type: AIServiceType, response_type: ResponseType,
                     request_params: Dict[str, Any]) -> str:
        """Generate cache key for AI response.
        
        Args:
            service_type: AI service type
            response_type: Response type
            request_params: Request parameters
            
        Returns:
            Cache key
        """
        key_data = {
            'service': service_type.value,
            'type': response_type.value,
            'params': self._normalize_params(request_params)
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _normalize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parameters for consistent caching.
        
        Args:
            params: Request parameters
            
        Returns:
            Normalized parameters
        """
        normalized = {}
        
        for key, value in params.items():
            if isinstance(value, (list, tuple)):
                normalized[key] = tuple(sorted(value) if all(isinstance(x, (str, int, float)) for x in value) else value)
            elif isinstance(value, dict):
                normalized[key] = self._normalize_params(value)
            elif isinstance(value, float):
                # Round floats to avoid precision issues
                normalized[key] = round(value, 6)
            else:
                normalized[key] = value
        
        return normalized
    
    def _compress_data(self, data: Any) -> Tuple[bytes, float]:
        """Compress response data.
        
        Args:
            data: Data to compress
            
        Returns:
            Tuple of (compressed_data, compression_ratio)
        """
        try:
            # Serialize data
            serialized = pickle.dumps(data)
            original_size = len(serialized)
            
            if self.compression_enabled and original_size > 1024:  # Only compress if > 1KB
                compressed = gzip.compress(serialized, compresslevel=6)
                compression_ratio = len(compressed) / original_size
                return compressed, compression_ratio
            else:
                return serialized, 1.0
                
        except Exception as e:
            self._logger.warning(f"Failed to compress data: {e}")
            # Fallback to uncompressed
            serialized = pickle.dumps(data)
            return serialized, 1.0
    
    def _get_ttl(self, response_type: ResponseType, request_params: Dict[str, Any]) -> float:
        """Get TTL for response type.
        
        Args:
            response_type: Response type
            request_params: Request parameters
            
        Returns:
            TTL in seconds
        """
        base_ttl = self._ttl_strategies.get(response_type, self.default_ttl)
        
        # Adjust TTL based on request parameters
        if 'cache_ttl' in request_params:
            return float(request_params['cache_ttl'])
        
        # Dynamic TTL adjustments
        if response_type == ResponseType.WEATHER_ANALYSIS:
            # Shorter TTL for current weather, longer for forecasts
            if request_params.get('forecast_days', 0) > 1:
                base_ttl *= 2
        
        elif response_type == ResponseType.MUSIC_RECOMMENDATION:
            # Longer TTL for genre-based recommendations
            if 'genre' in request_params:
                base_ttl *= 1.5
        
        return base_ttl
    
    def get(self, service_type: AIServiceType, response_type: ResponseType,
           request_params: Dict[str, Any]) -> Optional[Any]:
        """Get cached AI response.
        
        Args:
            service_type: AI service type
            response_type: Response type
            request_params: Request parameters
            
        Returns:
            Cached response data or None
        """
        key = self._generate_key(service_type, response_type, request_params)
        
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if entry is still valid
                if not entry.is_expired:
                    entry.access()
                    return entry.get_decompressed_data()
                else:
                    # Remove expired entry
                    del self._cache[key]
        
        return None
    
    def set(self, service_type: AIServiceType, response_type: ResponseType,
           request_params: Dict[str, Any], response_data: Any,
           api_cost: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Cache AI response.
        
        Args:
            service_type: AI service type
            response_type: Response type
            request_params: Request parameters
            response_data: Response data to cache
            api_cost: API cost for this request
            metadata: Additional metadata
        """
        key = self._generate_key(service_type, response_type, request_params)
        
        # Compress data
        compressed_data, compression_ratio = self._compress_data(response_data)
        
        # Get TTL
        ttl = self._get_ttl(response_type, request_params)
        
        entry = AIResponseEntry(
            response_data=compressed_data,
            service_type=service_type,
            response_type=response_type,
            request_params=request_params,
            metadata=metadata or {},
            ttl_seconds=ttl,
            api_cost=api_cost,
            compression_ratio=compression_ratio
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
            
            # Find entry to remove (LRU with cost consideration)
            removal_key = self._select_removal_candidate()
            if removal_key:
                removed_entry = self._cache.pop(removal_key)
                current_size -= removed_entry.size_mb
            else:
                break
    
    def _select_removal_candidate(self) -> Optional[str]:
        """Select cache entry for removal.
        
        Returns:
            Key of entry to remove
        """
        if not self._cache:
            return None
        
        # Score entries based on multiple factors
        scored_entries = []
        
        for key, entry in self._cache.items():
            # Factors: age, access frequency, cost, size
            age_score = entry.age_seconds / entry.ttl_seconds  # Higher = older
            access_score = 1.0 / (entry.access_count + 1)      # Higher = less accessed
            cost_score = 1.0 / (entry.api_cost + 0.01)         # Higher = cheaper to regenerate
            size_score = entry.size_mb                          # Higher = larger
            
            # Weighted combination
            total_score = (age_score * 0.3 + access_score * 0.3 + 
                          cost_score * 0.2 + size_score * 0.2)
            
            scored_entries.append((total_score, key))
        
        # Return key with highest removal score
        scored_entries.sort(reverse=True)
        return scored_entries[0][1]
    
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
            total_cost_saved = sum(entry.api_cost * entry.access_count for entry in self._cache.values())
            avg_compression = sum(entry.compression_ratio for entry in self._cache.values()) / len(self._cache) if self._cache else 1.0
            
            service_distribution = defaultdict(int)
            response_type_distribution = defaultdict(int)
            
            for entry in self._cache.values():
                service_distribution[entry.service_type.value] += 1
                response_type_distribution[entry.response_type.value] += 1
            
            return {
                'entries': len(self._cache),
                'max_entries': self.max_entries,
                'size_mb': self.get_size_mb(),
                'max_size_mb': self.max_size_mb,
                'utilization_percent': (len(self._cache) / self.max_entries) * 100,
                'size_utilization_percent': (self.get_size_mb() / self.max_size_mb) * 100,
                'total_accesses': total_accesses,
                'total_cost_saved': total_cost_saved,
                'avg_compression_ratio': avg_compression,
                'service_distribution': dict(service_distribution),
                'response_type_distribution': dict(response_type_distribution),
                'compression_enabled': self.compression_enabled
            }
    
    def clear(self) -> None:
        """Clear all cached responses."""
        with self._lock:
            self._cache.clear()
    
    def invalidate_service(self, service_type: AIServiceType) -> int:
        """Invalidate all entries for a specific service.
        
        Args:
            service_type: Service type to invalidate
            
        Returns:
            Number of entries removed
        """
        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.service_type == service_type
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            return len(keys_to_remove)
    
    def _cleanup_loop(self) -> None:
        """Cleanup expired entries periodically."""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                
                expired_keys = []
                
                with self._lock:
                    for key, entry in self._cache.items():
                        if entry.is_expired:
                            expired_keys.append(key)
                
                # Remove expired entries
                if expired_keys:
                    with self._lock:
                        for key in expired_keys:
                            if key in self._cache:
                                del self._cache[key]
                    
                    self._logger.debug(f"Cleaned up {len(expired_keys)} expired AI response cache entries")
                
            except Exception as e:
                self._logger.error(f"Error in AI response cache cleanup: {e}")


class AIResponseOptimizer:
    """Service for AI response optimization and management."""
    
    def __init__(self, 
                 cache_size_mb: float = 500.0,
                 max_cache_entries: int = 10000,
                 default_ttl: float = 3600.0,
                 compression_enabled: bool = True):
        """
        Initialize AI response optimizer.
        
        Args:
            cache_size_mb: Maximum cache size in MB
            max_cache_entries: Maximum cache entries
            default_ttl: Default cache TTL
            compression_enabled: Whether to enable compression
        """
        self._cache = AIResponseCache(
            max_size_mb=cache_size_mb,
            max_entries=max_cache_entries,
            default_ttl=default_ttl,
            compression_enabled=compression_enabled
        )
        
        self._stats = AIResponseStats()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Service-specific configurations
        self._service_configs = {
            AIServiceType.GEMINI: {
                'rate_limit': 60,  # requests per minute
                'cost_per_request': 0.001,
                'retry_attempts': 3
            },
            AIServiceType.SPOTIFY: {
                'rate_limit': 100,
                'cost_per_request': 0.0,  # Free tier
                'retry_attempts': 2
            },
            AIServiceType.WEATHER_AI: {
                'rate_limit': 1000,
                'cost_per_request': 0.0001,
                'retry_attempts': 3
            }
        }
    
    def get_cached_response(self, service_type: AIServiceType, response_type: ResponseType,
                           request_params: Dict[str, Any]) -> Optional[Any]:
        """Get cached AI response.
        
        Args:
            service_type: AI service type
            response_type: Response type
            request_params: Request parameters
            
        Returns:
            Cached response or None
        """
        start_time = time.time()
        
        cached_response = self._cache.get(service_type, response_type, request_params)
        
        response_time = time.time() - start_time
        
        if cached_response is not None:
            with self._lock:
                self._stats.update_request(
                    service_type=service_type,
                    response_type=response_type,
                    response_time=response_time,
                    from_cache=True
                )
            
            self._logger.debug(f"Cache hit for {service_type.value} {response_type.value}")
            return cached_response
        
        return None
    
    def cache_response(self, service_type: AIServiceType, response_type: ResponseType,
                      request_params: Dict[str, Any], response_data: Any,
                      response_time: float, api_cost: float = 0.0,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Cache AI response.
        
        Args:
            service_type: AI service type
            response_type: Response type
            request_params: Request parameters
            response_data: Response data
            response_time: Response time
            api_cost: API cost
            metadata: Additional metadata
        """
        self._cache.set(
            service_type=service_type,
            response_type=response_type,
            request_params=request_params,
            response_data=response_data,
            api_cost=api_cost,
            metadata=metadata
        )
        
        with self._lock:
            self._stats.update_request(
                service_type=service_type,
                response_type=response_type,
                response_time=response_time,
                api_cost=api_cost,
                from_cache=False
            )
        
        self._logger.debug(f"Cached response for {service_type.value} {response_type.value}")
    
    def get_or_generate_response(self, service_type: AIServiceType, response_type: ResponseType,
                               request_params: Dict[str, Any], generator_func: Callable,
                               api_cost: float = 0.0) -> Any:
        """Get cached response or generate new one.
        
        Args:
            service_type: AI service type
            response_type: Response type
            request_params: Request parameters
            generator_func: Function to generate response if not cached
            api_cost: API cost for generation
            
        Returns:
            Response data
        """
        # Try cache first
        cached_response = self.get_cached_response(service_type, response_type, request_params)
        if cached_response is not None:
            return cached_response
        
        # Generate new response
        start_time = time.time()
        
        try:
            response_data = generator_func(request_params)
            response_time = time.time() - start_time
            
            # Cache the response
            self.cache_response(
                service_type=service_type,
                response_type=response_type,
                request_params=request_params,
                response_data=response_data,
                response_time=response_time,
                api_cost=api_cost
            )
            
            return response_data
            
        except Exception as e:
            self._logger.error(f"Failed to generate {service_type.value} response: {e}")
            raise
    
    def preload_common_responses(self, preload_configs: List[Dict[str, Any]]) -> None:
        """Preload common AI responses.
        
        Args:
            preload_configs: List of preload configurations
        """
        for config in preload_configs:
            try:
                service_type = AIServiceType(config.get('service_type'))
                response_type = ResponseType(config.get('response_type'))
                request_params = config.get('request_params', {})
                generator_func = config.get('generator_func')
                api_cost = config.get('api_cost', 0.0)
                
                if generator_func:
                    self.get_or_generate_response(
                        service_type=service_type,
                        response_type=response_type,
                        request_params=request_params,
                        generator_func=generator_func,
                        api_cost=api_cost
                    )
                
            except Exception as e:
                self._logger.warning(f"Failed to preload AI response: {e}")
    
    def invalidate_service_cache(self, service_type: AIServiceType) -> int:
        """Invalidate cache for specific service.
        
        Args:
            service_type: Service type to invalidate
            
        Returns:
            Number of entries removed
        """
        removed_count = self._cache.invalidate_service(service_type)
        self._logger.info(f"Invalidated {removed_count} cache entries for {service_type.value}")
        return removed_count
    
    def cleanup_memory(self) -> Dict[str, Any]:
        """Clean up AI response memory.
        
        Returns:
            Cleanup results
        """
        cleanup_results = {
            'start_time': time.time(),
            'actions_taken': []
        }
        
        # Get stats before cleanup
        cache_stats_before = self._cache.get_stats()
        
        # Clear cache if memory usage is high
        if cache_stats_before['size_utilization_percent'] > 85:
            self._cache.clear()
            cleanup_results['actions_taken'].append("Cleared AI response cache due to high memory usage")
        
        cleanup_results['end_time'] = time.time()
        cleanup_results['duration'] = cleanup_results['end_time'] - cleanup_results['start_time']
        
        return cleanup_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive AI optimization statistics.
        
        Returns:
            Statistics dictionary
        """
        cache_stats = self._cache.get_stats()
        
        with self._lock:
            response_stats = {
                'total_requests': self._stats.total_requests,
                'cache_hit_rate': self._stats.cache_hit_rate,
                'avg_response_time': self._stats.avg_response_time,
                'total_api_cost': self._stats.total_api_cost,
                'cost_savings': self._stats.cost_savings,
                'service_counts': dict(self._stats.service_counts),
                'response_type_counts': dict(self._stats.response_type_counts),
                'compression_savings_mb': self._stats.compression_savings_mb
            }
        
        return {
            'response_stats': response_stats,
            'cache_stats': cache_stats,
            'service_configs': self._service_configs
        }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Optimize AI response performance.
        
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
        
        # Optimize cache settings based on usage patterns
        stats = self.get_stats()
        cache_hit_rate = stats['response_stats']['cache_hit_rate']
        
        if cache_hit_rate < 50:
            # Increase TTL for better hit rates
            optimization_results['actions_taken'].append("Increased cache TTL due to low hit rate")
        
        optimization_results['end_time'] = time.time()
        optimization_results['duration'] = optimization_results['end_time'] - optimization_results['start_time']
        
        return optimization_results


# Decorators for AI response optimization
def cached_ai_response(service_type: AIServiceType, response_type: ResponseType,
                      cache_ttl: Optional[float] = None):
    """Decorator for caching AI responses.
    
    Args:
        service_type: AI service type
        response_type: Response type
        cache_ttl: Cache time-to-live
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            optimizer = get_ai_optimizer()
            
            # Extract request parameters
            request_params = kwargs.copy()
            if cache_ttl:
                request_params['cache_ttl'] = cache_ttl
            
            # Try to get cached response
            cached_response = optimizer.get_cached_response(
                service_type=service_type,
                response_type=response_type,
                request_params=request_params
            )
            
            if cached_response is not None:
                return cached_response
            
            # Generate new response
            start_time = time.time()
            response = func(*args, **kwargs)
            response_time = time.time() - start_time
            
            # Cache the response
            optimizer.cache_response(
                service_type=service_type,
                response_type=response_type,
                request_params=request_params,
                response_data=response,
                response_time=response_time
            )
            
            return response
        
        return wrapper
    
    return decorator


def cost_aware_ai_call(api_cost: float = 0.0):
    """Decorator for cost-aware AI calls.
    
    Args:
        api_cost: API cost per call
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would track API costs and optimize based on budget
            # For now, just execute the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Global AI optimizer instance
_global_ai_optimizer = None


def get_ai_optimizer() -> AIResponseOptimizer:
    """Get global AI optimizer instance.
    
    Returns:
        AI optimizer instance
    """
    global _global_ai_optimizer
    if _global_ai_optimizer is None:
        _global_ai_optimizer = AIResponseOptimizer()
    return _global_ai_optimizer