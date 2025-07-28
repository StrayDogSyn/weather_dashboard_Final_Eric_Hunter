#!/usr/bin/env python3
"""
Chart UI Components

Contains all UI components, controls, and interface elements for the
advanced temperature chart widget.

Author: Eric Hunter (Cortana Builder Agent)
Version: 3.0.0 (TRAE 2.0 Phase 3)
"""

import customtkinter as ctk
from typing import Callable, Optional
from ...ui.components.glass import GlassFrame, GlassButton


class ChartUIComponents:
    """Manages all UI components for the chart widget."""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.header_frame: Optional[GlassFrame] = None
        self.chart_container: Optional[GlassFrame] = None
        self.loading_overlay: Optional[GlassFrame] = None
        self.toolbar_frame: Optional[GlassFrame] = None
        
        # Control references
        self.time_range_menu: Optional[ctk.CTkOptionMenu] = None
        self.chart_type_menu: Optional[ctk.CTkOptionMenu] = None
        self.annotations_switch: Optional[ctk.CTkSwitch] = None
        self.trends_switch: Optional[ctk.CTkSwitch] = None
        self.export_button: Optional[GlassButton] = None
        self.refresh_button: Optional[GlassButton] = None
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.loading_label: Optional[ctk.CTkLabel] = None
    
    def setup_ui(self):
        """Setup all UI components."""
        self._setup_header()
        self._setup_chart_container()
        self._setup_loading_overlay()
    
    def _setup_header(self):
        """Setup header frame with controls."""
        self.header_frame = GlassFrame(
            self.parent,
            height=80,
            fg_color=("#FAFAFA", "#1A1A1A"),
            corner_radius=15
        )
        self.header_frame.pack(fill="x", padx=15, pady=(15, 10))
        self.header_frame.pack_propagate(False)
        
        self._setup_left_controls()
        self._setup_right_controls()
    
    def _setup_left_controls(self):
        """Setup left side controls (time range, chart type)."""
        left_controls = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        left_controls.pack(side="left", fill="y", padx=15, pady=10)
        
        # Time range selector
        ctk.CTkLabel(
            left_controls,
            text="Time Range:",
            font=("Segoe UI", 12, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        ).pack(side="left", padx=(0, 8))
        
        self.time_range_menu = ctk.CTkOptionMenu(
            left_controls,
            values=["24h", "7d", "30d", "90d", "custom"],
            command=self.parent._on_time_range_change,
            width=100,
            height=32,
            corner_radius=8,
            fg_color=("#F0F0F0", "#333333"),
            button_color=("#E8E8E8", "#444444"),
            button_hover_color=("#E0E0E0", "#555555"),
            dropdown_fg_color=("#F0F0F0", "#333333")
        )
        self.time_range_menu.pack(side="left", padx=(0, 15))
        self.time_range_menu.set("7d")
        
        # Chart type selector
        ctk.CTkLabel(
            left_controls,
            text="Chart Type:",
            font=("Segoe UI", 12, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        ).pack(side="left", padx=(0, 8))
        
        self.chart_type_menu = ctk.CTkOptionMenu(
            left_controls,
            values=["Line", "Area", "Bar", "Scatter", "Candlestick"],
            command=self.parent._on_chart_type_change,
            width=120,
            height=32,
            corner_radius=8,
            fg_color=("#F0F0F0", "#333333"),
            button_color=("#E8E8E8", "#444444"),
            button_hover_color=("#E0E0E0", "#555555"),
            dropdown_fg_color=("#F0F0F0", "#333333")
        )
        self.chart_type_menu.pack(side="left", padx=(0, 15))
        self.chart_type_menu.set("Line")
    
    def _setup_right_controls(self):
        """Setup right side controls (switches, buttons)."""
        right_controls = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_controls.pack(side="right", fill="y", padx=15, pady=10)
        
        # Toggle switches
        self.annotations_switch = ctk.CTkSwitch(
            right_controls,
            text="Annotations",
            command=self.parent._toggle_annotations,
            width=50,
            height=24,
            switch_width=40,
            switch_height=20,
            corner_radius=10,
            fg_color=("#F0F0F0", "#333333"),
            progress_color=("#4A90E2", "#4A90E2"),
            button_color=("#FFFFFF", "#CCCCCC"),
            button_hover_color=("#F0F0F0", "#DDDDDD")
        )
        self.annotations_switch.pack(side="left", padx=(0, 10))
        self.annotations_switch.select()
        
        self.trends_switch = ctk.CTkSwitch(
            right_controls,
            text="Trends",
            command=self.parent._toggle_trends,
            width=50,
            height=24,
            switch_width=40,
            switch_height=20,
            corner_radius=10,
            fg_color=("#F0F0F0", "#333333"),
            progress_color=("#50C878", "#50C878"),
            button_color=("#FFFFFF", "#CCCCCC"),
            button_hover_color=("#F0F0F0", "#DDDDDD")
        )
        self.trends_switch.pack(side="left", padx=(0, 10))
        self.trends_switch.select()
        
        # Export button
        self.export_button = GlassButton(
            right_controls,
            text="📊 Export",
            command=self.parent._show_export_dialog,
            width=80,
            height=32,
            corner_radius=8
        )
        self.export_button.pack(side="left", padx=(0, 10))
        
        # Refresh button
        self.refresh_button = GlassButton(
            right_controls,
            text="🔄 Refresh",
            command=self.parent.refresh_chart,
            width=80,
            height=32,
            corner_radius=8
        )
        self.refresh_button.pack(side="left")
    
    def _setup_chart_container(self):
        """Setup chart container frame."""
        self.chart_container = GlassFrame(
            self.parent,
            fg_color=("#FCFCFC", "#1A1A1A"),
            corner_radius=15,
            border_width=1,
            border_color=("#F0F0F0", "#404040")
        )
        self.chart_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    def _setup_loading_overlay(self):
        """Setup loading overlay components."""
        self.loading_overlay = GlassFrame(
            self.chart_container,
            fg_color=("#2A2A2A", "#1A1A1A"),
            corner_radius=15
        )
        
        self.loading_label = ctk.CTkLabel(
            self.loading_overlay,
            text="🔄 Loading chart data...",
            font=("Segoe UI", 16, "bold"),
            text_color=("#FFFFFF", "#E0E0E0")
        )
        self.loading_label.pack(expand=True)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.loading_overlay,
            width=200,
            height=8,
            corner_radius=4,
            fg_color=("#F0F0F0", "#333333"),
            progress_color=("#4A90E2", "#4A90E2")
        )
        self.progress_bar.pack(pady=(10, 0))
        self.progress_bar.set(0)
    
    def create_custom_toolbar(self):
        """Create custom glassmorphic navigation toolbar."""
        self.toolbar_frame = GlassFrame(
            self.chart_container,
            height=40,
            fg_color=("#FAFAFA", "#1A1A1A"),
            corner_radius=10
        )
        self.toolbar_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.toolbar_frame.pack_propagate(False)
        
        # Zoom controls
        zoom_frame = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        zoom_frame.pack(side="left", fill="y", padx=10, pady=5)
        
        zoom_in_btn = GlassButton(
            zoom_frame,
            text="🔍+",
            command=self.parent._zoom_in,
            width=40,
            height=30,
            corner_radius=6
        )
        zoom_in_btn.pack(side="left", padx=(0, 5))
        
        zoom_out_btn = GlassButton(
            zoom_frame,
            text="🔍-",
            command=self.parent._zoom_out,
            width=40,
            height=30,
            corner_radius=6
        )
        zoom_out_btn.pack(side="left", padx=(0, 5))
        
        reset_zoom_btn = GlassButton(
            zoom_frame,
            text="🏠",
            command=self.parent._reset_zoom,
            width=40,
            height=30,
            corner_radius=6
        )
        reset_zoom_btn.pack(side="left", padx=(0, 5))
        
        # Pan controls
        pan_frame = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        pan_frame.pack(side="left", fill="y", padx=10, pady=5)
        
        pan_left_btn = GlassButton(
            pan_frame,
            text="⬅️",
            command=self.parent._pan_left,
            width=40,
            height=30,
            corner_radius=6
        )
        pan_left_btn.pack(side="left", padx=(0, 5))
        
        pan_right_btn = GlassButton(
            pan_frame,
            text="➡️",
            command=self.parent._pan_right,
            width=40,
            height=30,
            corner_radius=6
        )
        pan_right_btn.pack(side="left")
        
        # Info and help
        info_frame = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        info_frame.pack(side="right", fill="y", padx=10, pady=5)
        
        help_btn = GlassButton(
            info_frame,
            text="❓",
            command=self.parent._show_help_dialog,
            width=40,
            height=30,
            corner_radius=6
        )
        help_btn.pack(side="left")
    
    def show_loading(self, message: str = "Loading chart data..."):
        """Show loading overlay."""
        self.loading_label.configure(text=f"🔄 {message}")
        self.loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.progress_bar.set(0)
    
    def hide_loading(self):
        """Hide loading overlay."""
        self.loading_overlay.place_forget()
    
    def update_progress(self, value: float):
        """Update progress bar value (0.0 to 1.0)."""
        if self.progress_bar:
            self.progress_bar.set(value)
    
    def get_chart_container(self) -> GlassFrame:
        """Get the chart container frame."""
        return self.chart_container