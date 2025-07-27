"""Activity Suggester Feature - AI-powered activity recommendations based on weather conditions.

This module implements the Activity Suggester feature (⭐⭐⭐ difficulty) which provides
intelligent activity recommendations using Google Gemini AI, weather data analysis,
and user preferences with a modern glassmorphic interface.

Features:
- AI-powered activity recommendations using Google Gemini
- Weather-aware suggestion algorithms
- User preference learning and personalization
- Activity categorization and filtering
- Spotify integration for mood-based music recommendations
- Interactive glassmorphic UI with smooth animations
- Activity history and favorites tracking
- Export and sharing capabilities

Author: Eric Hunter
Date: 2024
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict

import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, filedialog

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except ImportError:
    spotipy = None

# Import project modules
try:
    from ..core.database_manager import DatabaseManager
    from ..ui.components.base_components import GlassFrame, GlassButton, GlassLabel, GlassEntry
    from ..ui.theme_manager import ThemeManager
    from ..utils.logger import LoggerMixin
    from ..services.weather_service import WeatherData
except ImportError:
    # Fallback for testing
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))

    from core.database_manager import DatabaseManager
    from ui.components.base_components import GlassFrame, GlassButton, GlassLabel, GlassEntry
    from ui.theme_manager import ThemeManager
    from utils.logger import LoggerMixin
    from services.weather_service import WeatherData


class ActivityCategory(Enum):
    """Activity categories for organization and filtering."""
    OUTDOOR = "outdoor"
    INDOOR = "indoor"
    SPORTS = "sports"
    CREATIVE = "creative"
    SOCIAL = "social"
    RELAXATION = "relaxation"
    EXERCISE = "exercise"
    ENTERTAINMENT = "entertainment"
    EDUCATIONAL = "educational"
    CULINARY = "culinary"


class WeatherSuitability(Enum):
    """Weather suitability ratings for activities."""
    PERFECT = "perfect"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNSUITABLE = "unsuitable"


class DifficultyLevel(Enum):
    """Activity difficulty levels."""
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    EXPERT = "expert"


@dataclass
class ActivitySuggestion:
    """Data class for activity suggestions."""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    category: ActivityCategory = ActivityCategory.OUTDOOR
    difficulty: DifficultyLevel = DifficultyLevel.EASY
    duration_minutes: int = 60
    weather_suitability: WeatherSuitability = WeatherSuitability.GOOD
    required_items: List[str] = field(default_factory=list)
    location_type: str = "anywhere"  # indoor, outdoor, specific location
    cost_estimate: str = "free"  # free, low, medium, high
    group_size: str = "any"  # solo, small group, large group, any
    ai_reasoning: str = ""
    confidence_score: float = 0.0
    weather_condition: Optional[str] = None
    temperature: Optional[float] = None
    created_at: Optional[datetime] = None
    is_favorite: bool = False
    user_rating: Optional[int] = None
    times_suggested: int = 0
    times_completed: int = 0
    spotify_playlist_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert enums to strings
        data['category'] = self.category.value
        data['difficulty'] = self.difficulty.value
        data['weather_suitability'] = self.weather_suitability.value
        # Convert datetime to ISO string
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivitySuggestion':
        """Create from dictionary."""
        # Convert string enums back to enum objects
        if 'category' in data and isinstance(data['category'], str):
            data['category'] = ActivityCategory(data['category'])
        if 'difficulty' in data and isinstance(data['difficulty'], str):
            data['difficulty'] = DifficultyLevel(data['difficulty'])
        if 'weather_suitability' in data and isinstance(data['weather_suitability'], str):
            data['weather_suitability'] = WeatherSuitability(data['weather_suitability'])
        # Convert ISO string to datetime
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])

        return cls(**data)


@dataclass
class UserPreferences:
    """User preferences for activity suggestions."""
    preferred_categories: List[ActivityCategory] = field(default_factory=list)
    preferred_difficulty: List[DifficultyLevel] = field(default_factory=list)
    max_duration_minutes: int = 180
    budget_preference: str = "any"  # free, low, medium, high, any
    group_preference: str = "any"  # solo, small, large, any
    indoor_outdoor_preference: str = "any"  # indoor, outdoor, any
    avoid_categories: List[ActivityCategory] = field(default_factory=list)
    favorite_activities: List[str] = field(default_factory=list)
    completed_activities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['preferred_categories'] = [cat.value for cat in self.preferred_categories]
        data['preferred_difficulty'] = [diff.value for diff in self.preferred_difficulty]
        data['avoid_categories'] = [cat.value for cat in self.avoid_categories]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create from dictionary."""
        if 'preferred_categories' in data:
            data['preferred_categories'] = [ActivityCategory(cat) for cat in data['preferred_categories']]
        if 'preferred_difficulty' in data:
            data['preferred_difficulty'] = [DifficultyLevel(diff) for diff in data['preferred_difficulty']]
        if 'avoid_categories' in data:
            data['avoid_categories'] = [ActivityCategory(cat) for cat in data['avoid_categories']]

        return cls(**data)


