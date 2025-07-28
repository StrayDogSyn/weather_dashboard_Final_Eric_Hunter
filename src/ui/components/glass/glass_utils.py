"""Utility functions for glassmorphic components.

This module provides utility functions for creating standardized
glassmorphic UI components and layouts for the weather dashboard.

Functions:
    create_glass_card: Create standardized glass card components
    create_glass_toolbar: Create standardized glass toolbar components
    create_glass_dialog: Create standardized glass dialog components
    create_glass_notification: Create standardized glass notification components
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, List, Callable

from .core_types import ComponentSize, GlassEffect
from .glass_frame import GlassFrame
from .glass_button import GlassButton
from .glass_text import GlassLabel
from src.utils.logger import LoggerMixin


class GlassUtilities(LoggerMixin):
    """Utility class for glassmorphic component creation.
    
    This class provides static methods for creating standardized
    glassmorphic components with consistent styling and behavior.
    """
    
    @staticmethod
    def create_glass_card(
        parent,
        title: str,
        content_widget: Optional[ctk.CTkBaseClass] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        glass_effect: Optional[GlassEffect] = None
    ) -> GlassFrame:
        """Create a standardized glass card component.
        
        Args:
            parent: Parent widget
            title: Card title text
            content_widget: Optional content widget to embed
            size: Card size configuration
            glass_effect: Optional custom glass effect
            
        Returns:
            Configured GlassFrame card component
        """
        # Create card frame
        card = GlassFrame(parent, size=size, glass_effect=glass_effect)
        
        # Configure card layout
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        
        # Add title section
        title_frame = GlassFrame(card, size=ComponentSize.SMALL)
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        title_label = GlassLabel(
            title_frame,
            text=title,
            text_style="heading",
            size=ComponentSize.MEDIUM
        )
        title_label.pack(pady=5, padx=10, anchor="w")
        
        # Add content section if provided
        if content_widget:
            content_frame = GlassFrame(card, size=ComponentSize.MEDIUM)
            content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
            
            # Reparent content widget to content frame
            content_widget.pack(in_=content_frame, fill="both", expand=True, padx=5, pady=5)
        
        GlassUtilities().logger.debug(f"Glass card created: '{title}'")
        return card
    
    @staticmethod
    def create_glass_toolbar(
        parent,
        buttons: List[Dict[str, Any]],
        size: ComponentSize = ComponentSize.MEDIUM,
        glass_effect: Optional[GlassEffect] = None
    ) -> GlassFrame:
        """Create a standardized glass toolbar component.
        
        Args:
            parent: Parent widget
            buttons: List of button configurations
            size: Toolbar size configuration
            glass_effect: Optional custom glass effect
            
        Returns:
            Configured GlassFrame toolbar component
        """
        # Create toolbar frame
        toolbar = GlassFrame(parent, size=size, glass_effect=glass_effect)
        
        # Set fixed height for toolbar
        height_configs = {
            ComponentSize.SMALL: 50,
            ComponentSize.MEDIUM: 60,
            ComponentSize.LARGE: 70,
            ComponentSize.EXTRA_LARGE: 80
        }
        
        toolbar_height = height_configs.get(size, 60)
        toolbar.configure(height=toolbar_height)
        
        # Create button container
        button_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=5)
        
        # Create buttons
        for i, button_config in enumerate(buttons):
            button = GlassButton(
                button_frame,
                text=button_config.get('text', f'Button {i+1}'),
                size=ComponentSize.SMALL,
                command=button_config.get('command'),
                icon=button_config.get('icon'),
                glass_effect=glass_effect
            )
            
            # Pack button with spacing
            button.pack(side="left", padx=5, pady=5)
            
            # Add separator if specified
            if button_config.get('separator', False) and i < len(buttons) - 1:
                separator = ctk.CTkFrame(
                    button_frame,
                    width=2,
                    height=30,
                    fg_color="#666666"
                )
                separator.pack(side="left", padx=10, pady=10)
        
        GlassUtilities().logger.debug(f"Glass toolbar created with {len(buttons)} buttons")
        return toolbar
    
    @staticmethod
    def create_glass_dialog(
        parent,
        title: str,
        message: str,
        buttons: List[Dict[str, Any]],
        size: ComponentSize = ComponentSize.MEDIUM,
        glass_effect: Optional[GlassEffect] = None
    ) -> GlassFrame:
        """Create a standardized glass dialog component.
        
        Args:
            parent: Parent widget
            title: Dialog title text
            message: Dialog message text
            buttons: List of button configurations
            size: Dialog size configuration
            glass_effect: Optional custom glass effect
            
        Returns:
            Configured GlassFrame dialog component
        """
        # Create dialog frame
        dialog = GlassFrame(parent, size=size, glass_effect=glass_effect)
        
        # Configure dialog layout
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)
        
        # Add title section
        title_frame = GlassFrame(dialog, size=ComponentSize.SMALL)
        title_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        
        title_label = GlassLabel(
            title_frame,
            text=title,
            text_style="heading",
            size=ComponentSize.MEDIUM
        )
        title_label.pack(pady=5, padx=10)
        
        # Add message section
        message_frame = GlassFrame(dialog, size=ComponentSize.MEDIUM)
        message_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        
        message_label = GlassLabel(
            message_frame,
            text=message,
            text_style="body",
            size=ComponentSize.MEDIUM
        )
        message_label.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Add button section
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 15))
        
        # Create buttons
        for button_config in buttons:
            button = GlassButton(
                button_frame,
                text=button_config.get('text', 'OK'),
                size=ComponentSize.SMALL,
                command=button_config.get('command'),
                glass_effect=glass_effect
            )
            button.pack(side="right", padx=5, pady=5)
        
        GlassUtilities().logger.debug(f"Glass dialog created: '{title}'")
        return dialog
    
    @staticmethod
    def create_glass_notification(
        parent,
        message: str,
        notification_type: str = "info",
        duration: int = 3000,
        size: ComponentSize = ComponentSize.MEDIUM,
        glass_effect: Optional[GlassEffect] = None
    ) -> GlassFrame:
        """Create a standardized glass notification component.
        
        Args:
            parent: Parent widget
            message: Notification message text
            notification_type: Type of notification (info, success, warning, error)
            duration: Auto-hide duration in milliseconds (0 for persistent)
            size: Notification size configuration
            glass_effect: Optional custom glass effect
            
        Returns:
            Configured GlassFrame notification component
        """
        # Create notification frame
        notification = GlassFrame(parent, size=size, glass_effect=glass_effect)
        
        # Configure notification styling based on type
        type_configs = {
            'info': {'color': '#2196F3', 'icon': 'ℹ'},
            'success': {'color': '#4CAF50', 'icon': '✓'},
            'warning': {'color': '#FF9800', 'icon': '⚠'},
            'error': {'color': '#F44336', 'icon': '✗'}
        }
        
        config = type_configs.get(notification_type, type_configs['info'])
        
        # Update notification border color
        notification.configure(border_color=config['color'])
        
        # Create content frame
        content_frame = ctk.CTkFrame(notification, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add icon
        icon_label = GlassLabel(
            content_frame,
            text=config['icon'],
            text_style="heading",
            size=ComponentSize.SMALL
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        # Add message
        message_label = GlassLabel(
            content_frame,
            text=message,
            text_style="body",
            size=ComponentSize.SMALL
        )
        message_label.pack(side="left", fill="both", expand=True)
        
        # Add close button
        def close_notification():
            notification.destroy()
        
        close_button = GlassButton(
            content_frame,
            text="×",
            size=ComponentSize.SMALL,
            command=close_notification,
            glass_effect=glass_effect
        )
        close_button.pack(side="right", padx=(10, 0))
        
        # Auto-hide if duration is specified
        if duration > 0:
            notification.after(duration, close_notification)
        
        GlassUtilities().logger.debug(f"Glass notification created: '{notification_type}' - '{message}'")
        return notification


# Convenience functions for backward compatibility
def create_glass_card(
    parent,
    title: str,
    content_widget: Optional[ctk.CTkBaseClass] = None,
    size: ComponentSize = ComponentSize.MEDIUM
) -> GlassFrame:
    """Create a standardized glass card component.
    
    Args:
        parent: Parent widget
        title: Card title
        content_widget: Optional content widget to embed
        size: Card size
        
    Returns:
        Configured GlassFrame card
    """
    return GlassUtilities.create_glass_card(parent, title, content_widget, size)


def create_glass_toolbar(
    parent,
    buttons: List[Dict[str, Any]],
    size: ComponentSize = ComponentSize.MEDIUM
) -> GlassFrame:
    """Create a standardized glass toolbar component.
    
    Args:
        parent: Parent widget
        buttons: List of button configurations
        size: Toolbar size
        
    Returns:
        Configured GlassFrame toolbar
    """
    return GlassUtilities.create_glass_toolbar(parent, buttons, size)


def create_glass_dialog(
    parent,
    title: str,
    message: str,
    buttons: List[Dict[str, Any]],
    size: ComponentSize = ComponentSize.MEDIUM
) -> GlassFrame:
    """Create a standardized glass dialog component.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Dialog message
        buttons: List of button configurations
        size: Dialog size
        
    Returns:
        Configured GlassFrame dialog
    """
    return GlassUtilities.create_glass_dialog(parent, title, message, buttons, size)


def create_glass_notification(
    parent,
    message: str,
    notification_type: str = "info",
    duration: int = 3000,
    size: ComponentSize = ComponentSize.MEDIUM
) -> GlassFrame:
    """Create a standardized glass notification component.
    
    Args:
        parent: Parent widget
        message: Notification message
        notification_type: Type of notification
        duration: Auto-hide duration in milliseconds
        size: Notification size
        
    Returns:
        Configured GlassFrame notification
    """
    return GlassUtilities.create_glass_notification(parent, message, notification_type, duration, size)