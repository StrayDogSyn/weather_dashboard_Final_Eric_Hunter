"""Google Gemini AI service for intelligent activity suggestions."""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from ..models.activity_models import ActivitySuggestion, UserPreferences, TimeContext, ActivityCategory
from ..models.weather_models import WeatherData
from .config_service import ConfigService


class GeminiService:
    """Service for Google Gemini AI integration."""
    
    def __init__(self, config_service: ConfigService):
        """Initialize Gemini service.
        
        Args:
            config_service: Configuration service instance
        """
        self.config_service = config_service
        self.logger = logging.getLogger(__name__)
        self.model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini API."""
        try:
            if genai is None:
                self.logger.warning("Google Generative AI library not installed")
                return
            
            api_key = self.config_service.get('gemini_api_key')
            if not api_key:
                self.logger.warning("Gemini API key not configured")
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.logger.info("✅ Gemini service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini service: {e}")
    
    async def generate_activity_suggestions(
        self,
        weather_data: WeatherData,
        user_preferences: UserPreferences,
        time_context: TimeContext
    ) -> List[ActivitySuggestion]:
        """Generate AI-powered activity suggestions.
        
        Args:
            weather_data: Current weather conditions
            user_preferences: User preferences and history
            time_context: Time and scheduling context
            
        Returns:
            List of activity suggestions
        """
        if not self.model:
            return self._get_fallback_suggestions(weather_data, user_preferences)
        
        try:
            prompt = self.create_weather_context_prompt(
                weather_data, user_preferences, time_context
            )
            
            response = await asyncio.to_thread(
                self.model.generate_content, prompt
            )
            
            if response and response.text:
                return self.parse_activity_response(response.text)
            else:
                self.logger.warning("Empty response from Gemini API")
                return self._get_fallback_suggestions(weather_data, user_preferences)
                
        except Exception as e:
            self.logger.error(f"Error generating activity suggestions: {e}")
            return self._get_fallback_suggestions(weather_data, user_preferences)
    
    def create_weather_context_prompt(
        self,
        weather_data: WeatherData,
        user_preferences: UserPreferences,
        time_context: TimeContext
    ) -> str:
        """Create intelligent prompt with weather and user context.
        
        Args:
            weather_data: Current weather conditions
            user_preferences: User preferences
            time_context: Time context
            
        Returns:
            Formatted prompt string
        """
        ACTIVITY_PROMPT_TEMPLATE = """
Analyze the current weather conditions and suggest 5 creative, safe, and weather-appropriate activities:

Weather Context:
- Temperature: {temperature}°C
- Condition: {condition}
- Humidity: {humidity}%
- Wind: {wind_speed} km/h
- Visibility: {visibility} km
- UV Index: {uv_index}
- Air Quality: {air_quality}

User Context:
- Fitness Level: {fitness_level}/5
- Available Time: {time_available} minutes
- Budget: {budget_range}
- Equipment: {equipment_list}
- Favorite Categories: {category_preferences}
- Indoor Preference: {indoor_preference}%
- Current Time: {current_time}
- Season: {season}

Generate activities in this exact JSON format:
[
  {{
    "title": "Activity Name",
    "description": "Brief 2-sentence description",
    "category": "fitness|outdoor|creative|social|relaxation|educational",
    "indoor": true/false,
    "duration_minutes": number,
    "difficulty_level": 1-5,
    "equipment_needed": ["item1", "item2"],
    "weather_suitability": 0.0-1.0,
    "cost_estimate": "free|low|medium|high",
    "safety_considerations": ["consideration1", "consideration2"]
  }}
]

