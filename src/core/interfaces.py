"""Core interfaces for the Weather Dashboard application.

Defines contracts for services, repositories, and UI components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol

from ..models.weather_models import WeatherData
from ..models.journal_models import JournalEntry


class IConfigurationService(ABC):
    """Configuration service interface."""

    @abstractmethod
    def get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key for a specific service."""
        pass

    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting."""
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate the current configuration."""
        pass


class IWeatherService(ABC):
    """Weather service interface."""

    @abstractmethod
    def get_current_weather(self, location: str) -> WeatherData:
        """Get current weather for a location."""
        pass

    @abstractmethod
    def get_forecast(self, location: str) -> List[WeatherData]:
        """Get weather forecast for a location."""
        pass

    @abstractmethod
    def search_locations(self, query: str) -> List[Dict[str, Any]]:
        """Search for locations."""
        pass


class IJournalService(ABC):
    """Journal service interface."""

    @abstractmethod
    def create_entry(self, entry: JournalEntry) -> JournalEntry:
        """Create a new journal entry."""
        pass

    @abstractmethod
    def get_entries(self, filters: Optional[Dict[str, Any]] = None) -> List[JournalEntry]:
        """Get journal entries with optional filters."""
        pass

    @abstractmethod
    def update_entry(self, entry_id: str, updates: Dict[str, Any]) -> Optional[JournalEntry]:
        """Update a journal entry."""
        pass

    @abstractmethod
    def delete_entry(self, entry_id: str) -> bool:
        """Delete a journal entry."""
        pass


class IActivityService(ABC):
    """Activity service interface."""

    @abstractmethod
    def get_activity_suggestions(self, weather_data: WeatherData) -> List[Dict[str, Any]]:
        """Get activity suggestions based on weather."""
        pass

    @abstractmethod
    def get_fallback_activities(self) -> List[Dict[str, Any]]:
        """Get fallback activities when weather data is unavailable."""
        pass


class IWeatherRepository(ABC):
    """Weather data repository interface."""

    @abstractmethod
    async def get_current_weather(self, location: str) -> WeatherData:
        """Get current weather data."""
        pass

    @abstractmethod
    async def save_weather_data(self, location: str, data: WeatherData) -> None:
        """Save weather data to cache."""
        pass

    @abstractmethod
    async def get_cached_weather(self, location: str) -> Optional[WeatherData]:
        """Get cached weather data."""
        pass


class IJournalRepository(ABC):
    """Journal data repository interface."""

    @abstractmethod
    async def save_entry(self, entry: JournalEntry) -> JournalEntry:
        """Save a journal entry."""
        pass

    @abstractmethod
    async def get_entries(self, filters: Optional[Dict[str, Any]] = None) -> List[JournalEntry]:
        """Get journal entries."""
        pass

    @abstractmethod
    async def update_entry(self, entry_id: str, updates: Dict[str, Any]) -> Optional[JournalEntry]:
        """Update a journal entry."""
        pass

    @abstractmethod
    async def delete_entry(self, entry_id: str) -> bool:
        """Delete a journal entry."""
        pass


class IUIComponent(ABC):
    """Base interface for UI components."""

    @abstractmethod
    def create(self) -> Any:
        """Create the UI component."""
        pass

    @abstractmethod
    def update(self, data: Any) -> None:
        """Update the component with new data."""
        pass

    @abstractmethod
    def destroy(self) -> None:
        """Destroy the component."""
        pass


class IWeatherDisplay(IUIComponent):
    """Weather display component interface."""

    @abstractmethod
    def show_loading(self) -> None:
        """Show loading state."""
        pass

    @abstractmethod
    def show_error(self, error: str) -> None:
        """Show error state."""
        pass

    @abstractmethod
    def show_weather(self, weather_data: WeatherData) -> None:
        """Show weather data."""
        pass


class IJournalDisplay(IUIComponent):
    """Journal display component interface."""

    @abstractmethod
    def show_entries(self, entries: List[JournalEntry]) -> None:
        """Show journal entries."""
        pass

    @abstractmethod
    def show_entry_editor(self, entry: Optional[JournalEntry] = None) -> None:
        """Show entry editor."""
        pass


