import json
import logging
import os
from typing import Any, Dict, List

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from src.models.weather_models import WeatherData
from src.services.config_service import ConfigService


class ActivityService:
    """Service for AI-powered activity suggestions."""

    def __init__(self, config_service: ConfigService):
        self.config = config_service
        self.logger = logging.getLogger(__name__)

        # Initialize Gemini if API key available
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and genai:
            try:
                genai.configure(api_key=gemini_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                self.logger.info("Gemini AI initialized")
            except Exception as e:
                self.model = None
                self.logger.warning(f"Failed to initialize Gemini: {e}")
        else:
            self.model = None
            if not gemini_key:
                self.logger.warning("Gemini API key not found")
            if not genai:
                self.logger.warning("Gemini library not available")

    def get_activity_suggestions(self, weather_data: WeatherData) -> List[Dict[str, Any]]:
        """Get AI-powered activity suggestions based on weather."""
        if not self.model:
            return self._get_fallback_suggestions(weather_data)

        try:
            # Create prompt
            prompt = f"""
Based on the current weather conditions:
- Temperature: {weather_data.temperature}°C
- Condition: {weather_data.description}
- Humidity: {weather_data.humidity}%
- Wind Speed: {weather_data.wind_speed} m/s

Suggest 5 activities suitable for these conditions.
For each activity provide:
1. Title
2. Category (Indoor/Outdoor)
3. Description
4. Duration
5. Required items
6. Icon (emoji)

Format as JSON array with this structure:
[
  {{
    "title": "Activity Name",
    "category": "Indoor" or "Outdoor",
    "icon": "🏖️",
    "description": "Brief description",
    "time": "Duration estimate",
    "items": "Required items"
  }}
]
"""

            # Get AI response
            response = self.model.generate_content(prompt)

            # Parse and return suggestions
            try:
                # Extract JSON from response
                response_text = response.text
                # Find JSON array in response
                start_idx = response_text.find("[")
                end_idx = response_text.rfind("]") + 1

                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    suggestions = json.loads(json_str)

                    # Validate and clean suggestions
                    validated_suggestions = []
                    for suggestion in suggestions[:5]:  # Limit to 5
                        if all(
                            key in suggestion
                            for key in ["title", "category", "description", "time", "items"]
                        ):
                            # Add default icon if missing
                            if "icon" not in suggestion:
                                suggestion["icon"] = (
                                    "🎯" if suggestion["category"] == "Outdoor" else "🏠"
                                )
                            validated_suggestions.append(suggestion)

                    if validated_suggestions:
                        self.logger.info(
                            f"Generated {
                                len(validated_suggestions)} AI activity suggestions"
                        )
                        return validated_suggestions

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"Failed to parse AI response: {e}")

            # Fallback if parsing fails
            return self._get_fallback_suggestions(weather_data)

        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            return self._get_fallback_suggestions(weather_data)

    def _get_fallback_suggestions(self, weather_data: WeatherData) -> List[Dict[str, Any]]:
        """Fallback suggestions when AI is not available."""
        temp = weather_data.temperature
        condition = weather_data.description.lower()

        # Weather-based activity suggestions
        if "rain" in condition or "storm" in condition:
            return [
                {
                    "title": "Indoor Reading",
                    "category": "Indoor",
                    "icon": "📚",
                    "description": "Perfect rainy day for a good book",
                    "time": "1-3 hours",
                    "items": "Book, comfortable chair, hot drink",
                },
                {
                    "title": "Movie Marathon",
                    "category": "Indoor",
                    "icon": "🎬",
                    "description": "Cozy indoor entertainment",
                    "time": "2-4 hours",
                    "items": "Streaming service, snacks, blanket",
                },
                {
                    "title": "Cooking Project",
                    "category": "Indoor",
                    "icon": "👨‍🍳",
                    "description": "Try a new recipe",
                    "time": "1-2 hours",
                    "items": "Ingredients, cooking utensils",
                },
                {
                    "title": "Board Games",
                    "category": "Indoor",
                    "icon": "🎲",
                    "description": "Fun indoor games with family",
                    "time": "1-3 hours",
                    "items": "Board games, friends/family",
                },
                {
                    "title": "Art & Crafts",
                    "category": "Indoor",
                    "icon": "🎨",
                    "description": "Creative indoor activity",
                    "time": "2-4 hours",
                    "items": "Art supplies, workspace",
                },
            ]
        elif temp > 25:  # Warm weather
            return [
                {
                    "title": "Beach Day",
                    "category": "Outdoor",
                    "icon": "🏖️",
                    "description": "Perfect weather for the beach",
                    "time": "3-4 hours",
                    "items": "Sunscreen, towel, swimsuit",
                },
                {
                    "title": "Outdoor Picnic",
                    "category": "Outdoor",
                    "icon": "🧺",
                    "description": "Enjoy a meal in the park",
                    "time": "2-3 hours",
                    "items": "Blanket, food, drinks",
                },
                {
                    "title": "Swimming",
                    "category": "Outdoor",
                    "icon": "🏊‍♂️",
                    "description": "Cool off in the water",
                    "time": "1-2 hours",
                    "items": "Swimsuit, towel, water bottle",
                },
                {
                    "title": "Outdoor Sports",
                    "category": "Outdoor",
                    "icon": "⚽",
                    "description": "Great weather for sports",
                    "time": "1-3 hours",
                    "items": "Sports equipment, water",
                },
                {
                    "title": "Garden Work",
                    "category": "Outdoor",
                    "icon": "🌱",
                    "description": "Tend to plants and flowers",
                    "time": "1-2 hours",
                    "items": "Gardening tools, gloves",
                },
            ]
        elif temp > 15:  # Mild weather
            return [
                {
                    "title": "Nature Walk",
                    "category": "Outdoor",
                    "icon": "🚶",
                    "description": "Comfortable weather for walking",
                    "time": "1-2 hours",
                    "items": "Comfortable shoes, water",
                },
                {
                    "title": "Cycling",
                    "category": "Outdoor",
                    "icon": "🚴",
                    "description": "Great conditions for cycling",
                    "time": "1-3 hours",
                    "items": "Bicycle, helmet",
                },
                {
                    "title": "Photography Walk",
                    "category": "Outdoor",
                    "icon": "📸",
                    "description": "Capture beautiful moments",
                    "time": "2-3 hours",
                    "items": "Camera, comfortable shoes",
                },
                {
                    "title": "Outdoor Café",
                    "category": "Outdoor",
                    "icon": "☕",
                    "description": "Enjoy coffee outside",
                    "time": "1-2 hours",
                    "items": "Book or laptop, jacket",
                },
                {
                    "title": "Park Visit",
                    "category": "Outdoor",
                    "icon": "🌳",
                    "description": "Relax in nature",
                    "time": "1-3 hours",
                    "items": "Blanket, snacks",
                },
            ]
        else:  # Cold weather
            return [
                {
                    "title": "Museum Visit",
                    "category": "Indoor",
                    "icon": "🏛️",
                    "description": "Explore art and culture indoors",
                    "time": "2-3 hours",
                    "items": "Camera, comfortable shoes",
                },
                {
                    "title": "Coffee Shop Work",
                    "category": "Indoor",
                    "icon": "☕",
                    "description": "Cozy indoor workspace",
                    "time": "2-4 hours",
                    "items": "Laptop, notebook",
                },
                {
                    "title": "Shopping Mall",
                    "category": "Indoor",
                    "icon": "🛍️",
                    "description": "Warm indoor shopping",
                    "time": "2-4 hours",
                    "items": "Wallet, shopping list",
                },
                {
                    "title": "Gym Workout",
                    "category": "Indoor",
                    "icon": "💪",
                    "description": "Stay active indoors",
                    "time": "1-2 hours",
                    "items": "Workout clothes, water bottle",
                },
                {
                    "title": "Library Visit",
                    "category": "Indoor",
                    "icon": "📖",
                    "description": "Quiet study or reading time",
                    "time": "2-4 hours",
                    "items": "Library card, notebook",
                },
            ]

    def get_activity_by_category(
        self, weather_data: WeatherData, category: str
    ) -> List[Dict[str, Any]]:
        """Get activities filtered by category (Indoor/Outdoor)."""
        all_activities = self.get_activity_suggestions(weather_data)
        return [
            activity
            for activity in all_activities
            if activity["category"].lower() == category.lower()
        ]

    def get_quick_activity(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Get a single quick activity suggestion."""
        activities = self.get_activity_suggestions(weather_data)
        if activities:
            # Return the first activity that's under 2 hours
            for activity in activities:
                if "1" in activity["time"] or "hour" in activity["time"]:
                    return activity
            return activities[0]  # Fallback to first activity
        return {
            "title": "Relax",
            "category": "Indoor",
            "icon": "😌",
            "description": "Take some time to relax",
            "time": "30 minutes",
            "items": "Comfortable space",
        }
