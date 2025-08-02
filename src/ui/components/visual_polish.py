"""Visual Polish System

Provides glass morphism effects, shadows, consistent spacing,
loading skeletons, and keyboard shortcuts for enhanced UI.
"""

import tkinter as tk
from enum import Enum
from typing import Callable, Dict, Optional

import customtkinter as ctk

from .animation_manager import AnimationManager


class SpacingGrid(Enum):
    """8px grid spacing system."""

    XS = 4  # 0.5 units
    SM = 8  # 1 unit
    MD = 16  # 2 units
    LG = 24  # 3 units
    XL = 32  # 4 units
    XXL = 48  # 6 units


class GlassMorphism:
    """Glass morphism effects for modern UI."""

    def __init__(self, theme_colors: Optional[Dict[str, str]] = None):
        self.theme_colors = theme_colors or {
            "glass_bg": "#FFFFFF",
            "glass_border": "#E0E0E0",
            "glass_shadow": "#000000",
            "glass_highlight": "#FFFFFF",
        }

    def apply_glass_effect(
        self,
        widget: ctk.CTkFrame,
        opacity: float = 0.1,
        blur_radius: int = 10,
        border_opacity: float = 0.2,
        add_highlight: bool = True,
    ) -> ctk.CTkFrame:
        """Apply glass morphism effect to widget."""

        # Calculate glass colors with opacity
        glass_bg = self._apply_opacity(self.theme_colors["glass_bg"], opacity)
        glass_border = self._apply_opacity(self.theme_colors["glass_border"], border_opacity)

        # Configure widget with glass properties
        widget.configure(
            fg_color=glass_bg, border_color=glass_border, border_width=1, corner_radius=12
        )

        # Add highlight effect
        if add_highlight:
            self._add_glass_highlight(widget)

        return widget

    def create_glass_card(
        self, parent: ctk.CTkBaseClass, width: int = 300, height: int = 200, opacity: float = 0.1
    ) -> ctk.CTkFrame:
        """Create glass morphism card."""

        card = ctk.CTkFrame(parent, width=width, height=height)

        return self.apply_glass_effect(card, opacity=opacity)

    def _apply_opacity(self, color: str, opacity: float) -> str:
        """Apply opacity to hex color."""
        try:
            # Remove # if present
            color = color.lstrip("#")

            # Convert to RGB
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)

            # Apply opacity (blend with white for glass effect)
            r = int(r + (255 - r) * (1 - opacity))
            g = int(g + (255 - g) * (1 - opacity))
            b = int(b + (255 - b) * (1 - opacity))

            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return color

    def _add_glass_highlight(self, widget: ctk.CTkFrame):
        """Add subtle highlight to glass element."""
        # Create highlight frame
        highlight = ctk.CTkFrame(
            widget,
            height=2,
            fg_color=self._apply_opacity(self.theme_colors["glass_highlight"], 0.3),
            corner_radius=0,
        )
        highlight.place(relx=0, rely=0, relwidth=1.0)


