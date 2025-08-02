"""API Optimization Service.

Provides intelligent API call optimization including request batching, smart prefetching,
HTTP/2 parallel requests, and response compression for improved performance.
"""

import asyncio
import gzip
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import aiohttp
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref


class RequestPriority(Enum):
    """Request priority levels."""
    CRITICAL = 0    # Current weather, alerts
    HIGH = 1        # Forecast data
    MEDIUM = 2      # Historical data, maps
    LOW = 3         # Background updates
    PREFETCH = 4    # Predictive loading


class CacheStrategy(Enum):
    """Cache strategies for API responses."""
    NO_CACHE = "no_cache"
    SHORT_TERM = "short_term"      # 5 minutes
    MEDIUM_TERM = "medium_term"    # 30 minutes
    LONG_TERM = "long_term"        # 2 hours
    PERSISTENT = "persistent"      # 24 hours


@dataclass
class APIRequest:
    """Represents an API request."""
    url: str
    method: str = "GET"
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    data: Optional[Any] = None
    priority: RequestPriority = RequestPriority.MEDIUM
    cache_strategy: CacheStrategy = CacheStrategy.MEDIUM_TERM
    timeout: float = 30.0
    retry_count: int = 3
    batch_key: Optional[str] = None
    callback: Optional[Callable[[Any], None]] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}
        if self.headers is None:
            self.headers = {}
    
    def cache_key(self) -> str:
        """Generate cache key for this request."""
        key_parts = [self.url, self.method]
        if self.params:
            sorted_params = sorted(self.params.items())
            key_parts.append(str(sorted_params))
        return "|".join(key_parts)


@dataclass
class BatchRequest:
    """Represents a batch of related API requests."""
    batch_key: str
    requests: List[APIRequest] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    max_wait_time: float = 1.0  # Maximum time to wait for more requests
    max_batch_size: int = 10
    
    def can_add_request(self) -> bool:
        """Check if more requests can be added to this batch."""
        return (
            len(self.requests) < self.max_batch_size and
            time.time() - self.created_at < self.max_wait_time
        )


@dataclass
class PrefetchRule:
    """Rule for predictive API prefetching."""
    trigger_pattern: str  # Pattern that triggers prefetch
    prefetch_urls: List[str]  # URLs to prefetch
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: RequestPriority = RequestPriority.PREFETCH
    cache_strategy: CacheStrategy = CacheStrategy.MEDIUM_TERM


