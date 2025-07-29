"""Loading Overlay Component

Displays loading states with animations and progress indicators.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional
import threading
import time

from ..theme import DataTerminalTheme


class LoadingSpinner(ctk.CTkFrame):
    """Animated loading spinner widget."""
    
    def __init__(self, parent, size: int = 40, **kwargs):
        """Initialize loading spinner."""
        super().__init__(parent, **kwargs)
        
        self.size = size
        self.angle = 0
        self.is_spinning = False
        self.animation_thread: Optional[threading.Thread] = None
        
        # Configure frame
        self.configure(
            width=size + 10,
            height=size + 10,
            fg_color="transparent"
        )
        
        # Create canvas for spinner
        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=DataTerminalTheme.BACKGROUND,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(expand=True, fill="both")
        
        # Draw initial spinner
        self._draw_spinner()
    
    def _draw_spinner(self) -> None:
        """Draw the spinner on canvas."""
        self.canvas.delete("all")
        
        center_x = self.size // 2
        center_y = self.size // 2
        radius = self.size // 3
        
        # Draw spinner arcs
        for i in range(8):
            start_angle = (self.angle + i * 45) % 360
            alpha = 1.0 - (i * 0.12)  # Fade effect
            
            # Calculate color with alpha
            color = self._get_color_with_alpha(DataTerminalTheme.PRIMARY, alpha)
            
            # Draw arc segment
            x1 = center_x - radius
            y1 = center_y - radius
            x2 = center_x + radius
            y2 = center_y + radius
            
            self.canvas.create_arc(
                x1, y1, x2, y2,
                start=start_angle,
                extent=30,
                outline=color,
                width=3,
                style="arc"
            )
    
    def _get_color_with_alpha(self, hex_color: str, alpha: float) -> str:
        """Get color with alpha transparency effect."""
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Apply alpha by blending with background
        bg_color = DataTerminalTheme.BACKGROUND.lstrip('#')
        bg_r, bg_g, bg_b = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Blend colors
        final_r = int(r * alpha + bg_r * (1 - alpha))
        final_g = int(g * alpha + bg_g * (1 - alpha))
        final_b = int(b * alpha + bg_b * (1 - alpha))
        
        return f"#{final_r:02x}{final_g:02x}{final_b:02x}"
    
    def start_spinning(self) -> None:
        """Start the spinner animation."""
        if self.is_spinning:
            return
        
        self.is_spinning = True
        self.animation_thread = threading.Thread(
            target=self._animate,
            daemon=True
        )
        self.animation_thread.start()
    
    def stop_spinning(self) -> None:
        """Stop the spinner animation."""
        self.is_spinning = False
    
    def _animate(self) -> None:
        """Animation loop for spinner."""
        while self.is_spinning:
            self.angle = (self.angle + 15) % 360
            
            # Update on main thread
            try:
                self.after(0, self._draw_spinner)
                time.sleep(0.05)  # ~20 FPS
            except tk.TclError:
                # Widget destroyed
                break


class LoadingOverlay(ctk.CTkToplevel):
    """Full-screen loading overlay with spinner and message."""
    
    def __init__(self, parent, **kwargs):
        """Initialize loading overlay."""
        super().__init__(parent, **kwargs)
        
        self.parent_window = parent
        self.is_visible = False
        
        # Configure window
        self.title("Loading...")
        self.configure(fg_color=DataTerminalTheme.BACKGROUND)
        
        # Make it modal and always on top
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)
        
        # Remove window decorations
        self.overrideredirect(True)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_widgets()
        self._setup_layout()
        
        # Initially hidden
        self.withdraw()
    
    def _create_widgets(self) -> None:
        """Create overlay widgets."""
        # Main container
        self.container = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        # Content frame
        self.content_frame = ctk.CTkFrame(
            self.container,
            **DataTerminalTheme.get_frame_style("highlight")
        )
        
        # Loading spinner
        self.spinner = LoadingSpinner(
            self.content_frame,
            size=60,
            fg_color="transparent"
        )
        
        # Loading message
        self.message_label = ctk.CTkLabel(
            self.content_frame,
            text="Loading...",
            **DataTerminalTheme.get_label_style("subtitle")
        )
        
        # Progress bar (optional)
        self.progress_bar = ctk.CTkProgressBar(
            self.content_frame,
            width=300,
            height=8,
            fg_color=DataTerminalTheme.ACCENT,
            progress_color=DataTerminalTheme.PRIMARY
        )
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            **DataTerminalTheme.get_label_style("caption")
        )
    
    def _setup_layout(self) -> None:
        """Arrange widgets."""
        # Main container (centered)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        # Content frame (centered)
        self.content_frame.place(
            relx=0.5, rely=0.5,
            anchor="center",
            width=400, height=250
        )
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Content layout
        self.spinner.grid(row=0, column=0, pady=(30, 20))
        self.message_label.grid(row=1, column=0, pady=(0, 15))
        self.progress_bar.grid(row=2, column=0, pady=(0, 10), padx=30, sticky="ew")
        self.status_label.grid(row=3, column=0, pady=(0, 30))
    
    def show(self, message: str = "Loading...", show_progress: bool = False) -> None:
        """Show the loading overlay."""
        if self.is_visible:
            return
        
        self.is_visible = True
        
        # Update message
        self.message_label.configure(text=message)
        
        # Show/hide progress bar
        if show_progress:
            self.progress_bar.grid()
            self.progress_bar.set(0)
        else:
            self.progress_bar.grid_remove()
        
        # Position overlay over parent
        self._position_over_parent()
        
        # Show window
        self.deiconify()
        self.lift()
        self.focus_set()
        
        # Start spinner animation
        self.spinner.start_spinning()
        
        # Update display
        self.update()
    
    def hide(self) -> None:
        """Hide the loading overlay."""
        if not self.is_visible:
            return
        
        self.is_visible = False
        
        # Stop spinner
        self.spinner.stop_spinning()
        
        # Hide window
        self.withdraw()
        
        # Release grab
        try:
            self.grab_release()
        except tk.TclError:
            pass
    
    def update_message(self, message: str) -> None:
        """Update loading message."""
        self.message_label.configure(text=message)
        self.update()
    
    def update_progress(self, progress: float, status: str = "") -> None:
        """Update progress bar and status."""
        if hasattr(self.progress_bar, 'set'):
            self.progress_bar.set(progress)
        
        if status:
            self.status_label.configure(text=status)
        
        self.update()
    
    def _position_over_parent(self) -> None:
        """Position overlay to cover parent window."""
        # Get parent window geometry
        self.parent_window.update_idletasks()
        
        parent_x = self.parent_window.winfo_x()
        parent_y = self.parent_window.winfo_y()
        parent_width = self.parent_window.winfo_width()
        parent_height = self.parent_window.winfo_height()
        
        # Set overlay geometry to match parent
        self.geometry(f"{parent_width}x{parent_height}+{parent_x}+{parent_y}")


class SimpleLoadingDialog(ctk.CTkToplevel):
    """Simple loading dialog for quick operations."""
    
    def __init__(self, parent, message: str = "Loading...", **kwargs):
        """Initialize simple loading dialog."""
        super().__init__(parent, **kwargs)
        
        # Configure window
        self.title("Loading")
        self.configure(fg_color=DataTerminalTheme.BACKGROUND)
        self.resizable(False, False)
        
        # Make it modal
        self.transient(parent)
        self.grab_set()
        
        # Create content
        self.main_frame = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("default")
        )
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Spinner
        self.spinner = LoadingSpinner(
            self.main_frame,
            size=40,
            fg_color="transparent"
        )
        self.spinner.pack(pady=(20, 10))
        
        # Message
        self.message_label = ctk.CTkLabel(
            self.main_frame,
            text=message,
            **DataTerminalTheme.get_label_style("default")
        )
        self.message_label.pack(pady=(0, 20))
        
        # Center on parent
        self._center_on_parent()
        
        # Start spinner
        self.spinner.start_spinning()
    
    def _center_on_parent(self) -> None:
        """Center dialog on parent window."""
        self.update_idletasks()
        
        # Get dialog size
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        
        # Get parent position and size
        parent = self.master
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def close(self) -> None:
        """Close the dialog."""
        self.spinner.stop_spinning()
        self.grab_release()
        self.destroy()