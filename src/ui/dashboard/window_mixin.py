"""Window Management Mixin

Handles window creation, configuration, and state management.
"""

import customtkinter as ctk
from typing import Optional

from .base_dashboard import BaseDashboard
from services.window_manager import WindowStateManager


class WindowMixin(BaseDashboard):
    """Mixin for window management functionality."""
    
    def __init__(self):
        """Initialize window management."""
        super().__init__()
        self.window_manager: Optional[WindowStateManager] = None
    
    def _setup_window(self):
        """Configure main window properties and behavior."""
        self._log_method_call("_setup_window")
        
        # Set window title
        self.title(self.DEFAULT_WINDOW_TITLE)
        
        # Configure window properties
        self.minsize(self.MIN_WINDOW_WIDTH, self.MIN_WINDOW_HEIGHT)
        self.resizable(True, True)
        
        # Set initial geometry
        self.geometry(f"{self.MIN_WINDOW_WIDTH}x{self.MIN_WINDOW_HEIGHT}")
        
        # Configure window manager if available
        if hasattr(self, 'config') and self.config:
            try:
                # Use default window config path instead of ConfigService object
                self.window_manager = WindowStateManager("data/window_config.json")
                if self.window_manager:
                    self.window_manager.setup_window(self)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Window manager setup failed: {e}")
        
        # Configure close protocol
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Center window on screen
        self._center_window()
    
    def _center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        
        # Get window dimensions
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate center position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set window position
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _maximize_window(self):
        """Maximize the window to full screen."""
        self._log_method_call("_maximize_window")
        
        try:
            # Get screen dimensions
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Set window to full screen size
            self.geometry(f"{screen_width}x{screen_height}+0+0")
            
            if self.logger:
                self.logger.info(f"Window maximized to {screen_width}x{screen_height}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to maximize window: {e}")
    
    def _on_closing(self):
        """Handle window closing event."""
        self._log_method_call("_on_closing")
        
        try:
            # Save window state if manager is available
            if self.window_manager:
                self.window_manager.save_window_state(self)
            
            # Log shutdown
            if self.logger:
                self.logger.info("🔴 Application shutting down...")
            
            # Destroy window
            self.destroy()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during shutdown: {e}")
            # Force destroy if there's an error
            self.destroy()
    
    def _configure_window_bindings(self):
        """Configure window-level event bindings."""
        self._log_method_call("_configure_window_bindings")
        
        # Bind window resize events
        self.bind("<Configure>", self._on_window_configure)
        
        # Bind focus events
        self.bind("<FocusIn>", self._on_window_focus_in)
        self.bind("<FocusOut>", self._on_window_focus_out)
    
    def _on_window_configure(self, event):
        """Handle window configuration changes."""
        if event.widget == self and not self._resizing:
            self._resizing = True
            self.after(100, self._on_resize_complete)
    
    def _on_resize_complete(self):
        """Handle completion of window resize."""
        self._resizing = False
        
        # Update responsive layout if method exists
        if hasattr(self, '_update_responsive_layout'):
            self._update_responsive_layout()
    
    def _on_window_focus_in(self, event):
        """Handle window gaining focus."""
        if self.logger:
            self.logger.debug("Window gained focus")
    
    def _on_window_focus_out(self, event):
        """Handle window losing focus."""
        if self.logger:
            self.logger.debug("Window lost focus")