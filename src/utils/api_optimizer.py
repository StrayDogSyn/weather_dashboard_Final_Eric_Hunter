#!/usr/bin/env python3
"""
API Optimizer for Weather Dashboard
Implements intelligent API request management, caching, and rate limiting.
"""

import hashlib
import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class RequestPriority(Enum):
    """Priority levels for API requests."""

    CRITICAL = 1  # User-initiated, immediate
    HIGH = 2  # Important background updates
    MEDIUM = 3  # Regular updates
    LOW = 4  # Nice-to-have data
    BACKGROUND = 5  # Prefetch/cache warming


class CacheStrategy(Enum):
    """Cache strategies for API requests."""

    CACHE_FIRST = "cache_first"  # Try cache first, fallback to API
    API_FIRST = "api_first"  # Try API first, fallback to cache
    CACHE_ONLY = "cache_only"  # Only use cache
    API_ONLY = "api_only"  # Only use API
    REFRESH = "refresh"  # Force refresh from API


@dataclass
class APIRequest:
    """Represents an API request with metadata."""

    endpoint: str
    params: Dict[str, Any] = field(default_factory=dict)
    priority: RequestPriority = RequestPriority.MEDIUM
    cache_strategy: CacheStrategy = CacheStrategy.CACHE_FIRST
    cache_ttl: int = 300  # seconds
    timeout: float = 10.0
    retry_count: int = 2
    callback: Optional[Callable[[Any], None]] = None
    error_callback: Optional[Callable[[Exception], None]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Generate request ID after initialization."""
        self.request_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique request ID based on endpoint and params."""
        content = f"{self.endpoint}:{json.dumps(self.params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class APIResponse:
    """Represents an API response with metadata."""

    request_id: str
    data: Any
    success: bool
    error: Optional[Exception] = None
    from_cache: bool = False
    response_time: float = 0.0
    timestamp: float = field(default_factory=time.time)
    cache_hit: bool = False


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_second: float = 10.0, burst_size: int = 20):
        """Initialize rate limiter."""
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = threading.Lock()

    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens for request."""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update

            # Add tokens based on elapsed time
            self.tokens = min(
                self.burst_size, self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def wait_time(self, tokens: int = 1) -> float:
        """Calculate wait time for tokens."""
        with self._lock:
            if self.tokens >= tokens:
                return 0.0

            needed_tokens = tokens - self.tokens
            return needed_tokens / self.requests_per_second


class APIOptimizer:
    """Main API optimization manager."""

    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_size: int = 20,
        max_concurrent: int = 5,
        cache_size: int = 1000,
    ):
        """Initialize API optimizer."""
        self.rate_limiter = RateLimiter(requests_per_second, burst_size)
        self.max_concurrent = max_concurrent

        # Request management
        self._request_queue: deque = deque()
        self._active_requests: Dict[str, APIRequest] = {}
        self._request_cache: Dict[str, APIResponse] = {}
        self._cache_size = cache_size

        # Threading
        self._worker_threads: List[threading.Thread] = []
        self._shutdown_event = threading.Event()
        self._queue_lock = threading.Lock()
        self._cache_lock = threading.Lock()

        # Statistics
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "rate_limited_requests": 0,
            "concurrent_requests": 0,
        }

        self.logger = logging.getLogger(__name__)

        # Start worker threads
        self._start_workers()

    def _start_workers(self) -> None:
        """Start worker threads for processing requests."""
        for i in range(self.max_concurrent):
            worker = threading.Thread(
                target=self._worker_loop, name=f"APIOptimizer-Worker-{i}", daemon=True
            )
            worker.start()
            self._worker_threads.append(worker)

        self.logger.info(f"Started {self.max_concurrent} API optimizer worker threads")

    def submit_request(self, request: APIRequest) -> str:
        """Submit an API request for processing."""
        with self._queue_lock:
            # Check if request is already active
            if request.request_id in self._active_requests:
                return request.request_id

            # Add to queue based on priority
            self._insert_by_priority(request)
            self._stats["total_requests"] += 1

            self.logger.debug(
                f"Queued request {request.request_id} with priority {request.priority.name}"
            )
            return request.request_id

    def _insert_by_priority(self, request: APIRequest) -> None:
        """Insert request into queue based on priority."""
        # Find insertion point based on priority
        insert_index = 0
        for i, queued_request in enumerate(self._request_queue):
            if request.priority.value < queued_request.priority.value:
                insert_index = i
                break
            insert_index = i + 1

        # Insert at calculated position
        if insert_index >= len(self._request_queue):
            self._request_queue.append(request)
        else:
            self._request_queue.insert(insert_index, request)


    def _get_next_request(self) -> Optional[APIRequest]:
        """Get the next request from the queue."""
        with self._queue_lock:
            if not self._request_queue:
                return None

            # Check rate limiting
            if not self.rate_limiter.acquire():
                self._stats["rate_limited_requests"] += 1
                return None

            request = self._request_queue.popleft()
            self._active_requests[request.request_id] = request
            self._stats["concurrent_requests"] += 1

            return request

    def _process_request(self, request: APIRequest) -> None:
        """Process a single API request."""
        start_time = time.time()
        response = None

        try:
            # Handle different cache strategies
            if request.cache_strategy == CacheStrategy.CACHE_ONLY:
                response = self._get_cached_response(request)
                if not response:
                    raise Exception("No cached data available")

            elif request.cache_strategy == CacheStrategy.CACHE_FIRST:
                response = self._get_cached_response(request)
                if not response:
                    response = self._make_api_call(request)

            elif request.cache_strategy == CacheStrategy.API_FIRST:
                try:
                    response = self._make_api_call(request)
                except Exception:
                    response = self._get_cached_response(request)
                    if not response:
                        raise

            elif request.cache_strategy in [
                CacheStrategy.API_ONLY, CacheStrategy.REFRESH
            ]:
                response = self._make_api_call(request)

            # Update statistics
            response_time = time.time() - start_time
            self._update_stats(response, response_time)

            # Cache successful responses
            if response.success and request.cache_strategy != CacheStrategy.API_ONLY:
                self._cache_response(request, response)

            # Call success callback
            if request.callback:
                try:
                    request.callback(response.data)
                except Exception as e:
                    self.logger.error(
                        f"Callback error for request {request.request_id}: {e}"
                    )

        except Exception as e:
            # Create error response
            response = APIResponse(
                request_id=request.request_id,
                data=None,
                success=False,
                error=e,
                response_time=time.time() - start_time,
            )

            self._update_stats(response, response.response_time)

            # Call error callback
            if request.error_callback:
                try:
                    request.error_callback(e)
                except Exception as callback_error:
                    self.logger.error(f"Error callback failed: {callback_error}")

            self.logger.error(f"Request {request.request_id} failed: {e}")

        finally:
            # Clean up active request
            with self._queue_lock:
                self._active_requests.pop(request.request_id, None)
                self._stats["concurrent_requests"] -= 1

    def _get_cached_response(self, request: APIRequest) -> Optional[APIResponse]:
        """Get cached response if available and valid."""
        with self._cache_lock:
            cached = self._request_cache.get(request.request_id)

            if not cached:
                self._stats["cache_misses"] += 1
                return None

            # Check if cache is still valid
            age = time.time() - cached.timestamp
            if age > request.cache_ttl:
                self._request_cache.pop(request.request_id, None)
                self._stats["cache_misses"] += 1
                return None

            # Return cached response
            self._stats["cache_hits"] += 1
            cached.cache_hit = True
            return cached

    def _make_api_call(self, request: APIRequest) -> APIResponse:
        """Make actual API call (placeholder - to be implemented by subclasses)."""
        # This is a placeholder - actual implementation would depend on the specific API
        # For now, simulate an API call
        time.sleep(0.1)  # Simulate network delay

        # Mock successful response
        response = APIResponse(
            request_id=request.request_id,
            data={
                "mock": "data",
                "endpoint": request.endpoint,
                "params": request.params
            },
            success=True,
            response_time=0.1,
        )

        return response

    def _cache_response(self, request: APIRequest, response: APIResponse) -> None:
        """Cache a successful response."""
        with self._cache_lock:
            # Implement LRU eviction if cache is full
            if len(self._request_cache) >= self._cache_size:
                # Remove oldest entry
                oldest_key = min(
                    self._request_cache.keys(),
                    key=lambda k: self._request_cache[k].timestamp
                )
                self._request_cache.pop(oldest_key, None)

            self._request_cache[request.request_id] = response

    def _update_stats(self, response: APIResponse, response_time: float) -> None:
        """Update performance statistics."""
        if response.success:
            self._stats["successful_requests"] += 1
        else:
            self._stats["failed_requests"] += 1

        # Update average response time
        total_responses = (
            self._stats["successful_requests"] + self._stats["failed_requests"]
        )
        current_avg = self._stats["average_response_time"]
        self._stats["average_response_time"] = (
            current_avg * (total_responses - 1) + response_time
        ) / total_responses

    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific request."""
        # Check if request is active
        if request_id in self._active_requests:
            return {
                "status": "processing",
                "request": self._active_requests[request_id]
            }

        # Check if request is in queue
        with self._queue_lock:
            for request in self._request_queue:
                if request.request_id == request_id:
                    return {"status": "queued", "request": request}

        # Check if response is cached
        with self._cache_lock:
            if request_id in self._request_cache:
                return {
                    "status": "completed",
                    "response": self._request_cache[request_id]
                }

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._queue_lock:
            queue_size = len(self._request_queue)
            active_count = len(self._active_requests)

        with self._cache_lock:
            cache_size = len(self._request_cache)

        stats = self._stats.copy()
        stats.update(
            {
                "queue_size": queue_size,
                "active_requests": active_count,
                "cache_size": cache_size,
                "cache_hit_ratio": (
                    self._stats["cache_hits"]
                    / max(1, self._stats["cache_hits"] + self._stats["cache_misses"])
                )
                * 100,
            }
        )

        return stats

    def _worker_loop(self) -> None:
        """Worker thread loop for processing API requests."""
        while not self._shutdown_event.is_set():
            try:
                # Get next request from queue
                request = self._get_next_request()
                
                if request is None:
                    # No requests available, wait a bit
                    time.sleep(0.1)
                    continue
                
                # Process the request
                self._process_request(request)
                
                # Remove from active requests
                with self._queue_lock:
                    self._active_requests.pop(request.request_id, None)
                    self._stats["concurrent_requests"] -= 1
                    
            except Exception as e:
                self.logger.error(f"Error in worker loop: {e}")
                time.sleep(1)  # Wait before retrying

    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cached responses."""
        with self._cache_lock:
            if pattern:
                # Clear entries matching pattern
                to_remove = [
                    key for key in self._request_cache.keys() if pattern in key
                ]
                for key in to_remove:
                    self._request_cache.pop(key, None)
                cleared = len(to_remove)
            else:
                # Clear all
                cleared = len(self._request_cache)
                self._request_cache.clear()

        self.logger.info(f"Cleared {cleared} cached responses")
        return cleared

    def shutdown(self) -> None:
        """Shutdown the API optimizer."""
        self.logger.info("Shutting down API optimizer")

        # Signal shutdown
        self._shutdown_event.set()

        # Wait for workers to finish
        for worker in self._worker_threads:
            worker.join(timeout=5.0)

        # Clear caches and queues
        with self._queue_lock:
            self._request_queue.clear()
            self._active_requests.clear()

        with self._cache_lock:
            self._request_cache.clear()

        self.logger.info("API optimizer shutdown complete")


# Utility functions for creating common request types
def create_weather_request(
    location: str, priority: RequestPriority = RequestPriority.HIGH
) -> APIRequest:
    """Create a weather data request."""
    return APIRequest(
        endpoint="weather/current",
        params={"location": location},
        priority=priority,
        cache_strategy=CacheStrategy.CACHE_FIRST,
        cache_ttl=600,  # 10 minutes
    )


def create_forecast_request(location: str, days: int = 7) -> APIRequest:
    """Create a forecast request."""
    return APIRequest(
        endpoint="weather/forecast",
        params={"location": location, "days": days},
        priority=RequestPriority.MEDIUM,
        cache_strategy=CacheStrategy.CACHE_FIRST,
        cache_ttl=1800,  # 30 minutes
    )
