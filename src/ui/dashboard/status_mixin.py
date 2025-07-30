"""Status and Loading Management Mixin

Handles status updates, loading states, and user feedback.
"""

import customtkinter as ctk
from typing import Optional
from datetime import datetime

from .base_dashboard import BaseDashboard


class StatusMixin(BaseDashboard):
    """Mixin for status and loading state management."""
    
    def __init__(self):
        """Initialize status management."""
        super().__init__()
        
        # Status UI components
        self.status_bar: Optional[ctk.CTkFrame] = None
        self.status_label: Optional[ctk.CTkLabel] = None
        self.last_update_label: Optional[ctk.CTkLabel] = None
        self.loading_overlay: Optional[ctk.CTkFrame] = None
        self.loading_label: Optional[ctk.CTkLabel] = None
        self.loading_spinner: Optional[ctk.CTkProgressBar] = None
        
        # Status state
        self._current_status = ""
        self._current_status_type = self.STATUS_INFO
    
    def _setup_status_bar(self):
        """Set up the status bar at the bottom of the window."""
        self._log_method_call("_setup_status_bar")
        
        try:
            # Create status bar frame
            self.status_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
            self.status_bar.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
            self.status_bar.grid_propagate(False)
            
            # Configure status bar grid
            self.status_bar.grid_columnconfigure(0, weight=1)
            self.status_bar.grid_columnconfigure(1, weight=0)
            
            # Create status label
            self.status_label = ctk.CTkLabel(
                self.status_bar,
                text="Ready",
                font=ctk.CTkFont(size=12),
                anchor="w"
            )
            self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            # Create last update label
            self.last_update_label = ctk.CTkLabel(
                self.status_bar,
                text="",
                font=ctk.CTkFont(size=10),
                text_color="gray60",
                anchor="e"
            )
            self.last_update_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
            
            # Update grid configuration to include status bar
            self.grid_rowconfigure(2, weight=0)
            
            if self.logger:
                self.logger.info("📊 Status bar created")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Status bar setup failed: {e}")
    
    def _update_status(self, message: str, status_type: str = None):
        """Update the status message and color."""
        if status_type is None:
            status_type = self.STATUS_INFO
        
        self._log_method_call("_update_status", message, status_type)
        
        try:
            # Store current status
            self._current_status = message
            self._current_status_type = status_type
            
            # Update status label if available
            if self.status_label:
                self.status_label.configure(
                    text=message,
                    text_color=self._get_status_color(status_type)
                )
            
            # Log status update
            if self.logger:
                status_icon = {
                    self.STATUS_INFO: "ℹ️",
                    self.STATUS_SUCCESS: "✅",
                    self.STATUS_WARNING: "⚠️",
                    self.STATUS_ERROR: "❌"
                }.get(status_type, "ℹ️")
                
                self.logger.info(f"{status_icon} {message}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Status update failed: {e}")
    
    def _update_last_update(self):
        """Update the last update timestamp."""
        try:
            if self.last_update_label:
                timestamp = self._format_timestamp()
                self.last_update_label.configure(text=f"Updated: {timestamp}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Last update timestamp failed: {e}")
    
    def _show_loading(self, message: str = "Loading..."):
        """Show loading overlay with message."""
        self._log_method_call("_show_loading", message)
        
        try:
            # Set loading state
            self.is_loading = True
            
            # Create loading overlay if it doesn't exist
            if not self.loading_overlay:
                self._create_loading_overlay()
            
            # Update loading message
            if self.loading_label:
                self.loading_label.configure(text=message)
            
            # Show loading overlay
            if self.loading_overlay:
                self.loading_overlay.lift()
                self.loading_overlay.grid(
                    row=0, column=0, rowspan=3, columnspan=1,
                    sticky="nsew", padx=0, pady=0
                )
            
            # Start spinner animation
            if self.loading_spinner:
                self.loading_spinner.start()
            
            # Update status
            self._update_status(message, self.STATUS_INFO)
            
        except Exception as e:
            self.is_loading = False
            if self.logger:
                self.logger.error(f"Show loading failed: {e}")
    
    def _hide_loading(self):
        """Hide loading overlay."""
        self._log_method_call("_hide_loading")
        
        try:
            # Clear loading state
            self.is_loading = False
            
            # Stop spinner animation
            if self.loading_spinner:
                self.loading_spinner.stop()
            
            # Hide loading overlay
            if self.loading_overlay:
                self.loading_overlay.grid_remove()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Hide loading failed: {e}")
    
    def _create_loading_overlay(self):
        """Create the loading overlay components."""
        try:
            # Create semi-transparent overlay
            self.loading_overlay = ctk.CTkFrame(
                self,
                fg_color=("gray80", "gray20"),
                corner_radius=0
            )
            
            # Configure overlay grid
            self.loading_overlay.grid_rowconfigure(0, weight=1)
            self.loading_overlay.grid_rowconfigure(1, weight=0)
            self.loading_overlay.grid_rowconfigure(2, weight=1)
            self.loading_overlay.grid_columnconfigure(0, weight=1)
            
            # Create loading content frame
            loading_content = ctk.CTkFrame(
                self.loading_overlay,
                width=300,
                height=150,
                corner_radius=10
            )
            loading_content.grid(row=1, column=0, padx=20, pady=20)
            loading_content.grid_propagate(False)
            
            # Configure loading content grid
            loading_content.grid_rowconfigure(0, weight=1)
            loading_content.grid_rowconfigure(1, weight=0)
            loading_content.grid_rowconfigure(2, weight=1)
            loading_content.grid_columnconfigure(0, weight=1)
            
            # Create loading spinner
            self.loading_spinner = ctk.CTkProgressBar(
                loading_content,
                mode="indeterminate",
                width=200
            )
            self.loading_spinner.grid(row=1, column=0, padx=20, pady=(20, 10))
            
            # Create loading label
            self.loading_label = ctk.CTkLabel(
                loading_content,
                text="Loading...",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            self.loading_label.grid(row=2, column=0, padx=20, pady=(0, 20))
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Loading overlay creation failed: {e}")
    
    def _get_current_status(self) -> tuple[str, str]:
        """Get current status message and type."""
        return self._current_status, self._current_status_type
    
    def _clear_status(self):
        """Clear the current status message."""
        self._update_status("Ready", self.STATUS_INFO)
    
    def _show_temporary_status(self, message: str, status_type: str, duration_ms: int = 3000):
        """Show a temporary status message that auto-clears."""
        self._log_method_call("_show_temporary_status", message, status_type, duration_ms)
        
        try:
            # Show the status
            self._update_status(message, status_type)
            
            # Schedule status clear
            self.after(duration_ms, self._clear_status)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Temporary status failed: {e}")
    
    def _update_loading_progress(self, progress: float, message: str = None):
        """Update loading progress (0.0 to 1.0)."""
        try:
            if self.loading_spinner and hasattr(self.loading_spinner, 'set'):
                self.loading_spinner.set(progress)
            
            if message and self.loading_label:
                self.loading_label.configure(text=message)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Loading progress update failed: {e}")
    
    def _is_loading_visible(self) -> bool:
        """Check if loading overlay is currently visible."""
        try:
            return (self.loading_overlay is not None and 
                   self.loading_overlay.winfo_viewable())
        except:
            return False