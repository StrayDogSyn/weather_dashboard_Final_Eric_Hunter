
from src.ui.theme import DataTerminalTheme
from src.ui.safe_widgets import SafeCTkFrame, SafeCTkLabel, SafeCTkButton, SafeCTkScrollableFrame
from src.ui.components.glassmorphic import GlassmorphicFrame, GlassButton, GlassPanel
import customtkinter as ctk


class ActivitiesTabManager:
    """Manages activities tab functionality and AI-powered activity suggestions."""

    def __init__(self, parent, activity_service, cache_manager, logger):
        self.parent = parent
        self.activity_service = activity_service
        self.cache_manager = cache_manager
        self.logger = logger
        self.current_weather_data = None
        self.current_city = "Unknown"
        
        # Flag to prevent stale callbacks during UI refresh
        self.is_refreshing_activities = False

    def create_activities_tab(self, activities_tab):
        """Create activities tab content."""
        self.activities_tab = activities_tab
        self._create_activities_tab_content()

    def _create_activities_tab_content(self):
        """Create AI-powered activities tab with glassmorphic design."""
        # Configure main grid
        self.activities_tab.grid_columnconfigure(0, weight=1)
        self.activities_tab.grid_rowconfigure(1, weight=1)

        # Main glassmorphic container
        self.main_container = GlassPanel(
            self.activities_tab,
            width=800,
            height=600,
            glass_opacity=0.05
        )
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # Create glassmorphic header
        self._create_glassmorphic_header()

        # Activity cards container with glassmorphic styling
        self.activities_container = ctk.CTkScrollableFrame(
            self.main_container, 
            fg_color="transparent", 
            corner_radius=0
        )
        self.activities_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Configure activities container grid for responsive layout
        self.activities_container.grid_columnconfigure(0, weight=1)
        self.activities_container.grid_columnconfigure(1, weight=1)
        self.activities_container.grid_columnconfigure(2, weight=1)

        # Create sample activity cards
        self._create_sample_activities()

    def _create_glassmorphic_header(self):
        """Create glassmorphic header with filters and title."""
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        # Title with glow effect
        title = ctk.CTkLabel(
            header_frame,
            text="🌟 AI-Powered Activity Suggestions",
            font=("Arial", 24, "bold"),
            text_color="#00D4FF"
        )
        title.grid(row=0, column=0, sticky="w")

        # Filter buttons with glass effect
        filter_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        filter_frame.grid(row=0, column=2, sticky="e")

        filters = ["All Activities", "Outdoor", "Indoor", "Social", "Fitness"]
        for i, filter_name in enumerate(filters):
            btn = GlassButton(
                filter_frame,
                text=filter_name,
                width=100,
                height=32,
                command=lambda f=filter_name: self.apply_filter(f)
            )
            btn.grid(row=0, column=i, padx=5)

    def apply_filter(self, filter_name):
        """Apply activity filter."""
        # Placeholder for filter functionality
        self.logger.debug(f"Applied filter: {filter_name}")

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
        """Create activity cards from activities list using safe two-phase update."""
        # Set flag to prevent stale callbacks during refresh
        self.is_refreshing_activities = True
        
        try:
            # Phase 1: Cancel any pending scheduled operations that might target widgets
            if hasattr(self, '_cleanup_scheduled_calls'):
                self._cleanup_scheduled_calls()
            
            # Clear existing cards
            for widget in self.activities_container.winfo_children():
                widget.destroy()
            
            # CRITICAL: Force Tkinter to process all widget destructions NOW
            # This ensures the container is truly empty before we add new widgets
            self.activities_container.update_idletasks()

            # Calculate grid layout
            cards_per_row = 3
            for i, activity in enumerate(activities):
                row = i // cards_per_row
                col = i % cards_per_row

                # Create glassmorphic activity card
                card = GlassPanel(
                    self.activities_container,
                    width=280,
                    height=200,
                    glass_opacity=0.1
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
                    header, 
                    text=activity.get("icon", "🎯"), 
                    font=("Arial", 32)
                )
                icon_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

                # Title
                title_label = ctk.CTkLabel(
                    header,
                    text=activity.get("title", "Activity"),
                    font=("Arial", 18, "bold"),
                    text_color="#FFFFFF",
                    anchor="w"
                )
                title_label.grid(row=0, column=1, sticky="ew")

                # Description with semi-transparent background
                desc_frame = ctk.CTkFrame(
                    card,
                    fg_color="#FFFFFF0D",
                    corner_radius=10
                )
                desc_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

                desc_label = ctk.CTkLabel(
                    desc_frame,
                    text=activity.get("description", "No description available"),
                    font=("Arial", 12),
                    text_color="#FFFFFFB3",
                    wraplength=250,
                    justify="left"
                )
                desc_label.pack(padx=10, pady=10)

                # Action buttons with glassmorphic styling
                self._create_card_actions(card, activity)

    def _create_card_actions(self, card, activity_data):
        """Create glassmorphic action buttons for activity card."""
        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        # Start Activity button
        start_btn = GlassButton(
            button_frame,
            text="▶️ Start",
            width=100,
            height=32,
            command=lambda: self._start_activity(activity_data)
        )
        start_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        # More Info button
        info_btn = GlassButton(
            button_frame,
            text="ℹ️ Info",
            width=100,
            height=32,
            command=lambda: self._show_activity_info(activity_data)
        )
        info_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _start_activity(self, activity_data):
        """Start the selected activity."""
        self.logger.info(f"Starting activity: {activity_data.get('title', 'Unknown')}")
        # Placeholder for activity start functionality

    def _show_activity_info(self, activity_data):
        """Show detailed information about the activity."""
        self.logger.info(f"Showing info for activity: {activity_data.get('title', 'Unknown')}")
        # Placeholder for activity info functionality
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error creating activity cards: {e}")
        finally:
            # Always reset the flag
            self.is_refreshing_activities = False

    def update_activity_suggestions(self, weather_data):
        """Update activity suggestions based on weather with caching."""
        # STEP 3 DEBUG: Implement thread-safe UI updates
        
        # Check if UI is currently being refreshed - if so, discard this update
        if getattr(self, 'is_refreshing_activities', False):
            self.logger.debug("Discarding activity update - UI is currently being refreshed")
            return
            
        def _safe_update():
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
                    # Generate new suggestions
                    if self.activity_service:
                        suggestions = self.activity_service.get_activity_suggestions(weather_data)
                        # Cache the suggestions for 30 minutes
                        self.cache_manager.set(cache_key, suggestions, ttl=1800)
                        self.logger.debug(f"Generated and cached new activity suggestions for {self.current_city}")
                    else:
                        suggestions = self._get_fallback_activities()

                # Create cards for suggestions (this method handles clearing existing cards)
                self._create_activity_cards(suggestions)

            except Exception as e:
                self.logger.error(f"Error updating activity suggestions: {e}")
                # Fallback to default activities
                fallback_activities = self._get_fallback_activities()
                self._create_activity_cards(fallback_activities)
        
        # Schedule UI update on main thread using safe_after_idle
        if hasattr(self.activities_container, 'safe_after_idle'):
            self.activities_container.safe_after_idle(_safe_update)
        else:
            # Fallback to regular after_idle if SafeWidget not available
            try:
                if self.activities_container.winfo_exists():
                    self.activities_container.after_idle(_safe_update)
            except Exception as e:
                self.logger.error(f"Failed to schedule UI update: {e}")

    def _refresh_activity_suggestions(self):
        """Refresh activity suggestions when weather data changes."""
        # STEP 3 DEBUG: Implement thread-safe UI updates
        
        # Check if UI is currently being refreshed - if so, discard this update
        if getattr(self, 'is_refreshing_activities', False):
            self.logger.debug("Discarding activity refresh - UI is currently being updated")
            return
            
        def _safe_refresh():
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
        
        # Schedule UI refresh on main thread using safe_after_idle
        if hasattr(self, "activities_container") and hasattr(self.activities_container, 'safe_after_idle'):
            self.activities_container.safe_after_idle(_safe_refresh)
        else:
            # Fallback to regular after_idle if SafeWidget not available
            try:
                if hasattr(self, "activities_container") and self.activities_container.winfo_exists():
                    self.activities_container.after_idle(_safe_refresh)
            except Exception as e:
                self.logger.error(f"Failed to schedule UI refresh: {e}")

    def set_current_city(self, city):
        """Set the current city for activity suggestions."""
        self.current_city = city

    def set_weather_data(self, weather_data):
        """Set the current weather data for activity suggestions."""
        self.current_weather_data = weather_data
        self.update_activity_suggestions(weather_data)