class ShadowSystem:
    """Advanced shadow system for depth and hierarchy."""

    def __init__(self, theme_colors: Optional[Dict[str, str]] = None):
        self.theme_colors = theme_colors or {
            "shadow_light": "#00000010",
            "shadow_medium": "#00000020",
            "shadow_heavy": "#00000040",
            "shadow_color": "#000000",
        }

    def add_elevation_shadow(
        self, widget: ctk.CTkBaseClass, elevation: int = 2, color: Optional[str] = None
    ) -> ctk.CTkFrame:
        """Add Material Design elevation shadow."""

        shadow_color = color or self.theme_colors["shadow_color"]

        # Shadow properties based on elevation
        shadow_configs = {
            1: {"offset": 1, "blur": 3, "opacity": 0.12},
            2: {"offset": 2, "blur": 6, "opacity": 0.16},
            3: {"offset": 3, "blur": 10, "opacity": 0.19},
            4: {"offset": 4, "blur": 14, "opacity": 0.25},
            5: {"offset": 5, "blur": 18, "opacity": 0.30},
        }

        config = shadow_configs.get(elevation, shadow_configs[2])

        # Create shadow frame
        shadow_frame = ctk.CTkFrame(
            widget.master,
            width=widget.winfo_reqwidth() + config["blur"],
            height=widget.winfo_reqheight() + config["blur"],
            fg_color=self._apply_shadow_opacity(shadow_color, config["opacity"]),
            corner_radius=getattr(widget, "_corner_radius", 6) + 2,
        )

        # Position shadow behind widget
        shadow_frame.place(
            x=widget.winfo_x() + config["offset"], y=widget.winfo_y() + config["offset"]
        )

        # Lower shadow behind widget
        shadow_frame.lower(widget)

        return shadow_frame

    def add_glow_effect(
        self,
        widget: ctk.CTkBaseClass,
        color: str = "#4A9EFF",
        intensity: float = 0.3,
        radius: int = 8,
    ):
        """Add glow effect around widget."""

        glow_frame = ctk.CTkFrame(
            widget.master,
            width=widget.winfo_reqwidth() + radius * 2,
            height=widget.winfo_reqheight() + radius * 2,
            fg_color=self._apply_shadow_opacity(color, intensity),
            corner_radius=getattr(widget, "_corner_radius", 6) + radius,
        )

        # Position glow behind widget
        glow_frame.place(x=widget.winfo_x() - radius, y=widget.winfo_y() - radius)

        glow_frame.lower(widget)

        return glow_frame

    def _apply_shadow_opacity(self, color: str, opacity: float) -> str:
        """Apply opacity to shadow color."""
        try:
            color = color.lstrip("#")
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)

            # Convert to RGBA-like representation
            alpha = int(255 * opacity)
            return f"#{r:02x}{g:02x}{b:02x}{alpha:02x}"
        except (ValueError, IndexError):
            return color


