"""AI-powered activity generation service using Google Gemini.

This module handles all AI-related functionality for generating activity suggestions
based on weather conditions and user preferences.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .models import ActivitySuggestion, UserPreferences, ActivityCategory, DifficultyLevel, WeatherSuitability


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
        weather_data,
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
        weather_data,
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
        weather_data,
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

{prefs_context}

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

    def _parse_ai_response(self, response_text: str, weather_data) -> List[ActivitySuggestion]:
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
        weather_data,
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

        # Filter based on user preferences
        filtered_suggestions = self._filter_by_preferences(suggestions, user_preferences)
        
        # Return requested number of suggestions
        return filtered_suggestions[:count]

    def _filter_by_preferences(self, suggestions: List[ActivitySuggestion], preferences: UserPreferences) -> List[ActivitySuggestion]:
        """Filter suggestions based on user preferences."""
        filtered = []
        
        for suggestion in suggestions:
            # Skip if category is in avoid list
            if suggestion.category in preferences.avoid_categories:
                continue
                
            # Check duration preference
            if suggestion.duration_minutes > preferences.max_duration_minutes:
                continue
                
            # Check indoor/outdoor preference
            if preferences.indoor_outdoor_preference != "any":
                if preferences.indoor_outdoor_preference == "indoor" and suggestion.location_type != "indoor":
                    continue
                if preferences.indoor_outdoor_preference == "outdoor" and suggestion.location_type != "outdoor":
                    continue
                    
            # Check preferred categories (if any specified)
            if preferences.preferred_categories:
                if suggestion.category not in preferences.preferred_categories:
                    continue
                    
            # Check preferred difficulty (if any specified)
            if preferences.preferred_difficulty:
                if suggestion.difficulty not in preferences.preferred_difficulty:
                    continue
                    
            filtered.append(suggestion)
            
        return filtered