#!/usr/bin/env python3
"""
Weather Journal Widget - Main UI component

This module contains the main Weather Journal widget that provides
the complete journal interface with rich text editing, search, and weather correlation.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from typing import Dict, List, Optional, Any

from ...utils.logger import LoggerMixin
from ...ui.components.glass import (
    GlassFrame, GlassButton, GlassLabel, GlassEntry,
    ComponentSize, create_glass_card, GlassEffect
)
from ...ui.theme_manager import ThemeManager
from ...services.weather_service import WeatherData
from ...core.database_manager import DatabaseManager
from .models import JournalEntry, EntryMood, SearchFilter
from .journal_controller import JournalController
from .ui_components import RichTextEditor
from .utils import format_date_for_display, truncate_text, extract_weather_info_from_entry


class WeatherJournalWidget(GlassFrame, LoggerMixin):
    """
    Weather Journal Widget - Main journal interface.

    This class implements the complete weather journal feature
    with rich text editing, search, and weather correlation.
    """

    def __init__(
        self,
        parent,
        database_manager: DatabaseManager,
        **kwargs
    ):
        glass_effect = GlassEffect(
            background_alpha=0.05,
            border_alpha=0.1,
            corner_radius=15
        )

        super().__init__(parent, glass_effect=glass_effect, size=ComponentSize.EXTRA_LARGE, **kwargs)

        # Core dependencies
        self.database_manager = database_manager
        self.controller = JournalController(database_manager)
        self.theme_manager = ThemeManager()

        # UI components
        self.sidebar: Optional[GlassFrame] = None
        self.editor_panel: Optional[GlassFrame] = None
        self.entry_list: Optional[ctk.CTkScrollableFrame] = None
        self.editor: Optional[RichTextEditor] = None

        # UI variables
        self.title_var = tk.StringVar()
        self.mood_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="all")
        self.auto_save_var = tk.BooleanVar(value=True)

        # UI labels for status
        self.entry_info_label: Optional[GlassLabel] = None
        self.save_status_label: Optional[GlassLabel] = None
        self.stats_label: Optional[GlassLabel] = None
        self.weather_info_label: Optional[GlassLabel] = None

        # Auto-save timer
        self._auto_save_timer = None

        # Setup controller callbacks
        self._setup_controller_callbacks()

        # Initialize UI
        self._setup_ui()

        # Load initial state
        self.controller.create_new_entry()

        self.logger.info("Weather Journal Widget initialized")

    def _setup_controller_callbacks(self):
        """Setup callbacks from controller to update UI."""
        self.controller.add_entry_updated_callback(self._on_entry_updated)
        self.controller.add_entries_changed_callback(self._on_entries_changed)
        self.controller.add_save_status_callback(self._on_save_status_updated)

    def _setup_ui(self):
        """Setup the journal user interface."""
        # Configure main layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar
        self._create_sidebar()

        # Create editor panel
        self._create_editor_panel()

        self.logger.debug("Journal UI setup completed")

    def _create_sidebar(self):
        """Create the journal sidebar with entry list and controls."""
        self.sidebar = GlassFrame(
            self,
            glass_effect=GlassEffect(
                background_alpha=0.1,
                border_alpha=0.2,
                corner_radius=15
            )
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.sidebar.configure(width=300)

        # Header
        header_frame = GlassFrame(self.sidebar)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_label = GlassLabel(
            header_frame,
            text="Weather Journal",
            text_style="heading",
            size=ComponentSize.LARGE
        )
        title_label.pack(side="left")

        # Control buttons
        controls_frame = GlassFrame(self.sidebar)
        controls_frame.pack(fill="x", padx=10, pady=5)

        self.new_entry_button = GlassButton(
            controls_frame,
            text="+ New Entry",
            size=ComponentSize.MEDIUM,
            command=self._create_new_entry
        )
        self.new_entry_button.pack(fill="x", pady=2)

        # Search frame
        search_frame = GlassFrame(self.sidebar)
        search_frame.pack(fill="x", padx=10, pady=5)

        self.search_entry = GlassEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search entries...",
            size=ComponentSize.MEDIUM
        )
        self.search_entry.pack(fill="x", pady=2)
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Filter options
        filter_frame = GlassFrame(search_frame)
        filter_frame.pack(fill="x", pady=(5, 0))

        filter_options = [
            ("All", "all"),
            ("Title", "title"),
            ("Content", "content"),
            ("Mood", "mood"),
            ("Weather", "weather")
        ]

        for i, (text, value) in enumerate(filter_options):
            radio = ctk.CTkRadioButton(
                filter_frame,
                text=text,
                variable=self.filter_var,
                value=value,
                command=self._on_filter_changed
            )
            radio.grid(row=i//3, column=i%3, sticky="w", padx=2, pady=1)

        # Entry list
        list_frame = GlassFrame(self.sidebar)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.entry_list = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="transparent"
        )
        self.entry_list.pack(fill="both", expand=True, padx=5, pady=5)

        # Statistics panel
        stats_frame = GlassFrame(self.sidebar)
        stats_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.stats_label = GlassLabel(
            stats_frame,
            text="Total Entries: 0",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.stats_label.pack(pady=5)

    def _create_editor_panel(self):
        """Create the main editor panel."""
        self.editor_panel = GlassFrame(
            self,
            glass_effect=GlassEffect(
                background_alpha=0.03,
                border_alpha=0.1,
                corner_radius=15
            )
        )
        self.editor_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        # Editor header
        self._create_editor_header()

        # Rich text editor
        self.editor = RichTextEditor(self.editor_panel)
        self.editor.pack(fill="both", expand=True, padx=10, pady=5)
        self.editor.add_content_changed_callback(self._on_content_changed)

        # Entry metadata panel
        self._create_metadata_panel()

        # Action buttons
        self._create_action_buttons()

    def _create_editor_header(self):
        """Create editor header with title and metadata."""
        header_frame = GlassFrame(self.editor_panel)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Title entry
        title_frame = GlassFrame(header_frame)
        title_frame.pack(fill="x", pady=5)

        GlassLabel(
            title_frame,
            text="Title:",
            size=ComponentSize.MEDIUM
        ).pack(side="left", padx=(0, 10))

        self.title_entry = GlassEntry(
            title_frame,
            textvariable=self.title_var,
            placeholder_text="Enter entry title...",
            size=ComponentSize.LARGE
        )
        self.title_entry.pack(fill="x", side="left", expand=True)
        self.title_entry.bind("<KeyRelease>", self._on_title_changed)

        # Entry info
        info_frame = GlassFrame(header_frame)
        info_frame.pack(fill="x", pady=2)

        self.entry_info_label = GlassLabel(
            info_frame,
            text="New Entry",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.entry_info_label.pack(side="left")

        self.save_status_label = GlassLabel(
            info_frame,
            text="",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.save_status_label.pack(side="right")

    def _create_metadata_panel(self):
        """Create metadata panel for mood, tags, and weather."""
        metadata_frame = GlassFrame(self.editor_panel)
        metadata_frame.pack(fill="x", padx=10, pady=5)

        # Mood selection
        mood_frame = GlassFrame(metadata_frame)
        mood_frame.pack(side="left", padx=5, pady=5)

        GlassLabel(
            mood_frame,
            text="Mood:",
            size=ComponentSize.SMALL
        ).pack(side="left", padx=(0, 5))

        self.mood_combo = ctk.CTkComboBox(
            mood_frame,
            variable=self.mood_var,
            values=[mood.value for mood in EntryMood],
            width=100,
            command=self._on_mood_changed
        )
        self.mood_combo.pack(side="left", padx=2)

        # Tags entry
        tags_frame = GlassFrame(metadata_frame)
        tags_frame.pack(side="left", padx=15, pady=5)

        GlassLabel(
            tags_frame,
            text="Tags:",
            size=ComponentSize.SMALL
        ).pack(side="left", padx=(0, 5))

        self.tags_entry = GlassEntry(
            tags_frame,
            textvariable=self.tags_var,
            placeholder_text="tag1, tag2, tag3",
            size=ComponentSize.MEDIUM,
            width=200
        )
        self.tags_entry.pack(side="left", padx=2)
        self.tags_entry.bind("<KeyRelease>", self._on_tags_changed)

        # Weather info
        weather_frame = GlassFrame(metadata_frame)
        weather_frame.pack(side="right", padx=5, pady=5)

        self.weather_info_label = GlassLabel(
            weather_frame,
            text="Weather: Not available",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.weather_info_label.pack(side="left")

        self.refresh_weather_button = GlassButton(
            weather_frame,
            text="🔄",
            size=ComponentSize.SMALL,
            command=self._refresh_weather
        )
        self.refresh_weather_button.pack(side="left", padx=(5, 0))

    def _create_action_buttons(self):
        """Create action buttons for save, delete, export."""
        action_frame = GlassFrame(self.editor_panel)
        action_frame.pack(fill="x", padx=10, pady=(5, 10))

        # Left side buttons
        left_frame = GlassFrame(action_frame)
        left_frame.pack(side="left")

        self.save_button = GlassButton(
            left_frame,
            text="💾 Save",
            size=ComponentSize.MEDIUM,
            command=self._save_entry
        )
        self.save_button.pack(side="left", padx=2)

        self.auto_save_check = ctk.CTkCheckBox(
            left_frame,
            text="Auto-save",
            variable=self.auto_save_var,
            command=self._on_auto_save_changed
        )
        self.auto_save_check.pack(side="left", padx=10)

        # Right side buttons
        right_frame = GlassFrame(action_frame)
        right_frame.pack(side="right")

        self.export_button = GlassButton(
            right_frame,
            text="📤 Export",
            size=ComponentSize.MEDIUM,
            command=self._export_entry
        )
        self.export_button.pack(side="left", padx=2)

        self.delete_button = GlassButton(
            right_frame,
            text="🗑️ Delete",
            size=ComponentSize.MEDIUM,
            command=self._delete_entry
        )
        self.delete_button.pack(side="left", padx=2)

        self.favorite_button = GlassButton(
            right_frame,
            text="⭐",
            size=ComponentSize.MEDIUM,
            command=self._toggle_favorite
        )
        self.favorite_button.pack(side="left", padx=2)

    # Controller Event Handlers

    def _on_entry_updated(self):
        """Handle entry updated event from controller."""
        entry = self.controller.get_current_entry()
        if entry:
            # Update UI with entry data
            self.title_var.set(entry.title or "")
            self.editor.set_content(entry.content or "")
            
            # Update metadata
            if entry.mood:
                self.mood_var.set(entry.mood.value)
            else:
                self.mood_var.set("")
            
            if entry.tags:
                self.tags_var.set(", ".join(entry.tags))
            else:
                self.tags_var.set("")
            
            # Update info displays
            self._update_editor_info()
            self._update_weather_display()
            self._update_favorite_button()

    def _on_entries_changed(self):
        """Handle entries list changed event from controller."""
        self._update_entry_list()
        self._update_statistics()

    def _on_save_status_updated(self, status: str):
        """Handle save status updated event from controller."""
        timestamp = datetime.now().strftime("%I:%M %p")
        self.save_status_label.configure(text=f"{status} at {timestamp}")

    # UI Event Handlers

    def _create_new_entry(self):
        """Create a new journal entry."""
        self.controller.create_new_entry()

    def _save_entry(self):
        """Save current journal entry."""
        self.controller.save_current_entry(
            self.title_var.get(),
            self.editor.get_content(),
            self.mood_var.get(),
            self.tags_var.get()
        )

    def _delete_entry(self):
        """Delete current journal entry."""
        self.controller.delete_current_entry()

    def _export_entry(self):
        """Export current entry to file."""
        self.controller.export_current_entry()

    def _toggle_favorite(self):
        """Toggle favorite status of current entry."""
        if self.controller.toggle_favorite():
            self._update_favorite_button()

    def _refresh_weather(self):
        """Refresh current weather data."""
        # This would be connected to the weather service in a real implementation
        self._update_weather_display()

    def _on_content_changed(self):
        """Handle content change events."""
        self.controller.mark_content_changed()
        
        # Auto-save if enabled
        if self.auto_save_var.get():
            # Debounce auto-save
            if self._auto_save_timer:
                self.after_cancel(self._auto_save_timer)
            
            self._auto_save_timer = self.after(2000, self._auto_save)

    def _on_title_changed(self, event=None):
        """Handle title change events."""
        self._on_content_changed()

    def _on_mood_changed(self, value=None):
        """Handle mood change events."""
        self._on_content_changed()

    def _on_tags_changed(self, event=None):
        """Handle tags change events."""
        self._on_content_changed()

    def _on_auto_save_changed(self):
        """Handle auto-save setting change."""
        self.controller.set_auto_save(self.auto_save_var.get())

    def _auto_save(self):
        """Perform auto-save."""
        if self.controller.has_unsaved_changes:
            self._save_entry()

    def _on_search_changed(self, event=None):
        """Handle search input changes."""
        search_query = self.search_var.get().strip()
        
        if not search_query:
            # Show all entries
            entries = self.controller.get_all_entries()
        else:
            # Perform search
            filter_type = SearchFilter(self.filter_var.get())
            entries = self.controller.search_entries(search_query, filter_type)
        
        self._update_entry_list(entries)

    def _on_filter_changed(self):
        """Handle filter change events."""
        self._on_search_changed()

    def _select_entry(self, entry_id: int):
        """Select and load a journal entry for editing."""
        self.controller.load_entry(entry_id)

    # UI Update Methods

    def _update_entry_list(self, entries: Optional[List[JournalEntry]] = None):
        """Update the entry list display."""
        # Clear existing entries
        for widget in self.entry_list.winfo_children():
            widget.destroy()

        # Use provided entries or all entries
        display_entries = entries if entries is not None else self.controller.get_all_entries()

        # Create entry widgets
        for entry in display_entries:
            self._create_entry_widget(entry)

    def _create_entry_widget(self, entry: JournalEntry):
        """Create widget for a single journal entry."""
        entry_frame = GlassFrame(
            self.entry_list,
            glass_effect=GlassEffect(
                background_alpha=0.1,
                border_alpha=0.2,
                corner_radius=8
            )
        )
        entry_frame.pack(fill="x", pady=2)

        # Entry header
        header_frame = GlassFrame(entry_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Title and favorite
        title_text = entry.title or "Untitled Entry"
        if entry.is_favorite:
            title_text = f"⭐ {title_text}"

        title_label = GlassLabel(
            header_frame,
            text=title_text,
            text_style="normal",
            size=ComponentSize.MEDIUM
        )
        title_label.pack(side="left")

        # Mood
        if entry.mood:
            mood_label = GlassLabel(
                header_frame,
                text=entry.mood.value,
                size=ComponentSize.MEDIUM
            )
            mood_label.pack(side="right")

        # Entry info
        info_frame = GlassFrame(entry_frame)
        info_frame.pack(fill="x", padx=10, pady=2)

        # Date and word count
        date_str = format_date_for_display(entry.created_at)
        info_text = f"{date_str} • {entry.word_count} words"

        if entry.weather_condition:
            info_text += f" • {entry.weather_condition}"

        info_label = GlassLabel(
            info_frame,
            text=info_text,
            text_style="caption",
            size=ComponentSize.SMALL
        )
        info_label.pack(side="left")

        # Content preview
        if entry.content:
            preview_text = truncate_text(entry.content, 100)
            preview_label = GlassLabel(
                entry_frame,
                text=preview_text,
                text_style="caption",
                size=ComponentSize.SMALL
            )
            preview_label.pack(fill="x", padx=10, pady=(2, 10))

        # Tags
        if entry.tags:
            tags_frame = GlassFrame(entry_frame)
            tags_frame.pack(fill="x", padx=10, pady=(0, 10))

            for tag in entry.tags[:3]:  # Show max 3 tags
                tag_label = GlassLabel(
                    tags_frame,
                    text=f"#{tag}",
                    text_style="caption",
                    size=ComponentSize.SMALL
                )
                tag_label.pack(side="left", padx=(0, 5))

        # Bind click event
        def on_click(event, entry_id=entry.id):
            self._select_entry(entry_id)

        entry_frame.bind("<Button-1>", on_click)
        for child in entry_frame.winfo_children():
            child.bind("<Button-1>", on_click)

    def _update_statistics(self):
        """Update journal statistics display."""
        stats = self.controller.get_statistics()
        stats_text = f"Entries: {stats['total_entries']} • Words: {stats['total_words']:,}"
        self.stats_label.configure(text=stats_text)

    def _update_editor_info(self):
        """Update editor information display."""
        entry = self.controller.get_current_entry()
        if entry:
            if entry.id:
                # Existing entry
                created_str = format_date_for_display(entry.created_at)
                updated_str = format_date_for_display(entry.updated_at)
                info_text = f"Created: {created_str} | Updated: {updated_str}"
            else:
                # New entry
                info_text = "New Entry"
        else:
            info_text = "No Entry Selected"

        self.entry_info_label.configure(text=info_text)

    def _update_weather_display(self):
        """Update weather information display."""
        entry = self.controller.get_current_entry()
        if entry:
            weather_text = extract_weather_info_from_entry(entry)
        else:
            weather_text = "Weather: Not available"

        self.weather_info_label.configure(text=weather_text)

    def _update_favorite_button(self):
        """Update favorite button appearance."""
        entry = self.controller.get_current_entry()
        if entry and entry.is_favorite:
            self.favorite_button.configure(text="⭐", fg_color=("#FFD700", "#FFA500"))
        else:
            glass_config = self.favorite_button._get_glass_button_config()
            self.favorite_button.configure(text="☆", fg_color=glass_config['fg_color'])

    # Public API Methods

    def set_weather_data(self, weather_data: WeatherData):
        """Set current weather data for new entries."""
        self.controller.set_weather_data(weather_data)
        self._update_weather_display()

    def get_current_entry(self) -> Optional[JournalEntry]:
        """Get currently selected entry."""
        return self.controller.get_current_entry()

    def refresh_entries(self):
        """Refresh entries from database."""
        self.controller.refresh_entries()

    def export_all_entries(self, filename: str, format_type: str = "json") -> bool:
        """Export all entries to file."""
        return self.controller.export_all_entries(filename, format_type)

    def get_mood_analytics(self) -> Dict[str, Any]:
        """Get mood analytics and correlations."""
        return self.controller.get_mood_analytics()


def create_weather_journal(
    parent,
    database_manager: DatabaseManager,
    **kwargs
) -> WeatherJournalWidget:
    """
    Factory function to create a Weather Journal widget.

    Args:
        parent: Parent widget
        database_manager: Database manager instance
        **kwargs: Additional widget arguments

    Returns:
        WeatherJournalWidget: Configured journal widget
    """
    return WeatherJournalWidget(
        parent=parent,
        database_manager=database_manager,
        **kwargs
    )