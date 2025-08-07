"""Journal repository for data persistence and management."""

import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .journal_entry import JournalEntry, Mood


class JournalRepository:
    """Repository for managing journal entries with local persistence."""

    def __init__(self, data_dir: str = "data/journal"):
        """Initialize repository with data directory."""
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.entries_file = self.data_dir / "entries.json"
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # In-memory cache
        self._entries: Dict[str, JournalEntry] = {}
        self._loaded = False

        # Load existing entries
        self._load_entries()

    def _load_entries(self):
        """Load entries from JSON file."""
        try:
            if self.entries_file.exists():
                with open(self.entries_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for entry_data in data.get("entries", []):
                    try:
                        entry = JournalEntry.from_dict(entry_data)
                        self._entries[entry.id] = entry
                    except Exception as e:
                        self.logger.warning(f"Failed to load entry: {e}")

                self.logger.info(f"Loaded {len(self._entries)} journal entries")
            else:
                self.logger.info("No existing journal entries found")

        except Exception as e:
            self.logger.error(f"Failed to load journal entries: {e}")

        self._loaded = True

    def _save_entries(self, create_backup: bool = True):
        """Save entries to JSON file with optional backup."""
        try:
            # Create backup if requested and file exists
            if create_backup and self.entries_file.exists():
                self._create_backup()

            # Prepare data for saving
            data = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "entries": [entry.to_dict() for entry in self._entries.values()],
            }

            # Write to temporary file first
            temp_file = self.entries_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic move
            temp_file.replace(self.entries_file)

            self.logger.debug(f"Saved {len(self._entries)} journal entries")

        except Exception as e:
            self.logger.error(f"Failed to save journal entries: {e}")
            raise

    def _create_backup(self):
        """Create backup of current entries file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"entries_backup_{timestamp}.json"
            shutil.copy2(self.entries_file, backup_file)

            # Clean old backups (keep last 10)
            backups = sorted(self.backup_dir.glob("entries_backup_*.json"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()

        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")

    def create_entry(self, entry: JournalEntry) -> JournalEntry:
        """Create a new journal entry."""
        self._entries[entry.id] = entry
        self._save_entries()
        self.logger.info(f"Created journal entry: {entry.id}")
        return entry

    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Get entry by ID."""
        return self._entries.get(entry_id)

    def update_entry(self, entry: JournalEntry) -> JournalEntry:
        """Update existing entry."""
        if entry.id not in self._entries:
            raise ValueError(f"Entry {entry.id} not found")

        entry.updated_at = datetime.now()
        self._entries[entry.id] = entry
        self._save_entries()
        self.logger.info(f"Updated journal entry: {entry.id}")
        return entry

    def delete_entry(self, entry_id: str) -> bool:
        """Delete entry by ID."""
        if entry_id in self._entries:
            del self._entries[entry_id]
            self._save_entries()
            self.logger.info(f"Deleted journal entry: {entry_id}")
            return True
        return False

    def get_all_entries(self) -> List[JournalEntry]:
        """Get all entries sorted by creation date (newest first)."""
        return sorted(self._entries.values(), key=lambda e: e.created_at, reverse=True)

    def get_entries_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[JournalEntry]:
        """Get entries within date range."""
        entries = []
        for entry in self._entries.values():
            if start_date <= entry.created_at <= end_date:
                entries.append(entry)
        return sorted(entries, key=lambda e: e.created_at, reverse=True)

    def get_entries_by_mood(self, mood: Mood) -> List[JournalEntry]:
        """Get entries by mood."""
        entries = [entry for entry in self._entries.values() if entry.mood == mood]
        return sorted(entries, key=lambda e: e.created_at, reverse=True)

    def get_entries_by_location(self, location: str) -> List[JournalEntry]:
        """Get entries by location (case-insensitive partial match)."""
        location_lower = location.lower()
        entries = [
            entry for entry in self._entries.values() if location_lower in entry.location.lower()
        ]
        return sorted(entries, key=lambda e: e.created_at, reverse=True)

    def search_entries(self, query: str) -> List[JournalEntry]:
        """Search entries by content, title, or tags."""
        query_lower = query.lower()
        entries = []

        for entry in self._entries.values():
            # Search in title, content, and tags
            if (
                query_lower in entry.title.lower()
                or query_lower in entry.content.lower()
                or any(query_lower in tag.lower() for tag in entry.tags)
            ):
                entries.append(entry)

        return sorted(entries, key=lambda e: e.created_at, reverse=True)

    def get_entries_by_tag(self, tag: str) -> List[JournalEntry]:
        """Get entries by tag."""
        tag_lower = tag.lower()
        entries = [
            entry
            for entry in self._entries.values()
            if tag_lower in [t.lower() for t in entry.tags]
        ]
        return sorted(entries, key=lambda e: e.created_at, reverse=True)

    def get_mood_statistics(self) -> Dict[Mood, int]:
        """Get mood statistics across all entries."""
        mood_counts = {mood: 0 for mood in Mood}

        for entry in self._entries.values():
            if entry.mood:
                mood_counts[entry.mood] += 1

        return mood_counts

    def get_writing_frequency(self, days: int = 30) -> Dict[str, int]:
        """Get writing frequency over the last N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        frequency = {}
        current_date = start_date.date()

        while current_date <= end_date.date():
            frequency[current_date.strftime("%Y-%m-%d")] = 0
            current_date += timedelta(days=1)

        for entry in self._entries.values():
            if start_date <= entry.created_at <= end_date:
                date_key = entry.created_at.strftime("%Y-%m-%d")
                frequency[date_key] += 1

        return frequency

    def get_weather_mood_correlation(self) -> Dict[str, Dict[Mood, int]]:
        """Get correlation between weather conditions and moods."""
        correlation = {}

        for entry in self._entries.values():
            if entry.weather_snapshot and entry.mood:
                condition = entry.weather_snapshot.condition
                if condition not in correlation:
                    correlation[condition] = {mood: 0 for mood in Mood}
                correlation[condition][entry.mood] += 1

        return correlation

    def get_all_tags(self) -> List[Tuple[str, int]]:
        """Get all tags with their usage counts."""
        tag_counts = {}

        for entry in self._entries.values():
            for tag in entry.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    def get_word_cloud_data(self) -> Dict[str, int]:
        """Get word frequency data for word cloud generation."""
        import re
        from collections import Counter

        # Common stop words to exclude
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "among",
            "is",
            "was",
            "are",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "her",
            "its",
            "our",
            "their",
            "this",
            "that",
            "these",
            "those",
        }

        all_words = []

        for entry in self._entries.values():
            # Remove HTML tags and extract words
            clean_text = re.sub(r"<[^>]+>", "", entry.content)
            words = re.findall(r"\b\w+\b", clean_text.lower())

            # Filter out stop words and short words
            filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]

            all_words.extend(filtered_words)

        # Count word frequencies
        word_counts = Counter(all_words)

        # Return top 100 words
        return dict(word_counts.most_common(100))

    def export_to_json(self, file_path: str) -> bool:
        """Export all entries to JSON file."""
        try:
            export_data = {
                "export_date": datetime.now().isoformat(),
                "total_entries": len(self._entries),
                "entries": [entry.to_dict() for entry in self.get_all_entries()],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Exported {len(self._entries)} entries to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export entries: {e}")
            return False

    def import_from_json(self, file_path: str) -> Tuple[int, int]:
        """Import entries from JSON file. Returns (imported, skipped) counts."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            imported = 0
            skipped = 0

            for entry_data in data.get("entries", []):
                try:
                    entry = JournalEntry.from_dict(entry_data)

                    # Skip if entry already exists
                    if entry.id in self._entries:
                        skipped += 1
                        continue

                    self._entries[entry.id] = entry
                    imported += 1

                except Exception as e:
                    self.logger.warning(f"Failed to import entry: {e}")
                    skipped += 1

            if imported > 0:
                self._save_entries()

            self.logger.info(f"Imported {imported} entries, skipped {skipped}")
            return imported, skipped

        except Exception as e:
            self.logger.error(f"Failed to import entries: {e}")
            return 0, 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about journal entries."""
        entries = list(self._entries.values())

        if not entries:
            return {
                "total_entries": 0,
                "total_words": 0,
                "average_words_per_entry": 0,
                "mood_distribution": {},
                "writing_streak": 0,
                "most_productive_day": None,
                "favorite_location": None,
            }

        # Basic stats
        total_entries = len(entries)
        total_words = sum(entry.word_count for entry in entries)
        average_words = total_words / total_entries if total_entries > 0 else 0

        # Mood distribution
        mood_stats = self.get_mood_statistics()
        mood_distribution = {mood.value: count for mood, count in mood_stats.items()}

        # Writing streak (consecutive days with entries)
        dates = sorted([entry.created_at.date() for entry in entries], reverse=True)
        streak = 0
        current_date = datetime.now().date()

        for date in dates:
            if date == current_date or date == current_date - timedelta(days=1):
                streak += 1
                current_date = date - timedelta(days=1)
            else:
                break

        # Most productive day (day of week with most entries)
        day_counts = {}
        for entry in entries:
            day = entry.created_at.strftime("%A")
            day_counts[day] = day_counts.get(day, 0) + 1

        most_productive_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None

        # Favorite location
        location_counts = {}
        for entry in entries:
            if entry.location:
                location_counts[entry.location] = location_counts.get(entry.location, 0) + 1

        favorite_location = (
            max(location_counts.items(), key=lambda x: x[1])[0] if location_counts else None
        )

        return {
            "total_entries": total_entries,
            "total_words": total_words,
            "average_words_per_entry": round(average_words, 1),
            "mood_distribution": mood_distribution,
            "writing_streak": streak,
            "most_productive_day": most_productive_day,
            "favorite_location": favorite_location,
            "first_entry_date": min(entry.created_at for entry in entries).strftime("%Y-%m-%d"),
            "last_entry_date": max(entry.created_at for entry in entries).strftime("%Y-%m-%d"),
        }
