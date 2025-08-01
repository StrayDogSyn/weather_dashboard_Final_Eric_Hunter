"""Base UI Component

Provides common functionality for all UI components.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import customtkinter as ctk

from ...core.event_bus import get_event_bus, EventTypes
from ...core.interfaces import IUIComponent


class BaseComponent(IUIComponent, ABC):
    """Base class for all UI components.

    Provides common functionality like event handling, error management,
    and lifecycle management.
    """

    def __init__(self, parent: Optional[ctk.CTkFrame] = None, **kwargs):
        """Initialize the base component.

        Args:
            parent: Parent widget
            **kwargs: Additional arguments
        """
        self.parent = parent
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_bus = get_event_bus()
        self.widgets: Dict[str, Any] = {}
        self._is_created = False
        self._is_destroyed = False

        # Initialize component
        self._setup_component(**kwargs)
        self._subscribe_to_events()

    def _setup_component(self, **kwargs) -> None:
        """Setup component-specific initialization.

        Args:
            **kwargs: Component-specific arguments
        """
        # Override in subclasses
        pass

    def _subscribe_to_events(self) -> None:
        """Subscribe to relevant events.

        Override in subclasses to subscribe to specific events.
        """
        # Subscribe to common events
        self.event_bus.subscribe(EventTypes.THEME_CHANGED, self._on_theme_changed)
        self.event_bus.subscribe(EventTypes.ERROR_OCCURRED, self._on_error_occurred)

    def create(self) -> Any:
        """Create the UI component.

        Returns:
            The created widget
        """
        if self._is_created:
            self.logger.warning("Component already created")
            return self._get_main_widget()

        try:
            widget = self._create_widget()
            self._is_created = True
            self.logger.debug("Component created successfully")
            return widget
        except Exception as e:
            self.logger.error(f"Failed to create component: {e}")
            self._handle_creation_error(e)
            return None

    @abstractmethod
    def _create_widget(self) -> Any:
        """Create the main widget for this component.

        Returns:
            The created widget
        """
        pass

    def update(self, data: Any) -> None:
        """Update the component with new data.

        Args:
            data: New data to display
        """
        if not self._is_created or self._is_destroyed:
            self.logger.warning("Cannot update component - not created or destroyed")
            return

        try:
            self._update_widget(data)
        except Exception as e:
            self.logger.error(f"Failed to update component: {e}")
            self._handle_update_error(e)

    @abstractmethod
    def _update_widget(self, data: Any) -> None:
        """Update the widget with new data.

        Args:
            data: New data to display
        """
        pass

    def destroy(self) -> None:
        """Destroy the component and clean up resources."""
        if self._is_destroyed:
            return

        try:
            self._unsubscribe_from_events()
            self._destroy_widget()
            self._is_destroyed = True
            self.logger.debug("Component destroyed successfully")
        except Exception as e:
            self.logger.error(f"Error destroying component: {e}")

    def _unsubscribe_from_events(self) -> None:
        """Unsubscribe from all events."""
        self.event_bus.unsubscribe(EventTypes.THEME_CHANGED, self._on_theme_changed)
        self.event_bus.unsubscribe(EventTypes.ERROR_OCCURRED, self._on_error_occurred)

    def _destroy_widget(self) -> None:
        """Destroy the main widget.

        Override in subclasses if needed.
        """
        main_widget = self._get_main_widget()
        if main_widget and hasattr(main_widget, 'destroy'):
            main_widget.destroy()

    def _get_main_widget(self) -> Optional[Any]:
        """Get the main widget for this component.

        Returns:
            The main widget or None
        """
        # Override in subclasses to return the main widget
        return None

    def _handle_creation_error(self, error: Exception) -> None:
        """Handle errors during component creation.

        Args:
            error: The error that occurred
        """
        self.logger.error(f"Component creation failed: {error}")
        # Publish error event
        self.event_bus.publish(EventTypes.ERROR_OCCURRED, {
            'component': self.__class__.__name__,
            'operation': 'creation',
            'error': str(error)
        })

    def _handle_update_error(self, error: Exception) -> None:
        """Handle errors during component update.

        Args:
            error: The error that occurred
        """
        self.logger.error(f"Component update failed: {error}")
        # Publish error event
        self.event_bus.publish(EventTypes.ERROR_OCCURRED, {
            'component': self.__class__.__name__,
            'operation': 'update',
            'error': str(error)
        })

    def _on_theme_changed(self, data: Any) -> None:
        """Handle theme change events.

        Args:
            data: Theme change data
        """
        if self._is_created and not self._is_destroyed:
            self._apply_theme_changes(data)

    def _apply_theme_changes(self, theme_data: Any) -> None:
        """Apply theme changes to the component.

        Args:
            theme_data: Theme data
        """
        # Override in subclasses to apply theme changes
        pass

    def _on_error_occurred(self, data: Dict[str, Any]) -> None:
        """Handle error events.

        Args:
            data: Error data
        """
        if data.get('component') == self.__class__.__name__:
            self._handle_external_error(data)

    def _handle_external_error(self, error_data: Dict[str, Any]) -> None:
        """Handle errors from other components.

        Args:
            error_data: Error data
        """
        # Override in subclasses to handle external errors
        pass

    def is_created(self) -> bool:
        """Check if component is created.

        Returns:
            True if created, False otherwise
        """
        return self._is_created

    def is_destroyed(self) -> bool:
        """Check if component is destroyed.

        Returns:
            True if destroyed, False otherwise
        """
        return self._is_destroyed

    def get_widget(self, name: str) -> Optional[Any]:
        """Get a widget by name.

        Args:
            name: Widget name

        Returns:
            The widget or None if not found
        """
        return self.widgets.get(name)

    def add_widget(self, name: str, widget: Any) -> None:
        """Add a widget to the component's widget collection.

        Args:
            name: Widget name
            widget: The widget
        """
        self.widgets[name] = widget

    def remove_widget(self, name: str) -> None:
        """Remove a widget from the component's widget collection.

        Args:
            name: Widget name
        """
        if name in self.widgets:
            del self.widgets[name]

    def clear_widgets(self) -> None:
        """Clear all widgets from the component's collection."""
        self.widgets.clear()

    def show_loading(self) -> None:
        """Show loading state.

        Override in subclasses to implement loading state.
        """
        pass

    def hide_loading(self) -> None:
        """Hide loading state.

        Override in subclasses to implement loading state.
        """
        pass

    def show_error(self, error: str) -> None:
        """Show error state.

        Args:
            error: Error message
        """
        self.logger.error(f"Component error: {error}")
        # Override in subclasses to implement error display

    def show_success(self, message: str) -> None:
        """Show success state.

        Args:
            message: Success message
        """
        self.logger.info(f"Component success: {message}")
        # Override in subclasses to implement success display


