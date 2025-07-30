"""Chart Widgets Mixin for Temperature Chart Component.

This module provides the ChartWidgetsMixin class that handles UI widget creation,
layout management, and widget styling for the temperature chart.
"""

import customtkinter as ctk
from typing import Dict, Any


class ChartWidgetsMixin:
    """Mixin for chart widget creation and layout management."""
    
    def create_widgets(self):
        """Create all UI widgets for the temperature chart."""
        self._create_title_label()
        self._create_timeframe_buttons()
        self._create_export_buttons()
        self._create_chart_frame()
        self._create_tooltip_frame()
        
    def _create_title_label(self):
        """Create the chart title label."""
        self.title_label = ctk.CTkLabel(
            self,
            text="INTERACTIVE TEMPERATURE ANALYSIS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#00ff88"
        )
        
    def _create_timeframe_buttons(self):
        """Create timeframe selection buttons."""
        self.timeframe_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # Timeframe options
        timeframes = [
            ("24H", "24h"),
            ("7D", "7d"),
            ("30D", "30d")
        ]
        
        self.timeframe_buttons = {}
        
        for i, (display_text, value) in enumerate(timeframes):
            button = ctk.CTkButton(
                self.timeframe_frame,
                text=display_text,
                width=60,
                height=30,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#2a2a2a" if value != self.current_timeframe else "#00ff88",
                hover_color="#3a3a3a",
                text_color="#ffffff" if value != self.current_timeframe else "#000000",
                command=lambda tf=value: self.change_timeframe(tf)
            )
            button.grid(row=0, column=i, padx=5)
            self.timeframe_buttons[value] = button
            
    def _create_export_buttons(self):
        """Create export functionality buttons."""
        self.export_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # PNG Export button
        self.png_button = ctk.CTkButton(
            self.export_frame,
            text="📊 PNG",
            width=80,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            text_color="#00ff88",
            command=lambda: self.export_chart('png')
        )
        self.png_button.grid(row=0, column=0, padx=5)
        
        # PDF Export button
        self.pdf_button = ctk.CTkButton(
            self.export_frame,
            text="📄 PDF",
            width=80,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            text_color="#00ff88",
            command=lambda: self.export_chart('pdf')
        )
        self.pdf_button.grid(row=0, column=1, padx=5)
        
    def _create_chart_frame(self):
        """Create the main chart container frame."""
        self.chart_frame = ctk.CTkFrame(
            self,
            fg_color="#1a1a1a",
            corner_radius=10,
            border_width=1,
            border_color="#00ff88"
        )
        
    def _create_tooltip_frame(self):
        """Create the tooltip frame for interactive features."""
        self.tooltip_frame = ctk.CTkFrame(
            self,
            fg_color="#2a2a2a",
            corner_radius=8,
            border_width=1,
            border_color="#00ff88"
        )
        
        # Tooltip label
        self.tooltip_label = ctk.CTkLabel(
            self.tooltip_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#00ff88",
            justify="left"
        )
        self.tooltip_label.pack(padx=10, pady=5)
        
        # Initially hide tooltip
        self.tooltip_frame.place_forget()
        
    def setup_layout(self):
        """Setup the layout of all widgets."""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        # Place title
        self.title_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")
        
        # Create control panel frame
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.grid(row=1, column=0, pady=5, sticky="ew")
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        
        # Place timeframe buttons (left side)
        self.timeframe_frame.grid(row=0, column=0, sticky="w", padx=(10, 0))
        
        # Place export buttons (right side)
        self.export_frame.grid(row=0, column=1, sticky="e", padx=(0, 10))
        
        # Place chart frame
        self.chart_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        
    def update_timeframe_buttons(self, active_timeframe: str):
        """Update the appearance of timeframe buttons."""
        for timeframe, button in self.timeframe_buttons.items():
            if timeframe == active_timeframe:
                button.configure(
                    fg_color="#00ff88",
                    text_color="#000000"
                )
            else:
                button.configure(
                    fg_color="#2a2a2a",
                    text_color="#ffffff"
                )
                
    def show_tooltip(self, x: int, y: int, content: str):
        """Show tooltip at specified coordinates."""
        self.tooltip_label.configure(text=content)
        
        # Position tooltip
        tooltip_x = x + 10
        tooltip_y = y - 30
        
        # Ensure tooltip stays within widget bounds
        widget_width = self.winfo_width()
        widget_height = self.winfo_height()
        
        if tooltip_x + 200 > widget_width:
            tooltip_x = x - 210
        if tooltip_y < 0:
            tooltip_y = y + 10
            
        self.tooltip_frame.place(x=tooltip_x, y=tooltip_y)
        
    def hide_tooltip(self):
        """Hide the tooltip."""
        self.tooltip_frame.place_forget()
        
    def show_notification(self, message: str, notification_type: str = "info"):
        """Show a temporary notification message."""
        # Create notification frame
        notification_frame = ctk.CTkFrame(
            self,
            fg_color="#2a2a2a" if notification_type == "info" else "#ff4444",
            corner_radius=8,
            border_width=1,
            border_color="#00ff88" if notification_type == "info" else "#ff6666"
        )
        
        # Notification label
        notification_label = ctk.CTkLabel(
            notification_frame,
            text=message,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00ff88" if notification_type == "info" else "#ffffff"
        )
        notification_label.pack(padx=15, pady=10)
        
        # Position notification
        notification_frame.place(
            relx=0.5,
            rely=0.1,
            anchor="center"
        )
        
        # Auto-hide after 3 seconds
        self.after(3000, notification_frame.destroy)
        
    def get_widget_dimensions(self) -> Dict[str, Any]:
        """Get current widget dimensions for calculations."""
        return {
            'width': self.winfo_width(),
            'height': self.winfo_height(),
            'chart_width': self.chart_frame.winfo_width(),
            'chart_height': self.chart_frame.winfo_height()
        }
        
    def update_widget_styling(self, theme: str = "dark"):
        """Update widget styling based on theme."""
        if theme == "dark":
            colors = {
                'bg': '#1a1a1a',
                'fg': '#2a2a2a',
                'accent': '#00ff88',
                'text': '#ffffff'
            }
        else:
            colors = {
                'bg': '#ffffff',
                'fg': '#f0f0f0',
                'accent': '#007755',
                'text': '#000000'
            }
            
        # Update chart frame
        self.chart_frame.configure(
            fg_color=colors['bg'],
            border_color=colors['accent']
        )
        
        # Update tooltip frame
        self.tooltip_frame.configure(
            fg_color=colors['fg'],
            border_color=colors['accent']
        )
        
        # Update tooltip label
        self.tooltip_label.configure(text_color=colors['accent'])