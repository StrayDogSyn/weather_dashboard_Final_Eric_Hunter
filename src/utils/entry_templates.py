from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.safe_math import safe_divide


@dataclass
class EntryTemplate:
    """Template for journal entries."""

    name: str
    category: str
    content_template: str
    suggested_tags: List[str]
    mood_prompt: str
    weather_focus: List[str]  # Weather aspects to highlight
    description: str


class EntryTemplateManager:
    """Manager for journal entry templates."""

    def __init__(self):
        """Initialize the template manager with predefined templates."""
        self.templates = self._create_default_templates()

    def _create_default_templates(self) -> Dict[str, EntryTemplate]:
        """Create the default set of entry templates."""
        templates = {}

        # Daily Weather Template
        templates["daily_weather"] = EntryTemplate(
            name="Daily Weather Check-in",
            category="Daily",
            content_template="""Today's Weather Reflection:

Morning Conditions:
- Temperature: {temperature}°F
- Sky: {conditions}
- Wind: {wind_speed} mph

How the weather affected my day:
[Describe how today's weather influenced your mood, activities, or plans]

Weather highlights:
[Note any interesting weather phenomena, changes throughout the day, or memorable moments]

Tomorrow's plans based on forecast:
[How will tomorrow's expected weather influence your plans?]

Overall weather satisfaction: [Rate 1-10]""",
            suggested_tags=["daily", "weather", "mood", "reflection"],
            mood_prompt="How did today's weather make you feel overall?",
            weather_focus=["temperature", "conditions", "wind_speed", "humidity", "pressure"],
            description="Perfect for daily weather tracking and mood correlation",
        )

        # Travel Template
        templates["travel"] = EntryTemplate(
            name="Travel Weather Log",
            category="Travel",
            content_template="""Travel Weather Experience:

Destination: [Location]
Travel Date: {date}

Weather Conditions:
- Temperature: {temperature}°F
- Conditions: {conditions}
- Visibility: {visibility}
- Wind: {wind_speed} mph

Travel Impact:
[How did the weather affect your travel plans, transportation, or itinerary?]

Destination Weather:
[Describe the weather at your destination and how it compared to expectations]

Weather Preparations:
[What weather-related preparations did you make? What would you do differently?]

Memorable Weather Moments:
[Any unique weather experiences during your travels]

Travel Weather Rating: [Rate 1-10]""",
            suggested_tags=["travel", "destination", "planning", "adventure"],
            mood_prompt="How did the weather enhance or challenge your travel experience?",
            weather_focus=[
                "temperature",
                "conditions",
                "wind_speed",
                "visibility",
                "precipitation",
            ],
            description="Ideal for documenting weather during trips and vacations",
        )

        # Outdoor Activities Template
        templates["outdoor_activity"] = EntryTemplate(
            name="Outdoor Activity Weather",
            category="Outdoor",
            content_template="""Outdoor Activity Weather Report:

Activity: [Type of outdoor activity]
Location: [Where you went]
Duration: [How long you were outside]

Weather Conditions:
- Temperature: {temperature}°F
- Conditions: {conditions}
- Wind: {wind_speed} mph
- UV Index: {uv_index}

Activity Performance:
[How did the weather conditions affect your activity performance or enjoyment?]

Gear and Preparation:
[What weather-appropriate gear did you use? What worked well or poorly?]

Weather Challenges:
[Any weather-related obstacles or unexpected conditions you encountered]

Best Weather Moments:
[Highlight the most enjoyable weather-related aspects of your activity]

Would you do this activity in similar conditions again? [Yes/No and why]

Activity Weather Rating: [Rate 1-10]""",
            suggested_tags=["outdoor", "activity", "exercise", "nature"],
            mood_prompt="How did the weather conditions enhance your outdoor experience?",
            weather_focus=["temperature", "conditions", "wind_speed", "uv_index", "humidity"],
            description="Great for tracking weather during outdoor sports and activities",
        )

        # Seasonal Reflection Template
        templates["seasonal"] = EntryTemplate(
            name="Seasonal Weather Reflection",
            category="Seasonal",
            content_template="""Seasonal Weather Reflection:

Season: [Current season]
Date: {date}

Today's Seasonal Weather:
- Temperature: {temperature}°F
- Conditions: {conditions}
- Seasonal Indicators: [Signs of the season you noticed]

Seasonal Mood:
[How does this season typically affect your mood and energy levels?]

Seasonal Activities:
[What season-specific activities are you enjoying or planning?]

Weather Patterns:
[Have you noticed any unusual weather patterns for this time of year?]

Seasonal Preparations:
[How are you preparing for upcoming seasonal weather changes?]

Favorite Seasonal Weather:
[What's your favorite type of weather for this season and why?]

Seasonal Weather Appreciation: [Rate 1-10]""",
            suggested_tags=["seasonal", "patterns", "mood", "nature"],
            mood_prompt="How does this season's weather typically make you feel?",
            weather_focus=["temperature", "conditions", "seasonal_patterns"],
            description="Perfect for reflecting on seasonal weather patterns and their effects",
        )

        # Extreme Weather Template
        templates["extreme_weather"] = EntryTemplate(
            name="Extreme Weather Event",
            category="Extreme",
            content_template="""Extreme Weather Event Documentation:

Event Type: [Storm, heat wave, blizzard, etc.]
Date and Time: {date}
Location: [Where you experienced this weather]

Weather Conditions:
- Temperature: {temperature}°F
- Conditions: {conditions}
- Wind Speed: {wind_speed} mph
- Precipitation: [Amount and type]
- Pressure: {pressure} inHg

Event Description:
[Detailed description of the extreme weather event]

Safety Measures:
[What precautions did you take? How did you stay safe?]

Impact on Daily Life:
[How did this weather event affect your plans, transportation, or routine?]

Emotional Response:
[How did experiencing this extreme weather make you feel?]

Lessons Learned:
[What did you learn about weather preparedness or safety?]

Photos/Documentation:
[Note any photos or additional documentation you captured]

Extreme Weather Impact Rating: [Rate 1-10]""",
            suggested_tags=["extreme", "storm", "safety", "documentation"],
            mood_prompt="How did experiencing this extreme weather event affect your emotions?",
            weather_focus=["temperature", "conditions", "wind_speed", "pressure", "precipitation"],
            description="For documenting significant weather events and their impacts",
        )

        # Garden/Nature Template
        templates["garden_nature"] = EntryTemplate(
            name="Garden & Nature Weather",
            category="Nature",
            content_template="""Garden & Nature Weather Observation:

Location: [Garden, park, natural area]
Date: {date}

Weather Conditions:
- Temperature: {temperature}°F
- Conditions: {conditions}
- Humidity: {humidity}%
- Recent Precipitation: [Amount and timing]

Plant/Nature Observations:
[How are plants, animals, or natural features responding to current weather?]

Garden Impact:
[If applicable, how is the weather affecting your garden or plants?]

Wildlife Activity:
[Any changes in animal behavior related to weather conditions?]

Nature's Weather Signs:
[Natural indicators of weather changes you observed]

Seasonal Changes:
[Weather-related seasonal changes you're noticing in nature]

Weather Wishes:
[What weather conditions would benefit the plants/nature you observed?]

Nature Weather Harmony Rating: [Rate 1-10]""",
            suggested_tags=["garden", "nature", "plants", "wildlife"],
            mood_prompt="How does observing nature in these weather conditions make you feel?",
            weather_focus=["temperature", "humidity", "precipitation", "conditions"],
            description="Ideal for tracking weather's impact on gardens and natural environments",
        )

        # Quick Check-in Template
        templates["quick_checkin"] = EntryTemplate(
            name="Quick Weather Check-in",
            category="Quick",
            content_template="""Quick Weather Check-in:

Time: {time}
Weather: {temperature}°F, {conditions}

Mood: [How you're feeling right now]

Weather Impact: [One sentence about how weather is affecting you today]

Activity: [What you're doing or planning to do]

Weather Wish: [If you could change one thing about today's weather, what would it be?]

Quick Rating: [Rate today's weather 1-10]""",
            suggested_tags=["quick", "checkin", "mood"],
            mood_prompt="Quick mood check - how's the weather making you feel?",
            weather_focus=["temperature", "conditions"],
            description="Fast and simple weather mood tracking",
        )

        return templates

    def get_template(self, template_id: str) -> Optional[EntryTemplate]:
        """Get a specific template by ID."""
        return self.templates.get(template_id)

    def get_all_templates(self) -> Dict[str, EntryTemplate]:
        """Get all available templates."""
        return self.templates.copy()

    def get_templates_by_category(self, category: str) -> Dict[str, EntryTemplate]:
        """Get templates filtered by category."""
        return {
            tid: template
            for tid, template in self.templates.items()
            if template.category.lower() == category.lower()
        }

    def get_template_names(self) -> List[str]:
        """Get list of all template names."""
        return [template.name for template in self.templates.values()]

    def get_template_categories(self) -> List[str]:
        """Get list of unique template categories."""
        categories = set(template.category for template in self.templates.values())
        return sorted(list(categories))

    def apply_template(
        self,
        template_id: str,
        weather_data: Optional[Dict[str, Any]] = None,
        custom_values: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Apply a template with weather data and custom values.

        Args:
            template_id: ID of the template to apply
            weather_data: Current weather data to fill in template
            custom_values: Custom values to override template placeholders

        Returns:
            Dictionary with filled template data or None if template not found
        """
        template = self.get_template(template_id)
        if not template:
            return None

        # Prepare template values
        template_values = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "temperature": "N/A",
            "conditions": "N/A",
            "wind_speed": "N/A",
            "humidity": "N/A",
            "pressure": "N/A",
            "visibility": "N/A",
            "uv_index": "N/A",
            "precipitation": "N/A",
        }

        # Fill in weather data if available
        if weather_data:
            if "main" in weather_data:
                template_values["temperature"] = f"{weather_data['main'].get('temp', 'N/A')}"
                template_values["humidity"] = f"{weather_data['main'].get('humidity', 'N/A')}"
                template_values["pressure"] = f"{weather_data['main'].get('pressure', 'N/A')}"

            if "weather" in weather_data and weather_data["weather"]:
                template_values["conditions"] = weather_data["weather"][0].get("description", "N/A")

            if "wind" in weather_data:
                template_values["wind_speed"] = f"{weather_data['wind'].get('speed', 'N/A')}"

            if "visibility" in weather_data and weather_data["visibility"] is not None:
                template_values["visibility"] = (
                    f"{safe_divide(weather_data['visibility'], 1000, 0):.1f} km"
                )

        # Apply custom values
        if custom_values:
            template_values.update(custom_values)

        # Format the template content
        try:
            formatted_content = template.content_template.format(**template_values)
        except KeyError as e:
            # If some placeholders are missing, just use the template as-is
            formatted_content = template.content_template

        return {
            "template_id": template_id,
            "template_name": template.name,
            "category": template.category,
            "content": formatted_content,
            "suggested_tags": template.suggested_tags.copy(),
            "mood_prompt": template.mood_prompt,
            "weather_focus": template.weather_focus.copy(),
            "description": template.description,
        }

    def create_custom_template(self, template_id: str, template: EntryTemplate) -> bool:
        """Create a custom template.

        Args:
            template_id: Unique ID for the template
            template: EntryTemplate instance

        Returns:
            True if created successfully, False if ID already exists
        """
        if template_id in self.templates:
            return False

        self.templates[template_id] = template
        return True

    def update_template(self, template_id: str, template: EntryTemplate) -> bool:
        """Update an existing template.

        Args:
            template_id: ID of template to update
            template: Updated EntryTemplate instance

        Returns:
            True if updated successfully, False if template doesn't exist
        """
        if template_id not in self.templates:
            return False

        self.templates[template_id] = template
        return True

    def delete_template(self, template_id: str) -> bool:
        """Delete a template.

        Args:
            template_id: ID of template to delete

        Returns:
            True if deleted successfully, False if template doesn't exist
        """
        if template_id not in self.templates:
            return False

        del self.templates[template_id]
        return True

    def search_templates(self, query: str) -> Dict[str, EntryTemplate]:
        """Search templates by name, category, or description.

        Args:
            query: Search query string

        Returns:
            Dictionary of matching templates
        """
        query_lower = query.lower()
        matching_templates = {}

        for template_id, template in self.templates.items():
            if (
                query_lower in template.name.lower()
                or query_lower in template.category.lower()
                or query_lower in template.description.lower()
                or any(query_lower in tag.lower() for tag in template.suggested_tags)
            ):
                matching_templates[template_id] = template

        return matching_templates

    def get_template_suggestions(
        self, weather_data: Optional[Dict[str, Any]] = None, activity_type: Optional[str] = None
    ) -> List[str]:
        """Get template suggestions based on weather conditions or activity type.

        Args:
            weather_data: Current weather data
            activity_type: Type of activity planned

        Returns:
            List of suggested template IDs
        """
        suggestions = []

        # Default suggestion
        suggestions.append("quick_checkin")

        # Weather-based suggestions
        if weather_data:
            # Check for extreme weather
            if "wind" in weather_data and weather_data["wind"].get("speed", 0) > 25:
                suggestions.append("extreme_weather")

            if "main" in weather_data:
                temp = weather_data["main"].get("temp", 20)
                if temp > 35 or temp < -10:  # Extreme temperatures
                    suggestions.append("extreme_weather")

            # Check weather conditions
            if "weather" in weather_data and weather_data["weather"]:
                condition = weather_data["weather"][0].get("main", "").lower()
                if condition in ["thunderstorm", "snow", "extreme"]:
                    suggestions.append("extreme_weather")

        # Activity-based suggestions
        if activity_type:
            activity_lower = activity_type.lower()
            if any(word in activity_lower for word in ["travel", "trip", "vacation"]):
                suggestions.append("travel")
            elif any(
                word in activity_lower for word in ["outdoor", "hike", "run", "bike", "sport"]
            ):
                suggestions.append("outdoor_activity")
            elif any(word in activity_lower for word in ["garden", "plant", "nature"]):
                suggestions.append("garden_nature")

        # Always suggest daily and seasonal templates
        suggestions.extend(["daily_weather", "seasonal"])

        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen and suggestion in self.templates:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)

        return unique_suggestions