class LoadingSkeleton:
    """Advanced loading skeleton system."""

    def __init__(self, theme_colors: Optional[Dict[str, str]] = None):
        self.theme_colors = theme_colors or {
            "skeleton_bg": "#2A2A2A",
            "skeleton_highlight": "#3A3A3A",
            "skeleton_shimmer": "#4A4A4A",
        }

        self.active_skeletons = []

    def create_text_skeleton(
        self, parent: ctk.CTkBaseClass, lines: int = 3, width_variance: bool = True
    ) -> ctk.CTkFrame:
        """Create text loading skeleton."""

        skeleton_frame = ctk.CTkFrame(parent, fg_color="transparent")

        for i in range(lines):
            # Vary line widths for realistic effect
            if width_variance:
                width_factor = 1.0 if i < lines - 1 else 0.6 + (i * 0.1)
            else:
                width_factor = 1.0

            line = ctk.CTkFrame(
                skeleton_frame,
                height=16,
                fg_color=self.theme_colors["skeleton_bg"],
                corner_radius=8,
            )
            line.pack(
                fill="x", pady=(0, SpacingGrid.SM.value), padx=(0, int((1 - width_factor) * 100))
            )

            # Add shimmer effect
            self._add_shimmer_effect(line)

        self.active_skeletons.append(skeleton_frame)
        return skeleton_frame

    def create_card_skeleton(
        self,
        parent: ctk.CTkBaseClass,
        width: int = 300,
        height: int = 200,
        include_image: bool = True,
    ) -> ctk.CTkFrame:
        """Create card loading skeleton."""

        skeleton_frame = ctk.CTkFrame(
            parent,
            width=width,
            height=height,
            fg_color=self.theme_colors["skeleton_bg"],
            corner_radius=12,
        )
        skeleton_frame.pack_propagate(False)

        content_frame = ctk.CTkFrame(skeleton_frame, fg_color="transparent")
        content_frame.pack(
            fill="both", expand=True, padx=SpacingGrid.MD.value, pady=SpacingGrid.MD.value
        )

        # Image placeholder
        if include_image:
            image_skeleton = ctk.CTkFrame(
                content_frame,
                height=80,
                fg_color=self.theme_colors["skeleton_highlight"],
                corner_radius=8,
            )
            image_skeleton.pack(fill="x", pady=(0, SpacingGrid.MD.value))
            self._add_shimmer_effect(image_skeleton)

        # Text lines
        for i in range(3):
            width_factor = [1.0, 0.8, 0.6][i]
            line = ctk.CTkFrame(
                content_frame,
                height=12,
                fg_color=self.theme_colors["skeleton_highlight"],
                corner_radius=6,
            )
            line.pack(
                fill="x", pady=(0, SpacingGrid.SM.value), padx=(0, int((1 - width_factor) * 100))
            )
            self._add_shimmer_effect(line)

        self.active_skeletons.append(skeleton_frame)
        return skeleton_frame

    def create_chart_skeleton(
        self, parent: ctk.CTkBaseClass, width: int = 400, height: int = 300
    ) -> ctk.CTkFrame:
        """Create chart loading skeleton."""

        skeleton_frame = ctk.CTkFrame(
            parent,
            width=width,
            height=height,
            fg_color=self.theme_colors["skeleton_bg"],
            corner_radius=12,
        )
        skeleton_frame.pack_propagate(False)

        # Chart area
        chart_area = ctk.CTkFrame(
            skeleton_frame, fg_color=self.theme_colors["skeleton_highlight"], corner_radius=8
        )
        chart_area.pack(
            fill="both", expand=True, padx=SpacingGrid.MD.value, pady=SpacingGrid.MD.value
        )

        # Add bars or lines to simulate chart
        bars_frame = ctk.CTkFrame(chart_area, fg_color="transparent")
        bars_frame.pack(side="bottom", fill="x", padx=20, pady=20)

        for i in range(7):  # 7 bars for week
            bar_height = 40 + (i * 10) % 60  # Varying heights
            bar = ctk.CTkFrame(
                bars_frame,
                width=20,
                height=bar_height,
                fg_color=self.theme_colors["skeleton_shimmer"],
                corner_radius=4,
            )
            bar.pack(side="left", padx=2, anchor="s")
            self._add_shimmer_effect(bar)

        self.active_skeletons.append(skeleton_frame)
        return skeleton_frame

    def _add_shimmer_effect(self, widget: ctk.CTkFrame):
        """Add shimmer animation to skeleton element."""

        def shimmer_animation(alpha: float = 0.3):
            try:
                # Pulse between normal and highlight colors
                if alpha >= 1.0:
                    direction = -0.05
                elif alpha <= 0.3:
                    direction = 0.05
                else:
                    direction = getattr(shimmer_animation, "direction", 0.05)

                shimmer_animation.direction = direction
                new_alpha = alpha + direction

                # Apply shimmer color
                shimmer_color = self._blend_colors(
                    self.theme_colors["skeleton_bg"],
                    self.theme_colors["skeleton_shimmer"],
                    new_alpha,
                )

                widget.configure(fg_color=shimmer_color)

                # Continue animation
                widget.after(100, lambda: shimmer_animation(new_alpha))
            except tk.TclError:
                pass  # Widget destroyed

        shimmer_animation()

    def _blend_colors(self, color1: str, color2: str, factor: float) -> str:
        """Blend two colors with given factor."""
        try:
            c1 = color1.lstrip("#")
            c2 = color2.lstrip("#")

            r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
            r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)

            r = int(r1 + (r2 - r1) * factor)
            g = int(g1 + (g2 - g1) * factor)
            b = int(b1 + (b2 - b1) * factor)

            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return color1

    def remove_skeleton(self, skeleton: ctk.CTkFrame):
        """Remove skeleton with fade out."""
        if skeleton in self.active_skeletons:
            self.active_skeletons.remove(skeleton)
            AnimationManager.fade_out(skeleton, duration=300, callback=skeleton.destroy)

    def clear_all_skeletons(self):
        """Clear all active skeletons."""
        for skeleton in self.active_skeletons[:]:
            self.remove_skeleton(skeleton)


