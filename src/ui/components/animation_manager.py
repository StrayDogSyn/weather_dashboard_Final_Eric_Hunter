"""Animation Manager for Visual Effects

Provides comprehensive animation and visual effect capabilities for the weather dashboard.
Includes shimmer effects, smooth transitions, micro-interactions, and theme-aware animations.
"""

import math
import threading
import time
from typing import Callable, Dict, Optional
import tkinter as tk
import customtkinter as ctk

# ShimmerEffect class moved to src/ui/components/common/loading_spinner.py
# Use ShimmerLoader component instead

class AnimationManager:
    """Manages smooth transitions and animations for UI elements."""

    def __init__(self):
        self.active_animations = {}
        self.shimmer_effects = {}
        self.scheduled_calls = []
        self.is_destroyed = False
        self.theme_colors = {
            "primary": "#1f538d",
            "secondary": "#14375e",
            "accent": "#00d4aa",
            "background": "#0d1117",
            "surface": "#161b22",
            "text": "#f0f6fc",
        }

    def safe_after(self, widget, delay, callback):
        """Safe after() call that tracks scheduled calls for cleanup."""
        if self.is_destroyed:
            return None
        try:
            if not widget or not widget.winfo_exists():
                return None
            call_id = widget.after(delay, callback)
            self.scheduled_calls.append((widget, call_id))
            return call_id
        except (tk.TclError, AttributeError):
            return None

    def cleanup(self):
        """Cancel all scheduled after() calls."""
        self.is_destroyed = True
        for widget, call_id in self.scheduled_calls:
            try:
                widget.after_cancel(call_id)
            except (tk.TclError, ValueError):
                pass
        self.scheduled_calls.clear()

    def fade_in(
        self, widget: ctk.CTkBaseClass, duration: int = 300, callback: Optional[Callable] = None
    ):
        """Fade in effect for widgets."""
        if not hasattr(widget, "configure"):
            return

        steps = 20
        step_duration = duration // steps

        def safe_update(alpha):
            try:
                if widget.winfo_exists():
                    self._set_widget_alpha(widget, alpha)
                    if alpha >= 1.0 and callback:
                        callback()
            except tk.TclError:
                pass

        def animate(step=0):
            if step <= steps and not self.is_destroyed:
                alpha = step / steps
                safe_update(alpha)
                if step < steps:
                    self.safe_after(widget.master, step_duration, lambda: animate(step + 1))

        animate()

    def fade_out(
        self, widget: ctk.CTkBaseClass, duration: int = 300, callback: Optional[Callable] = None
    ):
        """Fade out effect for widgets."""
        if not hasattr(widget, "configure"):
            return

        steps = 20
        step_duration = duration // steps

        def safe_update(alpha):
            try:
                if widget.winfo_exists():
                    self._set_widget_alpha(widget, alpha)
                    if alpha <= 0.0 and callback:
                        callback()
            except tk.TclError:
                pass

        def animate(step=0):
            if step <= steps and not self.is_destroyed:
                alpha = 1.0 - (step / steps)
                safe_update(alpha)
                if step < steps:
                    self.safe_after(widget.master, step_duration, lambda: animate(step + 1))

        animate()

    def slide_in(
        self,
        widget: ctk.CTkBaseClass,
        direction: str = "left",
        duration: int = 400,
        distance: int = 100,
    ):
        """Slide animation for widgets."""
        if not hasattr(widget, "place"):
            return

        # Get current position
        try:
            current_x = widget.winfo_x()
            current_y = widget.winfo_y()
        except tk.TclError:
            return

        # Calculate start position
        start_x, start_y = current_x, current_y

        if direction == "left":
            start_x -= distance
        elif direction == "right":
            start_x += distance
        elif direction == "up":
            start_y -= distance
        elif direction == "down":
            start_y += distance

        # Set initial position
        widget.place(x=start_x, y=start_y)

        # Animation parameters
        steps = 30
        step_duration = duration // steps

        def animate(step=0):
            if step <= steps and not self.is_destroyed:
                progress = step / steps
                # Ease-out animation
                eased_progress = 1 - (1 - progress) ** 3

                x = start_x + (current_x - start_x) * eased_progress
                y = start_y + (current_y - start_y) * eased_progress

                # Safe move with widget existence check
                try:
                    if widget.winfo_exists():
                        AnimationManager._move_widget(widget, x, y)
                except tk.TclError:
                    pass

                if step < steps:
                    self.safe_after(widget.master, step_duration, lambda: animate(step + 1))

        animate()

    def pulse_effect(self, widget: ctk.CTkBaseClass, duration: int = 1000, intensity: float = 0.2):
        """Create pulsing effect for alerts and notifications."""
        if not hasattr(widget, "configure"):
            return

        original_color = widget.cget("fg_color") if hasattr(widget, "cget") else "#2A2A2A"
        start_time = time.time()

        def animate():
            if self.is_destroyed:
                return

            current_time = time.time()
            if current_time - start_time >= duration / 1000:
                # Restore original color and finish
                try:
                    if widget.winfo_exists():
                        self._set_widget_color(widget, original_color)
                except tk.TclError:
                    pass
                return

            progress = ((current_time - start_time) * 1000) % 1000 / 1000
            alpha = intensity * math.sin(progress * math.pi * 2)

            # Calculate pulsed color
            try:
                if isinstance(original_color, str) and original_color.startswith("#"):
                    r = int(original_color[1:3], 16)
                    g = int(original_color[3:5], 16)
                    b = int(original_color[5:7], 16)

                    # Add pulse intensity
                    r = min(255, int(r + 255 * alpha))
                    g = min(255, int(g + 255 * alpha))
                    b = min(255, int(b + 255 * alpha))

                    pulsed_color = f"#{r:02x}{g:02x}{b:02x}"

                    if widget.winfo_exists():
                        self._set_widget_color(widget, pulsed_color)
            except (ValueError, AttributeError, tk.TclError):
                pass

            # Schedule next frame
            self.safe_after(widget.master, 50, animate)

        animate()

    def success_pulse(self, widget: ctk.CTkBaseClass, duration: int = 800, intensity: float = 0.2):
        """Create success pulse effect with green tint."""
        if not widget or not hasattr(widget, "configure"):
            return

        try:
            original_color = widget.cget("fg_color") if hasattr(widget, "cget") else "#2A2A2A"
        except (tk.TclError, AttributeError):
            return

        start_time = time.time()
        success_color = self.theme_colors.get("accent", "#00d4aa")  # Green success color

        def animate():
            if self.is_destroyed:
                return

            try:
                if not widget or not widget.winfo_exists():
                    return
            except (tk.TclError, AttributeError):
                return

            current_time = time.time()
            if current_time - start_time >= duration / 1000:
                # Restore original color and finish
                try:
                    if widget and widget.winfo_exists():
                        self._set_widget_color(widget, original_color)
                except (tk.TclError, AttributeError):
                    pass
                return

            progress = ((current_time - start_time) * 1000) % 1000 / 1000
            alpha = intensity * math.sin(progress * math.pi * 2)

            # Calculate success pulsed color with green tint
            try:
                if isinstance(success_color, str) and success_color.startswith("#"):
                    # Extract RGB from success color
                    sr = int(success_color[1:3], 16)
                    sg = int(success_color[3:5], 16)
                    sb = int(success_color[5:7], 16)

                    # Extract RGB from original color
                    if isinstance(original_color, str) and original_color.startswith("#"):
                        or_val = int(original_color[1:3], 16)
                        og = int(original_color[3:5], 16)
                        ob = int(original_color[5:7], 16)
                    else:
                        or_val, og, ob = 42, 42, 42  # Default gray

                    # Blend original with success color based on pulse
                    r = min(255, int(or_val + (sr - or_val) * alpha))
                    g = min(255, int(og + (sg - og) * alpha))
                    b = min(255, int(ob + (sb - ob) * alpha))

                    pulsed_color = f"#{r:02x}{g:02x}{b:02x}"

                    if widget and widget.winfo_exists():
                        self._set_widget_color(widget, pulsed_color)
            except (ValueError, AttributeError, tk.TclError):
                pass

            # Schedule next frame - use widget itself if master is None
            try:
                target_widget = widget.master if widget.master else widget
                if target_widget and target_widget.winfo_exists():
                    self.safe_after(target_widget, 50, animate)
            except (tk.TclError, AttributeError):
                pass

        animate()

    def pulse_animation(
        self, widget: ctk.CTkBaseClass, duration: int = 600, intensity: float = 0.15
    ):
        """Create a gentle pulse animation for user interactions."""
        if not hasattr(widget, "configure"):
            return

        original_color = widget.cget("fg_color") if hasattr(widget, "cget") else "#2A2A2A"
        start_time = time.time()
        primary_color = self.theme_colors.get("primary", "#1f538d")

        def animate():
            if self.is_destroyed:
                return

            current_time = time.time()
            if current_time - start_time >= duration / 1000:
                # Restore original color and finish
                try:
                    if widget.winfo_exists():
                        self._set_widget_color(widget, original_color)
                except tk.TclError:
                    pass
                return

            progress = ((current_time - start_time) * 1000) % 800 / 800
            alpha = intensity * math.sin(progress * math.pi * 2)

            # Calculate pulsed color with primary theme color
            try:
                if isinstance(primary_color, str) and primary_color.startswith("#"):
                    # Extract RGB from primary color
                    pr = int(primary_color[1:3], 16)
                    pg = int(primary_color[3:5], 16)
                    pb = int(primary_color[5:7], 16)

                    # Extract RGB from original color
                    if isinstance(original_color, str) and original_color.startswith("#"):
                        or_val = int(original_color[1:3], 16)
                        og = int(original_color[3:5], 16)
                        ob = int(original_color[5:7], 16)
                    else:
                        or_val, og, ob = 42, 42, 42  # Default gray

                    # Blend original with primary color based on pulse
                    r = min(255, int(or_val + (pr - or_val) * alpha))
                    g = min(255, int(og + (pg - og) * alpha))
                    b = min(255, int(ob + (pb - ob) * alpha))

                    pulsed_color = f"#{r:02x}{g:02x}{b:02x}"

                    if widget.winfo_exists():
                        self._set_widget_color(widget, pulsed_color)
            except (ValueError, AttributeError, tk.TclError):
                pass

            # Schedule next frame
            self.safe_after(widget.master, 50, animate)

        animate()

    def warning_pulse(self, widget: ctk.CTkBaseClass, duration: int = 1200, intensity: float = 0.3):
        """Create warning pulse effect with red/orange tint."""
        if not hasattr(widget, "configure"):
            return

        original_color = widget.cget("fg_color") if hasattr(widget, "cget") else "#2A2A2A"
        start_time = time.time()
        warning_color = "#ff6b6b"  # Red warning color

        def animate():
            if self.is_destroyed:
                return

            current_time = time.time()
            if current_time - start_time >= duration / 1000:
                # Restore original color and finish
                try:
                    if widget.winfo_exists():
                        self._set_widget_color(widget, original_color)
                except tk.TclError:
                    pass
                return

            progress = ((current_time - start_time) * 1000) % 1200 / 1200
            alpha = intensity * math.sin(progress * math.pi * 2)

            # Calculate warning pulsed color with red tint
            try:
                if isinstance(warning_color, str) and warning_color.startswith("#"):
                    # Extract RGB from warning color
                    wr = int(warning_color[1:3], 16)
                    wg = int(warning_color[3:5], 16)
                    wb = int(warning_color[5:7], 16)

                    # Extract RGB from original color
                    if isinstance(original_color, str) and original_color.startswith("#"):
                        or_val = int(original_color[1:3], 16)
                        og = int(original_color[3:5], 16)
                        ob = int(original_color[5:7], 16)
                    else:
                        or_val, og, ob = 42, 42, 42  # Default gray

                    # Blend original with warning color based on pulse
                    r = min(255, int(or_val + (wr - or_val) * alpha))
                    g = min(255, int(og + (wg - og) * alpha))
                    b = min(255, int(ob + (wb - ob) * alpha))

                    pulsed_color = f"#{r:02x}{g:02x}{b:02x}"

                    if widget.winfo_exists():
                        self._set_widget_color(widget, pulsed_color)
            except (ValueError, AttributeError, tk.TclError):
                pass

            # Schedule next frame
            self.safe_after(widget.master, 50, animate)

        animate()

    def number_transition(
        self,
        label: ctk.CTkLabel,
        start_value: float,
        end_value: float,
        duration: int = 500,
        format_str: str = "{:.1f}",
    ):
        """Smooth number transitions for temperature and metrics."""
        steps = 30
        step_duration = duration // steps

        def animate(step=0):
            if step <= steps and not self.is_destroyed:
                progress = step / steps
                # Ease-out animation
                eased_progress = 1 - (1 - progress) ** 2

                current_value = start_value + (end_value - start_value) * eased_progress

                def safe_update():
                    try:
                        if label.winfo_exists():
                            label.configure(text=format_str.format(current_value))
                    except tk.TclError:
                        pass

                safe_update()

                if step < steps:
                    self.safe_after(label.master, step_duration, lambda: animate(step + 1))

        animate()

    def animate_number_change(self, label: ctk.CTkLabel, new_text: str, duration: int = 500):
        """Animate text changes with smooth transitions."""
        try:
            # Simply update the label text with a fade effect
            self.fade_in(label, duration)
            label.configure(text=new_text)
        except Exception:
            # Fallback to direct text update
            label.configure(text=new_text)

    @staticmethod
    def _set_widget_alpha(widget: ctk.CTkBaseClass, alpha: float):
        """Set widget transparency (simplified for CustomTkinter)."""
        try:
            # CustomTkinter doesn't support true alpha, so we simulate with color intensity
            if hasattr(widget, "configure"):
                # This is a simplified approach - in a real implementation,
                # you might need to adjust colors based on alpha
                pass
        except tk.TclError:
            pass

    @staticmethod
    def _move_widget(widget: ctk.CTkBaseClass, x: float, y: float):
        """Move widget to specified position."""
        try:
            if hasattr(widget, "place"):
                widget.place(x=int(x), y=int(y))
        except tk.TclError:
            pass

    @staticmethod
    def _set_widget_color(widget: ctk.CTkBaseClass, color: str):
        """Set widget color safely."""
        try:
            if hasattr(widget, "configure"):
                widget.configure(fg_color=color)
        except (tk.TclError, AttributeError):
            pass

