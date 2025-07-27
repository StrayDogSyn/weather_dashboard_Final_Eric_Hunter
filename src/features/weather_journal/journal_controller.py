#!/usr/bin/env python3
"""
Weather Journal Controller - Business logic and state management

This module contains the controller logic for the Weather Journal feature,
handling business logic, state management, and coordination between components.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from tkinter import messagebox, filedialog
from pathlib import Path

from ...utils.logger import LoggerMixin
from ...core.database_manager import DatabaseManager
from ...services.weather_service import WeatherData
from .models import JournalEntry, EntryMood, SearchFilter
from .database import JournalDatabase
from .utils import (
    format_entry_as_text, format_entry_as_markdown,
    export_entries_to_json, export_entries_to_csv,
    calculate_mood_analytics, generate_export_filename,
    parse_tags_string, validate_entry_data
)


class JournalController(LoggerMixin):
    """
    Controller for Weather Journal business logic.
    
    This class manages the business logic, state, and coordination
    between different components of the Weather Journal feature.
    """

    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
        self.journal_db = JournalDatabase(database_manager)
        
        # Current state
        self.current_entry: Optional[JournalEntry] = None
        self.entries: List[JournalEntry] = []
        self.is_editing = False
        self.has_unsaved_changes = False
        
        # Current weather data
        self.current_weather: Optional[WeatherData] = None
        
        # Auto-save settings
        self.auto_save_enabled = True
        self.auto_save_delay = 2000  # milliseconds
        
        # Callbacks for UI updates
        self.entry_updated_callbacks: List[Callable] = []
        self.entries_changed_callbacks: List[Callable] = []
        self.save_status_callbacks: List[Callable[[str], None]] = []
        
        # Load initial data
        self.refresh_entries()
        
        self.logger.info("Weather Journal Controller initialized")

    def add_entry_updated_callback(self, callback: Callable):
        """Add callback for when current entry is updated."""
        self.entry_updated_callbacks.append(callback)

    def add_entries_changed_callback(self, callback: Callable):
        """Add callback for when entries list changes."""
        self.entries_changed_callbacks.append(callback)

    def add_save_status_callback(self, callback: Callable[[str], None]):
        """Add callback for save status updates."""
        self.save_status_callbacks.append(callback)

    def _notify_entry_updated(self):
        """Notify listeners that current entry was updated."""
        for callback in self.entry_updated_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in entry updated callback: {e}")

    def _notify_entries_changed(self):
        """Notify listeners that entries list changed."""
        for callback in self.entries_changed_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in entries changed callback: {e}")

    def _notify_save_status(self, status: str):
        """Notify listeners of save status update."""
        for callback in self.save_status_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Error in save status callback: {e}")

    # Entry Management Methods

    def create_new_entry(self) -> bool:
        """Create a new journal entry."""
        # Check for unsaved changes
        if self.has_unsaved_changes:
            if not self._confirm_discard_changes():
                return False

        # Create new entry
        self.current_entry = JournalEntry()
        self.is_editing = True
        self.has_unsaved_changes = False

        # Update weather data for new entry
        if self.current_weather:
            self._apply_weather_to_current_entry()

        self._notify_entry_updated()
        self._notify_save_status("New Entry")

        self.logger.debug("Created new journal entry")
        return True

    def load_entry(self, entry_id: int) -> bool:
        """Load an existing entry for editing."""
        # Check for unsaved changes
        if self.has_unsaved_changes:
            if not self._confirm_discard_changes():
                return False

        # Find and load entry
        entry = next((e for e in self.entries if e.id == entry_id), None)
        if not entry:
            # Try loading from database
            entry = self.journal_db.get_entry(entry_id)

        if entry:
            self.current_entry = entry
            self.is_editing = True
            self.has_unsaved_changes = False

            self._notify_entry_updated()
            self._notify_save_status("Loaded")

            self.logger.debug(f"Loaded entry: {entry.title}")
            return True
        else:
            self.logger.warning(f"Entry not found: {entry_id}")
            return False

    def save_current_entry(self, title: str, content: str, mood_value: str = "", tags_string: str = "") -> bool:
        """Save the current journal entry."""
        if not self.current_entry:
            return False

        # Validate input
        errors = validate_entry_data(title, content)
        if errors:
            error_msg = "\n".join(errors.values())
            messagebox.showerror("Validation Error", error_msg)
            return False

        try:
            # Update entry data
            self.current_entry.update_content(title.strip(), content)

            # Update mood
            self.current_entry.mood = None
            if mood_value:
                for mood in EntryMood:
                    if mood.value == mood_value:
                        self.current_entry.mood = mood
                        break

            # Update tags
            self.current_entry.tags = parse_tags_string(tags_string)

            # Update weather data
            if self.current_weather:
                self._apply_weather_to_current_entry()

            # Save to database
            entry_id = self.journal_db.save_entry(self.current_entry)

            # Update entry ID if new
            if self.current_entry.id is None:
                self.current_entry.id = entry_id
                self.entries.append(self.current_entry)
                self._notify_entries_changed()

            self.has_unsaved_changes = False
            self._notify_save_status("Saved")

            self.logger.info(f"Saved journal entry: {self.current_entry.title}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving journal entry: {e}")
            messagebox.showerror("Error", f"Failed to save entry: {e}")
            return False

    def delete_current_entry(self) -> bool:
        """Delete the current journal entry."""
        if not self.current_entry or not self.current_entry.id:
            return False

        # Confirm deletion
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{self.current_entry.title or 'Untitled Entry'}'?\n\nThis action cannot be undone."
        ):
            return False

        try:
            # Delete from database
            if self.journal_db.delete_entry(self.current_entry.id):
                # Remove from entries list
                self.entries = [e for e in self.entries if e.id != self.current_entry.id]

                # Create new entry
                self.create_new_entry()

                self._notify_entries_changed()

                self.logger.info(f"Deleted journal entry: {self.current_entry.title}")
                return True
            else:
                messagebox.showerror("Error", "Failed to delete entry from database.")
                return False

        except Exception as e:
            self.logger.error(f"Error deleting journal entry: {e}")
            messagebox.showerror("Error", f"Failed to delete entry: {e}")
            return False

    def toggle_favorite(self) -> bool:
        """Toggle favorite status of current entry."""
        if not self.current_entry:
            return False

        self.current_entry.is_favorite = not self.current_entry.is_favorite
        
        # Auto-save if enabled
        if self.auto_save_enabled:
            # Note: This would trigger auto-save in the UI
            pass
        else:
            self.has_unsaved_changes = True
            self._notify_save_status("Modified")

        self._notify_entry_updated()
        return True

    def mark_content_changed(self):
        """Mark that the content has been changed."""
        if self.is_editing:
            self.has_unsaved_changes = True
            self._notify_save_status("Modified")

    # Search and Filter Methods

    def search_entries(self, query: str, filter_type: SearchFilter = SearchFilter.ALL) -> List[JournalEntry]:
        """Search journal entries."""
        if not query.strip():
            return self.entries

        try:
            results = self.journal_db.search_entries(query.strip(), filter_type)
            return results
        except Exception as e:
            self.logger.error(f"Error searching entries: {e}")
            return []

    def filter_entries_by_date_range(self, start_date: datetime, end_date: datetime) -> List[JournalEntry]:
        """Filter entries by date range."""
        try:
            return self.journal_db.get_entries_by_date_range(start_date, end_date)
        except Exception as e:
            self.logger.error(f"Error filtering entries by date: {e}")
            return []

    def get_entries_by_mood(self, mood: EntryMood) -> List[JournalEntry]:
        """Get entries filtered by mood."""
        return [entry for entry in self.entries if entry.mood == mood]

    def get_favorite_entries(self) -> List[JournalEntry]:
        """Get all favorite entries."""
        return [entry for entry in self.entries if entry.is_favorite]

    # Export Methods

    def export_current_entry(self) -> bool:
        """Export current entry to file."""
        if not self.current_entry:
            return False

        # Get export filename
        default_filename = generate_export_filename(self.current_entry, "txt")

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
            return False

        try:
            file_ext = Path(filename).suffix.lower()

            if file_ext == '.json':
                # Export as JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.current_entry.to_dict(), f, indent=2, ensure_ascii=False)

            elif file_ext == '.md':
                # Export as Markdown
                content = format_entry_as_markdown(self.current_entry)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)

            else:
                # Export as plain text
                content = format_entry_as_text(self.current_entry)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)

            messagebox.showinfo("Export Complete", f"Entry exported to {filename}")
            self.logger.info(f"Exported entry to {filename}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting entry: {e}")
            messagebox.showerror("Error", f"Failed to export entry: {e}")
            return False

    def export_all_entries(self, filename: str, format_type: str = "json") -> bool:
        """Export all entries to file."""
        try:
            if format_type.lower() == "json":
                return export_entries_to_json(self.entries, filename)
            elif format_type.lower() == "csv":
                return export_entries_to_csv(self.entries, filename)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error exporting all entries: {e}")
            return False

    # Analytics Methods

    def get_mood_analytics(self) -> Dict[str, Any]:
        """Get mood analytics and correlations."""
        try:
            mood_stats = self.journal_db.get_mood_statistics()
            
            # Use utility function for additional analytics
            analytics = calculate_mood_analytics(self.entries)
            analytics['mood_distribution'] = mood_stats
            
            return analytics

        except Exception as e:
            self.logger.error(f"Error calculating mood analytics: {e}")
            return {}

    def get_statistics(self) -> Dict[str, Any]:
        """Get general journal statistics."""
        total_entries = len(self.entries)
        total_words = sum(entry.word_count for entry in self.entries)
        favorite_count = len([e for e in self.entries if e.is_favorite])
        entries_with_weather = len([e for e in self.entries if e.weather_condition])

        return {
            'total_entries': total_entries,
            'total_words': total_words,
            'favorite_count': favorite_count,
            'entries_with_weather': entries_with_weather,
            'average_words_per_entry': total_words / total_entries if total_entries > 0 else 0
        }

    # Weather Integration Methods

    def set_weather_data(self, weather_data: WeatherData):
        """Set current weather data for new entries."""
        self.current_weather = weather_data
        self.logger.debug(f"Weather data updated: {weather_data.condition}, {weather_data.temperature}°F")

    def _apply_weather_to_current_entry(self):
        """Apply current weather data to the current entry."""
        if self.current_weather and self.current_entry:
            self.current_entry.weather_temperature = self.current_weather.temperature
            self.current_entry.weather_condition = self.current_weather.condition
            self.current_entry.weather_humidity = self.current_weather.humidity
            self.current_entry.weather_pressure = self.current_weather.pressure
            self.current_entry.weather_wind_speed = self.current_weather.wind_speed
            self.current_entry.weather_location = self.current_weather.location

    # Data Management Methods

    def refresh_entries(self):
        """Refresh entries from database."""
        try:
            self.entries = self.journal_db.get_all_entries()
            self._notify_entries_changed()
            self.logger.debug(f"Loaded {len(self.entries)} journal entries")
        except Exception as e:
            self.logger.error(f"Error loading journal entries: {e}")

    def get_all_entries(self) -> List[JournalEntry]:
        """Get all journal entries."""
        return self.entries.copy()

    def get_current_entry(self) -> Optional[JournalEntry]:
        """Get currently selected entry."""
        return self.current_entry

    # Helper Methods

    def _confirm_discard_changes(self) -> bool:
        """Confirm discarding unsaved changes."""
        return messagebox.askyesno(
            "Unsaved Changes",
            "You have unsaved changes. Do you want to discard them?"
        )

    def set_auto_save(self, enabled: bool):
        """Enable or disable auto-save."""
        self.auto_save_enabled = enabled

    def get_auto_save_enabled(self) -> bool:
        """Check if auto-save is enabled."""
        return self.auto_save_enabled