import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class WindowStateManager:
    def __init__(self, config_file="data/window_config.json"):
        self.config_file = config_file
        self.window_locked = False  # Add lock flag
        self.default_config = {
            "start_maximized": True,
            "remember_size": False,  # Changed to False to always maximize
            "lock_maximized": True,  # Add lock flag
            "last_width": 1920,
            "last_height": 1080,
            "last_x": 0,
            "last_y": 0,
            "window_state": "zoomed"
        }
    
    def load_window_config(self):
        """Load window configuration with fallback to defaults."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged_config = self.default_config.copy()
                    merged_config.update(config)
                    return merged_config
        except Exception as e:
            logger.warning(f"Failed to load window config: {e}")
        
        return self.default_config.copy()
    
    def save_window_config(self, window):
        """Save current window configuration."""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config = {
                "start_maximized": window.state() == 'zoomed',
                "remember_size": True,
                "last_width": window.winfo_width(),
                "last_height": window.winfo_height(),
                "last_x": window.winfo_x(),
                "last_y": window.winfo_y(),
                "window_state": window.state()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info("Window configuration saved")
            
        except Exception as e:
            logger.error(f"Failed to save window config: {e}")
    
    def apply_window_state(self, window):
        """Apply window state with locking mechanism."""
        config = self.load_window_config()
        
        try:
            # Always start maximized for professional appearance
            self.lock_window_state(window)
            window.state('zoomed')
            logger.info("Window set to maximized state with lock")
            
            # Prevent resizing during initialization
            window.resizable(False, False)
            window.after(2000, lambda: self.unlock_window_state(window))  # Unlock after 2 seconds
            
        except Exception as e:
            logger.error(f"Failed to apply window state: {e}")
            window.geometry("1920x1080+0+0")
    
    def lock_window_state(self, window):
        """Lock window state to prevent unwanted resizing."""
        self.window_locked = True
        # Override window manager events
        window.bind('<Configure>', self.on_configure_locked)
    
    def unlock_window_state(self, window):
        """Unlock window state and allow normal resizing."""
        self.window_locked = False
        window.resizable(True, True)
        # Restore normal configure event handling
        window.bind('<Configure>', lambda e: self.on_configure_normal(e, window))
        logger.info("Window state unlocked - normal resizing enabled")
    
    def on_configure_locked(self, event):
        """Handle configure events while locked - prevent resizing."""
        if self.window_locked and event.widget.winfo_class() == 'Tk':
            # Force back to maximized if someone tries to resize
            try:
                event.widget.state('zoomed')
            except:
                pass
    
    def on_configure_normal(self, event, window):
        """Handle normal configure events after unlock."""
        # Allow normal window behavior
        pass