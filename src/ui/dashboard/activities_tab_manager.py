import customtkinter as ctk

from src.ui.theme import DataTerminalTheme


class ActivitiesTabManager:
    """Manages activities tab functionality and AI-powered activity suggestions."""

    def __init__(self, parent, activity_service, cache_manager, logger):
        self.parent = parent
        self.activity_service = activity_service
        self.cache_manager = cache_manager
        self.logger = logger
        self.current_weather_data = None
        self.current_city = "Unknown"

    def create_activities_tab(self, activities_tab):
        """Create activities tab content."""
        self.activities_tab = activities_tab
        self._create_activities_tab_content()

    def _create_activities_tab_content(self):
        """Create AI-powered activities tab with improved layout."""
        # Configure main grid
        self.activities_tab.grid_columnconfigure(0, weight=1)
        self.activities_tab.grid_rowconfigure(1, weight=1)

        # Header with better spacing
        header_frame = ctk.CTkFrame(self.activities_tab, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 8))
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header_frame,
            text="🎯 AI Activity Suggestions",
            font=(DataTerminalTheme.FONT_FAMILY, 20, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        title.grid(row=0, column=0, sticky="w", pady=15)

        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Get New Suggestions",
            width=160,
            height=32,
            corner_radius=16,
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.SUCCESS,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            command=self._refresh_activity_suggestions,
        )
        refresh_btn.grid(row=0, column=1, sticky="e", pady=15, padx=(15, 0))

        # Activity cards container with better structure
        self.activities_container = ctk.CTkScrollableFrame(
            self.activities_tab, fg_color="transparent", corner_radius=0
        )
        self.activities_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 15))

        # Configure activities container grid for responsive layout
        self.activities_container.grid_columnconfigure(0, weight=1)
        self.activities_container.grid_columnconfigure(1, weight=1)
        self.activities_container.grid_columnconfigure(2, weight=1)

        # Create sample activity cards
        self._create_sample_activities()

    def _create_sample_activities(self):
        """Create dynamic activity suggestions based on current weather."""
        # Get weather-based activity suggestions
        if self.activity_service and self.current_weather_data:
            try:
                activities = self.activity_service.get_activity_suggestions(
                    self.current_weather_data
                )
            except Exception as e:
                self.logger.error(f"Error getting activity suggestions: {e}")
                activities = self._get_fallback_activities()
        else:
            activities = self._get_fallback_activities()

        # Create activity cards
        self._create_activity_cards(activities)

    def _get_fallback_activities(self):
        """Get fallback activities when weather data or service is unavailable."""
        return [
            {
                "title": "Morning Jog in the Park",
                "category": "Outdoor",
                "icon": "🏃",
                "description": "Perfect weather for a refreshing morning run",
                "time": "30-45 minutes",
                "items": "Running shoes, water bottle",
            },
            {
                "title": "Indoor Yoga Session",
                "category": "Indoor",
                "icon": "🧘",
                "description": "Relaxing yoga to start your day",
                "time": "20-30 minutes",
                "items": "Yoga mat, comfortable clothes",
            },
            {
                "title": "Photography Walk",
                "category": "Outdoor",
                "icon": "📸",
                "description": "Great lighting conditions for photography",
                "time": "1-2 hours",
                "items": "Camera, comfortable shoes",
            },
        ]

    def _create_activity_cards(self, activities):
        """Create activity cards from activities list."""
        # Clear existing cards
        for widget in self.activities_container.winfo_children():
            widget.destroy()

        # Calculate grid layout
        cards_per_row = 3
        for i, activity in enumerate(activities):
            row = i // cards_per_row
            col = i % cards_per_row

            card = ctk.CTkFrame(
                self.activities_container,
                fg_color=DataTerminalTheme.CARD_BG,
                corner_radius=16,
                border_width=1,
                border_color=DataTerminalTheme.BORDER,
                height=200,
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="ew")
            card.grid_propagate(False)

            # Configure card grid
            card.grid_rowconfigure(0, weight=0)  # Header
            card.grid_rowconfigure(1, weight=1)  # Description
            card.grid_rowconfigure(2, weight=0)  # Details
            card.grid_columnconfigure(0, weight=1)

            # Header with icon and title
            header = ctk.CTkFrame(card, fg_color="transparent", height=50)
            header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
            header.grid_propagate(False)
            header.grid_columnconfigure(1, weight=1)

            # Icon
            icon_label = ctk.CTkLabel(
                header, text=activity.get("icon", "🎯"), font=(DataTerminalTheme.FONT_FAMILY, 28)
            )
            icon_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

            # Title
            title_label = ctk.CTkLabel(
                header,
                text=activity.get("title", "Activity"),
                font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
                text_color=DataTerminalTheme.TEXT,
                anchor="w",
            )
            title_label.grid(row=0, column=1, sticky="ew")

            # Category badge
            category_badge = ctk.CTkLabel(
                header,
                text=activity.get("category", "General"),
                fg_color=DataTerminalTheme.PRIMARY,
                corner_radius=10,
                text_color=DataTerminalTheme.BACKGROUND,
                font=(DataTerminalTheme.FONT_FAMILY, 10, "bold"),
                width=60,
                height=20,
            )
            category_badge.grid(row=0, column=2, padx=(10, 0), sticky="e")

            # Description
            desc_label = ctk.CTkLabel(
                card,
                text=activity.get("description", "No description available"),
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                anchor="nw",
                justify="left",
                wraplength=250,
            )
            desc_label.grid(row=1, column=0, sticky="new", padx=15, pady=5)

            # Details
            details_frame = ctk.CTkFrame(card, fg_color="transparent", height=40)
            details_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 15))
            details_frame.grid_propagate(False)
            details_frame.grid_columnconfigure(0, weight=1)
            details_frame.grid_columnconfigure(1, weight=1)

            time_label = ctk.CTkLabel(
                details_frame,
                text=f"⏱️ {activity.get('time', 'Variable')}",
                font=(DataTerminalTheme.FONT_FAMILY, 11),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                anchor="w",
            )
            time_label.grid(row=0, column=0, sticky="w", pady=2)

            items_label = ctk.CTkLabel(
                details_frame,
                text=f"📦 {activity.get('items', 'None required')}",
                font=(DataTerminalTheme.FONT_FAMILY, 11),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                anchor="w",
            )
            items_label.grid(row=1, column=0, sticky="w", pady=2)

    def update_activity_suggestions(self, weather_data):
        """Update activity suggestions based on weather with caching."""
        try:
            self.current_weather_data = weather_data

            # Create cache key based on weather conditions
            cache_key = f"activities_{self.current_city}_{weather_data.get('condition', 'unknown')}_{weather_data.get('temperature', 0)}"

            # Try to get cached suggestions first
            cached_suggestions = self.cache_manager.get(cache_key)
            if cached_suggestions:
                self.logger.debug(f"Using cached activity suggestions for {self.current_city}")
                suggestions = cached_suggestions
            else:
                # Get new suggestions
                if self.activity_service:
                    suggestions = self.activity_service.get_activity_suggestions(weather_data)
                    # Cache the suggestions for 30 minutes
                    self.cache_manager.set(
                        cache_key,
                        suggestions,
                        ttl=1800,  # 30 minutes
                        tags=["activities", f"city_{self.current_city}"],
                    )
                else:
                    suggestions = self._get_fallback_activities()

            # Create cards for suggestions (this method handles clearing existing cards)
            self._create_activity_cards(suggestions)

        except Exception as e:
            self.logger.error(f"Error updating activity suggestions: {e}")
            # Fallback to default activities
            fallback_activities = self._get_fallback_activities()
            self._create_activity_cards(fallback_activities)

    def _refresh_activity_suggestions(self):
        """Refresh activity suggestions when weather data changes."""
        if hasattr(self, "activities_container") and self.activities_container.winfo_exists():
            try:
                # Get updated activity suggestions
                if self.activity_service and self.current_weather_data:
                    activities = self.activity_service.get_activity_suggestions(
                        self.current_weather_data
                    )
                else:
                    activities = self._get_fallback_activities()

                # Update the activity cards
                self._create_activity_cards(activities)
            except Exception as e:
                self.logger.error(f"Error refreshing activity suggestions: {e}")

    def set_current_city(self, city):
        """Set the current city for activity suggestions."""
        self.current_city = city

    def set_weather_data(self, weather_data):
        """Set the current weather data for activity suggestions."""
        self.current_weather_data = weather_data
        self.update_activity_suggestions(weather_data)
