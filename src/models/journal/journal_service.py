"""Journal service for managing journal entries with weather integration."""

import logging
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .journal_entry import JournalEntry, Mood, WeatherSnapshot
from .journal_repository import JournalRepository


class JournalService:
    """Service for managing journal entries with auto-save and weather integration."""

    def __init__(self, repository: Optional[JournalRepository] = None, weather_service=None):
        """Initialize journal service."""
        self.logger = logging.getLogger(__name__)
        self.repository = repository or JournalRepository()
        self.weather_service = weather_service

        # Auto-save configuration
        self.auto_save_interval = 30  # seconds
        self.auto_save_timer: Optional[threading.Timer] = None
        self.auto_save_callbacks: List[Callable] = []

        # Current editing session
        self.current_entry: Optional[JournalEntry] = None
        self.unsaved_changes = False

        self.logger.info("Journal service initialized")

    def create_entry(
        self,
        title: str = "",
        content: str = "",
        location: str = "",
        mood: Optional[Mood] = None,
        auto_fill_weather: bool = True,
    ) -> JournalEntry:
        """Create a new journal entry with optional weather auto-fill."""
        entry = JournalEntry(title=title, content=content, location=location, mood=mood)

        # Auto-fill weather data if requested and service available
        if auto_fill_weather and self.weather_service and location:
            try:
                weather_data = self.weather_service.get_current_weather(location)
                if weather_data:
                    entry.weather_snapshot = self._create_weather_snapshot(weather_data)
                    entry.latitude = getattr(weather_data, "latitude", None)
                    entry.longitude = getattr(weather_data, "longitude", None)
            except Exception as e:
                self.logger.warning(f"Failed to auto-fill weather data: {e}")

        # Save to repository
        saved_entry = self.repository.create_entry(entry)
        self.logger.info(f"Created journal entry: {saved_entry.id}")

        return saved_entry

    def _create_weather_snapshot(self, weather_data) -> WeatherSnapshot:
        """Create weather snapshot from weather service data."""
        return WeatherSnapshot(
            temperature=weather_data.temperature,
            feels_like=weather_data.feels_like,
            condition=(
                weather_data.condition.value
                if hasattr(weather_data.condition, "value")
                else str(weather_data.condition)
            ),
            description=weather_data.description,
            humidity=weather_data.humidity,
            pressure=weather_data.pressure,
            wind_speed=weather_data.wind_speed,
            wind_direction=weather_data.wind_direction,
            visibility=weather_data.visibility,
            uv_index=weather_data.uv_index,
            cloudiness=weather_data.cloudiness,
        )

    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Get entry by ID."""
        return self.repository.get_entry(entry_id)

    def update_entry(self, entry: JournalEntry) -> JournalEntry:
        """Update existing entry."""
        updated_entry = self.repository.update_entry(entry)
        self.logger.info(f"Updated journal entry: {updated_entry.id}")
        return updated_entry

    def delete_entry(self, entry_id: str) -> bool:
        """Delete entry by ID."""
        success = self.repository.delete_entry(entry_id)
        if success:
            self.logger.info(f"Deleted journal entry: {entry_id}")
        return success

    def get_all_entries(self) -> List[JournalEntry]:
        """Get all entries sorted by creation date."""
        return self.repository.get_all_entries()

    def search_entries(self, query: str) -> List[JournalEntry]:
        """Search entries by content, title, or tags."""
        return self.repository.search_entries(query)

    def get_entries_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[JournalEntry]:
        """Get entries within date range."""
        return self.repository.get_entries_by_date_range(start_date, end_date)

    def get_entries_by_mood(self, mood: Mood) -> List[JournalEntry]:
        """Get entries by mood."""
        return self.repository.get_entries_by_mood(mood)

    def get_entries_by_location(self, location: str) -> List[JournalEntry]:
        """Get entries by location."""
        return self.repository.get_entries_by_location(location)

    def get_entries_by_tag(self, tag: str) -> List[JournalEntry]:
        """Get entries by tag."""
        return self.repository.get_entries_by_tag(tag)

    # Auto-save functionality
    def start_editing_session(self, entry: JournalEntry):
        """Start editing session with auto-save."""
        self.current_entry = entry
        self.unsaved_changes = False
        self._start_auto_save_timer()

    def end_editing_session(self, save_changes: bool = True):
        """End editing session and optionally save changes."""
        self._stop_auto_save_timer()

        if save_changes and self.current_entry and self.unsaved_changes:
            self.update_entry(self.current_entry)
            self.unsaved_changes = False

        self.current_entry = None

    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes in current session."""
        self.unsaved_changes = True
        if not self.auto_save_timer or not self.auto_save_timer.is_alive():
            self._start_auto_save_timer()

    def _start_auto_save_timer(self):
        """Start auto-save timer."""
        self._stop_auto_save_timer()
        self.auto_save_timer = threading.Timer(self.auto_save_interval, self._auto_save)
        self.auto_save_timer.start()

    def _stop_auto_save_timer(self):
        """Stop auto-save timer."""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
            self.auto_save_timer = None

    def _auto_save(self):
        """Perform auto-save of current entry."""
        try:
            if self.current_entry and self.unsaved_changes:
                self.current_entry.mark_auto_saved()
                self.repository.update_entry(self.current_entry)
                self.unsaved_changes = False

                # Notify callbacks
                for callback in self.auto_save_callbacks:
                    try:
                        callback(self.current_entry)
                    except Exception as e:
                        self.logger.warning(f"Auto-save callback failed: {e}")


                # Schedule next auto-save if still editing
                if self.current_entry:
                    self._start_auto_save_timer()

        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")

    def add_auto_save_callback(self, callback: Callable):
        """Add callback to be called after auto-save."""
        self.auto_save_callbacks.append(callback)

    def remove_auto_save_callback(self, callback: Callable):
        """Remove auto-save callback."""
        if callback in self.auto_save_callbacks:
            self.auto_save_callbacks.remove(callback)

    # Analytics and insights
    def get_mood_statistics(self) -> Dict[Mood, int]:
        """Get mood statistics across all entries."""
        return self.repository.get_mood_statistics()

    def get_writing_frequency(self, days: int = 30) -> Dict[str, int]:
        """Get writing frequency over the last N days."""
        return self.repository.get_writing_frequency(days)

    def get_weather_mood_correlation(self) -> Dict[str, Dict[Mood, int]]:
        """Get correlation between weather conditions and moods."""
        return self.repository.get_weather_mood_correlation()

    def get_mood_weather_insights(self) -> Dict[str, Any]:
        """Get insights about mood-weather correlations."""
        correlation = self.get_weather_mood_correlation()
        insights = {
            "most_common_moods_by_weather": {},
            "favorite_weather_conditions": {},
            "mood_weather_patterns": [],
        }

        # Find most common mood for each weather condition
        for weather, mood_counts in correlation.items():
            if mood_counts:
                most_common_mood = max(mood_counts.items(), key=lambda x: x[1])
                if most_common_mood[1] > 0:
                    insights["most_common_moods_by_weather"][weather] = {
                        "mood": most_common_mood[0].value,
                        "count": most_common_mood[1],
                        "emoji": most_common_mood[0].emoji,
                    }

        # Find favorite weather conditions for each mood
        mood_weather_totals = {}
        for weather, mood_counts in correlation.items():
            for mood, count in mood_counts.items():
                if mood not in mood_weather_totals:
                    mood_weather_totals[mood] = {}
                mood_weather_totals[mood][weather] = count

        for mood, weather_counts in mood_weather_totals.items():
            if weather_counts:
                favorite_weather = max(weather_counts.items(), key=lambda x: x[1])
                if favorite_weather[1] > 0:
                    insights["favorite_weather_conditions"][mood.value] = {
                        "weather": favorite_weather[0],
                        "count": favorite_weather[1],
                    }

        return insights

    def get_writing_patterns(self) -> Dict[str, Any]:
        """Get writing pattern insights."""
        entries = self.get_all_entries()

        if not entries:
            return {"patterns": [], "recommendations": []}

        patterns = []
        recommendations = []

        # Analyze writing times
        hour_counts = {}
        for entry in entries:
            hour = entry.created_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        if hour_counts:
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
            patterns.append(f"You write most often at {peak_hour}:00")

            if 6 <= peak_hour <= 11:
                recommendations.append(
                    "You're a morning writer! Consider setting aside time each morning for journaling."
                )
            elif 12 <= peak_hour <= 17:
                recommendations.append(
                    "Afternoon writing works well for you. Try journaling during lunch breaks."
                )
            elif 18 <= peak_hour <= 23:
                recommendations.append(
                    "Evening journaling helps you reflect on the day. Keep up this habit!"
                )

        # Analyze writing frequency
        frequency = self.get_writing_frequency(30)
        recent_entries = sum(frequency.values())

        if recent_entries > 20:
            patterns.append("You're a frequent writer with excellent consistency")
            recommendations.append(
                "Your writing habit is strong! Consider exploring different topics or formats."
            )
        elif recent_entries > 10:
            patterns.append("You have a good writing routine")
            recommendations.append(
                "Try to maintain your current pace and perhaps add more detail to entries."
            )
        else:
            patterns.append("You write occasionally")
            recommendations.append(
                "Consider setting a goal to write more regularly, even just a few sentences daily."
            )

        return {
            "patterns": patterns,
            "recommendations": recommendations,
            "peak_writing_hour": hour_counts and max(hour_counts.items(), key=lambda x: x[1])[0],
            "entries_last_30_days": recent_entries,
        }

    def get_word_cloud_data(self) -> Dict[str, int]:
        """Get word frequency data for word cloud generation."""
        return self.repository.get_word_cloud_data()

    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics and insights."""
        base_stats = self.repository.get_statistics()
        mood_insights = self.get_mood_weather_insights()
        writing_patterns = self.get_writing_patterns()

        return {
            **base_stats,
            "mood_weather_insights": mood_insights,
            "writing_patterns": writing_patterns,
            "tags": dict(self.repository.get_all_tags()[:10]),  # Top 10 tags
        }

    # Export functionality
    def export_to_json(self, file_path: str) -> bool:
        """Export all entries to JSON file."""
        return self.repository.export_to_json(file_path)

    def export_to_pdf(self, file_path: str, entries: Optional[List[JournalEntry]] = None) -> bool:
        """Export entries to PDF file."""
        try:
            import html

            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

            # Use all entries if none specified
            if entries is None:
                entries = self.get_all_entries()

            if not entries:
                self.logger.warning("No entries to export")
                return False

            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=1 * inch)
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue,
            )

            entry_title_style = ParagraphStyle(
                "EntryTitle",
                parent=styles["Heading2"],
                fontSize=14,
                spaceAfter=6,
                textColor=colors.black,
            )

            meta_style = ParagraphStyle(
                "Meta", parent=styles["Normal"], fontSize=10, textColor=colors.grey, spaceAfter=6
            )

            content_style = ParagraphStyle(
                "Content",
                parent=styles["Normal"],
                fontSize=11,
                spaceAfter=12,
                leftIndent=0.2 * inch,
            )

            # Build PDF content
            story = []

            # Title page
            story.append(Paragraph("Journal Export", title_style))
            story.append(
                Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", meta_style)
            )
            story.append(Paragraph(f"Total entries: {len(entries)}", meta_style))
            story.append(Spacer(1, 0.5 * inch))

            # Add entries
            for i, entry in enumerate(entries):
                if i > 0:
                    story.append(PageBreak())

                # Entry title
                title = entry.title or f"Entry from {entry.date_str}"
                story.append(Paragraph(html.escape(title), entry_title_style))

                # Entry metadata
                meta_info = f"Date: {entry.date_str} at {entry.time_str}"
                if entry.location:
                    meta_info += f" | Location: {entry.location}"
                if entry.mood:
                    meta_info += f" | Mood: {entry.mood_display}"
                if entry.weather_snapshot:
                    meta_info += f" | Weather: {entry.weather_display}"

                story.append(Paragraph(html.escape(meta_info), meta_style))

                # Entry content
                if entry.content:
                    # Remove HTML tags for PDF
                    import re

                    clean_content = re.sub(r"<[^>]+>", "", entry.content)
                    story.append(Paragraph(html.escape(clean_content), content_style))

                # Tags
                if entry.tags:
                    tags_text = f"Tags: {', '.join(entry.tags)}"
                    story.append(Paragraph(html.escape(tags_text), meta_style))

                story.append(Spacer(1, 0.2 * inch))

            # Build PDF
            doc.build(story)

            self.logger.info(f"Exported {len(entries)} entries to PDF: {file_path}")
            return True

        except ImportError:
            self.logger.error("ReportLab not installed. Cannot export to PDF.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to export to PDF: {e}")
            return False

    def import_from_json(self, file_path: str) -> tuple[int, int]:
        """Import entries from JSON file."""
        return self.repository.import_from_json(file_path)

    def cleanup(self):
        """Cleanup resources and stop auto-save timer."""
        self._stop_auto_save_timer()
        self.logger.info("Journal service cleaned up")
