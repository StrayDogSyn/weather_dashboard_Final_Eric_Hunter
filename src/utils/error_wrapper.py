"""Error wrapper utilities for safe UI operations."""

import logging
import threading
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def safe_ui_call(func: Callable) -> Callable:
    """Wrapper to catch and log UI errors safely.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            if "main thread" in str(e):
                logger.error(f"Thread error in {func.__name__}: {e}")
                # Attempt recovery
                try:
                    if args and hasattr(args[0], 'winfo_toplevel'):
                        root = args[0].winfo_toplevel()
                        root.after(0, lambda: func(*args, **kwargs))
                except Exception:
                    logger.warning(f"Recovery attempt failed for {func.__name__}")
                    pass
            else:
                raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            # Don't re-raise for UI stability
            return None
    return wrapper


def safe_async_call(func: Callable) -> Callable:
    """Wrapper for async functions to handle errors safely.
    
    Args:
        func: Async function to wrap
        
    Returns:
        Wrapped async function with error handling
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Async error in {func.__name__}: {e}")
            return None
    return wrapper


def safe_service_call(func: Callable) -> Callable:
    """Wrapper for service calls to handle errors gracefully.
    
    Args:
        func: Service function to wrap
        
    Returns:
        Wrapped function with service error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Service error in {func.__name__}: {e}")
            # Return safe default for service calls
            return None
    return wrapper


def ensure_main_thread(func: Callable) -> Callable:
    """Ensure function runs on main thread to prevent threading conflicts.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that executes on main thread
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        if threading.current_thread() is not threading.main_thread():
            # Schedule on main thread
            try:
                if hasattr(self, 'after'):
                    self.after(0, lambda: func(self, *args, **kwargs))
                elif hasattr(self, 'parent') and hasattr(self.parent, 'after'):
                    self.parent.after(0, lambda: func(self, *args, **kwargs))
                elif hasattr(self, 'winfo_toplevel'):
                    root = self.winfo_toplevel()
                    root.after(0, lambda: func(self, *args, **kwargs))
                else:
                    # If we can't schedule, just run it directly but log a debug message
                    logger.debug(f"Running {func.__name__} directly - no main thread scheduler found")
                    return func(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Failed to schedule {func.__name__} on main thread: {e}")
                return None
        else:
            return func(self, *args, **kwargs)
    return wrapper