import logging
from datetime import datetime
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)

class WeatherActivitySuggestions:
    """Generates weather-appropriate activity suggestions using AI"""
    
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
        self.activity_categories = {
            'outdoor': {
                'description': 'Activities best enjoyed outside',
                'weather_requirements': ['sunny', 'partly_cloudy', 'clear']
            },
            'indoor': {
                'description': 'Activities perfect for staying inside',
                'weather_requirements': ['rainy', 'stormy', 'snowy', 'extreme_cold', 'extreme_heat']
            },
            'exercise': {
                'description': 'Physical activities and workouts',
                'weather_requirements': ['any']
            },
            'creative': {
                'description': 'Artistic and creative pursuits',
                'weather_requirements': ['any']
            },
            'social': {
                'description': 'Activities to enjoy with others',
                'weather_requirements': ['any']
            },
            'relaxation': {
                'description': 'Peaceful and calming activities',
                'weather_requirements': ['any']
            }
        }
        
        self.fallback_activities = {
            'sunny': [
                {'name': 'Outdoor Picnic', 'category': 'outdoor', 'description': 'Enjoy a meal in the park with beautiful weather'},
                {'name': 'Nature Photography', 'category': 'outdoor', 'description': 'Capture the beauty of sunny landscapes'},
                {'name': 'Beach Volleyball', 'category': 'exercise', 'description': 'Fun team sport perfect for sunny days'},
                {'name': 'Gardening', 'category': 'outdoor', 'description': 'Tend to plants and enjoy the sunshine'}
            ],
            'rainy': [
                {'name': 'Reading Marathon', 'category': 'indoor', 'description': 'Cozy up with a good book and hot tea'},
                {'name': 'Indoor Yoga', 'category': 'exercise', 'description': 'Peaceful exercise while listening to rain'},
                {'name': 'Cooking Project', 'category': 'creative', 'description': 'Try a new recipe or bake something special'},
                {'name': 'Board Games', 'category': 'social', 'description': 'Fun indoor games with family or friends'}
            ],
            'snowy': [
                {'name': 'Hot Chocolate & Movies', 'category': 'relaxation', 'description': 'Warm drinks and cozy entertainment'},
                {'name': 'Winter Photography', 'category': 'outdoor', 'description': 'Capture beautiful snowy landscapes'},
                {'name': 'Indoor Crafts', 'category': 'creative', 'description': 'Perfect weather for artistic projects'},
                {'name': 'Fireplace Reading', 'category': 'relaxation', 'description': 'Read by a warm fire while snow falls'}
            ],
            'cloudy': [
                {'name': 'Museum Visit', 'category': 'indoor', 'description': 'Perfect weather for cultural exploration'},
                {'name': 'Coffee Shop Writing', 'category': 'creative', 'description': 'Atmospheric weather for creative writing'},
                {'name': 'Indoor Rock Climbing', 'category': 'exercise', 'description': 'Active fun regardless of weather'},
                {'name': 'Shopping', 'category': 'social', 'description': 'Browse stores and enjoy indoor activities'}
            ]
        }
    
    async def generate_suggestions(self, weather_data: dict, preferences: dict = None) -> Dict[str, Any]:
        """Generate AI-powered activity suggestions based on weather"""
        try:
            # Build context-aware prompt
            prompt = self._build_activity_prompt(weather_data, preferences)
            
            # Get AI suggestions
            response = await self.gemini_service.generate_content(prompt)
            
            # Parse and structure the response
            suggestions = self._parse_ai_response(response, weather_data)
            
            return {
                'suggestions': suggestions,
                'weather_context': weather_data,
                'timestamp': datetime.now().isoformat(),
                'ai_generated': True
            }
            
        except Exception as e:
            logger.error(f"AI activity suggestion failed: {e}")
            return self._get_fallback_suggestions(weather_data, preferences)
    
    def _build_activity_prompt(self, weather_data: dict, preferences: dict = None) -> str:
        """Build a context-aware prompt for activity suggestions"""
        base_prompt = f"""
        Based on the current weather conditions, suggest 6-8 specific activities that would be perfect for today.
        
        Weather Details:
        - Condition: {weather_data.get('condition', 'unknown')}
        - Temperature: {weather_data.get('temperature', 'unknown')}°C
        - Humidity: {weather_data.get('humidity', 'unknown')}%
        - Wind: {weather_data.get('wind_speed', 'unknown')} km/h
        - Location: {weather_data.get('location', 'unknown')}
        """
        
        if preferences:
            base_prompt += f"""
            
            User Preferences:
            - Preferred categories: {preferences.get('categories', 'any')}
            - Activity level: {preferences.get('activity_level', 'moderate')}
            - Indoor/Outdoor preference: {preferences.get('location_preference', 'any')}
            - Time available: {preferences.get('time_available', 'flexible')}
            """
        
        base_prompt += """
        
        Please provide suggestions in this JSON format:
        {
            "activities": [
                {
                    "name": "Activity Name",
                    "category": "outdoor/indoor/exercise/creative/social/relaxation",
                    "description": "Brief description of why this is perfect for current weather",
                    "duration": "estimated time needed",
                    "difficulty": "easy/moderate/challenging",
                    "weather_match": "explanation of how this fits the weather"
                }
            ]
        }
        
        Focus on activities that specifically take advantage of or are well-suited to the current weather conditions.
        """
        
        return base_prompt
    
    def _parse_ai_response(self, response: str, weather_data: dict) -> List[Dict[str, Any]]:
        """Parse AI response and extract structured activity data"""
        try:
            # Try to extract JSON from the response
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                
                parsed = json.loads(json_str)
                activities = parsed.get('activities', [])
                
                # Validate and enhance each activity
                validated_activities = []
                for activity in activities:
                    if self._validate_activity(activity):
                        activity['weather_condition'] = weather_data.get('condition', 'unknown')
                        activity['temperature_range'] = self._get_temperature_category(weather_data.get('temperature', 20))
                        validated_activities.append(activity)
                
                return validated_activities
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse AI response: {e}")
        
        # Fallback to text parsing if JSON parsing fails
        return self._parse_text_response(response, weather_data)
    
    def _validate_activity(self, activity: dict) -> bool:
        """Validate that an activity has required fields"""
        required_fields = ['name', 'category', 'description']
        return all(field in activity and activity[field] for field in required_fields)
    
    def _parse_text_response(self, response: str, weather_data: dict) -> List[Dict[str, Any]]:
        """Parse text response when JSON parsing fails"""
        activities = []
        lines = response.split('\n')
        
        current_activity = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    
                    if key in ['name', 'activity', 'title']:
                        if current_activity:
                            activities.append(current_activity)
                        current_activity = {'name': value, 'category': 'general', 'description': ''}
                    elif key in ['description', 'details']:
                        current_activity['description'] = value
                    elif key == 'category':
                        current_activity['category'] = value
        
        if current_activity:
            activities.append(current_activity)
        
        return activities[:8]  # Limit to 8 activities
    
    def _get_temperature_category(self, temp: float) -> str:
        """Categorize temperature for activity matching"""
        if temp < 0:
            return 'freezing'
        elif temp < 10:
            return 'cold'
        elif temp < 20:
            return 'cool'
        elif temp < 25:
            return 'mild'
        elif temp < 30:
            return 'warm'
        else:
            return 'hot'
    
    def _get_fallback_suggestions(self, weather_data: dict, preferences: dict = None) -> Dict[str, Any]:
        """Provide fallback suggestions when AI generation fails"""
        condition = weather_data.get('condition', '').lower()
        
        # Map weather conditions to fallback categories
        if any(word in condition for word in ['sun', 'clear', 'bright']):
            activities = self.fallback_activities['sunny']
        elif any(word in condition for word in ['rain', 'storm', 'drizzle']):
            activities = self.fallback_activities['rainy']
        elif any(word in condition for word in ['snow', 'blizzard', 'flurr']):
            activities = self.fallback_activities['snowy']
        else:
            activities = self.fallback_activities['cloudy']
        
        # Filter by preferences if provided
        if preferences and 'categories' in preferences:
            preferred_categories = preferences['categories']
            if isinstance(preferred_categories, str):
                preferred_categories = [preferred_categories]
            activities = [a for a in activities if a['category'] in preferred_categories]
        
        return {
            'suggestions': activities,
            'weather_context': weather_data,
            'timestamp': datetime.now().isoformat(),
            'ai_generated': False,
            'fallback': True
        }
    
    async def get_category_suggestions(self, category: str, weather_data: dict) -> List[Dict[str, Any]]:
        """Get suggestions for a specific activity category"""
        if category not in self.activity_categories:
            raise ValueError(f"Unknown category: {category}")
        
        prompt = f"""
        Suggest 5 specific {category} activities that are perfect for {weather_data.get('condition', 'current')} weather 
        at {weather_data.get('temperature', 20)}°C.
        
        Focus on {self.activity_categories[category]['description']}.
        
        Provide each suggestion with:
        - Activity name
        - Brief description
        - Why it's perfect for this weather
        """
        
        try:
            response = await self.gemini_service.generate_content(prompt)
            suggestions = self._parse_ai_response(response, weather_data)
            
            # Ensure all suggestions are in the requested category
            for suggestion in suggestions:
                suggestion['category'] = category
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Category suggestion failed: {e}")
            return [a for a in self.fallback_activities.get(weather_data.get('condition', 'cloudy'), []) 
                   if a['category'] == category][:5]
    
    def get_available_categories(self) -> Dict[str, str]:
        """Get list of available activity categories"""
        return {cat: info['description'] for cat, info in self.activity_categories.items()}