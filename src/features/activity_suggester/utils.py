"""
Activity Suggester Utilities

This module contains utility functions and helper classes for the Activity Suggester.
Includes formatting, validation, data processing, and other reusable functionality.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import os
from dataclasses import asdict

from .models import (
    ActivitySuggestion, ActivityCategory, DifficultyLevel, 
    WeatherSuitability, UserPreferences
)


class ActivityUtils:
    """Utility class for activity-related operations."""
    
    @staticmethod
    def get_category_colors() -> Dict[ActivityCategory, str]:
        """Get color mapping for activity categories."""
        return {
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
    
    @staticmethod
    def get_category_icons() -> Dict[ActivityCategory, str]:
        """Get icon mapping for activity categories."""
        return {
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
    
    @staticmethod
    def get_suitability_colors() -> Dict[WeatherSuitability, str]:
        """Get color mapping for weather suitability."""
        return {
            WeatherSuitability.PERFECT: "#4CAF50",
            WeatherSuitability.GOOD: "#8BC34A",
            WeatherSuitability.FAIR: "#FFC107",
            WeatherSuitability.POOR: "#FF9800",
            WeatherSuitability.UNSUITABLE: "#F44336"
        }
    
    @staticmethod
    def get_mood_mapping() -> Dict[ActivityCategory, str]:
        """Get mood mapping for music recommendations."""
        return {
            ActivityCategory.OUTDOOR: "energetic",
            ActivityCategory.INDOOR: "relaxed",
            ActivityCategory.EXERCISE: "workout",
            ActivityCategory.CREATIVE: "focus",
            ActivityCategory.SOCIAL: "party",
            ActivityCategory.RELAXATION: "chill"
        }
    
    @staticmethod
    def format_duration(minutes: int) -> str:
        """Format duration in minutes to human-readable string."""
        if minutes < 60:
            return f"{minutes} min"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours}h"
            else:
                return f"{hours}h {remaining_minutes}min"
    
    @staticmethod
    def format_activity_summary(activity: ActivitySuggestion) -> str:
        """Format activity summary for display."""
        return (f"{activity.title} | "
                f"{activity.category.value.title()} | "
                f"{ActivityUtils.format_duration(activity.duration_minutes)} | "
                f"{activity.difficulty.value.title()}")
    
    @staticmethod
    def validate_activity_data(activity_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate activity data dictionary."""
        required_fields = ['title', 'description', 'category', 'difficulty', 'duration_minutes']
        
        for field in required_fields:
            if field not in activity_data:
                return False, f"Missing required field: {field}"
        
        # Validate specific fields
        if not isinstance(activity_data['duration_minutes'], int) or activity_data['duration_minutes'] <= 0:
            return False, "Duration must be a positive integer"
        
        try:
            ActivityCategory(activity_data['category'])
        except ValueError:
            return False, f"Invalid category: {activity_data['category']}"
        
        try:
            DifficultyLevel(activity_data['difficulty'])
        except ValueError:
            return False, f"Invalid difficulty: {activity_data['difficulty']}"
        
        return True, "Valid"
    
    @staticmethod
    def calculate_activity_score(activity: ActivitySuggestion, preferences: UserPreferences) -> float:
        """Calculate activity relevance score based on user preferences."""
        score = 0.0
        
        # Category preference
        if activity.category in preferences.preferred_categories:
            score += 30
        
        # Difficulty preference
        if activity.difficulty in preferences.preferred_difficulty:
            score += 20
        
        # Duration preference
        if activity.duration_minutes <= preferences.max_duration_minutes:
            score += 25
        else:
            # Penalty for exceeding preferred duration
            excess = activity.duration_minutes - preferences.max_duration_minutes
            score -= min(excess * 0.5, 20)
        
        # Weather suitability
        suitability_scores = {
            WeatherSuitability.PERFECT: 25,
            WeatherSuitability.GOOD: 20,
            WeatherSuitability.FAIR: 10,
            WeatherSuitability.POOR: 5,
            WeatherSuitability.UNSUITABLE: 0
        }
        score += suitability_scores.get(activity.weather_suitability, 0)
        
        # Bonus for favorites
        if activity.is_favorite:
            score += 15
        
        # User rating bonus
        if activity.user_rating:
            score += activity.user_rating * 2
        
        return max(0, min(100, score))
    
    @staticmethod
    def filter_activities_by_weather(activities: List[ActivitySuggestion], 
                                   weather_condition: str) -> List[ActivitySuggestion]:
        """Filter activities based on weather condition."""
        weather_condition = weather_condition.lower()
        
        # Define weather-based filtering
        if 'rain' in weather_condition or 'storm' in weather_condition:
            # Prefer indoor activities during rain
            return [a for a in activities if a.category == ActivityCategory.INDOOR or 
                   a.weather_suitability in [WeatherSuitability.PERFECT, WeatherSuitability.GOOD]]
        
        elif 'snow' in weather_condition:
            # Winter activities or indoor activities
            return [a for a in activities if 'winter' in a.description.lower() or 
                   a.category == ActivityCategory.INDOOR]
        
        elif 'sun' in weather_condition or 'clear' in weather_condition:
            # Prefer outdoor activities on sunny days
            return [a for a in activities if a.category == ActivityCategory.OUTDOOR or 
                   a.weather_suitability == WeatherSuitability.PERFECT]
        
        else:
            # Return all activities for neutral weather
            return activities
    
    @staticmethod
    def get_activity_recommendations(activities: List[ActivitySuggestion], 
                                   preferences: UserPreferences,
                                   count: int = 5) -> List[ActivitySuggestion]:
        """Get top activity recommendations based on preferences."""
        # Calculate scores for all activities
        scored_activities = []
        for activity in activities:
            score = ActivityUtils.calculate_activity_score(activity, preferences)
            scored_activities.append((activity, score))
        
        # Sort by score (descending) and return top activities
        scored_activities.sort(key=lambda x: x[1], reverse=True)
        return [activity for activity, score in scored_activities[:count]]