class MicroInteractions:
    """Handles micro-interactions like hover effects and click feedback."""

    def __init__(self, theme_colors: Optional[Dict[str, str]] = None):
        self.theme_colors = theme_colors or {
            "primary": "#4A9EFF",
            "hover": "#5AAFFF",
            "active": "#3A8EEF",
            "glow": "#87CEEB",
        }
        self.hover_effects = {}

    def add_hover_glow(self, widget: ctk.CTkBaseClass, glow_color: Optional[str] = None):
        """Add glow effect on hover."""
        glow_color = glow_color or self.theme_colors["glow"]

        def on_enter(event):
            try:
                widget.configure(border_width=2, border_color=glow_color)
                # Note: pulse_effect would need animation_manager instance
            except tk.TclError:
                pass

        def on_leave(event):
            try:
                widget.configure(border_width=0)
            except tk.TclError:
                pass

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

        self.hover_effects[widget] = (on_enter, on_leave)

    def add_click_ripple(self, widget: ctk.CTkBaseClass):
        """Add ripple effect on click."""

        def on_click(event):
            # Create ripple effect (simplified)
            # Note: pulse_effect would need animation_manager instance
            pass

        widget.bind("<Button-1>", on_click)

    def add_hover_effect(self, widget: ctk.CTkBaseClass, hover_color: Optional[str] = None):
        """Add hover effect to widget."""
        self.add_hover_glow(widget, hover_color)

    def add_click_effect(self, widget: ctk.CTkBaseClass):
        """Add click effect to widget."""
        self.add_click_ripple(widget)

    def add_ripple_effect(self, widget: ctk.CTkBaseClass):
        """Add ripple effect to widget."""
        self.add_click_ripple(widget)

    def add_warning_pulse(self, widget: ctk.CTkBaseClass, animation_manager: "AnimationManager"):
        """Add warning pulse effect to widget."""
        animation_manager.pulse_effect(widget, duration=1000, intensity=0.4)

    def add_success_pulse(self, widget: ctk.CTkBaseClass, animation_manager: "AnimationManager"):
        """Add success pulse effect to widget."""
        animation_manager.pulse_effect(widget, duration=800, intensity=0.2)

    def remove_effects(self, widget: ctk.CTkBaseClass):
        """Remove all effects from widget."""
        if widget in self.hover_effects:
            try:
                widget.unbind("<Enter>")
                widget.unbind("<Leave>")
                widget.unbind("<Button-1>")
            except tk.TclError:
                pass
            del self.hover_effects[widget]

