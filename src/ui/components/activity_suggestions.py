"""AI-powered activity suggester component with glassmorphic styling."""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from models.activity_models import (
    ActivitySuggestion, UserPreferences, TimeContext, ActivityCategory,
    ActivityPlan, EQUIPMENT_CATEGORIES, DIFFICULTY_DESCRIPTIONS
)
from models.weather_models import WeatherData
from services.gemini_service import GeminiService
from services.config_service import ConfigService
from ..theme import DataTerminalTheme


class ActivitySuggesterComponent(ctk.CTkFrame):
    """AI-powered activity suggester with comprehensive features."""
    
    def __init__(
        self,
        parent,
        gemini_service: GeminiService,
        config_service: ConfigService,
        weather_data: Optional[WeatherData] = None
    ):
        """Initialize activity suggester component.
        
        Args:
            parent: Parent widget
            gemini_service: Gemini AI service
            config_service: Configuration service
            weather_data: Current weather data
        """
        super().__init__(parent, fg_color="transparent")
        
        self.gemini_service = gemini_service
        self.config_service = config_service
        self.weather_data = weather_data
        
        # State management
        self.current_suggestions: List[ActivitySuggestion] = []
        self.user_preferences = self._load_user_preferences()
        self.activity_plans: List[ActivityPlan] = []
        self.selected_filters = {
            'categories': set(),
            'indoor_only': False,
            'max_duration': 120,
            'max_difficulty': 5,
            'cost_range': 'all'
        }
        
        # UI components
        self.suggestion_cards = []
        self.filter_widgets = {}
        
        # Setup UI
        self._setup_ui()
        self._load_initial_suggestions()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header section
        self._create_header()
        
        # Main content area
        self._create_main_content()
        
        # Apply theme
        self._apply_theme()
    
    def _create_header(self):
        """Create header with title and controls."""
        header_frame = ctk.CTkFrame(
            self,
            height=80,
            fg_color=DataTerminalTheme.SURFACE_COLOR,
            corner_radius=15
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title with AI icon
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        ai_label = ctk.CTkLabel(
            title_frame,
            text="🤖",
            font=ctk.CTkFont(size=24)
        )
        ai_label.pack(side="left", padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="AI Activity Suggestions",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY_COLOR
        )
        title_label.pack(side="left")
        
        # Control buttons
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=2, sticky="e", padx=20, pady=15)
        
        self.refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Refresh",
            width=100,
            height=35,
            fg_color=DataTerminalTheme.ACCENT_COLOR,
            hover_color=DataTerminalTheme.HOVER_COLOR,
            command=self._refresh_suggestions
        )
        self.refresh_btn.pack(side="right", padx=(10, 0))
        
        self.preferences_btn = ctk.CTkButton(
            controls_frame,
            text="⚙️ Preferences",
            width=120,
            height=35,
            fg_color=DataTerminalTheme.SECONDARY_COLOR,
            hover_color=DataTerminalTheme.HOVER_COLOR,
            command=self._open_preferences
        )
        self.preferences_btn.pack(side="right")
    
    def _create_main_content(self):
        """Create main content area with filters and suggestions."""
        main_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left sidebar - Filters
        self._create_filters_sidebar(main_frame)
        
        # Right content - Suggestions
        self._create_suggestions_area(main_frame)
    
    def _create_filters_sidebar(self, parent):
        """Create filters sidebar."""
        filters_frame = ctk.CTkFrame(
            parent,
            width=280,
            fg_color=DataTerminalTheme.SURFACE_COLOR,
            corner_radius=15
        )
        filters_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10), pady=5)
        filters_frame.grid_propagate(False)
        
        # Filters title
        filters_title = ctk.CTkLabel(
            filters_frame,
            text="🎯 Filters",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY_COLOR
        )
        filters_title.pack(pady=(15, 10))
        
        # Scrollable frame for filters
        filters_scroll = ctk.CTkScrollableFrame(
            filters_frame,
            fg_color="transparent"
        )
        filters_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Category filters
        self._create_category_filters(filters_scroll)
        
        # Duration filter
        self._create_duration_filter(filters_scroll)
        
        # Difficulty filter
        self._create_difficulty_filter(filters_scroll)
        
        # Indoor/Outdoor filter
        self._create_location_filter(filters_scroll)
        
        # Cost filter
        self._create_cost_filter(filters_scroll)
        
        # Apply filters button
        apply_btn = ctk.CTkButton(
            filters_scroll,
            text="Apply Filters",
            fg_color=DataTerminalTheme.ACCENT_COLOR,
            hover_color=DataTerminalTheme.HOVER_COLOR,
            command=self._apply_filters
        )
        apply_btn.pack(pady=(20, 10), fill="x")
    
    def _create_category_filters(self, parent):
        """Create category filter checkboxes."""
        category_frame = ctk.CTkFrame(parent, fg_color="transparent")
        category_frame.pack(fill="x", pady=(0, 15))
        
        category_label = ctk.CTkLabel(
            category_frame,
            text="Categories",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=DataTerminalTheme.TEXT_COLOR
        )
        category_label.pack(anchor="w", pady=(0, 5))
        
        self.category_vars = {}
        for category in ActivityCategory:
            var = tk.BooleanVar()
            checkbox = ctk.CTkCheckBox(
                category_frame,
                text=category.value.title(),
                variable=var,
                text_color=DataTerminalTheme.TEXT_COLOR,
                fg_color=DataTerminalTheme.ACCENT_COLOR,
                hover_color=DataTerminalTheme.HOVER_COLOR
            )
            checkbox.pack(anchor="w", pady=2)
            self.category_vars[category] = var
    
    def _create_duration_filter(self, parent):
        """Create duration filter slider."""
        duration_frame = ctk.CTkFrame(parent, fg_color="transparent")
        duration_frame.pack(fill="x", pady=(0, 15))
        
        duration_label = ctk.CTkLabel(
            duration_frame,
            text="Max Duration (minutes)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=DataTerminalTheme.TEXT_COLOR
        )
        duration_label.pack(anchor="w", pady=(0, 5))
        
        self.duration_var = tk.IntVar(value=120)
        self.duration_slider = ctk.CTkSlider(
            duration_frame,
            from_=15,
            to=240,
            number_of_steps=15,
            variable=self.duration_var,
            fg_color=DataTerminalTheme.SURFACE_COLOR,
            progress_color=DataTerminalTheme.ACCENT_COLOR,
            button_color=DataTerminalTheme.PRIMARY_COLOR
        )
        self.duration_slider.pack(fill="x", pady=(0, 5))
        
        self.duration_value_label = ctk.CTkLabel(
            duration_frame,
            text="120 minutes",
            text_color=DataTerminalTheme.TEXT_COLOR
        )
        self.duration_value_label.pack(anchor="w")
        
        # Update label when slider changes
        self.duration_slider.configure(
            command=lambda value: self.duration_value_label.configure(
                text=f"{int(value)} minutes"
            )
        )
    
    def _create_difficulty_filter(self, parent):
        """Create difficulty filter slider."""
        difficulty_frame = ctk.CTkFrame(parent, fg_color="transparent")
        difficulty_frame.pack(fill="x", pady=(0, 15))
        
        difficulty_label = ctk.CTkLabel(
            difficulty_frame,
            text="Max Difficulty",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=DataTerminalTheme.TEXT_COLOR
        )
        difficulty_label.pack(anchor="w", pady=(0, 5))
        
        self.difficulty_var = tk.IntVar(value=5)
        self.difficulty_slider = ctk.CTkSlider(
            difficulty_frame,
            from_=1,
            to=5,
            number_of_steps=4,
            variable=self.difficulty_var,
            fg_color=DataTerminalTheme.SURFACE_COLOR,
            progress_color=DataTerminalTheme.ACCENT_COLOR,
            button_color=DataTerminalTheme.PRIMARY_COLOR
        )
        self.difficulty_slider.pack(fill="x", pady=(0, 5))
        
        self.difficulty_value_label = ctk.CTkLabel(
            difficulty_frame,
            text="5 - Very Hard",
            text_color=DataTerminalTheme.TEXT_COLOR
        )
        self.difficulty_value_label.pack(anchor="w")
        
        # Update label when slider changes
        self.difficulty_slider.configure(
            command=lambda value: self.difficulty_value_label.configure(
                text=f"{int(value)} - {DIFFICULTY_DESCRIPTIONS[int(value)].split(' - ')[1]}"
            )
        )
    
    def _create_location_filter(self, parent):
        """Create indoor/outdoor filter."""
        location_frame = ctk.CTkFrame(parent, fg_color="transparent")
        location_frame.pack(fill="x", pady=(0, 15))
        
        location_label = ctk.CTkLabel(
            location_frame,
            text="Location Preference",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=DataTerminalTheme.TEXT_COLOR
        )
        location_label.pack(anchor="w", pady=(0, 5))
        
        self.location_var = tk.StringVar(value="both")
        
        location_options = [
            ("Both Indoor & Outdoor", "both"),
            ("Indoor Only", "indoor"),
            ("Outdoor Only", "outdoor")
        ]
        
        for text, value in location_options:
            radio = ctk.CTkRadioButton(
                location_frame,
                text=text,
                variable=self.location_var,
                value=value,
                text_color=DataTerminalTheme.TEXT_COLOR,
                fg_color=DataTerminalTheme.ACCENT_COLOR,
                hover_color=DataTerminalTheme.HOVER_COLOR
            )
            radio.pack(anchor="w", pady=2)
    
    def _create_cost_filter(self, parent):
        """Create cost filter dropdown."""
        cost_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cost_frame.pack(fill="x", pady=(0, 15))
        
        cost_label = ctk.CTkLabel(
            cost_frame,
            text="Cost Range",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=DataTerminalTheme.TEXT_COLOR
        )
        cost_label.pack(anchor="w", pady=(0, 5))
        
        self.cost_var = tk.StringVar(value="all")
        self.cost_dropdown = ctk.CTkOptionMenu(
            cost_frame,
            values=["All Costs", "Free Only", "Low Cost", "Medium Cost", "High Cost"],
            variable=self.cost_var,
            fg_color=DataTerminalTheme.SURFACE_COLOR,
            button_color=DataTerminalTheme.ACCENT_COLOR,
            button_hover_color=DataTerminalTheme.HOVER_COLOR
        )
        self.cost_dropdown.pack(fill="x")
    
    def _create_suggestions_area(self, parent):
        """Create suggestions display area."""
        suggestions_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        suggestions_frame.grid(row=0, column=1, sticky="nsew", pady=5)
        suggestions_frame.grid_rowconfigure(0, weight=1)
        suggestions_frame.grid_columnconfigure(0, weight=1)
        
        # Suggestions header
        suggestions_header = ctk.CTkFrame(
            suggestions_frame,
            height=60,
            fg_color=DataTerminalTheme.SURFACE_COLOR,
            corner_radius=15
        )
        suggestions_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        suggestions_header.grid_propagate(False)
        suggestions_header.grid_columnconfigure(1, weight=1)
        
        suggestions_title = ctk.CTkLabel(
            suggestions_header,
            text="💡 Personalized Suggestions",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY_COLOR
        )
        suggestions_title.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        # Weather info
        if self.weather_data:
            weather_info = ctk.CTkLabel(
                suggestions_header,
                text=f"🌤️ {self.weather_data.temperature}°C, {self.weather_data.condition}",
                font=ctk.CTkFont(size=12),
                text_color=DataTerminalTheme.TEXT_COLOR
            )
            weather_info.grid(row=0, column=1, sticky="e", padx=20, pady=15)
        
        # Scrollable suggestions area
        self.suggestions_scroll = ctk.CTkScrollableFrame(
            suggestions_frame,
            fg_color="transparent"
        )
        self.suggestions_scroll.grid(row=1, column=0, sticky="nsew")
        self.suggestions_scroll.grid_columnconfigure(0, weight=1)
    
    def _apply_theme(self):
        """Apply Data Terminal theme to components."""
        # Theme is applied during component creation
        pass
    
    def _load_user_preferences(self) -> UserPreferences:
        """Load user preferences from storage."""
        try:
            prefs_file = Path("data/user_preferences.json")
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    data = json.load(f)
                return UserPreferences.from_dict(data)
        except Exception as e:
            print(f"Error loading user preferences: {e}")
        
        # Return default preferences
        return UserPreferences(
            favorite_categories=[ActivityCategory.FITNESS, ActivityCategory.OUTDOOR],
            fitness_level=3,
            budget_range="free",
            equipment_available=["comfortable shoes", "water bottle"],
            time_availability=60,
            indoor_preference=0.3
        )
    
    def _save_user_preferences(self):
        """Save user preferences to storage."""
        try:
            prefs_file = Path("data/user_preferences.json")
            prefs_file.parent.mkdir(exist_ok=True)
            
            with open(prefs_file, 'w') as f:
                json.dump(self.user_preferences.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving user preferences: {e}")
    
    def _load_initial_suggestions(self):
        """Load initial activity suggestions."""
        if self.weather_data:
            asyncio.create_task(self._generate_suggestions())
        else:
            self._show_placeholder_suggestions()
    
    async def _generate_suggestions(self):
        """Generate AI-powered activity suggestions."""
        try:
            time_context = TimeContext(
                available_minutes=self.user_preferences.time_availability
            )
            
            suggestions = await self.gemini_service.generate_activity_suggestions(
                self.weather_data,
                self.user_preferences,
                time_context
            )
            
            self.current_suggestions = suggestions
            self._display_suggestions(suggestions)
            
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            self._show_error_message("Failed to generate AI suggestions")
    
    def _show_placeholder_suggestions(self):
        """Show placeholder suggestions when weather data is unavailable."""
        placeholder_suggestions = [
            ActivitySuggestion(
                id="placeholder_1",
                title="Morning Yoga",
                description="Start your day with gentle yoga stretches. Perfect for flexibility and mindfulness.",
                category=ActivityCategory.FITNESS,
                indoor=True,
                duration_minutes=30,
                difficulty_level=2,
                equipment_needed=["yoga mat"],
                weather_suitability={'current': 1.0},
                cost_estimate="free",
                safety_considerations=["Use proper form"]
            ),
            ActivitySuggestion(
                id="placeholder_2",
                title="Nature Photography",
                description="Capture the beauty of your surroundings. Great for creativity and outdoor exploration.",
                category=ActivityCategory.CREATIVE,
                indoor=False,
                duration_minutes=60,
                difficulty_level=1,
                equipment_needed=["camera or phone"],
                weather_suitability={'current': 0.8},
                cost_estimate="free",
                safety_considerations=["Watch your surroundings"]
            )
        ]
        
        self.current_suggestions = placeholder_suggestions
        self._display_suggestions(placeholder_suggestions)
    
    def _display_suggestions(self, suggestions: List[ActivitySuggestion]):
        """Display activity suggestions in the UI."""
        # Clear existing suggestions
        for widget in self.suggestions_scroll.winfo_children():
            widget.destroy()
        
        self.suggestion_cards = []
        
        if not suggestions:
            self._show_no_suggestions_message()
            return
        
        # Create suggestion cards
        for i, suggestion in enumerate(suggestions):
            card = self._create_suggestion_card(suggestion, i)
            card.grid(row=i, column=0, sticky="ew", pady=10, padx=10)
            self.suggestion_cards.append(card)
    
    def _create_suggestion_card(self, suggestion: ActivitySuggestion, index: int) -> ctk.CTkFrame:
        """Create a suggestion card with glassmorphic styling."""
        card = ctk.CTkFrame(
            self.suggestions_scroll,
            fg_color=DataTerminalTheme.SURFACE_COLOR,
            corner_radius=15,
            border_width=1,
            border_color=DataTerminalTheme.ACCENT_COLOR
        )
        card.grid_columnconfigure(1, weight=1)
        
        # Category icon and indoor/outdoor indicator
        icon_frame = ctk.CTkFrame(card, fg_color="transparent", width=80)
        icon_frame.grid(row=0, column=0, rowspan=3, sticky="ns", padx=15, pady=15)
        icon_frame.grid_propagate(False)
        
        # Category icon
        category_icons = {
            ActivityCategory.FITNESS: "💪",
            ActivityCategory.OUTDOOR: "🌲",
            ActivityCategory.CREATIVE: "🎨",
            ActivityCategory.SOCIAL: "👥",
            ActivityCategory.RELAXATION: "🧘",
            ActivityCategory.EDUCATIONAL: "📚",
            ActivityCategory.ENTERTAINMENT: "🎭",
            ActivityCategory.SPORTS: "⚽",
            ActivityCategory.ADVENTURE: "🏔️",
            ActivityCategory.CULTURAL: "🏛️"
        }
        
        icon_label = ctk.CTkLabel(
            icon_frame,
            text=category_icons.get(suggestion.category, "🎯"),
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=(10, 5))
        
        # Indoor/outdoor indicator
        location_indicator = ctk.CTkLabel(
            icon_frame,
            text="🏠" if suggestion.indoor else "🌤️",
            font=ctk.CTkFont(size=16)
        )
        location_indicator.pack()
        
        # Main content
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.grid(row=0, column=1, sticky="ew", padx=(0, 15), pady=15)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Title and difficulty
        title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=suggestion.title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY_COLOR,
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Difficulty stars
        difficulty_stars = "⭐" * suggestion.difficulty_level + "☆" * (5 - suggestion.difficulty_level)
        difficulty_label = ctk.CTkLabel(
            title_frame,
            text=difficulty_stars,
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.ACCENT_COLOR
        )
        difficulty_label.grid(row=0, column=1, sticky="e")
        
        # Description
        desc_label = ctk.CTkLabel(
            content_frame,
            text=suggestion.description,
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT_COLOR,
            anchor="w",
            justify="left",
            wraplength=400
        )
        desc_label.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # Details row
        details_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        details_frame.grid(row=2, column=0, sticky="ew")
        
        # Duration
        duration_label = ctk.CTkLabel(
            details_frame,
            text=f"⏱️ {suggestion.duration_minutes}min",
            font=ctk.CTkFont(size=11),
            text_color=DataTerminalTheme.TEXT_COLOR
        )
        duration_label.pack(side="left", padx=(0, 15))
        
        # Cost
        cost_label = ctk.CTkLabel(
            details_frame,
            text=f"💰 {suggestion.cost_estimate.title()}",
            font=ctk.CTkFont(size=11),
            text_color=DataTerminalTheme.TEXT_COLOR
        )
        cost_label.pack(side="left", padx=(0, 15))
        
        # Weather suitability
        suitability = suggestion.get_suitability_score()
        suitability_color = DataTerminalTheme.ACCENT_COLOR if suitability > 0.7 else DataTerminalTheme.WARNING_COLOR
        suitability_label = ctk.CTkLabel(
            details_frame,
            text=f"🌤️ {int(suitability * 100)}%",
            font=ctk.CTkFont(size=11),
            text_color=suitability_color
        )
        suitability_label.pack(side="left")
        
        # Action buttons
        actions_frame = ctk.CTkFrame(card, fg_color="transparent", width=120)
        actions_frame.grid(row=0, column=2, rowspan=3, sticky="ns", padx=15, pady=15)
        actions_frame.grid_propagate(False)
        
        # Plan button
        plan_btn = ctk.CTkButton(
            actions_frame,
            text="📅 Plan",
            width=100,
            height=30,
            fg_color=DataTerminalTheme.ACCENT_COLOR,
            hover_color=DataTerminalTheme.HOVER_COLOR,
            command=lambda: self._plan_activity(suggestion)
        )
        plan_btn.pack(pady=(0, 5))
        
        # Rate button
        rate_btn = ctk.CTkButton(
            actions_frame,
            text="⭐ Rate",
            width=100,
            height=30,
            fg_color=DataTerminalTheme.SECONDARY_COLOR,
            hover_color=DataTerminalTheme.HOVER_COLOR,
            command=lambda: self._rate_activity(suggestion)
        )
        rate_btn.pack(pady=(0, 5))
        
        # More info button
        info_btn = ctk.CTkButton(
            actions_frame,
            text="ℹ️ Info",
            width=100,
            height=30,
            fg_color=DataTerminalTheme.SURFACE_COLOR,
            hover_color=DataTerminalTheme.HOVER_COLOR,
            border_width=1,
            border_color=DataTerminalTheme.ACCENT_COLOR,
            command=lambda: self._show_activity_details(suggestion)
        )
        info_btn.pack()
        
        return card
    
    def _show_no_suggestions_message(self):
        """Show message when no suggestions are available."""
        message_frame = ctk.CTkFrame(
            self.suggestions_scroll,
            fg_color=DataTerminalTheme.SURFACE_COLOR,
            corner_radius=15
        )
        message_frame.grid(row=0, column=0, sticky="ew", pady=20, padx=20)
        
        message_label = ctk.CTkLabel(
            message_frame,
            text="🤔 No activities match your current filters.\nTry adjusting your preferences or refresh for new suggestions.",
            font=ctk.CTkFont(size=14),
            text_color=DataTerminalTheme.TEXT_COLOR,
            justify="center"
        )
        message_label.pack(pady=40)
    
    def _show_error_message(self, message: str):
        """Show error message."""
        error_frame = ctk.CTkFrame(
            self.suggestions_scroll,
            fg_color=DataTerminalTheme.ERROR_COLOR,
            corner_radius=15
        )
        error_frame.grid(row=0, column=0, sticky="ew", pady=20, padx=20)
        
        error_label = ctk.CTkLabel(
            error_frame,
            text=f"❌ {message}",
            font=ctk.CTkFont(size=14),
            text_color="white"
        )
        error_label.pack(pady=20)
    
    # Event handlers
    def _refresh_suggestions(self):
        """Refresh activity suggestions."""
        if self.weather_data:
            asyncio.create_task(self._generate_suggestions())
        else:
            self._show_placeholder_suggestions()
    
    def _apply_filters(self):
        """Apply current filters to suggestions."""
        # Update selected filters
        self.selected_filters['categories'] = {
            cat for cat, var in self.category_vars.items() if var.get()
        }
        self.selected_filters['max_duration'] = self.duration_var.get()
        self.selected_filters['max_difficulty'] = self.difficulty_var.get()
        self.selected_filters['location_preference'] = self.location_var.get()
        self.selected_filters['cost_range'] = self.cost_var.get().lower().replace(' only', '').replace(' cost', '')
        
        # Filter current suggestions
        filtered_suggestions = self._filter_suggestions(self.current_suggestions)
        self._display_suggestions(filtered_suggestions)
    
    def _filter_suggestions(self, suggestions: List[ActivitySuggestion]) -> List[ActivitySuggestion]:
        """Filter suggestions based on current filters."""
        filtered = []
        
        for suggestion in suggestions:
            # Category filter
            if (self.selected_filters['categories'] and 
                suggestion.category not in self.selected_filters['categories']):
                continue
            
            # Duration filter
            if suggestion.duration_minutes > self.selected_filters['max_duration']:
                continue
            
            # Difficulty filter
            if suggestion.difficulty_level > self.selected_filters['max_difficulty']:
                continue
            
            # Location filter
            location_pref = self.selected_filters['location_preference']
            if location_pref == 'indoor' and not suggestion.indoor:
                continue
            if location_pref == 'outdoor' and suggestion.indoor:
                continue
            
            # Cost filter
            cost_filter = self.selected_filters['cost_range']
            if cost_filter != 'all' and suggestion.cost_estimate != cost_filter:
                continue
            
            filtered.append(suggestion)
        
        return filtered
    
    def _plan_activity(self, suggestion: ActivitySuggestion):
        """Plan an activity for later."""
        # Create activity plan dialog
        dialog = ActivityPlanDialog(self, suggestion)
        plan = dialog.get_plan()
        
        if plan:
            self.activity_plans.append(plan)
            messagebox.showinfo("Activity Planned", f"'{suggestion.title}' has been added to your activity plan!")
    
    def _rate_activity(self, suggestion: ActivitySuggestion):
        """Rate an activity."""
        dialog = ActivityRatingDialog(self, suggestion)
        rating = dialog.get_rating()
        
        if rating:
            suggestion.user_rating = rating
            self.user_preferences.add_activity_rating(suggestion.id, rating)
            self._save_user_preferences()
            messagebox.showinfo("Rating Saved", f"Thank you for rating '{suggestion.title}'!")
    
    def _show_activity_details(self, suggestion: ActivitySuggestion):
        """Show detailed activity information."""
        dialog = ActivityDetailsDialog(self, suggestion)
        dialog.show()
    
    def _open_preferences(self):
        """Open user preferences dialog."""
        dialog = UserPreferencesDialog(self, self.user_preferences)
        updated_prefs = dialog.get_preferences()
        
        if updated_prefs:
            self.user_preferences = updated_prefs
            self._save_user_preferences()
            self._refresh_suggestions()
    
    # Public methods
    def update_weather_data(self, weather_data: WeatherData):
        """Update weather data and refresh suggestions."""
        self.weather_data = weather_data
        self._refresh_suggestions()
    
    def get_activity_plans(self) -> List[ActivityPlan]:
        """Get current activity plans."""
        return self.activity_plans.copy()
    
    def clear_activity_plans(self):
        """Clear all activity plans."""
        self.activity_plans.clear()


# Dialog classes for various interactions
class ActivityPlanDialog:
    """Dialog for planning activities."""
    
    def __init__(self, parent, suggestion: ActivitySuggestion):
        self.parent = parent
        self.suggestion = suggestion
        self.result = None
    
    def get_plan(self) -> Optional[ActivityPlan]:
        """Get activity plan from user input."""
        # Simplified implementation - in real app, would show proper dialog
        from datetime import datetime, timedelta
        
        plan = ActivityPlan(
            id=f"plan_{datetime.now().timestamp()}",
            activity_suggestion=self.suggestion,
            planned_date=datetime.now() + timedelta(hours=1),
            planned_duration=self.suggestion.duration_minutes,
            notes="Planned via AI suggestions"
        )
        
        return plan


class ActivityRatingDialog:
    """Dialog for rating activities."""
    
    def __init__(self, parent, suggestion: ActivitySuggestion):
        self.parent = parent
        self.suggestion = suggestion
        self.result = None
    
    def get_rating(self) -> Optional[int]:
        """Get activity rating from user."""
        # Simplified implementation - in real app, would show proper dialog
        return 4  # Default rating


class ActivityDetailsDialog:
    """Dialog for showing activity details."""
    
    def __init__(self, parent, suggestion: ActivitySuggestion):
        self.parent = parent
        self.suggestion = suggestion
    
    def show(self):
        """Show activity details."""
        # Simplified implementation - in real app, would show proper dialog
        details = f"""
Activity: {self.suggestion.title}
Category: {self.suggestion.category.value.title()}
Duration: {self.suggestion.duration_minutes} minutes
Difficulty: {self.suggestion.difficulty_level}/5
Location: {'Indoor' if self.suggestion.indoor else 'Outdoor'}
Cost: {self.suggestion.cost_estimate.title()}

Description:
{self.suggestion.description}

Equipment Needed:
{', '.join(self.suggestion.equipment_needed) if self.suggestion.equipment_needed else 'None'}

Safety Considerations:
{chr(10).join(f'• {item}' for item in self.suggestion.safety_considerations) if self.suggestion.safety_considerations else 'None'}
"""
        
        messagebox.showinfo("Activity Details", details)


class UserPreferencesDialog:
    """Dialog for editing user preferences."""
    
    def __init__(self, parent, preferences: UserPreferences):
        self.parent = parent
        self.preferences = preferences
        self.result = None
    
    def get_preferences(self) -> Optional[UserPreferences]:
        """Get updated user preferences."""
        # Simplified implementation - in real app, would show proper dialog
        return self.preferences