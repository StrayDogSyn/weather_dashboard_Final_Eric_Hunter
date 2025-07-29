import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class WindowStateManager:
    def __init__(self, config_file="data/window_config.json"):
        self.config_file = config_file
        self.default_config = {
            "start_maximized": True,
            "remember_size": True,
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
        """Apply saved window state to window."""
        config = self.load_window_config()
        
        try:
            if config.get("start_maximized", True):
                # Force maximized startup
                window.state('zoomed')
                logger.info("Window set to maximized state")
            else:
                # Use saved dimensions
                width = config.get("last_width", 1920)
                height = config.get("last_height", 1080)
                x = config.get("last_x", 0)
                y = config.get("last_y", 0)
                window.geometry(f"{width}x{height}+{x}+{y}")
                logger.info(f"Window set to saved dimensions: {width}x{height}")
                
        except Exception as e:
            logger.error(f"Failed to apply window state: {e}")
            # Fallback to large geometry
            window.geometry("1920x1080+0+0")