"""Status bar component for the weather dashboard."""

import tkinter as tk
from datetime import datetime
import customtkinter as ctk


class StatusBar:
    """Status bar component with connection indicator and time display."""
    
    def __init__(self, parent):
        """Initialize the status bar.
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.is_destroyed = False
        self.scheduled_calls = []
        
        # Create status bar frame
        self.status_frame = ctk.CTkFrame(
            parent,
            height=30,
            corner_radius=0,
            fg_color=("#f0f0f0", "#2b2b2b")
        )
        
        # Create status components
        self._create_status_components()
        
        # Start time updates
        self._update_time()
    
    def _create_status_components(self):
        """Create status bar components."""
        # Status label
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=("Segoe UI", 11),
            text_color=("#666666", "#cccccc")
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Connection indicator
        self.connection_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=("Segoe UI", 12),
            text_color="#4CAF50"  # Green for connected
        )
        self.connection_indicator.pack(side="left", padx=(0, 10))
        
        # Time display
        self.time_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=("Segoe UI", 11),
            text_color=("#666666", "#cccccc")
        )
        self.time_label.pack(side="right", padx=10, pady=5)
    
    def pack(self, **kwargs):
        """Pack the status bar frame."""
        self.status_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the status bar frame."""
        self.status_frame.grid(**kwargs)
    
    def update_status(self, message):
        """Update status message.
        
        Args:
            message: Status message to display
        """
        if not self.is_destroyed:
            self.status_label.configure(text=message)
    
    def update_connection_status(self, connected=True):
        """Update connection indicator.
        
        Args:
            connected: Whether connection is active
        """
        if not self.is_destroyed:
            color = "#4CAF50" if connected else "#f44336"  # Green or red
            self.connection_indicator.configure(text_color=color)
    
    def _update_time(self):
        """Update time display."""
        try:
            if self.is_destroyed or not hasattr(self.parent, 'winfo_exists') or not self.parent.winfo_exists():
                return
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.configure(text=current_time)
            
            # Schedule next update
            call_id = self.safe_after(1000, self._update_time)
            if call_id:
                self.scheduled_calls.append(call_id)
                
        except tk.TclError:
            # Widget has been destroyed, stop the timer
            return
    
    def safe_after(self, delay, callback):
        """Safely schedule a callback.
        
        Args:
            delay: Delay in milliseconds
            callback: Callback function
            
        Returns:
            Call ID or None if failed
        """
        try:
            if not self.is_destroyed and hasattr(self.parent, 'after'):
                return self.parent.after(delay, callback)
        except (tk.TclError, AttributeError):
            pass
        return None
    
    def cleanup(self):
        """Clean up scheduled calls and mark as destroyed."""
        self.is_destroyed = True
        
        # Cancel scheduled calls
        for call_id in self.scheduled_calls:
            try:
                if hasattr(self.parent, 'after_cancel'):
                    self.parent.after_cancel(call_id)
            except (tk.TclError, AttributeError):
                pass
        
        self.scheduled_calls.clear()
    
    def destroy(self):
        """Destroy the status bar."""
        self.cleanup()
        if hasattr(self.status_frame, 'destroy'):
            self.status_frame.destroy()