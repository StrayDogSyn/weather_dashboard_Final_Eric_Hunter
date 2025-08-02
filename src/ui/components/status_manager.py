"""Enhanced Status Message System

Provides dynamic status messages, weather facts, contextual help,
and smooth transitions for better user experience.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, Dict, List, Callable
import threading
import time
import random
from datetime import datetime
from enum import Enum

from .animation_manager import AnimationManager


class StatusType(Enum):
    """Status message types."""
    READY = "ready"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    TIP = "tip"
    FACT = "fact"


class StatusMessageManager:
    """Enhanced status message manager with dynamic content."""
    
    def __init__(self, parent: ctk.CTkBaseClass, theme_colors: Optional[Dict[str, str]] = None):
        self.parent = parent
        self.theme_colors = theme_colors or {
            'status_bg': '#1A1A1A',
            'status_text': '#FFFFFF',
            'status_secondary': '#CCCCCC',
            'accent': '#4A9EFF',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336'
        }
        
        self.status_frame = None
        self.status_label = None
        self.icon_label = None
        self.progress_bar = None
        
        self.current_status = StatusType.READY
        self.auto_cycle_timer = None
        self.typing_timer = None
        self.scheduled_calls = []
        self.is_destroyed = False
        
        # Dynamic content
        self.weather_facts = [
            "Did you know? Lightning strikes the Earth about 100 times per second!",
            "Fun fact: No two snowflakes are exactly alike in structure.",
            "Weather tip: Red sky at night, sailor's delight; red sky at morning, sailors take warning.",
            "Interesting: The fastest recorded wind speed was 301 mph during a tornado.",
            "Cool fact: Raindrops are not tear-shaped - they're actually round!",
            "Weather wisdom: Cumulonimbus clouds can reach heights of 60,000 feet.",
            "Did you know? The word 'hurricane' comes from the Taíno word 'huracán'.",
            "Fun fact: Antarctica is technically a desert due to its low precipitation.",
            "Weather insight: Barometric pressure drops before storms arrive.",
            "Fascinating: A single thunderstorm can contain 15 million gallons of water."
        ]
        
        self.helpful_tips = [
            "💡 Tip: Click on any chart to see detailed information",
            "🎨 Tip: Try different themes from the theme selector",
            "📊 Tip: Use the ML panel to compare weather patterns",
            "🔄 Tip: Data refreshes automatically every 10 minutes",
            "⌨️ Tip: Press Ctrl+R to refresh data manually",
            "📍 Tip: Click the location icon to change cities",
            "📈 Tip: Hover over charts for detailed values",
            "🌡️ Tip: Temperature units can be changed in settings",
            "⏰ Tip: Check the forecast tab for 5-day predictions",
            "🔍 Tip: Use search to find weather for any city"
        ]
        
        self.contextual_help = {
            'loading_weather': "Fetching latest weather data from multiple sources...",
            'loading_forecast': "Analyzing forecast patterns and trends...",
            'loading_ml': "Processing machine learning weather insights...",
            'loading_charts': "Generating beautiful weather visualizations...",
            'error_network': "Check your internet connection and try again",
            'error_api': "Weather service temporarily unavailable",
            'success_data': "Weather data updated successfully!",
            'success_theme': "Theme applied successfully!"
        }
    
    def create_status_bar(self, width: int = 400, height: int = 40) -> ctk.CTkFrame:
        """Create enhanced status bar with animations."""
        
        self.status_frame = ctk.CTkFrame(
            self.parent,
            width=width,
            height=height,
            fg_color=self.theme_colors['status_bg'],
            corner_radius=8
        )
        
        # Content container
        content_frame = ctk.CTkFrame(
            self.status_frame,
            fg_color="transparent"
        )
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Icon label
        self.icon_label = ctk.CTkLabel(
            content_frame,
            text="🌤️",
            font=("JetBrains Mono", 16),
            width=30
        )
        self.icon_label.pack(side="left", padx=(0, 10))
        
        # Status text
        self.status_label = ctk.CTkLabel(
            content_frame,
            text="Ready",
            font=("JetBrains Mono", 12),
            text_color=self.theme_colors['status_text'],
            anchor="w"
        )
        self.status_label.pack(side="left", fill="both", expand=True)
        
        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(
            content_frame,
            width=60,
            height=8,
            progress_color=self.theme_colors['accent']
        )
        
        # Start with ready state
        self.set_ready_state()
        
        return self.status_frame
    
    def set_status(self, 
                  message: str, 
                  status_type: StatusType = StatusType.INFO,
                  show_progress: bool = False,
                  progress_value: Optional[float] = None,
                  auto_clear: Optional[int] = None,
                  typing_effect: bool = False):
        """Set status message with animations."""
        
        if not self.status_label:
            return
        
        self.current_status = status_type
        
        # Update icon and colors
        icon, text_color = self._get_status_styling(status_type)
        
        self.icon_label.configure(text=icon)
        self.status_label.configure(text_color=text_color)
        
        # Show/hide progress bar
        if show_progress:
            self.progress_bar.pack(side="right", padx=(10, 0))
            if progress_value is not None:
                self.progress_bar.set(progress_value)
        else:
            self.progress_bar.pack_forget()
        
        # Set message with optional typing effect
        if typing_effect:
            self._type_message(message)
        else:
            self.status_label.configure(text=message)
        
        # Add subtle animation
        AnimationManager.fade_in(self.status_frame, duration=200)
        
        # Auto-clear timer
        if auto_clear:
            def clear_status():
                try:
                    if not self.parent.winfo_exists():
                        return
                    if self.current_status == status_type:  # Only clear if status hasn't changed
                        self.set_ready_state()
                except tk.TclError:
                    # Widget has been destroyed
                    return
            
            self.safe_after(auto_clear, clear_status)
    
    def set_loading_state(self, 
                         operation: str = "Loading",
                         show_progress: bool = True,
                         contextual_message: Optional[str] = None):
        """Set loading state with contextual message."""
        
        message = contextual_message or self.contextual_help.get(
            f'loading_{operation.lower()}', 
            f"{operation}..."
        )
        
        self.set_status(
            message=message,
            status_type=StatusType.LOADING,
            show_progress=show_progress,
            typing_effect=True
        )
        
        # Start progress animation
        if show_progress:
            self._animate_progress()
    
    def set_success_state(self, message: str, auto_clear: int = 3000):
        """Set success state."""
        self.set_status(
            message=message,
            status_type=StatusType.SUCCESS,
            auto_clear=auto_clear
        )
    
    def set_error_state(self, message: str, auto_clear: int = 5000):
        """Set error state."""
        self.set_status(
            message=message,
            status_type=StatusType.ERROR,
            auto_clear=auto_clear
        )
    
    def set_ready_state(self):
        """Set ready state with dynamic tips."""
        # Randomly choose between tip and ready message
        if random.random() < 0.7:  # 70% chance for tip
            tip = random.choice(self.helpful_tips)
            self.set_status(
                message=tip,
                status_type=StatusType.TIP,
                auto_clear=8000
            )
        else:
            self.set_status(
                message="Ready - Weather dashboard is up to date",
                status_type=StatusType.READY
            )
        
        # Start auto-cycling tips
        self._start_auto_cycle()
    
    def show_weather_fact(self):
        """Show random weather fact."""
        fact = random.choice(self.weather_facts)
        self.set_status(
            message=fact,
            status_type=StatusType.FACT,
            auto_clear=10000,
            typing_effect=True
        )
    
    def show_contextual_help(self, context: str):
        """Show contextual help message."""
        help_message = self.contextual_help.get(
            context, 
            "Need help? Check the documentation for more information."
        )
        
        self.set_status(
            message=help_message,
            status_type=StatusType.INFO,
            auto_clear=5000
        )
    
    def show_loading_message(self, message: str = "Loading weather data..."):
        """Show loading message."""
        self.set_loading_state(operation="Loading", contextual_message=message)
    
    def clear_messages(self):
        """Clear all status messages."""
        self.set_ready_state()
    
    def update_progress(self, value: float, message: Optional[str] = None):
        """Update progress bar value."""
        if self.progress_bar and self.progress_bar.winfo_viewable():
            self.progress_bar.set(value)
            
            if message:
                self.status_label.configure(text=message)
    
    def _get_status_styling(self, status_type: StatusType) -> tuple:
        """Get icon and color for status type."""
        styling = {
            StatusType.READY: ("🌤️", self.theme_colors['status_text']),
            StatusType.LOADING: ("⏳", self.theme_colors['accent']),
            StatusType.SUCCESS: ("✅", self.theme_colors['success']),
            StatusType.ERROR: ("❌", self.theme_colors['error']),
            StatusType.INFO: ("ℹ️", self.theme_colors['accent']),
            StatusType.TIP: ("💡", self.theme_colors['accent']),
            StatusType.FACT: ("🌍", self.theme_colors['accent'])
        }
        return styling.get(status_type, styling[StatusType.READY])
    
    def _type_message(self, message: str, delay: int = 50):
        """Create typing effect for message."""
        if self.typing_timer:
            self.parent.after_cancel(self.typing_timer)
        
        def type_char(index: int = 0):
            try:
                if not self.parent.winfo_exists() or not self.status_label:
                    return
                if index <= len(message):
                    self.status_label.configure(text=message[:index])
                    if index < len(message):
                        self.typing_timer = self.safe_after(
                            delay, 
                            lambda: type_char(index + 1)
                        )
            except tk.TclError:
                # Widget has been destroyed
                return
        
        type_char()
    
    def _animate_progress(self):
        """Animate progress bar for loading states."""
        try:
            if not self.parent.winfo_exists():
                return
            if (self.current_status == StatusType.LOADING and 
                self.progress_bar and 
                self.progress_bar.winfo_viewable()):
                
                # Indeterminate progress animation
                current_value = self.progress_bar.get()
                new_value = (current_value + 0.02) % 1.0
                self.progress_bar.set(new_value)
                
                # Continue animation
                self.safe_after(50, self._animate_progress)
        except tk.TclError:
            # Widget has been destroyed
            return
    
    def _start_auto_cycle(self):
        """Start auto-cycling through tips and facts."""
        if self.auto_cycle_timer:
            self.auto_cycle_timer.cancel()
        
        def cycle_content():
            if self.current_status == StatusType.READY:
                # Randomly show tip or fact
                if random.random() < 0.6:
                    tip = random.choice(self.helpful_tips)
                    self.set_status(
                        message=tip,
                        status_type=StatusType.TIP,
                        auto_clear=8000
                    )
                else:
                    self.show_weather_fact()
            
            # Schedule next cycle
            self.auto_cycle_timer = threading.Timer(15.0, cycle_content)
            self.auto_cycle_timer.start()
        
        # Start first cycle
        self.auto_cycle_timer = threading.Timer(10.0, cycle_content)
        self.auto_cycle_timer.start()
    
    def apply_theme(self, theme_colors: Dict[str, str]):
        """Apply new theme colors."""
        self.theme_colors.update(theme_colors)
        
        if self.status_frame:
            self.status_frame.configure(fg_color=self.theme_colors['status_bg'])
        
        if self.status_label:
            self.status_label.configure(text_color=self.theme_colors['status_text'])
        
        if self.progress_bar:
            self.progress_bar.configure(progress_color=self.theme_colors['accent'])
        
        # Update current status styling
        if self.icon_label and self.status_label:
            icon, text_color = self._get_status_styling(self.current_status)
            self.icon_label.configure(text=icon)
            self.status_label.configure(text_color=text_color)
    
    def update_theme(self, theme_data: Dict = None):
        """Update theme colors for status message manager."""
        if theme_data:
            self.apply_theme(theme_data)
    
    def safe_after(self, delay, callback):
        """Safe after() call that tracks scheduled calls for cleanup."""
        if self.is_destroyed:
            return None
        try:
            if not self.parent.winfo_exists():
                return None
            call_id = self.parent.after(delay, callback)
            self.scheduled_calls.append(call_id)
            return call_id
        except tk.TclError:
            return None
    
    def cleanup(self):
        """Clean up timers and resources."""
        self.is_destroyed = True
        
        if self.auto_cycle_timer:
            self.auto_cycle_timer.cancel()
            self.auto_cycle_timer = None
        
        if self.typing_timer:
            try:
                self.parent.after_cancel(self.typing_timer)
            except (tk.TclError, ValueError):
                pass
            self.typing_timer = None
        
        # Cancel all scheduled after() calls
        for call_id in self.scheduled_calls:
            try:
                self.parent.after_cancel(call_id)
            except (tk.TclError, ValueError):
                pass
        self.scheduled_calls.clear()


class TooltipManager:
    """Contextual tooltip system for enhanced user experience."""
    
    def __init__(self, theme_colors: Optional[Dict[str, str]] = None):
        self.theme_colors = theme_colors or {
            'tooltip_bg': '#2A2A2A',
            'tooltip_border': '#4A4A4A',
            'tooltip_text': '#FFFFFF',
            'tooltip_shadow': '#000000'
        }
        
        self.active_tooltips = {}
    
    def add_tooltip(self, 
                   widget: ctk.CTkBaseClass, 
                   text: str,
                   delay: int = 500,
                   follow_mouse: bool = True):
        """Add tooltip to widget."""
        
        tooltip_data = {
            'text': text,
            'delay': delay,
            'follow_mouse': follow_mouse,
            'tooltip_window': None,
            'show_timer': None
        }
        
        def on_enter(event):
            def show_tooltip():
                try:
                    if not widget.winfo_exists():
                        return
                    if widget in self.active_tooltips:
                        self._show_tooltip(widget, event if follow_mouse else None)
                except tk.TclError:
                    # Widget has been destroyed
                    return
            
            try:
                tooltip_data['show_timer'] = widget.after(delay, show_tooltip)
            except tk.TclError:
                pass
        
        def on_leave(event):
            if tooltip_data['show_timer']:
                try:
                    widget.after_cancel(tooltip_data['show_timer'])
                except (tk.TclError, ValueError):
                    pass
                tooltip_data['show_timer'] = None
            
            self._hide_tooltip(widget)
        
        def on_motion(event):
            if follow_mouse and tooltip_data['tooltip_window']:
                self._update_tooltip_position(widget, event)
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
        if follow_mouse:
            widget.bind("<Motion>", on_motion)
        
        self.active_tooltips[widget] = tooltip_data
    
    def _show_tooltip(self, widget: ctk.CTkBaseClass, event=None):
        """Show tooltip window."""
        tooltip_data = self.active_tooltips.get(widget)
        if not tooltip_data:
            return
        
        # Create tooltip window
        tooltip_window = tk.Toplevel(widget)
        tooltip_window.wm_overrideredirect(True)
        tooltip_window.configure(bg=self.theme_colors['tooltip_shadow'])
        
        # Create tooltip frame
        tooltip_frame = ctk.CTkFrame(
            tooltip_window,
            fg_color=self.theme_colors['tooltip_bg'],
            border_color=self.theme_colors['tooltip_border'],
            border_width=1,
            corner_radius=6
        )
        tooltip_frame.pack(padx=1, pady=1)
        
        # Tooltip text
        tooltip_label = ctk.CTkLabel(
            tooltip_frame,
            text=tooltip_data['text'],
            font=("JetBrains Mono", 11),
            text_color=self.theme_colors['tooltip_text'],
            wraplength=300
        )
        tooltip_label.pack(padx=8, pady=6)
        
        # Position tooltip
        if event:
            x = event.x_root + 10
            y = event.y_root + 10
        else:
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() - 30
        
        tooltip_window.geometry(f"+{x}+{y}")
        
        # Store tooltip window
        tooltip_data['tooltip_window'] = tooltip_window
        
        # Fade in animation
        tooltip_window.attributes('-alpha', 0.0)
        self._fade_in_tooltip(tooltip_window)
    
    def _hide_tooltip(self, widget: ctk.CTkBaseClass):
        """Hide tooltip window."""
        tooltip_data = self.active_tooltips.get(widget)
        if tooltip_data and tooltip_data['tooltip_window']:
            try:
                tooltip_data['tooltip_window'].destroy()
            except tk.TclError:
                pass
            tooltip_data['tooltip_window'] = None
    
    def _update_tooltip_position(self, widget: ctk.CTkBaseClass, event):
        """Update tooltip position for mouse following."""
        tooltip_data = self.active_tooltips.get(widget)
        if tooltip_data and tooltip_data['tooltip_window']:
            x = event.x_root + 10
            y = event.y_root + 10
            tooltip_data['tooltip_window'].geometry(f"+{x}+{y}")
    
    def _fade_in_tooltip(self, tooltip_window, alpha: float = 0.0):
        """Fade in tooltip animation."""
        try:
            if not tooltip_window.winfo_exists():
                return
            if alpha < 0.9:
                tooltip_window.attributes('-alpha', alpha)
                try:
                    tooltip_window.after(20, lambda: self._fade_in_tooltip(tooltip_window, alpha + 0.1))
                except tk.TclError:
                    pass
            else:
                tooltip_window.attributes('-alpha', 0.9)
        except tk.TclError:
            pass
    
    def remove_tooltip(self, widget: ctk.CTkBaseClass):
        """Remove tooltip from widget."""
        if widget in self.active_tooltips:
            self._hide_tooltip(widget)
            del self.active_tooltips[widget]
    
    def cleanup(self):
        """Clean up all tooltips."""
        for widget in list(self.active_tooltips.keys()):
            self.remove_tooltip(widget)