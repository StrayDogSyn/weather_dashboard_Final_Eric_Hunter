"""Suggestion Engine Mixin

Contains all AI suggestion generation and activity management methods.
"""

import json
from typing import List, Dict
import threading
import traceback
import customtkinter as ctk
from ui.theme import DataTerminalTheme


class SuggestionEngineMixin:
    """Mixin class containing suggestion generation and activity management methods."""
    
    def _fetch_suggestions(self) -> None:
        """Fetch suggestions from AI and weather data using enhanced AI service."""
        try:
            # Get current weather
            self.current_weather = self.weather_service.get_current_weather()
            
            # Update weather display
            self.after(0, self._update_weather_display)
            
            # Generate AI suggestions using enhanced service with fallback hierarchy
            ai_suggestions = None
            
            # Try enhanced AI service first
            try:
                ai_suggestions = self._generate_enhanced_ai_suggestions()
                if ai_suggestions:
                    print("✅ Generated suggestions using enhanced AI service")
            except Exception as e:
                print(f"⚠️ Enhanced AI service failed: {e}")
                
                # Fallback to legacy AI methods
                if hasattr(self, 'gemini_available') and self.gemini_available and self.current_weather:
                    try:
                        ai_suggestions = self._generate_gemini_suggestions()
                        if ai_suggestions:
                            print("✅ Generated suggestions using legacy Gemini")
                    except Exception as gemini_error:
                        print(f"⚠️ Legacy Gemini generation failed: {gemini_error}")
                
                # Fallback to OpenAI if Gemini failed
                if not ai_suggestions and hasattr(self, 'openai_available') and self.openai_available and self.current_weather:
                    try:
                        ai_suggestions = self._generate_openai_suggestions()
                        if ai_suggestions:
                            print("✅ Generated suggestions using legacy OpenAI")
                    except Exception as openai_error:
                        print(f"⚠️ Legacy OpenAI generation failed: {openai_error}")
            
            # Final fallback to default suggestions
            if not ai_suggestions:
                ai_suggestions = self._get_fallback_suggestions()
                print("ℹ️ Using fallback suggestions")
            
            self.suggestions = ai_suggestions
            
            # Update UI
            self.after(0, self._display_suggestions)
            self.after(0, lambda: self.refresh_btn.configure(state="normal", text="🔄 Refresh"))
            self.after(0, self._update_ai_status)
            
        except Exception as e:
            print(f"Error fetching suggestions: {e}")
            self.after(0, self._show_error)
    
    def _generate_enhanced_ai_suggestions(self) -> List[Dict]:
        """Generate activity suggestions using enhanced AI service."""
        try:
            if not self.current_weather:
                return self._get_fallback_suggestions()
            
            # Get user preferences
            preferences = self._get_user_preferences()
            
            # Use enhanced AI service with intelligent model selection
            response = self.ai_service.generate_activity_suggestions(
                weather_data=self.current_weather,
                user_preferences=preferences
            )
            
            if response and isinstance(response, dict) and 'activities' in response:
                return response['activities']
            else:
                print("⚠️ Enhanced AI service returned invalid response format")
                return []
            
        except Exception as e:
            print(f"❌ Enhanced AI generation error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_user_preferences(self) -> Dict:
        """Get user preferences for activity suggestions."""
        # Get user activity history from database
        history = self._get_user_activity_history()
        
        # Extract preferences from history
        liked_activities = [h['activity_name'] for h in history if h['liked']]
        preferred_categories = self._get_preferred_categories()
        
        return {
            'liked_activities': liked_activities,
            'preferred_categories': preferred_categories,
            'fitness_level': 'moderate',  # Could be expanded to user settings
            'time_available': '1-2 hours'  # Could be expanded to user settings
        }
    
    def _generate_gemini_suggestions(self) -> List[Dict]:
        """Generate activity suggestions using Gemini AI."""
        try:
            # Get user preferences
            preferences = self._get_user_activity_history()
            
            # Create prompt
            prompt = self._create_ai_prompt(self.current_weather, preferences)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            suggestions_data = json.loads(response.text)
            return suggestions_data.get('activities', [])
            
        except Exception as e:
            print(f"❌ Gemini generation error: {e}")
            # Fallback to OpenAI if available
            if hasattr(self, 'openai_available') and self.openai_available:
                print("🔄 Falling back to OpenAI...")
                return self._generate_openai_suggestions()
            return self._get_fallback_suggestions()
    
    def _generate_openai_suggestions(self) -> List[Dict]:
        """Generate activity suggestions using OpenAI API."""
        try:
            # Get user preferences
            preferences = self._get_user_activity_history()
            
            # Create prompt
            prompt = self._create_ai_prompt(self.current_weather, preferences)
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that provides personalized activity suggestions based on weather conditions. Always respond with valid JSON in the exact format requested."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Parse JSON response
            response_text = response.choices[0].message.content
            suggestions_data = json.loads(response_text)
            return suggestions_data.get('activities', [])
            
        except Exception as e:
            print(f"❌ OpenAI generation error: {e}")
            return self._get_fallback_suggestions()
    
    def _create_ai_prompt(self, weather: Dict, preferences: List[Dict]) -> str:
        """Create prompt for AI suggestion generation."""
        temp = weather.get('temperature', 20)
        condition = weather.get('condition', 'Clear')
        humidity = weather.get('humidity', 50)
        wind_speed = weather.get('wind_speed', 5)
        
        liked_activities = [p['activity_name'] for p in preferences if p.get('liked') == 1]
        disliked_activities = [p['activity_name'] for p in preferences if p.get('liked') == 0]
        
        prompt = f"""
        Generate 6-8 personalized activity suggestions based on current weather conditions.
        
        Current Weather:
        - Temperature: {temp}°C
        - Condition: {condition}
        - Humidity: {humidity}%
        - Wind Speed: {wind_speed} km/h
        
        User Preferences:
        - Liked activities: {', '.join(liked_activities) if liked_activities else 'None recorded'}
        - Disliked activities: {', '.join(disliked_activities) if disliked_activities else 'None recorded'}
        
        Please respond with a JSON object in this exact format:
        {{
            "activities": [
                {{
                    "name": "Activity Name",
                    "category": "Outdoor|Indoor|Fitness|Creative|Social",
                    "description": "Brief description of the activity",
                    "weather_suitability": "Why this activity fits the current weather",
                    "duration": "Estimated time (e.g., '30 minutes', '2 hours')",
                    "difficulty": "Easy|Medium|Hard",
                    "equipment_needed": ["item1", "item2"],
                    "benefits": ["benefit1", "benefit2"]
                }}
            ]
        }}
        
        Consider weather appropriateness, user preferences, and provide diverse activity types.
        """
        
        return prompt
    
    def _get_fallback_suggestions(self) -> List[Dict]:
        """Provide fallback suggestions when AI is unavailable."""
        if not hasattr(self, 'current_weather') or not self.current_weather:
            temp = 20
            condition = "Clear"
        else:
            temp = self.current_weather.get('temperature', 20)
            condition = self.current_weather.get('condition', 'Clear')
        
        suggestions = []
        
        # Temperature-based suggestions
        if temp > 25:
            suggestions.extend([
                {
                    "name": "Swimming",
                    "category": "Outdoor",
                    "description": "Cool off with a refreshing swim",
                    "weather_suitability": "Perfect for hot weather",
                    "duration": "1-2 hours",
                    "difficulty": "Easy",
                    "equipment_needed": ["Swimwear", "Towel"],
                    "benefits": ["Full body workout", "Cooling"]
                },
                {
                    "name": "Ice Cream Walk",
                    "category": "Social",
                    "description": "Enjoy ice cream while taking a leisurely walk",
                    "weather_suitability": "Great way to stay cool",
                    "duration": "30 minutes",
                    "difficulty": "Easy",
                    "equipment_needed": [],
                    "benefits": ["Social interaction", "Light exercise"]
                }
            ])
        elif temp < 10:
            suggestions.extend([
                {
                    "name": "Hot Chocolate & Reading",
                    "category": "Indoor",
                    "description": "Cozy up with a warm drink and a good book",
                    "weather_suitability": "Perfect for cold weather",
                    "duration": "1-3 hours",
                    "difficulty": "Easy",
                    "equipment_needed": ["Book", "Hot chocolate"],
                    "benefits": ["Relaxation", "Mental stimulation"]
                },
                {
                    "name": "Indoor Yoga",
                    "category": "Fitness",
                    "description": "Warm up your body with gentle yoga",
                    "weather_suitability": "Stay warm indoors",
                    "duration": "30-60 minutes",
                    "difficulty": "Easy",
                    "equipment_needed": ["Yoga mat"],
                    "benefits": ["Flexibility", "Stress relief"]
                }
            ])
        
        # Condition-based suggestions
        if "rain" in condition.lower():
            suggestions.extend([
                {
                    "name": "Museum Visit",
                    "category": "Indoor",
                    "description": "Explore art, history, or science exhibits",
                    "weather_suitability": "Perfect rainy day activity",
                    "duration": "2-4 hours",
                    "difficulty": "Easy",
                    "equipment_needed": [],
                    "benefits": ["Learning", "Cultural enrichment"]
                },
                {
                    "name": "Cooking Challenge",
                    "category": "Creative",
                    "description": "Try a new recipe or cooking technique",
                    "weather_suitability": "Great indoor activity",
                    "duration": "1-2 hours",
                    "difficulty": "Medium",
                    "equipment_needed": ["Ingredients", "Kitchen tools"],
                    "benefits": ["Creativity", "Practical skill"]
                }
            ])
        elif "clear" in condition.lower() or "sunny" in condition.lower():
            suggestions.extend([
                {
                    "name": "Nature Photography",
                    "category": "Outdoor",
                    "description": "Capture beautiful outdoor scenes",
                    "weather_suitability": "Great lighting for photos",
                    "duration": "1-3 hours",
                    "difficulty": "Easy",
                    "equipment_needed": ["Camera or phone"],
                    "benefits": ["Creativity", "Nature connection"]
                },
                {
                    "name": "Picnic in the Park",
                    "category": "Social",
                    "description": "Enjoy food outdoors with friends or family",
                    "weather_suitability": "Perfect sunny weather activity",
                    "duration": "2-3 hours",
                    "difficulty": "Easy",
                    "equipment_needed": ["Blanket", "Food"],
                    "benefits": ["Social bonding", "Fresh air"]
                }
            ])
        
        # Always include some general suggestions
        suggestions.extend([
            {
                "name": "Meditation",
                "category": "Indoor",
                "description": "Practice mindfulness and relaxation",
                "weather_suitability": "Good for any weather",
                "duration": "10-30 minutes",
                "difficulty": "Easy",
                "equipment_needed": [],
                "benefits": ["Stress relief", "Mental clarity"]
            },
            {
                "name": "Journaling",
                "category": "Creative",
                "description": "Write about your thoughts and experiences",
                "weather_suitability": "Perfect for any weather",
                "duration": "20-60 minutes",
                "difficulty": "Easy",
                "equipment_needed": ["Notebook", "Pen"],
                "benefits": ["Self-reflection", "Emotional processing"]
            }
        ])
        
        return suggestions[:8]  # Limit to 8 suggestions
    
    def _rate_activity(self, activity: Dict, rating: int) -> None:
        """Rate an activity and save to database."""
        try:
            # Save rating to database
            self._save_activity_rating(activity, rating)
            
            # Show confirmation message
            self._show_temporary_message(f"⭐ Rated '{activity.get('name')}' with {rating} stars!")
            
        except Exception as e:
            print(f"Error rating activity: {e}")
    
    def _show_activity_details(self, activity: Dict) -> None:
        """Show detailed information about an activity."""
        try:
            # Create details window
            details_window = ctk.CTkToplevel(self)
            details_window.title(f"Activity Details - {activity.get('name', 'Unknown')}")
            details_window.geometry("500x600")
            details_window.transient(self)
            details_window.grab_set()
            
            # Configure grid
            details_window.grid_rowconfigure(0, weight=1)
            details_window.grid_columnconfigure(0, weight=1)
            
            # Main frame
            main_frame = ctk.CTkScrollableFrame(
                details_window,
                fg_color=DataTerminalTheme.CARD_BG
            )
            main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
            # Activity name
            name_label = ctk.CTkLabel(
                main_frame,
                text=activity.get('name', 'Unknown Activity'),
                font=(DataTerminalTheme.FONT_FAMILY, 20, "bold"),
                text_color=DataTerminalTheme.TEXT
            )
            name_label.pack(pady=(0, 10))
            
            # Category
            category_label = ctk.CTkLabel(
                main_frame,
                text=f"Category: {activity.get('category', 'General')}",
                font=(DataTerminalTheme.FONT_FAMILY, 14),
                text_color=DataTerminalTheme.PRIMARY
            )
            category_label.pack(pady=(0, 15))
            
            # Description
            desc_frame = ctk.CTkFrame(main_frame, fg_color=DataTerminalTheme.CARD_BG)
            desc_frame.pack(fill="x", pady=(0, 15))
            
            ctk.CTkLabel(
                desc_frame,
                text="Description:",
                font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
                text_color=DataTerminalTheme.TEXT
            ).pack(anchor="w", padx=15, pady=(15, 5))
            
            ctk.CTkLabel(
                desc_frame,
                text=activity.get('description', 'No description available'),
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                wraplength=400,
                justify="left"
            ).pack(anchor="w", padx=15, pady=(0, 15))
            
            # Weather suitability
            if 'weather_suitability' in activity:
                weather_frame = ctk.CTkFrame(main_frame, fg_color=DataTerminalTheme.CARD_BG)
                weather_frame.pack(fill="x", pady=(0, 15))
                
                ctk.CTkLabel(
                    weather_frame,
                    text="Weather Suitability:",
                    font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
                    text_color=DataTerminalTheme.TEXT
                ).pack(anchor="w", padx=15, pady=(15, 5))
                
                ctk.CTkLabel(
                    weather_frame,
                    text=activity['weather_suitability'],
                    font=(DataTerminalTheme.FONT_FAMILY, 12),
                    text_color=DataTerminalTheme.TEXT_SECONDARY,
                    wraplength=400,
                    justify="left"
                ).pack(anchor="w", padx=15, pady=(0, 15))
            
            # Details grid
            details_frame = ctk.CTkFrame(main_frame, fg_color=DataTerminalTheme.CARD_BG)
            details_frame.pack(fill="x", pady=(0, 15))
            
            details_content = ctk.CTkFrame(details_frame, fg_color="transparent")
            details_content.pack(fill="x", padx=15, pady=15)
            
            # Duration and Difficulty
            info_text = f"⏱️ Duration: {activity.get('duration', 'Unknown')}\n"
            info_text += f"📊 Difficulty: {activity.get('difficulty', 'Unknown')}"
            
            ctk.CTkLabel(
                details_content,
                text=info_text,
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                text_color=DataTerminalTheme.TEXT,
                justify="left"
            ).pack(anchor="w")
            
            # Equipment needed
            if 'equipment_needed' in activity and activity['equipment_needed']:
                equipment_frame = ctk.CTkFrame(main_frame, fg_color=DataTerminalTheme.CARD_BG)
                equipment_frame.pack(fill="x", pady=(0, 15))
                
                ctk.CTkLabel(
                    equipment_frame,
                    text="Equipment Needed:",
                    font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
                    text_color=DataTerminalTheme.TEXT
                ).pack(anchor="w", padx=15, pady=(15, 5))
                
                equipment_text = "• " + "\n• ".join(activity['equipment_needed'])
                ctk.CTkLabel(
                    equipment_frame,
                    text=equipment_text,
                    font=(DataTerminalTheme.FONT_FAMILY, 12),
                    text_color=DataTerminalTheme.TEXT_SECONDARY,
                    justify="left"
                ).pack(anchor="w", padx=15, pady=(0, 15))
            
            # Benefits
            if 'benefits' in activity and activity['benefits']:
                benefits_frame = ctk.CTkFrame(main_frame, fg_color=DataTerminalTheme.CARD_BG)
                benefits_frame.pack(fill="x", pady=(0, 15))
                
                ctk.CTkLabel(
                    benefits_frame,
                    text="Benefits:",
                    font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
                    text_color=DataTerminalTheme.TEXT
                ).pack(anchor="w", padx=15, pady=(15, 5))
                
                benefits_text = "• " + "\n• ".join(activity['benefits'])
                ctk.CTkLabel(
                    benefits_frame,
                    text=benefits_text,
                    font=(DataTerminalTheme.FONT_FAMILY, 12),
                    text_color=DataTerminalTheme.SUCCESS,
                    justify="left"
                ).pack(anchor="w", padx=15, pady=(0, 15))
            
            # Close button
            close_btn = ctk.CTkButton(
                main_frame,
                text="Close",
                width=100,
                height=32,
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                fg_color=DataTerminalTheme.PRIMARY,
                hover_color=DataTerminalTheme.PRIMARY,
                command=details_window.destroy
            )
            close_btn.pack(pady=20)
            
        except Exception as e:
            print(f"Error showing activity details: {e}")
    
    def update_weather(self, weather_data: Dict) -> None:
        """Update weather data and refresh suggestions if needed."""
        self.current_weather = weather_data
        self._update_weather_display()