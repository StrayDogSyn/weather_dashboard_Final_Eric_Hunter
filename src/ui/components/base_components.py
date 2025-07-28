#!/usr/bin/env python3
"""
Base UI Components - Backward Compatibility Module

This module provides backward compatibility imports for glassmorphic UI components.
All components have been moved to the glass package for better organization.

For new code, import directly from the glass package:
    from src.ui.components.glass import GlassFrame, GlassButton
    
This module maintains backward compatibility for existing imports:
    from src.ui.components.glass import GlassFrame, GlassButton
"""

# Import all components from the new glass package for backward compatibility
from src.ui.components.glass import (
    # Core types
    ComponentSize,
    AnimationState,
    GlassEffect,
    
    # Components
    GlassFrame,
    GlassButton,
    GlassLabel,
    GlassEntry,
    GlassProgressBar,
    
    # Utilities
    create_glass_card,
    create_glass_toolbar,
    create_glass_dialog,
    create_glass_notification,
    GlassUtilities
)

# Re-export everything for backward compatibility
__all__ = [
    # Core types
    'ComponentSize',
    'AnimationState',
    'GlassEffect',
    
    # Components
    'GlassFrame',
    'GlassButton',
    'GlassLabel',
    'GlassEntry',
    'GlassProgressBar',
    
    # Utilities
    'create_glass_card',
    'create_glass_toolbar',
    'create_glass_dialog',
    'create_glass_notification',
    'GlassUtilities'
]


# Note: All component implementations have been moved to src.ui.components.glass
# This file now only provides backward compatibility imports


if __name__ == "__main__":
    # Test the glassmorphic components (imported from glass package)
    import tkinter as tk

    root = tk.Tk()
    root.title("Glassmorphic Components Test")
    root.geometry("800x600")

    # Create test components using imported classes
    frame = GlassFrame(root, size=ComponentSize.LARGE)
    frame.pack(pady=20, padx=20)

    label = GlassLabel(frame, text="Glassmorphic Label", text_style="heading")
    label.pack(pady=10)

    button = GlassButton(frame, text="Glass Button")
    button.pack(pady=5)

    entry = GlassEntry(frame, placeholder_text="Enter text...")
    entry.pack(pady=5)

    progress = GlassProgressBar(frame)
    progress.pack(pady=10)
    progress.set(0.7)

    root.mainloop()