Ensure activities are:
1. Weather-appropriate and safe
2. Matched to user's fitness level and preferences
3. Realistic for available time and equipment
4. Diverse in categories and difficulty
5. Include both indoor and outdoor options when appropriate
"""
        
        return ACTIVITY_PROMPT_TEMPLATE.format(
            temperature=weather_data.temperature,
            condition=weather_data.condition,
            humidity=weather_data.humidity,
            wind_speed=weather_data.wind_speed,
            visibility=getattr(weather_data, 'visibility', 10),
            uv_index=getattr(weather_data, 'uv_index', 'N/A'),
            air_quality=getattr(weather_data, 'air_quality', 'Good'),
            fitness_level=user_preferences.fitness_level,
            time_available=time_context.available_minutes,
            budget_range=user_preferences.budget_range,
            equipment_list=', '.join(user_preferences.equipment_available),
            category_preferences=', '.join([cat.value for cat in user_preferences.favorite_categories]),
            indoor_preference=int(user_preferences.indoor_preference * 100),
            current_time=time_context.current_time.strftime('%H:%M'),
            season=time_context.season
        )
    
    def parse_activity_response(self, response: str) -> List[ActivitySuggestion]:
        """Parse Gemini response into activity suggestions.
        
        Args:
            response: Raw response from Gemini API
            
        Returns:
            List of parsed activity suggestions
        """
        try:
            # Extract JSON from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                self.logger.warning("No JSON found in Gemini response")
                return []
            
            json_str = response[start_idx:end_idx]
            activities_data = json.loads(json_str)
            
            suggestions = []
            for i, activity in enumerate(activities_data[:5]):  # Limit to 5
                try:
                    suggestion = ActivitySuggestion(
                        id=f"gemini_{datetime.now().timestamp()}_{i}",
                        title=activity.get('title', 'Unknown Activity'),
                        description=activity.get('description', ''),
                        category=ActivityCategory(activity.get('category', 'outdoor')),
                        indoor=activity.get('indoor', False),
                        duration_minutes=activity.get('duration_minutes', 30),
                        difficulty_level=activity.get('difficulty_level', 3),
                        equipment_needed=activity.get('equipment_needed', []),
                        weather_suitability={'current': activity.get('weather_suitability', 0.8)},
                        cost_estimate=activity.get('cost_estimate', 'free'),
                        safety_considerations=activity.get('safety_considerations', [])
                    )
                    suggestions.append(suggestion)
                except Exception as e:
                    self.logger.warning(f"Error parsing activity {i}: {e}")
                    continue
            
            return suggestions
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from Gemini response: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing activity response: {e}")
            return []
    
    def _get_fallback_suggestions(
        self,
        weather_data: WeatherData,
        user_preferences: UserPreferences
    ) -> List[ActivitySuggestion]:
        """Get fallback suggestions when Gemini is unavailable.
        
        Args:
            weather_data: Current weather conditions
            user_preferences: User preferences
            
        Returns:
            List of fallback activity suggestions
        """
        suggestions = []
        
        # Weather-based fallback logic
        if weather_data.temperature > 20 and 'rain' not in weather_data.condition.lower():
            suggestions.append(ActivitySuggestion(
                id="fallback_outdoor_1",
                title="Outdoor Walk",
                description="Enjoy a refreshing walk in the pleasant weather. Great for fitness and mental health.",
                category=ActivityCategory.FITNESS,
                indoor=False,
                duration_minutes=30,
                difficulty_level=2,
                equipment_needed=["comfortable shoes"],
                weather_suitability={'current': 0.9},
                cost_estimate="free",
                safety_considerations=["Stay hydrated", "Wear sunscreen"]
            ))
        
        if weather_data.temperature < 10 or 'rain' in weather_data.condition.lower():
            suggestions.append(ActivitySuggestion(
                id="fallback_indoor_1",
                title="Indoor Yoga",
                description="Practice mindful yoga to stay active indoors. Perfect for relaxation and flexibility.",
                category=ActivityCategory.FITNESS,
                indoor=True,
                duration_minutes=45,
                difficulty_level=2,
                equipment_needed=["yoga mat"],
                weather_suitability={'current': 1.0},
                cost_estimate="free",
                safety_considerations=["Use proper form", "Listen to your body"]
            ))
        
        # Add more fallback suggestions based on preferences
        if ActivityCategory.CREATIVE in user_preferences.favorite_categories:
            suggestions.append(ActivitySuggestion(
                id="fallback_creative_1",
                title="Creative Writing",
                description="Express your thoughts through writing. Weather can be great inspiration for stories.",
                category=ActivityCategory.CREATIVE,
                indoor=True,
                duration_minutes=60,
                difficulty_level=1,
                equipment_needed=["notebook", "pen"],
                weather_suitability={'current': 1.0},
                cost_estimate="free",
                safety_considerations=[]
            ))
        
        return suggestions[:3]  # Return up to 3 fallback suggestions
    
    def is_available(self) -> bool:
        """Check if Gemini service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        return self.model is not None
    
    async def test_connection(self) -> bool:
        """Test Gemini API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.model:
            return False
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                "Test connection. Respond with 'OK'."
            )
            return response and 'OK' in response.text
        except Exception as e:
            self.logger.error(f"Gemini connection test failed: {e}")
            return False