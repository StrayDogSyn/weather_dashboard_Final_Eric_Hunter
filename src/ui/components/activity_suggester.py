import customtkinter as ctk
from typing import List, Dict, Optional
from datetime import datetime
import json
import sqlite3
from pathlib import Path
from ui.theme import DataTerminalTheme
import threading

# Optional import for Google Generative AI
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

class ActivitySuggester(ctk.CTkFrame):
    """AI-powered activity suggestions based on weather conditions."""
    
    def __init__(self, parent, weather_service, config_service, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.weather_service = weather_service
        self.config_service = config_service
        self.current_weather = None
        self.suggestions = []
        
        # Initialize Gemini API
        self._initialize_gemini()
        
        # Setup preferences database
        self._setup_database()
        
        # Create UI
        self._create_ui()
        
        # Load initial suggestions
        self._refresh_suggestions()
    
    def _initialize_gemini(self):
        """Initialize Google Gemini API."""
        if not GENAI_AVAILABLE:
            self.model = None
            self.gemini_available = False
            print("Warning: google-generativeai package not installed")
            return
            
        try:
            api_key = self.config_service.get('gemini_api_key')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.gemini_available = True
            else:
                self.gemini_available = False
                self.model = None
        except Exception as e:
            print(f"Gemini initialization error: {e}")
            self.gemini_available = False
            self.model = None
    
    def _setup_database(self):
        """Setup SQLite for activity preferences."""
        db_path = Path("data") / "activity_preferences.db"
        db_path.parent.mkdir(exist_ok=True)
        
        self.conn = sqlite3.connect(str(db_path))
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_name TEXT,
                category TEXT,
                liked INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                weather_condition TEXT,
                temperature REAL
            )
        ''')
        self.conn.commit()
    
    def _create_ui(self):
        """Create activity suggester interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header section
        self._create_header()
        
        # Suggestions area
        self._create_suggestions_area()
    
    def _create_header(self):
        """Create header with filters and refresh."""
        header_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        # Title and weather info
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            title_frame,
            text="🎯 AI Activity Suggestions",
            font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
            text_color=DataTerminalTheme.PRIMARY
        ).pack(side="left")
        
        self.weather_label = ctk.CTkLabel(
            title_frame,
            text="Loading weather...",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.weather_label.pack(side="left", padx=(20, 0))
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            title_frame,
            text="🔄 Refresh",
            width=100,
            height=32,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.SUCCESS,
            command=self._refresh_suggestions
        )
        self.refresh_btn.pack(side="right")
        
        # Category filters
        filter_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            filter_frame,
            text="Filter by category:",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT
        ).pack(side="left", padx=(0, 10))
        
        categories = ["All", "Outdoor", "Indoor", "Fitness", "Creative", "Social"]
        self.category_buttons = {}
        self.selected_category = "All"
        
        for cat in categories:
            btn = ctk.CTkButton(
                filter_frame,
                text=cat,
                width=80,
                height=28,
                font=(DataTerminalTheme.FONT_FAMILY, 11),
                fg_color=DataTerminalTheme.CARD_BG,
                hover_color=DataTerminalTheme.HOVER,
                border_width=1,
                border_color=DataTerminalTheme.BORDER,
                command=lambda c=cat: self._filter_category(c)
            )
            btn.pack(side="left", padx=3)
            self.category_buttons[cat] = btn
        
        # Set "All" as active
        self.category_buttons["All"].configure(
            fg_color=DataTerminalTheme.PRIMARY,
            border_color=DataTerminalTheme.PRIMARY
        )
    
    def _create_suggestions_area(self):
        """Create scrollable area for activity cards."""
        self.suggestions_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER
        )
        self.suggestions_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Loading indicator
        self.loading_label = ctk.CTkLabel(
            self.suggestions_frame,
            text="🔄 Generating AI suggestions...",
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.loading_label.pack(pady=50)
    
    def _filter_category(self, category: str):
        """Filter suggestions by category."""
        # Update button states
        for cat, btn in self.category_buttons.items():
            if cat == category:
                btn.configure(
                    fg_color=DataTerminalTheme.PRIMARY,
                    border_color=DataTerminalTheme.PRIMARY
                )
            else:
                btn.configure(
                    fg_color=DataTerminalTheme.CARD_BG,
                    border_color=DataTerminalTheme.BORDER
                )
        
        self.selected_category = category
        self._display_suggestions()
    
    def _refresh_suggestions(self):
        """Refresh activity suggestions."""
        self.loading_label.pack(pady=50)
        self.refresh_btn.configure(state="disabled", text="Loading...")
        
        # Run in background thread
        threading.Thread(target=self._fetch_suggestions, daemon=True).start()
    
    def _fetch_suggestions(self):
        """Fetch suggestions from AI and weather data."""
        try:
            # Get current weather
            self.current_weather = self.weather_service.get_current_weather()
            
            # Update weather display
            self.after(0, self._update_weather_display)
            
            # Generate AI suggestions
            if self.gemini_available and self.current_weather:
                ai_suggestions = self._generate_ai_suggestions()
            else:
                ai_suggestions = self._get_fallback_suggestions()
            
            self.suggestions = ai_suggestions
            
            # Update UI
            self.after(0, self._display_suggestions)
            self.after(0, lambda: self.refresh_btn.configure(state="normal", text="🔄 Refresh"))
            
        except Exception as e:
            print(f"Error fetching suggestions: {e}")
            self.after(0, self._show_error)
    
    def _update_weather_display(self):
        """Update weather information in header."""
        if self.current_weather:
            temp = self.current_weather.get('temperature', 'N/A')
            condition = self.current_weather.get('condition', 'Unknown')
            self.weather_label.configure(
                text=f"🌡️ {temp}°C | {condition}"
            )
        else:
            self.weather_label.configure(text="Weather unavailable")
    
    def _generate_ai_suggestions(self) -> List[Dict]:
        """Generate activity suggestions using Gemini AI."""
        try:
            # Get user preferences
            preferences = self._get_user_preferences()
            
            # Create prompt
            prompt = self._create_ai_prompt(self.current_weather, preferences)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            suggestions_data = json.loads(response.text)
            return suggestions_data.get('activities', [])
            
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._get_fallback_suggestions()
    
    def _create_ai_prompt(self, weather: Dict, preferences: List[Dict]) -> str:
        """Create prompt for AI suggestion generation."""
        temp = weather.get('temperature', 20)
        condition = weather.get('condition', 'Clear')
        humidity = weather.get('humidity', 50)
        wind_speed = weather.get('wind_speed', 5)
        
        liked_activities = [p['activity_name'] for p in preferences if p['liked'] == 1]
        disliked_activities = [p['activity_name'] for p in preferences if p['liked'] == 0]
        
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
    
    def _get_user_preferences(self) -> List[Dict]:
        """Get user activity preferences from database."""
        try:
            self.cursor.execute(
                "SELECT activity_name, category, liked FROM activity_preferences ORDER BY timestamp DESC LIMIT 50"
            )
            return [{
                'activity_name': row[0],
                'category': row[1],
                'liked': row[2]
            } for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Database error: {e}")
            return []
    
    def _get_fallback_suggestions(self) -> List[Dict]:
        """Provide fallback suggestions when AI is unavailable."""
        if not self.current_weather:
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
    
    def _display_suggestions(self):
        """Display activity suggestions in the UI."""
        # Clear existing content
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()
        
        # Filter suggestions by category
        filtered_suggestions = self.suggestions
        if self.selected_category != "All":
            filtered_suggestions = [
                s for s in self.suggestions 
                if s.get('category') == self.selected_category
            ]
        
        if not filtered_suggestions:
            no_results_label = ctk.CTkLabel(
                self.suggestions_frame,
                text=f"No {self.selected_category.lower()} activities found",
                font=(DataTerminalTheme.FONT_FAMILY, 14),
                text_color=DataTerminalTheme.TEXT_SECONDARY
            )
            no_results_label.pack(pady=50)
            return
        
        # Create activity cards
        for i, activity in enumerate(filtered_suggestions):
            self._create_activity_card(activity, i)
    
    def _create_activity_card(self, activity: Dict, index: int):
        """Create a card for an activity suggestion."""
        card_frame = ctk.CTkFrame(
            self.suggestions_frame,
            fg_color=DataTerminalTheme.BG,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER
        )
        card_frame.pack(fill="x", padx=10, pady=5)
        
        # Main content frame
        content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header with name and category
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Activity name
        name_label = ctk.CTkLabel(
            header_frame,
            text=activity.get('name', 'Unknown Activity'),
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        name_label.pack(side="left")
        
        # Category badge
        category = activity.get('category', 'General')
        category_colors = {
            'Outdoor': DataTerminalTheme.SUCCESS,
            'Indoor': DataTerminalTheme.WARNING,
            'Fitness': DataTerminalTheme.ERROR,
            'Creative': DataTerminalTheme.PRIMARY,
            'Social': "#9C27B0"
        }
        
        category_label = ctk.CTkLabel(
            header_frame,
            text=category,
            font=(DataTerminalTheme.FONT_FAMILY, 10, "bold"),
            text_color="white",
            fg_color=category_colors.get(category, DataTerminalTheme.TEXT_SECONDARY),
            corner_radius=12,
            width=60,
            height=24
        )
        category_label.pack(side="right")
        
        # Description
        desc_label = ctk.CTkLabel(
            content_frame,
            text=activity.get('description', ''),
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT,
            wraplength=400,
            justify="left"
        )
        desc_label.pack(anchor="w", pady=(0, 8))
        
        # Weather suitability
        weather_label = ctk.CTkLabel(
            content_frame,
            text=f"🌤️ {activity.get('weather_suitability', '')}",
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            text_color=DataTerminalTheme.SUCCESS,
            wraplength=400,
            justify="left"
        )
        weather_label.pack(anchor="w", pady=(0, 8))
        
        # Details frame
        details_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        details_frame.pack(fill="x", pady=(0, 10))
        
        # Duration and difficulty
        duration = activity.get('duration', 'Unknown')
        difficulty = activity.get('difficulty', 'Unknown')
        
        details_text = f"⏱️ {duration} | 📊 {difficulty}"
        details_label = ctk.CTkLabel(
            details_frame,
            text=details_text,
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        details_label.pack(side="left")
        
        # Action buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # Like button
        like_btn = ctk.CTkButton(
            button_frame,
            text="👍 Like",
            width=80,
            height=28,
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            fg_color=DataTerminalTheme.SUCCESS,
            hover_color="#2E7D32",
            command=lambda: self._rate_activity(activity, 1)
        )
        like_btn.pack(side="left", padx=(0, 5))
        
        # Dislike button
        dislike_btn = ctk.CTkButton(
            button_frame,
            text="👎 Pass",
            width=80,
            height=28,
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            fg_color=DataTerminalTheme.ERROR,
            hover_color="#C62828",
            command=lambda: self._rate_activity(activity, 0)
        )
        dislike_btn.pack(side="left", padx=(0, 10))
        
        # More info button
        info_btn = ctk.CTkButton(
            button_frame,
            text="ℹ️ Details",
            width=80,
            height=28,
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            fg_color=DataTerminalTheme.CARD_BG,
            hover_color=DataTerminalTheme.HOVER,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
            command=lambda: self._show_activity_details(activity)
        )
        info_btn.pack(side="right")
    
    def _rate_activity(self, activity: Dict, rating: int):
        """Save user rating for an activity."""
        try:
            weather_condition = self.current_weather.get('condition', '') if self.current_weather else ''
            temperature = self.current_weather.get('temperature', 0) if self.current_weather else 0
            
            self.cursor.execute(
                "INSERT INTO activity_preferences (activity_name, category, liked, weather_condition, temperature) VALUES (?, ?, ?, ?, ?)",
                (activity['name'], activity.get('category', ''), rating, weather_condition, temperature)
            )
            self.conn.commit()
            
            # Show feedback
            feedback = "👍 Thanks for the feedback!" if rating == 1 else "👎 We'll suggest different activities"
            self._show_temporary_message(feedback)
            
        except Exception as e:
            print(f"Error saving rating: {e}")
    
    def _show_activity_details(self, activity: Dict):
        """Show detailed information about an activity."""
        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title(f"Activity Details - {activity.get('name', 'Unknown')}")
        popup.geometry("500x600")
        popup.configure(fg_color=DataTerminalTheme.BG)
        
        # Make popup modal
        popup.transient(self)
        popup.grab_set()
        
        # Center popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (500 // 2)
        y = (popup.winfo_screenheight() // 2) - (600 // 2)
        popup.geometry(f"500x600+{x}+{y}")
        
        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(
            popup,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Activity name
        name_label = ctk.CTkLabel(
            scroll_frame,
            text=activity.get('name', 'Unknown Activity'),
            font=(DataTerminalTheme.FONT_FAMILY, 20, "bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        name_label.pack(pady=(0, 15))
        
        # Description
        desc_label = ctk.CTkLabel(
            scroll_frame,
            text=activity.get('description', 'No description available'),
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.TEXT,
            wraplength=450,
            justify="left"
        )
        desc_label.pack(pady=(0, 15))
        
        # Weather suitability
        weather_frame = ctk.CTkFrame(scroll_frame, fg_color=DataTerminalTheme.BG)
        weather_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            weather_frame,
            text="🌤️ Weather Suitability",
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            text_color=DataTerminalTheme.SUCCESS
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            weather_frame,
            text=activity.get('weather_suitability', 'Not specified'),
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT,
            wraplength=430,
            justify="left"
        ).pack(pady=(0, 10))
        
        # Equipment needed
        equipment = activity.get('equipment_needed', [])
        if equipment:
            equipment_frame = ctk.CTkFrame(scroll_frame, fg_color=DataTerminalTheme.BG)
            equipment_frame.pack(fill="x", pady=(0, 15))
            
            ctk.CTkLabel(
                equipment_frame,
                text="🎒 Equipment Needed",
                font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
                text_color=DataTerminalTheme.WARNING
            ).pack(pady=(10, 5))
            
            equipment_text = "• " + "\n• ".join(equipment)
            ctk.CTkLabel(
                equipment_frame,
                text=equipment_text,
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                text_color=DataTerminalTheme.TEXT,
                justify="left"
            ).pack(pady=(0, 10))
        
        # Benefits
        benefits = activity.get('benefits', [])
        if benefits:
            benefits_frame = ctk.CTkFrame(scroll_frame, fg_color=DataTerminalTheme.BG)
            benefits_frame.pack(fill="x", pady=(0, 15))
            
            ctk.CTkLabel(
                benefits_frame,
                text="✨ Benefits",
                font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
                text_color=DataTerminalTheme.PRIMARY
            ).pack(pady=(10, 5))
            
            benefits_text = "• " + "\n• ".join(benefits)
            ctk.CTkLabel(
                benefits_frame,
                text=benefits_text,
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                text_color=DataTerminalTheme.TEXT,
                justify="left"
            ).pack(pady=(0, 10))
        
        # Close button
        close_btn = ctk.CTkButton(
            scroll_frame,
            text="Close",
            width=100,
            height=32,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            fg_color=DataTerminalTheme.PRIMARY,
            command=popup.destroy
        )
        close_btn.pack(pady=20)
    
    def _show_temporary_message(self, message: str):
        """Show a temporary feedback message."""
        # Create temporary label
        temp_label = ctk.CTkLabel(
            self,
            text=message,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.SUCCESS,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=8
        )
        temp_label.place(relx=0.5, rely=0.1, anchor="center")
        
        # Remove after 2 seconds
        self.after(2000, temp_label.destroy)
    
    def _show_error(self):
        """Show error message when suggestions fail to load."""
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()
        
        error_label = ctk.CTkLabel(
            self.suggestions_frame,
            text="❌ Failed to load suggestions\nPlease check your internet connection and try again",
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.ERROR,
            justify="center"
        )
        error_label.pack(pady=50)
        
        self.refresh_btn.configure(state="normal", text="🔄 Refresh")
    
    def update_weather(self, weather_data: Dict):
        """Update weather data and refresh suggestions."""
        self.current_weather = weather_data
        self._update_weather_display()
        # Optionally auto-refresh suggestions when weather updates
        # self._refresh_suggestions()
    
    def __del__(self):
        """Clean up database connection."""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass