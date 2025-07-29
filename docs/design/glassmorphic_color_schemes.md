# Glassmorphic Color Schemes for Weather Dashboard

This document provides comprehensive color schemes for implementing glassmorphic design in the weather dashboard GUI, featuring blurred/frosted backgrounds with black, hunter green, and silver accents.

## Core Glassmorphic Principles

### Visual Characteristics

- **Transparency**: 10-30% opacity for glass elements
- **Blur Effects**: 10-20px backdrop blur for frosted glass appearance
- **Subtle Borders**: 1-2px borders with low opacity
- **Layered Depth**: Multiple glass layers with varying transparency
- **Soft Shadows**: Subtle drop shadows for depth perception

## Primary Color Schemes

### Scheme 1: "Midnight Forest" (Recommended)

```python
class MidnightForestGlass:
    # Background layers
    PRIMARY_BG = "#0a0a0a"           # Deep black base
    GLASS_BG = "rgba(20, 40, 30, 0.15)"  # Hunter green tinted glass
    OVERLAY_BG = "rgba(0, 0, 0, 0.25)"   # Black overlay
    
    # Glass element backgrounds
    CARD_GLASS = "rgba(45, 85, 65, 0.12)"     # Hunter green glass cards
    PANEL_GLASS = "rgba(192, 192, 192, 0.08)" # Silver tinted panels
    MODAL_GLASS = "rgba(20, 40, 30, 0.20)"    # Darker green for modals
    
    # Accent colors
    HUNTER_GREEN = "#355E3B"         # Primary hunter green
    HUNTER_GREEN_LIGHT = "#4A7C59"   # Lighter hunter green
    HUNTER_GREEN_DARK = "#2C4A32"    # Darker hunter green
    
    SILVER = "#C0C0C0"              # Primary silver
    SILVER_LIGHT = "#E5E5E5"         # Light silver
    SILVER_DARK = "#A0A0A0"          # Dark silver
    
    # Border and outline colors
    GLASS_BORDER = "rgba(192, 192, 192, 0.15)"  # Silver glass borders
    ACCENT_BORDER = "rgba(53, 94, 59, 0.30)"    # Hunter green borders
    FOCUS_BORDER = "rgba(192, 192, 192, 0.40)"  # Silver focus borders
    
    # Text colors
    TEXT_PRIMARY = "#E5E5E5"         # Light silver text
    TEXT_SECONDARY = "#A0A0A0"       # Medium silver text
    TEXT_ACCENT = "#4A7C59"          # Hunter green accent text
    TEXT_MUTED = "rgba(192, 192, 192, 0.60)"  # Muted silver text
    
    # Interactive states
    HOVER_OVERLAY = "rgba(53, 94, 59, 0.10)"   # Hunter green hover
    ACTIVE_OVERLAY = "rgba(192, 192, 192, 0.15)" # Silver active state
    DISABLED_OVERLAY = "rgba(0, 0, 0, 0.30)"    # Black disabled state
```

### Scheme 2: "Silver Mist"

```python
class SilverMistGlass:
    # Background layers
    PRIMARY_BG = "#0f0f0f"           # Charcoal black base
    GLASS_BG = "rgba(192, 192, 192, 0.08)"  # Silver tinted glass
    OVERLAY_BG = "rgba(0, 0, 0, 0.20)"      # Light black overlay
    
    # Glass element backgrounds
    CARD_GLASS = "rgba(192, 192, 192, 0.10)"     # Silver glass cards
    PANEL_GLASS = "rgba(53, 94, 59, 0.08)"       # Hunter green panels
    MODAL_GLASS = "rgba(192, 192, 192, 0.15)"    # Brighter silver modals
    
    # Accent colors (same as Scheme 1)
    HUNTER_GREEN = "#355E3B"
    HUNTER_GREEN_LIGHT = "#4A7C59"
    HUNTER_GREEN_DARK = "#2C4A32"
    
    SILVER = "#C0C0C0"
    SILVER_LIGHT = "#E5E5E5"
    SILVER_DARK = "#A0A0A0"
    
    # Border and outline colors
    GLASS_BORDER = "rgba(53, 94, 59, 0.20)"     # Hunter green borders
    ACCENT_BORDER = "rgba(192, 192, 192, 0.25)" # Silver accent borders
    FOCUS_BORDER = "rgba(53, 94, 59, 0.40)"     # Hunter green focus
```

### Scheme 3: "Forest Shadow"

```python
class ForestShadowGlass:
    # Background layers
    PRIMARY_BG = "#000000"           # Pure black base
    GLASS_BG = "rgba(53, 94, 59, 0.12)"     # Hunter green glass
    OVERLAY_BG = "rgba(20, 20, 20, 0.30)"   # Dark overlay
    
    # Glass element backgrounds
    CARD_GLASS = "rgba(0, 0, 0, 0.25)"          # Black glass cards
    PANEL_GLASS = "rgba(53, 94, 59, 0.15)"      # Hunter green panels
    MODAL_GLASS = "rgba(192, 192, 192, 0.10)"   # Silver modals
    
    # Enhanced contrast for readability
    TEXT_PRIMARY = "#F0F0F0"         # Brighter silver text
    TEXT_SECONDARY = "#B0B0B0"       # Medium silver text
    TEXT_ACCENT = "#5A9B6A"          # Brighter hunter green
```

