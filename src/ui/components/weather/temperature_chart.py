"""Temperature Chart Component

Simplified temperature chart widget for weather data visualization.
"""

from datetime import datetime, timedelta
from typing import List, Optional
import tkinter as tk
import customtkinter as ctk
from ..glassmorphic.base_frame import GlassmorphicFrame


class TemperatureChart(GlassmorphicFrame):
    """Interactive temperature chart with glassmorphic styling."""

    def __init__(self, parent, width: int = 400, height: int = 200, **kwargs):
        """Initialize temperature chart.
        
        Args:
            parent: Parent widget
            width: Chart width
            height: Chart height
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, width=width, height=height, **kwargs)
        
        # Data storage
        self.temperatures: List[float] = []
        self.timestamps: List[datetime] = []
        self.max_points = 24  # Show 24 hours of data
        self.temp_unit = "C"
        
        # Chart styling
        self.chart_color = "#00FF41"
        self.bg_color = "#0D0D0D"
        self.text_color = "#E0E0E0"
        self.grid_color = "#333333"
        
        # Temperature range colors
        self.temp_colors = {
            "cold": "#4A90E2",    # Blue
            "moderate": "#7ED321", # Green
            "hot": "#D0021B",     # Red
        }
        
        # Tooltip state
        self.tooltip_window = None
        self.hover_index = -1
        
        # Track scheduled calls
        self.scheduled_calls = set()
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(
            self,
            bg=self.bg_color,
            highlightthickness=0,
            height=height - 20
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind events
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Motion>", self._on_mouse_motion)
        self.canvas.bind("<Leave>", self._on_mouse_leave)
        
        # Initial draw
        self.safe_after(100, self._draw_chart)
    
    def safe_after(self, delay_ms: int, callback, *args):
        """Safely schedule an after() call with error handling."""
        try:
            if not self.winfo_exists():
                return None
            
            if args:
                call_id = self.after(delay_ms, callback, *args)
            else:
                call_id = self.after(delay_ms, callback)
            self.scheduled_calls.add(call_id)
            return call_id
        except Exception as e:
            print(f"Error scheduling after() call: {e}")
            return None
    
    def update_data(self, temperatures: List[float], timestamps: Optional[List[datetime]] = None):
        """Update chart data.
        
        Args:
            temperatures: List of temperature values
            timestamps: Optional list of timestamps (auto-generated if None)
        """
        self.temperatures = temperatures[-self.max_points:]  # Keep only recent data
        
        if timestamps:
            self.timestamps = timestamps[-self.max_points:]
        else:
            # Generate timestamps for the last N hours
            now = datetime.now()
            self.timestamps = [
                now - timedelta(hours=i) for i in range(len(self.temperatures) - 1, -1, -1)
            ]
        
        self._draw_chart()
    
    def set_temperature_unit(self, unit: str):
        """Set temperature unit (C or F).
        
        Args:
            unit: Temperature unit ("C" or "F")
        """
        self.temp_unit = unit
        self._draw_chart()
    
    def _draw_chart(self):
        """Draw the temperature chart."""
        try:
            if not self.canvas.winfo_exists():
                return
            
            self.canvas.delete("all")
            
            if not self.temperatures:
                self._draw_no_data_message()
                return
            
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            if width <= 1 or height <= 1:
                return
            
            # Calculate margins
            margin_left = 50
            margin_right = 20
            margin_top = 20
            margin_bottom = 40
            
            chart_width = width - margin_left - margin_right
            chart_height = height - margin_top - margin_bottom
            
            if chart_width <= 0 or chart_height <= 0:
                return
            
            # Calculate temperature range
            min_temp = min(self.temperatures)
            max_temp = max(self.temperatures)
            temp_range = max_temp - min_temp
            
            if temp_range == 0:
                temp_range = 1  # Avoid division by zero
            
            # Draw grid lines
            self._draw_grid(margin_left, margin_top, chart_width, chart_height, min_temp, max_temp)
            
            # Draw temperature line
            self._draw_temperature_line(margin_left, margin_top, chart_width, chart_height, min_temp, temp_range)
            
            # Draw axes labels
            self._draw_axes_labels(margin_left, margin_top, chart_width, chart_height, min_temp, max_temp)
            
        except Exception as e:
            print(f"Error drawing chart: {e}")
    
    def _draw_no_data_message(self):
        """Draw message when no data is available."""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        self.canvas.create_text(
            width // 2,
            height // 2,
            text="No temperature data available",
            fill=self.text_color,
            font=("Consolas", 12),
            anchor="center"
        )
    
    def _draw_grid(self, margin_left, margin_top, chart_width, chart_height, min_temp, max_temp):
        """Draw grid lines."""
        # Horizontal grid lines (temperature)
        num_h_lines = 5
        for i in range(num_h_lines + 1):
            y = margin_top + (chart_height * i / num_h_lines)
            self.canvas.create_line(
                margin_left, y, margin_left + chart_width, y,
                fill=self.grid_color, width=1
            )
        
        # Vertical grid lines (time)
        num_v_lines = min(6, len(self.temperatures))
        if num_v_lines > 1:
            for i in range(num_v_lines):
                x = margin_left + (chart_width * i / (num_v_lines - 1))
                self.canvas.create_line(
                    x, margin_top, x, margin_top + chart_height,
                    fill=self.grid_color, width=1
                )
    
    def _draw_temperature_line(self, margin_left, margin_top, chart_width, chart_height, min_temp, temp_range):
        """Draw the temperature line."""
        if len(self.temperatures) < 2:
            return
        
        points = []
        for i, temp in enumerate(self.temperatures):
            x = margin_left + (chart_width * i / (len(self.temperatures) - 1))
            y = margin_top + chart_height - ((temp - min_temp) / temp_range * chart_height)
            points.extend([x, y])
        
        # Draw line
        if len(points) >= 4:
            self.canvas.create_line(
                points,
                fill=self._get_temperature_color(sum(self.temperatures) / len(self.temperatures)),
                width=3,
                smooth=True,
                tags="temp_line"
            )
        
        # Draw data points
        for i, temp in enumerate(self.temperatures):
            x = margin_left + (chart_width * i / (len(self.temperatures) - 1))
            y = margin_top + chart_height - ((temp - min_temp) / temp_range * chart_height)
            
            self.canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill=self._get_temperature_color(temp),
                outline="white",
                width=1,
                tags=f"point_{i}"
            )
    
    def _draw_axes_labels(self, margin_left, margin_top, chart_width, chart_height, min_temp, max_temp):
        """Draw axes labels."""
        # Y-axis labels (temperature)
        num_labels = 5
        for i in range(num_labels + 1):
            temp = min_temp + (max_temp - min_temp) * i / num_labels
            y = margin_top + chart_height - (chart_height * i / num_labels)
            
            self.canvas.create_text(
                margin_left - 10, y,
                text=f"{temp:.0f}°{self.temp_unit}",
                fill=self.text_color,
                font=("Consolas", 9),
                anchor="e"
            )
        
        # X-axis labels (time)
        if self.timestamps:
            num_time_labels = min(4, len(self.timestamps))
            for i in range(num_time_labels):
                idx = int(i * (len(self.timestamps) - 1) / (num_time_labels - 1)) if num_time_labels > 1 else 0
                timestamp = self.timestamps[idx]
                x = margin_left + (chart_width * idx / (len(self.timestamps) - 1)) if len(self.timestamps) > 1 else margin_left + chart_width // 2
                
                time_str = timestamp.strftime("%H:%M")
                self.canvas.create_text(
                    x, margin_top + chart_height + 15,
                    text=time_str,
                    fill=self.text_color,
                    font=("Consolas", 9),
                    anchor="center"
                )
    
    def _get_temperature_color(self, temp: float) -> str:
        """Get color based on temperature.
        
        Args:
            temp: Temperature value
            
        Returns:
            Color string
        """
        # Convert to Celsius for color calculation
        temp_c = temp if self.temp_unit == "C" else (temp - 32) * 5/9
        
        if temp_c < 10:
            return self.temp_colors["cold"]
        elif temp_c < 25:
            return self.temp_colors["moderate"]
        else:
            return self.temp_colors["hot"]
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize event."""
        self.safe_after(50, self._draw_chart)
    
    def _on_mouse_motion(self, event):
        """Handle mouse motion for tooltips."""
        if not self.temperatures:
            return
        
        # Find nearest data point
        width = self.canvas.winfo_width()
        margin_left = 50
        margin_right = 20
        chart_width = width - margin_left - margin_right
        
        if chart_width <= 0:
            return
        
        # Calculate which data point is closest
        relative_x = event.x - margin_left
        if relative_x < 0 or relative_x > chart_width:
            self._hide_tooltip()
            return
        
        point_index = int(relative_x / chart_width * (len(self.temperatures) - 1))
        point_index = max(0, min(point_index, len(self.temperatures) - 1))
        
        if point_index != self.hover_index:
            self.hover_index = point_index
            self._show_tooltip(event.x, event.y, point_index)
    
    def _on_mouse_leave(self, event):
        """Handle mouse leave event."""
        self._hide_tooltip()
        self.hover_index = -1
    
    def _show_tooltip(self, x: int, y: int, index: int):
        """Show tooltip with temperature data."""
        if index < 0 or index >= len(self.temperatures):
            return
        
        temp = self.temperatures[index]
        timestamp = self.timestamps[index] if index < len(self.timestamps) else None
        
        # Create tooltip text
        tooltip_text = f"{temp:.1f}°{self.temp_unit}"
        if timestamp:
            tooltip_text += f"\n{timestamp.strftime('%H:%M')}"
        
        # Position tooltip
        tooltip_x = self.winfo_rootx() + x + 10
        tooltip_y = self.winfo_rooty() + y - 10
        
        self._hide_tooltip()  # Hide existing tooltip
        
        # Create new tooltip window
        self.tooltip_window = tk.Toplevel(self)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{tooltip_x}+{tooltip_y}")
        
        label = tk.Label(
            self.tooltip_window,
            text=tooltip_text,
            background="#2A2A2A",
            foreground="#E0E0E0",
            relief="solid",
            borderwidth=1,
            font=("Consolas", 9)
        )
        label.pack()
    
    def _hide_tooltip(self):
        """Hide tooltip window."""
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except Exception:
                pass
            self.tooltip_window = None
    
    def destroy(self):
        """Clean up when destroying widget."""
        # Cancel scheduled calls
        for call_id in self.scheduled_calls.copy():
            try:
                self.after_cancel(call_id)
            except Exception:
                pass
        self.scheduled_calls.clear()
        
        # Hide tooltip
        self._hide_tooltip()
        
        super().destroy()