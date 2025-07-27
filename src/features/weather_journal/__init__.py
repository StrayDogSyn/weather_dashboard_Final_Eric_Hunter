#!/usr/bin/env python3
"""
Weather Journal Feature Package

This package provides a modular Weather Journal implementation with:
- Rich text editing with glassmorphic styling
- Weather-aware journal entries with automatic metadata
- Advanced search and filtering capabilities
- Export functionality with multiple formats
- Mood tracking and weather correlation analysis
- Professional data persistence and synchronization

Package Structure:
- models.py: Data structures and enums (EntryMood, SearchFilter, JournalEntry)
- database.py: Database operations and persistence (JournalDatabase)
- ui_components.py: Reusable UI components (RichTextEditor)
- journal_controller.py: Business logic and state management
- journal_widget.py: Main UI widget (WeatherJournalWidget)
- utils.py: Utility functions and formatters

Usage:
    from .weather_journal import create_weather_journal
    
    journal = create_weather_journal(parent, database_manager)
    journal.pack(fill="both", expand=True)
"""

# Import main components for easy access
from .models import EntryMood, SearchFilter, JournalEntry
from .database import JournalDatabase
from .ui_components import RichTextEditor
from .journal_controller import JournalController
from .journal_widget import WeatherJournalWidget, create_weather_journal
from .utils import (
    format_entry_as_text,
    format_entry_as_markdown,
    export_entries_to_json,
    export_entries_to_csv,
    calculate_mood_analytics,
    sanitize_filename,
    generate_export_filename,
    parse_tags_string,
    format_tags_for_display,
    calculate_reading_time,
    truncate_text,
    format_date_for_display,
    format_datetime_for_display,
    validate_entry_data,
    extract_weather_info_from_entry,
    search_entries_by_content
)

# Main export - the factory function for creating the journal widget
__all__ = [
    # Main factory function
    'create_weather_journal',
    
    # Core components
    'WeatherJournalWidget',
    'JournalController',
    'RichTextEditor',
    'JournalDatabase',
    
    # Data models
    'JournalEntry',
    'EntryMood',
    'SearchFilter',
    
    # Utility functions
    'format_entry_as_text',
    'format_entry_as_markdown',
    'export_entries_to_json',
    'export_entries_to_csv',
    'calculate_mood_analytics',
    'sanitize_filename',
    'generate_export_filename',
    'parse_tags_string',
    'format_tags_for_display',
    'calculate_reading_time',
    'truncate_text',
    'format_date_for_display',
    'format_datetime_for_display',
    'validate_entry_data',
    'extract_weather_info_from_entry',
    'search_entries_by_content'
]

# Package metadata
__version__ = "1.0.0"
__author__ = "Weather Dashboard Team"
__description__ = "Modular Weather Journal feature with rich text editing and weather correlation"