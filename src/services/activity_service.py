import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from src.models.weather_models import WeatherData
from src.services.config_service import ConfigService


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

    def __init__(self, config_service: ConfigService):
        self.config = config_service
        self.logger = logging.getLogger(__name__)
        
        # Cache for activity suggestions (30 minutes)
        self._cache = {}
        self._cache_duration = timedelta(minutes=30)
        
        # Initialize Gemini with proper error handling
        self.model = None
        self._initialize_gemini()
        
        # Activity categories mapping
        self.activity_categories = {
            self.OUTDOOR_ADVENTURES: ["hiking", "cycling", "swimming", "running", "climbing", "kayaking"],
            self.INDOOR_ACTIVITIES: ["museums", "shopping", "cooking", "reading", "gaming", "crafts"],
            self.WEATHER_SPECIFIC: ["skiing", "beach", "ice_skating", "sledding", "sunbathing"],
            self.SOCIAL_ACTIVITIES: ["dining", "parties", "concerts", "festivals", "meetups"]
        }
    
    def _initialize_gemini(self) -> None:
        """Initialize Google Gemini with comprehensive error handling."""
        try:
            gemini_key = os.getenv("GEMINI_API_KEY")
            
            if not gemini_key:
                self.logger.warning("GEMINI_API_KEY not found in environment variables")
                return
                
            if not genai:
                self.logger.warning("Google Generative AI library not available. Install with: pip install google-generativeai")
                return
                
            # Configure and test Gemini
            genai.configure(api_key=gemini_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            
            # Test the connection with a simple prompt
            test_response = self.model.generate_content("Hello")
            if test_response and test_response.text:
                self.logger.info("✅ Gemini AI initialized successfully")
            else:
                raise Exception("Invalid response from Gemini")
                
        except Exception as e:
            self.model = None
            self.logger.error(f"❌ Failed to initialize Gemini AI: {e}")
            self.logger.info("🔄 Falling back to rule-based activity suggestions")

    def get_activity_suggestions(self, weather_data: WeatherData, 
                                location_type: str = "urban",
                                duration_filter: Optional[str] = None,
                                equipment_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get intelligent activity suggestions with caching and filtering.
        
        Args:
            weather_data: Current weather conditions
            location_type: 'urban' or 'rural' for location-specific suggestions
            duration_filter: Filter by duration (short/medium/long)
            equipment_filter: Filter by equipment needed (none/basic/advanced)
        """
        # Check cache first
        cache_key = self._generate_cache_key(weather_data, location_type, duration_filter, equipment_filter)
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
        filtered_suggestions = self._apply_filters(suggestions, duration_filter, equipment_filter)
        
        # Cache the results
        self._cache_suggestions(cache_key, filtered_suggestions)
        
        return filtered_suggestions
    
    def _generate_cache_key(self, weather_data: WeatherData, location_type: str, 
                           duration_filter: Optional[str], equipment_filter: Optional[str]) -> str:
        """Generate a cache key for the given parameters."""
        return f"{weather_data.temperature}_{weather_data.description}_{location_type}_{duration_filter}_{equipment_filter}"
    
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
    
    def _get_ai_suggestions(self, weather_data: WeatherData, location_type: str) -> List[Dict[str, Any]]:
        """Get AI-powered suggestions with enhanced prompt engineering."""
        try:
            # Get current time context
            current_hour = datetime.now().hour
            current_month = datetime.now().month
            
            # Determine time of day
            if 6 <= current_hour < 12:
                time_of_day = "morning"
            elif 12 <= current_hour < 17:
                time_of_day = "afternoon"
            elif 17 <= current_hour < 21:
                time_of_day = "evening"
            else:
                time_of_day = "night"
            
            # Determine season
            if current_month in [12, 1, 2]:
                season = "winter"
            elif current_month in [3, 4, 5]:
                season = "spring"
            elif current_month in [6, 7, 8]:
                season = "summer"
            else:
                season = "autumn"
            
            # Create enhanced prompt
            prompt = f"""
You are an expert activity recommendation system. Based on the following comprehensive weather and context data, suggest 6 diverse activities.

🌤️ WEATHER CONDITIONS:
- Temperature: {weather_data.temperature}°C (feels like: {getattr(weather_data, 'feels_like', weather_data.temperature)}°C)
- Weather: {weather_data.description}
- Humidity: {weather_data.humidity}%
- Wind Speed: {weather_data.wind_speed} m/s
- Visibility: {getattr(weather_data, 'visibility', 'Good')}

🕐 TIME CONTEXT:
- Time of day: {time_of_day}
- Season: {season}
- Location type: {location_type}

📋 ACTIVITY CATEGORIES TO CONSIDER:
1. Outdoor Adventures: hiking, cycling, swimming, running, climbing
2. Indoor Activities: museums, shopping, cooking, reading, crafts
3. Weather-Specific: skiing (snow), beach (hot), ice skating (cold)
4. Social Activities: dining, concerts, festivals, meetups

⚡ REQUIREMENTS:
- Provide exactly 6 activities
- Mix of indoor/outdoor based on weather
- Consider safety (avoid outdoor activities in storms)
- Include duration estimates
- Specify equipment needs
- Add appropriate emoji icons
- Consider time of day appropriateness

Format as valid JSON array:
[
  {{
    "title": "Activity Name",
    "category": "outdoor_adventures|indoor_activities|weather_specific|social_activities",
    "subcategory": "Indoor|Outdoor",
    "icon": "🏖️",
    "description": "Engaging description explaining why it's perfect for current conditions",
    "duration": "30 minutes|1-2 hours|3+ hours",
    "equipment": "none|basic|advanced",
    "items": "Specific items needed",
    "safety_notes": "Any safety considerations"
  }}
]
"""

            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Parse and validate response
            suggestions = self._parse_ai_response(response.text)
            
            if suggestions:
                self.logger.info(f"🤖 Generated {len(suggestions)} AI activity suggestions")
                return suggestions
            else:
                self.logger.warning("⚠️ AI response parsing failed, using fallback")
                return self._get_fallback_suggestions(weather_data)
                
        except Exception as e:
            self.logger.error(f"❌ Gemini API error: {e}")
            return self._get_fallback_suggestions(weather_data)
    
    def _parse_ai_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse and validate AI response."""
        try:
            # Find JSON array in response
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            
            if start_idx == -1 or end_idx == 0:
                return []
            
            json_str = response_text[start_idx:end_idx]
            suggestions = json.loads(json_str)
            
            # Validate and clean suggestions
            validated_suggestions = []
            required_fields = ["title", "category", "description", "duration", "items"]
            
            for suggestion in suggestions[:6]:  # Limit to 6
                if all(field in suggestion for field in required_fields):
                    # Add default values for missing optional fields
                    suggestion.setdefault("icon", self._get_default_icon(suggestion.get("category", "")))
                    suggestion.setdefault("subcategory", "Indoor" if "indoor" in suggestion.get("category", "") else "Outdoor")
                    suggestion.setdefault("equipment", "basic")
                    suggestion.setdefault("safety_notes", "Follow standard safety precautions")
                    
                    validated_suggestions.append(suggestion)
            
            return validated_suggestions
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self.logger.warning(f"Failed to parse AI response: {e}")
            return []
    
    def _get_default_icon(self, category: str) -> str:
        """Get default icon based on category."""
        icon_map = {
            "outdoor_adventures": "🏃",
            "indoor_activities": "🏠",
            "weather_specific": "🌤️",
            "social_activities": "👥"
        }
        return icon_map.get(category, "🎯")
    
    def _apply_filters(self, suggestions: List[Dict[str, Any]], 
                      duration_filter: Optional[str], 
                      equipment_filter: Optional[str]) -> List[Dict[str, Any]]:
        """Apply duration and equipment filters to suggestions."""
        filtered = suggestions
        
        # Apply duration filter
        if duration_filter:
            filtered = self._filter_by_duration(filtered, duration_filter)
        
        # Apply equipment filter
        if equipment_filter:
            filtered = self._filter_by_equipment(filtered, equipment_filter)
        
        return filtered
    
    def _filter_by_duration(self, suggestions: List[Dict[str, Any]], duration_filter: str) -> List[Dict[str, Any]]:
        """Filter activities by duration."""
        duration_mapping = {
            self.DURATION_SHORT: ["30 minutes", "1 hour", "30-60 minutes"],
            self.DURATION_MEDIUM: ["1-2 hours", "2-3 hours", "1-3 hours"],
            self.DURATION_LONG: ["3+ hours", "4+ hours", "3-4 hours", "all day"]
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
    
    def _filter_by_equipment(self, suggestions: List[Dict[str, Any]], equipment_filter: str) -> List[Dict[str, Any]]:
        """Filter activities by equipment requirements."""
        if equipment_filter not in [self.EQUIPMENT_NONE, self.EQUIPMENT_BASIC, self.EQUIPMENT_ADVANCED]:
            return suggestions
        
        filtered = []
        for suggestion in suggestions:
            equipment_level = suggestion.get("equipment", "basic").lower()
            items = suggestion.get("items", "").lower()
            
            # Determine equipment level based on items if not explicitly set
            if equipment_level == "basic" and items:
                if any(word in items for word in ["specialized", "professional", "advanced", "expensive"]):
                    equipment_level = "advanced"
                elif any(word in items for word in ["none", "nothing", "no equipment"]):
                    equipment_level = "none"
            
            # Filter based on equipment level
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
            suggestions.extend([
                {
                    "title": "Visit a Museum",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "🏛️",
                    "description": "Explore art, history, or science exhibits while staying dry",
                    "duration": "2-3 hours",
                    "equipment": "none",
                    "items": "Comfortable walking shoes",
                    "safety_notes": "Follow museum guidelines"
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
                    "safety_notes": "Take breaks to rest your eyes"
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
                    "safety_notes": "Handle knives and heat sources carefully"
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
                    "safety_notes": "Keep small pieces away from children"
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
                    "safety_notes": "Use art supplies safely, ensure good ventilation"
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
                    "safety_notes": "Take breaks to stretch and rest eyes"
                }
            ])
        elif temp > 25:  # Warm weather
            suggestions.extend([
                {
                    "title": "Beach Day",
                    "category": self.WEATHER_SPECIFIC,
                    "subcategory": "Outdoor",
                    "icon": "🏖️",
                    "description": "Perfect weather for the beach with sun and sand",
                    "duration": "3-4 hours",
                    "equipment": "basic",
                    "items": "Sunscreen, towel, swimsuit, umbrella",
                    "safety_notes": "Stay hydrated and reapply sunscreen regularly"
                },
                {
                    "title": "Outdoor Picnic",
                    "category": self.SOCIAL_ACTIVITIES,
                    "subcategory": "Outdoor",
                    "icon": "🧺",
                    "description": "Enjoy a meal in the park with perfect weather",
                    "duration": "2-3 hours",
                    "equipment": "basic",
                    "items": "Blanket, food, drinks, cooler",
                    "safety_notes": "Keep food at safe temperatures"
                },
                {
                    "title": "Swimming",
                    "category": self.WEATHER_SPECIFIC,
                    "subcategory": "Outdoor",
                    "icon": "🏊‍♂️",
                    "description": "Cool off in the water on this warm day",
                    "duration": "1-2 hours",
                    "equipment": "basic",
                    "items": "Swimsuit, towel, water bottle",
                    "safety_notes": "Swim in designated areas with lifeguards when possible"
                },
                {
                    "title": "Outdoor Sports",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "⚽",
                    "description": "Great weather for active sports and games",
                    "duration": "1-3 hours",
                    "equipment": "basic",
                    "items": "Sports equipment, water, sunscreen",
                    "safety_notes": "Take frequent water breaks and avoid overheating"
                },
                {
                    "title": "Garden Work",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "🌱",
                    "description": "Perfect conditions for tending to plants and flowers",
                    "duration": "1-2 hours",
                    "equipment": "basic",
                    "items": "Gardening tools, gloves, hat, water",
                    "safety_notes": "Work during cooler parts of the day and stay hydrated"
                },
                {
                    "title": "Ice Cream Tour",
                    "category": self.SOCIAL_ACTIVITIES,
                    "subcategory": "Outdoor",
                    "icon": "🍦",
                    "description": "Cool treats perfect for hot weather",
                    "duration": "1-2 hours",
                    "equipment": "none",
                    "items": "Money, comfortable walking shoes",
                    "safety_notes": "Stay in shaded areas when possible"
                }
            ])
        elif temp > 15:  # Mild weather
            suggestions.extend([
                {
                    "title": "Nature Walk",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "🚶",
                    "description": "Perfect temperature for peaceful walking and nature observation",
                    "duration": "1-2 hours",
                    "equipment": "none",
                    "items": "Comfortable walking shoes, water bottle",
                    "safety_notes": "Stay on marked trails and inform someone of your route"
                },
                {
                    "title": "Cycling Adventure",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "🚴",
                    "description": "Ideal cycling weather for exploration and exercise",
                    "duration": "1-3 hours",
                    "equipment": "advanced",
                    "items": "Bicycle, helmet, water bottle, repair kit",
                    "safety_notes": "Wear helmet, follow traffic rules, check bike before riding"
                },
                {
                    "title": "Photography Walk",
                    "category": self.OUTDOOR_ADVENTURES,
                    "subcategory": "Outdoor",
                    "icon": "📸",
                    "description": "Great lighting and comfortable conditions for capturing beautiful moments",
                    "duration": "2-3 hours",
                    "equipment": "basic",
                    "items": "Camera or smartphone, comfortable shoes, extra battery",
                    "safety_notes": "Be aware of surroundings while focusing on shots"
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
                    "safety_notes": "Keep belongings secure in public spaces"
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
                    "safety_notes": "Stay hydrated and be mindful of other park users"
                },
                {
                    "title": "Farmers Market",
                    "category": self.SOCIAL_ACTIVITIES,
                    "subcategory": "Outdoor",
                    "icon": "🥕",
                    "description": "Browse local produce and crafts in pleasant weather",
                    "duration": "1-2 hours",
                    "equipment": "none",
                    "items": "Reusable bags, money, shopping list",
                    "safety_notes": "Handle fresh produce safely and check payment methods"
                }
            ])
        else:  # Cold weather
            suggestions.extend([
                {
                    "title": "Museum Visit",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "🏛️",
                    "description": "Explore art, history, and culture in a warm, comfortable environment",
                    "duration": "2-3 hours",
                    "equipment": "none",
                    "items": "Comfortable walking shoes, camera (if allowed)",
                    "safety_notes": "Follow museum rules and guidelines"
                },
                {
                    "title": "Coffee Shop Work",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "☕",
                    "description": "Cozy indoor workspace perfect for productivity",
                    "duration": "2-4 hours",
                    "equipment": "basic",
                    "items": "Laptop, notebook, charger, headphones",
                    "safety_notes": "Keep belongings secure and be considerate of other customers"
                },
                {
                    "title": "Shopping Mall",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "🛍️",
                    "description": "Warm indoor shopping and browsing experience",
                    "duration": "2-4 hours",
                    "equipment": "none",
                    "items": "Wallet, shopping list, comfortable shoes",
                    "safety_notes": "Keep track of spending and stay aware of surroundings"
                },
                {
                    "title": "Gym Workout",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "💪",
                    "description": "Stay active and warm with indoor exercise",
                    "duration": "1-2 hours",
                    "equipment": "basic",
                    "items": "Workout clothes, water bottle, towel, gym membership",
                    "safety_notes": "Warm up properly and use equipment safely"
                },
                {
                    "title": "Library Visit",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "📖",
                    "description": "Quiet, warm space for reading, studying, or research",
                    "duration": "2-4 hours",
                    "equipment": "none",
                    "items": "Library card, notebook, pen, laptop (optional)",
                    "safety_notes": "Maintain quiet atmosphere and follow library policies"
                },
                {
                    "title": "Indoor Climbing",
                    "category": self.INDOOR_ACTIVITIES,
                    "subcategory": "Indoor",
                    "icon": "🧗",
                    "description": "Exciting indoor rock climbing to stay active in cold weather",
                    "duration": "2-3 hours",
                    "equipment": "advanced",
                    "items": "Climbing shoes, harness, chalk bag (often rentable)",
                    "safety_notes": "Follow all safety protocols and climb with proper supervision"
                }
            ])
        
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
            "safety_notes": "Take breaks to rest your eyes"
        }
