"""Glassmorphic UI Components Package.

This package provides a comprehensive set of glassmorphic UI components
for the weather dashboard application. All components feature consistent
glassmorphic styling with transparency, blur effects, and modern aesthetics.

Components:
    GlassFrame: Base glassmorphic container component
    GlassButton: Interactive glassmorphic button with icon support
    GlassLabel: Glassmorphic text display component
    GlassEntry: Glassmorphic text input component
    GlassProgressBar: Glassmorphic progress indicator
    
Utilities:
    create_glass_card: Create standardized glass card layouts
    create_glass_toolbar: Create standardized glass toolbars
    create_glass_dialog: Create standardized glass dialogs
    create_glass_notification: Create standardized glass notifications
    GlassEffect: Core glassmorphic effect configuration
    ComponentSize: Standard component sizing enumeration
    AnimationState: Animation state management enumeration

Usage:
    from src.ui.components.glass import GlassFrame, GlassButton
    from src.ui.components.glass import create_glass_card
    
    # Create a glass frame
    frame = GlassFrame(parent)
    
    # Create a glass button
    button = GlassButton(parent, text="Click Me")
    
    # Create a glass card
    card = create_glass_card(parent, "Card Title")
"""

# Core types and effects
from .core_types import ComponentSize, AnimationState, GlassEffect

# Base components
from .glass_frame import GlassFrame
from .glass_button import GlassButton
from .glass_text import GlassLabel, GlassEntry
from .glass_progress import GlassProgressBar

# Utility functions
from .glass_utils import (
    create_glass_card,
    create_glass_toolbar,
    create_glass_dialog,
    create_glass_notification,
    GlassUtilities
)

# Public API
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

# Version info
__version__ = '1.0.0'
__author__ = 'Weather Dashboard Team'