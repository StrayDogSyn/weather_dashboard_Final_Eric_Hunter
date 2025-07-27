#!/usr/bin/env python3
"""
Weather Journal Feature - Rich Text Weather Diary

This module implements the Weather Journal capstone feature (⭐⭐ difficulty),
demonstrating advanced text editing and data management including:
- Rich text editor with glassmorphic styling
- Weather-aware journal entries with automatic metadata
- Advanced search and filtering capabilities
- Export functionality with multiple formats
- Mood tracking and weather correlation analysis
- Professional data persistence and synchronization

Architectural Decisions:
- Rich text widget integration with CustomTkinter
- Structured data model for journal entries
- Search engine with full-text capabilities
- Export system with multiple format support
- Weather correlation analytics
- Professional error handling and data validation
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import re
import threading
from pathlib import Path
import sqlite3

from ..utils.logger import LoggerMixin
from ..ui.components.base_components import (
    GlassFrame, GlassButton, GlassLabel, GlassEntry,
    ComponentSize, create_glass_card
)
from ..ui.theme_manager import ThemeManager, WeatherTheme, GlassEffect
from ..services.weather_service import WeatherData
from ..core.database_manager import DatabaseManager


class EntryMood(Enum):
    """
    Mood options for journal entries.

    This enum provides structured mood tracking
    for weather correlation analysis.
    """
    VERY_HAPPY = "😄"
    HAPPY = "😊"
    NEUTRAL = "😐"
    SAD = "😔"
    VERY_SAD = "😢"
    ENERGETIC = "⚡"
    CALM = "😌"
    ANXIOUS = "😰"
    EXCITED = "🤩"
    TIRED = "😴"


class SearchFilter(Enum):
    """
    Search filter options for journal entries.

    This enum supports comprehensive search capabilities
    with multiple filtering criteria.
    """
    ALL = "all"
    TITLE = "title"
    CONTENT = "content"
    MOOD = "mood"
    WEATHER = "weather"
    DATE = "date"
    TAGS = "tags"


@dataclass
class JournalEntry:
    """
    Journal entry data structure.

    This dataclass provides comprehensive journal entry
    with weather correlation and metadata.
    """
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    mood: Optional[EntryMood] = None
    tags: List[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Weather data at time of entry
    weather_temperature: Optional[float] = None
    weather_condition: Optional[str] = None
    weather_humidity: Optional[float] = None
    weather_pressure: Optional[float] = None
    weather_wind_speed: Optional[float] = None
    weather_location: Optional[str] = None

    # Entry metadata
    word_count: int = 0
    reading_time: int = 0  # estimated reading time in minutes
    is_favorite: bool = False
    is_private: bool = False

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at

        # Calculate word count and reading time
        self._update_metadata()

    def _update_metadata(self):
        """Update entry metadata based on content."""
        words = len(self.content.split())
        self.word_count = words
        self.reading_time = max(1, words // 200)  # Assume 200 words per minute

    def update_content(self, title: str, content: str):
        """Update entry content and metadata."""
        self.title = title
        self.content = content
        self.updated_at = datetime.now()
        self._update_metadata()

    def add_tag(self, tag: str):
        """Add a tag to the entry."""
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Remove a tag from the entry."""
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        data = asdict(self)

        # Convert datetime objects to ISO strings
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()

        # Convert mood enum to value
        if self.mood:
            data['mood'] = self.mood.value

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JournalEntry':
        """Create entry from dictionary."""
        # Convert ISO strings to datetime objects
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])

        # Convert mood value to enum
        if 'mood' in data and data['mood']:
            for mood in EntryMood:
                if mood.value == data['mood']:
                    data['mood'] = mood
                    break

        return cls(**data)


