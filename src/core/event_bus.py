"""Event Bus Implementation

Provides a centralized event system for loose coupling between components.
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict

from .interfaces import IEventBus


class EventBus(IEventBus):
    """Centralized event bus for component communication."""

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._logger = logging.getLogger(__name__)
        self._logger.info("Event bus initialized")

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event occurs
        """
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            self._logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Function to remove from subscribers
        """
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            self._logger.debug(f"Unsubscribed from event: {event_type}")

    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event.

        Args:
            event_type: Type of event to publish
            data: Optional data to pass to handlers
        """
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self._logger.error(f"Error in event handler for {event_type}: {e}")
            self._logger.debug(f"Published event: {event_type}")

    def clear_subscribers(self, event_type: Optional[str] = None) -> None:
        """Clear subscribers for an event type or all events.

        Args:
            event_type: Specific event type to clear, or None for all
        """
        if event_type:
            if event_type in self._subscribers:
                del self._subscribers[event_type]
                self._logger.debug(f"Cleared subscribers for event: {event_type}")
        else:
            self._subscribers.clear()
            self._logger.debug("Cleared all event subscribers")

    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type.

        Args:
            event_type: Type of event

        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))

    def get_all_event_types(self) -> List[str]:
        """Get all registered event types.

        Returns:
            List of event types
        """
        return list(self._subscribers.keys())


# Event type constants
class EventTypes:
    """Common event types used throughout the application."""

    # Weather events
    WEATHER_UPDATED = "weather_updated"
    WEATHER_ERROR = "weather_error"
    WEATHER_LOADING = "weather_loading"
    LOCATION_CHANGED = "location_changed"

    # Journal events
    JOURNAL_ENTRY_CREATED = "journal_entry_created"
    JOURNAL_ENTRY_UPDATED = "journal_entry_updated"
    JOURNAL_ENTRY_DELETED = "journal_entry_deleted"
    JOURNAL_ENTRIES_LOADED = "journal_entries_loaded"

    # Activity events
    ACTIVITIES_UPDATED = "activities_updated"
    ACTIVITY_SELECTED = "activity_selected"

    # UI events
    THEME_CHANGED = "theme_changed"
    WINDOW_RESIZED = "window_resized"
    TAB_CHANGED = "tab_changed"

    # Configuration events
    CONFIG_UPDATED = "config_updated"
    API_KEY_UPDATED = "api_key_updated"

    # System events
    APPLICATION_STARTED = "application_started"
    APPLICATION_SHUTDOWN = "application_shutdown"
    ERROR_OCCURRED = "error_occurred"
    CACHE_CLEARED = "cache_cleared"

    # Auto-refresh events
    AUTO_REFRESH_STARTED = "auto_refresh_started"
    AUTO_REFRESH_STOPPED = "auto_refresh_stopped"
    AUTO_REFRESH_INTERVAL_CHANGED = "auto_refresh_interval_changed"

    # Keyboard events
    KEYBOARD_SHORTCUT_TRIGGERED = "keyboard_shortcut_triggered"

    # Accessibility events
    ACCESSIBILITY_TOGGLED = "accessibility_toggled"
    FONT_SIZE_CHANGED = "font_size_changed"
    HIGH_CONTRAST_TOGGLED = "high_contrast_toggled"


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns:
        Global event bus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def publish_event(event_type: str, data: Any = None) -> None:
    """Publish an event using the global event bus.

    Args:
        event_type: Type of event to publish
        data: Optional data to pass to handlers
    """
    get_event_bus().publish(event_type, data)


def subscribe_to_event(event_type: str, handler: Callable) -> None:
    """Subscribe to an event using the global event bus.

    Args:
        event_type: Type of event to subscribe to
        handler: Function to call when event occurs
    """
    get_event_bus().subscribe(event_type, handler)


def unsubscribe_from_event(event_type: str, handler: Callable) -> None:
    """Unsubscribe from an event using the global event bus.

    Args:
        event_type: Type of event to unsubscribe from
        handler: Function to remove from subscribers
    """
    get_event_bus().unsubscribe(event_type, handler)
