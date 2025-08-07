"""Component Factory for Standardized UI Components

Provides a centralized factory for creating UI components with consistent styling.
"""

from typing import Any, Dict, Optional, Type, Union
import customtkinter as ctk
from ..theme import DataTerminalTheme
from ..themes.glassmorphic_theme import GlassmorphicTheme, ThemeMode
from .glassmorphic import GlassmorphicFrame, GlassButton, GlassPanel
from .common import LoadingSpinner, ErrorDisplay, InlineErrorDisplay


class ComponentFactory:
    """Factory for creating standardized UI components."""
    
    def __init__(self, theme_provider: Optional[Union[DataTerminalTheme, GlassmorphicTheme]] = None):
        """Initialize component factory.
        
        Args:
            theme_provider: Theme provider instance (defaults to DataTerminalTheme)
        """
        self.theme = theme_provider or DataTerminalTheme
        self._component_registry: Dict[str, Type] = {
            'frame': ctk.CTkFrame,
            'button': ctk.CTkButton,
            'label': ctk.CTkLabel,
            'entry': ctk.CTkEntry,
            'textbox': ctk.CTkTextbox,
            'switch': ctk.CTkSwitch,
            'checkbox': ctk.CTkCheckBox,
            'glass_frame': GlassmorphicFrame,
            'glass_button': GlassButton,
            'glass_panel': GlassPanel,
            'loading_spinner': LoadingSpinner,
            'error_display': ErrorDisplay,
            'inline_error': InlineErrorDisplay,
        }
    
    def create_frame(self, parent, variant: str = "default", **kwargs) -> ctk.CTkFrame:
        """Create a standardized frame.
        
        Args:
            parent: Parent widget
            variant: Style variant (default, main, highlight, glass)
            **kwargs: Additional customization options
            
        Returns:
            Configured CTkFrame instance
        """
        if variant == "glass":
            return self._create_glass_component('glass_frame', parent, **kwargs)
        
        style = self.theme.get_frame_style(variant)
        style.update(kwargs)
        return ctk.CTkFrame(parent, **style)
    
    def create_button(self, parent, text: str = "", variant: str = "primary", **kwargs) -> ctk.CTkButton:
        """Create a standardized button.
        
        Args:
            parent: Parent widget
            text: Button text
            variant: Style variant (primary, secondary, danger, glass)
            **kwargs: Additional customization options
            
        Returns:
            Configured CTkButton instance
        """
        if variant == "glass":
            return self._create_glass_component('glass_button', parent, text=text, **kwargs)
        
        style = self.theme.get_button_style(variant)
        style.update(kwargs)
        return ctk.CTkButton(parent, text=text, **style)
    
    def create_label(self, parent, text: str = "", variant: str = "default", **kwargs) -> ctk.CTkLabel:
        """Create a standardized label.
        
        Args:
            parent: Parent widget
            text: Label text
            variant: Style variant (default, title, subtitle, caption, value)
            **kwargs: Additional customization options
            
        Returns:
            Configured CTkLabel instance
        """
        style = self.theme.get_label_style(variant)
        style.update(kwargs)
        return ctk.CTkLabel(parent, text=text, **style)
    
    def create_entry(self, parent, placeholder: str = "", **kwargs) -> ctk.CTkEntry:
        """Create a standardized entry field.
        
        Args:
            parent: Parent widget
            placeholder: Placeholder text
            **kwargs: Additional customization options
            
        Returns:
            Configured CTkEntry instance
        """
        style = self.theme.get_entry_style()
        style.update(kwargs)
        if placeholder:
            style['placeholder_text'] = placeholder
        return ctk.CTkEntry(parent, **style)
    
    def create_textbox(self, parent, **kwargs) -> ctk.CTkTextbox:
        """Create a standardized textbox.
        
        Args:
            parent: Parent widget
            **kwargs: Additional customization options
            
        Returns:
            Configured CTkTextbox instance
        """
        style = self.theme.get_textbox_style()
        style.update(kwargs)
        return ctk.CTkTextbox(parent, **style)
    
    def create_switch(self, parent, text: str = "", **kwargs) -> ctk.CTkSwitch:
        """Create a standardized switch.
        
        Args:
            parent: Parent widget
            text: Switch text
            **kwargs: Additional customization options
            
        Returns:
            Configured CTkSwitch instance
        """
        style = self.theme.get_switch_style()
        style.update(kwargs)
        return ctk.CTkSwitch(parent, text=text, **style)
    
    def create_checkbox(self, parent, text: str = "", **kwargs) -> ctk.CTkCheckBox:
        """Create a standardized checkbox.
        
        Args:
            parent: Parent widget
            text: Checkbox text
            **kwargs: Additional customization options
            
        Returns:
            Configured CTkCheckBox instance
        """
        style = self.theme.get_checkbox_style()
        style.update(kwargs)
        return ctk.CTkCheckBox(parent, text=text, **style)
    
    def create_loading_spinner(self, parent, text: str = "Loading...", **kwargs) -> LoadingSpinner:
        """Create a standardized loading spinner.
        
        Args:
            parent: Parent widget
            text: Loading text
            **kwargs: Additional customization options
            
        Returns:
            Configured LoadingSpinner instance
        """
        return LoadingSpinner(parent, text=text, **kwargs)
    
    def create_error_display(self, parent, message: str = "", **kwargs) -> ErrorDisplay:
        """Create a standardized error display.
        
        Args:
            parent: Parent widget
            message: Error message
            **kwargs: Additional customization options
            
        Returns:
            Configured ErrorDisplay instance
        """
        return ErrorDisplay(parent, message=message, **kwargs)
    
    def _create_glass_component(self, component_type: str, parent, **kwargs):
        """Create a glassmorphic component.
        
        Args:
            component_type: Type of glass component
            parent: Parent widget
            **kwargs: Additional customization options
            
        Returns:
            Configured glassmorphic component
        """
        component_class = self._component_registry.get(component_type)
        if not component_class:
            raise ValueError(f"Unknown glass component type: {component_type}")
        
        return component_class(parent, **kwargs)
    
    def register_component(self, name: str, component_class: Type) -> None:
        """Register a custom component type.
        
        Args:
            name: Component name
            component_class: Component class
        """
        self._component_registry[name] = component_class
    
    def get_registered_components(self) -> Dict[str, Type]:
        """Get all registered component types.
        
        Returns:
            Dictionary of registered components
        """
        return self._component_registry.copy()
    
    def create_component(self, component_type: str, parent, **kwargs):
        """Create a component by type name.
        
        Args:
            component_type: Registered component type name
            parent: Parent widget
            **kwargs: Component-specific arguments
            
        Returns:
            Configured component instance
        """
        component_class = self._component_registry.get(component_type)
        if not component_class:
            raise ValueError(f"Unknown component type: {component_type}")
        
        return component_class(parent, **kwargs)


