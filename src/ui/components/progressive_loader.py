"""Progressive Loading UI Component.

Provides visual feedback during async loading operations with
skeleton screens, progress indicators, and smooth transitions.
"""

import tkinter as tk
from typing import Dict, Any, Callable, Optional
import logging
from dataclasses import dataclass
from enum import Enum

try:
    import customtkinter as ctk
except ImportError:
    ctk = None


class LoadingState(Enum):
    """Loading states for UI feedback."""
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class LoadingStep:
    """Represents a loading step with UI information."""
    name: str
    display_text: str
    icon: str = "⏳"
    estimated_duration: float = 1.0


class ProgressiveLoader:
    """Progressive loading UI with skeleton screens and progress feedback."""
    
    def __init__(self, parent, width: int = 400, height: int = 300):
        """Initialize the progressive loader.
        
        Args:
            parent: Parent widget
            width: Loader width
            height: Loader height
        """
        self.logger = logging.getLogger(__name__)
        self.parent = parent
        self.width = width
        self.height = height
        
        # State management
        self.state = LoadingState.IDLE
        self.current_step = 0
        self.total_steps = 0
        self.progress = 0.0
        
        # Callbacks
        self.on_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_cancel: Optional[Callable] = None
        
        # UI components
        self.main_frame = None
        self.progress_bar = None
        self.status_label = None
        self.step_label = None
        self.cancel_button = None
        self.skeleton_frame = None
        
        # Loading steps
        self.steps: Dict[str, LoadingStep] = {}
        self.step_order: list = []
        
        # Animation
        self.animation_id = None
        self.pulse_alpha = 0.5
        self.pulse_direction = 1
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the progressive loader UI."""
        # Main container
        if ctk:
            self.main_frame = ctk.CTkFrame(
                self.parent,
                width=self.width,
                height=self.height,
                corner_radius=15
            )
        else:
            self.main_frame = tk.Frame(
                self.parent,
                width=self.width,
                height=self.height,
                bg='#2d2d2d',
                relief='raised',
                bd=2
            )
        
        self.main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        self.main_frame.pack_propagate(False)
        
        # Header
        self._create_header()
        
        # Progress section
        self._create_progress_section()
        
        # Skeleton content area
        self._create_skeleton_area()
        
        # Controls
        self._create_controls()
    
    def _create_header(self):
        """Create the header section."""
        if ctk:
            header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        else:
            header_frame = tk.Frame(self.main_frame, bg='#2d2d2d')
        
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        # Title
        if ctk:
            title_label = ctk.CTkLabel(
                header_frame,
                text="⚡ PROJECT CODEFRONT",
                font=ctk.CTkFont(size=18, weight="bold")
            )
        else:
            title_label = tk.Label(
                header_frame,
                text="⚡ PROJECT CODEFRONT",
                font=("Arial", 18, "bold"),
                fg='#ffffff',
                bg='#2d2d2d'
            )
        
        title_label.pack()
        
        # Subtitle
        if ctk:
            subtitle_label = ctk.CTkLabel(
                header_frame,
                text="Advanced Weather Intelligence System v3.5",
                font=ctk.CTkFont(size=12)
            )
        else:
            subtitle_label = tk.Label(
                header_frame,
                text="Advanced Weather Intelligence System v3.5",
                font=("Arial", 12),
                fg='#cccccc',
                bg='#2d2d2d'
            )
        
        subtitle_label.pack(pady=(0, 5))
        
        # Capstone info
        if ctk:
            capstone_label = ctk.CTkLabel(
                header_frame,
                text="Justice Through Code - Tech Pathways Capstone",
                font=ctk.CTkFont(size=10)
            )
        else:
            capstone_label = tk.Label(
                header_frame,
                text="Justice Through Code - Tech Pathways Capstone",
                font=("Arial", 10),
                fg='#999999',
                bg='#2d2d2d'
            )
        
        capstone_label.pack()
    
    def _create_progress_section(self):
        """Create the progress indicator section."""
        if ctk:
            progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        else:
            progress_frame = tk.Frame(self.main_frame, bg='#2d2d2d')
        
        progress_frame.pack(fill='x', padx=20, pady=10)
        
        # Current step label
        if ctk:
            self.step_label = ctk.CTkLabel(
                progress_frame,
                text="Initializing...",
                font=ctk.CTkFont(size=14)
            )
        else:
            self.step_label = tk.Label(
                progress_frame,
                text="Initializing...",
                font=("Arial", 14),
                fg='#cccccc',
                bg='#2d2d2d'
            )
        
        self.step_label.pack(pady=(0, 5))
        
        # Progress bar
        if ctk:
            self.progress_bar = ctk.CTkProgressBar(
                progress_frame,
                width=self.width - 80,
                height=8
            )
            self.progress_bar.set(0)
        else:
            # Create custom progress bar for tkinter
            progress_bg = tk.Frame(
                progress_frame,
                height=8,
                bg='#404040',
                relief='sunken',
                bd=1
            )
            progress_bg.pack(fill='x', pady=5)
            
            self.progress_bar = tk.Frame(
                progress_bg,
                height=6,
                bg='#4CAF50'
            )
            self.progress_bar.place(x=1, y=1, width=0)
        
        if ctk:
            self.progress_bar.pack(pady=5)
        
        # Status label
        if ctk:
            self.status_label = ctk.CTkLabel(
                progress_frame,
                text="0% complete",
                font=ctk.CTkFont(size=12),
                text_color='#888888'
            )
        else:
            self.status_label = tk.Label(
                progress_frame,
                text="0% complete",
                font=("Arial", 12),
                fg='#888888',
                bg='#2d2d2d'
            )
        
        self.status_label.pack()
    
    def _create_skeleton_area(self):
        """Create the skeleton content area."""
        if ctk:
            self.skeleton_frame = ctk.CTkFrame(
                self.main_frame,
                corner_radius=10
            )
        else:
            self.skeleton_frame = tk.Frame(
                self.main_frame,
                bg='#3d3d3d',
                relief='sunken',
                bd=1
            )
        
        self.skeleton_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create skeleton elements
        self._create_skeleton_elements()
    
    def _create_skeleton_elements(self):
        """Create skeleton loading elements."""
        # Weather card skeleton
        if ctk:
            card_frame = ctk.CTkFrame(
                self.skeleton_frame,
                height=120,
                corner_radius=8
            )
        else:
            card_frame = tk.Frame(
                self.skeleton_frame,
                height=120,
                bg='#4d4d4d',
                relief='raised',
                bd=1
            )
        
        card_frame.pack(fill='x', padx=10, pady=10)
        card_frame.pack_propagate(False)
        
        # Skeleton text lines
        for i, width in enumerate([0.7, 0.5, 0.8, 0.6]):
            if ctk:
                skeleton_line = ctk.CTkFrame(
                    card_frame,
                    height=12,
                    corner_radius=6,
                    fg_color='#5d5d5d'
                )
            else:
                skeleton_line = tk.Frame(
                    card_frame,
                    height=12,
                    bg='#5d5d5d'
                )
            
            skeleton_line.pack(
                fill='x',
                padx=(10, int((1-width) * 200)),
                pady=5
            )
            skeleton_line.pack_propagate(False)
        
        # Start skeleton animation
        self._animate_skeleton()
    
    def _create_controls(self):
        """Create control buttons."""
        if ctk:
            controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        else:
            controls_frame = tk.Frame(self.main_frame, bg='#2d2d2d')
        
        controls_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Cancel button
        if ctk:
            self.cancel_button = ctk.CTkButton(
                controls_frame,
                text="Cancel",
                width=100,
                height=32,
                command=self._on_cancel_clicked
            )
        else:
            self.cancel_button = tk.Button(
                controls_frame,
                text="Cancel",
                width=12,
                command=self._on_cancel_clicked,
                bg='#ff4444',
                fg='white',
                relief='flat'
            )
        
        self.cancel_button.pack(side='right')
    
    def add_step(self, name: str, display_text: str, icon: str = "⏳", estimated_duration: float = 1.0):
        """Add a loading step.
        
        Args:
            name: Step identifier
            display_text: Text to display during this step
            icon: Icon to show
            estimated_duration: Estimated duration in seconds
        """
        step = LoadingStep(name, display_text, icon, estimated_duration)
        self.steps[name] = step
        self.step_order.append(name)
        self.total_steps = len(self.step_order)
    
    def start_loading(self):
        """Start the loading process."""
        self.state = LoadingState.LOADING
        self.current_step = 0
        self.progress = 0.0
        self._update_ui()
        
        self.logger.info("Progressive loading started")
    
    def update_step(self, step_name: str, progress: float = None):
        """Update the current loading step.
        
        Args:
            step_name: Name of the current step
            progress: Optional progress within the step (0.0 to 1.0)
        """
        if step_name in self.steps:
            try:
                step_index = self.step_order.index(step_name)
                self.current_step = step_index
                
                if progress is not None:
                    # Calculate overall progress
                    base_progress = step_index / self.total_steps if self.total_steps > 0 else 0
                    step_progress = progress / self.total_steps if self.total_steps > 0 else 0
                    self.progress = base_progress + step_progress
                else:
                    self.progress = (step_index + 1) / self.total_steps if self.total_steps > 0 else 1.0
                
                self._update_ui()
                
            except ValueError:
                self.logger.warning(f"Unknown step: {step_name}")
    
    def complete_loading(self, success: bool = True, message: str = None):
        """Complete the loading process.
        
        Args:
            success: Whether loading was successful
            message: Optional completion message
        """
        if success:
            self.state = LoadingState.SUCCESS
            self.progress = 1.0
            if message:
                self._update_status(message)
            else:
                self._update_status("Loading complete!")
            
            if self.on_complete:
                self.on_complete()
        else:
            self.state = LoadingState.ERROR
            if message:
                self._update_status(f"Error: {message}")
            else:
                self._update_status("Loading failed")
            
            if self.on_error:
                self.on_error(message)
        
        self._update_ui()
        self.logger.info(f"Loading completed: {success}")
    
    def _update_ui(self):
        """Update the UI based on current state."""
        # Update progress bar
        if ctk and self.progress_bar:
            self.progress_bar.set(self.progress)
        elif self.progress_bar and not ctk:
            # Update custom progress bar
            parent_width = self.progress_bar.master.winfo_width()
            if parent_width > 1:
                progress_width = max(0, int((parent_width - 2) * self.progress))
                self.progress_bar.place(width=progress_width)
        
        # Update step label
        if self.step_label and self.current_step < len(self.step_order):
            step_name = self.step_order[self.current_step]
            step = self.steps[step_name]
            
            if ctk:
                self.step_label.configure(text=f"{step.icon} {step.display_text}")
            else:
                self.step_label.config(text=f"{step.icon} {step.display_text}")
        
        # Update status
        percentage = int(self.progress * 100)
        self._update_status(f"{percentage}% complete")
        
        # Update cancel button state
        if self.cancel_button:
            if self.state in [LoadingState.SUCCESS, LoadingState.ERROR, LoadingState.CANCELLED]:
                if ctk:
                    self.cancel_button.configure(text="Close", state="normal")
                else:
                    self.cancel_button.config(text="Close", state="normal")
            else:
                if ctk:
                    self.cancel_button.configure(text="Cancel", state="normal")
                else:
                    self.cancel_button.config(text="Cancel", state="normal")
    
    def _update_status(self, text: str):
        """Update the status label.
        
        Args:
            text: Status text to display
        """
        if self.status_label:
            if ctk:
                self.status_label.configure(text=text)
            else:
                self.status_label.config(text=text)
    
    def _animate_skeleton(self):
        """Animate skeleton loading elements."""
        if self.state != LoadingState.LOADING:
            return
        
        # Update pulse alpha
        self.pulse_alpha += 0.02 * self.pulse_direction
        if self.pulse_alpha >= 0.8:
            self.pulse_direction = -1
        elif self.pulse_alpha <= 0.3:
            self.pulse_direction = 1
        
        # Schedule next animation frame
        if self.main_frame and self.main_frame.winfo_exists():
            self.animation_id = self.main_frame.after(50, self._animate_skeleton)
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        if self.state in [LoadingState.SUCCESS, LoadingState.ERROR, LoadingState.CANCELLED]:
            # Close button functionality
            if self.on_cancel:
                self.on_cancel()
        else:
            # Cancel loading
            self.state = LoadingState.CANCELLED
            self._update_status("Cancelled")
            self._update_ui()
            
            if self.on_cancel:
                self.on_cancel()
            
            self.logger.info("Loading cancelled by user")
    
    def hide(self):
        """Hide the loader."""
        if self.main_frame:
            self.main_frame.pack_forget()
    
    def show(self):
        """Show the loader."""
        if self.main_frame:
            self.main_frame.pack(expand=True, fill='both', padx=20, pady=20)
    
    def destroy(self):
        """Destroy the loader and clean up resources."""
        if self.animation_id:
            self.main_frame.after_cancel(self.animation_id)
            self.animation_id = None
        
        if self.main_frame:
            self.main_frame.destroy()
            self.main_frame = None
        
        self.logger.info("Progressive loader destroyed")