class ContainerComponent(BaseComponent):
    """Base class for components that contain other components."""

    def __init__(self, parent: Optional[ctk.CTkFrame] = None, **kwargs):
        """Initialize the container component.

        Args:
            parent: Parent widget
            **kwargs: Additional arguments
        """
        self.child_components: Dict[str, BaseComponent] = {}
        super().__init__(parent, **kwargs)

    def add_component(self, name: str, component: BaseComponent) -> None:
        """Add a child component.

        Args:
            name: Component name
            component: The component to add
        """
        self.child_components[name] = component

    def remove_component(self, name: str) -> None:
        """Remove a child component.

        Args:
            name: Component name
        """
        if name in self.child_components:
            component = self.child_components[name]
            component.destroy()
            del self.child_components[name]

    def get_component(self, name: str) -> Optional[BaseComponent]:
        """Get a child component by name.

        Args:
            name: Component name

        Returns:
            The component or None if not found
        """
        return self.child_components.get(name)

    def destroy(self) -> None:
        """Destroy the container and all child components."""
        # Destroy all child components
        for component in self.child_components.values():
            component.destroy()
        self.child_components.clear()

        # Call parent destroy
        super().destroy()

    def update_all_components(self, data: Any) -> None:
        """Update all child components with new data.

        Args:
            data: New data to pass to components
        """
        for component in self.child_components.values():
            if component.is_created() and not component.is_destroyed():
                component.update(data)
