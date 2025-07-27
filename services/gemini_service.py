"""Gemini AI service for conversational features."""

import logging
from typing import Optional, List, Dict, Any

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from config.settings import settings


class GeminiServiceError(Exception):
    """Custom exception for Gemini AI service errors."""
    pass


class GeminiService:
    """Google Gemini AI service for weather-related conversations."""
    
    def __init__(self):
        if not genai:
            raise GeminiServiceError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )
        
        if not settings.gemini_api_key:
            raise GeminiServiceError(
                "GEMINI_API_KEY not configured. "
                "Please set it in your .env file."
            )
        
        # Configure Gemini AI
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # System prompt for weather-focused conversations
        self.system_prompt = (
            "You are a helpful weather assistant. Provide concise, "
            "accurate information about weather conditions, forecasts, "
            "and weather-related activities. Keep responses under 200 words."
        )
    
    def generate_weather_insight(self, weather_data: Dict[str, Any]) -> str:
        """Generate weather insights based on current conditions."""
        prompt = f"""
        {self.system_prompt}
        
        Current weather conditions:
        - Location: {weather_data.get('location', 'Unknown')}
        - Temperature: {weather_data.get('temperature', 'N/A')}°C
        - Description: {weather_data.get('description', 'N/A')}
        - Humidity: {weather_data.get('humidity', 'N/A')}%
        
        Provide a brief, helpful insight about these conditions and 
        suggest appropriate activities or clothing recommendations.
        """
        
        return self._generate_response(prompt)
    
    def answer_weather_question(self, question: str, 
                              context_data: Optional[Dict[str, Any]] = None) -> str:
        """Answer weather-related questions with optional context."""
        context_info = ""
        if context_data:
            context_info = f"""
            Current weather context:
            - Location: {context_data.get('location', 'Unknown')}
            - Temperature: {context_data.get('temperature', 'N/A')}°C
            - Conditions: {context_data.get('description', 'N/A')}
            """
        
        prompt = f"""
        {self.system_prompt}
        {context_info}
        
        User question: {question}
        
        Please provide a helpful, accurate answer.
        """
        
        return self._generate_response(prompt)
    
    def _generate_response(self, prompt: str) -> str:
        """Generate response using Gemini AI."""
        try:
            response = self.model.generate_content(prompt)
            
            if not response.text:
                return "I'm sorry, I couldn't generate a response. Please try again."
            
            return response.text.strip()
            
        except Exception as e:
            logging.error(f"Gemini AI error: {e}")
            raise GeminiServiceError(f"Failed to generate response: {e}")
    
    def is_available(self) -> bool:
        """Check if Gemini service is properly configured and available."""
        return bool(genai and settings.gemini_api_key)