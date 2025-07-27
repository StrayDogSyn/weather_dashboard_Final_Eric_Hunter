#!/usr/bin/env python3
"""
Weather Journal Utilities - Helper functions and formatters

This module contains utility functions, formatters, and helper methods
used throughout the Weather Journal feature.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from .models import JournalEntry


def format_entry_as_text(entry: JournalEntry) -> str:
    """Format entry as plain text."""
    lines = []

    # Title
    lines.append(entry.title or "Untitled Entry")
    lines.append("=" * len(lines[0]))
    lines.append("")

    # Metadata
    if entry.created_at:
        lines.append(f"Date: {entry.created_at.strftime('%B %d, %Y at %I:%M %p')}")

    if entry.mood:
        lines.append(f"Mood: {entry.mood.value}")

    if entry.tags:
        lines.append(f"Tags: {', '.join(entry.tags)}")

    if entry.weather_condition:
        weather_info = f"Weather: {entry.weather_condition}"
        if entry.weather_temperature:
            weather_info += f", {entry.weather_temperature}°F"
        if entry.weather_location:
            weather_info += f" in {entry.weather_location}"
        lines.append(weather_info)

    lines.append(f"Word Count: {entry.word_count}")
    lines.append(f"Reading Time: {entry.reading_time} min")
    lines.append("")

    # Content
    lines.append("Content:")
    lines.append("-" * 8)
    lines.append(entry.content or "")

    return "\n".join(lines)


def format_entry_as_markdown(entry: JournalEntry) -> str:
    """Format entry as Markdown."""
    lines = []

    # Title
    lines.append(f"# {entry.title or 'Untitled Entry'}")
    lines.append("")

    # Metadata table
    lines.append("## Entry Details")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")

    if entry.created_at:
        lines.append(f"| Date | {entry.created_at.strftime('%B %d, %Y at %I:%M %p')} |")

    if entry.mood:
        lines.append(f"| Mood | {entry.mood.value} |")

    if entry.tags:
        lines.append(f"| Tags | {', '.join(entry.tags)} |")

    if entry.weather_condition:
        weather_info = entry.weather_condition
        if entry.weather_temperature:
            weather_info += f", {entry.weather_temperature}°F"
        lines.append(f"| Weather | {weather_info} |")

    lines.append(f"| Word Count | {entry.word_count} |")
    lines.append(f"| Reading Time | {entry.reading_time} min |")
    lines.append("")

    # Content
    lines.append("## Content")
    lines.append("")
    lines.append(entry.content or "")

    return "\n".join(lines)


def export_entries_to_json(entries: List[JournalEntry], filename: str) -> bool:
    """Export entries to JSON file."""
    try:
        entries_data = [entry.to_dict() for entry in entries]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(entries_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def export_entries_to_csv(entries: List[JournalEntry], filename: str) -> bool:
    """Export entries to CSV file."""
    try:
        import csv
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'ID', 'Title', 'Content', 'Mood', 'Tags', 'Created', 'Updated',
                'Weather Condition', 'Temperature', 'Word Count', 'Is Favorite'
            ])

            # Data
            for entry in entries:
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
        return True
    except Exception:
        return False


def calculate_mood_analytics(entries: List[JournalEntry]) -> Dict[str, Any]:
    """Calculate mood analytics and correlations."""
    # Mood distribution
    mood_stats = {}
    for entry in entries:
        if entry.mood:
            mood_value = entry.mood.value
            mood_stats[mood_value] = mood_stats.get(mood_value, 0) + 1

    # Weather-mood correlations
    weather_mood_correlation = {}
    for entry in entries:
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
        'total_entries': len(entries),
        'entries_with_mood': len([e for e in entries if e.mood]),
        'entries_with_weather': len([e for e in entries if e.weather_condition])
    }


def sanitize_filename(title: str) -> str:
    """Sanitize a string for use as a filename."""
    if not title:
        return "journal_entry"
    
    # Remove invalid characters and replace with underscores
    safe_title = re.sub(r'[^\w\s-]', '', title).strip()
    safe_title = re.sub(r'[-\s]+', '_', safe_title)
    
    # Ensure it's not too long
    if len(safe_title) > 50:
        safe_title = safe_title[:50]
    
    return safe_title or "journal_entry"


def generate_export_filename(entry: JournalEntry, file_type: str = "txt") -> str:
    """Generate a default filename for exporting an entry."""
    title = entry.title or "journal_entry"
    safe_title = sanitize_filename(title)
    date_str = datetime.now().strftime('%Y%m%d')
    return f"{safe_title}_{date_str}.{file_type}"


def parse_tags_string(tags_string: str) -> List[str]:
    """Parse a comma-separated tags string into a list."""
    if not tags_string.strip():
        return []
    
    tags = [tag.strip().lower() for tag in tags_string.split(",") if tag.strip()]
    return tags


def format_tags_for_display(tags: List[str]) -> str:
    """Format tags list for display."""
    if not tags:
        return ""
    return ", ".join(tags)


def calculate_reading_time(content: str) -> int:
    """Calculate estimated reading time in minutes."""
    if not content:
        return 0
    
    words = len(content.split())
    # Assume 200 words per minute reading speed
    return max(1, words // 200)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


def format_date_for_display(date: datetime) -> str:
    """Format datetime for display in UI."""
    if not date:
        return "Unknown"
    
    return date.strftime("%m/%d/%Y")


def format_datetime_for_display(date: datetime) -> str:
    """Format datetime with time for display in UI."""
    if not date:
        return "Unknown"
    
    return date.strftime("%B %d, %Y at %I:%M %p")


def validate_entry_data(title: str, content: str) -> Dict[str, str]:
    """Validate entry data and return error messages."""
    errors = {}
    
    if not title.strip():
        errors['title'] = "Title cannot be empty"
    elif len(title.strip()) > 200:
        errors['title'] = "Title cannot exceed 200 characters"
    
    if not content.strip():
        errors['content'] = "Content cannot be empty"
    elif len(content.strip()) > 100000:  # 100k character limit
        errors['content'] = "Content cannot exceed 100,000 characters"
    
    return errors


def extract_weather_info_from_entry(entry: JournalEntry) -> str:
    """Extract weather information as a formatted string."""
    if not entry.weather_condition:
        return "Weather: Not available"
    
    weather_text = f"Weather: {entry.weather_condition}"
    if entry.weather_temperature:
        weather_text += f", {entry.weather_temperature}°F"
    if entry.weather_location:
        weather_text += f" in {entry.weather_location}"
    
    return weather_text


def search_entries_by_content(entries: List[JournalEntry], query: str) -> List[JournalEntry]:
    """Simple client-side search through entries."""
    if not query.strip():
        return entries
    
    query = query.lower()
    results = []
    
    for entry in entries:
        # Search in title, content, and tags
        if (query in entry.title.lower() or 
            query in entry.content.lower() or 
            any(query in tag.lower() for tag in entry.tags) or
            (entry.weather_condition and query in entry.weather_condition.lower())):
            results.append(entry)
    
    return results