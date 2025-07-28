#!/usr/bin/env python3
"""
Weather Journal Feature - Rich Text Weather Diary

This module provides the main entry point for the Weather Journal feature,
now implemented using a modular architecture for better maintainability
and code organization.

The Weather Journal feature demonstrates advanced text editing and data management including:
- Rich text editor with glassmorphic styling
- Weather-aware journal entries with automatic metadata
- Advanced search and filtering capabilities
- Export functionality with multiple formats
- Mood tracking and weather correlation analysis
- Professional data persistence and synchronization

Usage:
    from .weather_journal import create_weather_journal
    
    journal = create_weather_journal(parent, database_manager)
    journal.pack(fill="both", expand=True)
"""

# Import all components from the modular package
from .weather_journal.journal_widget import WeatherJournalWidget, create_weather_journal
from .weather_journal.journal_controller import JournalController
from .weather_journal.ui_components import RichTextEditor
from .weather_journal.database import JournalDatabase
from .weather_journal.models import EntryMood, SearchFilter, JournalEntry

# Main factory function for backward compatibility
def create_weather_journal_widget(parent, database_manager, **kwargs):
    """
    Backward compatibility function.
    
    Args:
        parent: Parent widget
        database_manager: Database manager instance
        **kwargs: Additional widget arguments
    
    Returns:
        WeatherJournalWidget: Configured journal widget
    """
    return create_weather_journal(parent, database_manager, **kwargs)


# Test functionality when run directly
if __name__ == "__main__":
    # Test the weather journal widget
    import sys
    import customtkinter as ctk
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