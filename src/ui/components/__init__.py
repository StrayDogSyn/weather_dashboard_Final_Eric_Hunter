"""UI Components Package

This package contains all custom UI components for the Weather Dashboard.
"""

# Import all hunter glass components
from .hunter_glass import (
    HunterGlassButton,
    HunterGlassFrame,
    HunterGlassPanel,
    HunterGlassLabel,
    HunterGlassEntry,
    HunterColors,
    AnimationManager
)

# Import hunter widgets if they exist
try:
    from .hunter_widgets import (
        Hunter3DButton,
        Hunter3DEntry,
        Hunter3DFrame
    )
except ImportError:
    # Hunter widgets not available, define placeholders
    Hunter3DButton = HunterGlassButton
    Hunter3DEntry = HunterGlassEntry
    Hunter3DFrame = HunterGlassFrame

# Import glass components if they exist
try:
    from .glass import (
        GlassFrame,
        GlassButton,
        GlassLabel,
        GlassEntry
    )
except ImportError:
    # Glass components not available, use hunter glass as fallback
    GlassFrame = HunterGlassFrame
    GlassButton = HunterGlassButton
    GlassLabel = HunterGlassLabel
    GlassEntry = HunterGlassEntry

# Export all components
__all__ = [
    'HunterGlassButton',
    'HunterGlassFrame', 
    'HunterGlassPanel',
    'HunterGlassLabel',
    'HunterGlassEntry',
    'HunterColors',
    'AnimationManager',
    'Hunter3DButton',
    'Hunter3DEntry', 
    'Hunter3DFrame',
    'GlassFrame',
    'GlassButton',
    'GlassLabel',
    'GlassEntry'
]