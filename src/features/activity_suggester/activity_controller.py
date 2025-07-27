"""
Activity Controller

This module contains the business logic and controller methods for the Activity Suggester.
It handles data processing, suggestion generation, user interactions, and state management.
"""

import threading
from typing import List, Optional, Dict, Any
from tkinter import messagebox
import webbrowser
import json
from datetime import datetime

from .models import (
    ActivitySuggestion, ActivityCategory, DifficultyLevel, 
    WeatherSuitability, UserPreferences, WeatherData
)
from .database import ActivityDatabase
from .ai_service import AIActivityGenerator
from .spotify_service import SpotifyIntegration
from ..shared.logger_mixin import LoggerMixin


class ActivityController(LoggerMixin):
    """Controller class for managing activity suggestion business logic."""
    
    def __init__(self, parent_widget):
        """Initialize controller with parent widget."""
        self.parent = parent_widget
        
        # State management
        self.current_weather: Optional[WeatherData] = None
        self.current_suggestions: List[ActivitySuggestion] = []
        self.selected_activity: Optional[ActivitySuggestion] = None
        self.is_generating = False
        self.generation_thread: Optional[threading.Thread] = None
    
    def configure_api_keys(self, gemini_api_key: Optional[str] = None,
                          spotify_client_id: Optional[str] = None,
                          spotify_client_secret: Optional[str] = None):
        """Configure API keys for AI and Spotify integration."""
        if gemini_api_key:
            self.parent.ai_generator = AIActivityGenerator(api_key=gemini_api_key)
            self.logger.info("Configured Gemini AI integration")

        if spotify_client_id and spotify_client_secret:
            self.parent.spotify_integration = SpotifyIntegration(
                client_id=spotify_client_id,
                client_secret=spotify_client_secret
            )
            self.logger.info("Configured Spotify integration")
    
    def load_recent_suggestions(self):
        """Load recent suggestions from database."""
        try:
            recent_activities = self.parent.activity_db.load_activities(limit=10)
            if recent_activities:
                self.current_suggestions = recent_activities
                self.parent.ui_components._update_suggestions_display()

        except Exception as e:
            self.logger.error(f"Error loading recent suggestions: {e}")
    
    def generate_suggestions(self):
        """Generate new activity suggestions."""
        if self.is_generating:
            return

        self.is_generating = True
        self.parent._update_status("Generating suggestions...")
        self.parent._show_loading()

        # Disable generate button
        self.parent.generate_button.configure(state="disabled", text="🔄 Generating...")

        # Start generation in background thread
        self.generation_thread = threading.Thread(
            target=self._generate_suggestions_background,
            daemon=True
        )
        self.generation_thread.start()
    
    def _generate_suggestions_background(self):
        """Generate suggestions in background thread."""
        try:
            # Generate suggestions using AI
            suggestions = self.parent.ai_generator.generate_suggestions(
                weather_data=self.current_weather or self._get_default_weather(),
                user_preferences=self.parent.user_preferences,
                count=6
            )

            # Save suggestions to database
            for suggestion in suggestions:
                suggestion.times_suggested += 1
                self.parent.activity_db.save_activity(suggestion)
                self.parent.activity_db.log_activity_action(suggestion.id, "suggested")

            # Update UI on main thread
            self.parent.after(0, lambda: self._on_suggestions_generated(suggestions))

        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            self.parent.after(0, lambda: self._on_generation_error(str(e)))
    
    def _on_suggestions_generated(self, suggestions: List[ActivitySuggestion]):
        """Handle successful suggestion generation."""
        self.current_suggestions = suggestions
        self.is_generating = False

        # Update UI
        self.parent._hide_loading()
        self.parent._update_suggestions_display()
        self.parent._update_status(f"Generated {len(suggestions)} new suggestions")

        # Re-enable generate button
        self.parent.generate_button.configure(state="normal", text="🔄 Generate New")

        self.logger.info(f"Successfully generated {len(suggestions)} suggestions")
    
    def _on_generation_error(self, error_message: str):
        """Handle suggestion generation error."""
        self.is_generating = False

        # Update UI
        self.parent._hide_loading()
        self.parent._update_status(f"Error: {error_message}")

        # Re-enable generate button
        self.parent.generate_button.configure(state="normal", text="🔄 Generate New")

        # Show error message
        messagebox.showerror("Generation Error", f"Failed to generate suggestions:\n{error_message}")
    
    def filter_suggestions(self, suggestions: List[ActivitySuggestion]) -> List[ActivitySuggestion]:
        """Filter suggestions based on current filter settings."""
        filtered = suggestions

        # Category filter
        if self.parent.category_var.get() != "all":
            category = ActivityCategory(self.parent.category_var.get())
            filtered = [s for s in filtered if s.category == category]

        # Difficulty filter
        if self.parent.difficulty_var.get() != "all":
            difficulty = DifficultyLevel(self.parent.difficulty_var.get())
            filtered = [s for s in filtered if s.difficulty == difficulty]

        # Duration filter
        max_duration = self.parent.duration_var.get()
        filtered = [s for s in filtered if s.duration_minutes <= max_duration]

        # Favorites filter
        if self.parent.show_favorites_var.get():
            filtered = [s for s in filtered if s.is_favorite]

        return filtered
    
    def toggle_favorite(self, suggestion: ActivitySuggestion):
        """Toggle favorite status of an activity."""
        suggestion.is_favorite = not suggestion.is_favorite
        self.parent.activity_db.save_activity(suggestion)
        self.parent.activity_db.log_activity_action(
            suggestion.id,
            "favorited" if suggestion.is_favorite else "unfavorited"
        )

        # Update display
        self.parent._update_suggestions_display()

        self.logger.info(f"Toggled favorite for activity: {suggestion.title}")
    
    def mark_activity_complete(self, suggestion: ActivitySuggestion):
        """Mark an activity as completed."""
        suggestion.times_completed += 1
        self.parent.activity_db.save_activity(suggestion)
        self.parent.activity_db.log_activity_action(suggestion.id, "completed")

        # Show completion message
        messagebox.showinfo(
            "Activity Completed",
            f"Great job completing '{suggestion.title}'!\n\nWould you like to rate this activity?"
        )

        # Show rating dialog
        self.parent.ui_components.show_rating_dialog(suggestion)

        self.logger.info(f"Marked activity complete: {suggestion.title}")
    
    def get_activity_music(self, suggestion: ActivitySuggestion):
        """Get music recommendations for activity."""
        try:
            # Determine mood based on activity
            mood_mapping = {
                ActivityCategory.OUTDOOR: "energetic",
                ActivityCategory.INDOOR: "relaxed",
                ActivityCategory.EXERCISE: "workout",
                ActivityCategory.CREATIVE: "focus",
                ActivityCategory.SOCIAL: "party",
                ActivityCategory.RELAXATION: "chill"
            }

            mood = mood_mapping.get(suggestion.category, "happy")

            # Get weather-based mood adjustment
            if hasattr(self, 'current_weather') and self.current_weather:
                weather_condition = self.current_weather.condition.lower()
                if 'rain' in weather_condition or 'storm' in weather_condition:
                    mood = "rainy"
                elif 'snow' in weather_condition:
                    mood = "winter"
                elif 'sun' in weather_condition or 'clear' in weather_condition:
                    mood = "sunny"

            # Get playlist
            playlist = self.parent.spotify_integration.get_mood_playlist(mood)

            if playlist:
                # Show music window
                self.parent.ui_components.show_music_window(suggestion, playlist)
            else:
                messagebox.showinfo(
                    "Music Unavailable",
                    "Unable to get music recommendations at this time."
                )

        except Exception as e:
            self.logger.error(f"Error getting activity music: {e}")
            messagebox.showerror("Error", "Failed to get music recommendations.")
    
    def set_weather_data(self, weather_data: dict):
        """Set current weather data for activity suggestions."""
        self.current_weather = weather_data
        self.logger.info("Updated weather data for activity suggestions")
    
    def set_user_preferences(self, preferences: UserPreferences):
        """Set user preferences for activity suggestions."""
        self.parent.user_preferences = preferences
        self.parent.activity_db.save_user_preferences(preferences)
        self.logger.info("Updated user preferences")
    
    def get_user_preferences(self) -> UserPreferences:
        """Get current user preferences."""
        return self.parent.user_preferences
    
    def refresh_suggestions(self):
        """Refresh activity suggestions."""
        self.generate_suggestions()
    
    def get_activity_stats(self) -> dict:
        """Get activity statistics."""
        return self.parent.activity_db.get_activity_stats()
    
    def export_activity_data(self, file_path: str) -> bool:
        """Export activity data to JSON file."""
        try:
            from dataclasses import asdict
            
            data = {
                'activities': [asdict(activity) for activity in self.parent.activity_db.get_all_activities()],
                'preferences': asdict(self.parent.user_preferences),
                'stats': self.get_activity_stats(),
                'exported_at': datetime.now().isoformat()
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Exported activity data to: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting activity data: {e}")
            return False
    
    def _get_default_weather(self) -> dict:
        """Get default weather data for testing."""
        return {
            'condition': 'partly_cloudy',
            'temperature': 20,
            'humidity': 60,
            'wind_speed': 10
        }
    
    def on_filter_changed(self, *args):
        """Handle filter changes."""
        # Update duration label
        self.parent.duration_value_label.configure(text=f"{self.parent.duration_var.get()} min")

        # Update suggestions display
        self.parent._update_suggestions_display()
    
    def show_preferences_dialog(self):
        """Show user preferences dialog."""
        self.parent.ui_components.show_preferences_dialog(self.parent.user_preferences)
    
    def show_analytics_dialog(self):
        """Show activity analytics dialog."""
        stats = self.parent.activity_db.get_activity_stats()
        self.parent.ui_components.show_analytics_dialog(stats)
    
    def export_activities(self):
        """Export activities to a file."""
        try:
            activities = self.parent.activity_db.load_activities(limit=1000)
            self.parent.ui_components.show_export_dialog(activities, self.parent.user_preferences)
                
        except Exception as e:
            self.logger.error(f"Error exporting activities: {e}")
            self.parent.ui_components.show_export_error(str(e))