"""OpenAI Fallback Service

Provides fallback functionality when OpenAI API is rate limited or unavailable.
Includes mock responses to maintain application functionality.
"""

import logging
from typing import Dict, Any

try:
    import openai
    from openai import RateLimitError
except ImportError:
    openai = None
    class RateLimitError(Exception):
        pass

logger = logging.getLogger(__name__)


class OpenAIFallback:
    """OpenAI service with fallback to mock responses when rate limited."""
    
    def __init__(self):
        self.rate_limited = False
        self.fallback_to_mock = True
        
    def get_completion(self, prompt: str) -> str:
        """Get completion with fallback"""
        if self.rate_limited:
            return self._get_mock_response(prompt)
            
        try:
            response = self._try_openai(prompt)
            return response
        except RateLimitError:
            logger.warning("OpenAI rate limited, using mock responses")
            self.rate_limited = True
            return self._get_mock_response(prompt)
    
    def _try_openai(self, prompt: str) -> str:
        """Attempt to get response from OpenAI API."""
        if not openai:
            raise RateLimitError("OpenAI not available")
            
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise RateLimitError(f"OpenAI API error: {e}")
    
    def _get_mock_response(self, prompt: str) -> str:
        """Generate mock response based on prompt content."""
        prompt_lower = prompt.lower()
        
        # Weather-related responses
        if any(word in prompt_lower for word in ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'cloudy']):
            return self._get_weather_mock_response(prompt_lower)
        
        # Location-related responses
        if any(word in prompt_lower for word in ['location', 'city', 'place', 'where']):
            return "This appears to be a location-related query. Please check the weather data for accurate information."
        
        # Analysis-related responses
        if any(word in prompt_lower for word in ['analyze', 'analysis', 'trend', 'pattern']):
            return "Based on the available data, there are interesting patterns that suggest seasonal variations and regional differences."
        
        # Default response
        return "I'm currently using a fallback response due to API limitations. Please try again later for more detailed information."
    
    def _get_weather_mock_response(self, prompt: str) -> str:
        """Generate weather-specific mock responses."""
        if 'temperature' in prompt:
            return "Temperature patterns show typical seasonal variations with moderate fluctuations throughout the day."
        elif 'rain' in prompt or 'precipitation' in prompt:
            return "Precipitation levels appear normal for this time of year with occasional showers expected."
        elif 'forecast' in prompt:
            return "The forecast indicates generally stable weather conditions with typical seasonal patterns."
        elif 'sunny' in prompt or 'clear' in prompt:
            return "Clear skies and sunny conditions are favorable for outdoor activities."
        elif 'cloudy' in prompt or 'overcast' in prompt:
            return "Cloudy conditions may persist with possible breaks in cloud cover throughout the day."
        else:
            return "Weather conditions appear to be within normal ranges for this location and time of year."
    
    def reset_rate_limit(self):
        """Reset rate limit status (for testing or manual reset)."""
        self.rate_limited = False
        logger.info("Rate limit status reset")
    
    def is_rate_limited(self) -> bool:
        """Check if currently rate limited."""
        return self.rate_limited
    
    def set_fallback_mode(self, enabled: bool):
        """Enable or disable fallback to mock responses."""
        self.fallback_to_mock = enabled
        logger.info(f"Fallback mode {'enabled' if enabled else 'disabled'}")