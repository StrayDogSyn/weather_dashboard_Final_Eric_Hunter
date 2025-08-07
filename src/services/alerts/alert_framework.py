"""Alert Framework System

Configurable alert threshold system and notification framework for weather alerts.
Provides a foundation for future integration with real alert APIs.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from pathlib import Path


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    EXTREME = "extreme"


class AlertType(Enum):
    """Types of weather alerts."""
    TEMPERATURE = "temperature"
    PRECIPITATION = "precipitation"
    WIND = "wind"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    AIR_QUALITY = "air_quality"
    UV_INDEX = "uv_index"
    STORM = "storm"
    FLOOD = "flood"
    FIRE_WEATHER = "fire_weather"


@dataclass
class AlertThreshold:
    """Configuration for alert thresholds."""
    alert_type: AlertType
    severity: AlertSeverity
    condition: str  # e.g., ">", "<", "==", "between"
    value: float
    value_max: Optional[float] = None  # For "between" conditions
    unit: str = ""
    message_template: str = ""
    enabled: bool = True
    duration_minutes: int = 0  # Minimum duration for sustained conditions


@dataclass
class WeatherAlert:
    """Weather alert instance."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    expires_at: Optional[datetime] = None
    location: str = ""
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    unit: str = ""
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertFramework:
    """Configurable alert threshold system and notification framework."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the alert framework.
        
        Args:
            config_path: Path to alert configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or "config/alert_thresholds.json"
        
        # Alert storage
        self.active_alerts: Dict[str, WeatherAlert] = {}
        self.alert_history: List[WeatherAlert] = []
        
        # Thresholds and callbacks
        self.thresholds: List[AlertThreshold] = []
        self.notification_callbacks: List[Callable[[WeatherAlert], None]] = []
        
        # Load configuration
        self._load_default_thresholds()
        self._load_config()
        
    def _load_default_thresholds(self):
        """Load default alert thresholds."""
        default_thresholds = [
            # Temperature alerts
            AlertThreshold(
                alert_type=AlertType.TEMPERATURE,
                severity=AlertSeverity.HIGH,
                condition=">",
                value=35.0,
                unit="°C",
                message_template="High temperature alert: {current_value}°C (threshold: {threshold_value}°C)",
                duration_minutes=30
            ),
            AlertThreshold(
                alert_type=AlertType.TEMPERATURE,
                severity=AlertSeverity.HIGH,
                condition="<",
                value=-10.0,
                unit="°C",
                message_template="Low temperature alert: {current_value}°C (threshold: {threshold_value}°C)",
                duration_minutes=30
            ),
            
            # Wind alerts
            AlertThreshold(
                alert_type=AlertType.WIND,
                severity=AlertSeverity.MODERATE,
                condition=">",
                value=15.0,
                unit="m/s",
                message_template="High wind alert: {current_value} m/s (threshold: {threshold_value} m/s)",
                duration_minutes=15
            ),
            AlertThreshold(
                alert_type=AlertType.WIND,
                severity=AlertSeverity.SEVERE,
                condition=">",
                value=25.0,
                unit="m/s",
                message_template="Severe wind alert: {current_value} m/s (threshold: {threshold_value} m/s)",
                duration_minutes=10
            ),
            
            # Precipitation alerts
            AlertThreshold(
                alert_type=AlertType.PRECIPITATION,
                severity=AlertSeverity.MODERATE,
                condition=">",
                value=80.0,
                unit="%",
                message_template="High precipitation probability: {current_value}% (threshold: {threshold_value}%)"
            ),
            
            # Air quality alerts
            AlertThreshold(
                alert_type=AlertType.AIR_QUALITY,
                severity=AlertSeverity.MODERATE,
                condition=">",
                value=100,
                unit="AQI",
                message_template="Poor air quality: AQI {current_value} (threshold: {threshold_value})"
            ),
            AlertThreshold(
                alert_type=AlertType.AIR_QUALITY,
                severity=AlertSeverity.HIGH,
                condition=">",
                value=150,
                unit="AQI",
                message_template="Unhealthy air quality: AQI {current_value} (threshold: {threshold_value})"
            ),
            
            # UV Index alerts
            AlertThreshold(
                alert_type=AlertType.UV_INDEX,
                severity=AlertSeverity.MODERATE,
                condition=">",
                value=6,
                unit="UV",
                message_template="High UV exposure: UV Index {current_value} (threshold: {threshold_value})"
            ),
            AlertThreshold(
                alert_type=AlertType.UV_INDEX,
                severity=AlertSeverity.HIGH,
                condition=">",
                value=8,
                unit="UV",
                message_template="Very high UV exposure: UV Index {current_value} (threshold: {threshold_value})"
            ),
        ]
        
        self.thresholds.extend(default_thresholds)
        
    def _load_config(self):
        """Load alert configuration from file."""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    
                # Load custom thresholds
                if 'thresholds' in config_data:
                    for threshold_data in config_data['thresholds']:
                        threshold = AlertThreshold(
                            alert_type=AlertType(threshold_data['alert_type']),
                            severity=AlertSeverity(threshold_data['severity']),
                            condition=threshold_data['condition'],
                            value=threshold_data['value'],
                            value_max=threshold_data.get('value_max'),
                            unit=threshold_data.get('unit', ''),
                            message_template=threshold_data.get('message_template', ''),
                            enabled=threshold_data.get('enabled', True),
                            duration_minutes=threshold_data.get('duration_minutes', 0)
                        )
                        self.thresholds.append(threshold)
                        
                self.logger.info(f"Loaded alert configuration from {self.config_path}")
            else:
                self.logger.info("No custom alert configuration found, using defaults")
                
        except Exception as e:
            self.logger.error(f"Error loading alert configuration: {e}")
            
    def save_config(self):
        """Save current alert configuration to file."""
        try:
            config_data = {
                'thresholds': [
                    {
                        'alert_type': threshold.alert_type.value,
                        'severity': threshold.severity.value,
                        'condition': threshold.condition,
                        'value': threshold.value,
                        'value_max': threshold.value_max,
                        'unit': threshold.unit,
                        'message_template': threshold.message_template,
                        'enabled': threshold.enabled,
                        'duration_minutes': threshold.duration_minutes
                    }
                    for threshold in self.thresholds
                ]
            }
            
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            self.logger.info(f"Saved alert configuration to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving alert configuration: {e}")
            
    def add_threshold(self, threshold: AlertThreshold):
        """Add a new alert threshold."""
        self.thresholds.append(threshold)
        self.logger.info(f"Added alert threshold: {threshold.alert_type.value} {threshold.condition} {threshold.value}")
        
    def remove_threshold(self, alert_type: AlertType, condition: str, value: float):
        """Remove an alert threshold."""
        self.thresholds = [
            t for t in self.thresholds 
            if not (t.alert_type == alert_type and t.condition == condition and t.value == value)
        ]
        
    def add_notification_callback(self, callback: Callable[[WeatherAlert], None]):
        """Add a notification callback function."""
        self.notification_callbacks.append(callback)
        
    def check_weather_data(self, weather_data: Dict[str, Any], location: str = "") -> List[WeatherAlert]:
        """Check weather data against all thresholds and generate alerts.
        
        Args:
            weather_data: Dictionary containing weather measurements
            location: Location name for the alert
            
        Returns:
            List of new alerts generated
        """
        new_alerts = []
        
        # Map weather data to alert types
        data_mapping = {
            AlertType.TEMPERATURE: weather_data.get('temperature'),
            AlertType.WIND: weather_data.get('wind_speed'),
            AlertType.HUMIDITY: weather_data.get('humidity'),
            AlertType.PRESSURE: weather_data.get('pressure'),
            AlertType.AIR_QUALITY: weather_data.get('aqi'),
            AlertType.UV_INDEX: weather_data.get('uv_index'),
            AlertType.PRECIPITATION: weather_data.get('precipitation_probability')
        }