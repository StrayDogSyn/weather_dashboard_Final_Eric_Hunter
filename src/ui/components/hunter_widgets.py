"""Hunter Theme 3D Glass Components

Implements glassmorphic UI widgets with Hunter theme styling,
including 3D buttons with multi-layer shadows and frosted glass panels.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Any
from ..themes.hunter_glass import HunterColors, HunterStyling, HunterAnimations

class HunterGlassButton(tk.Button):
    """3D glassmorphic button with Hunter theme styling"""
    
    def __init__(self, parent, text: str = "", command: Optional[Callable] = None, **kwargs):
        # Remove custom kwargs before passing to Button
        self.glass_style = kwargs.pop('glass_style', 'primary')
        self.elevation = kwargs.pop('elevation', HunterStyling.SHADOW_NORMAL)
        
        super().__init__(parent, text=text, command=command, **kwargs)
        
        self._setup_styling()
        self._bind_events()
        self._animation_id = None
    
    def _setup_styling(self):
        """Configure 3D glass button styling"""
        self.configure(
            relief='flat',
            borderwidth=0,
            font=('Segoe UI', 10, 'bold'),
            fg=HunterColors.HUNTER_SILVER,
            activeforeground=HunterColors.HUNTER_SILVER,
            cursor='hand2'
        )
        self._apply_raised_state()
    
    def _apply_raised_state(self):
        """Apply raised button appearance with gradient"""
        self.configure(
            bg=HunterColors.BUTTON_RAISED[1],  # Hunter green center
            activebackground=HunterColors.BUTTON_RAISED[0]  # Silver on hover
        )
        # Simulate 3D effect with relief and border
        self.configure(relief='raised', borderwidth=2)
    
    def _apply_pressed_state(self):
        """Apply pressed button appearance"""
        self.configure(
            bg=HunterColors.BUTTON_PRESSED[1],  # Darker green
            relief='sunken',
            borderwidth=1
        )
    
    def _bind_events(self):
        """Bind hover and click events for 3D effects"""
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)
    
    def _on_enter(self, event):
        """Handle mouse enter - elevate button"""
        self._animate_elevation(HunterStyling.SHADOW_HOVER)
        self.configure(bg=HunterColors.GLASS_HUNTER_HOVER.replace('80', 'AA'))  # More opaque on hover
    
    def _on_leave(self, event):
        """Handle mouse leave - return to normal"""
        self._animate_elevation(HunterStyling.SHADOW_NORMAL)
        self._apply_raised_state()
    
    def _on_press(self, event):
        """Handle button press"""
        self._apply_pressed_state()
        self.elevation = HunterStyling.SHADOW_PRESSED
    
    def _on_release(self, event):
        """Handle button release"""
        self._apply_raised_state()
        self.elevation = HunterStyling.SHADOW_NORMAL
    
    def _animate_elevation(self, target_elevation: int):
        """Animate shadow elevation change"""
        if self._animation_id:
            self.after_cancel(self._animation_id)
        
        start_elevation = self.elevation
        steps = 10
        step_size = (target_elevation - start_elevation) / steps
        
        def animate_step(step: int):
            if step <= steps:
                progress = step / steps
                eased_progress = HunterAnimations.ease_out_cubic(progress)
                current_elevation = start_elevation + (step_size * steps * eased_progress)
                self.elevation = current_elevation
                self._animation_id = self.after(15, lambda: animate_step(step + 1))
        
        animate_step(0)

class HunterGlassPanel(tk.Frame):
    """Frosted glass panel with Hunter theme styling"""
    
    def __init__(self, parent, glass_opacity: float = 0.35, blur_radius: int = 15, **kwargs):
        self.glass_opacity = glass_opacity
        self.blur_radius = blur_radius
        
        super().__init__(parent, **kwargs)
        self._setup_glass_styling()
    
    def _setup_glass_styling(self):
        """Configure frosted glass panel appearance"""
        self.configure(
            bg=HunterColors.GLASS_HUNTER_PRIMARY,
            relief='flat',
            borderwidth=HunterStyling.GLASS_BORDER,
            highlightbackground=HunterColors.HUNTER_SILVER,
            highlightcolor=HunterColors.HUNTER_SILVER,
            highlightthickness=1
        )
    
    def add_glass_effect(self):
        """Add visual glass effect overlay"""
        # Create a subtle inner shadow effect
        inner_frame = tk.Frame(
            self,
            bg=HunterColors.GLASS_HUNTER_ACCENT,
            height=2
        )
        inner_frame.pack(fill='x', side='top')
        
        # Add silver edge highlight
        highlight_frame = tk.Frame(
            self,
            bg=HunterColors.HUNTER_SILVER,
            height=1
        )
        highlight_frame.pack(fill='x', side='top')

class HunterGlassLabel(tk.Label):
    """Glass-styled label with Hunter theme"""
    
    def __init__(self, parent, text: str = "", style: str = 'primary', **kwargs):
        self.glass_style = style
        
        super().__init__(parent, text=text, **kwargs)
        self._setup_glass_label_styling()
    
    def _setup_glass_label_styling(self):
        """Configure glass label appearance"""
        if self.glass_style == 'primary':
            fg_color = HunterColors.HUNTER_SILVER
            bg_color = HunterColors.GLASS_HUNTER_PRIMARY
        elif self.glass_style == 'accent':
            fg_color = HunterColors.HUNTER_GREEN
            bg_color = HunterColors.GLASS_HUNTER_ACCENT
        else:
            fg_color = HunterColors.HUNTER_SILVER
            bg_color = HunterColors.HUNTER_DARK_SLATE
        
        self.configure(
            fg=fg_color,
            bg=bg_color,
            font=('Segoe UI', 9),
            relief='flat',
            borderwidth=0
        )

class HunterGlassEntry(tk.Entry):
    """Glass-styled entry widget with Hunter theme"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._setup_glass_entry_styling()
        self._bind_focus_events()
    
    def _setup_glass_entry_styling(self):
        """Configure glass entry appearance"""
        self.configure(
            bg=HunterColors.GLASS_HUNTER_PRIMARY,
            fg=HunterColors.HUNTER_SILVER,
            insertbackground=HunterColors.HUNTER_SILVER,
            selectbackground=HunterColors.HUNTER_GREEN,
            selectforeground=HunterColors.HUNTER_SILVER,
            relief='flat',
            borderwidth=2,
            highlightbackground=HunterColors.HUNTER_DARK_SLATE,
            highlightcolor=HunterColors.HUNTER_GREEN,
            highlightthickness=1,
            font=('Segoe UI', 9)
        )
    
    def _bind_focus_events(self):
        """Bind focus events for interactive styling"""
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)
    
    def _on_focus_in(self, event):
        """Handle focus in - highlight border"""
        self.configure(
            highlightbackground=HunterColors.HUNTER_GREEN,
            bg=HunterColors.GLASS_HUNTER_HOVER
        )
    
    def _on_focus_out(self, event):
        """Handle focus out - return to normal"""
        self.configure(
            highlightbackground=HunterColors.HUNTER_DARK_SLATE,
            bg=HunterColors.GLASS_HUNTER_PRIMARY
        )