class JournalDatabase(LoggerMixin):
    """
    Database manager for journal entries.

    This class provides comprehensive database operations
    for journal entry persistence and retrieval.
    """

    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
        self._create_tables()

    def _create_tables(self):
        """Create journal tables if they don't exist."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Create journal entries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS journal_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        mood TEXT,
                        tags TEXT,  -- JSON array of tags
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        weather_temperature REAL,
                        weather_condition TEXT,
                        weather_humidity REAL,
                        weather_pressure REAL,
                        weather_wind_speed REAL,
                        weather_location TEXT,
                        word_count INTEGER DEFAULT 0,
                        reading_time INTEGER DEFAULT 0,
                        is_favorite BOOLEAN DEFAULT FALSE,
                        is_private BOOLEAN DEFAULT FALSE
                    )
                """)

                # Create search index for full-text search
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS journal_search
                    USING fts5(title, content, tags, weather_condition)
                """)

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error creating journal tables: {e}")
            raise

    def save_entry(self, entry: JournalEntry) -> int:
        """Save journal entry to database."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                tags_json = json.dumps(entry.tags) if entry.tags else '[]'
                mood_value = entry.mood.value if entry.mood else None

                if entry.id is None:
                    # Insert new entry
                    cursor.execute("""
                        INSERT INTO journal_entries (
                            title, content, mood, tags, created_at, updated_at,
                            weather_temperature, weather_condition, weather_humidity,
                            weather_pressure, weather_wind_speed, weather_location,
                            word_count, reading_time, is_favorite, is_private
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.title, entry.content, mood_value, tags_json,
                        entry.created_at, entry.updated_at,
                        entry.weather_temperature, entry.weather_condition,
                        entry.weather_humidity, entry.weather_pressure,
                        entry.weather_wind_speed, entry.weather_location,
                        entry.word_count, entry.reading_time,
                        entry.is_favorite, entry.is_private
                    ))

                    entry.id = cursor.lastrowid

                    # Add to search index
                    cursor.execute("""
                        INSERT INTO journal_search (rowid, title, content, tags, weather_condition)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        entry.id, entry.title, entry.content,
                        ' '.join(entry.tags), entry.weather_condition or ''
                    ))

                else:
                    # Update existing entry
                    cursor.execute("""
                        UPDATE journal_entries SET
                            title = ?, content = ?, mood = ?, tags = ?, updated_at = ?,
                            weather_temperature = ?, weather_condition = ?,
                            weather_humidity = ?, weather_pressure = ?,
                            weather_wind_speed = ?, weather_location = ?,
                            word_count = ?, reading_time = ?,
                            is_favorite = ?, is_private = ?
                        WHERE id = ?
                    """, (
                        entry.title, entry.content, mood_value, tags_json, entry.updated_at,
                        entry.weather_temperature, entry.weather_condition,
                        entry.weather_humidity, entry.weather_pressure,
                        entry.weather_wind_speed, entry.weather_location,
                        entry.word_count, entry.reading_time,
                        entry.is_favorite, entry.is_private, entry.id
                    ))

                    # Update search index
                    cursor.execute("""
                        UPDATE journal_search SET
                            title = ?, content = ?, tags = ?, weather_condition = ?
                        WHERE rowid = ?
                    """, (
                        entry.title, entry.content, ' '.join(entry.tags),
                        entry.weather_condition or '', entry.id
                    ))

                conn.commit()
                return entry.id

        except Exception as e:
            self.logger.error(f"Error saving journal entry: {e}")
            raise

    def get_entry(self, entry_id: int) -> Optional[JournalEntry]:
        """Get journal entry by ID."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM journal_entries WHERE id = ?
                """, (entry_id,))

                row = cursor.fetchone()
                if row:
                    return self._row_to_entry(row)

                return None

        except Exception as e:
            self.logger.error(f"Error getting journal entry {entry_id}: {e}")
            return None

    def get_all_entries(self, limit: Optional[int] = None, offset: int = 0) -> List[JournalEntry]:
        """Get all journal entries."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM journal_entries ORDER BY updated_at DESC"
                params = []

                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [self._row_to_entry(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error getting journal entries: {e}")
            return []

    def search_entries(self, query: str, filter_type: SearchFilter = SearchFilter.ALL) -> List[JournalEntry]:
        """Search journal entries."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                if filter_type == SearchFilter.ALL:
                    # Full-text search
                    cursor.execute("""
                        SELECT je.* FROM journal_entries je
                        JOIN journal_search js ON je.id = js.rowid
                        WHERE journal_search MATCH ?
                        ORDER BY je.updated_at DESC
                    """, (query,))
                else:
                    # Specific field search
                    field_map = {
                        SearchFilter.TITLE: "title",
                        SearchFilter.CONTENT: "content",
                        SearchFilter.MOOD: "mood",
                        SearchFilter.WEATHER: "weather_condition",
                        SearchFilter.TAGS: "tags"
                    }

                    field = field_map.get(filter_type, "title")
                    cursor.execute(f"""
                        SELECT * FROM journal_entries
                        WHERE {field} LIKE ?
                        ORDER BY updated_at DESC
                    """, (f"%{query}%",))

                rows = cursor.fetchall()
                return [self._row_to_entry(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error searching journal entries: {e}")
            return []

    def delete_entry(self, entry_id: int) -> bool:
        """Delete journal entry."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Delete from main table
                cursor.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))

                # Delete from search index
                cursor.execute("DELETE FROM journal_search WHERE rowid = ?", (entry_id,))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Error deleting journal entry {entry_id}: {e}")
            return False

    def get_entries_by_date_range(self, start_date: datetime, end_date: datetime) -> List[JournalEntry]:
        """Get entries within date range."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM journal_entries
                    WHERE created_at BETWEEN ? AND ?
                    ORDER BY created_at DESC
                """, (start_date, end_date))

                rows = cursor.fetchall()
                return [self._row_to_entry(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error getting entries by date range: {e}")
            return []

    def get_mood_statistics(self) -> Dict[str, int]:
        """Get mood statistics for all entries."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT mood, COUNT(*) as count
                    FROM journal_entries
                    WHERE mood IS NOT NULL
                    GROUP BY mood
                """)

                rows = cursor.fetchall()
                return {row[0]: row[1] for row in rows}

        except Exception as e:
            self.logger.error(f"Error getting mood statistics: {e}")
            return {}

    def _row_to_entry(self, row) -> JournalEntry:
        """Convert database row to JournalEntry object."""
        tags = json.loads(row[4]) if row[4] else []

        # Find mood enum
        mood = None
        if row[3]:
            for mood_enum in EntryMood:
                if mood_enum.value == row[3]:
                    mood = mood_enum
                    break

        return JournalEntry(
            id=row[0],
            title=row[1],
            content=row[2],
            mood=mood,
            tags=tags,
            created_at=datetime.fromisoformat(row[5]) if row[5] else None,
            updated_at=datetime.fromisoformat(row[6]) if row[6] else None,
            weather_temperature=row[7],
            weather_condition=row[8],
            weather_humidity=row[9],
            weather_pressure=row[10],
            weather_wind_speed=row[11],
            weather_location=row[12],
            word_count=row[13] or 0,
            reading_time=row[14] or 0,
            is_favorite=bool(row[15]),
            is_private=bool(row[16])
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
        self.size_entry = GlassEntry(
            size_frame,
            textvariable=self.size_var,
            size=ComponentSize.SMALL,
            width=50
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
        self.journal_db = JournalDatabase(database_manager)
        self.theme_manager = ThemeManager()

        # Current state
        self.current_entry: Optional[JournalEntry] = None
        self.entries: List[JournalEntry] = []
        self.is_editing = False
        self.has_unsaved_changes = False

        # Current weather data
        self.current_weather: Optional[WeatherData] = None

        # UI components
        self.sidebar: Optional[GlassFrame] = None
        self.editor_panel: Optional[GlassFrame] = None
        self.entry_list: Optional[ctk.CTkScrollableFrame] = None
        self.editor: Optional[RichTextEditor] = None

        # Initialize UI
        self._setup_ui()
        self._load_entries()

        self.logger.info("Weather Journal Widget initialized")

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

        self.search_var = tk.StringVar()
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

        self.filter_var = tk.StringVar(value="all")
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

        self.title_var = tk.StringVar()
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

        self.mood_var = tk.StringVar()
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

        self.tags_var = tk.StringVar()
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

        self.auto_save_var = tk.BooleanVar(value=True)
        self.auto_save_check = ctk.CTkCheckBox(
            left_frame,
            text="Auto-save",
            variable=self.auto_save_var
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

    def _load_entries(self):
        """Load all journal entries from database."""
        try:
            self.entries = self.journal_db.get_all_entries()
            self._update_entry_list()
            self._update_statistics()

            self.logger.debug(f"Loaded {len(self.entries)} journal entries")

        except Exception as e:
            self.logger.error(f"Error loading journal entries: {e}")
            messagebox.showerror("Error", f"Failed to load journal entries: {e}")

    def _update_entry_list(self, entries: Optional[List[JournalEntry]] = None):
        """Update the entry list display."""
        # Clear existing entries
        for widget in self.entry_list.winfo_children():
            widget.destroy()

        # Use provided entries or all entries
        display_entries = entries if entries is not None else self.entries

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
        date_str = entry.created_at.strftime("%m/%d/%Y") if entry.created_at else "Unknown"
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
            preview_text = entry.content[:100] + "..." if len(entry.content) > 100 else entry.content
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
        total_entries = len(self.entries)
        total_words = sum(entry.word_count for entry in self.entries)

        stats_text = f"Entries: {total_entries} • Words: {total_words:,}"
        self.stats_label.configure(text=stats_text)

    def _select_entry(self, entry_id: int):
        """Select and load a journal entry for editing."""
        # Check for unsaved changes
        if self.has_unsaved_changes:
            if not self._confirm_discard_changes():
                return

        # Find and load entry
        entry = next((e for e in self.entries if e.id == entry_id), None)
        if entry:
            self._load_entry(entry)

    def _load_entry(self, entry: JournalEntry):
        """Load entry into editor."""
        self.current_entry = entry
        self.is_editing = True

        # Load content
        self.title_var.set(entry.title or "")
        self.editor.set_content(entry.content or "")

        # Load metadata
        if entry.mood:
            self.mood_var.set(entry.mood.value)
        else:
            self.mood_var.set("")

        if entry.tags:
            self.tags_var.set(", ".join(entry.tags))
        else:
            self.tags_var.set("")

        # Update UI
        self._update_editor_info()
        self._update_weather_display()
        self._update_favorite_button()

        self.has_unsaved_changes = False
        self._update_save_status("Loaded")

        self.logger.debug(f"Loaded entry: {entry.title}")

    def _create_new_entry(self):
        """Create a new journal entry."""
        # Check for unsaved changes
        if self.has_unsaved_changes:
            if not self._confirm_discard_changes():
                return

        # Create new entry
        self.current_entry = JournalEntry()
        self.is_editing = True

        # Clear editor
        self.title_var.set("")
        self.editor.clear_content()
        self.mood_var.set("")
        self.tags_var.set("")

        # Update UI
        self._update_editor_info()
        self._refresh_weather()
        self._update_favorite_button()

        self.has_unsaved_changes = False
        self._update_save_status("New Entry")

        # Focus title entry
        self.title_entry.focus()

        self.logger.debug("Created new journal entry")

    def _save_entry(self):
        """Save current journal entry."""
        if not self.current_entry:
            return

        try:
            # Update entry data
            self.current_entry.update_content(
                self.title_var.get().strip(),
                self.editor.get_content()
            )

            # Update mood
            mood_value = self.mood_var.get()
            if mood_value:
                for mood in EntryMood:
                    if mood.value == mood_value:
                        self.current_entry.mood = mood
                        break
            else:
                self.current_entry.mood = None

            # Update tags
            tags_text = self.tags_var.get().strip()
            if tags_text:
                tags = [tag.strip().lower() for tag in tags_text.split(",") if tag.strip()]
                self.current_entry.tags = tags
            else:
                self.current_entry.tags = []

            # Update weather data
            if self.current_weather:
                self.current_entry.weather_temperature = self.current_weather.temperature
                self.current_entry.weather_condition = self.current_weather.condition
                self.current_entry.weather_humidity = self.current_weather.humidity
                self.current_entry.weather_pressure = self.current_weather.pressure
                self.current_entry.weather_wind_speed = self.current_weather.wind_speed
                self.current_entry.weather_location = self.current_weather.location

            # Save to database
            entry_id = self.journal_db.save_entry(self.current_entry)

            # Update entry ID if new
            if self.current_entry.id is None:
                self.current_entry.id = entry_id
                self.entries.append(self.current_entry)

            # Update UI
            self._update_entry_list()
            self._update_statistics()

            self.has_unsaved_changes = False
            self._update_save_status("Saved")

            self.logger.info(f"Saved journal entry: {self.current_entry.title}")

        except Exception as e:
            self.logger.error(f"Error saving journal entry: {e}")
            messagebox.showerror("Error", f"Failed to save entry: {e}")

    def _delete_entry(self):
        """Delete current journal entry."""
        if not self.current_entry or not self.current_entry.id:
            return

        # Confirm deletion
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{self.current_entry.title or 'Untitled Entry'}'?\n\nThis action cannot be undone."
        ):
            return

        try:
            # Delete from database
            if self.journal_db.delete_entry(self.current_entry.id):
                # Remove from entries list
                self.entries = [e for e in self.entries if e.id != self.current_entry.id]

                # Clear editor
                self._create_new_entry()

                # Update UI
                self._update_entry_list()
                self._update_statistics()

                self.logger.info(f"Deleted journal entry: {self.current_entry.title}")

            else:
                messagebox.showerror("Error", "Failed to delete entry from database.")

        except Exception as e:
            self.logger.error(f"Error deleting journal entry: {e}")
            messagebox.showerror("Error", f"Failed to delete entry: {e}")

    def _export_entry(self):
        """Export current entry to file."""
        if not self.current_entry:
            return

        # Get export filename
        title = self.current_entry.title or "journal_entry"
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        default_filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d')}.txt"

        filename = filedialog.asksaveasfilename(
            title="Export Journal Entry",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialvalue=default_filename
        )

        if not filename:
            return

        try:
            file_ext = Path(filename).suffix.lower()

            if file_ext == '.json':
                # Export as JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.current_entry.to_dict(), f, indent=2, ensure_ascii=False)

            elif file_ext == '.md':
                # Export as Markdown
                content = self._format_entry_as_markdown()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)

            else:
                # Export as plain text
                content = self._format_entry_as_text()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)

            messagebox.showinfo("Export Complete", f"Entry exported to {filename}")
            self.logger.info(f"Exported entry to {filename}")

        except Exception as e:
            self.logger.error(f"Error exporting entry: {e}")
            messagebox.showerror("Error", f"Failed to export entry: {e}")

    def _format_entry_as_text(self) -> str:
        """Format entry as plain text."""
        lines = []

        # Title
        lines.append(self.current_entry.title or "Untitled Entry")
        lines.append("=" * len(lines[0]))
        lines.append("")

        # Metadata
        if self.current_entry.created_at:
            lines.append(f"Date: {self.current_entry.created_at.strftime('%B %d, %Y at %I:%M %p')}")

        if self.current_entry.mood:
            lines.append(f"Mood: {self.current_entry.mood.value}")

        if self.current_entry.tags:
            lines.append(f"Tags: {', '.join(self.current_entry.tags)}")

        if self.current_entry.weather_condition:
            weather_info = f"Weather: {self.current_entry.weather_condition}"
            if self.current_entry.weather_temperature:
                weather_info += f", {self.current_entry.weather_temperature}°F"
            if self.current_entry.weather_location:
                weather_info += f" in {self.current_entry.weather_location}"
            lines.append(weather_info)

        lines.append(f"Word Count: {self.current_entry.word_count}")
        lines.append(f"Reading Time: {self.current_entry.reading_time} min")
        lines.append("")

        # Content
        lines.append("Content:")
        lines.append("-" * 8)
        lines.append(self.current_entry.content or "")

        return "\n".join(lines)

    def _format_entry_as_markdown(self) -> str:
        """Format entry as Markdown."""
        lines = []

        # Title
        lines.append(f"# {self.current_entry.title or 'Untitled Entry'}")
        lines.append("")

        # Metadata table
        lines.append("## Entry Details")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")

        if self.current_entry.created_at:
            lines.append(f"| Date | {self.current_entry.created_at.strftime('%B %d, %Y at %I:%M %p')} |")

        if self.current_entry.mood:
            lines.append(f"| Mood | {self.current_entry.mood.value} |")

        if self.current_entry.tags:
            lines.append(f"| Tags | {', '.join(self.current_entry.tags)} |")

        if self.current_entry.weather_condition:
            weather_info = self.current_entry.weather_condition
            if self.current_entry.weather_temperature:
                weather_info += f", {self.current_entry.weather_temperature}°F"
            lines.append(f"| Weather | {weather_info} |")

        lines.append(f"| Word Count | {self.current_entry.word_count} |")
        lines.append(f"| Reading Time | {self.current_entry.reading_time} min |")
        lines.append("")

        # Content
        lines.append("## Content")
        lines.append("")
        lines.append(self.current_entry.content or "")

        return "\n".join(lines)

    def _toggle_favorite(self):
        """Toggle favorite status of current entry."""
        if not self.current_entry:
            return

        self.current_entry.is_favorite = not self.current_entry.is_favorite
        self._update_favorite_button()

        # Auto-save if enabled
        if self.auto_save_var.get():
            self._save_entry()
        else:
            self.has_unsaved_changes = True
            self._update_save_status("Modified")

    def _update_favorite_button(self):
        """Update favorite button appearance."""
        if self.current_entry and self.current_entry.is_favorite:
            self.favorite_button.configure(text="⭐", fg_color=("#FFD700", "#FFA500"))
        else:
            glass_config = self.favorite_button._get_glass_button_config()
            self.favorite_button.configure(text="☆", fg_color=glass_config['fg_color'])

    def _refresh_weather(self):
        """Refresh current weather data."""
        # Placeholder for weather service integration
        # This would be connected to the weather service in a real implementation
        self.current_weather = None
        self._update_weather_display()

        self.logger.debug("Weather data refreshed")

    def _update_weather_display(self):
        """Update weather information display."""
        if self.current_weather:
            weather_text = f"Weather: {self.current_weather.condition}, {self.current_weather.temperature}°F"
        elif self.current_entry and self.current_entry.weather_condition:
            weather_text = f"Weather: {self.current_entry.weather_condition}"
            if self.current_entry.weather_temperature:
                weather_text += f", {self.current_entry.weather_temperature}°F"
        else:
            weather_text = "Weather: Not available"

        self.weather_info_label.configure(text=weather_text)

    def _update_editor_info(self):
        """Update editor information display."""
        if self.current_entry:
            if self.current_entry.id:
                # Existing entry
                created_str = self.current_entry.created_at.strftime("%m/%d/%Y") if self.current_entry.created_at else "Unknown"
                updated_str = self.current_entry.updated_at.strftime("%m/%d/%Y") if self.current_entry.updated_at else "Unknown"
                info_text = f"Created: {created_str} | Updated: {updated_str}"
            else:
                # New entry
                info_text = "New Entry"
        else:
            info_text = "No Entry Selected"

        self.entry_info_label.configure(text=info_text)

    def _update_save_status(self, status: str):
        """Update save status display."""
        timestamp = datetime.now().strftime("%I:%M %p")
        self.save_status_label.configure(text=f"{status} at {timestamp}")

    def _on_content_changed(self):
        """Handle content change events."""
        if self.is_editing:
            self.has_unsaved_changes = True
            self._update_save_status("Modified")

            # Auto-save if enabled
            if self.auto_save_var.get():
                # Debounce auto-save
                if hasattr(self, '_auto_save_timer'):
                    self.after_cancel(self._auto_save_timer)

                self._auto_save_timer = self.after(2000, self._auto_save)  # 2 second delay

    def _on_title_changed(self, event=None):
        """Handle title change events."""
        self._on_content_changed()

    def _on_mood_changed(self, value=None):
        """Handle mood change events."""
        self._on_content_changed()

    def _on_tags_changed(self, event=None):
        """Handle tags change events."""
        self._on_content_changed()

    def _auto_save(self):
        """Perform auto-save."""
        if self.has_unsaved_changes and self.current_entry:
            self._save_entry()

    def _on_search_changed(self, event=None):
        """Handle search input changes."""
        search_query = self.search_var.get().strip()

        if not search_query:
            # Show all entries
            self._update_entry_list()
        else:
            # Perform search
            filter_type = SearchFilter(self.filter_var.get())
            results = self.journal_db.search_entries(search_query, filter_type)
            self._update_entry_list(results)

    def _on_filter_changed(self):
        """Handle filter change events."""
        self._on_search_changed()

    def _confirm_discard_changes(self) -> bool:
        """Confirm discarding unsaved changes."""
        return messagebox.askyesno(
            "Unsaved Changes",
            "You have unsaved changes. Do you want to discard them?"
        )

    # Public API methods

    def set_weather_data(self, weather_data: WeatherData):
        """Set current weather data for new entries."""
        self.current_weather = weather_data
        self._update_weather_display()

        self.logger.debug(f"Weather data updated: {weather_data.condition}, {weather_data.temperature}°F")

    def get_current_entry(self) -> Optional[JournalEntry]:
        """Get currently selected entry."""
        return self.current_entry

    def refresh_entries(self):
        """Refresh entries from database."""
        self._load_entries()

    def export_all_entries(self, filename: str, format_type: str = "json"):
        """Export all entries to file."""
        try:
            if format_type.lower() == "json":
                # Export as JSON
                entries_data = [entry.to_dict() for entry in self.entries]
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(entries_data, f, indent=2, ensure_ascii=False)

            elif format_type.lower() == "csv":
                # Export as CSV
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)

                    # Header
                    writer.writerow([
                        'ID', 'Title', 'Content', 'Mood', 'Tags', 'Created', 'Updated',
                        'Weather Condition', 'Temperature', 'Word Count', 'Is Favorite'
                    ])

                    # Data
                    for entry in self.entries:
                        writer.writerow([
                            entry.id,
                            entry.title,
                            entry.content,
                            entry.mood.value if entry.mood else '',
                            ', '.join(entry.tags) if entry.tags else '',
                            entry.created_at.isoformat() if entry.created_at else '',
                            entry.updated_at.isoformat() if entry.updated_at else '',
                            entry.weather_condition or '',
                            entry.weather_temperature or '',
                            entry.word_count,
                            entry.is_favorite
                        ])

            self.logger.info(f"Exported {len(self.entries)} entries to {filename}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting entries: {e}")
            return False

    def get_mood_analytics(self) -> Dict[str, Any]:
        """Get mood analytics and correlations."""
        try:
            mood_stats = self.journal_db.get_mood_statistics()

            # Calculate weather correlations
            weather_mood_correlation = {}
            for entry in self.entries:
                if entry.mood and entry.weather_condition:
                    condition = entry.weather_condition.lower()
                    mood = entry.mood.value

                    if condition not in weather_mood_correlation:
                        weather_mood_correlation[condition] = {}

                    if mood not in weather_mood_correlation[condition]:
                        weather_mood_correlation[condition][mood] = 0

                    weather_mood_correlation[condition][mood] += 1

            return {
                'mood_distribution': mood_stats,
                'weather_mood_correlation': weather_mood_correlation,
                'total_entries': len(self.entries),
                'entries_with_mood': len([e for e in self.entries if e.mood]),
                'entries_with_weather': len([e for e in self.entries if e.weather_condition])
            }

        except Exception as e:
            self.logger.error(f"Error calculating mood analytics: {e}")
            return {}


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


if __name__ == "__main__":
    # Test the weather journal widget
    import sys
    from pathlib import Path

    # Add src to path for imports
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))

    from core.database_manager import DatabaseManager

    # Create test application
    root = ctk.CTk()
    root.title("Weather Journal Test")
    root.geometry("1200x800")

    # Initialize database
    db_manager = DatabaseManager(":memory:")  # In-memory database for testing

    # Create journal widget
    journal = create_weather_journal(root, db_manager)
    journal.pack(fill="both", expand=True, padx=20, pady=20)

    # Run test
    root.mainloop()
