"""
UI Components for Activity Suggester

This module contains all UI-related methods for creating cards, dialogs,
and other visual components used in the Activity Suggester widget.
"""

import customtkinter as ctk
import webbrowser
from tkinter import messagebox, filedialog
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from .models import (
    ActivitySuggestion, ActivityCategory, DifficultyLevel, 
    WeatherSuitability, UserPreferences
)
from ...ui.components.base_components import (
    GlassFrame, GlassLabel, GlassButton
)


class ActivityUIComponents:
    """Helper class for creating UI components for the Activity Suggester."""
    
    def __init__(self, parent_widget):
        """Initialize with parent widget for context."""
        self.parent = parent_widget
        
    def create_suggestion_card(self, suggestion: ActivitySuggestion, index: int) -> ctk.CTkFrame:
        """Create a glassmorphic suggestion card."""
        # Main card frame
        card = GlassFrame(self.parent.suggestions_scroll)
        card.grid_columnconfigure(1, weight=1)

        # Category icon and color
        category_colors = {
            ActivityCategory.OUTDOOR: "#4CAF50",
            ActivityCategory.INDOOR: "#2196F3",
            ActivityCategory.SPORTS: "#FF9800",
            ActivityCategory.CREATIVE: "#9C27B0",
            ActivityCategory.SOCIAL: "#E91E63",
            ActivityCategory.RELAXATION: "#00BCD4",
            ActivityCategory.EXERCISE: "#F44336",
            ActivityCategory.ENTERTAINMENT: "#FFEB3B",
            ActivityCategory.EDUCATIONAL: "#795548",
            ActivityCategory.CULINARY: "#FF5722"
        }

        category_icons = {
            ActivityCategory.OUTDOOR: "🌲",
            ActivityCategory.INDOOR: "🏠",
            ActivityCategory.SPORTS: "⚽",
            ActivityCategory.CREATIVE: "🎨",
            ActivityCategory.SOCIAL: "👥",
            ActivityCategory.RELAXATION: "🧘",
            ActivityCategory.EXERCISE: "💪",
            ActivityCategory.ENTERTAINMENT: "🎬",
            ActivityCategory.EDUCATIONAL: "📚",
            ActivityCategory.CULINARY: "🍳"
        }

        # Left side - Category icon
        icon_frame = ctk.CTkFrame(
            card,
            width=60,
            height=60,
            fg_color=category_colors.get(suggestion.category, "#757575")
        )
        icon_frame.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(15, 10), pady=15)
        icon_frame.grid_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_frame,
            text=category_icons.get(suggestion.category, "🎯"),
            font=("Segoe UI", 24)
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Main content area
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=15)
        content_frame.grid_columnconfigure(0, weight=1)

        # Title and favorite button
        title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        title_frame.grid_columnconfigure(0, weight=1)

        title_label = GlassLabel(
            title_frame,
            text=suggestion.title,
            font=("Segoe UI", 16, "bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="ew")

        favorite_button = GlassButton(
            title_frame,
            text="⭐" if suggestion.is_favorite else "☆",
            width=30,
            height=30,
            command=lambda s=suggestion: self.parent._toggle_favorite(s)
        )
        favorite_button.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Description
        desc_label = GlassLabel(
            content_frame,
            text=suggestion.description,
            font=("Segoe UI", 11),
            anchor="w",
            wraplength=400
        )
        desc_label.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Metadata row
        meta_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        meta_frame.grid(row=2, column=0, sticky="ew")

        # Duration and difficulty
        duration_label = GlassLabel(
            meta_frame,
            text=f"⏱️ {suggestion.duration_minutes}min",
            font=("Segoe UI", 10)
        )
        duration_label.pack(side="left", padx=(0, 15))

        difficulty_label = GlassLabel(
            meta_frame,
            text=f"📊 {suggestion.difficulty.value.title()}",
            font=("Segoe UI", 10)
        )
        difficulty_label.pack(side="left", padx=(0, 15))

        # Weather suitability
        suitability_colors = {
            WeatherSuitability.PERFECT: "#4CAF50",
            WeatherSuitability.GOOD: "#8BC34A",
            WeatherSuitability.FAIR: "#FFC107",
            WeatherSuitability.POOR: "#FF9800",
            WeatherSuitability.UNSUITABLE: "#F44336"
        }

        suitability_label = GlassLabel(
            meta_frame,
            text=f"🌤️ {suggestion.weather_suitability.value.title()}",
            font=("Segoe UI", 10),
            text_color=suitability_colors.get(suggestion.weather_suitability, "#757575")
        )
        suitability_label.pack(side="left", padx=(0, 15))

        # Cost estimate
        cost_label = GlassLabel(
            meta_frame,
            text=f"💰 {suggestion.cost_estimate.title()}",
            font=("Segoe UI", 10)
        )
        cost_label.pack(side="left")

        # Action buttons
        actions_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        details_button = GlassButton(
            actions_frame,
            text="📋 Details",
            width=80,
            height=28,
            command=lambda s=suggestion: self.show_activity_details(s)
        )
        details_button.pack(side="left", padx=(0, 10))

        complete_button = GlassButton(
            actions_frame,
            text="✅ Mark Complete",
            width=120,
            height=28,
            command=lambda s=suggestion: self.parent._mark_activity_complete(s)
        )
        complete_button.pack(side="left", padx=(0, 10))

        if self.parent.spotify_integration.spotify:
            music_button = GlassButton(
                actions_frame,
                text="🎵 Music",
                width=80,
                height=28,
                command=lambda s=suggestion: self.parent._get_activity_music(s)
            )
            music_button.pack(side="left")

        return card
    
    def show_activity_details(self, suggestion: ActivitySuggestion):
        """Show detailed activity information."""
        details_window = ctk.CTkToplevel(self.parent)
        details_window.title(f"Activity Details - {suggestion.title}")
        details_window.geometry("500x600")
        details_window.transient(self.parent)

        # Main content frame
        content_frame = GlassFrame(details_window)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = GlassLabel(
            content_frame,
            text=suggestion.title,
            font=("Segoe UI", 20, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Description
        desc_frame = GlassFrame(content_frame)
        desc_frame.pack(fill="x", pady=(0, 10))

        desc_title = GlassLabel(desc_frame, text="Description:", font=("Segoe UI", 12, "bold"))
        desc_title.pack(anchor="w", padx=10, pady=(10, 5))

        desc_text = GlassLabel(
            desc_frame,
            text=suggestion.description,
            font=("Segoe UI", 11),
            wraplength=450,
            justify="left"
        )
        desc_text.pack(anchor="w", padx=10, pady=(0, 10))

        # Details grid
        details_frame = GlassFrame(content_frame)
        details_frame.pack(fill="x", pady=(0, 10))

        details_info = [
            ("Category:", suggestion.category.value.title()),
            ("Difficulty:", suggestion.difficulty.value.title()),
            ("Duration:", f"{suggestion.duration_minutes} minutes"),
            ("Weather Suitability:", suggestion.weather_suitability.value.title()),
            ("Location Type:", suggestion.location_type.title()),
            ("Cost Estimate:", suggestion.cost_estimate.title()),
            ("Group Size:", suggestion.group_size.title()),
            ("Times Suggested:", str(suggestion.times_suggested)),
            ("Times Completed:", str(suggestion.times_completed))
        ]

        for i, (label, value) in enumerate(details_info):
            row_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)

            label_widget = GlassLabel(row_frame, text=label, font=("Segoe UI", 11, "bold"))
            label_widget.pack(side="left")

            value_widget = GlassLabel(row_frame, text=value, font=("Segoe UI", 11))
            value_widget.pack(side="right")

        # Required items
        if suggestion.required_items:
            items_frame = GlassFrame(content_frame)
            items_frame.pack(fill="x", pady=(0, 10))

            items_title = GlassLabel(items_frame, text="Required Items:", font=("Segoe UI", 12, "bold"))
            items_title.pack(anchor="w", padx=10, pady=(10, 5))

            items_text = GlassLabel(
                items_frame,
                text="• " + "\n• ".join(suggestion.required_items),
                font=("Segoe UI", 11),
                justify="left"
            )
            items_text.pack(anchor="w", padx=10, pady=(0, 10))

        # AI reasoning
        if suggestion.ai_reasoning:
            reasoning_frame = GlassFrame(content_frame)
            reasoning_frame.pack(fill="x", pady=(0, 10))

            reasoning_title = GlassLabel(reasoning_frame, text="AI Reasoning:", font=("Segoe UI", 12, "bold"))
            reasoning_title.pack(anchor="w", padx=10, pady=(10, 5))

            reasoning_text = GlassLabel(
                reasoning_frame,
                text=suggestion.ai_reasoning,
                font=("Segoe UI", 11),
                wraplength=450,
                justify="left"
            )
            reasoning_text.pack(anchor="w", padx=10, pady=(0, 10))

        # Action buttons
        actions_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(10, 0))

        close_button = GlassButton(
            actions_frame,
            text="Close",
            command=details_window.destroy,
            width=100
        )
        close_button.pack(side="right", padx=(10, 0))

        complete_button = GlassButton(
            actions_frame,
            text="Mark Complete",
            command=lambda: [self.parent._mark_activity_complete(suggestion), details_window.destroy()],
            width=120
        )
        complete_button.pack(side="right")
    
    def show_rating_dialog(self, suggestion: ActivitySuggestion):
        """Show rating dialog for completed activity."""
        rating_window = ctk.CTkToplevel(self.parent)
        rating_window.title("Rate Activity")
        rating_window.geometry("400x300")
        rating_window.transient(self.parent)

        # Main content
        content_frame = GlassFrame(rating_window)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = GlassLabel(
            content_frame,
            text=f"How was '{suggestion.title}'?",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Rating stars
        rating_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        rating_frame.pack(pady=(0, 20))

        rating_var = ctk.IntVar(value=5)

        for i in range(1, 6):
            star_button = GlassButton(
                rating_frame,
                text="⭐",
                width=40,
                height=40,
                command=lambda r=i: rating_var.set(r)
            )
            star_button.pack(side="left", padx=2)

        # Feedback text
        feedback_label = GlassLabel(content_frame, text="Additional feedback (optional):")
        feedback_label.pack(anchor="w", pady=(0, 5))

        feedback_text = ctk.CTkTextbox(content_frame, height=80)
        feedback_text.pack(fill="x", pady=(0, 20))

        # Buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        def save_rating():
            rating = rating_var.get()
            feedback = feedback_text.get("1.0", "end-1c").strip()

            # Save rating to database
            self.parent.activity_db.save_activity_rating(suggestion.id, rating, feedback)

            # Update suggestion rating
            suggestion.user_rating = rating
            self.parent.activity_db.save_activity(suggestion)

            rating_window.destroy()
            self.parent.logger.info(f"Saved rating {rating}/5 for activity: {suggestion.title}")

        cancel_button = GlassButton(
            button_frame,
            text="Skip",
            command=rating_window.destroy,
            width=80
        )
        cancel_button.pack(side="right", padx=(10, 0))

        save_button = GlassButton(
            button_frame,
            text="Save Rating",
            command=save_rating,
            width=100
        )
        save_button.pack(side="right")
    
    def show_music_window(self, suggestion: ActivitySuggestion, playlist: dict):
        """Show music recommendations window."""
        music_window = ctk.CTkToplevel(self.parent)
        music_window.title(f"Music for {suggestion.title}")
        music_window.geometry("500x400")
        music_window.transient(self.parent)

        # Main content
        content_frame = GlassFrame(music_window)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = GlassLabel(
            content_frame,
            text=f"🎵 Music for {suggestion.title}",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Playlist info
        if playlist.get('name'):
            playlist_label = GlassLabel(
                content_frame,
                text=f"Playlist: {playlist['name']}",
                font=("Segoe UI", 12)
            )
            playlist_label.pack(pady=(0, 10))

        # Tracks list
        tracks_frame = GlassFrame(content_frame)
        tracks_frame.pack(fill="both", expand=True, pady=(0, 10))

        tracks_label = GlassLabel(tracks_frame, text="Recommended Tracks:", font=("Segoe UI", 12, "bold"))
        tracks_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Scrollable tracks list
        tracks_scroll = ctk.CTkScrollableFrame(tracks_frame)
        tracks_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        tracks = playlist.get('tracks', [])
        for track in tracks[:10]:  # Show first 10 tracks
            track_frame = ctk.CTkFrame(tracks_scroll, fg_color="transparent")
            track_frame.pack(fill="x", pady=2)

            track_text = f"♪ {track.get('name', 'Unknown')} - {track.get('artist', 'Unknown Artist')}"
            track_label = GlassLabel(track_frame, text=track_text, font=("Segoe UI", 10))
            track_label.pack(anchor="w", padx=5)

        # Action buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        close_button = GlassButton(
            button_frame,
            text="Close",
            command=music_window.destroy,
            width=80
        )
        close_button.pack(side="right", padx=(10, 0))

        if playlist.get('external_url'):
            open_button = GlassButton(
                button_frame,
                text="Open in Spotify",
                command=lambda: webbrowser.open(playlist['external_url']),
                width=120
            )
            open_button.pack(side="right")
    
    def show_preferences_dialog(self, user_preferences: UserPreferences):
        """Show user preferences dialog."""
        preferences_window = ctk.CTkToplevel(self.parent)
        preferences_window.title("Activity Preferences")
        preferences_window.geometry("600x500")
        preferences_window.transient(self.parent)

        # Main content frame
        content_frame = GlassFrame(preferences_window)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = GlassLabel(
            content_frame,
            text="⚙️ Activity Preferences",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Preferences form
        prefs_frame = GlassFrame(content_frame)
        prefs_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Category preferences
        cat_label = GlassLabel(prefs_frame, text="Preferred Categories:", font=("Segoe UI", 12, "bold"))
        cat_label.pack(anchor="w", padx=10, pady=(10, 5))

        pref_categories = {}
        for category in ActivityCategory:
            var = ctk.BooleanVar(value=category in user_preferences.preferred_categories)
            checkbox = ctk.CTkCheckBox(prefs_frame, text=category.value.title(), variable=var)
            checkbox.pack(anchor="w", padx=20, pady=2)
            pref_categories[category] = var

        # Difficulty preferences
        diff_label = GlassLabel(prefs_frame, text="Preferred Difficulty:", font=("Segoe UI", 12, "bold"))
        diff_label.pack(anchor="w", padx=10, pady=(15, 5))

        pref_difficulties = {}
        for difficulty in DifficultyLevel:
            var = ctk.BooleanVar(value=difficulty in user_preferences.preferred_difficulty)
            checkbox = ctk.CTkCheckBox(prefs_frame, text=difficulty.value.title(), variable=var)
            checkbox.pack(anchor="w", padx=20, pady=2)
            pref_difficulties[difficulty] = var

        # Max duration
        duration_label = GlassLabel(prefs_frame, text="Max Duration (minutes):", font=("Segoe UI", 12, "bold"))
        duration_label.pack(anchor="w", padx=10, pady=(15, 5))

        pref_duration = ctk.IntVar(value=user_preferences.max_duration_minutes)
        duration_slider = ctk.CTkSlider(prefs_frame, from_=15, to=300, variable=pref_duration)
        duration_slider.pack(fill="x", padx=20, pady=5)

        duration_value = GlassLabel(prefs_frame, text=f"{user_preferences.max_duration_minutes} min")
        duration_value.pack(anchor="w", padx=20)

        # Buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        def save_preferences():
            # Update preferences
            user_preferences.preferred_categories = [
                cat for cat, var in pref_categories.items() if var.get()
            ]
            user_preferences.preferred_difficulty = [
                diff for diff, var in pref_difficulties.items() if var.get()
            ]
            user_preferences.max_duration_minutes = pref_duration.get()

            # Save to database
            self.parent.activity_db.save_user_preferences(user_preferences)

            # Close window
            preferences_window.destroy()

            # Refresh suggestions
            self.parent._generate_suggestions()

            self.parent.logger.info("User preferences saved")

        save_button = GlassButton(
            button_frame,
            text="💾 Save Preferences",
            command=save_preferences,
            width=150
        )
        save_button.pack(side="right", padx=(10, 0))

        cancel_button = GlassButton(
            button_frame,
            text="❌ Cancel",
            command=preferences_window.destroy,
            width=100
        )
        cancel_button.pack(side="right")
    
    def show_analytics_dialog(self, stats: Dict[str, Any]):
        """Show activity analytics dialog."""
        analytics_window = ctk.CTkToplevel(self.parent)
        analytics_window.title("Activity Analytics")
        analytics_window.geometry("700x600")
        analytics_window.transient(self.parent)

        # Main content frame
        content_frame = GlassFrame(analytics_window)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = GlassLabel(
            content_frame,
            text="📊 Activity Analytics",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Analytics content
        analytics_frame = GlassFrame(content_frame)
        analytics_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Basic stats
        stats_text = f"""📈 Activity Statistics:

• Total Activities: {stats.get('total_activities', 0)}
• Favorites: {stats.get('favorites_count', 0)}
• Most Popular Category: {stats.get('popular_category', 'N/A')}
• Average Rating: {stats.get('average_rating', 'N/A')}
• Total Completions: {stats.get('total_completions', 0)}

🏆 Top Activities:"""

        for i, activity in enumerate(stats.get('popular_activities', [])[:5], 1):
            stats_text += f"\n{i}. {activity.get('title', 'Unknown')} ({activity.get('times_suggested', 0)} suggestions)"

        stats_label = GlassLabel(
            analytics_frame,
            text=stats_text,
            font=("Segoe UI", 11),
            justify="left",
            anchor="nw"
        )
        stats_label.pack(fill="both", expand=True, padx=10, pady=10)

        # Close button
        close_button = GlassButton(
            content_frame,
            text="✅ Close",
            command=analytics_window.destroy,
            width=100
        )
        close_button.pack()
    
    def show_export_dialog(self, activities: List[ActivitySuggestion], user_preferences: UserPreferences):
        """Show export activities dialog."""
        try:
            # Ask user for file location
            file_path = filedialog.asksaveasfilename(
                title="Export Activities",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                # Convert to exportable format
                export_data = {
                    "export_date": datetime.now().isoformat(),
                    "total_activities": len(activities),
                    "user_preferences": user_preferences.to_dict(),
                    "activities": [
                        {
                            "id": activity.id,
                            "title": activity.title,
                            "description": activity.description,
                            "category": activity.category.value,
                            "difficulty": activity.difficulty.value,
                            "duration_minutes": activity.duration_minutes,
                            "weather_suitability": activity.weather_suitability.value,
                            "required_items": activity.required_items,
                            "location_type": activity.location_type,
                            "cost_estimate": activity.cost_estimate,
                            "group_size": activity.group_size,
                            "ai_reasoning": activity.ai_reasoning,
                            "confidence_score": activity.confidence_score,
                            "weather_condition": activity.weather_condition,
                            "temperature": activity.temperature,
                            "is_favorite": activity.is_favorite,
                            "user_rating": activity.user_rating,
                            "times_suggested": activity.times_suggested,
                            "times_completed": activity.times_completed,
                            "created_at": activity.created_at.isoformat() if activity.created_at else None
                        }
                        for activity in activities
                    ]
                }
                
                # Write to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                self.parent.logger.info(f"Exported {len(activities)} activities to {file_path}")
                
                # Show success message
                self.show_export_success(len(activities))
                
        except Exception as e:
            self.parent.logger.error(f"Error exporting activities: {e}")
            self.show_export_error(str(e))
    
    def show_export_success(self, activity_count: int):
        """Show export success dialog."""
        success_window = ctk.CTkToplevel(self.parent)
        success_window.title("Export Successful")
        success_window.geometry("300x150")
        success_window.transient(self.parent)
        
        success_label = GlassLabel(
            success_window,
            text=f"✅ Successfully exported\n{activity_count} activities!",
            font=("Segoe UI", 12)
        )
        success_label.pack(expand=True)
        
        ok_button = GlassButton(
            success_window,
            text="OK",
            command=success_window.destroy,
            width=80
        )
        ok_button.pack(pady=(0, 20))
    
    def show_export_error(self, error_message: str):
        """Show export error dialog."""
        error_window = ctk.CTkToplevel(self.parent)
        error_window.title("Export Error")
        error_window.geometry("300x150")
        error_window.transient(self.parent)
        
        error_label = GlassLabel(
            error_window,
            text=f"❌ Export failed:\n{error_message}",
            font=("Segoe UI", 12)
        )
        error_label.pack(expand=True)
        
        ok_button = GlassButton(
            error_window,
            text="OK",
            command=error_window.destroy,
            width=80
        )
        ok_button.pack(pady=(0, 20))