## CSS Implementation Examples

### Basic Glass Card Component

```css
.glass-card {
    background: rgba(45, 85, 65, 0.12);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid rgba(192, 192, 192, 0.15);
    border-radius: 12px;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}

.glass-card:hover {
    background: rgba(45, 85, 65, 0.18);
    border-color: rgba(192, 192, 192, 0.25);
    transform: translateY(-2px);
    box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.15);
}
```

### Weather Panel Glass Effect

```css
.weather-panel {
    background: linear-gradient(
        135deg,
        rgba(53, 94, 59, 0.15) 0%,
        rgba(192, 192, 192, 0.08) 100%
    );
    backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    position: relative;
    overflow: hidden;
}

.weather-panel::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(192, 192, 192, 0.3),
        transparent
    );
}
```

## Tkinter Implementation

### Enhanced GlassmorphicStyle Class

```python
class EnhancedGlassmorphicStyle:
    """Enhanced glassmorphic styling with multiple color schemes."""
    
    # Scheme selection
    CURRENT_SCHEME = "midnight_forest"  # Options: midnight_forest, silver_mist, forest_shadow
    
    # Midnight Forest Scheme
    MIDNIGHT_FOREST = {
        'background': '#0a0a0a',
        'glass_bg': '#1a2820',  # Approximated RGBA for Tkinter
        'card_bg': '#2d5541',   # Approximated glass card
        'panel_bg': '#1a1a1a',  # Approximated panel
        'text_primary': '#E5E5E5',
        'text_secondary': '#A0A0A0',
        'text_accent': '#4A7C59',
        'hunter_green': '#355E3B',
        'hunter_green_light': '#4A7C59',
        'silver': '#C0C0C0',
        'silver_light': '#E5E5E5',
        'border_color': '#404040',
        'hover_color': '#2C4A32',
        'active_color': '#4A7C59'
    }
    
    # Silver Mist Scheme
    SILVER_MIST = {
        'background': '#0f0f0f',
        'glass_bg': '#1f1f1f',
        'card_bg': '#2a2a2a',
        'panel_bg': '#1a2820',
        'text_primary': '#E5E5E5',
        'text_secondary': '#A0A0A0',
        'text_accent': '#355E3B',
        'hunter_green': '#355E3B',
        'hunter_green_light': '#4A7C59',
        'silver': '#C0C0C0',
        'silver_light': '#E5E5E5',
        'border_color': '#505050',
        'hover_color': '#C0C0C0',
        'active_color': '#E5E5E5'
    }
    
    @classmethod
    def get_current_colors(cls):
        """Get colors for the currently selected scheme."""
        schemes = {
            'midnight_forest': cls.MIDNIGHT_FOREST,
            'silver_mist': cls.SILVER_MIST
        }
        return schemes.get(cls.CURRENT_SCHEME, cls.MIDNIGHT_FOREST)
    
    @classmethod
    def create_glass_frame_style(cls):
        """Create style configuration for glass frames."""
        colors = cls.get_current_colors()
        return {
            'bg': colors['glass_bg'],
            'highlightbackground': colors['border_color'],
            'highlightthickness': 1,
            'relief': 'flat',
            'bd': 0
        }
    
    @classmethod
    def create_glass_button_style(cls):
        """Create style configuration for glass buttons."""
        colors = cls.get_current_colors()
        return {
            'bg': colors['card_bg'],
            'fg': colors['text_primary'],
            'activebackground': colors['hover_color'],
            'activeforeground': colors['text_primary'],
            'relief': 'flat',
            'bd': 1,
            'highlightbackground': colors['border_color'],
            'font': ('Segoe UI', 10),
            'cursor': 'hand2'
        }
```

## Weather-Specific Color Applications

### Temperature Display

