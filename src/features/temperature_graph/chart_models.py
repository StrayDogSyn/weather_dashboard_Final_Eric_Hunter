#!/usr/bin/env python3
"""
Chart Data Models and Classes

Contains all data models, dataclasses, and supporting classes for the
advanced temperature chart widget.

Author: Eric Hunter (Cortana Builder Agent)
Version: 3.0.0 (TRAE 2.0 Phase 3)
"""

import customtkinter as ctk
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from .models import (
    TemperatureDataPoint, ChartType, TimeRange, ChartConfig,
    ChartAnalytics, ExportSettings
)


@dataclass
class WeatherEvent:
    """Weather event annotation data."""
    timestamp: datetime
    event_type: str  # 'extreme_heat', 'freezing', 'rain', 'storm'
    temperature: float
    description: str
    icon: str  # emoji
    severity: int  # 1-5 scale


@dataclass
class CityComparison:
    """Multi-city comparison data."""
    city_name: str
    data_points: List[TemperatureDataPoint]
    color: str
    line_style: str
    marker_style: str
    visible: bool = True


class GlassmorphicTooltip(ctk.CTkToplevel):
    """Glassmorphic tooltip window for chart interactions."""
    
    def __init__(self, parent, x: int, y: int, content: str):
        super().__init__(parent)
        
        # Configure window
        self.withdraw()  # Hide initially
        self.overrideredirect(True)  # Remove window decorations
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.95)
        
        # Glassmorphic styling
        self.configure(fg_color=("#F0F0F0", "#2A2A2A"))
        
        # Content frame
        content_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=12,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        content_frame.pack(padx=8, pady=8)
        
        # Content label
        self.content_label = ctk.CTkLabel(
            content_frame,
            text=content,
            font=("Segoe UI", 11),
            text_color=("#FFFFFF", "#E0E0E0"),
            justify="left"
        )
        self.content_label.pack(padx=12, pady=8)
        
        # Position tooltip
        self.geometry(f"+{x}+{y}")
        
        # Auto-hide timer
        self.after(3000, self.hide_tooltip)
    
    def update_content(self, content: str):
        """Update tooltip content."""
        self.content_label.configure(text=content)
    
    def show_tooltip(self):
        """Show tooltip with fade-in effect."""
        self.deiconify()
        self.lift()
    
    def hide_tooltip(self):
        """Hide tooltip."""
        try:
            self.destroy()
        except:
            pass