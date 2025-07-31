#!/usr/bin/env python3
"""
Configuration Manager for Weather Dashboard Scripts

Provides centralized configuration management with:
- YAML configuration file support
- Environment-specific overrides
- Schema validation
- Default value handling
- Configuration merging
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class ConfigSchema:
    """Base configuration schema."""
    
    # Common settings
    project_name: str = "Weather Dashboard"
    version: str = "1.0.0"
    environment: str = "development"
    
    # Logging settings
    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True
    
    # File operation settings
    dry_run: bool = True
    backup_enabled: bool = True
    
    # Performance settings
    max_workers: int = 4
    timeout_seconds: int = 30
    
    # Custom settings (script-specific)
    custom: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """Manages configuration for Weather Dashboard scripts."""
    
    def __init__(self, project_root: Path, config_name: str = "scripts_config.yaml"):
        self.project_root = project_root
        self.config_dir = project_root / "scripts" / "config"
        self.config_file = self.config_dir / config_name
        self.schema = ConfigSchema()
        self._config_data: Dict[str, Any] = {}
        self._loaded = False
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file and environment."""
        # Start with default schema values
        self._config_data = self._schema_to_dict(self.schema)
        
        # Load from file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                self._merge_config(file_config)
            except Exception as e:
                print(f"Warning: Failed to load config file {self.config_file}: {e}")
        else:
            # Create default config file
            self._create_default_config()
        
        # Apply environment overrides
        self._apply_environment_overrides()
        
        self._loaded = True
    
    def _schema_to_dict(self, schema: ConfigSchema) -> Dict[str, Any]:
        """Convert schema dataclass to dictionary."""
        result = {}
        for field_name, field_def in schema.__dataclass_fields__.items():
            value = getattr(schema, field_name)
            result[field_name] = deepcopy(value)
        return result
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """Merge new configuration with existing configuration."""
        def merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
            result = deepcopy(base)
            for key, value in update.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = deepcopy(value)
            return result
        
        self._config_data = merge_dicts(self._config_data, new_config)
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides."""
        env_prefix = "WD_SCRIPT_"
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                # Convert string values to appropriate types
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
                
                self._config_data[config_key] = value
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = {
            'project_name': 'Weather Dashboard',
            'version': '1.0.0',
            'environment': 'development',
            
            'logging': {
                'level': 'INFO',
                'to_file': True,
                'to_console': True,
                'max_file_size_mb': 10,
                'backup_count': 5
            },
            
            'operations': {
                'dry_run': True,
                'backup_enabled': True,
                'max_workers': 4,
                'timeout_seconds': 30
            },
            
            'cleanup': {
                'cache_retention_days': 7,
                'export_retention_days': 30,
                'aggressive_mode': False,
                'patterns': {
                    'legacy': [
                        '.*_legacy\.py$',
                        '.*_backup\.py$',
                        '.*_old\.py$',
                        '.*\.py\.bak$',
                        '.*~$',
                        '.*\.orig$',
                        '.*\.tmp$'
                    ],
                    'weather_cache': [
                        '**/weather_cache*.json',
                        '**/cache/*.json',
                        '**/temp_weather_data*.json',
                        '**/forecast_cache*.json'
                    ],
                    'chart_exports': [
                        '**/exports/*.png',
                        '**/exports/*.pdf',
                        '**/chart_exports/*.png'
                    ]
                }
            },
            
            'quality_checks': {
                'tools': {
                    'black': {
                        'enabled': True,
                        'args': ['--check', '--diff']
                    },
                    'isort': {
                        'enabled': True,
                        'args': ['--check-only', '--diff']
                    },
                    'flake8': {
                        'enabled': True,
                        'args': ['--config=setup.cfg']
                    },
                    'mypy': {
                        'enabled': True,
                        'args': ['--config-file=setup.cfg']
                    }
                },
                'parallel_execution': True,
                'fail_fast': False
            },
            
            'mcp_servers': {
                'timeout': 10,
                'retry_count': 3,
                'servers': {
                    'blender': {
                        'command': 'uvx blender-mcp',
                        'description': 'Blender MCP Server'
                    },
                    'fetch': {
                        'command': 'uvx mcp-server-fetch',
                        'description': 'Fetch MCP Server'
                    }
                }
            }
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to create default config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        if not self._loaded:
            self._load_config()
        
        keys = key.split('.')
        value = self._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key (supports dot notation)."""
        keys = key.split('.')
        config = self._config_data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def load_custom_config(self, config_path: Union[str, Path]) -> None:
        """Load additional configuration from custom file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                custom_config = yaml.safe_load(f) or {}
            self._merge_config(custom_config)
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}")
    
    def save_config(self, config_path: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        if config_path is None:
            config_path = self.config_file
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save configuration to {config_path}: {e}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.get(section, {})
    
    def validate_config(self) -> bool:
        """Validate configuration against schema."""
        # Basic validation - can be extended with more sophisticated schema validation
        required_keys = ['project_name', 'version', 'environment']
        
        for key in required_keys:
            if self.get(key) is None:
                return False
        
        return True
    
    def get_environment_config(self, environment: str = None) -> Dict[str, Any]:
        """Get environment-specific configuration."""
        if environment is None:
            environment = self.get('environment', 'development')
        
        env_config = self.get(f'environments.{environment}', {})
        
        # Merge with base config
        base_config = deepcopy(self._config_data)
        if env_config:
            self._merge_config(env_config)
        
        return base_config
    
    @property
    def config_data(self) -> Dict[str, Any]:
        """Get read-only copy of configuration data."""
        return deepcopy(self._config_data)