```python
class WeatherGlassColors:
    """Weather-specific glassmorphic color mappings."""
    
    TEMPERATURE_COLORS = {
        'hot': {
            'glass': 'rgba(255, 100, 100, 0.15)',
            'border': 'rgba(255, 150, 150, 0.25)',
            'text': '#FFB3B3'
        },
        'warm': {
            'glass': 'rgba(255, 200, 100, 0.12)',
            'border': 'rgba(255, 220, 150, 0.20)',
            'text': '#FFD700'
        },
        'mild': {
            'glass': 'rgba(53, 94, 59, 0.12)',  # Hunter green
            'border': 'rgba(74, 124, 89, 0.25)',
            'text': '#4A7C59'
        },
        'cool': {
            'glass': 'rgba(100, 150, 255, 0.12)',
            'border': 'rgba(150, 180, 255, 0.20)',
            'text': '#87CEEB'
        },
        'cold': {
            'glass': 'rgba(192, 192, 192, 0.15)',  # Silver
            'border': 'rgba(220, 220, 220, 0.25)',
            'text': '#E5E5E5'
        }
    }
    
    CONDITION_COLORS = {
        'clear': {
            'glass': 'rgba(255, 215, 0, 0.10)',
            'accent': '#FFD700'
        },
        'clouds': {
            'glass': 'rgba(192, 192, 192, 0.12)',
            'accent': '#C0C0C0'
        },
        'rain': {
            'glass': 'rgba(100, 150, 200, 0.15)',
            'accent': '#6495ED'
        },
        'snow': {
            'glass': 'rgba(240, 248, 255, 0.12)',
            'accent': '#F0F8FF'
        },
        'storm': {
            'glass': 'rgba(75, 0, 130, 0.15)',
            'accent': '#4B0082'
        }
    }
```

## Implementation Guidelines

### 1. Layer Hierarchy

- **Background**: Solid dark color (#0a0a0a)
- **Base Glass**: Large panels with 10-15% opacity
- **Card Glass**: Individual components with 12-18% opacity
- **Interactive Glass**: Buttons/inputs with 15-25% opacity
- **Modal Glass**: Overlays with 20-30% opacity

### 2. Animation Transitions

```python
class GlassAnimations:
    """Animation configurations for glassmorphic elements."""
    
    HOVER_TRANSITION = {
        'duration': 300,  # milliseconds
        'easing': 'ease-out',
        'properties': ['background', 'border', 'transform', 'box-shadow']
    }
    
    FOCUS_TRANSITION = {
        'duration': 200,
        'easing': 'ease-in-out',
        'properties': ['border-color', 'box-shadow']
    }
    
    MODAL_TRANSITION = {
        'duration': 400,
        'easing': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'properties': ['opacity', 'backdrop-filter']
    }
```

### 3. Accessibility Considerations

- Maintain minimum 4.5:1 contrast ratio for text
- Provide high-contrast mode option
- Ensure focus indicators are clearly visible
- Test with screen readers for proper navigation

### 4. Performance Optimization

- Use `will-change` CSS property sparingly
- Limit backdrop-filter usage to essential elements
- Implement lazy loading for complex glass effects
- Consider reduced motion preferences

## Usage Examples

### Weather Card Implementation

```python
class WeatherGlassCard(tk.Frame):
    def __init__(self, parent, weather_data, **kwargs):
        colors = EnhancedGlassmorphicStyle.get_current_colors()
        
        super().__init__(
            parent,
            bg=colors['card_bg'],
            highlightbackground=colors['border_color'],
            highlightthickness=1,
            relief='flat',
            **kwargs
        )
        
        # Temperature-based glass tinting
        temp_range = self._get_temperature_range(weather_data.temperature)
        temp_colors = WeatherGlassColors.TEMPERATURE_COLORS[temp_range]
        
        # Apply temperature-specific styling
        self.configure(bg=self._blend_colors(
            colors['card_bg'], 
            temp_colors['glass']
        ))
```

### Dashboard Panel with Adaptive Colors

```python
class AdaptiveGlassPanel(tk.Frame):
    def __init__(self, parent, panel_type='default', **kwargs):
        self.colors = EnhancedGlassmorphicStyle.get_current_colors()
        self.panel_type = panel_type
        
        # Adaptive background based on panel type
        bg_color = self._get_adaptive_background()
        
        super().__init__(
            parent,
            bg=bg_color,
            **self._get_glass_style(),
            **kwargs
        )
    
    def _get_adaptive_background(self):
        """Get background color based on panel type and current weather."""
        base_color = self.colors['panel_bg']
        
        if self.panel_type == 'forecast':
            return self._tint_color(base_color, self.colors['hunter_green'], 0.1)
        elif self.panel_type == 'current':
            return self._tint_color(base_color, self.colors['silver'], 0.08)
        
        return base_color
```

## Color Scheme Switching

```python
class ColorSchemeManager:
    """Manage dynamic color scheme switching."""
    
    @staticmethod
    def switch_scheme(new_scheme: str):
        """Switch to a new color scheme and update all components."""
        EnhancedGlassmorphicStyle.CURRENT_SCHEME = new_scheme
        
        # Trigger UI update event
        # This would be implemented in your main application
        pass
    
    @staticmethod
    def get_available_schemes():
        """Get list of available color schemes."""
        return ['midnight_forest', 'silver_mist', 'forest_shadow']
    
    @staticmethod
    def create_scheme_preview(scheme_name: str):
        """Create a preview of the color scheme."""
        # Implementation for scheme preview generation
        pass
```

This comprehensive glassmorphic color scheme provides a modern, elegant foundation for your weather dashboard while maintaining excellent readability and visual hierarchy.
