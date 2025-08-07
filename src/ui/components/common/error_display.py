"""Error Display Component

Reusable error display widget with glassmorphic styling.
"""

from typing import Optional, Callable
import customtkinter as ctk
from ..glassmorphic.base_frame import GlassmorphicFrame
from ..glassmorphic.glass_button import GlassButton


class ErrorDisplay(GlassmorphicFrame):
    """Error display component with glassmorphic styling."""

    def __init__(self, parent, width: int = 400, height: int = 200, **kwargs):
        """Initialize error display.
        
        Args:
            parent: Parent widget
            width: Display width
            height: Display height
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, width=width, height=height, **kwargs)
        
        self.error_message = ""
        self.error_details = ""
        self.retry_callback: Optional[Callable] = None
        
        # Styling
        self.error_colors = {
            "bg": ("#2A1A1A", "#3A2A2A"),
            "border": ("#FF4444", "#FF6666"),
            "text": ("#FFE0E0", "#FFFFFF"),
            "accent": "#FF4444",
            "button": ("#FF3333", "#FF5555")
        }
        
        # Configure frame styling
        self.configure(
            fg_color=self.error_colors["bg"],
            border_width=2,
            border_color=self.error_colors["border"]
        )
        
        self._setup_layout()
    
    def _setup_layout(self):
        """Setup the error display layout."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Error icon and title
        self._create_header()
        
        # Error message area
        self._create_message_area()
        
        # Action buttons
        self._create_action_buttons()
    
    def _create_header(self):
        """Create error header with icon and title."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Error icon
        icon_label = ctk.CTkLabel(
            header_frame,
            text="⚠️",
            font=("Segoe UI Emoji", 24)
        )
        icon_label.grid(row=0, column=0, padx=(0, 10))
        
        # Error title
        self.title_label = ctk.CTkLabel(
            header_frame,
            text="Error Occurred",
            font=("Consolas", 16, "bold"),
            text_color=self.error_colors["accent"]
        )
        self.title_label.grid(row=0, column=1, sticky="w")
    
    def _create_message_area(self):
        """Create scrollable message area."""
        # Message frame with scrollbar
        message_frame = ctk.CTkFrame(
            self,
            fg_color=("#1A1A1A", "#2A2A2A"),
            corner_radius=8
        )
        message_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        message_frame.grid_columnconfigure(0, weight=1)
        message_frame.grid_rowconfigure(0, weight=1)
        
        # Scrollable text widget
        self.message_text = ctk.CTkTextbox(
            message_frame,
            font=("Consolas", 11),
            text_color=self.error_colors["text"],
            fg_color="transparent",
            wrap="word",
            state="disabled"
        )
        self.message_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def _create_action_buttons(self):
        """Create action buttons."""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Retry button
        self.retry_button = GlassButton(
            button_frame,
            text="🔄 Retry",
            command=self._on_retry_click,
            width=100,
            height=32,
            font=("Consolas", 11, "bold")
        )
        self.retry_button.grid(row=0, column=0, padx=5)
        
        # Copy error button
        self.copy_button = GlassButton(
            button_frame,
            text="📋 Copy Error",
            command=self._on_copy_click,
            width=100,
            height=32,
            font=("Consolas", 11)
        )
        self.copy_button.grid(row=0, column=1, padx=5)
        
        # Dismiss button
        self.dismiss_button = GlassButton(
            button_frame,
            text="✖️ Dismiss",
            command=self._on_dismiss_click,
            width=100,
            height=32,
            font=("Consolas", 11)
        )
        self.dismiss_button.grid(row=0, column=2, padx=5)
    
    def show_error(self, message: str, details: str = "", title: str = "Error Occurred"):
        """Display an error message.
        
        Args:
            message: Main error message
            details: Additional error details
            title: Error title
        """
        self.error_message = message
        self.error_details = details
        
        # Update title
        try:
            self.title_label.configure(text=title)
        except Exception:
            pass
        
        # Update message text
        try:
            self.message_text.configure(state="normal")
            self.message_text.delete("1.0", "end")
            
            # Insert main message
            self.message_text.insert("end", message)
            
            # Insert details if provided
            if details:
                self.message_text.insert("end", "\n\nDetails:\n")
                self.message_text.insert("end", details)
            
            self.message_text.configure(state="disabled")
        except Exception as e:
            print(f"Error updating message text: {e}")
    
    def show_network_error(self, url: str = "", status_code: Optional[int] = None):
        """Show a network-specific error.
        
        Args:
            url: Failed URL
            status_code: HTTP status code if available
        """
        message = "Network connection failed"
        details = "Please check your internet connection and try again."
        
        if url:
            details += f"\n\nURL: {url}"
        
        if status_code:
            details += f"\nStatus Code: {status_code}"
            
            # Add specific status code messages
            status_messages = {
                400: "Bad Request - Invalid request format",
                401: "Unauthorized - Authentication required",
                403: "Forbidden - Access denied",
                404: "Not Found - Resource not available",
                429: "Too Many Requests - Rate limit exceeded",
                500: "Internal Server Error - Server issue",
                502: "Bad Gateway - Server communication error",
                503: "Service Unavailable - Server temporarily down"
            }
            
            if status_code in status_messages:
                details += f"\n{status_messages[status_code]}"
        
        self.show_error(message, details, "Network Error")
    
    def show_api_error(self, api_name: str, error_code: str = "", error_message: str = ""):
        """Show an API-specific error.
        
        Args:
            api_name: Name of the API that failed
            error_code: API error code
            error_message: API error message
        """
        message = f"{api_name} API Error"
        details = f"The {api_name} service encountered an error."
        
        if error_code:
            details += f"\n\nError Code: {error_code}"
        
        if error_message:
            details += f"\nError Message: {error_message}"
        
        details += "\n\nPlease try again later or contact support if the problem persists."
        
        self.show_error(message, details, f"{api_name} Error")
    
    def show_validation_error(self, field_name: str, validation_message: str):
        """Show a validation error.
        
        Args:
            field_name: Name of the field that failed validation
            validation_message: Validation error message
        """
        message = f"Invalid {field_name}"
        details = validation_message
        
        self.show_error(message, details, "Validation Error")
    
    def set_retry_callback(self, callback: Callable):
        """Set callback for retry button.
        
        Args:
            callback: Function to call when retry is clicked
        """
        self.retry_callback = callback
        
        # Show/hide retry button based on callback
        if callback:
            self.retry_button.grid()
        else:
            self.retry_button.grid_remove()
    
    def _on_retry_click(self):
        """Handle retry button click."""
        if self.retry_callback:
            try:
                self.retry_callback()
            except Exception as e:
                print(f"Error in retry callback: {e}")
    
    def _on_copy_click(self):
        """Handle copy error button click."""
        try:
            # Prepare error text for clipboard
            error_text = self.error_message
            if self.error_details:
                error_text += f"\n\nDetails:\n{self.error_details}"
            
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(error_text)
            
            # Temporarily change button text to show success
            original_text = self.copy_button.cget("text")
            self.copy_button.configure(text="✅ Copied!")
            self.after(2000, lambda: self.copy_button.configure(text=original_text))
            
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
    
    def _on_dismiss_click(self):
        """Handle dismiss button click."""
        try:
            # Hide the error display
            self.pack_forget()
            self.grid_forget()
            self.place_forget()
        except Exception as e:
            print(f"Error dismissing error display: {e}")
    
    def clear_error(self):
        """Clear the current error display."""
        self.error_message = ""
        self.error_details = ""
        
        try:
            self.title_label.configure(text="Error Occurred")
            self.message_text.configure(state="normal")
            self.message_text.delete("1.0", "end")
            self.message_text.configure(state="disabled")
        except Exception:
            pass


class InlineErrorDisplay(ctk.CTkFrame):
    """Compact inline error display for forms and inputs."""

    def __init__(self, parent, **kwargs):
        """Initialize inline error display.
        
        Args:
            parent: Parent widget
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        # Styling
        self.error_color = "#FF4444"
        self.warning_color = "#FFA500"
        self.info_color = "#4A90E2"
        
        # Create error label
        self.error_label = ctk.CTkLabel(
            self,
            text="",
            font=("Consolas", 10),
            text_color=self.error_color,
            anchor="w"
        )
        self.error_label.pack(fill="x", padx=5, pady=2)
        
        # Initially hidden
        self.pack_forget()
    
    def show_error(self, message: str):
        """Show error message.
        
        Args:
            message: Error message to display
        """
        self.error_label.configure(
            text=f"❌ {message}",
            text_color=self.error_color
        )
        self.pack(fill="x", pady=(2, 5))
    
    def show_warning(self, message: str):
        """Show warning message.
        
        Args:
            message: Warning message to display
        """
        self.error_label.configure(
            text=f"⚠️ {message}",
            text_color=self.warning_color
        )
        self.pack(fill="x", pady=(2, 5))
    
    def show_info(self, message: str):
        """Show info message.
        
        Args:
            message: Info message to display
        """
        self.error_label.configure(
            text=f"ℹ️ {message}",
            text_color=self.info_color
        )
        self.pack(fill="x", pady=(2, 5))
    
    def hide(self):
        """Hide the error display."""
        self.pack_forget()
        self.error_label.configure(text="")