class KeyboardShortcuts:
    """Keyboard shortcuts system with visual feedback."""

    def __init__(self, parent: ctk.CTkBaseClass, theme_colors: Optional[Dict[str, str]] = None):
        self.parent = parent
        self.theme_colors = theme_colors or {
            "shortcut_bg": "#2A2A2A",
            "shortcut_border": "#4A4A4A",
            "shortcut_text": "#FFFFFF",
            "shortcut_key": "#4A9EFF",
        }

        self.shortcuts = {}
        self.help_window = None

        # Bind global shortcuts
        self._setup_global_shortcuts()

    def register_shortcut(
        self, key_combination: str, callback: Callable, description: str, category: str = "General"
    ):
        """Register keyboard shortcut."""

        self.shortcuts[key_combination] = {
            "callback": callback,
            "description": description,
            "category": category,
        }

        # Bind the shortcut
        self.parent.bind_all(f"<{key_combination}>", lambda e: callback())

    def show_shortcuts_help(self):
        """Show keyboard shortcuts help window."""

        if self.help_window:
            self.help_window.focus()
            return

        self.help_window = ctk.CTkToplevel(self.parent)
        self.help_window.title("Keyboard Shortcuts")
        self.help_window.geometry("500x600")
        self.help_window.configure(fg_color=self.theme_colors["shortcut_bg"])

        # Make window modal
        self.help_window.transient(self.parent)
        self.help_window.grab_set()

        # Header
        header = ctk.CTkLabel(
            self.help_window,
            text="⌨️ Keyboard Shortcuts",
            font=("JetBrains Mono", 20, "bold"),
            text_color=self.theme_colors["shortcut_text"],
        )
        header.pack(pady=SpacingGrid.LG.value)

        # Scrollable frame for shortcuts
        scroll_frame = ctk.CTkScrollableFrame(self.help_window, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=SpacingGrid.LG.value)

        # Group shortcuts by category
        categories = {}
        for key, data in self.shortcuts.items():
            category = data["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append((key, data))

        # Display shortcuts by category
        for category, shortcuts in categories.items():
            # Category header
            category_label = ctk.CTkLabel(
                scroll_frame,
                text=category,
                font=("JetBrains Mono", 16, "bold"),
                text_color=self.theme_colors["shortcut_key"],
                anchor="w",
            )
            category_label.pack(fill="x", pady=(SpacingGrid.LG.value, SpacingGrid.SM.value))

            # Shortcuts in category
            for key, data in shortcuts:
                self._create_shortcut_item(scroll_frame, key, data["description"])

        # Close button
        close_button = ctk.CTkButton(
            self.help_window,
            text="Close",
            command=self._close_help_window,
            font=("JetBrains Mono", 12),
            height=40,
        )
        close_button.pack(pady=SpacingGrid.LG.value)

        # Bind escape to close
        self.help_window.bind("<Escape>", lambda e: self._close_help_window())

        # Center window
        self.help_window.update_idletasks()
        x = (self.help_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.help_window.winfo_screenheight() // 2) - (600 // 2)
        self.help_window.geometry(f"500x600+{x}+{y}")

    def _create_shortcut_item(self, parent: ctk.CTkBaseClass, key: str, description: str):
        """Create shortcut item display."""

        item_frame = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        item_frame.pack(fill="x", pady=SpacingGrid.XS.value)
        item_frame.pack_propagate(False)

        # Key combination
        key_frame = ctk.CTkFrame(
            item_frame, fg_color=self.theme_colors["shortcut_border"], corner_radius=6, width=120
        )
        key_frame.pack(side="left", padx=(0, SpacingGrid.MD.value), fill="y")
        key_frame.pack_propagate(False)

        key_label = ctk.CTkLabel(
            key_frame,
            text=self._format_key_combination(key),
            font=("JetBrains Mono", 11, "bold"),
            text_color=self.theme_colors["shortcut_key"],
        )
        key_label.pack(expand=True)

        # Description
        desc_label = ctk.CTkLabel(
            item_frame,
            text=description,
            font=("JetBrains Mono", 11),
            text_color=self.theme_colors["shortcut_text"],
            anchor="w",
        )
        desc_label.pack(side="left", fill="both", expand=True)

    def _format_key_combination(self, key: str) -> str:
        """Format key combination for display."""
        # Replace common key names with symbols
        replacements = {
            "Control": "Ctrl",
            "Command": "Cmd",
            "Alt": "Alt",
            "Shift": "Shift",
            "Return": "Enter",
            "BackSpace": "Backspace",
            "Delete": "Del",
            "Escape": "Esc",
        }

        formatted = key
        for old, new in replacements.items():
            formatted = formatted.replace(old, new)

        return formatted

    def _setup_global_shortcuts(self):
        """Setup default global shortcuts."""

        # Register default shortcuts
        self.register_shortcut(
            "Control-h", self.show_shortcuts_help, "Show keyboard shortcuts help", "Help"
        )

        self.register_shortcut(
            "F1", self.show_shortcuts_help, "Show keyboard shortcuts help", "Help"
        )

    def _close_help_window(self):
        """Close help window."""
        if self.help_window:
            self.help_window.grab_release()
            self.help_window.destroy()
            self.help_window = None


class VisualPolishManager:
    """Main visual polish manager coordinating all effects."""

    def __init__(self, parent: ctk.CTkBaseClass, theme_colors: Optional[Dict[str, str]] = None):
        self.parent = parent
        self.theme_colors = theme_colors or {}

        # Initialize subsystems
        self.glass_morphism = GlassMorphism(theme_colors)
        self.shadow_system = ShadowSystem(theme_colors)
        self.loading_skeleton = LoadingSkeleton(theme_colors)
        self.keyboard_shortcuts = KeyboardShortcuts(parent, theme_colors)

        # Track polished elements
        self.polished_elements = []

    def apply_full_polish(self, widget: ctk.CTkBaseClass, polish_config: Dict) -> ctk.CTkBaseClass:
        """Apply comprehensive polish to widget."""

        # Glass morphism
        if polish_config.get("glass", False):
            self.glass_morphism.apply_glass_effect(
                widget, opacity=polish_config.get("glass_opacity", 0.1)
            )

        # Shadow
        if polish_config.get("shadow", False):
            self.shadow_system.add_elevation_shadow(
                widget, elevation=polish_config.get("shadow_elevation", 2)
            )

        # Glow effect
        if polish_config.get("glow", False):
            self.shadow_system.add_glow_effect(
                widget,
                color=polish_config.get("glow_color", "#4A9EFF"),
                intensity=polish_config.get("glow_intensity", 0.3),
            )

        # Consistent spacing
        if polish_config.get("spacing", False):
            self._apply_consistent_spacing(
                widget, polish_config.get("spacing_grid", SpacingGrid.MD)
            )

        self.polished_elements.append(widget)
        return widget

    def create_polished_card(
        self, parent: ctk.CTkBaseClass, width: int = 300, height: int = 200, **polish_config
    ) -> ctk.CTkFrame:
        """Create fully polished card."""

        card = ctk.CTkFrame(parent, width=width, height=height)
        return self.apply_full_polish(card, polish_config)

    def _apply_consistent_spacing(self, widget: ctk.CTkBaseClass, grid: SpacingGrid):
        """Apply consistent spacing using 8px grid."""
        spacing = grid.value

        # Apply padding if widget supports it
        if hasattr(widget, "configure"):
            try:
                widget.configure(padx=spacing, pady=spacing)
            except tk.TclError:
                pass

    def apply_theme(self, theme_colors: Dict[str, str]):
        """Apply theme to all polish systems."""
        self.theme_colors.update(theme_colors)

        # Update subsystems
        self.glass_morphism.theme_colors.update(theme_colors)
        self.shadow_system.theme_colors.update(theme_colors)
        self.loading_skeleton.theme_colors.update(theme_colors)
        self.keyboard_shortcuts.theme_colors.update(theme_colors)

    def update_theme(self, theme_data: Dict = None):
        """Update theme colors for visual polish manager."""
        if theme_data:
            self.apply_theme(theme_data)

    def cleanup(self):
        """Clean up all polish effects."""
        self.loading_skeleton.clear_all_skeletons()
        self.polished_elements.clear()
