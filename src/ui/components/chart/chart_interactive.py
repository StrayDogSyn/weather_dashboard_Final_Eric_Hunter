"""Interactive Features Mixin for Temperature Chart Component.

This module provides interactive capabilities including zoom, pan, hover tooltips,
real-time updates, and advanced user interaction features.
"""

import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import numpy as np
from matplotlib.widgets import Cursor, RectangleSelector


class ChartInteractiveMixin:
    """Mixin for interactive chart features and real-time updates."""

    def __init_interactive__(self):
        """Initialize interactive components."""
        self.zoom_enabled = True
        self.pan_enabled = True
        self.hover_enabled = True
        self.crosshair_enabled = True
        self.real_time_enabled = False

        # Interactive state
        self.zoom_history = []
        self.current_zoom = None
        self.is_panning = False
        self.pan_start = None

        # Hover state
        self.hover_annotation = None
        self.hover_point = None
        self.hover_data = {}

        # Real-time update state
        self.update_thread = None
        self.update_interval = 30  # seconds
        self.last_update = None

        # Interactive widgets
        self.rectangle_selector = None
        self.cursor = None

        # Callbacks
        self.on_data_point_click = None

    def _setup_interactive_features(self):
        """Setup interactive features for the chart."""
        try:
            if hasattr(self, "ax") and self.ax:
                # Setup hover events
                if self.hover_enabled:
                    self._setup_hover_tooltips()

                # Setup zoom and pan functionality
                if self.zoom_enabled or self.pan_enabled:
                    self._setup_zoom_pan()

                # Setup crosshair cursor
                if self.crosshair_enabled:
                    self._setup_crosshair_cursor()

        except Exception as e:
            print(f"Error setting up interactive features: {e}")
        self.on_zoom_change = None
        self.on_real_time_update = None

    def setup_interactive_features(self):
        """Setup all interactive features for the chart."""
        self._setup_zoom_pan()
        self._setup_hover_tooltips()
        self._setup_crosshair_cursor()
        self._setup_click_handlers()
        self._setup_keyboard_shortcuts()

    def _setup_zoom_pan(self):
        """Setup zoom and pan functionality."""
        if not self.zoom_enabled:
            return

        # Rectangle selector for zoom
        self.rectangle_selector = RectangleSelector(
            self.ax,
            self._on_zoom_select,
            useblit=True,
            button=[1],  # Left mouse button
            minspanx=5,
            minspany=5,
            spancoords="pixels",
            interactive=True,
            props=dict(facecolor="#00ff88", alpha=0.2, edgecolor="#00ff88", linewidth=2),
        )

        # Connect pan events
        self.canvas.mpl_connect("button_press_event", self._on_pan_start)
        self.canvas.mpl_connect("button_release_event", self._on_pan_end)
        self.canvas.mpl_connect("motion_notify_event", self._on_pan_motion)

        # Connect scroll wheel for zoom
        self.canvas.mpl_connect("scroll_event", self._on_scroll_zoom)

    def _setup_hover_tooltips(self):
        """Setup hover tooltips for data points."""
        if not self.hover_enabled:
            return

        self.canvas.mpl_connect("motion_notify_event", self._on_hover_motion)

        # Create hover annotation (initially invisible)
        self.hover_annotation = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(20, 20),
            textcoords="offset points",
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor="#1a1a1a",
                alpha=0.9,
                edgecolor="#00ff88",
                linewidth=1.5,
            ),
            arrowprops=dict(
                arrowstyle="->", connectionstyle="arc3,rad=0", color="#00ff88", alpha=0.8
            ),
            fontsize=9,
            color="white",
            visible=False,
            zorder=1000,
        )

    def _setup_crosshair_cursor(self):
        """Setup crosshair cursor for precise data reading."""
        if not self.crosshair_enabled:
            return

        self.cursor = Cursor(self.ax, useblit=True, color="#00ff88", linewidth=1, alpha=0.6)

    def _setup_click_handlers(self):
        """Setup click event handlers."""
        self.canvas.mpl_connect("button_press_event", self._on_chart_click)
        self.canvas.mpl_connect("button_release_event", self._on_chart_release)

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for chart interaction."""
        self.canvas.mpl_connect("key_press_event", self._on_key_press)

        # Make canvas focusable for keyboard events
        self.canvas.get_tk_widget().focus_set()

    def create_interactive_controls(self):
        """Create interactive control panel."""
        import customtkinter as ctk

        self.interactive_frame = ctk.CTkFrame(self, fg_color="transparent")

        # Zoom controls
        self._create_zoom_controls()

        # Real-time controls
        self._create_realtime_controls()

        # Export controls
        self._create_export_controls()

        # View controls
        self._create_view_controls()

    def _create_zoom_controls(self):
        """Create zoom control buttons."""
        import customtkinter as ctk

        self.zoom_frame = ctk.CTkFrame(self.interactive_frame, fg_color="transparent")

        button_config = {
            "width": 80,
            "height": 28,
            "font": ctk.CTkFont(size=10, weight="bold"),
            "fg_color": "#2a2a2a",
            "hover_color": "#3a3a3a",
            "text_color": "#00ff88",
        }

        # Zoom in button
        self.zoom_in_btn = ctk.CTkButton(
            self.zoom_frame, text="🔍+ Zoom In", command=self._zoom_in, **button_config
        )
        self.zoom_in_btn.grid(row=0, column=0, padx=2)

        # Zoom out button
        self.zoom_out_btn = ctk.CTkButton(
            self.zoom_frame, text="🔍- Zoom Out", command=self._zoom_out, **button_config
        )
        self.zoom_out_btn.grid(row=0, column=1, padx=2)

        # Reset zoom button
        self.reset_zoom_btn = ctk.CTkButton(
            self.zoom_frame, text="🏠 Reset", command=self._reset_zoom, **button_config
        )
        self.reset_zoom_btn.grid(row=0, column=2, padx=2)

        # Pan toggle
        self.pan_var = ctk.BooleanVar(value=True)
        self.pan_toggle = ctk.CTkCheckBox(
            self.zoom_frame,
            text="Pan",
            variable=self.pan_var,
            command=self._toggle_pan,
            font=ctk.CTkFont(size=10),
            text_color="#ffffff",
            fg_color="#00ff88",
        )
        self.pan_toggle.grid(row=0, column=3, padx=5)

    def _create_realtime_controls(self):
        """Create real-time update controls."""
        import customtkinter as ctk

        self.realtime_frame = ctk.CTkFrame(self.interactive_frame, fg_color="transparent")

        # Real-time toggle
        self.realtime_var = ctk.BooleanVar(value=False)
        self.realtime_toggle = ctk.CTkCheckBox(
            self.realtime_frame,
            text="🔄 Real-time Updates",
            variable=self.realtime_var,
            command=self._toggle_realtime,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#ffffff",
            fg_color="#00ff88",
        )
        self.realtime_toggle.grid(row=0, column=0, padx=5)

        # Update interval slider
        self.interval_label = ctk.CTkLabel(
            self.realtime_frame, text="Update: 30s", font=ctk.CTkFont(size=9), text_color="#ffffff"
        )
        self.interval_label.grid(row=0, column=1, padx=5)

        self.interval_slider = ctk.CTkSlider(
            self.realtime_frame,
            from_=10,
            to=300,
            number_of_steps=29,
            width=100,
            height=16,
            command=self._on_interval_change,
            fg_color="#2a2a2a",
            progress_color="#00ff88",
            button_color="#00ff88",
            button_hover_color="#00cc6a",
        )
        self.interval_slider.set(30)
        self.interval_slider.grid(row=0, column=2, padx=5)

    def _create_export_controls(self):
        """Create enhanced export controls."""
        import customtkinter as ctk

        self.export_frame = ctk.CTkFrame(self.interactive_frame, fg_color="transparent")

        button_config = {
            "width": 70,
            "height": 28,
            "font": ctk.CTkFont(size=9, weight="bold"),
            "fg_color": "#2a2a2a",
            "hover_color": "#3a3a3a",
            "text_color": "#00ff88",
        }

        # High-res PNG export
        self.export_png_btn = ctk.CTkButton(
            self.export_frame, text="📸 PNG", command=self._export_high_res_png, **button_config
        )
        self.export_png_btn.grid(row=0, column=0, padx=2)

        # SVG export
        self.export_svg_btn = ctk.CTkButton(
            self.export_frame, text="📊 SVG", command=self._export_svg, **button_config
        )
        self.export_svg_btn.grid(row=0, column=1, padx=2)

        # Data export
        self.export_data_btn = ctk.CTkButton(
            self.export_frame, text="💾 CSV", command=self._export_data_csv, **button_config
        )
        self.export_data_btn.grid(row=0, column=2, padx=2)

    def _create_view_controls(self):
        """Create view control options."""
        import customtkinter as ctk

        self.view_frame = ctk.CTkFrame(self.interactive_frame, fg_color="transparent")

        # Crosshair toggle
        self.crosshair_var = ctk.BooleanVar(value=True)
        self.crosshair_toggle = ctk.CTkCheckBox(
            self.view_frame,
            text="Crosshair",
            variable=self.crosshair_var,
            command=self._toggle_crosshair,
            font=ctk.CTkFont(size=9),
            text_color="#ffffff",
            fg_color="#00ff88",
        )
        self.crosshair_toggle.grid(row=0, column=0, padx=3)

        # Hover tooltips toggle
        self.hover_var = ctk.BooleanVar(value=True)
        self.hover_toggle = ctk.CTkCheckBox(
            self.view_frame,
            text="Tooltips",
            variable=self.hover_var,
            command=self._toggle_hover,
            font=ctk.CTkFont(size=9),
            text_color="#ffffff",
            fg_color="#00ff88",
        )
        self.hover_toggle.grid(row=0, column=1, padx=3)

        # Animation toggle
        self.animation_var = ctk.BooleanVar(value=True)
        self.animation_toggle = ctk.CTkCheckBox(
            self.view_frame,
            text="Animations",
            variable=self.animation_var,
            command=self._toggle_animations,
            font=ctk.CTkFont(size=9),
            text_color="#ffffff",
            fg_color="#00ff88",
        )
        self.animation_toggle.grid(row=0, column=2, padx=3)

    # Event handlers
    def _on_zoom_select(self, eclick, erelease):
        """Handle zoom rectangle selection."""
        if not self.zoom_enabled:
            return

        # Get selection bounds
        x1, x2 = sorted([eclick.xdata, erelease.xdata])
        y1, y2 = sorted([eclick.ydata, erelease.ydata])

        if x1 is None or x2 is None or y1 is None or y2 is None:
            return

        # Store current zoom for history
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()
        self.zoom_history.append((current_xlim, current_ylim))

        # Apply zoom
        self.ax.set_xlim(x1, x2)
        self.ax.set_ylim(y1, y2)

        # Update display
        self.canvas.draw()

        # Callback
        if self.on_zoom_change:
            self.on_zoom_change((x1, x2), (y1, y2))

    def _on_pan_start(self, event):
        """Handle pan start."""
        if not self.pan_enabled or not event.inaxes:
            return

        if event.button == 2:  # Middle mouse button
            self.is_panning = True
            self.pan_start = (event.xdata, event.ydata)

    def _on_pan_end(self, event):
        """Handle pan end."""
        if self.is_panning:
            self.is_panning = False
            self.pan_start = None

    def _on_pan_motion(self, event):
        """Handle pan motion."""
        if not self.is_panning or not event.inaxes or not self.pan_start:
            return

        # Calculate pan delta
        dx = self.pan_start[0] - event.xdata
        dy = self.pan_start[1] - event.ydata

        # Apply pan
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        self.ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
        self.ax.set_ylim(ylim[0] + dy, ylim[1] + dy)

        self.canvas.draw()

    def _on_scroll_zoom(self, event):
        """Handle scroll wheel zoom."""
        if not self.zoom_enabled or not event.inaxes:
            return

        # Zoom factor
        zoom_factor = 1.1 if event.step > 0 else 1 / 1.1

        # Get current limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # Calculate new limits centered on mouse position
        x_center = event.xdata
        y_center = event.ydata

        x_range = (xlim[1] - xlim[0]) * zoom_factor
        y_range = (ylim[1] - ylim[0]) * zoom_factor

        new_xlim = (x_center - x_range / 2, x_center + x_range / 2)
        new_ylim = (y_center - y_range / 2, y_center + y_range / 2)

        # Apply zoom
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)

        self.canvas.draw()

    def _on_hover_motion(self, event):
        """Handle hover motion for tooltips."""
        if not self.hover_enabled or not event.inaxes:
            if self.hover_annotation:
                self.hover_annotation.set_visible(False)
                self.canvas.draw_idle()
            return

        # Find nearest data point
        nearest_point = self._find_nearest_data_point(event.xdata, event.ydata)

        if nearest_point:
            self._show_hover_tooltip(nearest_point, event)
        else:
            if self.hover_annotation:
                self.hover_annotation.set_visible(False)
                self.canvas.draw_idle()

    def _find_nearest_data_point(self, x, y) -> Optional[Dict[str, Any]]:
        """Find the nearest data point to the cursor."""
        if not hasattr(self, "hover_data") or not self.hover_data:
            return None

        min_distance = float("inf")
        nearest_point = None

        for metric, data in self.hover_data.items():
            if "times" in data and "values" in data:
                times = data["times"]
                values = data["values"]

                for i, (time, value) in enumerate(zip(times, values)):
                    # Convert time to numeric for distance calculation
                    if hasattr(time, "timestamp"):
                        time_numeric = time.timestamp()
                    else:
                        time_numeric = i

                    # Calculate distance (normalized)
                    dx = abs(time_numeric - x) / (
                        max(times).timestamp() - min(times).timestamp()
                        if hasattr(times[0], "timestamp")
                        else len(times)
                    )
                    dy = (
                        abs(value - y) / (max(values) - min(values))
                        if max(values) != min(values)
                        else 0
                    )

                    distance = np.sqrt(dx**2 + dy**2)

                    if distance < min_distance and distance < 0.1:  # Threshold for selection
                        min_distance = distance
                        nearest_point = {
                            "metric": metric,
                            "time": time,
                            "value": value,
                            "index": i,
                            "x": time_numeric,
                            "y": value,
                        }

        return nearest_point

    def _show_hover_tooltip(self, point: Dict[str, Any], event):
        """Show hover tooltip for data point."""
        if not self.hover_annotation:
            return

        # Format tooltip text
        time_str = (
            point["time"].strftime("%Y-%m-%d %H:%M")
            if hasattr(point["time"], "strftime")
            else str(point["time"])
        )

        tooltip_text = (
            f"{point['metric'].title()}\n" f"Time: {time_str}\n" f"Value: {point['value']:.1f}"
        )

        # Update annotation
        self.hover_annotation.xy = (point["x"], point["y"])
        self.hover_annotation.set_text(tooltip_text)
        self.hover_annotation.set_visible(True)

        # Adjust annotation position to stay within bounds
        bbox = self.hover_annotation.get_window_extent()
        fig_bbox = self.figure.get_window_extent()

        if bbox.x1 > fig_bbox.x1:
            self.hover_annotation.xytext = (-20, 20)
        else:
            self.hover_annotation.xytext = (20, 20)

        self.canvas.draw_idle()

    def _on_chart_click(self, event):
        """Handle chart click events."""
        if not event.inaxes:
            return

        # Find clicked data point
        clicked_point = self._find_nearest_data_point(event.xdata, event.ydata)

        if clicked_point and self.on_data_point_click:
            self.on_data_point_click(clicked_point)

    def _on_chart_release(self, event):
        """Handle chart release events."""

    def _on_key_press(self, event):
        """Handle keyboard shortcuts."""
        if event.key == "r":
            self._reset_zoom()
        elif event.key == "+":
            self._zoom_in()
        elif event.key == "-":
            self._zoom_out()
        elif event.key == "h":
            self._toggle_hover()
        elif event.key == "c":
            self._toggle_crosshair()
        elif event.key == "t":
            self._toggle_realtime()

    # Control methods
    def _zoom_in(self):
        """Zoom in on the chart."""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2

        x_range = (xlim[1] - xlim[0]) * 0.8
        y_range = (ylim[1] - ylim[0]) * 0.8

        self.ax.set_xlim(x_center - x_range / 2, x_center + x_range / 2)
        self.ax.set_ylim(y_center - y_range / 2, y_center + y_range / 2)

        self.canvas.draw()

    def _zoom_out(self):
        """Zoom out on the chart."""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2

        x_range = (xlim[1] - xlim[0]) * 1.25
        y_range = (ylim[1] - ylim[0]) * 1.25

        self.ax.set_xlim(x_center - x_range / 2, x_center + x_range / 2)
        self.ax.set_ylim(y_center - y_range / 2, y_center + y_range / 2)

        self.canvas.draw()

    def _reset_zoom(self):
        """Reset zoom to original view."""
        if self.zoom_history:
            original_xlim, original_ylim = self.zoom_history[0]
            self.ax.set_xlim(original_xlim)
            self.ax.set_ylim(original_ylim)
        else:
            self.ax.autoscale()

        self.canvas.draw()

    def _toggle_pan(self):
        """Toggle pan functionality."""
        self.pan_enabled = self.pan_var.get()

    def _toggle_realtime(self):
        """Toggle real-time updates."""
        self.real_time_enabled = self.realtime_var.get()

        if self.real_time_enabled:
            self._start_realtime_updates()
        else:
            self._stop_realtime_updates()

    def _toggle_crosshair(self):
        """Toggle crosshair cursor."""
        self.crosshair_enabled = self.crosshair_var.get()

        if self.cursor:
            self.cursor.visible = self.crosshair_enabled
            self.canvas.draw_idle()

    def _toggle_hover(self):
        """Toggle hover tooltips."""
        self.hover_enabled = self.hover_var.get()

        if not self.hover_enabled and self.hover_annotation:
            self.hover_annotation.set_visible(False)
            self.canvas.draw_idle()

    def _toggle_animations(self):
        """Toggle chart animations."""
        # Implementation for animation toggle

    def _on_interval_change(self, value):
        """Handle update interval change."""
        self.update_interval = int(value)
        self.interval_label.configure(text=f"Update: {self.update_interval}s")

    # Real-time update methods
    def _start_realtime_updates(self):
        """Start real-time data updates."""
        if self.update_thread and self.update_thread.is_alive():
            return

        self.update_thread = threading.Thread(target=self._realtime_update_loop, daemon=True)
        self.update_thread.start()

    def _stop_realtime_updates(self):
        """Stop real-time data updates."""
        self.real_time_enabled = False

    def _realtime_update_loop(self):
        """Real-time update loop running in background thread."""
        while self.real_time_enabled:
            try:
                # Trigger update callback
                if self.on_real_time_update:
                    self.on_real_time_update()

                self.last_update = datetime.now()

                # Wait for next update
                time.sleep(self.update_interval)

            except Exception as e:
                print(f"Real-time update error: {e}")
                break

    # Export methods
    def _export_high_res_png(self):
        """Export chart as high-resolution PNG."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG files", "*.png")], title="Export Chart as PNG"
        )

        if filename:
            # Save with high DPI
            self.figure.savefig(
                filename, dpi=300, bbox_inches="tight", facecolor="#1a1a1a", edgecolor="none"
            )
            print(f"Chart exported to {filename}")

    def _export_svg(self):
        """Export chart as SVG."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".svg", filetypes=[("SVG files", "*.svg")], title="Export Chart as SVG"
        )

        if filename:
            self.figure.savefig(
                filename, format="svg", bbox_inches="tight", facecolor="#1a1a1a", edgecolor="none"
            )
            print(f"Chart exported to {filename}")

    def _export_data_csv(self):
        """Export chart data as CSV."""
        import csv
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Export Data as CSV"
        )

        if filename and hasattr(self, "hover_data"):
            try:
                with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)

                    # Write header
                    header = ["Time"]
                    for metric in self.hover_data.keys():
                        header.append(metric.title())
                    writer.writerow(header)

                    # Write data
                    if self.hover_data:
                        first_metric = list(self.hover_data.keys())[0]
                        times = self.hover_data[first_metric].get("times", [])

                        for i, time in enumerate(times):
                            row = [
                                (
                                    time.strftime("%Y-%m-%d %H:%M:%S")
                                    if hasattr(time, "strftime")
                                    else str(time)
                                )
                            ]

                            for metric in self.hover_data.keys():
                                values = self.hover_data[metric].get("values", [])
                                if i < len(values):
                                    row.append(values[i])
                                else:
                                    row.append("")

                            writer.writerow(row)

                print(f"Data exported to {filename}")

            except Exception as e:
                print(f"Error exporting data: {e}")

    def update_hover_data(self, data: Dict[str, Any]):
        """Update data for hover tooltips."""
        self.hover_data = data

    def set_callbacks(
        self,
        on_data_point_click: Optional[Callable] = None,
        on_zoom_change: Optional[Callable] = None,
        on_real_time_update: Optional[Callable] = None,
    ):
        """Set callback functions for interactive events."""
        self.on_data_point_click = on_data_point_click
        self.on_zoom_change = on_zoom_change
        self.on_real_time_update = on_real_time_update