class DataExporter:
    """Utility class for exporting activity data."""
    
    @staticmethod
    def export_to_json(activities: List[ActivitySuggestion], 
                      preferences: UserPreferences,
                      file_path: str) -> bool:
        """Export activities and preferences to JSON file."""
        try:
            export_data = {
                "export_date": datetime.now().isoformat(),
                "total_activities": len(activities),
                "user_preferences": preferences.to_dict(),
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
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def export_to_csv(activities: List[ActivitySuggestion], file_path: str) -> bool:
        """Export activities to CSV file."""
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'title', 'description', 'category', 'difficulty', 'duration_minutes',
                    'weather_suitability', 'location_type', 'cost_estimate', 'group_size',
                    'is_favorite', 'user_rating', 'times_suggested', 'times_completed'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for activity in activities:
                    writer.writerow({
                        'title': activity.title,
                        'description': activity.description,
                        'category': activity.category.value,
                        'difficulty': activity.difficulty.value,
                        'duration_minutes': activity.duration_minutes,
                        'weather_suitability': activity.weather_suitability.value,
                        'location_type': activity.location_type,
                        'cost_estimate': activity.cost_estimate,
                        'group_size': activity.group_size,
                        'is_favorite': activity.is_favorite,
                        'user_rating': activity.user_rating,
                        'times_suggested': activity.times_suggested,
                        'times_completed': activity.times_completed
                    })
            
            return True
            
        except Exception:
            return False


class ActivityValidator:
    """Utility class for validating activity data."""
    
    @staticmethod
    def validate_title(title: str) -> Tuple[bool, str]:
        """Validate activity title."""
        if not title or not title.strip():
            return False, "Title cannot be empty"
        
        if len(title.strip()) < 3:
            return False, "Title must be at least 3 characters long"
        
        if len(title.strip()) > 100:
            return False, "Title must be less than 100 characters"
        
        return True, "Valid"
    
    @staticmethod
    def validate_description(description: str) -> Tuple[bool, str]:
        """Validate activity description."""
        if not description or not description.strip():
            return False, "Description cannot be empty"
        
        if len(description.strip()) < 10:
            return False, "Description must be at least 10 characters long"
        
        if len(description.strip()) > 500:
            return False, "Description must be less than 500 characters"
        
        return True, "Valid"
    
    @staticmethod
    def validate_duration(duration: int) -> Tuple[bool, str]:
        """Validate activity duration."""
        if not isinstance(duration, int):
            return False, "Duration must be an integer"
        
        if duration <= 0:
            return False, "Duration must be positive"
        
        if duration > 480:  # 8 hours
            return False, "Duration cannot exceed 8 hours (480 minutes)"
        
        return True, "Valid"
    
    @staticmethod
    def validate_required_items(items: List[str]) -> Tuple[bool, str]:
        """Validate required items list."""
        if not isinstance(items, list):
            return False, "Required items must be a list"
        
        if len(items) > 20:
            return False, "Cannot have more than 20 required items"
        
        for item in items:
            if not isinstance(item, str) or not item.strip():
                return False, "All required items must be non-empty strings"
            
            if len(item.strip()) > 50:
                return False, "Each required item must be less than 50 characters"
        
        return True, "Valid"


class WeatherUtils:
    """Utility class for weather-related operations."""
    
    @staticmethod
    def get_weather_mood(weather_condition: str) -> str:
        """Get mood based on weather condition."""
        weather_condition = weather_condition.lower()
        
        if 'rain' in weather_condition or 'storm' in weather_condition:
            return "rainy"
        elif 'snow' in weather_condition:
            return "winter"
        elif 'sun' in weather_condition or 'clear' in weather_condition:
            return "sunny"
        elif 'cloud' in weather_condition:
            return "cloudy"
        else:
            return "neutral"
    
    @staticmethod
    def determine_suitability(activity_category: ActivityCategory, 
                            weather_condition: str,
                            temperature: float) -> WeatherSuitability:
        """Determine weather suitability for an activity."""
        weather_condition = weather_condition.lower()
        
        # Indoor activities are always suitable
        if activity_category == ActivityCategory.INDOOR:
            return WeatherSuitability.PERFECT
        
        # Outdoor activities depend on weather
        if activity_category == ActivityCategory.OUTDOOR:
            if 'storm' in weather_condition or 'heavy rain' in weather_condition:
                return WeatherSuitability.UNSUITABLE
            elif 'rain' in weather_condition:
                return WeatherSuitability.POOR
            elif 'snow' in weather_condition:
                return WeatherSuitability.FAIR if temperature > -5 else WeatherSuitability.POOR
            elif 'sun' in weather_condition or 'clear' in weather_condition:
                if 10 <= temperature <= 30:
                    return WeatherSuitability.PERFECT
                else:
                    return WeatherSuitability.GOOD
            else:
                return WeatherSuitability.FAIR
        
        # Sports activities
        if activity_category == ActivityCategory.SPORTS:
            if 'storm' in weather_condition:
                return WeatherSuitability.UNSUITABLE
            elif 'rain' in weather_condition:
                return WeatherSuitability.POOR
            elif 'sun' in weather_condition and 15 <= temperature <= 25:
                return WeatherSuitability.PERFECT
            else:
                return WeatherSuitability.GOOD
        
        # Default for other categories
        return WeatherSuitability.GOOD