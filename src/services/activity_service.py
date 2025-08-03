import json
import logging
import os
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from ..models.weather.current_weather import WeatherData
from .config_service import ConfigService


class ActivityService:
    """Service for AI-powered activity suggestions with intelligent categorization and caching."""

    # Activity categories
    OUTDOOR_ADVENTURES = "outdoor_adventures"
    INDOOR_ACTIVITIES = "indoor_activities"
    WEATHER_SPECIFIC = "weather_specific"
    SOCIAL_ACTIVITIES = "social_activities"

    # Duration filters
    DURATION_SHORT = "short"  # < 1 hour
    DURATION_MEDIUM = "medium"  # 1-3 hours
    DURATION_LONG = "long"  # > 3 hours

    # Equipment levels
    EQUIPMENT_NONE = "none"
    EQUIPMENT_BASIC = "basic"
    EQUIPMENT_ADVANCED = "advanced"

    # Cost levels
    COST_LOW = "$"  # Low cost activities
    COST_MEDIUM = "$$"  # Medium cost activities
    COST_HIGH = "$$$"  # High cost activities

    # Accessibility levels
    ACCESSIBILITY_EASY = "Easy"  # Easy accessibility
    ACCESSIBILITY_MODERATE = "Moderate"  # Moderate accessibility
    ACCESSIBILITY_DIFFICULT = "Difficult"  # Difficult accessibility

    def __init__(self, config_service: ConfigService):
        self.config = config_service
        self.logger = logging.getLogger(__name__)

        # Cache for activity suggestions (1 hour as requested)
        self._cache = {}
        self._cache_duration = timedelta(hours=1)

        # Request retry configuration
        self._max_retries = 3
        self._base_delay = 1.0  # Base delay for exponential backoff
        self._max_delay = 30.0  # Maximum delay between retries

        # API quota tracking
        self._request_count = 0
        self._quota_reset_time = datetime.now() + timedelta(hours=1)
        self._daily_quota_limit = 1000  # Conservative daily limit

        # Initialize Gemini with proper error handling
        self.model = None
        self._gemini_available = False
        self._initialize_gemini()

        # Activity categories mapping
        self.activity_categories = {
            self.OUTDOOR_ADVENTURES: [
                "hiking",
                "cycling",
                "swimming",
                "running",
                "climbing",
                "kayaking",
            ],
            self.INDOOR_ACTIVITIES: [
                "museums",
                "shopping",
                "cooking",
                "reading",
                "gaming",
                "crafts",
            ],
            self.WEATHER_SPECIFIC: ["skiing", "beach", "ice_skating", "sledding", "sunbathing"],
            self.SOCIAL_ACTIVITIES: ["dining", "parties", "concerts", "festivals", "meetups"],
        }

    def _initialize_gemini(self) -> None:
        """Initialize Google Gemini with comprehensive error handling and quota management."""
        try:
            # Try to get API key from config service first, then environment
            gemini_key = self.config.get_api_key("gemini")
            if not gemini_key:
                gemini_key = os.getenv("GEMINI_API_KEY")

            if not gemini_key:
                self.logger.warning(
                    "🔑 GEMINI_API_KEY not found in configuration or environment variables"
                )
                self._gemini_available = False
                return

            if not genai:
                self.logger.warning(
                    "📦 Google Generative AI library not available. Install with: pip install google-generativeai"
                )
                self._gemini_available = False
                return

            # Configure Gemini with safety settings
            genai.configure(api_key=gemini_key)

            # Use gemini-1.5-flash for better performance and lower cost
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }

            self.model = genai.GenerativeModel(
                "gemini-1.5-flash", generation_config=generation_config
            )

            # Test the connection with a simple prompt
            test_response = self._make_api_request_with_retry("Test connection")
            if test_response:
                self.logger.info("✅ Gemini AI successfully initialized and tested")
                self._gemini_available = True
            else:
                self.logger.warning("⚠️ Gemini AI test failed - no response received")
                self._gemini_available = False
                self.model = None

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Gemini AI: {e}")
            self._gemini_available = False
            self.model = None

    def get_activity_suggestions(
        self,
        weather_data: WeatherData,
        location_type: str = "urban",
        duration_filter: Optional[str] = None,
        equipment_filter: Optional[str] = None,
        cost_filter: Optional[str] = None,
        accessibility_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get intelligent activity suggestions with caching and filtering.

        Args:
            weather_data: Current weather conditions
            location_type: 'urban' or 'rural' for location-specific suggestions
            duration_filter: Filter by duration (short/medium/long)
            equipment_filter: Filter by equipment needed (none/basic/advanced)
            cost_filter: Filter by cost level ($, $$, $$$)
            accessibility_filter: Filter by accessibility (Easy, Moderate, Difficult)
        """
        # Check cache first
        cache_key = self._generate_cache_key(
            weather_data,
            location_type,
            duration_filter,
            equipment_filter,
            cost_filter,
            accessibility_filter,
        )
        cached_result = self._get_cached_suggestions(cache_key)
        if cached_result:
            self.logger.info("📋 Returning cached activity suggestions")
            return cached_result

        # Get suggestions from AI or fallback
        if self.model:
            suggestions = self._get_ai_suggestions(weather_data, location_type)
        else:
            suggestions = self._get_fallback_suggestions(weather_data)

        # Apply filters
        filtered_suggestions = self._apply_filters(
            suggestions, duration_filter, equipment_filter, cost_filter, accessibility_filter
        )

        # Cache the results
        self._cache_suggestions(cache_key, filtered_suggestions)

        return filtered_suggestions

    def _generate_cache_key(
        self,
        weather_data: WeatherData,
        location_type: str,
        duration_filter: Optional[str],
        equipment_filter: Optional[str],
        cost_filter: Optional[str] = None,
        accessibility_filter: Optional[str] = None,
    ) -> str:
        """Generate a cache key for the given parameters."""
        return f"{weather_data.temperature}_{weather_data.description}_{location_type}_{duration_filter}_{equipment_filter}_{cost_filter}_{accessibility_filter}"

    def _get_cached_suggestions(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached suggestions if they exist and are not expired."""
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_duration:
                return cached_data
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        return None

    def _cache_suggestions(self, cache_key: str, suggestions: List[Dict[str, Any]]) -> None:
        """Cache the suggestions with timestamp."""
        self._cache[cache_key] = (suggestions, datetime.now())
        # Clean old cache entries (keep only last 10)
        if len(self._cache) > 10:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

    def _make_api_request_with_retry(self, prompt: str) -> Optional[str]:
        """Make API request with exponential backoff retry logic."""
        if not self._gemini_available or not self.model:
            return None

        # Check quota limits
        if self._request_count >= self._daily_quota_limit:
            if datetime.now() < self._quota_reset_time:
                self.logger.warning("🚫 Daily API quota limit reached. Using fallback suggestions.")
                return None
            else:
                # Reset quota counter
                self._request_count = 0
                self._quota_reset_time = datetime.now() + timedelta(hours=24)

        for attempt in range(self._max_retries):
            try:
                self._request_count += 1
                response = self.model.generate_content(prompt)

                if response and response.text:
                    return response.text
                else:
                    self.logger.warning(f"Empty response from Gemini AI (attempt {attempt + 1})")

            except Exception as e:
                self.logger.warning(f"API request failed (attempt {attempt + 1}): {e}")

                if attempt < self._max_retries - 1:
                    # Exponential backoff with jitter
                    delay = min(self._base_delay * (2**attempt), self._max_delay)
                    jitter = random.uniform(0, 0.1) * delay
                    time.sleep(delay + jitter)

        self.logger.error("All API retry attempts failed")
        return None

    def _get_ai_suggestions(
        self, weather_data: WeatherData, location_type: str
    ) -> List[Dict[str, Any]]:
        """Get AI-powered suggestions with enhanced prompt engineering and location context."""
        if not self._gemini_available:
            return self._get_fallback_suggestions(weather_data)

        try:
            # Get current time context
            current_hour = datetime.now().hour
            current_month = datetime.now().month

            # Determine time of day with context
            if 6 <= current_hour < 12:
                time_of_day = "morning"
                time_context = "Start your day with energizing activities"
            elif 12 <= current_hour < 17:
                time_of_day = "afternoon"
                time_context = (
                    "Perfect time for outdoor exploration or productive indoor activities"
                )
            elif 17 <= current_hour < 21:
                time_of_day = "evening"
                time_context = "Wind down with relaxing or social activities"
            else:
                time_of_day = "night"
                time_context = "Focus on indoor, quiet, or evening entertainment activities"

            # Determine season with characteristics
            if current_month in [12, 1, 2]:
                season = "winter"
                season_context = "Cold weather activities, indoor alternatives, winter sports"
            elif current_month in [3, 4, 5]:
                season = "spring"
                season_context = "Mild weather, blooming nature, outdoor renewal activities"
            elif current_month in [6, 7, 8]:
                season = "summer"
                season_context = "Warm weather, water activities, extended daylight hours"
            else:
                season = "autumn"
                season_context = "Cool crisp air, fall colors, harvest activities"

            # Weather safety assessment
            safety_concerns = []
            if weather_data.temperature < 0:
                safety_concerns.append(
                    "freezing temperatures - recommend warm clothing and indoor alternatives"
                )
            elif weather_data.temperature > 30:
                safety_concerns.append("high temperatures - emphasize hydration and shade")
            if weather_data.wind_speed > 25:
                safety_concerns.append("strong winds - avoid outdoor activities with loose objects")
            if weather_data.humidity > 80:
                safety_concerns.append("high humidity - recommend air-conditioned spaces")
            if "rain" in weather_data.description.lower():
                safety_concerns.append("wet conditions - prioritize indoor activities")
            if "snow" in weather_data.description.lower():
                safety_concerns.append(
                    "snowy conditions - winter gear required for outdoor activities"
                )

            safety_context = (
                "\n- Safety considerations: " + "; ".join(safety_concerns)
                if safety_concerns
                else ""
            )

            # Create comprehensive prompt
            prompt = f"""
You are an expert local activity planner with deep knowledge of weather-appropriate activities. Based on the current conditions, suggest 6 diverse, engaging activities that are perfectly suited for the weather and time.

Current Weather Context:
- Temperature: {weather_data.temperature}°C (feels like: {getattr(weather_data, 'feels_like', weather_data.temperature)}°C)
- Weather: {weather_data.description}
- Humidity: {weather_data.humidity}%
- Wind Speed: {weather_data.wind_speed} m/s
- Visibility: {getattr(weather_data, 'visibility', 'Good')}
- Location type: {location_type}
- Time: {time_of_day} ({time_context})
- Season: {season} ({season_context}){safety_context}

Activity Categories (include variety):
🏞️ Outdoor Adventures: hiking, cycling, photography, sports, nature walks, outdoor dining
🏠 Indoor Activities: museums, galleries, shopping, cooking, crafts, reading, gaming
👥 Social Activities: dining, events, gatherings, classes, community activities
💪 Fitness Activities: gym workouts, yoga, running, swimming, sports, dance

Requirements:
- Provide exactly 6 activities with strategic indoor/outdoor balance based on weather
- Prioritize weather-appropriate and time-suitable activities
- Include specific local considerations when possible
- Vary duration (30min to 4+ hours) and equipment needs
- Consider accessibility and cost factors
- Add weather-specific safety notes
- Use relevant emoji icons

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "title": "Specific Activity Name",
    "category": "outdoor_adventures|indoor_activities|weather_specific|social_activities",
    "subcategory": "Indoor|Outdoor",
    "icon": "🌟",
    "description": "Detailed description explaining why this activity suits current weather and time",
    "duration": "30 minutes|1-2 hours|3+ hours",
    "equipment": "none|basic|advanced",
    "items": "Specific list of required items/preparation",
    "safety_notes": "Weather-specific safety considerations and tips"
  }}
]
"""

            # Make API request with retry logic
            response_text = self._make_api_request_with_retry(prompt)
            if response_text:
                suggestions = self._parse_ai_response(response_text)
                if suggestions:
                    self.logger.info(f"🤖 Generated {len(suggestions)} AI activity suggestions")
                    return suggestions
                else:
                    self.logger.warning("⚠️ AI response parsing failed, using fallback")
                    return self._get_fallback_suggestions(weather_data)
            else:
                self.logger.warning("Failed to get AI response, using fallback")
                return self._get_fallback_suggestions(weather_data)

        except Exception as e:
            self.logger.error(f"❌ Error getting AI suggestions: {e}")
            return self._get_fallback_suggestions(weather_data)

    def _parse_ai_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse and validate AI response with comprehensive error handling and enhanced validation."""
        try:
            # Clean response text and extract JSON
            cleaned_text = response_text.strip()

            # Handle markdown code blocks
            if "```json" in cleaned_text:
                json_start = cleaned_text.find("```json") + 7
                json_end = cleaned_text.find("```", json_start)
                if json_end != -1:
                    cleaned_text = cleaned_text[json_start:json_end].strip()
            elif "```" in cleaned_text:
                json_start = cleaned_text.find("```") + 3
                json_end = cleaned_text.find("```", json_start)
                if json_end != -1:
                    cleaned_text = cleaned_text[json_start:json_end].strip()

            # Find JSON array boundaries
            start_idx = cleaned_text.find("[")
            end_idx = cleaned_text.rfind("]") + 1

            if start_idx == -1 or end_idx == 0:
                self.logger.warning("No JSON array found in AI response")
                return []

            json_str = cleaned_text[start_idx:end_idx]
            suggestions = json.loads(json_str)

            # Validate structure
            if not isinstance(suggestions, list):
                self.logger.warning("AI response is not a list")
                return []

            # Validate and clean suggestions
            validated_suggestions = []
            required_fields = ["title", "category", "description", "duration", "items"]
            valid_categories = {
                "outdoor_adventures",
                "indoor_activities",
                "social_activities",
                "weather_specific",
            }
            valid_subcategories = {"Outdoor", "Indoor", "Social"}
            valid_equipment = {"none", "basic", "advanced"}

            for suggestion in suggestions[:6]:  # Limit to 6
                if not isinstance(suggestion, dict):
                    continue

                if all(field in suggestion for field in required_fields):
                    # Validate and normalize category
                    category = suggestion.get("category", "")
                    if category not in valid_categories:
                        # Try to map common variations
                        category_lower = category.lower()
                        if "outdoor" in category_lower or "adventure" in category_lower:
                            suggestion["category"] = "outdoor_adventures"
                        elif "indoor" in category_lower:
                            suggestion["category"] = "indoor_activities"
                        elif "social" in category_lower:
                            suggestion["category"] = "social_activities"
                        elif "weather" in category_lower:
                            suggestion["category"] = "weather_specific"
                        else:
                            suggestion["category"] = "indoor_activities"  # Default fallback

                    # Add default values for missing optional fields
                    suggestion.setdefault(
                        "icon", self._get_default_icon(suggestion.get("category", ""))
                    )

                    subcategory = suggestion.get("subcategory", "")
                    if subcategory not in valid_subcategories:
                        # Auto-determine subcategory from category
                        if "outdoor" in suggestion["category"]:
                            suggestion["subcategory"] = "Outdoor"
                        elif "social" in suggestion["category"]:
                            suggestion["subcategory"] = "Social"
                        else:
                            suggestion["subcategory"] = "Indoor"

                    equipment = suggestion.get("equipment", "basic")
                    if equipment not in valid_equipment:
                        suggestion["equipment"] = "basic"  # Default to basic if invalid

                    # Add cost and accessibility fields with defaults
                    suggestion.setdefault("cost", "$")
                    suggestion.setdefault("accessibility", "Easy")
                    suggestion.setdefault("safety_notes", "Follow standard safety precautions")

                    validated_suggestions.append(suggestion)

            self.logger.info(
                f"✅ Successfully parsed {len(validated_suggestions)} activity suggestions"
            )
            return validated_suggestions

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self.logger.warning(f"Failed to parse AI response: {e}")
            self.logger.debug(f"Failed to parse response: {response_text[:200]}...")
            return []

    def _get_default_icon(self, category: str) -> str:
        """Get default icon based on category."""
        icon_map = {
            "outdoor_adventures": "🏃",
            "indoor_activities": "🏠",
            "weather_specific": "🌤️",
            "social_activities": "👥",
        }
        return icon_map.get(category, "🎯")

    def _apply_filters(
        self,
        suggestions: List[Dict[str, Any]],
        duration_filter: Optional[str],
        equipment_filter: Optional[str],
        cost_filter: Optional[str] = None,
        accessibility_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Apply duration, equipment, cost, and accessibility filters to suggestions."""
        filtered = suggestions

        # Apply duration filter
        if duration_filter:
            filtered = self._filter_by_duration(filtered, duration_filter)

        # Apply equipment filter
        if equipment_filter:
            filtered = self._filter_by_equipment(filtered, equipment_filter)

        # Apply cost filter
        if cost_filter:
            filtered = self._filter_by_cost(filtered, cost_filter)

        # Apply accessibility filter
        if accessibility_filter:
            filtered = self._filter_by_accessibility(filtered, accessibility_filter)

        return filtered

    def _filter_by_duration(
        self, suggestions: List[Dict[str, Any]], duration_filter: str
    ) -> List[Dict[str, Any]]:
        """Filter activities by duration with enhanced matching."""
        duration_mapping = {
            self.DURATION_SHORT: ["30 minutes", "1 hour", "30-60 minutes", "1-2 hours"],
            self.DURATION_MEDIUM: ["1-2 hours", "2-3 hours", "1-3 hours", "2-4 hours"],
            self.DURATION_LONG: [
                "3+ hours",
                "4+ hours",
                "3-4 hours",
                "3-6 hours",
                "4-6 hours",
                "all day",
            ],
        }

        if duration_filter not in duration_mapping:
            return suggestions

        target_durations = duration_mapping[duration_filter]

        filtered = []
        for suggestion in suggestions:
            duration = suggestion.get("duration", suggestion.get("time", "")).lower()
            if any(target in duration for target in target_durations):
                filtered.append(suggestion)

        return filtered if filtered else suggestions  # Return all if no matches

    def _filter_by_cost(
        self, suggestions: List[Dict[str, Any]], cost_filter: str
    ) -> List[Dict[str, Any]]:
        """Filter activities by cost level."""
        if cost_filter not in ["$", "$$", "$$$"]:
            return suggestions

        filtered = []
        for suggestion in suggestions:
            cost = suggestion.get("cost", "$")

            # Filter based on cost level
            if cost_filter == "$" and cost == "$":
                filtered.append(suggestion)
            elif cost_filter == "$$" and cost in ["$", "$$"]:
                filtered.append(suggestion)
            elif cost_filter == "$$$":
                filtered.append(suggestion)  # Include all for highest cost filter

        return filtered if filtered else suggestions  # Return all if no matches

    def _filter_by_accessibility(
        self, suggestions: List[Dict[str, Any]], accessibility_filter: str
    ) -> List[Dict[str, Any]]:
        """Filter activities by accessibility level."""
        if accessibility_filter not in ["Easy", "Moderate", "Difficult"]:
            return suggestions

        filtered = []
        for suggestion in suggestions:
            accessibility = suggestion.get("accessibility", "Easy")

            # Filter based on accessibility level
            if accessibility_filter == "Easy" and accessibility == "Easy":
                filtered.append(suggestion)
            elif accessibility_filter == "Moderate" and accessibility in ["Easy", "Moderate"]:
                filtered.append(suggestion)
            elif accessibility_filter == "Difficult":
                filtered.append(suggestion)  # Include all for highest difficulty filter

        return filtered if filtered else suggestions  # Return all if no matches

    def _filter_by_equipment(
        self, suggestions: List[Dict[str, Any]], equipment_filter: str
    ) -> List[Dict[str, Any]]:
        """Filter activities by equipment requirements with enhanced matching."""
        if equipment_filter not in [
            self.EQUIPMENT_NONE,
            self.EQUIPMENT_BASIC,
            self.EQUIPMENT_ADVANCED,
        ]:
            return suggestions

        filtered = []
        for suggestion in suggestions:
            equipment_level = suggestion.get("equipment", "basic").lower()
            items = suggestion.get("items", "").lower()
            suggestion.get("cost", "$")
            suggestion.get("accessibility", "Easy")

            # Determine equipment level based on items if not explicitly set
            if equipment_level == "basic" and items:
                if any(
                    word in items
                    for word in ["specialized", "professional", "advanced", "expensive"]
                ):
                    equipment_level = "advanced"
                elif any(word in items for word in ["none", "nothing", "no equipment"]):
                    equipment_level = "none"

            # Filter based on equipment level with cost and accessibility consideration
            if equipment_filter == self.EQUIPMENT_NONE and equipment_level == "none":
                filtered.append(suggestion)
            elif equipment_filter == self.EQUIPMENT_BASIC and equipment_level in ["none", "basic"]:
                filtered.append(suggestion)
            elif equipment_filter == self.EQUIPMENT_ADVANCED:
                filtered.append(suggestion)  # Include all for advanced filter

        return filtered if filtered else suggestions  # Return all if no matches

    def _get_fallback_suggestions(self, weather_data: WeatherData) -> List[Dict[str, Any]]:
        """Enhanced fallback suggestions when AI is not available."""
        temp = weather_data.temperature
        condition = weather_data.description.lower()

        suggestions = []

        # Weather-based activity suggestions with enhanced format
        if "rain" in condition or "storm" in condition:
            suggestions.extend(
                [
                    {
                        "title": "Visit a Museum",
                        "category": self.INDOOR_ACTIVITIES,
                        "subcategory": "Indoor",
                        "icon": "🏛️",
                        "description": "Explore art, history, or science exhibits while staying dry",
                        "duration": "2-3 hours",
                        "equipment": "none",
                        "items": "Comfortable walking shoes",
                        "safety_notes": "Follow museum guidelines",
                        "cost": "$$",
                        "accessibility": "Easy",
                    },
                    {
                        "title": "Indoor Reading",
                        "category": self.INDOOR_ACTIVITIES,
                        "subcategory": "Indoor",
                        "icon": "📚",
                        "description": "Perfect rainy day for a good book",
                        "duration": "1-3 hours",
                        "equipment": "none",
                        "items": "Book, comfortable chair, hot drink",
                        "safety_notes": "Take breaks to rest your eyes",
                        "cost": "$",
                        "accessibility": "Easy",
                    },
                    {
                        "title": "Cooking Project",
                        "category": self.INDOOR_ACTIVITIES,
                        "subcategory": "Indoor",
                        "icon": "👨‍🍳",
                        "description": "Try a new recipe and learn culinary skills",
                        "duration": "1-2 hours",
                        "equipment": "basic",
                        "items": "Ingredients, cooking utensils",
                        "safety_notes": "Handle knives and heat sources carefully",
                        "cost": "$",
                        "accessibility": "Easy",
                    },
                    {
                        "title": "Board Games",
                        "category": self.SOCIAL_ACTIVITIES,
                        "subcategory": "Indoor",
                        "icon": "🎲",
                        "description": "Fun indoor games with family and friends",
                        "duration": "1-3 hours",
                        "equipment": "none",
                        "items": "Board games, friends/family",
                        "safety_notes": "Keep small pieces away from children",
                        "cost": "$",
                        "accessibility": "Easy",
                    },
                    {
                        "title": "Art & Crafts",
                        "category": self.INDOOR_ACTIVITIES,
                        "subcategory": "Indoor",
                        "icon": "🎨",
                        "description": "Creative indoor activity for all ages",
                        "duration": "2-4 hours",
                        "equipment": "basic",
                        "items": "Art supplies, workspace",
                        "safety_notes": "Use art supplies safely, ensure good ventilation",
                        "cost": "$",
                        "accessibility": "Easy",
                    },
                    {
                        "title": "Movie Marathon",
                        "category": self.INDOOR_ACTIVITIES,
                        "subcategory": "Indoor",
                        "icon": "🎬",
                        "description": "Cozy indoor entertainment",
                        "duration": "3+ hours",
                        "equipment": "none",
                        "items": "Streaming service, snacks, blanket",
                        "safety_notes": "Take breaks to stretch and rest eyes",
                        "cost": "$",
                        "accessibility": "Easy",
                    },
                ]
            )
        elif temp > 25:  # Warm weather
            outdoor_warm = [
                {
                    "title": "Beach & Water Sports",
                    "category": self.WEATHER_SPECIFIC,
                    "subcategory": "Outdoor",
                    "icon": "🏖️",
                    "description": "Perfect beach day with swimming, volleyball, and sun bathing in ideal conditions",
                    "duration": "3-6 hours",
                    "equipment": "basic",
                    "items": "Sunscreen SPF 30+, beach towel, water bottle, swimwear, beach umbrella",
                    "safety_notes": "Apply sunscreen every 2 hours, stay hydrated, and check water conditions",
                    "cost": "$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Outdoor Picnic Adventure",
                    "category": self.SOCIAL_ACTIVITIES,
                    "subcategory": "Outdoor",
                    "icon": "🧺",
                    "description": "Enjoy a delightful meal outdoors with friends or family in beautiful weather",
                    "duration": "2-4 hours",
                    "equipment": "basic",
                    "items": "Picnic basket, waterproof blanket, food, drinks, cooler with ice",
                    "safety_notes": "Keep perishable food cold, bring hand sanitizer, and clean up thoroughly",
                    "cost": "$$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Swimming & Water Activities",
                    "category": self.WEATHER_SPECIFIC,
                    "subcategory": "Outdoor",
                    "icon": "🏊‍♂️",
                    "description": "Cool off with swimming, water sports, or poolside relaxation",
                    "duration": "1-3 hours",
                    "equipment": "basic",
                    "items": "Swimsuit, towel, water bottle, goggles, sunscreen",
                    "safety_notes": "Swim in designated areas with lifeguards when possible, never swim alone",
                    "cost": "$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Outdoor Sports & Games",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "⚽",
                    "description": "Perfect weather for tennis, basketball, frisbee, or team sports",
                    "duration": "1-3 hours",
                    "equipment": "basic",
                    "items": "Sports equipment, water bottle, sunscreen, athletic wear",
                    "safety_notes": "Take frequent water breaks, avoid peak sun hours, and warm up properly",
                    "cost": "$",
                    "accessibility": "Moderate",
                },
                {
                    "title": "Photography Walk",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "📸",
                    "description": "Capture beautiful moments and scenery in perfect lighting conditions",
                    "duration": "1-3 hours",
                    "equipment": "basic",
                    "items": "Camera or smartphone, extra batteries, comfortable walking shoes",
                    "safety_notes": "Be aware of surroundings, respect private property, and protect equipment",
                    "cost": "$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Ice Cream & Treats Tour",
                    "category": self.SOCIAL_ACTIVITIES,
                    "subcategory": "Outdoor",
                    "icon": "🍦",
                    "description": "Cool treats and refreshments perfect for hot weather exploration",
                    "duration": "1-2 hours",
                    "equipment": "none",
                    "items": "Money, comfortable walking shoes, hat",
                    "safety_notes": "Stay in shaded areas when possible and stay hydrated",
                    "cost": "$",
                    "accessibility": "Easy",
                },
            ]
            suggestions.extend(outdoor_warm)
        elif temp > 15:  # Mild weather
            outdoor_mild = [
                {
                    "title": "Nature Trail Hiking",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "🥾",
                    "description": "Explore scenic trails and enjoy fresh air in comfortable temperatures",
                    "duration": "1-3 hours",
                    "equipment": "basic",
                    "items": "Hiking shoes, water bottle, trail map, light jacket, snacks",
                    "safety_notes": "Stay on marked trails, inform someone of your route, and check weather updates",
                    "cost": "$",
                    "accessibility": "Moderate",
                },
                {
                    "title": "Cycling Adventure",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "🚴‍♂️",
                    "description": "Perfect temperature for road cycling or mountain biking",
                    "duration": "1-4 hours",
                    "equipment": "advanced",
                    "items": "Bicycle, helmet, water bottle, repair kit, cycling clothes",
                    "safety_notes": "Always wear a helmet, follow traffic rules, and check bike condition",
                    "cost": "$",
                    "accessibility": "Moderate",
                },
                {
                    "title": "Farmers Market Tour",
                    "category": self.SOCIAL_ACTIVITIES,
                    "subcategory": "Outdoor",
                    "icon": "🛒",
                    "description": "Browse local markets, meet vendors, and discover fresh produce",
                    "duration": "2-3 hours",
                    "equipment": "none",
                    "items": "Money, reusable bags, comfortable walking shoes, market list",
                    "safety_notes": "Keep valuables secure, stay aware of surroundings, and handle food safely",
                    "cost": "$$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Outdoor Photography",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "📷",
                    "description": "Capture landscapes, wildlife, and street scenes in ideal lighting",
                    "duration": "2-4 hours",
                    "equipment": "basic",
                    "items": "Camera, extra batteries, memory cards, tripod, lens cloth",
                    "safety_notes": "Protect equipment from moisture, respect wildlife, and be mindful of private property",
                    "cost": "$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Outdoor Café",
                    "category": self.SOCIAL_ACTIVITIES,
                    "subcategory": "Outdoor",
                    "icon": "☕",
                    "description": "Perfect weather for enjoying coffee and socializing outside",
                    "duration": "1-2 hours",
                    "equipment": "none",
                    "items": "Light jacket (optional), book or laptop",
                    "safety_notes": "Keep belongings secure in public spaces",
                    "cost": "$$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Park Activities",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "🌳",
                    "description": "Enjoy various park facilities and outdoor games",
                    "duration": "1-3 hours",
                    "equipment": "basic",
                    "items": "Blanket, snacks, frisbee or ball",
                    "safety_notes": "Stay hydrated and be mindful of other park users",
                    "cost": "$",
                    "accessibility": "Easy",
                },
            ]
            suggestions.extend(outdoor_mild)
        else:  # Cold weather (15°C and below)
            cold_weather = [
                {
                    "title": "Museum & Cultural Center",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "🏛️",
                    "description": "Stay warm while exploring art, history, and cultural exhibitions",
                    "duration": "2-4 hours",
                    "equipment": "none",
                    "items": "Warm layers, comfortable walking shoes, museum map, camera",
                    "safety_notes": "Dress in layers for temperature changes, wear comfortable shoes for walking",
                    "cost": "$$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Indoor Fitness Center",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "💪",
                    "description": "Stay active and warm with comprehensive indoor workout facilities",
                    "duration": "1-2 hours",
                    "equipment": "basic",
                    "items": "Workout clothes, water bottle, towel, gym membership or day pass",
                    "safety_notes": "Warm up properly in cold weather, stay hydrated, and cool down gradually",
                    "cost": "$$",
                    "accessibility": "Moderate",
                },
                {
                    "title": "Cozy Café Hopping",
                    "category": self.SOCIAL_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "☕",
                    "description": "Warm up with hot beverages, pastries, and cozy atmosphere",
                    "duration": "2-3 hours",
                    "equipment": "none",
                    "items": "Warm coat, scarf, money, book or laptop, comfortable shoes",
                    "safety_notes": "Dress warmly for travel between locations, check opening hours",
                    "cost": "$$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Indoor Shopping Mall",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "🛍️",
                    "description": "Browse shops, enjoy food courts, and stay warm in climate-controlled environment",
                    "duration": "2-4 hours",
                    "equipment": "none",
                    "items": "Wallet, shopping list, comfortable shoes, reusable bags",
                    "safety_notes": "Keep track of spending, stay aware of surroundings, take breaks",
                    "cost": "$$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Library & Study Session",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "📚",
                    "description": "Enjoy quiet reading, research, or study in a warm, peaceful environment",
                    "duration": "1-4 hours",
                    "equipment": "none",
                    "items": "Library card, notebook, laptop, reading materials, warm clothes",
                    "safety_notes": "Follow library rules, take breaks to rest eyes, stay quiet",
                    "cost": "$",
                    "accessibility": "Easy",
                },
                {
                    "title": "Indoor Rock Climbing",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "🧗",
                    "description": "Exciting indoor rock climbing to stay active and warm in cold weather",
                    "duration": "2-3 hours",
                    "equipment": "advanced",
                    "items": "Climbing shoes, harness, chalk bag (often rentable), warm clothes for travel",
                    "safety_notes": "Follow all safety protocols, climb with proper supervision, dress warmly for travel",
                    "cost": "$$",
                    "accessibility": "Moderate",
                },
            ]
            suggestions.extend(cold_weather)

        return suggestions

    def get_activity_by_category(
        self, weather_data: WeatherData, category: str
    ) -> List[Dict[str, Any]]:
        """Get activities filtered by category."""
        all_suggestions = self.get_activity_suggestions(weather_data)
        return [
            activity
            for activity in all_suggestions
            if activity.get("category", "").lower() == category.lower()
        ]

    def get_quick_activity(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Get a single quick activity suggestion."""
        suggestions = self.get_activity_suggestions(weather_data)
        if suggestions:
            # Return the first suggestion or a random one
            import random

            return random.choice(suggestions)

        return {
            "title": "Indoor Reading",
            "category": self.INDOOR_ACTIVITIES,
            "subcategory": "Indoor",
            "icon": "📚",
            "description": "A good book is always a great activity",
            "duration": "1+ hours",
            "equipment": "none",
            "items": "Book, comfortable chair",
            "safety_notes": "Take breaks to rest your eyes",
        }
