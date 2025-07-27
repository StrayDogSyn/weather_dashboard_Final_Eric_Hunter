"""Clean Gemini AI service with proper authentication."""

import logging
from typing import Optional, Dict, Any

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None

from config.settings import get_settings


class GeminiError(Exception):
    """Custom exception for Gemini service errors."""
    pass


class GeminiService:
    """Clean Gemini AI service for weather insights."""
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """Initialize Gemini service with proper authentication."""
        if not self.is_available():
            logging.warning("Gemini service not available - missing API key or library")
            return
        
        try:
            # Configure the API key
            genai.configure(api_key=self.settings.gemini_api_key)
            
            # Initialize the model with safety settings
            self.model = genai.GenerativeModel(
                model_name="gemini-pro",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            )
            
            logging.info("Gemini service initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize Gemini service: {e}")
            self.model = None
            raise GeminiError(f"Gemini initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Gemini service is available."""
        return (
            genai is not None and 
            self.settings.has_gemini and 
            bool(self.settings.gemini_api_key)
        )
    
    def is_ready(self) -> bool:
        """Check if service is ready for use."""
        return self.is_available() and self.model is not None
    
    def generate_weather_insight(self, weather_data: Dict[str, Any]) -> Optional[str]:
        """Generate weather insights from weather data.
        
        Args:
            weather_data: Dictionary containing weather information
            
        Returns:
            Generated insight text or None if service unavailable
        """
        if not self.is_ready():
            logging.warning("Gemini service not ready for weather insights")
            return None
        
        try:
            # Create a focused prompt for weather insights
            prompt = self._create_weather_prompt(weather_data)
            
            # Generate content
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text.strip()
            else:
                logging.warning("Gemini returned empty response for weather insight")
                return None
                
        except Exception as e:
            logging.error(f"Failed to generate weather insight: {e}")
            raise GeminiError(f"Weather insight generation failed: {e}")
    
    def answer_weather_question(self, question: str, weather_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Answer weather-related questions.
        
        Args:
            question: User's weather question
            weather_data: Optional current weather data for context
            
        Returns:
            Answer text or None if service unavailable
        """
        if not self.is_ready():
            logging.warning("Gemini service not ready for questions")
            return None
        
        try:
            # Create a focused prompt for weather Q&A
            prompt = self._create_question_prompt(question, weather_data)
            
            # Generate content
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text.strip()
            else:
                logging.warning("Gemini returned empty response for weather question")
                return None
                
        except Exception as e:
            logging.error(f"Failed to answer weather question: {e}")
            raise GeminiError(f"Weather question answering failed: {e}")
    
    def _create_weather_prompt(self, weather_data: Dict[str, Any]) -> str:
        """Create a focused prompt for weather insights."""
        location = weather_data.get('location', 'Unknown')
        temp = weather_data.get('temperature', 0)
        feels_like = weather_data.get('feels_like', temp)
        humidity = weather_data.get('humidity', 0)
        description = weather_data.get('description', 'Unknown')
        wind_speed = weather_data.get('wind_speed', 0)
        
        return f"""You are a helpful weather assistant. Provide a brief, practical insight about the current weather conditions.

Current weather in {location}:
- Temperature: {temp}°C (feels like {feels_like}°C)
- Conditions: {description}
- Humidity: {humidity}%
- Wind Speed: {wind_speed} m/s

Provide a 2-3 sentence insight about:
1. How the weather feels and what to expect
2. Practical clothing or activity recommendations

Keep it conversational and helpful."""
    
    def _create_question_prompt(self, question: str, weather_data: Optional[Dict[str, Any]]) -> str:
        """Create a focused prompt for weather questions."""
        context = ""
        if weather_data:
            location = weather_data.get('location', 'Unknown')
            temp = weather_data.get('temperature', 0)
            description = weather_data.get('description', 'Unknown')
            context = f"\n\nCurrent weather context in {location}: {temp}°C, {description}"
        
        return f"""You are a helpful weather assistant. Answer the following weather-related question clearly and concisely.

Question: {question}{context}

Provide a helpful, accurate answer in 2-3 sentences. Focus on practical information."""
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            'available': self.is_available(),
            'ready': self.is_ready(),
            'has_api_key': bool(self.settings.gemini_api_key),
            'library_installed': genai is not None
        }