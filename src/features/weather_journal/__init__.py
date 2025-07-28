#!/usr/bin/env python3
"""
Weather Journal Package - Phase 4 Enhanced

This package provides advanced weather journaling functionality with:
- Tabbed glassmorphic interface
- Rich text editing with Markdown support
- Photo attachment system
- Advanced analytics and data visualization
- Professional export system

Package Structure:
- models.py: Data structures and enums (EntryMood, SearchFilter, JournalEntry)
- database.py: Database operations and persistence (JournalDatabase)
- ui_components.py: Reusable UI components (RichTextEditor)
- journal_controller.py: Business logic and state management
- journal_widget.py: Main UI widget (WeatherJournalWidget)
- tabbed_interface.py: Tabbed journal interface
- rich_text_editor.py: Markdown editor component
- photo_manager.py: Photo attachment system
- analytics_engine.py: Analytics and visualization
- export_system.py: Professional export functionality
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
from .tabbed_interface import TabbedJournalInterface
from .rich_text_editor import MarkdownEditor
from .photo_manager import PhotoManager, PhotoGalleryWidget
from .analytics_engine import AnalyticsEngine, AnalyticsVisualization
from .export_system import ExportSystem, ExportDialog
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
    
    # Phase 4 Enhanced components
    'TabbedJournalInterface',
    'MarkdownEditor',
    'PhotoManager',
    'PhotoGalleryWidget',
    'AnalyticsEngine',
    'AnalyticsVisualization',
    'ExportSystem',
    'ExportDialog',
    
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
__version__ = "1.4.0"
__author__ = "Weather Dashboard Team"
__description__ = "Advanced Weather Journal with tabbed interface, photo attachments, and analytics"