"""Event Handling Mixin

Handles all user interactions, event bindings, and input processing.
"""

import customtkinter as ctk
from typing import Optional

from .base_dashboard import BaseDashboard


class EventMixin(BaseDashboard):
    """Mixin for event handling and user interactions."""
    
    def __init__(self):
        """Initialize event handling."""
        super().__init__()
        
        # Event state
        self._last_key_time = 0
        self._key_sequence = ""
    
    def _setup_bindings(self):
        """Set up all event bindings for the dashboard."""
        self._log_method_call("_setup_bindings")
        
        try:
            # Window-level bindings
            self._configure_window_bindings()
            
            # Global key bindings
            self.bind_all("<Key>", self._on_key_input)
            self.bind_all("<KeyRelease>", self._on_key_release)
            
            # Mouse bindings
            self.bind("<Button-1>", self._on_click)
            
            # Focus bindings
            self.bind_all("<FocusIn>", self._on_widget_focus_in)
            self.bind_all("<FocusOut>", self._on_widget_focus_out)
            
            if self.logger:
                self.logger.info("🔗 Event bindings configured")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to setup bindings: {e}")
    
    def _on_click(self, event):
        """Handle mouse click events."""
        try:
            # Log click for debugging
            widget_name = event.widget.__class__.__name__
            self._log_method_call("_on_click", f"widget={widget_name}")
            
            # Handle click on different widgets
            self._on_widget_click(event)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Click handler error: {e}")
    
    def _on_key_input(self, event):
        """Handle key input events."""
        try:
            key = event.keysym
            widget = event.widget
            
            # Log key input for debugging
            self.logger.debug(f"Key input: {key} on {widget.__class__.__name__}")
            
            # Handle special keys
            if key == "Return" or key == "KP_Enter":
                self._handle_enter_key(event)
            elif key == "Escape":
                self._handle_escape_key(event)
            elif key == "F5":
                self._handle_refresh_key(event)
            elif key == "Tab":
                self._handle_tab_key(event)
            
            # Update key sequence for debugging
            self._update_key_sequence(key)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Key input handler error: {e}")
    
    def _on_key_release(self, event):
        """Handle key release events."""
        try:
            key = event.keysym
            
            # Log key release for debugging
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug(f"Key release: {key}")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Key release handler error: {e}")
    
    def _on_widget_click(self, event):
        """Handle widget-specific click events."""
        try:
            widget = event.widget
            widget_class = widget.__class__.__name__
            
            # Handle different widget types
            if "Entry" in widget_class:
                self._handle_entry_click(widget, event)
            elif "Button" in widget_class:
                self._handle_button_click(widget, event)
            elif "Frame" in widget_class:
                self._handle_frame_click(widget, event)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Widget click handler error: {e}")
    
    def _on_widget_focus_in(self, event):
        """Handle widget gaining focus."""
        try:
            widget = event.widget
            widget_class = widget.__class__.__name__
            
            if self.logger:
                self.logger.debug(f"Focus in: {widget_class}")
            
            # Handle focus for search widgets
            if "Entry" in widget_class and hasattr(widget, 'get'):
                self._handle_search_focus_in(widget)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Focus in handler error: {e}")
    
    def _on_widget_focus_out(self, event):
        """Handle widget losing focus."""
        try:
            widget = event.widget
            widget_class = widget.__class__.__name__
            
            if self.logger:
                self.logger.debug(f"Focus out: {widget_class}")
            
            # Handle focus loss for search widgets
            if "Entry" in widget_class and hasattr(widget, 'get'):
                self._handle_search_focus_out(widget)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Focus out handler error: {e}")
    
    def _handle_enter_key(self, event):
        """Handle Enter key press."""
        widget = event.widget
        
        # If in search widget, trigger search
        if hasattr(widget, 'get') and "Entry" in widget.__class__.__name__:
            search_text = widget.get().strip()
            if search_text:
                self._perform_search(search_text)
    
    def _handle_escape_key(self, event):
        """Handle Escape key press."""
        # Clear focus from current widget
        self.focus()
        
        # Clear search if in search widget
        widget = event.widget
        if hasattr(widget, 'delete') and "Entry" in widget.__class__.__name__:
            widget.delete(0, 'end')
    
    def _handle_refresh_key(self, event):
        """Handle F5 key press for refresh."""
        if hasattr(self, '_refresh_weather'):
            self._refresh_weather()
    
    def _handle_tab_key(self, event):
        """Handle Tab key press for navigation."""
        # Let default tab behavior handle focus navigation
        pass
    
    def _handle_entry_click(self, widget, event):
        """Handle click on entry widgets."""
        # Select all text on click for easy editing
        if hasattr(widget, 'select_range'):
            widget.select_range(0, 'end')
    
    def _handle_button_click(self, widget, event):
        """Handle click on button widgets."""
        # Log button clicks
        if self.logger:
            button_text = getattr(widget, '_text', 'Unknown')
            self.logger.debug(f"Button clicked: {button_text}")
    
    def _handle_frame_click(self, widget, event):
        """Handle click on frame widgets."""
        # Clear focus from other widgets when clicking on frames
        self.focus()
    
    def _handle_search_focus_in(self, widget):
        """Handle search widget gaining focus."""
        # Store current text for comparison
        if hasattr(widget, 'get'):
            self._last_known_text = widget.get()
    
    def _handle_search_focus_out(self, widget):
        """Handle search widget losing focus."""
        # Check if text changed and trigger search if needed
        if hasattr(widget, 'get'):
            current_text = widget.get().strip()
            if current_text and current_text != self._last_known_text:
                if self._validate_city_name(current_text):
                    self._perform_search(current_text)
    
    def _update_key_sequence(self, key: str):
        """Update key sequence for debugging."""
        import time
        current_time = time.time()
        
        # Reset sequence if too much time has passed
        if current_time - self._last_key_time > 2.0:
            self._key_sequence = ""
        
        # Add key to sequence
        self._key_sequence += key
        self._last_key_time = current_time
        
        # Keep sequence reasonable length
        if len(self._key_sequence) > 20:
            self._key_sequence = self._key_sequence[-20:]
    
    def test_search_widget(self):
        """Test search widget functionality."""
        self._log_method_call("test_search_widget")
        
        try:
            # Test enhanced search bar
            if self.enhanced_search_bar:
                if hasattr(self.enhanced_search_bar, 'test_functionality'):
                    return self.enhanced_search_bar.test_functionality()
            
            # Test standard search bar
            if self.search_bar:
                if hasattr(self.search_bar, 'test_functionality'):
                    return self.search_bar.test_functionality()
            
            # Test fallback search
            if self.fallback_search_entry:
                return self.fallback_search_entry
            
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Search widget test failed: {e}")
            return None