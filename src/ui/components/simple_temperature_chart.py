import tkinter as tk
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import customtkinter as ctk


class SimpleTemperatureChart(ctk.CTkFrame):
    """A professional interactive temperature chart widget with advanced features."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.temperatures: List[float] = []
        self.timestamps: List[datetime] = []
        self.max_points = 24  # Show 24 hours of data
        self.temp_unit = "C"  # Default to Celsius

        # Animation state
        self.animation_progress = 0.0
        self.animation_duration = 500  # 500ms
        self.animation_id = None
        self.old_temperatures = []

        # Zoom and pan state
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.is_panning = False

        # Tooltip state
        self.tooltip_window = None
        self.hover_index = -1

        # Initialize theme colors
        self.chart_color = "#00FF41"
        self.bg_color = "#0D0D0D"
        self.text_color = "#E0E0E0"
        self.grid_color = "#333333"

        # Temperature range colors
        self.temp_colors = {
            "cold": "#4A90E2",  # Blue
            "moderate": "#7ED321",  # Green
            "hot": "#D0021B",  # Red
        }

        # Create canvas for drawing the chart
        self.canvas = tk.Canvas(self, bg=self.bg_color, highlightthickness=0, height=300)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # Bind events
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Motion>", self._on_mouse_motion)
        self.canvas.bind("<Button-1>", self._on_mouse_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Leave>", self._on_mouse_leave)

    def update_data(
        self, temperatures: List[float], timestamps: Optional[List[datetime]] = None
    ) -> None:
        """Update the chart with new temperature data with smooth animation."""
        if not temperatures:
            self.temperatures = []
            self.timestamps = []
            self._draw_chart()
            return

        # Store old data for animation
        self.old_temperatures = self.temperatures.copy()

        # Update data
        self.temperatures = temperatures[-self.max_points :]

        # Generate timestamps if not provided
        if timestamps:
            self.timestamps = timestamps[-self.max_points :]
        else:
            now = datetime.now()
            self.timestamps = [
                now - timedelta(hours=i) for i in range(len(self.temperatures) - 1, -1, -1)
            ]

        # Start animation
        self._start_animation()

    def set_data(
        self, temperatures: List[float], timestamps: Optional[List[datetime]] = None
    ) -> None:
        """Set the chart data (alias for update_data)."""
        self.update_data(temperatures, timestamps)

    def set_temperature_unit(self, unit: str) -> None:
        """Set temperature unit and redraw chart."""
        if unit != self.temp_unit:
            old_unit = self.temp_unit
            self.temp_unit = unit

            # Convert existing temperatures
            if self.temperatures:
                converted_temps = []
                for temp in self.temperatures:
                    converted_temps.append(self._convert_temperature(temp, old_unit, unit))
                self.temperatures = converted_temps

            self._draw_chart()

    def _convert_temperature(self, temp: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature between units."""
        if from_unit == to_unit:
            return temp

        # Convert to Celsius first
        if from_unit == "F":
            celsius = (temp - 32) * 5 / 9
        elif from_unit == "K":
            celsius = temp - 273.15
        else:
            celsius = temp

        # Convert from Celsius to target unit
        if to_unit == "F":
            return (celsius * 9 / 5) + 32
        elif to_unit == "K":
            return celsius + 273.15
        else:
            return celsius

    def update_theme(self, theme_data: Dict[str, Any]) -> None:
        """Update chart colors based on theme data."""
        try:
            # Update canvas background
            self.canvas.configure(bg=theme_data.get("chart_bg", "#0D0D0D"))

            # Store theme colors for next redraw
            self.chart_color = theme_data.get("chart_color", "#00FF41")
            self.bg_color = theme_data.get("chart_bg", "#0D0D0D")
            self.text_color = theme_data.get("text", "#E0E0E0")
            self.grid_color = theme_data.get("secondary", "#333333")

            # Update temperature range colors based on theme
            primary = theme_data.get("primary", "#00FF41")
            secondary = theme_data.get("secondary", "#008F11")
            accent = theme_data.get("accent", "#00FF41")

            self.temp_colors = {
                "cold": self._adjust_color_brightness(primary, 0.7),
                "moderate": secondary,
                "hot": self._adjust_color_brightness(accent, 1.2),
            }

            # Redraw chart with new colors
            self._draw_chart()

        except Exception as e:
            print(f"Error updating chart theme: {e}")

    def _adjust_color_brightness(self, hex_color: str, factor: float) -> str:
        """Adjust the brightness of a hex color."""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip("#")

            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # Adjust brightness
            r = min(255, max(0, int(r * factor)))
            g = min(255, max(0, int(g * factor)))
            b = min(255, max(0, int(b * factor)))

            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _start_animation(self) -> None:
        """Start smooth animation transition."""
        if self.animation_id:
            self.after_cancel(self.animation_id)

        self.animation_progress = 0.0
        self._animate_step()

    def _animate_step(self) -> None:
        """Perform one step of the animation."""
        if self.animation_progress >= 1.0:
            self.animation_progress = 1.0
            self._draw_chart()
            return

        # Ease-in-out function
        t = self.animation_progress
        eased_t = t * t * (3.0 - 2.0 * t)

        self._draw_chart(eased_t)

        self.animation_progress += 1.0 / (self.animation_duration / 16)  # ~60fps
        self.animation_id = self.after(16, self._animate_step)

    def _interpolate_temperatures(self, progress: float) -> List[float]:
        """Interpolate between old and new temperatures for animation."""
        if not self.old_temperatures or progress >= 1.0:
            return self.temperatures

        # Ensure both lists have the same length for interpolation
        old_len = len(self.old_temperatures)
        new_len = len(self.temperatures)

        if old_len == new_len:
            return [
                old + (new - old) * progress
                for old, new in zip(self.old_temperatures, self.temperatures)
            ]
        else:
            # If lengths differ, just return current temperatures
            return self.temperatures

    def _draw_chart(self, animation_progress: float = 1.0) -> None:
        """Draw the professional temperature chart with all features."""
        # Clear canvas
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        # Get current temperatures (possibly interpolated)
        current_temps = self._interpolate_temperatures(animation_progress)

        if not current_temps:
            self._draw_no_data_message(width, height)
            return

        # Calculate chart dimensions with margins
        margin_left = 60
        margin_right = 40
        margin_top = 40
        margin_bottom = 60

        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        if chart_width <= 0 or chart_height <= 0:
            return

        # Apply zoom and pan
        chart_width * self.zoom_factor
        chart_height * self.zoom_factor

        # Find temperature range
        min_temp = min(current_temps)
        max_temp = max(current_temps)
        temp_range = max_temp - min_temp

        if temp_range == 0:
            temp_range = 10  # Default range
            min_temp -= 5
            max_temp += 5
        else:
            # Add padding
            padding = temp_range * 0.1
            min_temp -= padding
            max_temp += padding
            temp_range = max_temp - min_temp

        # Draw temperature range bands
        self._draw_temperature_bands(
            margin_left, margin_top, chart_width, chart_height, min_temp, max_temp
        )

        # Draw grid lines
        self._draw_grid_lines(
            margin_left, margin_top, chart_width, chart_height, min_temp, max_temp
        )

        # Calculate points with smooth interpolation
        points = self._calculate_smooth_points(
            current_temps, margin_left, margin_top, chart_width, chart_height, min_temp, temp_range
        )

        # Draw the temperature curve
        self._draw_temperature_curve(points)

        # Draw temperature points
        self._draw_temperature_points(points, current_temps)

        # Draw min/max markers
        self._draw_min_max_markers(
            current_temps,
            points,
            margin_left,
            margin_top,
            chart_width,
            chart_height,
            min_temp,
            temp_range,
        )

        # Draw axes labels
        self._draw_axes_labels(
            margin_left, margin_top, chart_width, chart_height, min_temp, max_temp
        )

        # Draw time labels
        self._draw_time_labels(margin_left, margin_top, chart_width, chart_height)

    def _draw_no_data_message(self, width: int, height: int) -> None:
        """Draw 'No data available' message."""
        self.canvas.create_text(
            width // 2,
            height // 2,
            text="No data available",
            fill=self.text_color,
            font=("Arial", 16),
            anchor="center",
        )

    def _draw_temperature_bands(
        self, x: int, y: int, width: int, height: int, min_temp: float, max_temp: float
    ) -> None:
        """Draw temperature range bands (cold, moderate, hot)."""
        temp_range = max_temp - min_temp

        # Define temperature thresholds based on unit
        if self.temp_unit == "F":
            cold_threshold = 50  # 50°F
            hot_threshold = 80  # 80°F
        elif self.temp_unit == "K":
            cold_threshold = 283.15  # 10°C in Kelvin
            hot_threshold = 299.15  # 26°C in Kelvin
        else:  # Celsius
            cold_threshold = 10  # 10°C
            hot_threshold = 26  # 26°C

        # Calculate band positions
        cold_y = y + height - ((cold_threshold - min_temp) / temp_range) * height
        hot_y = y + height - ((hot_threshold - min_temp) / temp_range) * height

        # Draw bands with transparency effect
        if cold_y < y + height:
            self.canvas.create_rectangle(
                x,
                max(cold_y, y),
                x + width,
                y + height,
                fill=self.temp_colors["cold"],
                outline="",
                stipple="gray25",
            )

        if hot_y > y and cold_y > y:
            self.canvas.create_rectangle(
                x,
                max(hot_y, y),
                x + width,
                min(cold_y, y + height),
                fill=self.temp_colors["moderate"],
                outline="",
                stipple="gray25",
            )

        if hot_y > y:
            self.canvas.create_rectangle(
                x,
                y,
                x + width,
                min(hot_y, y + height),
                fill=self.temp_colors["hot"],
                outline="",
                stipple="gray25",
            )

    def _draw_grid_lines(
        self, x: int, y: int, width: int, height: int, min_temp: float, max_temp: float
    ) -> None:
        """Draw grid lines with proper styling."""
        max_temp - min_temp

        # Horizontal grid lines (temperature)
        num_h_lines = 5
        for i in range(num_h_lines + 1):
            grid_y = y + (i / num_h_lines) * height
            self.canvas.create_line(
                x, grid_y, x + width, grid_y, fill=self.grid_color, width=1, dash=(2, 2)
            )

        # Vertical grid lines (time)
        num_v_lines = 6
        for i in range(num_v_lines + 1):
            grid_x = x + (i / num_v_lines) * width
            self.canvas.create_line(
                grid_x, y, grid_x, y + height, fill=self.grid_color, width=1, dash=(2, 2)
            )

    def _calculate_smooth_points(
        self,
        temps: List[float],
        x: int,
        y: int,
        width: int,
        height: int,
        min_temp: float,
        temp_range: float,
    ) -> List[Tuple[float, float]]:
        """Calculate smooth interpolated points for the temperature curve."""
        if len(temps) < 2:
            return []

        points = []

        # Calculate base points
        base_points = []
        for i, temp in enumerate(temps):
            point_x = x + (i / (len(temps) - 1)) * width
            point_y = y + height - ((temp - min_temp) / temp_range) * height
            base_points.append((point_x, point_y))

        # Create smooth curve using cubic interpolation
        if len(base_points) >= 3:
            # Add more points between existing points for smoothness
            for i in range(len(base_points) - 1):
                p0 = base_points[max(0, i - 1)]
                p1 = base_points[i]
                p2 = base_points[i + 1]
                p3 = base_points[min(len(base_points) - 1, i + 2)]

                # Add interpolated points
                steps = 10
                for step in range(steps):
                    t = step / steps

                    # Catmull-Rom spline interpolation
                    x_interp = self._catmull_rom_interpolate(p0[0], p1[0], p2[0], p3[0], t)
                    y_interp = self._catmull_rom_interpolate(p0[1], p1[1], p2[1], p3[1], t)

                    points.append((x_interp, y_interp))

            # Add the last point
            points.append(base_points[-1])
        else:
            points = base_points

        return points

    def _catmull_rom_interpolate(
        self, p0: float, p1: float, p2: float, p3: float, t: float
    ) -> float:
        """Catmull-Rom spline interpolation for smooth curves."""
        return 0.5 * (
            2 * p1
            + (-p0 + p2) * t
            + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
            + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t
        )

    def _draw_temperature_curve(self, points: List[Tuple[float, float]]) -> None:
        """Draw the smooth temperature curve."""
        if len(points) < 2:
            return

        # Convert points to flat list for tkinter
        flat_points = []
        for x, y in points:
            flat_points.extend([x, y])

        # Draw the main curve
        self.canvas.create_line(
            flat_points,
            fill=self.chart_color,
            width=3,
            smooth=True,
            capstyle="round",
            joinstyle="round",
        )

        # Add glow effect
        self.canvas.create_line(
            flat_points,
            fill=self.chart_color,
            width=6,
            smooth=True,
            capstyle="round",
            joinstyle="round",
            stipple="gray50",
        )

    def _draw_temperature_points(
        self, points: List[Tuple[float, float]], temps: List[float]
    ) -> None:
        """Draw temperature data points."""
        if not points or not temps:
            return

        # Only draw points for actual data points, not interpolated ones
        step = len(points) // len(temps) if len(points) > len(temps) else 1

        for i in range(0, len(points), step):
            if i // step < len(temps):
                x, y = points[i]

                # Outer circle
                self.canvas.create_oval(
                    x - 5,
                    y - 5,
                    x + 5,
                    y + 5,
                    fill=self.chart_color,
                    outline=self.text_color,
                    width=2,
                )

                # Inner circle
                self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill=self.bg_color, outline="")

    def _draw_min_max_markers(
        self,
        temps: List[float],
        points: List[Tuple[float, float]],
        x: int,
        y: int,
        width: int,
        height: int,
        min_temp: float,
        temp_range: float,
    ) -> None:
        """Draw min/max temperature markers with labels."""
        if not temps or not points:
            return

        min_val = min(temps)
        max_val = max(temps)
        min_idx = temps.index(min_val)
        max_idx = temps.index(max_val)

        # Calculate positions
        step = len(points) // len(temps) if len(points) > len(temps) else 1

        if min_idx * step < len(points):
            min_x, min_y = points[min_idx * step]

            # Min marker
            self.canvas.create_polygon(
                min_x,
                min_y - 15,
                min_x - 8,
                min_y - 25,
                min_x + 8,
                min_y - 25,
                fill=self.temp_colors["cold"],
                outline=self.text_color,
                width=1,
            )

            # Min label
            unit_symbol = "°" + self.temp_unit
            self.canvas.create_text(
                min_x,
                min_y - 35,
                text=f"Min: {min_val:.1f}{unit_symbol}",
                fill=self.text_color,
                font=("Arial", 10, "bold"),
                anchor="center",
            )

        if max_idx * step < len(points):
            max_x, max_y = points[max_idx * step]

            # Max marker
            self.canvas.create_polygon(
                max_x,
                max_y + 15,
                max_x - 8,
                max_y + 25,
                max_x + 8,
                max_y + 25,
                fill=self.temp_colors["hot"],
                outline=self.text_color,
                width=1,
            )

            # Max label
            unit_symbol = "°" + self.temp_unit
            self.canvas.create_text(
                max_x,
                max_y + 35,
                text=f"Max: {max_val:.1f}{unit_symbol}",
                fill=self.text_color,
                font=("Arial", 10, "bold"),
                anchor="center",
            )

    def _draw_axes_labels(
        self, x: int, y: int, width: int, height: int, min_temp: float, max_temp: float
    ) -> None:
        """Draw temperature axis labels."""
        temp_range = max_temp - min_temp
        unit_symbol = "°" + self.temp_unit

        # Y-axis labels (temperature)
        num_labels = 5
        for i in range(num_labels + 1):
            temp_val = min_temp + (i / num_labels) * temp_range
            label_y = y + height - (i / num_labels) * height

            self.canvas.create_text(
                x - 10,
                label_y,
                text=f"{temp_val:.0f}{unit_symbol}",
                fill=self.text_color,
                font=("Arial", 9),
                anchor="e",
            )

        # Y-axis title
        self.canvas.create_text(
            20,
            y + height // 2,
            text=f"Temperature ({unit_symbol})",
            fill=self.text_color,
            font=("Arial", 10, "bold"),
            anchor="center",
            angle=90,
        )

    def _draw_time_labels(self, x: int, y: int, width: int, height: int) -> None:
        """Draw time labels on x-axis (every 3 hours)."""
        if not self.timestamps:
            return

        # Show every 3rd hour or adjust based on data density
        step = max(1, len(self.timestamps) // 8)  # Show ~8 labels max

        for i in range(0, len(self.timestamps), step):
            if i < len(self.timestamps):
                timestamp = self.timestamps[i]
                label_x = x + (i / (len(self.timestamps) - 1)) * width

                # Format time (show hour)
                time_str = timestamp.strftime("%H:%M")

                self.canvas.create_text(
                    label_x,
                    y + height + 20,
                    text=time_str,
                    fill=self.text_color,
                    font=("Arial", 9),
                    anchor="center",
                )

        # X-axis title
        self.canvas.create_text(
            x + width // 2,
            y + height + 45,
            text="Time",
            fill=self.text_color,
            font=("Arial", 10, "bold"),
            anchor="center",
        )

    def _on_mouse_motion(self, event) -> None:
        """Handle mouse motion for hover tooltips."""
        if not self.temperatures:
            return

        # Find closest data point
        closest_index = self._find_closest_point(event.x, event.y)

        if closest_index != self.hover_index:
            self.hover_index = closest_index
            self._show_tooltip(event.x, event.y, closest_index)

    def _find_closest_point(self, mouse_x: int, mouse_y: int) -> int:
        """Find the closest data point to mouse position."""
        if not self.temperatures:
            return -1

        width = self.canvas.winfo_width()
        self.canvas.winfo_height()
        margin_left = 60
        margin_right = 40
        chart_width = width - margin_left - margin_right

        # Convert mouse x to data index
        relative_x = mouse_x - margin_left
        if relative_x < 0 or relative_x > chart_width:
            return -1

        index = int((relative_x / chart_width) * (len(self.temperatures) - 1))
        return max(0, min(index, len(self.temperatures) - 1))

    def _show_tooltip(self, x: int, y: int, index: int) -> None:
        """Show interactive tooltip with temperature and time."""
        if index < 0 or index >= len(self.temperatures):
            self._hide_tooltip()
            return

        temp = self.temperatures[index]
        timestamp = self.timestamps[index] if index < len(self.timestamps) else datetime.now()

        # Create or update tooltip
        if self.tooltip_window:
            self.tooltip_window.destroy()

        self.tooltip_window = tk.Toplevel(self)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.configure(bg="#2B2B2B")

        # Position tooltip
        root_x = self.winfo_rootx() + x + 10
        root_y = self.winfo_rooty() + y - 30
        self.tooltip_window.geometry(f"+{root_x}+{root_y}")

        # Tooltip content
        unit_symbol = "°" + self.temp_unit
        time_str = timestamp.strftime("%H:%M")

        tooltip_text = f"{temp:.1f}{unit_symbol}\n{time_str}"

        label = tk.Label(
            self.tooltip_window,
            text=tooltip_text,
            bg="#2B2B2B",
            fg="#FFFFFF",
            font=("Arial", 10),
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=4,
        )
        label.pack()

    def _hide_tooltip(self) -> None:
        """Hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
        self.hover_index = -1

    def _on_mouse_leave(self, event) -> None:
        """Handle mouse leaving the canvas."""
        self._hide_tooltip()

    def _on_mouse_press(self, event) -> None:
        """Handle mouse press for pan start."""
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.is_panning = True

    def _on_mouse_drag(self, event) -> None:
        """Handle mouse drag for panning."""
        if self.is_panning:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y

            self.pan_x += dx
            self.pan_y += dy

            self.last_mouse_x = event.x
            self.last_mouse_y = event.y

            self._draw_chart()

    def _on_mouse_release(self, event) -> None:
        """Handle mouse release for pan end."""
        self.is_panning = False

    def _on_mouse_wheel(self, event) -> None:
        """Handle mouse wheel for zooming."""
        # Zoom in/out
        zoom_delta = 0.1
        if event.delta > 0:
            self.zoom_factor = min(3.0, self.zoom_factor + zoom_delta)
        else:
            self.zoom_factor = max(0.5, self.zoom_factor - zoom_delta)

        self._draw_chart()

    def _on_canvas_resize(self, event) -> None:
        """Handle canvas resize event."""
        self._draw_chart()

    def reset_zoom_pan(self) -> None:
        """Reset zoom and pan to default values."""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._draw_chart()

    def _get_appearance_mode(self) -> str:
        """Get current appearance mode."""
        return ctk.get_appearance_mode().lower()
