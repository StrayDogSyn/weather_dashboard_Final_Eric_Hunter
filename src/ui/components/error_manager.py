"""Enhanced Error Management with Visual Styling

Provides styled error cards, notifications, and user-friendly error handling
with smooth animations and theme integration.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, Dict, Callable, List
import threading
import time
from datetime import datetime
from enum import Enum

from .animation_manager import AnimationManager, MicroInteractions


class ErrorLevel(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCard:
    """Styled error card with animations and theme integration."""
    
    def __init__(self, parent: ctk.CTkBaseClass, theme_colors: Optional[Dict[str, str]] = None):
        self.parent = parent
        self.theme_colors = theme_colors or {
            'error_bg': '#2A0A0A',
            'error_border': '#FF4444',
            'warning_bg': '#2A1A0A',
            'warning_border': '#FFA444',
            'info_bg': '#0A1A2A',
            'info_border': '#4488FF',
            'text': '#FFFFFF',
            'text_secondary': '#CCCCCC'
        }
        
        self.error_frame = None
        self.auto_dismiss_timer = None
        self.micro_interactions = MicroInteractions(theme_colors)
    
    def show_error_card(self, 
                       message: str, 
                       level: ErrorLevel = ErrorLevel.ERROR,
                       title: Optional[str] = None,
                       details: Optional[str] = None,
                       actions: Optional[List[Dict[str, Callable]]] = None,
                       auto_dismiss: Optional[int] = None,
                       width: int = 400,
                       height: int = 200) -> ctk.CTkFrame:
        """Show styled error card with animations."""
        
        # Dismiss existing error card
        self.dismiss_error_card()
        
        # Get colors based on error level
        bg_color, border_color, icon = self._get_level_styling(level)
        
        # Create main error frame
        self.error_frame = ctk.CTkFrame(
            self.parent,
            width=width,
            height=height,
            fg_color=bg_color,
            border_color=border_color,
            border_width=2,
            corner_radius=12
        )
        
        # Position in center of parent
        self.error_frame.place(
            relx=0.5, rely=0.5,
            anchor="center"
        )
        
        # Prevent frame from shrinking
        self.error_frame.pack_propagate(False)
        
        # Create header with icon and title
        header_frame = ctk.CTkFrame(
            self.error_frame,
            fg_color="transparent",
            height=60
        )
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        # Icon
        icon_label = ctk.CTkLabel(
            header_frame,
            text=icon,
            font=("JetBrains Mono", 32),
            text_color=border_color
        )
        icon_label.pack(side="left", padx=(0, 15))
        
        # Title and close button container
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(side="left", fill="both", expand=True)
        
        # Title
        title_text = title or self._get_default_title(level)
        title_label = ctk.CTkLabel(
            title_container,
            text=title_text,
            font=("JetBrains Mono", 18, "bold"),
            text_color=self.theme_colors['text'],
            anchor="w"
        )
        title_label.pack(anchor="w")
        
        # Close button
        close_button = ctk.CTkButton(
            header_frame,
            text="✕",
            width=30,
            height=30,
            font=("JetBrains Mono", 16),
            fg_color="transparent",
            text_color=self.theme_colors['text_secondary'],
            hover_color=border_color,
            command=self.dismiss_error_card
        )
        close_button.pack(side="right")
        
        # Add hover effect to close button
        self.micro_interactions.add_hover_glow(close_button, border_color)
        
        # Message content
        content_frame = ctk.CTkFrame(
            self.error_frame,
            fg_color="transparent"
        )
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Main message
        message_label = ctk.CTkLabel(
            content_frame,
            text=message,
            font=("JetBrains Mono", 14),
            text_color=self.theme_colors['text'],
            wraplength=width-80,
            justify="left",
            anchor="nw"
        )
        message_label.pack(anchor="nw", pady=(0, 10))
        
        # Details (if provided)
        if details:
            details_label = ctk.CTkLabel(
                content_frame,
                text=details,
                font=("JetBrains Mono", 12),
                text_color=self.theme_colors['text_secondary'],
                wraplength=width-80,
                justify="left",
                anchor="nw"
            )
            details_label.pack(anchor="nw", pady=(0, 15))
        
        # Action buttons (if provided)
        if actions:
            button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            button_frame.pack(fill="x", pady=(10, 0))
            
            for i, action in enumerate(actions):
                button = ctk.CTkButton(
                    button_frame,
                    text=action.get('text', 'Action'),
                    command=action.get('callback', lambda: None),
                    font=("JetBrains Mono", 12),
                    height=32,
                    fg_color=border_color,
                    hover_color=self._darken_color(border_color)
                )
                button.pack(side="left", padx=(0, 10) if i < len(actions)-1 else 0)
                
                # Add micro-interactions
                self.micro_interactions.add_hover_glow(button)
                self.micro_interactions.add_click_ripple(button)
        
        # Add entrance animation
        AnimationManager.fade_in(self.error_frame, duration=300)
        AnimationManager.slide_in(self.error_frame, direction="up", duration=400, distance=50)
        
        # Add pulsing effect for critical errors
        if level == ErrorLevel.CRITICAL:
            AnimationManager.pulse_effect(self.error_frame, duration=2000, intensity=0.3)
        
        # Auto-dismiss timer
        if auto_dismiss:
            self.auto_dismiss_timer = threading.Timer(auto_dismiss / 1000, self.dismiss_error_card)
            self.auto_dismiss_timer.start()
        
        return self.error_frame
    
    def dismiss_error_card(self):
        """Dismiss error card with animation."""
        if self.auto_dismiss_timer:
            self.auto_dismiss_timer.cancel()
            self.auto_dismiss_timer = None
        
        if self.error_frame:
            # Fade out animation
            AnimationManager.fade_out(
                self.error_frame, 
                duration=200, 
                callback=self._destroy_error_frame
            )
    
    def _destroy_error_frame(self):
        """Safely destroy error frame."""
        if self.error_frame:
            try:
                self.error_frame.destroy()
            except tk.TclError:
                pass
            self.error_frame = None
    
    def _get_level_styling(self, level: ErrorLevel) -> tuple:
        """Get styling based on error level."""
        styling = {
            ErrorLevel.INFO: (
                self.theme_colors['info_bg'],
                self.theme_colors['info_border'],
                "ℹ️"
            ),
            ErrorLevel.WARNING: (
                self.theme_colors['warning_bg'],
                self.theme_colors['warning_border'],
                "⚠️"
            ),
            ErrorLevel.ERROR: (
                self.theme_colors['error_bg'],
                self.theme_colors['error_border'],
                "❌"
            ),
            ErrorLevel.CRITICAL: (
                self.theme_colors['error_bg'],
                self.theme_colors['error_border'],
                "🚨"
            )
        }
        return styling.get(level, styling[ErrorLevel.ERROR])
    
    def _get_default_title(self, level: ErrorLevel) -> str:
        """Get default title based on error level."""
        titles = {
            ErrorLevel.INFO: "Information",
            ErrorLevel.WARNING: "Warning",
            ErrorLevel.ERROR: "Error",
            ErrorLevel.CRITICAL: "Critical Error"
        }
        return titles.get(level, "Error")
    
    def _darken_color(self, color: str, factor: float = 0.8) -> str:
        """Darken a hex color."""
        try:
            # Remove # if present
            color = color.lstrip('#')
            
            # Convert to RGB
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            
            # Darken
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return color


class NotificationToast:
    """Lightweight notification toast for quick messages."""
    
    def __init__(self, parent: ctk.CTkBaseClass, theme_colors: Optional[Dict[str, str]] = None):
        self.parent = parent
        self.theme_colors = theme_colors or {
            'toast_bg': '#2A2A2A',
            'toast_border': '#4A4A4A',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336',
            'info': '#2196F3',
            'text': '#FFFFFF'
        }
        
        self.active_toasts = []
    
    def show_toast(self, 
                  message: str, 
                  level: ErrorLevel = ErrorLevel.INFO,
                  duration: int = 3000,
                  position: str = "top-right") -> ctk.CTkFrame:
        """Show notification toast."""
        
        # Create toast frame
        toast_frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.theme_colors['toast_bg'],
            border_color=self._get_toast_color(level),
            border_width=1,
            corner_radius=8,
            height=60
        )
        
        # Position toast
        self._position_toast(toast_frame, position)
        
        # Create content
        content_frame = ctk.CTkFrame(toast_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Icon
        icon = self._get_toast_icon(level)
        icon_label = ctk.CTkLabel(
            content_frame,
            text=icon,
            font=("JetBrains Mono", 16),
            text_color=self._get_toast_color(level)
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        # Message
        message_label = ctk.CTkLabel(
            content_frame,
            text=message,
            font=("JetBrains Mono", 12),
            text_color=self.theme_colors['text'],
            anchor="w"
        )
        message_label.pack(side="left", fill="both", expand=True)
        
        # Add to active toasts
        self.active_toasts.append(toast_frame)
        
        # Entrance animation
        AnimationManager.slide_in(toast_frame, direction="right", duration=300, distance=100)
        
        # Auto-dismiss
        def dismiss_toast():
            if toast_frame in self.active_toasts:
                self.active_toasts.remove(toast_frame)
                AnimationManager.slide_in(
                    toast_frame, 
                    direction="right", 
                    duration=300, 
                    distance=100
                )
                self.parent.after(300, lambda: self._safe_destroy(toast_frame))
        
        self.parent.after(duration, dismiss_toast)
        
        return toast_frame
    
    def _position_toast(self, toast_frame: ctk.CTkFrame, position: str):
        """Position toast based on specified location."""
        # Calculate position based on existing toasts
        offset = len(self.active_toasts) * 70  # 60px height + 10px margin
        
        if position == "top-right":
            toast_frame.place(relx=1.0, rely=0.0, x=-20, y=20 + offset, anchor="ne")
        elif position == "top-left":
            toast_frame.place(relx=0.0, rely=0.0, x=20, y=20 + offset, anchor="nw")
        elif position == "bottom-right":
            toast_frame.place(relx=1.0, rely=1.0, x=-20, y=-20 - offset, anchor="se")
        elif position == "bottom-left":
            toast_frame.place(relx=0.0, rely=1.0, x=20, y=-20 - offset, anchor="sw")
        else:  # center
            toast_frame.place(relx=0.5, rely=0.1, y=offset, anchor="n")
    
    def _get_toast_color(self, level: ErrorLevel) -> str:
        """Get color for toast based on level."""
        colors = {
            ErrorLevel.INFO: self.theme_colors['info'],
            ErrorLevel.WARNING: self.theme_colors['warning'],
            ErrorLevel.ERROR: self.theme_colors['error'],
            ErrorLevel.CRITICAL: self.theme_colors['error']
        }
        return colors.get(level, self.theme_colors['info'])
    
    def _get_toast_icon(self, level: ErrorLevel) -> str:
        """Get icon for toast based on level."""
        icons = {
            ErrorLevel.INFO: "ℹ️",
            ErrorLevel.WARNING: "⚠️",
            ErrorLevel.ERROR: "❌",
            ErrorLevel.CRITICAL: "🚨"
        }
        return icons.get(level, "ℹ️")
    
    def _safe_destroy(self, widget):
        """Safely destroy widget."""
        try:
            widget.destroy()
        except tk.TclError:
            pass
    
    def clear_all_toasts(self):
        """Clear all active toasts."""
        for toast in self.active_toasts[:]:
            self._safe_destroy(toast)
        self.active_toasts.clear()


class ErrorManager:
    """Comprehensive error management system."""
    
    def __init__(self, parent: ctk.CTkBaseClass, theme_colors: Optional[Dict[str, str]] = None):
        self.parent = parent
        self.theme_colors = theme_colors
        
        self.error_card = ErrorCard(parent, theme_colors)
        self.notification_toast = NotificationToast(parent, theme_colors)
        
        # Error logging
        self.error_log = []
        self.max_log_entries = 100
    
    def show_error(self, 
                  message: str,
                  level: ErrorLevel = ErrorLevel.ERROR,
                  title: Optional[str] = None,
                  details: Optional[str] = None,
                  show_toast: bool = True,
                  show_card: bool = True,
                  actions: Optional[List[Dict[str, Callable]]] = None) -> Optional[ctk.CTkFrame]:
        """Show error with both toast and card options."""
        
        # Log error
        self._log_error(message, level, details)
        
        error_frame = None
        
        # Show toast for quick feedback
        if show_toast:
            self.notification_toast.show_toast(message, level)
        
        # Show detailed card for important errors
        if show_card and level in [ErrorLevel.ERROR, ErrorLevel.CRITICAL]:
            error_frame = self.error_card.show_error_card(
                message=message,
                level=level,
                title=title,
                details=details,
                actions=actions,
                auto_dismiss=10000 if level == ErrorLevel.ERROR else None
            )
        
        return error_frame
    
    def show_success(self, message: str, show_toast: bool = True):
        """Show success message."""
        if show_toast:
            # Customize toast colors for success
            success_colors = self.theme_colors.copy() if self.theme_colors else {}
            success_colors.update({
                'info': '#4CAF50',  # Green for success
            })
            
            toast = NotificationToast(self.parent, success_colors)
            toast.show_toast(f"✅ {message}", ErrorLevel.INFO)
    
    def show_loading_error(self, operation: str, error_details: str):
        """Show loading-specific error."""
        self.show_error(
            message=f"Failed to {operation}",
            level=ErrorLevel.ERROR,
            title="Loading Error",
            details=error_details,
            actions=[
                {
                    'text': 'Retry',
                    'callback': lambda: self._retry_operation(operation)
                },
                {
                    'text': 'Cancel',
                    'callback': self.error_card.dismiss_error_card
                }
            ]
        )
    
    def show_network_error(self, details: str = ""):
        """Show network-specific error."""
        self.show_error(
            message="Network connection failed",
            level=ErrorLevel.WARNING,
            title="Connection Error",
            details=f"Please check your internet connection. {details}",
            actions=[
                {
                    'text': 'Retry',
                    'callback': lambda: self._retry_network_operation()
                }
            ]
        )
    
    def show_api_error(self, api_name: str, status_code: int, details: str = ""):
        """Show API-specific error."""
        self.show_error(
            message=f"{api_name} API error (Code: {status_code})",
            level=ErrorLevel.ERROR,
            title="API Error",
            details=details or "The service is temporarily unavailable.",
            actions=[
                {
                    'text': 'Retry',
                    'callback': lambda: self._retry_api_call(api_name)
                }
            ]
        )
    
    def _log_error(self, message: str, level: ErrorLevel, details: Optional[str]):
        """Log error for debugging."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'message': message,
            'details': details
        }
        
        self.error_log.append(log_entry)
        
        # Maintain log size
        if len(self.error_log) > self.max_log_entries:
            self.error_log = self.error_log[-self.max_log_entries:]
    
    def _retry_operation(self, operation: str):
        """Placeholder for retry operations."""
        self.error_card.dismiss_error_card()
        self.show_success(f"Retrying {operation}...")
    
    def _retry_network_operation(self):
        """Placeholder for network retry."""
        self.error_card.dismiss_error_card()
        self.show_success("Checking connection...")
    
    def _retry_api_call(self, api_name: str):
        """Placeholder for API retry."""
        self.error_card.dismiss_error_card()
        self.show_success(f"Retrying {api_name} API...")
    
    def get_error_log(self) -> List[Dict]:
        """Get error log for debugging."""
        return self.error_log.copy()
    
    def clear_error_log(self):
        """Clear error log."""
        self.error_log.clear()
    
    def update_theme(self, theme_data: Dict = None):
        """Update theme colors for error manager components."""
        if theme_data:
            self.theme_colors = theme_data
            # Update error card and toast themes if they exist
            if hasattr(self.error_card, 'update_theme'):
                self.error_card.update_theme(theme_data)
            if hasattr(self.notification_toast, 'update_theme'):
                self.notification_toast.update_theme(theme_data)
    
    def cleanup(self):
        """Clean up error manager resources."""
        self.error_card.dismiss_error_card()
        self.notification_toast.clear_all_toasts()