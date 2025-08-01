"""AI Providers Mixin

Contains all AI service initialization and management methods.
"""

import traceback
from typing import Dict, List

# Import the enhanced AI service
from ....services.ai_service import AIService

# Optional imports for AI services (kept for backward compatibility)
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False


class AIProvidersMixin:
    """Mixin class containing AI provider initialization and management."""

    def _initialize_ai_services(self) -> None:
        """Initialize all AI services."""
        # Enhanced AI service initialization
        self.ai_service = AIService(self.config_service)

        # Legacy AI service initialization (for fallback)
        self.gemini_model = None
        self.openai_client = None

        # Initialize legacy AI services as backup
        self._initialize_gemini()
        self._initialize_openai()

    def _initialize_gemini(self) -> None:
        """Initialize Google Gemini API."""
        if not GENAI_AVAILABLE:
            self.model = None
            self.gemini_available = False
            print("Warning: google-generativeai package not installed")
            return

        try:
            print(f"Debug - ActivitySuggester: About to call config_service.get('gemini_api_key')")
            print(f"Debug - ActivitySuggester: config_service type: {type(self.config_service)}")
            print(
                f"Debug - ActivitySuggester: config_service instance: {getattr(self.config_service, 'instance_id', 'NO_ID')}"
            )
            print(
                f"Debug - ActivitySuggester: config_service has get method: {hasattr(self.config_service, 'get')}"
            )
            try:
                api_key = self.config_service.get("gemini_api_key")
                print(
                    f"Debug - ActivitySuggester: get() call completed, result type: {type(api_key)}"
                )
                print(
                    f"Debug - ActivitySuggester: get() call completed, result value: {repr(api_key)}"
                )
            except Exception as get_ex:
                print(f"Debug - ActivitySuggester: EXCEPTION in get() call: {get_ex}")
                traceback.print_exc()
                api_key = None
            print(
                f"Debug - ActivitySuggester: Gemini API key from config: {'[SET]' if api_key and api_key.strip() else '[EMPTY]'}"
            )
            if api_key and api_key.strip():
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                self.gemini_available = True
                print("✅ Gemini AI initialized successfully")
            else:
                self.gemini_available = False
                self.model = None
                print("⚠️ Gemini API key not found in configuration")
        except Exception as e:
            print(f"❌ Gemini initialization error: {e}")
            self.gemini_available = False
            self.model = None

    def _initialize_openai(self) -> None:
        """Initialize OpenAI API."""
        if not OPENAI_AVAILABLE:
            self.openai_client = None
            self.openai_available = False
            print("Warning: openai package not installed")
            return

        try:
            api_key = self.config_service.get("openai_api_key")
            print(
                f"Debug - ActivitySuggester: OpenAI API key from config: {'[SET]' if api_key and api_key.strip() else '[EMPTY]'}"
            )
            if api_key and api_key.strip():
                self.openai_client = openai.OpenAI(api_key=api_key)
                self.openai_available = True
                print("✅ OpenAI initialized successfully")
            else:
                self.openai_available = False
                self.openai_client = None
                print("⚠️ OpenAI API key not found in configuration")
        except Exception as e:
            print(f"❌ OpenAI initialization error: {e}")
            self.openai_available = False
            self.openai_client = None

    def _get_ai_status_text(self) -> str:
        """Get AI service status text for display."""
        status_parts = []

        # Check enhanced AI service
        if hasattr(self, "ai_service") and self.ai_service:
            status_parts.append("Enhanced AI: ✅")

        # Check legacy services
        if hasattr(self, "gemini_available") and self.gemini_available:
            status_parts.append("Gemini: ✅")

        if hasattr(self, "openai_available") and self.openai_available:
            status_parts.append("OpenAI: ✅")

        if not status_parts:
            return "AI: ❌ No services available"

        return " | ".join(status_parts)

    def _get_ai_suggestions(self, weather_data: Dict, user_preferences: List[Dict]) -> List[Dict]:
        """Get AI-powered activity suggestions."""
        try:
            # Try enhanced AI service first
            if hasattr(self, "ai_service") and self.ai_service:
                return self._get_enhanced_ai_suggestions(weather_data, user_preferences)

            # Fall back to legacy services
            return self._get_legacy_ai_suggestions(weather_data, user_preferences)

        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            traceback.print_exc()
            return self._get_fallback_suggestions()

    def _get_enhanced_ai_suggestions(
        self, weather_data: Dict, user_preferences: List[Dict]
    ) -> List[Dict]:
        """Get suggestions using the enhanced AI service."""
        try:
            # Prepare context for AI
            context = self._prepare_ai_context(weather_data, user_preferences)

            # Get suggestions from enhanced AI service
            response = self.ai_service.get_activity_suggestions(
                weather_data=weather_data, user_preferences=user_preferences, context=context
            )

            if response and "suggestions" in response:
                return response["suggestions"]

            return self._get_fallback_suggestions()

        except Exception as e:
            print(f"Error with enhanced AI service: {e}")
            return self._get_legacy_ai_suggestions(weather_data, user_preferences)

    def _get_legacy_ai_suggestions(
        self, weather_data: Dict, user_preferences: List[Dict]
    ) -> List[Dict]:
        """Get suggestions using legacy AI services."""
        try:
            # Try Gemini first
            if hasattr(self, "gemini_available") and self.gemini_available and self.model:
                return self._get_gemini_suggestions(weather_data, user_preferences)

            # Try OpenAI as fallback
            if hasattr(self, "openai_available") and self.openai_available and self.openai_client:
                return self._get_openai_suggestions(weather_data, user_preferences)

            return self._get_fallback_suggestions()

        except Exception as e:
            print(f"Error with legacy AI services: {e}")
            return self._get_fallback_suggestions()

    def _get_gemini_suggestions(
        self, weather_data: Dict, user_preferences: List[Dict]
    ) -> List[Dict]:
        """Get suggestions using Gemini AI."""
        try:
            prompt = self._create_ai_prompt(weather_data, user_preferences)
            response = self.model.generate_content(prompt)

            if response and response.text:
                return self._parse_ai_response(response.text)

            return self._get_fallback_suggestions()

        except Exception as e:
            print(f"Error with Gemini AI: {e}")
            return self._get_fallback_suggestions()

    def _get_openai_suggestions(
        self, weather_data: Dict, user_preferences: List[Dict]
    ) -> List[Dict]:
        """Get suggestions using OpenAI."""
        try:
            prompt = self._create_ai_prompt(weather_data, user_preferences)

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful activity suggestion assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )

            if response and response.choices and response.choices[0].message.content:
                return self._parse_ai_response(response.choices[0].message.content)

            return self._get_fallback_suggestions()

        except Exception as e:
            print(f"Error with OpenAI: {e}")
            return self._get_fallback_suggestions()

    def _create_ai_prompt(self, weather_data: Dict, user_preferences: List[Dict]) -> str:
        """Create AI prompt for activity suggestions."""
        prompt = f"""
        Based on the current weather conditions and user preferences, suggest 5 activities.
        
        Weather: {weather_data.get('condition', 'Unknown')} 
        Temperature: {weather_data.get('temperature', 'Unknown')}°C
        Humidity: {weather_data.get('humidity', 'Unknown')}%
        Wind: {weather_data.get('wind_speed', 'Unknown')} km/h
        
        User preferences (recent activities): {user_preferences}
        
        Please provide exactly 5 activity suggestions in JSON format:
        [
            {{
                "name": "Activity Name",
                "description": "Brief description",
                "category": "indoor/outdoor/fitness/creative/social",
                "duration": "30-60 minutes",
                "difficulty": "easy/medium/hard",
                "weather_suitability": "Perfect for current conditions"
            }}
        ]
        """
        return prompt.strip()

    def _parse_ai_response(self, response_text: str) -> List[Dict]:
        """Parse AI response into activity suggestions."""
        try:
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                suggestions = json.loads(json_str)

                # Validate and clean suggestions
                valid_suggestions = []
                for suggestion in suggestions:
                    if isinstance(suggestion, dict) and "name" in suggestion:
                        # Ensure all required fields
                        cleaned_suggestion = {
                            "name": suggestion.get("name", "Unknown Activity"),
                            "description": suggestion.get(
                                "description", "No description available"
                            ),
                            "category": suggestion.get("category", "general"),
                            "duration": suggestion.get("duration", "30-60 minutes"),
                            "difficulty": suggestion.get("difficulty", "medium"),
                            "weather_suitability": suggestion.get(
                                "weather_suitability", "Suitable for current conditions"
                            ),
                        }
                        valid_suggestions.append(cleaned_suggestion)

                return valid_suggestions[:5]  # Limit to 5 suggestions

            return self._get_fallback_suggestions()

        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return self._get_fallback_suggestions()

    def _prepare_ai_context(self, weather_data: Dict, user_preferences: List[Dict]) -> Dict:
        """Prepare context for AI service."""
        return {
            "weather_condition": weather_data.get("condition", "Unknown"),
            "temperature": weather_data.get("temperature", 0),
            "humidity": weather_data.get("humidity", 0),
            "wind_speed": weather_data.get("wind_speed", 0),
            "user_history": user_preferences,
            "request_type": "activity_suggestions",
            "max_suggestions": 5,
        }
