"""Timer Manager

Centralized timer management for safe scheduling and cleanup of all application timers.
Provides thread-safe timer operations and automatic cleanup on shutdown.
"""

import logging
import threading
from typing import Callable, Dict, Optional
import customtkinter as ctk

logger = logging.getLogger(__name__)


class TimerManager:
    """Manage all application timers safely with centralized control."""
    
    def __init__(self, root: ctk.CTk):
        """Initialize timer manager.
        
        Args:
            root: Root CTk window for scheduling timers
        """
        self.root = root
        self.timers: Dict[str, str] = {}  # name -> timer_id mapping
        self.running = True
        self._lock = threading.Lock()
        
        logger.info("TimerManager initialized")
        
    def schedule(self, name: str, interval_ms: int, 
                callback: Callable, start_immediately: bool = True) -> bool:
        """Schedule a recurring timer.
        
        Args:
            name: Unique timer name
            interval_ms: Interval in milliseconds
            callback: Function to call on timer
            start_immediately: Whether to start immediately or wait for interval
            
        Returns:
            bool: True if timer was scheduled successfully
        """
        if not self.running:
            logger.warning(f"Cannot schedule timer '{name}' - manager is shutting down")
            return False
            
        with self._lock:
            # Cancel existing timer with same name
            self.cancel(name)
            
            def timer_callback():
                """Internal timer callback with error handling."""
                if not self.running:
                    return
                    
                try:
                    # Check if root window still exists
                    if hasattr(self.root, 'winfo_exists') and not self.root.winfo_exists():
                        logger.warning(f"Root window destroyed, canceling timer '{name}'")
                        self.cancel(name)
                        return
                        
                    # Execute callback
                    callback()
                    
                except Exception as e:
                    logger.error(f"Timer '{name}' callback error: {e}")
                
                # Reschedule if still running
                with self._lock:
                    if self.running and name in self.timers:
                        try:
                            timer_id = self.root.after(interval_ms, timer_callback)
                            self.timers[name] = timer_id
                        except Exception as e:
                            logger.error(f"Failed to reschedule timer '{name}': {e}")
                            if name in self.timers:
                                del self.timers[name]
            
            try:
                # Start timer
                if start_immediately:
                    # Execute immediately, then schedule next
                    self.root.after_idle(timer_callback)
                else:
                    # Schedule for first execution
                    timer_id = self.root.after(interval_ms, timer_callback)
                    self.timers[name] = timer_id
                    
                logger.debug(f"Timer '{name}' scheduled with {interval_ms}ms interval")
                return True
                
            except Exception as e:
                logger.error(f"Failed to schedule timer '{name}': {e}")
                return False
    
    def schedule_once(self, name: str, delay_ms: int, callback: Callable) -> bool:
        """Schedule a one-time timer.
        
        Args:
            name: Unique timer name
            delay_ms: Delay in milliseconds
            callback: Function to call after delay
            
        Returns:
            bool: True if timer was scheduled successfully
        """
        if not self.running:
            logger.warning(f"Cannot schedule one-time timer '{name}' - manager is shutting down")
            return False
            
        with self._lock:
            # Cancel existing timer with same name
            self.cancel(name)
            
            def one_time_callback():
                """One-time callback with cleanup."""
                try:
                    # Check if root window still exists
                    if hasattr(self.root, 'winfo_exists') and not self.root.winfo_exists():
                        logger.warning(f"Root window destroyed, canceling one-time timer '{name}'")
                        return
                        
                    # Execute callback
                    callback()
                    
                except Exception as e:
                    logger.error(f"One-time timer '{name}' callback error: {e}")
                finally:
                    # Clean up timer reference
                    with self._lock:
                        if name in self.timers:
                            del self.timers[name]
            
            try:
                timer_id = self.root.after(delay_ms, one_time_callback)
                self.timers[name] = timer_id
                logger.debug(f"One-time timer '{name}' scheduled with {delay_ms}ms delay")
                return True
                
            except Exception as e:
                logger.error(f"Failed to schedule one-time timer '{name}': {e}")
                return False
    
    def cancel(self, name: str) -> bool:
        """Cancel a timer.
        
        Args:
            name: Timer name to cancel
            
        Returns:
            bool: True if timer was found and canceled
        """
        with self._lock:
            if name in self.timers:
                try:
                    self.root.after_cancel(self.timers[name])
                    del self.timers[name]
                    logger.debug(f"Timer '{name}' canceled")
                    return True
                except Exception as e:
                    logger.error(f"Failed to cancel timer '{name}': {e}")
                    # Remove from tracking even if cancel failed
                    if name in self.timers:
                        del self.timers[name]
                    return False
            return False
    
    def is_running(self, name: str) -> bool:
        """Check if a timer is currently running.
        
        Args:
            name: Timer name to check
            
        Returns:
            bool: True if timer is running
        """
        with self._lock:
            return name in self.timers
    
    def get_active_timers(self) -> list:
        """Get list of active timer names.
        
        Returns:
            list: List of active timer names
        """
        with self._lock:
            return list(self.timers.keys())
    
    def shutdown(self):
        """Cancel all timers and shutdown manager."""
        logger.info("Shutting down TimerManager")
        
        with self._lock:
            self.running = False
            
            # Cancel all active timers
            timer_names = list(self.timers.keys())
            for name in timer_names:
                try:
                    self.root.after_cancel(self.timers[name])
                    logger.debug(f"Canceled timer '{name}' during shutdown")
                except Exception as e:
                    logger.error(f"Error canceling timer '{name}' during shutdown: {e}")
            
            # Clear all timer references
            self.timers.clear()
            
        logger.info(f"TimerManager shutdown complete. Canceled {len(timer_names)} timers")
    
    def __del__(self):
        """Ensure cleanup on destruction."""
        if hasattr(self, 'running') and self.running:
            try:
                self.shutdown()
            except Exception:
                pass  # Ignore errors during destruction