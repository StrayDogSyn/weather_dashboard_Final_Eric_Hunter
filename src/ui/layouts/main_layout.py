"""Main Layout Component

Provides the overall application layout structure.
"""

from typing import Optional, Dict, Any
import customtkinter as ctk
from ..components.glassmorphic.base_frame import GlassmorphicFrame
from ..components.common.header import HeaderComponent as Header
from ..components.common.status_bar_component import StatusBarComponent
from ..components.common.loading_spinner import LoadingSpinner
from ..components.common.error_display import ErrorDisplay


class MainLayout(ctk.CTkFrame):
    """Main application layout with header, content area, and status bar."""

    def __init__(self, parent, **kwargs):
        """Initialize main layout.
        
        Args:
            parent: Parent widget
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        # Layout components
        self.header: Optional[Header] = None
        self.content_area: Optional[ctk.CTkFrame] = None
        self.status_bar: Optional[StatusBarComponent] = None
        self.loading_overlay: Optional[LoadingSpinner] = None
        self.error_overlay: Optional[ErrorDisplay] = None
        
        # Layout configuration
        self.header_height = 60
        self.status_bar_height = 30
        self.show_header = True
        self.show_status_bar = True
        
        # Styling
        self.configure(
            fg_color=("#0D0D0D", "#1A1A1A"),
            corner_radius=0
        )
        
        self._setup_layout()
    
    def _setup_layout(self):
        """Setup the main layout structure."""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        
        current_row = 0
        
        # Header section
        if self.show_header:
            self.grid_rowconfigure(current_row, weight=0)
            self._create_header(current_row)
            current_row += 1
        
        # Content area (expandable)
        self.grid_rowconfigure(current_row, weight=1)
        self._create_content_area(current_row)
        current_row += 1
        
        # Status bar section
        if self.show_status_bar:
            self.grid_rowconfigure(current_row, weight=0)
            self._create_status_bar(current_row)
            current_row += 1
    
    def _create_header(self, row: int):
        """Create header section.
        
        Args:
            row: Grid row for header
        """
        self.header = Header(
            self,
            height=self.header_height,
            corner_radius=0
        )
        self.header.grid(row=row, column=0, sticky="ew", padx=0, pady=0)
    
    def _create_content_area(self, row: int):
        """Create main content area.
        
        Args:
            row: Grid row for content area
        """
        self.content_area = GlassmorphicFrame(
            self,
            corner_radius=0,
            border_width=0
        )
        self.content_area.grid(row=row, column=0, sticky="nsew", padx=0, pady=0)
        
        # Configure content area grid
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)
    
    def _create_status_bar(self, row: int):
        """Create status bar section.
        
        Args:
            row: Grid row for status bar
        """
        self.status_bar = StatusBarComponent(
            self,
            height=self.status_bar_height,
            corner_radius=0
        )
        self.status_bar.grid(row=row, column=0, sticky="ew", padx=0, pady=0)
    
    def set_content(self, content_widget: ctk.CTkBaseClass):
        """Set the main content widget.
        
        Args:
            content_widget: Widget to display in content area
        """
        if self.content_area:
            # Clear existing content
            for child in self.content_area.winfo_children():
                child.destroy()
            
            # Add new content
            content_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    
    def get_header(self) -> Optional[Header]:
        """Get header component.
        
        Returns:
            Header component or None
        """
        return self.header
    
    def get_status_bar(self) -> Optional[StatusBarComponent]:
        """Get status bar component.
        
        Returns:
            Status bar component or None
        """
        return self.status_bar
    
    def get_content_area(self) -> Optional[ctk.CTkFrame]:
        """Get content area frame.
        
        Returns:
            Content area frame or None
        """
        return self.content_area
    
    def show_loading(self, message: str = "Loading..."):
        """Show loading overlay.
        
        Args:
            message: Loading message to display
        """
        self.hide_error()  # Hide any existing error
        
        if not self.loading_overlay:
            self.loading_overlay = LoadingSpinner(
                self,
                size=60,
                message=message
            )
        else:
            self.loading_overlay.set_message(message)
        
        # Position overlay in center
        self.loading_overlay.place(
            relx=0.5, rely=0.5,
            anchor="center"
        )
        self.loading_overlay.start_spinning()
    
    def hide_loading(self):
        """Hide loading overlay."""
        if self.loading_overlay:
            self.loading_overlay.stop_spinning()
            self.loading_overlay.place_forget()
    
    def show_error(self, message: str, details: str = "", title: str = "Error"):
        """Show error overlay.
        
        Args:
            message: Error message
            details: Additional error details
            title: Error title
        """
        self.hide_loading()  # Hide any existing loading
        
        if not self.error_overlay:
            self.error_overlay = ErrorDisplay(
                self,
                width=400,
                height=250
            )
        
        self.error_overlay.show_error(message, details, title)
        
        # Position overlay in center
        self.error_overlay.place(
            relx=0.5, rely=0.5,
            anchor="center"
        )
    
    def hide_error(self):
        """Hide error overlay."""
        if self.error_overlay:
            self.error_overlay.place_forget()
    
    def set_error_retry_callback(self, callback):
        """Set retry callback for error overlay.
        
        Args:
            callback: Function to call when retry is clicked
        """
        if self.error_overlay:
            self.error_overlay.set_retry_callback(callback)
    
    def update_status(self, message: str, status_type: str = "info"):
        """Update status bar message.
        
        Args:
            message: Status message
            status_type: Type of status ("info", "warning", "error", "success")
        """
        if self.status_bar:
            if hasattr(self.status_bar, 'update_status'):
                self.status_bar.update_status(message, status_type)
            elif hasattr(self.status_bar, 'set_status'):
                self.status_bar.set_status(message)
    
    def set_header_title(self, title: str):
        """Set header title.
        
        Args:
            title: Header title text
        """
        if self.header and hasattr(self.header, 'set_title'):
            self.header.set_title(title)
    
    def configure_layout(self, 
                        show_header: bool = True, 
                        show_status_bar: bool = True,
                        header_height: int = 60,
                        status_bar_height: int = 30):
        """Configure layout options.
        
        Args:
            show_header: Whether to show header
            show_status_bar: Whether to show status bar
            header_height: Header height in pixels
            status_bar_height: Status bar height in pixels
        """
        self.show_header = show_header
        self.show_status_bar = show_status_bar
        self.header_height = header_height
        self.status_bar_height = status_bar_height
        
        # Recreate layout if configuration changed
        self._recreate_layout()
    
    def _recreate_layout(self):
        """Recreate layout with new configuration."""
        # Store current content
        current_content = None
        if self.content_area and self.content_area.winfo_children():
            current_content = self.content_area.winfo_children()[0]
            current_content.grid_forget()
        
        # Clear existing layout
        for child in self.winfo_children():
            if child not in [self.loading_overlay, self.error_overlay]:
                child.destroy()
        
        # Reset component references
        self.header = None
        self.content_area = None
        self.status_bar = None
        
        # Recreate layout
        self._setup_layout()
        
        # Restore content
        if current_content and self.content_area:
            current_content.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    
    def get_layout_info(self) -> Dict[str, Any]:
        """Get current layout information.
        
        Returns:
            Dictionary with layout information
        """
        return {
            "show_header": self.show_header,
            "show_status_bar": self.show_status_bar,
            "header_height": self.header_height,
            "status_bar_height": self.status_bar_height,
            "has_content": self.content_area is not None and bool(self.content_area.winfo_children()),
            "loading_visible": self.loading_overlay is not None and self.loading_overlay.winfo_viewable(),
            "error_visible": self.error_overlay is not None and self.error_overlay.winfo_viewable()
        }