class IActivityDisplay(IUIComponent):
    """Activity display component interface."""

    @abstractmethod
    def show_activities(self, activities: List[Dict[str, Any]]) -> None:
        """Show activity suggestions."""
        pass

    @abstractmethod
    def refresh_activities(self, weather_data: WeatherData) -> None:
        """Refresh activities based on weather."""
        pass


class IEventBus(ABC):
    """Event bus interface for loose coupling between components."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to an event type."""
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Unsubscribe from an event type."""
        pass

    @abstractmethod
    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event."""
        pass


class ILogger(ABC):
    """Logger interface."""

    @abstractmethod
    def info(self, message: str) -> None:
        """Log info message."""
        pass

    @abstractmethod
    def error(self, message: str, exc_info: Optional[Exception] = None) -> None:
        """Log error message."""
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        """Log warning message."""
        pass

    @abstractmethod
    def debug(self, message: str) -> None:
        """Log debug message."""
        pass


class ICache(ABC):
    """Cache interface."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class IThemeManager(ABC):
    """Theme management interface."""

    @abstractmethod
    def get_current_theme(self) -> str:
        """Get current theme name."""
        pass

    @abstractmethod
    def set_theme(self, theme_name: str) -> None:
        """Set theme."""
        pass

    @abstractmethod
    def get_theme_colors(self) -> Dict[str, str]:
        """Get current theme colors."""
        pass

    @abstractmethod
    def get_available_themes(self) -> List[str]:
        """Get available themes."""
        pass


class IKeyboardShortcutManager(ABC):
    """Keyboard shortcut management interface."""

    @abstractmethod
    def register_shortcut(self, key: str, callback: callable) -> None:
        """Register a keyboard shortcut."""
        pass

    @abstractmethod
    def unregister_shortcut(self, key: str) -> None:
        """Unregister a keyboard shortcut."""
        pass

    @abstractmethod
    def handle_keypress(self, event: Any) -> bool:
        """Handle keypress event."""
        pass


class IAutoRefreshManager(ABC):
    """Auto-refresh management interface."""

    @abstractmethod
    def start_auto_refresh(self, interval: int, callback: callable) -> None:
        """Start auto-refresh with given interval."""
        pass

    @abstractmethod
    def stop_auto_refresh(self) -> None:
        """Stop auto-refresh."""
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if auto-refresh is enabled."""
        pass

    @abstractmethod
    def set_interval(self, interval: int) -> None:
        """Set refresh interval."""
        pass


class IErrorHandler(ABC):
    """Error handling interface."""

    @abstractmethod
    def handle_error(self, error: Exception, context: str) -> None:
        """Handle an error."""
        pass

    @abstractmethod
    def show_user_friendly_error(self, error: Exception) -> str:
        """Convert technical error to user-friendly message."""
        pass

    @abstractmethod
    def log_error(self, error: Exception, context: str) -> None:
        """Log error for debugging."""
        pass


class IDataValidator(ABC):
    """Data validation interface."""

    @abstractmethod
    def validate_weather_data(self, data: Dict[str, Any]) -> bool:
        """Validate weather data."""
        pass

    @abstractmethod
    def validate_journal_entry(self, entry: Dict[str, Any]) -> bool:
        """Validate journal entry."""
        pass

    @abstractmethod
    def validate_location(self, location: str) -> bool:
        """Validate location string."""
        pass


class IPerformanceMonitor(ABC):
    """Performance monitoring interface."""

    @abstractmethod
    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        pass

    @abstractmethod
    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration."""
        pass

    @abstractmethod
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics."""
        pass


class IAccessibilityManager(ABC):
    """Accessibility management interface."""

    @abstractmethod
    def enable_high_contrast(self) -> None:
        """Enable high contrast mode."""
        pass

    @abstractmethod
    def enable_screen_reader(self) -> None:
        """Enable screen reader support."""
        pass

    @abstractmethod
    def set_font_size(self, size: int) -> None:
        """Set font size for accessibility."""
        pass

    @abstractmethod
    def is_accessibility_enabled(self) -> bool:
        """Check if accessibility features are enabled."""
        pass
