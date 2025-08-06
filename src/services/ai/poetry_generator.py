import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class WeatherPoetryGenerator:
    """Generates weather-themed poetry using Gemini AI"""
    
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
        self.poetry_styles = {
            'haiku': {
                'description': '5-7-5 syllable pattern',
                'prompt': 'Write a haiku about {condition} weather with temperature {temp}°C. Follow 5-7-5 syllable pattern strictly.'
            },
            'limerick': {
                'description': 'Humorous 5-line poem',
                'prompt': 'Write a funny limerick about {condition} weather in {location}. Make it witty and weather-themed.'
            },
            'free_verse': {
                'description': 'Modern free-form poetry',
                'prompt': 'Write a short free verse poem capturing the essence of {condition} weather, {temp}°C, with {wind} wind.'
            },
            'sonnet': {
                'description': '14-line classical poem',
                'prompt': 'Write a 14-line sonnet about {condition} weather. Include imagery of temperature {temp}°C and {humidity}% humidity.'
            }
        }
        
    async def generate_poem(self, style: str, weather_data: dict) -> dict:
        """Generate weather-based poetry"""
        if style not in self.poetry_styles:
            raise ValueError(f"Unknown style: {style}")
        
        # Build prompt
        prompt_template = self.poetry_styles[style]['prompt']
        prompt = prompt_template.format(
            condition=weather_data.get('condition', 'mysterious weather'),
            temp=weather_data.get('temperature', 'comfortable'),
            location=weather_data.get('location', 'this place'),
            wind=weather_data.get('wind_description', 'gentle'),
            humidity=weather_data.get('humidity', 50)
        )
        
        try:
            response = await self.gemini_service.generate_content(prompt)
            
            return {
                'style': style,
                'poem': response,
                'weather': weather_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Poetry generation failed: {e}")
            return self.get_fallback_poem(style, weather_data)
    
    def get_fallback_poem(self, style: str, weather_data: dict) -> dict:
        """Provide fallback poems when AI generation fails"""
        fallback_poems = {
            'haiku': [
                "Gray clouds gather fast\nRaindrops dance on window panes\nNature's gentle song",
                "Sunshine breaks through clouds\nWarm rays kiss the morning dew\nDay begins anew",
                "Winter wind whispers\nSnowflakes fall like silent dreams\nEarth sleeps peacefully"
            ],
            'limerick': [
                "There once was weather so fine,\nWith sunshine that loved to shine,\nThe clouds stayed away,\nFor most of the day,\nAnd the forecast was simply divine!",
                "A storm cloud rolled in with a roar,\nWith rain like we'd not seen before,\nIt thundered and flashed,\nWhile the raindrops all dashed,\nThen left us all wanting much more!"
            ],
            'free_verse': [
                "The sky speaks in whispers today,\nClouds drift like thoughts\nacross the canvas of blue.\nTemperature holds steady,\na comfortable embrace\nfrom the atmosphere.",
                "Wind carries stories\nfrom distant places,\nwhile the sun paints\ngolden highlights\non everything it touches."
            ],
            'sonnet': [
                "When weather paints the world in shades of gray,\nAnd clouds like cotton blankets fill the sky,\nThe temperature speaks of autumn's way,\nAs gentle breezes whisper and reply.\n\nThe humidity hangs thick upon the air,\nLike morning mist that clings to verdant ground,\nWhile nature shows her beauty everywhere,\nIn every sight and every gentle sound.\n\nThough storms may come and sunshine may depart,\nThe weather's dance continues through each day,\nA symphony that touches every heart,\nIn its eternal, ever-changing way.\n\nSo let us pause and feel the weather's grace,\nAnd find in nature's moods our peaceful place."
            ]
        }
        
        import random
        fallback_poem = random.choice(fallback_poems.get(style, fallback_poems['haiku']))
        
        return {
            'style': style,
            'poem': fallback_poem,
            'weather': weather_data,
            'timestamp': datetime.now().isoformat(),
            'fallback': True
        }
    
    def get_available_styles(self) -> Dict[str, str]:
        """Get list of available poetry styles with descriptions"""
        return {style: info['description'] for style, info in self.poetry_styles.items()}
    
    async def generate_multiple_poems(self, weather_data: dict, styles: list = None) -> Dict[str, dict]:
        """Generate multiple poems in different styles"""
        if styles is None:
            styles = list(self.poetry_styles.keys())
        
        poems = {}
        for style in styles:
            if style in self.poetry_styles:
                try:
                    poems[style] = await self.generate_poem(style, weather_data)
                except Exception as e:
                    logger.error(f"Failed to generate {style} poem: {e}")
                    poems[style] = self.get_fallback_poem(style, weather_data)
        
        return poems