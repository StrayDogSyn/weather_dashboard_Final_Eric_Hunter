"""Async Loading System for Weather Dashboard.

Provides comprehensive async loading capabilities to reduce startup time
and improve responsiveness through parallel service initialization,
progressive UI loading, and optimized API call management.
"""

import asyncio
import concurrent.futures
import logging
import time
from typing import Dict, Any, Callable, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
from pathlib import Path


class LoadingPriority(Enum):
    """Loading priority levels for task scheduling."""
    CRITICAL = 1    # UI blocking, must complete first
    HIGH = 2        # Important for user experience
    NORMAL = 3      # Standard loading
    LOW = 4         # Background, can be deferred
    DEFERRED = 5    # Load only when needed


@dataclass
class LoadingTask:
    """Represents a loading task with metadata."""
    name: str
    func: Callable
    priority: LoadingPriority
    timeout: float = 30.0
    dependencies: List[str] = None
    retry_count: int = 3
    cache_key: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class LoadingResult:
    """Result of a loading operation."""
    task_name: str
    success: bool
    data: Any = None
    error: Optional[Exception] = None
    duration: float = 0.0
    from_cache: bool = False


class AsyncLoader:
    """Advanced async loading system with parallel execution and caching."""
    
    def __init__(self, max_workers: int = 4, cache_enabled: bool = True):
        """Initialize the async loader.
        
        Args:
            max_workers: Maximum number of concurrent workers
            cache_enabled: Whether to enable result caching
        """
        self.logger = logging.getLogger(__name__)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers
        self.cache_enabled = cache_enabled
        
        # Task management
        self.tasks: Dict[str, LoadingTask] = {}
        self.results: Dict[str, LoadingResult] = {}
        self.cache: Dict[str, Tuple[Any, float]] = {}  # (data, timestamp)
        self.cache_ttl = 300  # 5 minutes default TTL
        
        # Progress tracking
        self.progress_callbacks: List[Callable] = []
        self.total_tasks = 0
        self.completed_tasks = 0
        
        # State management
        self.is_loading = False
        self.cancelled = False
        
        self.logger.info(f"AsyncLoader initialized with {max_workers} workers")
    
    def add_task(self, task: LoadingTask) -> None:
        """Add a task to the loading queue.
        
        Args:
            task: LoadingTask to add
        """
        self.tasks[task.name] = task
        self.logger.debug(f"Added task: {task.name} (priority: {task.priority.name})")
    
    def add_progress_callback(self, callback: Callable[[str, float], None]) -> None:
        """Add a progress callback function.
        
        Args:
            callback: Function that receives (task_name, progress_percentage)
        """
        self.progress_callbacks.append(callback)
    
    async def load_parallel(self, tasks: Dict[str, Callable]) -> Dict[str, Any]:
        """Load multiple components in parallel.
        
        Args:
            tasks: Dictionary of task_name -> function mappings
            
        Returns:
            Dictionary of task_name -> result mappings
        """
        results = {}
        
        async def load_task(name: str, func: Callable):
            """Load a single task with error handling."""
            start_time = time.time()
            try:
                self.logger.info(f"Starting parallel task: {name}")
                
                # Check cache first
                if self.cache_enabled and name in self.cache:
                    cached_data, timestamp = self.cache[name]
                    if time.time() - timestamp < self.cache_ttl:
                        self.logger.info(f"Using cached result for {name}")
                        results[name] = cached_data
                        self._update_progress(name, 1.0)
                        return
                
                # Execute in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self.executor, func)
                
                # Cache result
                if self.cache_enabled:
                    self.cache[name] = (result, time.time())
                
                results[name] = result
                duration = time.time() - start_time
                self.logger.info(f"Completed parallel task: {name} in {duration:.2f}s")
                
                self._update_progress(name, 1.0)
                
            except Exception as e:
                duration = time.time() - start_time
                self.logger.error(f"Failed parallel task: {name} after {duration:.2f}s - {e}")
                results[name] = None
                self._update_progress(name, 1.0, error=str(e))
        
        # Execute all tasks concurrently
        await asyncio.gather(*[
            load_task(name, func)
            for name, func in tasks.items()
        ])
        
        return results
    
    async def load_sequential(self, tasks: List[Tuple[str, Callable]]) -> Dict[str, Any]:
        """Load tasks sequentially with dependency management.
        
        Args:
            tasks: List of (task_name, function) tuples in execution order
            
        Returns:
            Dictionary of task_name -> result mappings
        """
        results = {}
        
        for i, (name, func) in enumerate(tasks):
            if self.cancelled:
                break
                
            start_time = time.time()
            try:
                self.logger.info(f"Starting sequential task {i+1}/{len(tasks)}: {name}")
                
                # Check cache
                if self.cache_enabled and name in self.cache:
                    cached_data, timestamp = self.cache[name]
                    if time.time() - timestamp < self.cache_ttl:
                        self.logger.info(f"Using cached result for {name}")
                        results[name] = cached_data
                        self._update_progress(name, 1.0)
                        continue
                
                # Execute task
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self.executor, func)
                
                # Cache and store result
                if self.cache_enabled:
                    self.cache[name] = (result, time.time())
                
                results[name] = result
                duration = time.time() - start_time
                self.logger.info(f"Completed sequential task: {name} in {duration:.2f}s")
                
                self._update_progress(name, 1.0)
                
            except Exception as e:
                duration = time.time() - start_time
                self.logger.error(f"Failed sequential task: {name} after {duration:.2f}s - {e}")
                results[name] = None
                self._update_progress(name, 1.0, error=str(e))
        
        return results
    
    async def load_with_priorities(self) -> Dict[str, LoadingResult]:
        """Load all registered tasks respecting priority and dependencies.
        
        Returns:
            Dictionary of task results
        """
        if not self.tasks:
            self.logger.warning("No tasks registered for loading")
            return {}
        
        self.is_loading = True
        self.cancelled = False
        self.total_tasks = len(self.tasks)
        self.completed_tasks = 0
        
        # Sort tasks by priority
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: (t.priority.value, t.name)
        )
        
        # Group by priority for parallel execution within priority levels
        priority_groups = {}
        for task in sorted_tasks:
            if task.priority not in priority_groups:
                priority_groups[task.priority] = []
            priority_groups[task.priority].append(task)
        
        results = {}
        
        # Execute each priority group
        for priority in LoadingPriority:
            if priority not in priority_groups or self.cancelled:
                continue
                
            group_tasks = priority_groups[priority]
            self.logger.info(f"Loading {len(group_tasks)} {priority.name} priority tasks")
            
            # Execute tasks in this priority group in parallel
            group_results = await self._execute_task_group(group_tasks)
            results.update(group_results)
        
        self.is_loading = False
        self.logger.info(f"Completed loading {len(results)} tasks")
        return results
    
    async def _execute_task_group(self, tasks: List[LoadingTask]) -> Dict[str, LoadingResult]:
        """Execute a group of tasks with the same priority.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            Dictionary of task results
        """
        results = {}
        
        async def execute_single_task(task: LoadingTask) -> LoadingResult:
            """Execute a single task with retry logic."""
            start_time = time.time()
            
            # Check dependencies
            for dep in task.dependencies:
                if dep not in results or not results[dep].success:
                    error_msg = f"Dependency {dep} not satisfied for task {task.name}"
                    self.logger.error(error_msg)
                    return LoadingResult(
                        task_name=task.name,
                        success=False,
                        error=Exception(error_msg),
                        duration=time.time() - start_time
                    )
            
            # Check cache
            if self.cache_enabled and task.cache_key and task.cache_key in self.cache:
                cached_data, timestamp = self.cache[task.cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    self.logger.info(f"Using cached result for {task.name}")
                    result = LoadingResult(
                        task_name=task.name,
                        success=True,
                        data=cached_data,
                        duration=time.time() - start_time,
                        from_cache=True
                    )
                    self._mark_task_completed(task.name)
                    return result
            
            # Execute with retries
            last_error = None
            for attempt in range(task.retry_count):
                if self.cancelled:
                    break
                    
                try:
                    self.logger.info(f"Executing {task.name} (attempt {attempt + 1}/{task.retry_count})")
                    
                    # Execute with timeout
                    loop = asyncio.get_event_loop()
                    data = await asyncio.wait_for(
                        loop.run_in_executor(self.executor, task.func),
                        timeout=task.timeout
                    )
                    
                    # Cache result
                    if self.cache_enabled and task.cache_key:
                        self.cache[task.cache_key] = (data, time.time())
                    
                    duration = time.time() - start_time
                    self.logger.info(f"Successfully executed {task.name} in {duration:.2f}s")
                    
                    result = LoadingResult(
                        task_name=task.name,
                        success=True,
                        data=data,
                        duration=duration
                    )
                    
                    self._mark_task_completed(task.name)
                    return result
                    
                except Exception as e:
                    last_error = e
                    self.logger.warning(f"Attempt {attempt + 1} failed for {task.name}: {e}")
                    
                    if attempt < task.retry_count - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
            
            # All attempts failed
            duration = time.time() - start_time
            self.logger.error(f"Task {task.name} failed after {task.retry_count} attempts")
            
            result = LoadingResult(
                task_name=task.name,
                success=False,
                error=last_error,
                duration=duration
            )
            
            self._mark_task_completed(task.name)
            return result
        
        # Execute all tasks in the group concurrently
        task_results = await asyncio.gather(*[
            execute_single_task(task) for task in tasks
        ])
        
        # Convert to dictionary
        for result in task_results:
            results[result.task_name] = result
        
        return results
    
    def _update_progress(self, task_name: str, progress: float, error: str = None):
        """Update progress and notify callbacks.
        
        Args:
            task_name: Name of the task
            progress: Progress percentage (0.0 to 1.0)
            error: Optional error message
        """
        for callback in self.progress_callbacks:
            try:
                callback(task_name, progress)
            except Exception as e:
                self.logger.error(f"Progress callback failed: {e}")
    
    def _mark_task_completed(self, task_name: str):
        """Mark a task as completed and update overall progress.
        
        Args:
            task_name: Name of the completed task
        """
        self.completed_tasks += 1
        overall_progress = self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 1.0
        
        for callback in self.progress_callbacks:
            try:
                callback("overall", overall_progress)
            except Exception as e:
                self.logger.error(f"Overall progress callback failed: {e}")
    
    def cancel_loading(self):
        """Cancel all ongoing loading operations."""
        self.cancelled = True
        self.logger.info("Loading operations cancelled")
    
    def clear_cache(self):
        """Clear the result cache."""
        self.cache.clear()
        self.logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        valid_entries = sum(
            1 for _, timestamp in self.cache.values()
            if current_time - timestamp < self.cache_ttl
        )
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "cache_ttl": self.cache_ttl
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.cancel_loading()
        self.executor.shutdown(wait=True)
        self.clear_cache()
        self.logger.info("AsyncLoader cleanup completed")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore cleanup errors during destruction