# Global factory instance
_default_factory = None


def get_factory(theme_provider: Optional[Union[DataTerminalTheme, GlassmorphicTheme]] = None) -> ComponentFactory:
    """Get the default component factory instance.
    
    Args:
        theme_provider: Optional theme provider (creates new factory if provided)
        
    Returns:
        ComponentFactory instance
    """
    global _default_factory
    
    if theme_provider or _default_factory is None:
        _default_factory = ComponentFactory(theme_provider)
    
    return _default_factory


# Convenience functions for common components
def create_frame(parent, variant: str = "default", **kwargs) -> ctk.CTkFrame:
    """Create a standardized frame using the default factory."""
    return get_factory().create_frame(parent, variant, **kwargs)


def create_button(parent, text: str = "", variant: str = "primary", **kwargs) -> ctk.CTkButton:
    """Create a standardized button using the default factory."""
    return get_factory().create_button(parent, text, variant, **kwargs)


def create_label(parent, text: str = "", variant: str = "default", **kwargs) -> ctk.CTkLabel:
    """Create a standardized label using the default factory."""
    return get_factory().create_label(parent, text, variant, **kwargs)


def create_entry(parent, placeholder: str = "", **kwargs) -> ctk.CTkEntry:
    """Create a standardized entry using the default factory."""
    return get_factory().create_entry(parent, placeholder, **kwargs)