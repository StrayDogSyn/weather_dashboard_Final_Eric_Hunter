import customtkinter as ctk
import tkinter as tk
from typing import List, Optional


class SimpleTemperatureChart(ctk.CTkFrame):
    """A simple temperature chart widget using customtkinter."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.temperatures: List[float] = []
        self.max_points = 24  # Show 24 hours of data
        
        # Initialize theme colors
        self.chart_color = "#00FF41"
        self.bg_color = "#0D0D0D"
        self.text_color = "#E0E0E0"
        
        # Create canvas for drawing the chart
        self.canvas = tk.Canvas(
            self,
            bg=self.bg_color,
            highlightthickness=0,
            height=200
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind resize event
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        
    def update_data(self, temperatures: List[float]) -> None:
        """Update the chart with new temperature data."""
        self.temperatures = temperatures[-self.max_points:]  # Keep only recent data
        self._draw_chart()
        
    def set_data(self, temperatures: List[float]) -> None:
        """Set the chart data (alias for update_data)."""
        self.update_data(temperatures)
    
    def update_theme(self, theme_data):
        """Update chart colors based on theme data."""
        try:
            # Update canvas background
            self.canvas.configure(bg=theme_data.get("chart_bg", "#0D0D0D"))
            
            # Store theme colors for next redraw
            self.chart_color = theme_data.get("chart_color", "#00FF41")
            self.bg_color = theme_data.get("chart_bg", "#0D0D0D")
            self.text_color = theme_data.get("text", "#E0E0E0")
            
            # Redraw chart with new colors if data exists
            if hasattr(self, 'temp_data') and self.temp_data:
                self._draw_chart()
                
        except Exception as e:
            print(f"Error updating chart theme: {e}")
        
    def _draw_chart(self) -> None:
        """Draw the temperature chart on the canvas."""
        if not self.temperatures:
            return
            
        # Clear canvas
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
            
        # Calculate chart dimensions
        margin = 20
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        if len(self.temperatures) < 2:
            return
            
        # Find min and max temperatures for scaling
        min_temp = min(self.temperatures)
        max_temp = max(self.temperatures)
        temp_range = max_temp - min_temp
        
        if temp_range == 0:
            temp_range = 1  # Avoid division by zero
            
        # Calculate points
        points = []
        for i, temp in enumerate(self.temperatures):
            x = margin + (i / (len(self.temperatures) - 1)) * chart_width
            y = margin + chart_height - ((temp - min_temp) / temp_range) * chart_height
            points.extend([x, y])
            
        # Get theme colors
        chart_color = getattr(self, 'chart_color', '#00FF41')
        text_color = getattr(self, 'text_color', '#E0E0E0')
        
        # Draw the temperature line
        if len(points) >= 4:
            self.canvas.create_line(
                points,
                fill=chart_color,
                width=2,
                smooth=True
            )
            
        # Draw temperature points
        for i in range(0, len(points), 2):
            x, y = points[i], points[i + 1]
            self.canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill=chart_color,
                outline=text_color,
                width=1
            )
            
        # Draw temperature labels
        
        # Min and max temperature labels
        self.canvas.create_text(
            margin, margin + chart_height,
            text=f"{min_temp:.1f}°",
            fill=text_color,
            anchor="w"
        )
        
        self.canvas.create_text(
            margin, margin,
            text=f"{max_temp:.1f}°",
            fill=text_color,
            anchor="w"
        )
        
        # Current temperature (last point)
        if self.temperatures:
            current_temp = self.temperatures[-1]
            self.canvas.create_text(
                width - margin, margin + chart_height // 2,
                text=f"{current_temp:.1f}°",
                fill=text_color,
                anchor="e",
                font=("Arial", 12, "bold")
            )
            
    def _on_canvas_resize(self, event) -> None:
        """Handle canvas resize event."""
        self._draw_chart()
        
    def _get_appearance_mode(self) -> str:
        """Get current appearance mode."""
        return ctk.get_appearance_mode().lower()