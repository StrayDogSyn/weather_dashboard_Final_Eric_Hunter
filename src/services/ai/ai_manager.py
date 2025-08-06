import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..gemini_service import GeminiService
from .poetry_generator import WeatherPoetryGenerator
from .activity_suggestions import WeatherActivitySuggestions

logger = logging.getLogger(__name__)

class AIManager:
    """Unified manager for all AI-powered features in the weather dashboard"""
    
    def __init__(self, api_key: str = None):
        self.gemini_service = GeminiService(api_key)
        self.poetry_generator = WeatherPoetryGenerator(self.gemini_service)
        self.activity_suggestions = WeatherActivitySuggestions(self.gemini_service)
        
        self.is_available = self.gemini_service.is_configured
        
        if self.is_available:
            logger.info("AI Manager initialized successfully with Gemini integration")
        else:
            logger.warning("AI Manager initialized in fallback mode - Gemini not available")
    
    async def generate_weather_poetry(self, style: str, weather_data: dict) -> dict:
        """Generate weather-themed poetry in specified style"""
        try:
            return await self.poetry_generator.generate_poem(style, weather_data)
        except Exception as e:
            logger.error(f"Poetry generation failed: {e}")
            return self.poetry_generator.get_fallback_poem(style, weather_data)
    
    async def generate_multiple_poems(self, weather_data: dict, styles: list = None) -> Dict[str, dict]:
        """Generate multiple poems in different styles"""
        try:
            return await self.poetry_generator.generate_multiple_poems(weather_data, styles)
        except Exception as e:
            logger.error(f"Multiple poetry generation failed: {e}")
            # Return fallback poems for all requested styles
            if styles is None:
                styles = list(self.poetry_generator.poetry_styles.keys())
            
            fallback_poems = {}
            for style in styles:
                fallback_poems[style] = self.poetry_generator.get_fallback_poem(style, weather_data)
            return fallback_poems
    
    async def get_activity_suggestions(self, weather_data: dict, preferences: dict = None) -> Dict[str, Any]:
        """Get AI-powered activity suggestions"""
        try:
            return await self.activity_suggestions.generate_suggestions(weather_data, preferences)
        except Exception as e:
            logger.error(f"Activity suggestions failed: {e}")
            return self.activity_suggestions._get_fallback_suggestions(weather_data, preferences)
    
    async def get_category_activities(self, category: str, weather_data: dict) -> List[Dict[str, Any]]:
        """Get activities for a specific category"""
        try:
            return await self.activity_suggestions.get_category_suggestions(category, weather_data)
        except Exception as e:
            logger.error(f"Category activity suggestions failed: {e}")
            return []
    
    async def get_weather_insights(self, weather_data: dict) -> str:
        """Get AI-generated weather insights"""
        try:
            return await self.gemini_service.get_weather_insights(weather_data)
        except Exception as e:
            logger.error(f"Weather insights generation failed: {e}")
            return self._get_fallback_insights(weather_data)
    
    async def generate_weather_story(self, weather_data: dict, story_type: str = 'short') -> dict:
        """Generate a weather-themed story or narrative"""
        story_prompts = {
            'short': 'Write a short 2-paragraph story inspired by {condition} weather at {temp}°C. Make it atmospheric and engaging.',
            'adventure': 'Write an adventure story where the {condition} weather plays a crucial role in the plot. Include the {temp}°C temperature as an important element.',
            'mystery': 'Write a mysterious short story where {condition} weather creates the perfect atmosphere for intrigue at {temp}°C.',
            'romance': 'Write a romantic scene where {condition} weather at {temp}°C brings two characters together.',
            'fantasy': 'Write a fantasy tale where {condition} weather has magical properties in a world where temperature {temp}°C affects magic.'
        }
        
        if story_type not in story_prompts:
            story_type = 'short'
        
        prompt = story_prompts[story_type].format(
            condition=weather_data.get('condition', 'mysterious'),
            temp=weather_data.get('temperature', 20)
        )
        
        try:
            story = await self.gemini_service.generate_content(prompt)
            return {
                'story': story,
                'type': story_type,
                'weather': weather_data,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            return self._get_fallback_story(weather_data, story_type)
    
    async def generate_weather_facts(self, weather_data: dict) -> List[str]:
        """Generate interesting weather facts based on current conditions"""
        prompt = f"""
        Generate 5 interesting and educational facts about {weather_data.get('condition', 'weather')} conditions 
        and temperatures around {weather_data.get('temperature', 20)}°C. 
        
        Make the facts engaging, scientifically accurate, and relevant to the current weather.
        Format as a simple list, one fact per line.
        """
        
        try:
            response = await self.gemini_service.generate_content(prompt)
            facts = [fact.strip() for fact in response.split('\n') if fact.strip() and not fact.strip().startswith('#')]
            return facts[:5]  # Limit to 5 facts
        except Exception as e:
            logger.error(f"Weather facts generation failed: {e}")
            return self._get_fallback_facts(weather_data)
    
    def _get_fallback_insights(self, weather_data: dict) -> str:
        """Provide fallback weather insights"""
        temp = weather_data.get('temperature', 20)
        condition = weather_data.get('condition', 'current weather')
        
        insights = f"The {condition} conditions with a temperature of {temp}°C create "
        
        if temp > 25:
            insights += "ideal conditions for outdoor activities. Stay hydrated and consider sun protection."
        elif temp < 5:
            insights += "perfect weather for cozy indoor activities. Dress warmly if venturing outside."
        else:
            insights += "comfortable conditions for both indoor and outdoor pursuits."
        
        return insights
    
    def _get_fallback_story(self, weather_data: dict, story_type: str) -> dict:
        """Provide fallback weather story"""
        condition = weather_data.get('condition', 'mysterious weather')
        temp = weather_data.get('temperature', 20)
        
        fallback_stories = {
            'short': f"The {condition} created a perfect backdrop for the day ahead. At {temp}°C, the temperature felt just right for whatever adventures might unfold. Sometimes the best moments happen when we simply step outside and embrace whatever weather greets us.",
            'adventure': f"The {condition} weather at {temp}°C set the stage for an unexpected journey. What started as an ordinary day became extraordinary when the weather itself became part of the adventure.",
            'mystery': f"The {condition} conditions at {temp}°C seemed to hold secrets in every shadow. The weather itself became a character in the unfolding mystery.",
            'romance': f"Under the {condition} sky, with the temperature at a perfect {temp}°C, two hearts found each other. Sometimes the weather knows exactly when to create the perfect moment.",
            'fantasy': f"In a realm where {condition} weather at {temp}°C held magical properties, the very air shimmered with possibility and ancient power."
        }
        
        return {
            'story': fallback_stories.get(story_type, fallback_stories['short']),
            'type': story_type,
            'weather': weather_data,
            'timestamp': datetime.now().isoformat(),
            'fallback': True
        }
    
    def _get_fallback_facts(self, weather_data: dict) -> List[str]:
        """Provide fallback weather facts"""
        return [
            "Weather patterns are influenced by atmospheric pressure, temperature, and humidity.",
            "The Earth's rotation affects wind patterns through the Coriolis effect.",
            "Clouds form when water vapor in the air condenses around tiny particles.",
            "Temperature differences between air masses create weather fronts.",
            "Humidity affects how temperature feels to the human body."
        ]
    
    def get_available_poetry_styles(self) -> Dict[str, str]:
        """Get available poetry styles"""
        return self.poetry_generator.get_available_styles()
    
    def get_available_activity_categories(self) -> Dict[str, str]:
        """Get available activity categories"""
        return self.activity_suggestions.get_available_categories()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive AI service status"""
        gemini_status = self.gemini_service.get_service_status()
        
        return {
            'ai_manager_available': True,
            'gemini_service': gemini_status,
            'poetry_generator_available': True,
            'activity_suggestions_available': True,
            'features': {
                'poetry_generation': self.is_available,
                'activity_suggestions': self.is_available,
                'weather_insights': self.is_available,
                'weather_stories': self.is_available,
                'weather_facts': self.is_available
            },
            'fallback_mode': not self.is_available
        }
    
    async def test_all_features(self, weather_data: dict) -> Dict[str, Any]:
        """Test all AI features with sample data"""
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'weather_data': weather_data,
            'tests': {}
        }
        
        # Test poetry generation
        try:
            poem = await self.generate_weather_poetry('haiku', weather_data)
            test_results['tests']['poetry'] = {
                'success': True,
                'sample': poem.get('poem', '')[:100] + '...' if len(poem.get('poem', '')) > 100 else poem.get('poem', '')
            }
        except Exception as e:
            test_results['tests']['poetry'] = {'success': False, 'error': str(e)}
        
        # Test activity suggestions
        try:
            activities = await self.get_activity_suggestions(weather_data)
            test_results['tests']['activities'] = {
                'success': True,
                'count': len(activities.get('suggestions', []))
            }
        except Exception as e:
            test_results['tests']['activities'] = {'success': False, 'error': str(e)}
        
        # Test weather insights
        try:
            insights = await self.get_weather_insights(weather_data)
            test_results['tests']['insights'] = {
                'success': True,
                'sample': insights[:100] + '...' if len(insights) > 100 else insights
            }
        except Exception as e:
            test_results['tests']['insights'] = {'success': False, 'error': str(e)}
        
        return test_results