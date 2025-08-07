import time
import functools
from typing import Callable, Any

class RenderOptimizer:
    _frame_budget = 16.67  # 60fps budget in milliseconds
    
    @staticmethod
    def get_frame_budget():
        """Get the current frame budget in milliseconds"""
        return RenderOptimizer._frame_budget
    
    @staticmethod
    def set_frame_budget(fps: int):
        """Set target FPS and update frame budget"""
        RenderOptimizer._frame_budget = 1000.0 / fps
    
    @staticmethod
    def debounce(wait_ms: int, immediate: bool = False):
        """Debounce decorator for UI updates"""
        def decorator(func):
            func.timer = None
            
            def debounced(*args, **kwargs):
                def call_func():
                    func.timer = None
                    func(*args, **kwargs)
                
                if func.timer:
                    args[0].after_cancel(func.timer)
                    
                if immediate and func.timer is None:
                    func(*args, **kwargs)
                else:
                    func.timer = args[0].after(wait_ms, call_func)
            
            return debounced
        return decorator
    
    @staticmethod
    def throttle(wait_ms: int):
        """Throttle decorator to limit function calls"""
        def decorator(func):
            func.last_called = 0
            
            @functools.wraps(func)
            def throttled(*args, **kwargs):
                now = time.time() * 1000  # Convert to milliseconds
                if now - func.last_called >= wait_ms:
                    func.last_called = now
                    return func(*args, **kwargs)
            
            return throttled
        return decorator
    
    @staticmethod
    def measure_render_time(func):
        """Decorator to measure and log render times"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            
            render_time = (end_time - start_time) * 1000  # Convert to ms
            if render_time > RenderOptimizer._frame_budget:
                print(f"⚠️ Slow render: {func.__name__} took {render_time:.2f}ms (budget: {RenderOptimizer._frame_budget:.2f}ms)")
            
            return result
        return wrapper
    
    @staticmethod
    def batch_updates(widget):
        """Batch multiple UI updates"""
        class BatchContext:
            def __init__(self, widget):
                self.widget = widget
                self.updates = []
                
            def __enter__(self):
                try:
                    self.widget.configure(cursor="wait")
                except:
                    pass  # Some widgets don't support cursor
                return self
                
            def __exit__(self, *args):
                # Apply all updates at once
                for update in self.updates:
                    try:
                        update()
                    except Exception as e:
                        print(f"Batch update error: {e}")
                try:
                    self.widget.configure(cursor="")
                except:
                    pass
                
            def add_update(self, func):
                self.updates.append(func)
        
        return BatchContext(widget)