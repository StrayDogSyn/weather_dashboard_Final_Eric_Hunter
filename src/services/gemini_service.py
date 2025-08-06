"""Gemini AI Service for Activity Suggestions."""

import os
import json
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Google Generative AI not available. Install with: pip install google-generativeai")

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for AI-powered activity suggestions using Google Gemini."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        self.is_configured = False
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.is_configured = True
                logger.info("Gemini service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini service: {e}")
                self.is_configured = False
        else:
            logger.warning("Gemini service not configured - missing API key or library")
            
    def test_connection(self) -> bool:
        """Test connection to Gemini API."""
        if not self.is_configured:
            return False
            
        try:
            response = self.model.generate_content("Hello, this is a test.")
            return bool(response.text)
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False
            
    async def generate_content(self, prompt: str) -> str:
        """Generate content using Gemini AI."""
        if not self.is_configured:
            return self._get_fallback_response(prompt)
            
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self.model.generate_content, 
                prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating content with Gemini: {e}")
            return self._get_fallback_response(prompt)
            
    async def get_activity_suggestions(self, weather_data: Dict, preferences: Dict = None) -> List[Dict]:
        """Get AI-powered activity suggestions based on weather conditions."""
        try:
            # Build comprehensive prompt
            prompt = self._build_activity_prompt(weather_data, preferences)
            
            # Get AI response
            response = await self.generate_content(prompt)
            
            # Parse response into structured suggestions
            suggestions = self._parse_activity_response(response)
            
            # Add metadata
            for suggestion in suggestions:
                suggestion['generated_at'] = datetime.now().isoformat()
                suggestion['weather_context'] = {
                    'temperature': weather_data.get('temperature'),
                    'condition': weather_data.get('condition'),
                    'wind_speed': weather_data.get('wind_speed')
                }
                
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting activity suggestions: {e}")
            return self._get_fallback_activities(weather_data)
            
    def _build_activity_prompt(self, weather_data: Dict, preferences: Dict = None) -> str:
        """Build a comprehensive prompt for activity suggestions."""
        current_time = datetime.now()
        time_of_day = self._get_time_of_day(current_time)
        season = self._get_season(current_time)
        
        # Base weather information
        prompt = f"""
As an expert activity advisor, suggest 5 engaging activities based on the current weather conditions and context.

Weather Conditions:
- Temperature: {weather_data.get('temperature', 'Unknown')}°C
- Condition: {weather_data.get('condition', 'Unknown')}
- Wind Speed: {weather_data.get('wind_speed', 'Unknown')} km/h
- Humidity: {weather_data.get('humidity', 'Unknown')}%
- UV Index: {weather_data.get('uv_index', 'Unknown')}

Context:
- Time: {current_time.strftime('%H:%M')}
- Time of Day: {time_of_day}
- Season: {season}
- Day of Week: {current_time.strftime('%A')}
"""

        # Add preferences if provided
        if preferences:
            prompt += f"""
User Preferences:
- Activity Types: {preferences.get('activity_types', 'Any')}
- Fitness Level: {preferences.get('fitness_level', 'Moderate')}
- Duration Preference: {preferences.get('duration', 'Flexible')}
- Indoor/Outdoor: {preferences.get('location_preference', 'Both')}
- Budget: {preferences.get('budget', 'Flexible')}
"""

        prompt += """
For each activity, provide:
1. Activity Name (creative and specific)
2. Duration (in minutes)
3. Required Items (be specific)
4. Why it's perfect for this weather (detailed explanation)
5. Difficulty Level (Easy/Moderate/Hard)
6. Location Type (Indoor/Outdoor/Both)
7. Health Benefits
8. Fun Factor (1-10)

Format your response as a JSON array with this structure:
[
  {
    "name": "Activity Name",
    "duration": 60,
    "required_items": ["item1", "item2"],
    "weather_reasoning": "Why this is perfect for current weather",
    "difficulty": "Easy",
    "location": "Outdoor",
    "health_benefits": ["benefit1", "benefit2"],
    "fun_factor": 8,
    "description": "Detailed activity description",
    "tips": ["tip1", "tip2"]
  }
]

Make suggestions creative, practical, and perfectly matched to the weather conditions. Consider safety, enjoyment, and health benefits.
"""
        
        return prompt
        
    def _parse_activity_response(self, response: str) -> List[Dict]:
        """Parse AI response into structured activity suggestions."""
        try:
            # Try to extract JSON from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                activities = json.loads(json_str)
                
                # Validate and clean up activities
                validated_activities = []
                for activity in activities:
                    if self._validate_activity(activity):
                        validated_activities.append(self._clean_activity(activity))
                        
                return validated_activities[:5]  # Limit to 5 activities
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing activity response: {e}")
            
        # Fallback: try to parse as text
        return self._parse_text_response(response)
        
    def _validate_activity(self, activity: Dict) -> bool:
        """Validate activity structure."""
        required_fields = ['name', 'duration', 'required_items', 'weather_reasoning']
        return all(field in activity for field in required_fields)
        
    def _clean_activity(self, activity: Dict) -> Dict:
        """Clean and standardize activity data."""
        cleaned = {
            'name': str(activity.get('name', 'Unknown Activity')),
            'duration': int(activity.get('duration', 30)),
            'required_items': activity.get('required_items', []),
            'weather_reasoning': str(activity.get('weather_reasoning', '')),
            'difficulty': activity.get('difficulty', 'Moderate'),
            'location': activity.get('location', 'Both'),
            'health_benefits': activity.get('health_benefits', []),
            'fun_factor': min(10, max(1, int(activity.get('fun_factor', 5)))),
            'description': activity.get('description', ''),
            'tips': activity.get('tips', [])
        }
        
        # Ensure required_items is a list
        if isinstance(cleaned['required_items'], str):
            cleaned['required_items'] = [cleaned['required_items']]
            
        return cleaned
        
    def _parse_text_response(self, response: str) -> List[Dict]:
        """Parse text response as fallback."""
        activities = []
        lines = response.split('\n')
        current_activity = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for activity patterns
            if 'Activity:' in line or line.startswith('1.') or line.startswith('2.'):
                if current_activity:
                    activities.append(current_activity)
                current_activity = {
                    'name': line.split(':', 1)[-1].strip() if ':' in line else line,
                    'duration': 30,
                    'required_items': [],
                    'weather_reasoning': '',
                    'difficulty': 'Moderate',
                    'location': 'Both',
                    'health_benefits': [],
                    'fun_factor': 5,
                    'description': '',
                    'tips': []
                }
            elif 'Duration:' in line:
                try:
                    duration_str = line.split(':', 1)[-1].strip()
                    current_activity['duration'] = int(''.join(filter(str.isdigit, duration_str)))
                except ValueError:
                    pass
            elif 'Items:' in line or 'Required:' in line:
                items_str = line.split(':', 1)[-1].strip()
                current_activity['required_items'] = [item.strip() for item in items_str.split(',')]
            elif 'Why:' in line or 'Reasoning:' in line:
                current_activity['weather_reasoning'] = line.split(':', 1)[-1].strip()
                
        if current_activity:
            activities.append(current_activity)
            
        return activities[:5]
        
    def _get_fallback_response(self, prompt: str) -> str:
        """Get fallback response when Gemini is not available."""
        return """
[
  {
    "name": "Weather-Appropriate Indoor Reading",
    "duration": 45,
    "required_items": ["Book or e-reader", "Comfortable seating", "Good lighting"],
    "weather_reasoning": "Perfect indoor activity regardless of weather conditions",
    "difficulty": "Easy",
    "location": "Indoor",
    "health_benefits": ["Mental stimulation", "Stress reduction", "Improved focus"],
    "fun_factor": 7,
    "description": "Enjoy a good book in a comfortable indoor environment",
    "tips": ["Choose a book that matches your mood", "Create a cozy reading nook"]
  }
]
"""
        
    def _get_fallback_activities(self, weather_data: Dict) -> List[Dict]:
        """Get fallback activities when AI is not available."""
        temp = weather_data.get('temperature', 20)
        condition = weather_data.get('condition', '').lower()
        
        activities = []
        
        if temp > 25:
            activities.append({
                'name': 'Outdoor Water Activities',
                'duration': 90,
                'required_items': ['Swimwear', 'Sunscreen', 'Water bottle'],
                'weather_reasoning': 'Perfect warm weather for cooling water activities',
                'difficulty': 'Easy',
                'location': 'Outdoor',
                'health_benefits': ['Cardiovascular exercise', 'Full body workout'],
                'fun_factor': 9,
                'description': 'Enjoy swimming, water sports, or pool activities',
                'tips': ['Stay hydrated', 'Apply sunscreen regularly']
            })
        elif temp < 5:
            activities.append({
                'name': 'Cozy Indoor Crafting',
                'duration': 120,
                'required_items': ['Craft supplies', 'Warm beverage', 'Comfortable workspace'],
                'weather_reasoning': 'Cold weather is perfect for indoor creative activities',
                'difficulty': 'Easy',
                'location': 'Indoor',
                'health_benefits': ['Stress relief', 'Improved dexterity', 'Mental stimulation'],
                'fun_factor': 8,
                'description': 'Work on creative projects while staying warm indoors',
                'tips': ['Choose projects that match your skill level', 'Take breaks to stretch']
            })
        else:
            activities.append({
                'name': 'Nature Walk and Photography',
                'duration': 60,
                'required_items': ['Camera or phone', 'Comfortable shoes', 'Weather-appropriate clothing'],
                'weather_reasoning': 'Moderate weather is ideal for outdoor exploration',
                'difficulty': 'Easy',
                'location': 'Outdoor',
                'health_benefits': ['Cardiovascular exercise', 'Vitamin D', 'Mental wellness'],
                'fun_factor': 8,
                'description': 'Explore nature while capturing beautiful moments',
                'tips': ['Look for interesting lighting', 'Focus on details in nature']
            })
            
        # Add weather-specific activities
        if 'rain' in condition:
            activities.append({
                'name': 'Indoor Yoga and Meditation',
                'duration': 45,
                'required_items': ['Yoga mat', 'Comfortable clothing', 'Quiet space'],
                'weather_reasoning': 'Rainy weather creates a peaceful atmosphere for mindfulness',
                'difficulty': 'Easy',
                'location': 'Indoor',
                'health_benefits': ['Flexibility', 'Stress reduction', 'Mental clarity'],
                'fun_factor': 7,
                'description': 'Practice yoga and meditation while listening to rain',
                'tips': ['Start with beginner poses', 'Focus on breathing']
            })
            
        return activities
        
    def _get_time_of_day(self, dt: datetime) -> str:
        """Get time of day description."""
        hour = dt.hour
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"
            
    def _get_season(self, dt: datetime) -> str:
        """Get current season."""
        month = dt.month
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Autumn"
            
    async def get_weather_insights(self, weather_data: Dict) -> str:
        """Get AI insights about current weather conditions."""
        prompt = f"""
Provide interesting insights and observations about the current weather conditions:

Weather Data:
- Temperature: {weather_data.get('temperature')}°C
- Condition: {weather_data.get('condition')}
- Humidity: {weather_data.get('humidity')}%
- Wind Speed: {weather_data.get('wind_speed')} km/h
- Pressure: {weather_data.get('pressure')} hPa
- UV Index: {weather_data.get('uv_index')}

Provide 2-3 interesting insights about:
1. What this weather means for outdoor activities
2. Health considerations for these conditions
3. Interesting meteorological facts about this weather pattern

Keep it informative but engaging, around 150 words total.
"""
        
        response = await self.generate_content(prompt)
        return response if response else "Current weather conditions are suitable for various activities. Stay hydrated and dress appropriately for the temperature."
        
    def get_service_status(self) -> Dict:
        """Get service status information."""
        return {
            'configured': self.is_configured,
            'api_available': GEMINI_AVAILABLE,
            'has_api_key': bool(self.api_key),
            'model_loaded': self.model is not None
        }