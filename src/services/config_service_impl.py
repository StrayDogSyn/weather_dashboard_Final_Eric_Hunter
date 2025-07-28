#!/usr/bin/env python3
"""
Configuration Service Implementation for Dependency Injection

This module provides the concrete implementation of IConfigurationService interface,
adapting the existing configuration system to work with the dependency injection system.
It demonstrates how to bridge existing configuration code with new DI patterns.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0 (Dependency Injection Implementation)
"""

import os
import json
from typing import Any, Dict, Optional, List
from pathlib import Path

from core.interfaces import IConfigurationService, ILoggingService
from core.config_manager import ConfigManager


class ConfigurationServiceImpl(IConfigurationService):
    """Implementation of IConfigurationService using the existing ConfigManager.
    
    This adapter class bridges the existing ConfigManager with the new
    dependency injection interface, demonstrating how to integrate legacy
    configuration code with modern DI patterns.
    """
    
    def __init__(self, 
                 config_file_path: Optional[str] = None,
                 logger_service: Optional[ILoggingService] = None):
        """Initialize the configuration service implementation.
        
        Args:
            config_file_path: Optional path to configuration file
            logger_service: Optional logging service
        """
        self._logger_service = logger_service
        self._config_file_path = config_file_path or "config/settings.json"
        
        # Initialize the underlying config manager
        self._config_manager = ConfigManager()
        
        # Load additional configuration from file if it exists
        self._custom_config: Dict[str, Any] = {}
        self._load_custom_config()
        
        self._log_info(f"ConfigurationServiceImpl initialized with config file: {self._config_file_path}")
    
    def _log_info(self, message: str, **kwargs) -> None:
        """Log an info message if logger service is available."""
        if self._logger_service:
            self._logger_service.info(message, **kwargs)
    
    def _log_error(self, message: str, **kwargs) -> None:
        """Log an error message if logger service is available."""
        if self._logger_service:
            self._logger_service.error(message, **kwargs)
    
    def _log_warning(self, message: str, **kwargs) -> None:
        """Log a warning message if logger service is available."""
        if self._logger_service:
            self._logger_service.warning(message, **kwargs)
    
    def _load_custom_config(self) -> None:
        """Load custom configuration from file."""
        try:
            config_path = Path(self._config_file_path)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._custom_config = json.load(f)
                self._log_info(f"Loaded custom configuration from {self._config_file_path}")
            else:
                self._log_info(f"No custom configuration file found at {self._config_file_path}")
                # Create default configuration
                self._create_default_config()
        except Exception as e:
            self._log_error(f"Error loading custom configuration: {e}")
            self._custom_config = {}
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        try:
            default_config = {
                "database": {
                    "path": "data/weather_dashboard.db",
                    "backup_enabled": True,
                    "backup_interval_hours": 24
                },
                "weather": {
                    "default_location": "New York",
                    "update_interval_minutes": 30,
                    "cache_duration_hours": 1,
                    "providers": {
                        "openweathermap": {
                            "enabled": True,
                            "priority": 1
                        },
                        "weatherapi": {
                            "enabled": True,
                            "priority": 2
                        }
                    }
                },
                "ui": {
                    "theme": "dark",
                    "auto_refresh": True,
                    "show_notifications": True,
                    "temperature_unit": "celsius"
                },
                "logging": {
                    "level": "INFO",
                    "file_enabled": True,
                    "file_path": "logs/weather_dashboard.log",
                    "max_file_size_mb": 10,
                    "backup_count": 5
                },
                "services": {
                    "github": {
                        "enabled": False,
                        "cache_duration_hours": 6
                    },
                    "spotify": {
                        "enabled": False,
                        "cache_duration_hours": 1
                    },
                    "gemini": {
                        "enabled": False,
                        "model": "gemini-pro"
                    }
                }
            }
            
            # Ensure directory exists
            config_path = Path(self._config_file_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save default configuration
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            self._custom_config = default_config
            self._log_info(f"Created default configuration file at {self._config_file_path}")
            
        except Exception as e:
            self._log_error(f"Error creating default configuration: {e}")
    
    def _get_nested_value(self, config_dict: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """Get a nested value from configuration dictionary using dot notation.
        
        Args:
            config_dict: Configuration dictionary
            key_path: Dot-separated key path (e.g., 'database.path')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = key_path.split('.')
            value = config_dict
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def _set_nested_value(self, config_dict: Dict[str, Any], key_path: str, value: Any) -> None:
        """Set a nested value in configuration dictionary using dot notation.
        
        Args:
            config_dict: Configuration dictionary
            key_path: Dot-separated key path (e.g., 'database.path')
            value: Value to set
        """
        try:
            keys = key_path.split('.')
            current = config_dict
            
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the final value
            current[keys[-1]] = value
            
        except Exception as e:
            self._log_error(f"Error setting nested value {key_path}: {e}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting.
        
        Args:
            key: Setting key (supports dot notation for nested keys)
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        try:
            # First try custom configuration
            value = self._get_nested_value(self._custom_config, key)
            if value is not None:
                return value
            
            # Then try legacy config manager
            if hasattr(self._config_manager, 'get_setting'):
                value = self._config_manager.get_setting(key, default)
                if value != default:
                    return value
            
            # Finally try environment variables
            env_key = key.upper().replace('.', '_')
            env_value = os.getenv(env_key)
            if env_value is not None:
                # Try to parse as JSON for complex types
                try:
                    return json.loads(env_value)
                except json.JSONDecodeError:
                    return env_value
            
            return default
            
        except Exception as e:
            self._log_error(f"Error getting setting {key}: {e}")
            return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a configuration setting.
        
        Args:
            key: Setting key (supports dot notation for nested keys)
            value: Setting value
            
        Returns:
            True if setting was saved successfully, False otherwise
        """
        try:
            # Set in custom configuration
            self._set_nested_value(self._custom_config, key, value)
            
            # Save to file
            success = self._save_custom_config()
            
            if success:
                self._log_info(f"Setting saved: {key} = {value}")
            else:
                self._log_warning(f"Failed to save setting: {key}")
            
            return success
            
        except Exception as e:
            self._log_error(f"Error setting {key}: {e}")
            return False
    
    def _save_custom_config(self) -> bool:
        """Save custom configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            config_path = Path(self._config_file_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._custom_config, f, indent=2)
            
            return True
            
        except Exception as e:
            self._log_error(f"Error saving custom configuration: {e}")
            return False
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all configuration settings.
        
        Returns:
            Dictionary containing all settings
        """
        try:
            # Combine custom config with legacy config
            all_settings = self._custom_config.copy()
            
            # Add legacy config manager settings if available
            if hasattr(self._config_manager, 'get_all_settings'):
                legacy_settings = self._config_manager.get_all_settings()
                if isinstance(legacy_settings, dict):
                    # Merge legacy settings (custom config takes precedence)
                    for key, value in legacy_settings.items():
                        if key not in all_settings:
                            all_settings[key] = value
            
            self._log_info(f"Retrieved {len(all_settings)} configuration settings")
            return all_settings
            
        except Exception as e:
            self._log_error(f"Error getting all settings: {e}")
            return {}
    
    def has_setting(self, key: str) -> bool:
        """Check if a configuration setting exists.
        
        Args:
            key: Setting key to check
            
        Returns:
            True if setting exists, False otherwise
        """
        try:
            # Check custom configuration
            value = self._get_nested_value(self._custom_config, key)
            if value is not None:
                return True
            
            # Check legacy config manager
            if hasattr(self._config_manager, 'has_setting'):
                if self._config_manager.has_setting(key):
                    return True
            
            # Check environment variables
            env_key = key.upper().replace('.', '_')
            return os.getenv(env_key) is not None
            
        except Exception as e:
            self._log_error(f"Error checking setting {key}: {e}")
            return False
    
    def reload_configuration(self) -> bool:
        """Reload configuration from file.
        
        Returns:
            True if reloaded successfully, False otherwise
        """
        try:
            self._load_custom_config()
            
            # Reload legacy config manager if possible
            if hasattr(self._config_manager, 'reload'):
                self._config_manager.reload()
            
            self._log_info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            self._log_error(f"Error reloading configuration: {e}")
            return False
    
    def get_configuration_info(self) -> Dict[str, Any]:
        """Get information about the configuration system.
        
        Returns:
            Dictionary containing configuration system information
        """
        try:
            config_path = Path(self._config_file_path)
            
            info = {
                'config_file_path': str(config_path.absolute()),
                'config_file_exists': config_path.exists(),
                'config_file_size': config_path.stat().st_size if config_path.exists() else 0,
                'settings_count': len(self._custom_config),
                'has_legacy_config': hasattr(self._config_manager, 'get_all_settings'),
                'environment_variables': {
                    key: value for key, value in os.environ.items() 
                    if key.startswith(('WEATHER_', 'APP_', 'DATABASE_'))
                }
            }
            
            self._log_info("Retrieved configuration system information")
            return info
            
        except Exception as e:
            self._log_error(f"Error getting configuration info: {e}")
            return {}
    
    # ============================================================================
    # IConfigurationService Interface Implementation
    # ============================================================================
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value (IConfigurationService interface method).
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.get_setting(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value (IConfigurationService interface method).
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.set_setting(key, value)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section (IConfigurationService interface method).
        
        Args:
            section: Section name
            
        Returns:
            Dictionary of configuration values
        """
        try:
            # Get section from custom configuration
            section_data = self._get_nested_value(self._custom_config, section, {})
            if isinstance(section_data, dict):
                return section_data.copy()
            
            # If not found or not a dict, return empty dict
            self._log_warning(f"Section '{section}' not found or not a dictionary")
            return {}
            
        except Exception as e:
            self._log_error(f"Error getting section {section}: {e}")
            return {}


class MockConfigurationService(IConfigurationService):
    """Mock configuration service implementation for testing.
    
    This class provides a mock implementation of IConfigurationService
    that can be used for unit testing and development scenarios
    where real configuration is not needed.
    """
    
    def __init__(self, logger_service: Optional[ILoggingService] = None):
        """Initialize the mock configuration service.
        
        Args:
            logger_service: Optional logging service
        """
        self._logger_service = logger_service
        self._settings: Dict[str, Any] = {
            'database.path': 'mock://database.db',
            'weather.default_location': 'Mock City',
            'weather.update_interval_minutes': 30,
            'ui.theme': 'dark',
            'ui.temperature_unit': 'celsius',
            'logging.level': 'INFO'
        }
        self._should_fail = False
        
        self._log_info("MockConfigurationService initialized")
    
    def _log_info(self, message: str, **kwargs) -> None:
        """Log an info message if logger service is available."""
        if self._logger_service:
            self._logger_service.info(message, **kwargs)
    
    def set_should_fail(self, should_fail: bool) -> None:
        """Set whether the service should simulate failures.
        
        Args:
            should_fail: Whether to simulate failures
        """
        self._should_fail = should_fail
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a mock configuration setting.
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        if self._should_fail:
            self._log_info(f"MockConfigurationService simulating failure for get_setting: {key}")
            return default
        
        value = self._settings.get(key, default)
        self._log_info(f"MockConfigurationService returning setting {key} = {value}")
        return value
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a mock configuration setting.
        
        Args:
            key: Setting key
            value: Setting value
            
        Returns:
            True if setting was saved successfully, False if simulating failure
        """
        if self._should_fail:
            self._log_info(f"MockConfigurationService simulating failure for set_setting: {key}")
            return False
        
        self._settings[key] = value
        self._log_info(f"MockConfigurationService set setting {key} = {value}")
        return True
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all mock configuration settings.
        
        Returns:
            Dictionary containing all mock settings
        """
        if self._should_fail:
            self._log_info("MockConfigurationService simulating failure for get_all_settings")
            return {}
        
        self._log_info(f"MockConfigurationService returning {len(self._settings)} settings")
        return self._settings.copy()
    
    def has_setting(self, key: str) -> bool:
        """Check if a mock configuration setting exists.
        
        Args:
            key: Setting key to check
            
        Returns:
            True if setting exists, False otherwise
        """
        if self._should_fail:
            self._log_info(f"MockConfigurationService simulating failure for has_setting: {key}")
            return False
        
        exists = key in self._settings
        self._log_info(f"MockConfigurationService has_setting {key}: {exists}")
        return exists
    
    def reload_configuration(self) -> bool:
        """Reload mock configuration.
        
        Returns:
            True unless simulating failure
        """
        if self._should_fail:
            self._log_info("MockConfigurationService simulating failure for reload_configuration")
            return False
        
        self._log_info("MockConfigurationService configuration reloaded")
        return True
    
    def get_configuration_info(self) -> Dict[str, Any]:
        """Get mock configuration system information.
        
        Returns:
            Dictionary containing mock configuration information
        """
        if self._should_fail:
            self._log_info("MockConfigurationService simulating failure for get_configuration_info")
            return {}
        
        info = {
            'config_file_path': 'mock://config.json',
            'config_file_exists': True,
            'config_file_size': 1024,
            'settings_count': len(self._settings),
            'has_legacy_config': False,
            'environment_variables': {},
            'should_fail': self._should_fail
        }
        
        self._log_info("MockConfigurationService returning configuration info")
        return info
    
    # ============================================================================
    # IConfigurationService Interface Implementation
    # ============================================================================
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value (IConfigurationService interface method).
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.get_setting(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value (IConfigurationService interface method).
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.set_setting(key, value)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section (IConfigurationService interface method).
        
        Args:
            section: Section name
            
        Returns:
            Dictionary of configuration values
        """
        if self._should_fail:
            self._log_info(f"MockConfigurationService simulating failure for get_section: {section}")
            return {}
        
        # Filter settings that start with the section prefix
        section_prefix = f"{section}."
        section_data = {}
        
        for key, value in self._settings.items():
            if key.startswith(section_prefix):
                # Remove the section prefix from the key
                sub_key = key[len(section_prefix):]
                section_data[sub_key] = value
        
        self._log_info(f"MockConfigurationService returning section {section} with {len(section_data)} items")
        return section_data