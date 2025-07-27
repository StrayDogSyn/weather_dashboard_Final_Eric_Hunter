import customtkinter as ctk
from typing import Optional, Callable, Dict, Any

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class HunterGlassButton(ctk.CTkButton):
    """CustomTkinter button with Hunter glassmorphic theme"""
    
    def __init__(self, parent, text: str = "", command: Optional[Callable] = None, **kwargs):
        # Hunter theme defaults for CustomTkinter
        hunter_defaults = {
            "fg_color": "#355E3B",              # Hunter green
            "hover_color": "#4A7C59",           # Lighter hunter green
            "text_color": "#C0C0C0",            # Hunter silver
            "corner_radius": 12,                # Glassmorphic corners
            "border_width": 2,
            "border_color": ("#C0C0C0", "#808080"),  # Silver with dark variant
            "font": ("Segoe UI", 12, "normal"),
            "height": 35,
            "width": 120
        }
        
        # Merge user parameters with defaults
        final_kwargs = {**hunter_defaults, **kwargs}
        
        # Initialize as CustomTkinter button
        super().__init__(parent, text=text, command=command, **final_kwargs)
        
        # Add glassmorphic hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event=None):
        """Enhanced hover with full opacity border"""
        self.configure(border_color="#C0C0C0", fg_color="#4A7C59")
    
    def _on_leave(self, event=None):
        """Return to semi-transparent state"""
        self.configure(border_color=("#C0C0C0", "#808080"), fg_color="#355E3B")
    
    def add_3d_effects(self):
        """Add enhanced 3D effects (placeholder for future enhancements)"""
        # This method can be extended for more complex 3D effects
        pass

class HunterGlassFrame(ctk.CTkFrame):
    """CustomTkinter frame with Hunter glassmorphic styling"""
    
    def __init__(self, parent, **kwargs):
        hunter_defaults = {
            "fg_color": ("#355E3B", "#2F4F2F"),  # Hunter green with dark variant
            "corner_radius": 16,
            "border_width": 1,
            "border_color": ("#C0C0C0", "#808080")  # Silver with dark variant
        }
        
        final_kwargs = {**hunter_defaults, **kwargs}
        super().__init__(parent, **final_kwargs)

# Alias for backward compatibility
class HunterGlassPanel(HunterGlassFrame):
    """Alias for HunterGlassFrame to maintain backward compatibility"""
    def __init__(self, parent, glass_opacity=0.3, **kwargs):
        # Ignore glass_opacity parameter for now, use default styling
        super().__init__(parent, **kwargs)
    
    def add_glass_effect(self):
        """Add enhanced glass effects (placeholder for future enhancements)"""
        # This method can be extended for more complex glass effects
        pass

class HunterGlassLabel(ctk.CTkLabel):
    """CustomTkinter label with Hunter theme"""
    
    def __init__(self, parent, text: str = "", **kwargs):
        hunter_defaults = {
            "text_color": "#C0C0C0",            # Hunter silver
            "font": ("Segoe UI", 12, "normal")
        }
        
        # Handle style variations
        style = kwargs.pop('style', 'primary')
        if style == 'secondary':
            hunter_defaults["text_color"] = ("#C0C0C0", "#999999")
        elif style == 'accent':
            hunter_defaults["text_color"] = "#355E3B"
        elif style == 'header':
            hunter_defaults["font"] = ("Segoe UI", 24, "bold")
        
        final_kwargs = {**hunter_defaults, **kwargs}
        super().__init__(parent, text=text, **final_kwargs)

class HunterGlassEntry(ctk.CTkEntry):
    """CustomTkinter entry with Hunter glassmorphic styling"""
    
    def __init__(self, parent, **kwargs):
        hunter_defaults = {
            "fg_color": ("#2F4F4F", "#1C1C1C"),  # Dark slate with darker variant
            "text_color": "#C0C0C0",
            "placeholder_text_color": ("#C0C0C0", "#808080"),
            "border_color": ("#C0C0C0", "#808080"),
            "corner_radius": 8,
            "border_width": 1,
            "font": ("Segoe UI", 12, "normal"),
            "height": 32
        }
        
        final_kwargs = {**hunter_defaults, **kwargs}
        super().__init__(parent, **final_kwargs)
        
        # Focus effects
        self.bind("<FocusIn>", lambda e: self.configure(border_color="#355E3B"))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=("#C0C0C0", "#808080")))

class HunterColors:
    """Hunter theme color constants with glassmorphic variants"""
    # Base Hunter colors
    BLACK = "#1C1C1C"
    DARK_SLATE = "#2F4F4F"
    GREEN = "#355E3B"
    SILVER = "#C0C0C0"
    
    # Glassmorphic variants
    GLASS_PRIMARY = "#355E3B40"
    GLASS_SECONDARY = "#2F4F4F60"
    GLASS_ACCENT = ("#C0C0C0", "#808080")
    GLASS_HOVER = "#4A7C59"
    
    # Backward compatibility
    HUNTER_BLACK = BLACK
    HUNTER_DARK_SLATE = DARK_SLATE
    HUNTER_GREEN = GREEN
    HUNTER_SILVER = SILVER
    GLASS_HUNTER_PRIMARY = DARK_SLATE
    GLASS_HUNTER_ACCENT = SILVER
    GLASS_HUNTER_HOVER = GREEN

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