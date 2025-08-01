"""Chart Widgets Mixin for Temperature Chart Component.

This module provides the ChartWidgetsMixin class that handles UI widget creation,
layout management, and widget styling for the temperature chart.
"""

from typing import Any, Dict

import customtkinter as ctk


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
            text_color="#00ff88",
        )

    def _create_timeframe_buttons(self):
        """Create glassmorphic timeframe selection buttons with enhanced styling."""
        self.timeframe_frame = ctk.CTkFrame(self, fg_color="transparent")

        # Enhanced glassmorphic button configuration
        button_config = {
            "width": 70,
            "height": 36,
            "corner_radius": 12,
            "font": ctk.CTkFont(size=12, weight="bold"),
            "border_width": 2,
            "border_color": "#00ff88",
            "hover_color": "#1a4d3a",
            "text_color": "#ffffff",
            "fg_color": "#1a1a1a",
        }

        # Timeframe options
        timeframes = [("24H", "24h"), ("7D", "7d"), ("30D", "30d")]

        self.timeframe_buttons = {}

        for i, (display_text, value) in enumerate(timeframes):
            button = ctk.CTkButton(
                self.timeframe_frame,
                text=display_text,
                command=lambda tf=value: self._handle_timeframe_click(tf),
                **button_config
            )
            button.grid(row=0, column=i, padx=3)
            self.timeframe_buttons[value] = button

            # Add glassmorphic hover effects
            self._add_button_hover_effects(button)

        # Set initial active button
        self.update_timeframe_buttons(self.current_timeframe)

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
            command=self._export_png,
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
            command=self._export_pdf,
        )
        self.pdf_button.grid(row=0, column=1, padx=5)

    def _create_chart_frame(self):
        """Create the main chart container frame."""
        self.chart_frame = ctk.CTkFrame(
            self, fg_color="#1a1a1a", corner_radius=10, border_width=1, border_color="#00ff88"
        )

    def _create_tooltip_frame(self):
        """Create enhanced glassmorphic tooltip frame for interactive features."""
        self.tooltip_frame = ctk.CTkFrame(
            self, fg_color="#1a1a1a", corner_radius=12, border_width=2, border_color="#00ff88"
        )

        # Enhanced tooltip label with better typography
        self.tooltip_label = ctk.CTkLabel(
            self.tooltip_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="normal"),
            text_color="#00ff88",
            justify="left",
        )
        self.tooltip_label.pack(padx=12, pady=8)

        # Add trend indicator label
        self.trend_label = ctk.CTkLabel(
            self.tooltip_frame,
            text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#ffffff",
            justify="center",
        )
        self.trend_label.pack(padx=12, pady=(0, 8))

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
        """Update the appearance of timeframe buttons with glassmorphic styling."""
        for timeframe, button in self.timeframe_buttons.items():
            if timeframe == active_timeframe:
                button.configure(
                    fg_color="#00ff88",
                    text_color="#000000",
                    border_color="#00ff88",
                    hover_color="#00cc66",
                )
            else:
                button.configure(
                    fg_color="#1a1a1a",
                    text_color="#ffffff",
                    border_color="#00ff88",
                    hover_color="#1a4d3a",
                )

    def show_tooltip(self, x: int, y: int, content: str, trend_info: str = ""):
        """Show enhanced tooltip with trend analysis at specified coordinates."""
        self.tooltip_label.configure(text=content)
        self.trend_label.configure(text=trend_info)

        # Position tooltip with improved positioning logic
        tooltip_x = x + 15
        tooltip_y = y - 40

        # Ensure tooltip stays within widget bounds
        widget_width = self.winfo_width()
        widget_height = self.winfo_height()

        # Adjust horizontal position
        if tooltip_x + 220 > widget_width:
            tooltip_x = x - 235
        if tooltip_x < 0:
            tooltip_x = 10

        # Adjust vertical position
        if tooltip_y < 0:
            tooltip_y = y + 15
        if tooltip_y + 80 > widget_height:
            tooltip_y = widget_height - 90

        self.tooltip_frame.place(x=tooltip_x, y=tooltip_y)

        # Add fade-in animation effect
        self._animate_tooltip_show()

    def hide_tooltip(self):
        """Hide the tooltip with fade-out animation."""
        self._animate_tooltip_hide()

    def _animate_tooltip_show(self):
        """Animate tooltip appearance."""
        # Simple fade-in effect by adjusting alpha
        self.tooltip_frame.configure(fg_color="#1a1a1a")

    def _animate_tooltip_hide(self):
        """Animate tooltip disappearance."""

        # Hide tooltip after brief delay
        def hide_tooltip():
            self.tooltip_frame.place_forget()

        self.after(50, hide_tooltip)

    def _add_button_hover_effects(self, button):
        """Add glassmorphic hover effects to buttons."""

        def on_enter(event):
            if button.cget("fg_color") != "#00ff88":  # Not active button
                button.configure(fg_color="#2a2a2a")

        def on_leave(event):
            if button.cget("fg_color") != "#00ff88":  # Not active button
                button.configure(fg_color="#1a1a1a")

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def _handle_timeframe_click(self, timeframe: str):
        """Handle timeframe button click with animation."""
        # Add click animation
        button = self.timeframe_buttons[timeframe]
        button.cget("fg_color")

        # Brief flash effect
        button.configure(fg_color="#00cc66")

        def change_timeframe_callback():
            self.change_timeframe(timeframe)

        self.after(100, change_timeframe_callback)

    def show_notification(self, message: str, notification_type: str = "info"):
        """Show a temporary notification message."""
        # Create notification frame
        notification_frame = ctk.CTkFrame(
            self,
            fg_color="#2a2a2a" if notification_type == "info" else "#ff4444",
            corner_radius=8,
            border_width=1,
            border_color="#00ff88" if notification_type == "info" else "#ff6666",
        )

        # Notification label
        notification_label = ctk.CTkLabel(
            notification_frame,
            text=message,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00ff88" if notification_type == "info" else "#ffffff",
        )
        notification_label.pack(padx=15, pady=10)

        # Position notification
        notification_frame.place(relx=0.5, rely=0.1, anchor="center")

        # Auto-hide after 3 seconds
        self.after(3000, notification_frame.destroy)

    def get_widget_dimensions(self) -> Dict[str, Any]:
        """Get current widget dimensions for calculations."""
        return {
            "width": self.winfo_width(),
            "height": self.winfo_height(),
            "chart_width": self.chart_frame.winfo_width(),
            "chart_height": self.chart_frame.winfo_height(),
        }

    def update_widget_styling(self, theme: str = "dark"):
        """Update widget styling based on theme."""
        if theme == "dark":
            colors = {"bg": "#1a1a1a", "fg": "#2a2a2a", "accent": "#00ff88", "text": "#ffffff"}
        else:
            colors = {"bg": "#ffffff", "fg": "#f0f0f0", "accent": "#007755", "text": "#000000"}

        # Update chart frame
        self.chart_frame.configure(fg_color=colors["bg"], border_color=colors["accent"])

        # Update tooltip frame
        self.tooltip_frame.configure(fg_color=colors["fg"], border_color=colors["accent"])

        # Update tooltip label
        self.tooltip_label.configure(text_color=colors["accent"])

    def _export_png(self):
        """Helper method to export chart as PNG."""
        self.export_chart("png")

    def _export_pdf(self):
        """Helper method to export chart as PDF."""
        self.export_chart("pdf")