# Hunter3D Classes - Enhanced 3D versions
class Hunter3DButton(HunterGlassButton):
    """Enhanced 3D button with deeper shadows and effects"""
    
    def __init__(self, parent, text: str = "", command: Optional[Callable] = None, **kwargs):
        super().__init__(parent, text=text, command=command, **kwargs)
        self._enhance_3d_effects()
    
    def _enhance_3d_effects(self):
        """Apply enhanced 3D styling"""
        self.configure(
            relief='raised',
            borderwidth=3,  # Thicker border for more depth
            bg=HunterColors.BUTTON_RAISED[0],  # Silver base
            activebackground=HunterColors.BUTTON_RAISED[1]  # Green on hover
        )

class Hunter3DEntry(HunterGlassEntry):
    """Enhanced 3D entry with sunken appearance"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._enhance_3d_effects()
    
    def _enhance_3d_effects(self):
        """Apply enhanced 3D styling"""
        self.configure(
            relief='sunken',
            borderwidth=3,  # Deeper sunken effect
            highlightthickness=2
        )

class Hunter3DFrame(HunterGlassPanel):
    """Enhanced 3D frame with groove styling"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._enhance_3d_effects()
    
    def _enhance_3d_effects(self):
        """Apply enhanced 3D styling"""
        self.configure(
            relief='groove',
            borderwidth=4,  # Deeper groove effect
            bg=HunterColors.GLASS_HUNTER_PRIMARY
        )