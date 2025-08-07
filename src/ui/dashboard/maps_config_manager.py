"""Maps Configuration Manager for Weather Dashboard.

This module provides configuration management for the maps interface,
including user preferences, layer settings, and performance options.
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class MapsConfigManager:
    """Manages configuration for the maps interface."""
    
    def __init__(self, config_service=None, config_file: Optional[str] = None):
        """Initialize the maps configuration manager.
        
        Args:
            config_service: Main application config service
            config_file: Optional path to maps-specific config file
        """
        self.config_service = config_service
        self.config_file = config_file or "maps_config.json"
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.default_config = {
            'map_style': 'roadmap',
            'active_layers': ['temperature'],
            'last_latitude': 51.5074,
            'last_longitude': -0.1278,
            'last_zoom': 10,
            'layer_opacity': {
                'temperature': 0.7,
                'precipitation': 0.6,
                'wind': 0.5,
                'pressure': 0.4,
                'clouds': 0.5,
                'humidity': 0.6
            },
            'auto_refresh': True,
            'refresh_interval': 30,
            'show_help': True,
            'performance': {
                'enable_caching': True,
                'cache_size_limit': 1000,
                'viewport_loading': True,
                'throttle_updates': True,
                'lazy_loading': True
            },
            'ui_preferences': {
                'show_loading_shimmer': True,
                'fade_transitions': True,
                'keyboard_shortcuts': True,
                'tooltips_enabled': True
            },
            'weather_layers': {
                'temperature': {
                    'enabled': True,
                    'opacity': 0.7,
                    'color_scheme': 'thermal',
                    'data_density': 'medium'
                },
                'precipitation': {
                    'enabled': False,
                    'opacity': 0.6,
                    'color_scheme': 'precipitation',
                    'data_density': 'medium'
                },
                'wind': {
                    'enabled': False,
                    'opacity': 0.5,
                    'color_scheme': 'wind',
                    'data_density': 'low',
                    'show_arrows': True
                },
                'pressure': {
                    'enabled': False,
                    'opacity': 0.4,
                    'color_scheme': 'pressure',
                    'data_density': 'low'
                },
                'clouds': {
                    'enabled': False,
                    'opacity': 0.5,
                    'color_scheme': 'clouds',
                    'data_density': 'medium'
                },
                'humidity': {
                    'enabled': False,
                    'opacity': 0.6,
                    'color_scheme': 'humidity',
                    'data_density': 'medium'
                }
            }
        }
        
        # Load existing configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or config service."""
        try:
            # Try config service first
            if self.config_service:
                maps_config = self.config_service.get('maps_settings', {})
                if maps_config:
                    return self._merge_with_defaults(maps_config)
            
            # Try local config file
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    return self._merge_with_defaults(file_config)
            
        except Exception as e:
            self.logger.error(f"Error loading maps config: {e}")
        
        # Return default configuration
        return self.default_config.copy()
    
    def _merge_with_defaults(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user configuration with defaults."""
        merged = self.default_config.copy()
        
        def deep_merge(default: dict, user: dict) -> dict:
            """Recursively merge dictionaries."""
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        return deep_merge(merged, user_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def save(self) -> bool:
        """Save configuration to file and config service."""
        try:
            # Save to config service
            if self.config_service:
                self.config_service.set('maps_settings', self.config)
                self.config_service.save()
            
            # Save to local file as backup
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Maps configuration saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving maps config: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.default_config.copy()
        self.save()
        self.logger.info("Maps configuration reset to defaults")
    
    def get_layer_config(self, layer_name: str) -> Dict[str, Any]:
        """Get configuration for a specific weather layer."""
        return self.get(f'weather_layers.{layer_name}', {})
    
    def set_layer_config(self, layer_name: str, config: Dict[str, Any]) -> None:
        """Set configuration for a specific weather layer."""
        current_config = self.get_layer_config(layer_name)
        current_config.update(config)
        self.set(f'weather_layers.{layer_name}', current_config)
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.get('performance', {})
    
    def set_performance_config(self, config: Dict[str, Any]) -> None:
        """Set performance configuration."""
        current_config = self.get_performance_config()
        current_config.update(config)
        self.set('performance', current_config)
    
    def get_ui_preferences(self) -> Dict[str, Any]:
        """Get UI preferences."""
        return self.get('ui_preferences', {})
    
    def set_ui_preferences(self, preferences: Dict[str, Any]) -> None:
        """Set UI preferences."""
        current_prefs = self.get_ui_preferences()
        current_prefs.update(preferences)
        self.set('ui_preferences', current_prefs)
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            self.config = self._merge_with_defaults(imported_config)
            self.save()
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing config: {e}")
            return False
    
    def validate_config(self) -> bool:
        """Validate current configuration."""
        try:
            # Check required keys
            required_keys = ['map_style', 'last_latitude', 'last_longitude', 'last_zoom']
            for key in required_keys:
                if key not in self.config:
                    self.logger.warning(f"Missing required config key: {key}")
                    return False
            
            # Validate coordinate ranges
            lat = self.config.get('last_latitude', 0)
            lng = self.config.get('last_longitude', 0)
            
            if not (-90 <= lat <= 90):
                self.logger.warning(f"Invalid latitude: {lat}")
                return False
            
            if not (-180 <= lng <= 180):
                self.logger.warning(f"Invalid longitude: {lng}")
                return False
            
            # Validate zoom level
            zoom = self.config.get('last_zoom', 10)
            if not (1 <= zoom <= 20):
                self.logger.warning(f"Invalid zoom level: {zoom}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating config: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        return {
            'map_style': self.get('map_style'),
            'last_position': {
                'latitude': self.get('last_latitude'),
                'longitude': self.get('last_longitude'),
                'zoom': self.get('last_zoom')
            },
            'active_layers': self.get('active_layers', []),
            'auto_refresh': self.get('auto_refresh'),
            'refresh_interval': self.get('refresh_interval'),
            'performance_enabled': self.get('performance.enable_caching'),
            'ui_features': {
                'loading_shimmer': self.get('ui_preferences.show_loading_shimmer'),
                'fade_transitions': self.get('ui_preferences.fade_transitions'),
                'keyboard_shortcuts': self.get('ui_preferences.keyboard_shortcuts')
            }
        }