class LoadingSkeleton:
    """Creates loading skeleton placeholders for data."""

    def __init__(self, parent: ctk.CTkBaseClass, theme_colors: Optional[Dict[str, str]] = None):
        self.parent = parent
        self.theme_colors = theme_colors or {
            "bg": "#2A2A2A",
            "skeleton": "#3A3A3A",
            "highlight": "#4A4A4A",
        }
        self.skeleton_widgets = []

    def create_text_skeleton(self, width: int = 200, height: int = 20, **kwargs) -> ctk.CTkFrame:
        """Create text skeleton placeholder."""
        skeleton = ctk.CTkFrame(
            self.parent,
            width=width,
            height=height,
            fg_color=self.theme_colors["skeleton"],
            corner_radius=4,
            **kwargs,
        )

        # Add shimmer effect
        shimmer = ShimmerEffect(skeleton, self.theme_colors)
        shimmer.start_shimmer()

        self.skeleton_widgets.append((skeleton, shimmer))
        return skeleton

    def create_card_skeleton(self, width: int = 300, height: int = 150, **kwargs) -> ctk.CTkFrame:
        """Create card skeleton placeholder."""
        skeleton = ctk.CTkFrame(
            self.parent,
            width=width,
            height=height,
            fg_color=self.theme_colors["bg"],
            corner_radius=8,
            border_width=1,
            border_color=self.theme_colors["skeleton"],
            **kwargs,
        )

        # Add internal skeleton elements
        title_skeleton = ctk.CTkFrame(
            skeleton,
            width=width - 40,
            height=24,
            fg_color=self.theme_colors["skeleton"],
            corner_radius=4,
        )
        title_skeleton.pack(pady=(20, 10), padx=20, anchor="w")

        content_skeleton = ctk.CTkFrame(
            skeleton,
            width=width - 40,
            height=height - 80,
            fg_color=self.theme_colors["skeleton"],
            corner_radius=4,
        )
        content_skeleton.pack(pady=(0, 20), padx=20, fill="x")

        # Add shimmer effects
        shimmer = ShimmerEffect(skeleton, self.theme_colors)
        shimmer.start_shimmer()

        self.skeleton_widgets.append((skeleton, shimmer))
        return skeleton

    def clear_skeletons(self):
        """Remove all skeleton placeholders."""
        for skeleton, shimmer in self.skeleton_widgets:
            shimmer.stop_shimmer()
            try:
                skeleton.destroy()
            except tk.TclError:
                pass

        self.skeleton_widgets.clear()
