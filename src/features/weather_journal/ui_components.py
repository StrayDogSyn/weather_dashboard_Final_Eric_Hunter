#!/usr/bin/env python3
"""
Weather Journal UI Components - Reusable UI components

This module contains UI components specific to the Weather Journal feature
including the rich text editor and other specialized controls.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from typing import List, Callable

from ...utils.logger import LoggerMixin
from ...ui.components.glass import (
    GlassFrame, GlassButton, GlassLabel,
    ComponentSize, GlassEffect
)


class RichTextEditor(GlassFrame, LoggerMixin):
    """
    Rich text editor with glassmorphic styling.

    This class provides a professional text editing interface
    with advanced formatting and weather integration.
    """

    def __init__(self, parent, **kwargs):
        glass_effect = GlassEffect(
            background_alpha=0.05,
            border_alpha=0.1,
            corner_radius=10
        )

        super().__init__(parent, glass_effect=glass_effect, **kwargs)

        # Text formatting state
        self.is_bold = False
        self.is_italic = False
        self.current_font_size = 12

        # Setup UI
        self._setup_editor()

        # Callbacks
        self.content_changed_callbacks: List[Callable] = []

    def _setup_editor(self):
        """Setup the rich text editor interface."""
        # Toolbar
        self._create_toolbar()

        # Text area
        self._create_text_area()

        # Status bar
        self._create_status_bar()

    def _create_toolbar(self):
        """Create formatting toolbar."""
        self.toolbar = GlassFrame(self)
        self.toolbar.pack(fill="x", padx=5, pady=(5, 0))

        # Font controls
        font_frame = GlassFrame(self.toolbar)
        font_frame.pack(side="left", padx=5, pady=5)

        self.bold_button = GlassButton(
            font_frame,
            text="B",
            size=ComponentSize.SMALL,
            command=self._toggle_bold
        )
        self.bold_button.pack(side="left", padx=2)

        self.italic_button = GlassButton(
            font_frame,
            text="I",
            size=ComponentSize.SMALL,
            command=self._toggle_italic
        )
        self.italic_button.pack(side="left", padx=2)

        # Font size
        size_frame = GlassFrame(self.toolbar)
        size_frame.pack(side="left", padx=15, pady=5)

        GlassLabel(size_frame, text="Size:", size=ComponentSize.SMALL).pack(side="left", padx=(0, 5))

        self.size_var = tk.StringVar(value="12")
        self.size_entry = ctk.CTkEntry(
            size_frame,
            textvariable=self.size_var,
            width=50,
            height=28
        )
        self.size_entry.pack(side="left", padx=2)
        self.size_entry.bind("<Return>", self._change_font_size)

        # Insert controls
        insert_frame = GlassFrame(self.toolbar)
        insert_frame.pack(side="right", padx=5, pady=5)

        self.weather_button = GlassButton(
            insert_frame,
            text="🌤️",
            size=ComponentSize.SMALL,
            command=self._insert_weather
        )
        self.weather_button.pack(side="left", padx=2)

        self.timestamp_button = GlassButton(
            insert_frame,
            text="🕒",
            size=ComponentSize.SMALL,
            command=self._insert_timestamp
        )
        self.timestamp_button.pack(side="left", padx=2)

    def _create_text_area(self):
        """Create main text editing area."""
        # Text frame with scrollbar
        text_frame = GlassFrame(self)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Configure text widget with glassmorphic styling
        self.text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 12),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#4A90E2",
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=15
        )

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(text_frame, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind events
        self.text_widget.bind("<KeyRelease>", self._on_text_changed)
        self.text_widget.bind("<Button-1>", self._on_text_changed)

        # Configure text tags for formatting
        self.text_widget.tag_configure("bold", font=("Segoe UI", 12, "bold"))
        self.text_widget.tag_configure("italic", font=("Segoe UI", 12, "italic"))
        self.text_widget.tag_configure("weather", foreground="#4A90E2")
        self.text_widget.tag_configure("timestamp", foreground="#888888")

    def _create_status_bar(self):
        """Create status bar with word count and cursor position."""
        self.status_bar = GlassFrame(self)
        self.status_bar.pack(fill="x", padx=5, pady=(0, 5))

        self.word_count_label = GlassLabel(
            self.status_bar,
            text="Words: 0",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.word_count_label.pack(side="left", padx=10, pady=5)

        self.cursor_label = GlassLabel(
            self.status_bar,
            text="Line: 1, Col: 1",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.cursor_label.pack(side="right", padx=10, pady=5)

    def _toggle_bold(self):
        """Toggle bold formatting."""
        self.is_bold = not self.is_bold

        if self.is_bold:
            self.bold_button.configure(fg_color=("#4A90E2", "#357ABD"))
        else:
            glass_config = self.bold_button._get_glass_button_config()
            self.bold_button.configure(fg_color=glass_config['fg_color'])

        # Apply to selected text
        self._apply_formatting("bold", self.is_bold)

    def _toggle_italic(self):
        """Toggle italic formatting."""
        self.is_italic = not self.is_italic

        if self.is_italic:
            self.italic_button.configure(fg_color=("#4A90E2", "#357ABD"))
        else:
            glass_config = self.italic_button._get_glass_button_config()
            self.italic_button.configure(fg_color=glass_config['fg_color'])

        # Apply to selected text
        self._apply_formatting("italic", self.is_italic)

    def _change_font_size(self, event=None):
        """Change font size."""
        try:
            size = int(self.size_var.get())
            if 8 <= size <= 72:
                self.current_font_size = size
                self._update_font_size()
        except ValueError:
            self.size_var.set(str(self.current_font_size))

    def _update_font_size(self):
        """Update font size for text widget."""
        self.text_widget.configure(font=("Segoe UI", self.current_font_size))

        # Update tag fonts
        self.text_widget.tag_configure("bold", font=("Segoe UI", self.current_font_size, "bold"))
        self.text_widget.tag_configure("italic", font=("Segoe UI", self.current_font_size, "italic"))

    def _apply_formatting(self, tag: str, apply: bool):
        """Apply formatting to selected text."""
        try:
            selection = self.text_widget.tag_ranges(tk.SEL)
            if selection:
                start, end = selection[0], selection[1]
                if apply:
                    self.text_widget.tag_add(tag, start, end)
                else:
                    self.text_widget.tag_remove(tag, start, end)
        except tk.TclError:
            pass  # No selection

    def _insert_weather(self):
        """Insert current weather information."""
        # Placeholder for weather insertion
        weather_text = f"[Weather: {datetime.now().strftime('%I:%M %p')} - Clear, 72°F]"

        cursor_pos = self.text_widget.index(tk.INSERT)
        self.text_widget.insert(cursor_pos, weather_text)

        # Apply weather tag
        start_pos = cursor_pos
        end_pos = self.text_widget.index(f"{cursor_pos} + {len(weather_text)}c")
        self.text_widget.tag_add("weather", start_pos, end_pos)

        self._on_text_changed()

    def _insert_timestamp(self):
        """Insert current timestamp."""
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        cursor_pos = self.text_widget.index(tk.INSERT)
        self.text_widget.insert(cursor_pos, timestamp)

        # Apply timestamp tag
        start_pos = cursor_pos
        end_pos = self.text_widget.index(f"{cursor_pos} + {len(timestamp)}c")
        self.text_widget.tag_add("timestamp", start_pos, end_pos)

        self._on_text_changed()

    def _on_text_changed(self, event=None):
        """Handle text change events."""
        # Update word count
        content = self.get_content()
        word_count = len(content.split()) if content.strip() else 0
        self.word_count_label.configure(text=f"Words: {word_count}")

        # Update cursor position
        cursor_pos = self.text_widget.index(tk.INSERT)
        line, col = cursor_pos.split('.')
        self.cursor_label.configure(text=f"Line: {line}, Col: {int(col) + 1}")

        # Notify callbacks
        for callback in self.content_changed_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in content changed callback: {e}")

    def get_content(self) -> str:
        """Get text content."""
        return self.text_widget.get("1.0", tk.END).strip()

    def set_content(self, content: str):
        """Set text content."""
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", content)
        self._on_text_changed()

    def clear_content(self):
        """Clear all content."""
        self.text_widget.delete("1.0", tk.END)
        self._on_text_changed()

    def add_content_changed_callback(self, callback: Callable):
        """Add callback for content changes."""
        self.content_changed_callbacks.append(callback)