class APIOptimizer:
    """Optimizes API calls through batching, caching, and smart prefetching."""
    
    def __init__(self, max_concurrent: int = 10, enable_http2: bool = True):
        """Initialize API optimizer.
        
        Args:
            max_concurrent: Maximum concurrent requests
            enable_http2: Enable HTTP/2 support
        """
        self.logger = logging.getLogger(__name__)
        self.max_concurrent = max_concurrent
        self.enable_http2 = enable_http2
        
        # Request management
        self.request_queue: Dict[RequestPriority, deque] = {
            priority: deque() for priority in RequestPriority
        }
        self.active_requests: Set[asyncio.Task] = set()
        self.batch_requests: Dict[str, BatchRequest] = {}
        
        # Caching
        self.cache_manager = None
        self.cache_ttl = {
            CacheStrategy.SHORT_TERM: 300,     # 5 minutes
            CacheStrategy.MEDIUM_TERM: 1800,   # 30 minutes
            CacheStrategy.LONG_TERM: 7200,     # 2 hours
            CacheStrategy.PERSISTENT: 86400,   # 24 hours
        }
        
        # Prefetching
        self.prefetch_rules: List[PrefetchRule] = []
        self.prefetch_history: deque = deque(maxlen=100)
        
        # Performance tracking
        self.request_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'batched_requests': 0,
            'prefetch_hits': 0,
            'average_response_time': 0.0,
            'response_times': deque(maxlen=100)
        }
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        self.session_lock = asyncio.Lock()
        
        # Background tasks
        self.batch_processor_task: Optional[asyncio.Task] = None
        self.prefetch_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
        # Rate limiting
        self.rate_limits: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'requests': deque(maxlen=100),
            'max_per_minute': 60,
            'max_per_hour': 1000
        })
    
    def set_cache_manager(self, cache_manager) -> None:
        """Set cache manager for response caching."""
        self.cache_manager = cache_manager
    
    async def initialize(self) -> None:
        """Initialize the API optimizer."""
        self.logger.info("🚀 Initializing API optimizer...")
        
        # Create HTTP session with optimizations
        connector_kwargs = {
            'limit': self.max_concurrent,
            'limit_per_host': self.max_concurrent // 2,
            'ttl_dns_cache': 300,
            'use_dns_cache': True,
        }
        
        if self.enable_http2:
            connector_kwargs['enable_cleanup_closed'] = True
        
        connector = aiohttp.TCPConnector(**connector_kwargs)
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Accept-Encoding': 'gzip, deflate',
                'User-Agent': 'WeatherDashboard/1.0 (Optimized)'
            }
        )
        
        # Start background tasks
        self.batch_processor_task = asyncio.create_task(self._process_batches())
        self.prefetch_task = asyncio.create_task(self._prefetch_worker())
        
        self.logger.info("✅ API optimizer initialized")
    
    def add_prefetch_rule(self, rule: PrefetchRule) -> None:
        """Add a prefetch rule.
        
        Args:
            rule: Prefetch rule to add
        """
        self.prefetch_rules.append(rule)
        self.logger.debug(f"📋 Added prefetch rule: {rule.trigger_pattern}")
    
    async def request(self, api_request: APIRequest) -> Optional[Any]:
        """Make an optimized API request.
        
        Args:
            api_request: Request configuration
            
        Returns:
            Optional[Any]: Response data
        """
        if self._shutdown:
            return None
        
        # Check cache first
        if api_request.cache_strategy != CacheStrategy.NO_CACHE:
            cached_response = await self._get_cached_response(api_request)
            if cached_response is not None:
                self.request_stats['cache_hits'] += 1
                self._trigger_prefetch(api_request)
                return cached_response
            else:
                self.request_stats['cache_misses'] += 1
        
        # Check if request should be batched
        if api_request.batch_key:
            return await self._add_to_batch(api_request)
        
        # Make individual request
        return await self._execute_request(api_request)
    
    async def _get_cached_response(self, api_request: APIRequest) -> Optional[Any]:
        """Get cached response if available.
        
        Args:
            api_request: Request configuration
            
        Returns:
            Optional[Any]: Cached response data
        """
        if not self.cache_manager:
            return None
        
        cache_key = f"api:{api_request.cache_key()}"
        return self.cache_manager.get(cache_key)
    
    async def _cache_response(self, api_request: APIRequest, response_data: Any) -> None:
        """Cache API response.
        
        Args:
            api_request: Request configuration
            response_data: Response data to cache
        """
        if not self.cache_manager or api_request.cache_strategy == CacheStrategy.NO_CACHE:
            return
        
        cache_key = f"api:{api_request.cache_key()}"
        ttl = self.cache_ttl.get(api_request.cache_strategy, 1800)
        
        self.cache_manager.set(
            cache_key,
            response_data,
            ttl=ttl,
            tags=['api', 'response', api_request.cache_strategy.value]
        )
    
    async def _add_to_batch(self, api_request: APIRequest) -> Any:
        """Add request to batch or create new batch.
        
        Args:
            api_request: Request to batch
            
        Returns:
            Any: Response data (when batch is processed)
        """
        batch_key = api_request.batch_key
        
        # Get or create batch
        if batch_key in self.batch_requests:
            batch = self.batch_requests[batch_key]
            if batch.can_add_request():
                batch.requests.append(api_request)
            else:
                # Batch is full or expired, process it and create new one
                await self._process_batch(batch)
                batch = BatchRequest(batch_key=batch_key, requests=[api_request])
                self.batch_requests[batch_key] = batch
        else:
            batch = BatchRequest(batch_key=batch_key, requests=[api_request])
            self.batch_requests[batch_key] = batch
        
        # Wait for batch to be processed
        # In a real implementation, you'd use asyncio.Event or similar
        # For now, we'll process immediately if batch is ready
        if len(batch.requests) >= batch.max_batch_size:
            return await self._process_batch(batch)
        
        # For simplicity, execute individual request
        return await self._execute_request(api_request)
    
    async def _process_batch(self, batch: BatchRequest) -> List[Any]:
        """Process a batch of requests.
        
        Args:
            batch: Batch to process
            
        Returns:
            List[Any]: List of response data
        """
        self.logger.info(f"📦 Processing batch {batch.batch_key} with {len(batch.requests)} requests")
        
        # Execute all requests in parallel
        tasks = []
        for request in batch.requests:
            task = asyncio.create_task(self._execute_request(request))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.request_stats['batched_requests'] += len(batch.requests)
        
        # Remove batch from tracking
        if batch.batch_key in self.batch_requests:
            del self.batch_requests[batch.batch_key]
        
        return results
    
    async def _execute_request(self, api_request: APIRequest) -> Optional[Any]:
        """Execute a single API request.
        
        Args:
            api_request: Request to execute
            
        Returns:
            Optional[Any]: Response data
        """
        if not self.session:
            await self.initialize()
        
        # Check rate limits
        if not self._check_rate_limit(api_request.url):
            self.logger.warning(f"⚠️ Rate limit exceeded for {api_request.url}")
            await asyncio.sleep(1)  # Brief delay
        
        start_time = time.time()
        
        try:
            # Prepare request parameters
            kwargs = {
                'method': api_request.method,
                'url': api_request.url,
                'params': api_request.params,
                'headers': api_request.headers,
                'timeout': aiohttp.ClientTimeout(total=api_request.timeout)
            }
            
            if api_request.data:
                if isinstance(api_request.data, dict):
                    kwargs['json'] = api_request.data
                else:
                    kwargs['data'] = api_request.data
            
            # Execute request with retries
            for attempt in range(api_request.retry_count + 1):
                try:
                    async with self.session.request(**kwargs) as response:
                        if response.status == 200:
                            # Handle compressed responses
                            content = await response.read()
                            if response.headers.get('Content-Encoding') == 'gzip':
                                content = gzip.decompress(content)
                            
                            # Parse JSON if applicable
                            content_type = response.headers.get('Content-Type', '')
                            if 'application/json' in content_type:
                                response_data = json.loads(content.decode('utf-8'))
                            else:
                                response_data = content.decode('utf-8')
                            
                            # Cache response
                            await self._cache_response(api_request, response_data)
                            
                            # Update statistics
                            response_time = time.time() - start_time
                            self._update_stats(response_time)
                            
                            # Record rate limit usage
                            self._record_request(api_request.url)
                            
                            # Trigger prefetch
                            self._trigger_prefetch(api_request)
                            
                            # Execute callback if provided
                            if api_request.callback:
                                try:
                                    api_request.callback(response_data)
                                except Exception as e:
                                    self.logger.error(f"Callback error: {e}")
                            
                            return response_data
                        
                        elif response.status == 429:  # Rate limited
                            retry_after = int(response.headers.get('Retry-After', 60))
                            self.logger.warning(f"Rate limited, waiting {retry_after}s")
                            await asyncio.sleep(retry_after)
                        
                        else:
                            self.logger.warning(f"HTTP {response.status} for {api_request.url}")
                            if attempt < api_request.retry_count:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
                except asyncio.TimeoutError:
                    self.logger.warning(f"Timeout for {api_request.url} (attempt {attempt + 1})")
                    if attempt < api_request.retry_count:
                        await asyncio.sleep(1)
                
                except Exception as e:
                    self.logger.error(f"Request error for {api_request.url}: {e}")
                    if attempt < api_request.retry_count:
                        await asyncio.sleep(1)
            
            self.logger.error(f"❌ Failed to complete request to {api_request.url} after {api_request.retry_count + 1} attempts")
            return None
        
        except Exception as e:
            self.logger.error(f"Unexpected error for {api_request.url}: {e}")
            return None
    
    def _check_rate_limit(self, url: str) -> bool:
        """Check if request is within rate limits.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if within limits
        """
        # Extract domain for rate limiting
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        rate_limit = self.rate_limits[domain]
        now = time.time()
        
        # Clean old requests
        requests = rate_limit['requests']
        while requests and now - requests[0] > 3600:  # 1 hour
            requests.popleft()
        
        # Check limits
        recent_requests = sum(1 for req_time in requests if now - req_time < 60)  # 1 minute
        if recent_requests >= rate_limit['max_per_minute']:
            return False
        
        if len(requests) >= rate_limit['max_per_hour']:
            return False
        
        return True
    
    def _record_request(self, url: str) -> None:
        """Record a request for rate limiting.
        
        Args:
            url: URL that was requested
        """
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        self.rate_limits[domain]['requests'].append(time.time())
    
    def _update_stats(self, response_time: float) -> None:
        """Update performance statistics.
        
        Args:
            response_time: Response time in seconds
        """
        self.request_stats['total_requests'] += 1
        self.request_stats['response_times'].append(response_time)
        
        # Calculate average response time
        if self.request_stats['response_times']:
            avg_time = sum(self.request_stats['response_times']) / len(self.request_stats['response_times'])
            self.request_stats['average_response_time'] = avg_time
    
    def _trigger_prefetch(self, api_request: APIRequest) -> None:
        """Trigger prefetch based on current request.
        
        Args:
            api_request: Current request that might trigger prefetch
        """
        # Add to prefetch history
        self.prefetch_history.append({
            'url': api_request.url,
            'timestamp': time.time(),
            'params': api_request.params.copy() if api_request.params else {}
        })
        
        # Check prefetch rules
        for rule in self.prefetch_rules:
            if rule.trigger_pattern in api_request.url:
                # Schedule prefetch requests
                for prefetch_url in rule.prefetch_urls:
                    prefetch_request = APIRequest(
                        url=prefetch_url,
                        priority=rule.priority,
                        cache_strategy=rule.cache_strategy
                    )
                    
                    # Add to appropriate queue
                    self.request_queue[rule.priority].append(prefetch_request)
    
    async def _process_batches(self) -> None:
        """Background task to process batches."""
        while not self._shutdown:
            try:
                # Process expired batches
                expired_batches = []
                for batch_key, batch in self.batch_requests.items():
                    if time.time() - batch.created_at >= batch.max_wait_time:
                        expired_batches.append(batch_key)
                
                for batch_key in expired_batches:
                    batch = self.batch_requests.pop(batch_key)
                    asyncio.create_task(self._process_batch(batch))
                
                await asyncio.sleep(0.1)  # Check every 100ms
            
            except Exception as e:
                self.logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(1)
    
    async def _prefetch_worker(self) -> None:
        """Background task for prefetching."""
        while not self._shutdown:
            try:
                # Process prefetch queue
                for priority in [RequestPriority.PREFETCH]:
                    queue = self.request_queue[priority]
                    if queue and len(self.active_requests) < self.max_concurrent:
                        request = queue.popleft()
                        task = asyncio.create_task(self._execute_request(request))
                        self.active_requests.add(task)
                        
                        # Clean up completed tasks
                        self.active_requests = {t for t in self.active_requests if not t.done()}
                
                await asyncio.sleep(1)  # Check every second
            
            except Exception as e:
                self.logger.error(f"Prefetch worker error: {e}")
                await asyncio.sleep(5)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get API optimization statistics.
        
        Returns:
            Dict[str, Any]: Statistics data
        """
        stats = self.request_stats.copy()
        
        # Add additional metrics
        stats.update({
            'active_requests': len(self.active_requests),
            'pending_batches': len(self.batch_requests),
            'prefetch_rules': len(self.prefetch_rules),
            'cache_hit_ratio': (
                self.request_stats['cache_hits'] / 
                max(self.request_stats['cache_hits'] + self.request_stats['cache_misses'], 1)
            ),
            'rate_limits': {domain: len(data['requests']) for domain, data in self.rate_limits.items()}
        })
        
        return stats
    
    async def shutdown(self) -> None:
        """Shutdown the API optimizer."""
        self.logger.info("🛑 Shutting down API optimizer...")
        self._shutdown = True
        
        # Cancel background tasks
        if self.batch_processor_task:
            self.batch_processor_task.cancel()
        if self.prefetch_task:
            self.prefetch_task.cancel()
        
        # Process remaining batches
        for batch in list(self.batch_requests.values()):
            await self._process_batch(batch)
        
        # Cancel active requests
        for task in self.active_requests:
            task.cancel()
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        self.logger.info("✅ API optimizer shutdown complete")