class ActivityDatabase:
    """Database manager for activity suggestions and user data."""

    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager
        self.logger = logging.getLogger(__name__)
        self._initialize_tables()

    def _initialize_tables(self):
        """Initialize activity-related database tables."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Activity suggestions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activity_suggestions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        category TEXT NOT NULL,
                        difficulty TEXT NOT NULL,
                        duration_minutes INTEGER,
                        weather_suitability TEXT,
                        required_items TEXT,  -- JSON array
                        location_type TEXT,
                        cost_estimate TEXT,
                        group_size TEXT,
                        ai_reasoning TEXT,
                        confidence_score REAL,
                        weather_condition TEXT,
                        temperature REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_favorite BOOLEAN DEFAULT FALSE,
                        user_rating INTEGER,
                        times_suggested INTEGER DEFAULT 0,
                        times_completed INTEGER DEFAULT 0,
                        spotify_playlist_id TEXT
                    )
                """)

                # User preferences table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INTEGER PRIMARY KEY,
                        preferences_data TEXT  -- JSON data
                    )
                """)

                # Activity history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activity_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id INTEGER,
                        action_type TEXT,  -- suggested, favorited, completed, rated
                        action_data TEXT,  -- JSON data for additional info
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (activity_id) REFERENCES activity_suggestions (id)
                    )
                """)

                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_category ON activity_suggestions(category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_weather ON activity_suggestions(weather_condition)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_created ON activity_suggestions(created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_activity ON activity_history(activity_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON activity_history(timestamp)")

                conn.commit()
                self.logger.debug("Activity database tables initialized")

        except Exception as e:
            self.logger.error(f"Error initializing activity tables: {e}")
            raise

    def save_activity(self, activity: ActivitySuggestion) -> int:
        """Save activity suggestion to database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                if activity.id:
                    # Update existing activity
                    cursor.execute("""
                        UPDATE activity_suggestions SET
                            title = ?, description = ?, category = ?, difficulty = ?,
                            duration_minutes = ?, weather_suitability = ?, required_items = ?,
                            location_type = ?, cost_estimate = ?, group_size = ?,
                            ai_reasoning = ?, confidence_score = ?, weather_condition = ?,
                            temperature = ?, is_favorite = ?, user_rating = ?,
                            times_suggested = ?, times_completed = ?, spotify_playlist_id = ?
                        WHERE id = ?
                    """, (
                        activity.title, activity.description, activity.category.value,
                        activity.difficulty.value, activity.duration_minutes,
                        activity.weather_suitability.value, json.dumps(activity.required_items),
                        activity.location_type, activity.cost_estimate, activity.group_size,
                        activity.ai_reasoning, activity.confidence_score, activity.weather_condition,
                        activity.temperature, activity.is_favorite, activity.user_rating,
                        activity.times_suggested, activity.times_completed, activity.spotify_playlist_id,
                        activity.id
                    ))
                    activity_id = activity.id
                else:
                    # Insert new activity
                    cursor.execute("""
                        INSERT INTO activity_suggestions (
                            title, description, category, difficulty, duration_minutes,
                            weather_suitability, required_items, location_type, cost_estimate,
                            group_size, ai_reasoning, confidence_score, weather_condition,
                            temperature, is_favorite, user_rating, times_suggested,
                            times_completed, spotify_playlist_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        activity.title, activity.description, activity.category.value,
                        activity.difficulty.value, activity.duration_minutes,
                        activity.weather_suitability.value, json.dumps(activity.required_items),
                        activity.location_type, activity.cost_estimate, activity.group_size,
                        activity.ai_reasoning, activity.confidence_score, activity.weather_condition,
                        activity.temperature, activity.is_favorite, activity.user_rating,
                        activity.times_suggested, activity.times_completed, activity.spotify_playlist_id
                    ))
                    activity_id = cursor.lastrowid
                    activity.id = activity_id

                conn.commit()
                self.logger.debug(f"Activity saved with ID: {activity_id}")
                return activity_id

        except Exception as e:
            self.logger.error(f"Error saving activity: {e}")
            raise

    def load_activities(self, limit: int = 100, category: Optional[ActivityCategory] = None) -> List[ActivitySuggestion]:
        """Load activities from database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM activity_suggestions"
                params = []

                if category:
                    query += " WHERE category = ?"
                    params.append(category.value)

                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                activities = []
                for row in rows:
                    activity = ActivitySuggestion(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        category=ActivityCategory(row[3]),
                        difficulty=DifficultyLevel(row[4]),
                        duration_minutes=row[5],
                        weather_suitability=WeatherSuitability(row[6]) if row[6] else WeatherSuitability.GOOD,
                        required_items=json.loads(row[7]) if row[7] else [],
                        location_type=row[8],
                        cost_estimate=row[9],
                        group_size=row[10],
                        ai_reasoning=row[11],
                        confidence_score=row[12] or 0.0,
                        weather_condition=row[13],
                        temperature=row[14],
                        created_at=datetime.fromisoformat(row[15]) if row[15] else None,
                        is_favorite=bool(row[16]),
                        user_rating=row[17],
                        times_suggested=row[18] or 0,
                        times_completed=row[19] or 0,
                        spotify_playlist_id=row[20]
                    )
                    activities.append(activity)

                self.logger.debug(f"Loaded {len(activities)} activities")
                return activities

        except Exception as e:
            self.logger.error(f"Error loading activities: {e}")
            return []

    def save_user_preferences(self, preferences: UserPreferences):
        """Save user preferences to database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                preferences_json = json.dumps(preferences.to_dict())

                cursor.execute("""
                    INSERT OR REPLACE INTO user_preferences (id, preferences_data)
                    VALUES (1, ?)
                """, (preferences_json,))

                conn.commit()
                self.logger.debug("User preferences saved")

        except Exception as e:
            self.logger.error(f"Error saving user preferences: {e}")
            raise

    def load_user_preferences(self) -> UserPreferences:
        """Load user preferences from database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT preferences_data FROM user_preferences WHERE id = 1")
                row = cursor.fetchone()

                if row and row[0]:
                    preferences_data = json.loads(row[0])
                    return UserPreferences.from_dict(preferences_data)
                else:
                    # Return default preferences
                    return UserPreferences()

        except Exception as e:
            self.logger.error(f"Error loading user preferences: {e}")
            return UserPreferences()

    def log_activity_action(self, activity_id: int, action_type: str, action_data: Optional[Dict] = None):
        """Log user action for activity analytics."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO activity_history (activity_id, action_type, action_data)
                    VALUES (?, ?, ?)
                """, (activity_id, action_type, json.dumps(action_data) if action_data else None))

                conn.commit()
                self.logger.debug(f"Logged action '{action_type}' for activity {activity_id}")

        except Exception as e:
            self.logger.error(f"Error logging activity action: {e}")

    def get_activity_analytics(self) -> Dict[str, Any]:
        """Get activity analytics and statistics."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Category distribution
                cursor.execute("""
                    SELECT category, COUNT(*) as count
                    FROM activity_suggestions
                    GROUP BY category
                    ORDER BY count DESC
                """)
                category_stats = dict(cursor.fetchall())

                # Most popular activities
                cursor.execute("""
                    SELECT title, times_suggested, times_completed, user_rating
                    FROM activity_suggestions
                    WHERE times_suggested > 0
                    ORDER BY times_suggested DESC
                    LIMIT 10
                """)
                popular_activities = cursor.fetchall()

                # Recent activity trends
                cursor.execute("""
                    SELECT action_type, COUNT(*) as count
                    FROM activity_history
                    WHERE timestamp >= datetime('now', '-7 days')
                    GROUP BY action_type
                """)
                recent_trends = dict(cursor.fetchall())

                return {
                    'category_distribution': category_stats,
                    'popular_activities': popular_activities,
                    'recent_trends': recent_trends,
                    'total_activities': len(self.load_activities(limit=1000)),
                    'favorites_count': len([a for a in self.load_activities(limit=1000) if a.is_favorite])
                }

        except Exception as e:
            self.logger.error(f"Error getting activity analytics: {e}")
            return {}


class AIActivityGenerator:
    """AI-powered activity suggestion generator using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.model = None

        if api_key and genai:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.logger.info("Google Gemini AI initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing Gemini AI: {e}")
                self.model = None
        else:
            self.logger.warning("Gemini AI not available - using fallback suggestions")

    def generate_suggestions(
        self,
        weather_data: WeatherData,
        user_preferences: UserPreferences,
        count: int = 5
    ) -> List[ActivitySuggestion]:
        """Generate activity suggestions based on weather and preferences."""
        if self.model:
            return self._generate_ai_suggestions(weather_data, user_preferences, count)
        else:
            return self._generate_fallback_suggestions(weather_data, user_preferences, count)

    def _generate_ai_suggestions(
        self,
        weather_data: WeatherData,
        user_preferences: UserPreferences,
        count: int
    ) -> List[ActivitySuggestion]:
        """Generate suggestions using AI."""
        try:
            # Create detailed prompt for AI
            prompt = self._create_ai_prompt(weather_data, user_preferences, count)

            # Generate response
            response = self.model.generate_content(prompt)

            # Parse AI response
            suggestions = self._parse_ai_response(response.text, weather_data)

            self.logger.info(f"Generated {len(suggestions)} AI-powered suggestions")
            return suggestions

        except Exception as e:
            self.logger.error(f"Error generating AI suggestions: {e}")
            return self._generate_fallback_suggestions(weather_data, user_preferences, count)

    def _create_ai_prompt(
        self,
        weather_data: WeatherData,
        user_preferences: UserPreferences,
        count: int
    ) -> str:
        """Create detailed prompt for AI activity generation."""
        # Weather context
        weather_context = f"""
Current Weather Conditions:
- Condition: {weather_data.condition}
- Temperature: {weather_data.temperature}°F
- Humidity: {weather_data.humidity}%
- Wind Speed: {weather_data.wind_speed} mph
- Visibility: {weather_data.visibility} miles
"""

        # User preferences context
        prefs_context = f"""
User Preferences:
- Preferred Categories: {[cat.value for cat in user_preferences.preferred_categories]}
- Preferred Difficulty: {[diff.value for diff in user_preferences.preferred_difficulty]}
- Max Duration: {user_preferences.max_duration_minutes} minutes
- Budget Preference: {user_preferences.budget_preference}
- Group Preference: {user_preferences.group_preference}
- Indoor/Outdoor Preference: {user_preferences.indoor_outdoor_preference}
- Avoid Categories: {[cat.value for cat in user_preferences.avoid_categories]}
"""

        prompt = f"""
You are an expert activity recommendation system. Based on the current weather conditions and user preferences, suggest {count} specific, actionable activities.

{weather_context}

{user_preferences}

Please provide {count} activity suggestions in the following JSON format:

[
  {{
    "title": "Activity Name",
    "description": "Detailed description of the activity (2-3 sentences)",
    "category": "one of: outdoor, indoor, sports, creative, social, relaxation, exercise, entertainment, educational, culinary",
    "difficulty": "one of: easy, moderate, challenging, expert",
    "duration_minutes": 60,
    "weather_suitability": "one of: perfect, good, fair, poor, unsuitable",
    "required_items": ["item1", "item2"],
    "location_type": "indoor/outdoor/specific location",
    "cost_estimate": "free/low/medium/high",
    "group_size": "solo/small group/large group/any",
    "ai_reasoning": "Brief explanation of why this activity is recommended for the current conditions",
    "confidence_score": 0.85
  }}
]

Ensure activities are:
1. Weather-appropriate and safe
2. Aligned with user preferences
3. Specific and actionable
4. Diverse in category and type
5. Include both indoor and outdoor options when appropriate

Provide only the JSON array, no additional text.
"""

        return prompt

    def _parse_ai_response(self, response_text: str, weather_data: WeatherData) -> List[ActivitySuggestion]:
        """Parse AI response into ActivitySuggestion objects."""
        try:
            # Clean response text
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            # Parse JSON
            suggestions_data = json.loads(response_text)

            suggestions = []
            for data in suggestions_data:
                try:
                    suggestion = ActivitySuggestion(
                        title=data.get('title', 'Untitled Activity'),
                        description=data.get('description', ''),
                        category=ActivityCategory(data.get('category', 'outdoor')),
                        difficulty=DifficultyLevel(data.get('difficulty', 'easy')),
                        duration_minutes=data.get('duration_minutes', 60),
                        weather_suitability=WeatherSuitability(data.get('weather_suitability', 'good')),
                        required_items=data.get('required_items', []),
                        location_type=data.get('location_type', 'anywhere'),
                        cost_estimate=data.get('cost_estimate', 'free'),
                        group_size=data.get('group_size', 'any'),
                        ai_reasoning=data.get('ai_reasoning', ''),
                        confidence_score=data.get('confidence_score', 0.5),
                        weather_condition=weather_data.condition,
                        temperature=weather_data.temperature,
                        created_at=datetime.now()
                    )
                    suggestions.append(suggestion)
                except Exception as e:
                    self.logger.warning(f"Error parsing suggestion: {e}")
                    continue

            return suggestions

        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return []

    def _generate_fallback_suggestions(
        self,
        weather_data: WeatherData,
        user_preferences: UserPreferences,
        count: int
    ) -> List[ActivitySuggestion]:
        """Generate fallback suggestions when AI is not available."""
        suggestions = []

        # Weather-based activity templates
        if weather_data.temperature > 75 and 'sunny' in weather_data.condition.lower():
            suggestions.extend([
                ActivitySuggestion(
                    title="Outdoor Picnic",
                    description="Enjoy a relaxing picnic in a local park with friends or family. Perfect weather for outdoor dining!",
                    category=ActivityCategory.OUTDOOR,
                    difficulty=DifficultyLevel.EASY,
                    duration_minutes=120,
                    weather_suitability=WeatherSuitability.PERFECT,
                    required_items=["blanket", "food", "drinks", "sunscreen"],
                    location_type="outdoor",
                    cost_estimate="low",
                    group_size="any",
                    ai_reasoning="Sunny and warm weather is ideal for outdoor dining and socializing",
                    confidence_score=0.9,
                    weather_condition=weather_data.condition,
                    temperature=weather_data.temperature,
                    created_at=datetime.now()
                ),
                ActivitySuggestion(
                    title="Nature Photography Walk",
                    description="Explore local trails and capture the beauty of nature with your camera or smartphone.",
                    category=ActivityCategory.CREATIVE,
                    difficulty=DifficultyLevel.EASY,
                    duration_minutes=90,
                    weather_suitability=WeatherSuitability.PERFECT,
                    required_items=["camera or smartphone", "comfortable shoes", "water bottle"],
                    location_type="outdoor",
                    cost_estimate="free",
                    group_size="solo",
                    ai_reasoning="Great lighting and pleasant weather for outdoor photography",
                    confidence_score=0.85,
                    weather_condition=weather_data.condition,
                    temperature=weather_data.temperature,
                    created_at=datetime.now()
                )
            ])

        elif weather_data.temperature < 40 or 'rain' in weather_data.condition.lower():
            suggestions.extend([
                ActivitySuggestion(
                    title="Cozy Reading Session",
                    description="Curl up with a good book and a warm beverage. Perfect indoor activity for cold or rainy weather.",
                    category=ActivityCategory.RELAXATION,
                    difficulty=DifficultyLevel.EASY,
                    duration_minutes=120,
                    weather_suitability=WeatherSuitability.PERFECT,
                    required_items=["book", "warm beverage", "comfortable seating"],
                    location_type="indoor",
                    cost_estimate="free",
                    group_size="solo",
                    ai_reasoning="Indoor activities are ideal when weather is cold or wet",
                    confidence_score=0.9,
                    weather_condition=weather_data.condition,
                    temperature=weather_data.temperature,
                    created_at=datetime.now()
                ),
                ActivitySuggestion(
                    title="Home Cooking Project",
                    description="Try a new recipe or bake something special. Great way to spend time indoors productively.",
                    category=ActivityCategory.CULINARY,
                    difficulty=DifficultyLevel.MODERATE,
                    duration_minutes=90,
                    weather_suitability=WeatherSuitability.GOOD,
                    required_items=["ingredients", "cooking utensils", "recipe"],
                    location_type="indoor",
                    cost_estimate="low",
                    group_size="any",
                    ai_reasoning="Indoor cooking activities are perfect for staying warm and productive",
                    confidence_score=0.8,
                    weather_condition=weather_data.condition,
                    temperature=weather_data.temperature,
                    created_at=datetime.now()
                )
            ])

        # Add general suggestions
        suggestions.extend([
            ActivitySuggestion(
                title="Indoor Workout Session",
                description="Get your heart rate up with a home workout routine. No gym required!",
                category=ActivityCategory.EXERCISE,
                difficulty=DifficultyLevel.MODERATE,
                duration_minutes=45,
                weather_suitability=WeatherSuitability.GOOD,
                required_items=["exercise mat", "water bottle", "workout clothes"],
                location_type="indoor",
                cost_estimate="free",
                group_size="solo",
                ai_reasoning="Indoor exercise is always a good option regardless of weather",
                confidence_score=0.7,
                weather_condition=weather_data.condition,
                temperature=weather_data.temperature,
                created_at=datetime.now()
            ),
            ActivitySuggestion(
                title="Creative Art Project",
                description="Express your creativity with drawing, painting, or crafting. Let your imagination flow!",
                category=ActivityCategory.CREATIVE,
                difficulty=DifficultyLevel.EASY,
                duration_minutes=60,
                weather_suitability=WeatherSuitability.GOOD,
                required_items=["art supplies", "paper or canvas", "good lighting"],
                location_type="indoor",
                cost_estimate="low",
                group_size="solo",
                ai_reasoning="Creative activities are therapeutic and weather-independent",
                confidence_score=0.75,
                weather_condition=weather_data.condition,
                temperature=weather_data.temperature,
                created_at=datetime.now()
            )
        ])

        # Return requested number of suggestions
        return suggestions[:count]


class SpotifyIntegration:
    """Spotify integration for mood-based music recommendations."""

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.spotify = None
        self.logger = logging.getLogger(__name__)

        if client_id and client_secret and spotipy:
            try:
                credentials = SpotifyClientCredentials(
                    client_id=client_id,
                    client_secret=client_secret
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=credentials)
                self.logger.info("Spotify integration initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing Spotify: {e}")
                self.spotify = None
        else:
            self.logger.warning("Spotify integration not available")

    def get_activity_playlist(
        self,
        activity: ActivitySuggestion,
        weather_data: WeatherData
    ) -> Optional[Dict[str, Any]]:
        """Get Spotify playlist recommendations for an activity."""
        if not self.spotify:
            return None

        try:
            # Determine mood and genre based on activity and weather
            mood_keywords = self._get_mood_keywords(activity, weather_data)

            # Search for playlists
            results = self.spotify.search(
                q=f"{mood_keywords} {activity.category.value}",
                type='playlist',
                limit=5
            )

            if results['playlists']['items']:
                playlist = results['playlists']['items'][0]
                return {
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'description': playlist['description'],
                    'url': playlist['external_urls']['spotify'],
                    'image_url': playlist['images'][0]['url'] if playlist['images'] else None,
                    'tracks_total': playlist['tracks']['total']
                }

            return None

        except Exception as e:
            self.logger.error(f"Error getting Spotify playlist: {e}")
            return None

    def _get_mood_keywords(self, activity: ActivitySuggestion, weather_data: WeatherData) -> str:
        """Generate mood keywords for playlist search."""
        keywords = []

        # Activity-based keywords
        if activity.category == ActivityCategory.EXERCISE:
            keywords.extend(["workout", "energetic", "upbeat"])
        elif activity.category == ActivityCategory.RELAXATION:
            keywords.extend(["chill", "relaxing", "ambient"])
        elif activity.category == ActivityCategory.CREATIVE:
            keywords.extend(["focus", "instrumental", "creative"])
        elif activity.category == ActivityCategory.OUTDOOR:
            keywords.extend(["adventure", "nature", "uplifting"])

        # Weather-based keywords
        if 'sunny' in weather_data.condition.lower():
            keywords.extend(["sunny", "happy", "bright"])
        elif 'rain' in weather_data.condition.lower():
            keywords.extend(["rainy", "cozy", "mellow"])
        elif 'snow' in weather_data.condition.lower():
            keywords.extend(["winter", "peaceful", "calm"])

        return " ".join(keywords[:3])  # Use top 3 keywords


class ActivitySuggesterWidget(GlassFrame, LoggerMixin):
    """Main Activity Suggester widget with glassmorphic design."""

    def __init__(
        self,
        parent,
        database_manager: DatabaseManager,
        theme_manager: Optional[ThemeManager] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        # Core dependencies
        self.database_manager = database_manager
        self.theme_manager = theme_manager or ThemeManager()

        # Initialize services
        self.activity_db = ActivityDatabase(database_manager)
        self.ai_generator = AIActivityGenerator()  # Will be configured later
        self.spotify_integration = SpotifyIntegration()  # Will be configured later

        # State management
        self.current_weather: Optional[WeatherData] = None
        self.user_preferences = self.activity_db.load_user_preferences()
        self.current_suggestions: List[ActivitySuggestion] = []
        self.selected_activity: Optional[ActivitySuggestion] = None
        self.is_generating = False

        # UI components
        self.suggestion_cards: List[ctk.CTkFrame] = []
        self.generation_thread: Optional[threading.Thread] = None

        # Initialize UI
        self._setup_ui()
        self._load_recent_suggestions()

        self.logger.info("Activity Suggester widget initialized")

    def configure_api_keys(self, gemini_api_key: Optional[str] = None,
                          spotify_client_id: Optional[str] = None,
                          spotify_client_secret: Optional[str] = None):
        """Configure API keys for AI and Spotify integration."""
        if gemini_api_key:
            self.ai_generator = AIActivityGenerator(api_key=gemini_api_key)
            self.logger.info("Configured Gemini AI integration")

        if spotify_client_id and spotify_client_secret:
            self.spotify_integration = SpotifyIntegration(
                client_id=spotify_client_id,
                client_secret=spotify_client_secret
            )
            self.logger.info("Configured Spotify integration")

    def _setup_ui(self):
        """Setup the main UI layout."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header section
        self._create_header()

        # Main content area
        self._create_main_content()

        # Sidebar for preferences and controls
        self._create_sidebar()

        # Status bar
        self._create_status_bar()

        # Apply glassmorphic styling
        self._apply_glass_styling()

    def _create_header(self):
        """Create header with title and quick actions."""
        header_frame = GlassFrame(self)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = GlassLabel(
            header_frame,
            text="🎯 Activity Suggester",
            font=("Segoe UI", 24, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        # Quick action buttons
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=2, sticky="e", padx=20, pady=15)

        self.generate_button = GlassButton(
            actions_frame,
            text="🔄 Generate New",
            command=self._generate_suggestions,
            width=140
        )
        self.generate_button.pack(side="left", padx=(0, 10))

        self.preferences_button = GlassButton(
            actions_frame,
            text="⚙️ Preferences",
            command=self._show_preferences,
            width=140
        )
        self.preferences_button.pack(side="left", padx=(0, 10))

        self.analytics_button = GlassButton(
            actions_frame,
            text="📊 Analytics",
            command=self._show_analytics,
            width=120
        )
        self.analytics_button.pack(side="left")

    def _create_sidebar(self):
        """Create sidebar with filters and preferences."""
        sidebar_frame = GlassFrame(self, width=280)
        sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)
        sidebar_frame.grid_propagate(False)

        # Weather info section
        weather_section = GlassFrame(sidebar_frame)
        weather_section.pack(fill="x", padx=10, pady=(10, 5))

        weather_title = GlassLabel(
            weather_section,
            text="🌤️ Current Weather",
            font=("Segoe UI", 14, "bold")
        )
        weather_title.pack(pady=(10, 5))

        self.weather_info_label = GlassLabel(
            weather_section,
            text="Weather data not available",
            font=("Segoe UI", 11)
        )
        self.weather_info_label.pack(pady=(0, 10))

        # Quick filters section
        filters_section = GlassFrame(sidebar_frame)
        filters_section.pack(fill="x", padx=10, pady=5)

        filters_title = GlassLabel(
            filters_section,
            text="🔍 Quick Filters",
            font=("Segoe UI", 14, "bold")
        )
        filters_title.pack(pady=(10, 5))

        # Category filter
        self.category_var = ctk.StringVar(value="all")
        category_menu = ctk.CTkOptionMenu(
            filters_section,
            variable=self.category_var,
            values=["all"] + [cat.value for cat in ActivityCategory],
            command=self._on_filter_changed
        )
        category_menu.pack(fill="x", padx=10, pady=2)

        # Difficulty filter
        self.difficulty_var = ctk.StringVar(value="all")
        difficulty_menu = ctk.CTkOptionMenu(
            filters_section,
            variable=self.difficulty_var,
            values=["all"] + [diff.value for diff in DifficultyLevel],
            command=self._on_filter_changed
        )
        difficulty_menu.pack(fill="x", padx=10, pady=2)

        # Duration filter
        duration_label = GlassLabel(filters_section, text="Max Duration (minutes):")
        duration_label.pack(pady=(10, 2))

        self.duration_var = ctk.IntVar(value=180)
        duration_slider = ctk.CTkSlider(
            filters_section,
            from_=15,
            to=300,
            variable=self.duration_var,
            command=self._on_filter_changed
        )
        duration_slider.pack(fill="x", padx=10, pady=(0, 5))

        self.duration_value_label = GlassLabel(filters_section, text="180 min")
        self.duration_value_label.pack(pady=(0, 10))

        # Favorites section
        favorites_section = GlassFrame(sidebar_frame)
        favorites_section.pack(fill="x", padx=10, pady=5)

        favorites_title = GlassLabel(
            favorites_section,
            text="⭐ Quick Actions",
            font=("Segoe UI", 14, "bold")
        )
        favorites_title.pack(pady=(10, 5))

        self.show_favorites_var = ctk.BooleanVar()
        favorites_checkbox = ctk.CTkCheckBox(
            favorites_section,
            text="Show only favorites",
            variable=self.show_favorites_var,
            command=self._on_filter_changed
        )
        favorites_checkbox.pack(pady=2)

        export_button = GlassButton(
            favorites_section,
            text="📤 Export Activities",
            command=self._export_activities,
            width=200
        )
        export_button.pack(fill="x", padx=10, pady=(5, 10))

    def _create_main_content(self):
        """Create main content area for activity suggestions."""
        main_frame = GlassFrame(self)
        main_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Content header
        content_header = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        content_header.grid_columnconfigure(1, weight=1)

        suggestions_title = GlassLabel(
            content_header,
            text="💡 Activity Suggestions",
            font=("Segoe UI", 18, "bold")
        )
        suggestions_title.grid(row=0, column=0, sticky="w")

        self.suggestions_count_label = GlassLabel(
            content_header,
            text="0 suggestions",
            font=("Segoe UI", 12)
        )
        self.suggestions_count_label.grid(row=0, column=2, sticky="e")

        # Scrollable suggestions area
        self.suggestions_scroll = ctk.CTkScrollableFrame(
            main_frame,
            fg_color=("#F0F0F0", "#1A1A1A"),
            scrollbar_button_color=("#CCCCCC", "#444444")
        )
        self.suggestions_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=(5, 15))
        self.suggestions_scroll.grid_columnconfigure(0, weight=1)

        # Loading indicator
        self.loading_frame = ctk.CTkFrame(self.suggestions_scroll, fg_color="transparent")
        self.loading_label = GlassLabel(
            self.loading_frame,
            text="🔄 Generating personalized suggestions...",
            font=("Segoe UI", 14)
        )
        self.loading_label.pack(pady=50)

        # Empty state
        self.empty_frame = ctk.CTkFrame(self.suggestions_scroll, fg_color="transparent")
        empty_label = GlassLabel(
            self.empty_frame,
            text="🎯 Click 'Generate New' to get personalized activity suggestions!",
            font=("Segoe UI", 14)
        )
        empty_label.pack(pady=50)
        self.empty_frame.pack(fill="both", expand=True)

    def _create_status_bar(self):
        """Create status bar with generation info."""
        status_frame = GlassFrame(self, height=40)
        status_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=(5, 10))
        status_frame.grid_propagate(False)
        status_frame.grid_columnconfigure(1, weight=1)

        self.status_label = GlassLabel(
            status_frame,
            text="Ready to generate activity suggestions",
            font=("Segoe UI", 10)
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)

        self.ai_status_label = GlassLabel(
            status_frame,
            text="AI: Ready" if self.ai_generator.model else "AI: Fallback Mode",
            font=("Segoe UI", 10)
        )
        self.ai_status_label.grid(row=0, column=2, sticky="e", padx=15, pady=10)

    def _apply_glass_styling(self):
        """Apply glassmorphic styling to components."""
        if self.theme_manager:
            # Apply weather-responsive theme
            if self.current_weather:
                self.theme_manager.apply_weather_theme(self.current_weather.condition)

    def _load_recent_suggestions(self):
        """Load recent suggestions from database."""
        try:
            recent_activities = self.activity_db.load_activities(limit=10)
            if recent_activities:
                self.current_suggestions = recent_activities
                self._update_suggestions_display()

        except Exception as e:
            self.logger.error(f"Error loading recent suggestions: {e}")

    def _generate_suggestions(self):
        """Generate new activity suggestions."""
        if self.is_generating:
            return

        self.is_generating = True
        self._update_status("Generating suggestions...")
        self._show_loading()

        # Disable generate button
        self.generate_button.configure(state="disabled", text="🔄 Generating...")

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
            suggestions = self.ai_generator.generate_suggestions(
                weather_data=self.current_weather or self._get_default_weather(),
                user_preferences=self.user_preferences,
                count=6
            )

            # Save suggestions to database
            for suggestion in suggestions:
                suggestion.times_suggested += 1
                self.activity_db.save_activity(suggestion)
                self.activity_db.log_activity_action(suggestion.id, "suggested")

            # Update UI on main thread
            self.after(0, lambda: self._on_suggestions_generated(suggestions))

        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            self.after(0, lambda: self._on_generation_error(str(e)))

    def _on_suggestions_generated(self, suggestions: List[ActivitySuggestion]):
        """Handle successful suggestion generation."""
        self.current_suggestions = suggestions
        self.is_generating = False

        # Update UI
        self._hide_loading()
        self._update_suggestions_display()
        self._update_status(f"Generated {len(suggestions)} new suggestions")

        # Re-enable generate button
        self.generate_button.configure(state="normal", text="🔄 Generate New")

        self.logger.info(f"Successfully generated {len(suggestions)} suggestions")

    def _on_generation_error(self, error_message: str):
        """Handle suggestion generation error."""
        self.is_generating = False

        # Update UI
        self._hide_loading()
        self._update_status(f"Error: {error_message}")

        # Re-enable generate button
        self.generate_button.configure(state="normal", text="🔄 Generate New")

        # Show error message
        messagebox.showerror("Generation Error", f"Failed to generate suggestions:\n{error_message}")

    def _update_suggestions_display(self):
        """Update the suggestions display with current suggestions."""
        # Clear existing cards
        for card in self.suggestion_cards:
            card.destroy()
        self.suggestion_cards.clear()

        # Hide empty state
        self.empty_frame.pack_forget()

        # Filter suggestions based on current filters
        filtered_suggestions = self._filter_suggestions(self.current_suggestions)

        # Update count
        self.suggestions_count_label.configure(text=f"{len(filtered_suggestions)} suggestions")

        # Create suggestion cards
        for i, suggestion in enumerate(filtered_suggestions):
            card = self._create_suggestion_card(suggestion, i)
            card.pack(fill="x", padx=10, pady=5)
            self.suggestion_cards.append(card)

        # Show empty state if no suggestions
        if not filtered_suggestions:
            self.empty_frame.pack(fill="both", expand=True)

    def _create_suggestion_card(self, suggestion: ActivitySuggestion, index: int) -> ctk.CTkFrame:
        """Create a glassmorphic suggestion card."""
        # Main card frame
        card = GlassFrame(self.suggestions_scroll)
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
            command=lambda s=suggestion: self._toggle_favorite(s)
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
            command=lambda s=suggestion: self._show_activity_details(s)
        )
        details_button.pack(side="left", padx=(0, 10))

        complete_button = GlassButton(
            actions_frame,
            text="✅ Mark Complete",
            width=120,
            height=28,
            command=lambda s=suggestion: self._mark_activity_complete(s)
        )
        complete_button.pack(side="left", padx=(0, 10))

        if self.spotify_integration.spotify:
            music_button = GlassButton(
                actions_frame,
                text="🎵 Music",
                width=80,
                height=28,
                command=lambda s=suggestion: self._get_activity_music(s)
            )
            music_button.pack(side="left")

        return card

    def _filter_suggestions(self, suggestions: List[ActivitySuggestion]) -> List[ActivitySuggestion]:
        """Filter suggestions based on current filter settings."""
        filtered = suggestions

        # Category filter
        if self.category_var.get() != "all":
            category = ActivityCategory(self.category_var.get())
            filtered = [s for s in filtered if s.category == category]

        # Difficulty filter
        if self.difficulty_var.get() != "all":
            difficulty = DifficultyLevel(self.difficulty_var.get())
            filtered = [s for s in filtered if s.difficulty == difficulty]

        # Duration filter
        max_duration = self.duration_var.get()
        filtered = [s for s in filtered if s.duration_minutes <= max_duration]

        # Favorites filter
        if self.show_favorites_var.get():
            filtered = [s for s in filtered if s.is_favorite]

        return filtered

    def _show_loading(self):
        """Show loading indicator."""
        self.empty_frame.pack_forget()
        for card in self.suggestion_cards:
            card.pack_forget()
        self.loading_frame.pack(fill="both", expand=True)

    def _hide_loading(self):
        """Hide loading indicator."""
        self.loading_frame.pack_forget()

    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_label.configure(text=message)

    def _on_filter_changed(self, *args):
        """Handle filter changes."""
        # Update duration label
        self.duration_value_label.configure(text=f"{self.duration_var.get()} min")

        # Update suggestions display
        self._update_suggestions_display()

    def _toggle_favorite(self, suggestion: ActivitySuggestion):
        """Toggle favorite status of an activity."""
        suggestion.is_favorite = not suggestion.is_favorite
        self.activity_db.save_activity(suggestion)
        self.activity_db.log_activity_action(
            suggestion.id,
            "favorited" if suggestion.is_favorite else "unfavorited"
        )

        # Update display
        self._update_suggestions_display()

        self.logger.info(f"Toggled favorite for activity: {suggestion.title}")

    def _mark_activity_complete(self, suggestion: ActivitySuggestion):
        """Mark an activity as completed."""
        suggestion.times_completed += 1
        self.activity_db.save_activity(suggestion)
        self.activity_db.log_activity_action(suggestion.id, "completed")

        # Show completion message
        messagebox.showinfo(
            "Activity Completed",
            f"Great job completing '{suggestion.title}'!\n\nWould you like to rate this activity?"
        )

        # Show rating dialog
        self._show_rating_dialog(suggestion)

        self.logger.info(f"Marked activity complete: {suggestion.title}")

    def _show_activity_details(self, suggestion: ActivitySuggestion):
        """Show detailed activity information."""
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"Activity Details - {suggestion.title}")
        details_window.geometry("500x600")
        details_window.transient(self)

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
            command=lambda: [self._mark_activity_complete(suggestion), details_window.destroy()],
            width=120
        )
        complete_button.pack(side="right")

    def _show_rating_dialog(self, suggestion: ActivitySuggestion):
        """Show rating dialog for completed activity."""
        rating_window = ctk.CTkToplevel(self)
        rating_window.title("Rate Activity")
        rating_window.geometry("400x300")
        rating_window.transient(self)

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
            self.activity_db.save_activity_rating(suggestion.id, rating, feedback)

            # Update suggestion rating
            suggestion.user_rating = rating
            self.activity_db.save_activity(suggestion)

            rating_window.destroy()
            self.logger.info(f"Saved rating {rating}/5 for activity: {suggestion.title}")

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

    def _get_activity_music(self, suggestion: ActivitySuggestion):
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
            playlist = self.spotify_integration.get_mood_playlist(mood)

            if playlist:
                # Show music window
                self._show_music_window(suggestion, playlist)
            else:
                messagebox.showinfo(
                    "Music Unavailable",
                    "Unable to get music recommendations at this time."
                )

        except Exception as e:
            self.logger.error(f"Error getting activity music: {e}")
            messagebox.showerror("Error", "Failed to get music recommendations.")

    def _show_music_window(self, suggestion: ActivitySuggestion, playlist: dict):
        """Show music recommendations window."""
        music_window = ctk.CTkToplevel(self)
        music_window.title(f"Music for {suggestion.title}")
        music_window.geometry("500x400")
        music_window.transient(self)

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

    # Public API methods
    def set_weather_data(self, weather_data: dict):
        """Set current weather data for activity suggestions."""
        self.current_weather = weather_data
        self.logger.info("Updated weather data for activity suggestions")

    def set_user_preferences(self, preferences: UserPreferences):
        """Set user preferences for activity suggestions."""
        self.user_preferences = preferences
        self.activity_db.save_user_preferences(preferences)
        self.logger.info("Updated user preferences")

    def get_user_preferences(self) -> UserPreferences:
        """Get current user preferences."""
        return self.user_preferences

    def refresh_suggestions(self):
        """Refresh activity suggestions."""
        self._generate_suggestions()

    def get_activity_stats(self) -> dict:
        """Get activity statistics."""
        return self.activity_db.get_activity_stats()

    def _show_preferences(self):
        """Show user preferences dialog."""
        preferences_window = ctk.CTkToplevel(self)
        preferences_window.title("Activity Preferences")
        preferences_window.geometry("600x500")
        preferences_window.transient(self)

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

        self.pref_categories = {}
        for category in ActivityCategory:
            var = ctk.BooleanVar(value=category in self.user_preferences.preferred_categories)
            checkbox = ctk.CTkCheckBox(prefs_frame, text=category.value.title(), variable=var)
            checkbox.pack(anchor="w", padx=20, pady=2)
            self.pref_categories[category] = var

        # Difficulty preferences
        diff_label = GlassLabel(prefs_frame, text="Preferred Difficulty:", font=("Segoe UI", 12, "bold"))
        diff_label.pack(anchor="w", padx=10, pady=(15, 5))

        self.pref_difficulties = {}
        for difficulty in DifficultyLevel:
            var = ctk.BooleanVar(value=difficulty in self.user_preferences.preferred_difficulty)
            checkbox = ctk.CTkCheckBox(prefs_frame, text=difficulty.value.title(), variable=var)
            checkbox.pack(anchor="w", padx=20, pady=2)
            self.pref_difficulties[difficulty] = var

        # Max duration
        duration_label = GlassLabel(prefs_frame, text="Max Duration (minutes):", font=("Segoe UI", 12, "bold"))
        duration_label.pack(anchor="w", padx=10, pady=(15, 5))

        self.pref_duration = ctk.IntVar(value=self.user_preferences.max_duration_minutes)
        duration_slider = ctk.CTkSlider(prefs_frame, from_=15, to=300, variable=self.pref_duration)
        duration_slider.pack(fill="x", padx=20, pady=5)

        duration_value = GlassLabel(prefs_frame, text=f"{self.user_preferences.max_duration_minutes} min")
        duration_value.pack(anchor="w", padx=20)

        # Buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        save_button = GlassButton(
            button_frame,
            text="💾 Save Preferences",
            command=lambda: self._save_preferences(preferences_window),
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

    def _save_preferences(self, window):
        """Save user preferences from dialog."""
        # Update preferences
        self.user_preferences.preferred_categories = [
            cat for cat, var in self.pref_categories.items() if var.get()
        ]
        self.user_preferences.preferred_difficulty = [
            diff for diff, var in self.pref_difficulties.items() if var.get()
        ]
        self.user_preferences.max_duration_minutes = self.pref_duration.get()

        # Save to database
        self.activity_db.save_user_preferences(self.user_preferences)

        # Close window
        window.destroy()

        # Refresh suggestions
        self._generate_suggestions()

        self.logger.info("User preferences saved")

    def _show_analytics(self):
        """Show activity analytics dialog."""
        analytics_window = ctk.CTkToplevel(self)
        analytics_window.title("Activity Analytics")
        analytics_window.geometry("700x600")
        analytics_window.transient(self)

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

        # Get analytics data
        stats = self.activity_db.get_activity_stats()

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
    
    def _export_activities(self):
        """Export activities to a file."""
        try:
            from tkinter import filedialog
            import json
            from datetime import datetime
            
            # Ask user for file location
            file_path = filedialog.asksaveasfilename(
                title="Export Activities",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                # Get all activities
                activities = self.activity_db.load_activities(limit=1000)
                
                # Convert to exportable format
                export_data = {
                    "export_date": datetime.now().isoformat(),
                    "total_activities": len(activities),
                    "user_preferences": self.user_preferences.to_dict(),
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
                
                self.logger.info(f"Exported {len(activities)} activities to {file_path}")
                
                # Show success message
                success_window = ctk.CTkToplevel(self)
                success_window.title("Export Successful")
                success_window.geometry("300x150")
                success_window.transient(self)
                
                success_label = GlassLabel(
                    success_window,
                    text=f"✅ Successfully exported\n{len(activities)} activities!",
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
                
        except Exception as e:
            self.logger.error(f"Error exporting activities: {e}")
            
            # Show error message
            error_window = ctk.CTkToplevel(self)
            error_window.title("Export Error")
            error_window.geometry("300x150")
            error_window.transient(self)
            
            error_label = GlassLabel(
                error_window,
                text=f"❌ Export failed:\n{str(e)}",
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
    
    def export_activity_data(self, file_path: str):
        """Export activity data to JSON file."""
        try:
            data = {
                'activities': [asdict(activity) for activity in self.activity_db.get_all_activities()],
                'preferences': asdict(self.user_preferences),
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


def create_activity_suggester(parent, **kwargs) -> ActivitySuggesterWidget:
    """Factory function to create ActivitySuggesterWidget."""
    return ActivitySuggesterWidget(parent, **kwargs)


if __name__ == "__main__":
    # Test the widget
    import tempfile

    app = ctk.CTk()
    app.title("Activity Suggester Test")
    app.geometry("1000x700")

    # Create test database
    db_path = os.path.join(tempfile.gettempdir(), "test_activities.db")

    # Create widget
    widget = create_activity_suggester(app, db_path=db_path)
    widget.pack(fill="both", expand=True, padx=20, pady=20)

    # Set test weather data
    test_weather = {
        'condition': 'sunny',
        'temperature': 22,
        'humidity': 60,
        'wind_speed': 5
    }
    widget.set_weather_data(test_weather)

    app.mainloop()
