import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Dict, Any

class HunterGlassButton(tk.Button):
    """3D Glass button with Hunter theme styling and elevation effects"""
    
    def __init__(self, parent, text="", command=None, width=120, height=40, **kwargs):
        # Initialize with Hunter theme colors
        super().__init__(
            parent,
            text=text,
            command=command,
            width=width//8,  # Tkinter uses character width
            height=height//20,  # Tkinter uses character height
            bg=HunterColors.HUNTER_SILVER,
            fg=HunterColors.HUNTER_BLACK,
            font=('Segoe UI', 10, 'bold'),
            relief='raised',
            bd=2,
            cursor='hand2',
            **kwargs
        )
        
        self.default_bg = HunterColors.HUNTER_SILVER
        self.hover_bg = HunterColors.HUNTER_GREEN
        self.pressed_bg = HunterColors.HUNTER_DARK_SLATE
        
        self._setup_3d_effects()
    
    def _setup_3d_effects(self):
        """Setup 3D visual effects and hover animations"""
        # Bind hover events
        self.bind('<Enter>', self._on_hover_enter)
        self.bind('<Leave>', self._on_hover_leave)
        self.bind('<Button-1>', self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)
    
    def _on_hover_enter(self, event):
        """Handle mouse enter - elevation effect"""
        self.configure(
            bg=self.hover_bg,
            fg=HunterColors.HUNTER_SILVER,
            relief='raised',
            bd=3
        )
    
    def _on_hover_leave(self, event):
        """Handle mouse leave - return to normal"""
        self.configure(
            bg=self.default_bg,
            fg=HunterColors.HUNTER_BLACK,
            relief='raised',
            bd=2
        )
    
    def _on_press(self, event):
        """Handle button press - pressed state"""
        self.configure(
            bg=self.pressed_bg,
            fg=HunterColors.HUNTER_SILVER,
            relief='sunken',
            bd=1
        )
    
    def _on_release(self, event):
        """Handle button release - return to hover state"""
        self.configure(
            bg=self.hover_bg,
            fg=HunterColors.HUNTER_SILVER,
            relief='raised',
            bd=3
        )
    
    def add_3d_effects(self):
        """Add enhanced 3D effects (placeholder for future enhancements)"""
        # This method can be extended for more complex 3D effects
        pass

class HunterGlassPanel(tk.Frame):
    """Glassmorphic panel with frosted blur effects and Hunter theme"""
    
    def __init__(self, parent, glass_opacity=0.3, **kwargs):
        # Calculate glass color with opacity
        glass_color = HunterColors.GLASS_HUNTER_PRIMARY
        
        super().__init__(
            parent,
            bg=glass_color,
            relief='flat',
            bd=1,
            highlightbackground=HunterColors.HUNTER_SILVER,
            highlightthickness=1,
            **kwargs
        )
        
        self.glass_opacity = glass_opacity
        self._setup_glass_effects()
    
    def _setup_glass_effects(self):
        """Setup glassmorphic visual effects"""
        # Add subtle border for glass effect
        self.configure(
            relief='ridge',
            bd=2,
            highlightbackground=HunterColors.HUNTER_SILVER,
            highlightcolor=HunterColors.HUNTER_GREEN
        )
    
    def add_glass_effect(self):
        """Add enhanced glass effects (placeholder for future enhancements)"""
        # This method can be extended for more complex glass effects
        pass

class HunterGlassLabel(tk.Label):
    """Glass-styled label with Hunter theme"""
    
    def __init__(self, parent, text="", style='primary', **kwargs):
        # Set colors based on style
        if style == 'primary':
            fg_color = HunterColors.HUNTER_SILVER
        elif style == 'accent':
            fg_color = HunterColors.HUNTER_GREEN
        elif style == 'secondary':
            fg_color = HunterColors.HUNTER_DARK_SLATE
        else:
            fg_color = HunterColors.HUNTER_SILVER
        
        # Get parent background color safely
        try:
            parent_bg = parent.cget('bg')
        except:
            parent_bg = HunterColors.HUNTER_BLACK
        
        # Set default font if not provided
        if 'font' not in kwargs:
            kwargs['font'] = ('Segoe UI', 11)
        
        super().__init__(
            parent,
            text=text,
            fg=fg_color,
            bg=parent_bg,
            **kwargs
        )

class HunterGlassEntry(tk.Entry):
    """Glass-styled entry widget with Hunter theme"""
    
    def __init__(self, parent, placeholder="", width=20, **kwargs):
        super().__init__(
            parent,
            width=width,
            bg=HunterColors.GLASS_HUNTER_ACCENT,
            fg=HunterColors.HUNTER_BLACK,
            font=('Segoe UI', 10),
            relief='ridge',
            bd=2,
            highlightbackground=HunterColors.HUNTER_SILVER,
            highlightcolor=HunterColors.HUNTER_GREEN,
            insertbackground=HunterColors.HUNTER_GREEN,
            **kwargs
        )
        
        self.placeholder = placeholder
        self._setup_placeholder()
        self._setup_glass_effects()
    
    def _setup_placeholder(self):
        """Setup placeholder text functionality"""
        if self.placeholder:
            self.insert(0, self.placeholder)
            self.configure(fg='gray')
            
            self.bind('<FocusIn>', self._on_focus_in)
            self.bind('<FocusOut>', self._on_focus_out)
    
    def _on_focus_in(self, event):
        """Handle focus in - remove placeholder"""
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.configure(fg=HunterColors.HUNTER_BLACK)
    
    def _on_focus_out(self, event):
        """Handle focus out - restore placeholder if empty"""
        if not self.get():
            self.insert(0, self.placeholder)
            self.configure(fg='gray')
    
    def _setup_glass_effects(self):
        """Setup glass visual effects"""
        self.bind('<Enter>', self._on_hover_enter)
        self.bind('<Leave>', self._on_hover_leave)
    
    def _on_hover_enter(self, event):
        """Handle mouse enter - highlight effect"""
        self.configure(
            highlightbackground=HunterColors.HUNTER_GREEN,
            highlightthickness=2
        )
    
    def _on_hover_leave(self, event):
        """Handle mouse leave - return to normal"""
        self.configure(
            highlightbackground=HunterColors.HUNTER_SILVER,
            highlightthickness=1
        )
    
    def get(self):
        """Get entry value, excluding placeholder"""
        value = super().get()
        return "" if value == self.placeholder else value

class HunterColors:
    """Hunter theme color constants for backward compatibility"""
    HUNTER_BLACK = "#1C1C1C"
    HUNTER_DARK_SLATE = "#2F4F4F"
    HUNTER_GREEN = "#355E3B"
    HUNTER_SILVER = "#C0C0C0"
    GLASS_HUNTER_PRIMARY = "#2F4F4F"
    GLASS_HUNTER_ACCENT = "#C0C0C0"
    GLASS_HUNTER_HOVER = "#355E3B"

class AnimationManager:
    """Simple animation manager for smooth transitions"""
    
    def __init__(self, widget=None):
        self.widget = widget
        self.animations = {}
    
    def animate_color(self, from_color: str, to_color: str, duration: int = 300):
        """Animate color transition (placeholder implementation)"""
        # Simple immediate color change for now
        if self.widget:
            self.widget.configure(bg=to_color)
    
    def animate_elevation(self, from_elevation: int, to_elevation: int, duration: int = 200):
        """Animate elevation change (placeholder implementation)"""
        # Simple immediate elevation change for now
        if self.widget and hasattr(self.widget, 'configure'):
            bd = max(1, to_elevation // 2)
            self.widget.configure(bd=bd)