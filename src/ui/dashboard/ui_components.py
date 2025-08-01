"""UI Components Mixin

Contains all UI creation and layout methods for the dashboard.
"""

import customtkinter as ctk
from ..theme import DataTerminalTheme


class UIComponentsMixin:
    """Mixin class containing UI component creation methods."""
    
    def _configure_window(self) -> None:
        """Configure main window properties with enhanced styling."""
        self.title("🌤️ Professional Weather Dashboard - CodeFront Analytics")
        self.configure(fg_color=self.BACKGROUND)
        
        # Set window icon if available
        try:
            self.iconbitmap("assets/weather_icon.ico")
        except Exception:
            pass  # Icon file not found, continue without it
        
        # Configure window size and position with better defaults
        self.center_window()
        
        # Configure grid weights for responsive design with status bar
        self.grid_rowconfigure(0, weight=0)  # Status bar
        self.grid_rowconfigure(1, weight=0)  # Header
        self.grid_rowconfigure(2, weight=1)  # Main content area
        self.grid_columnconfigure(0, weight=1)
        
        # Create status bar
        self._create_status_bar()
        
        # Bind resize event for responsive design
        self.bind("<Configure>", self.on_window_resize)
    
    def center_window(self):
        """Center the window on the screen with error handling."""
        try:
            # Get screen dimensions
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            self.logger.debug(f"Screen dimensions: {screen_width}x{screen_height}")
            
            # Validate screen dimensions
            if screen_width is None or screen_height is None:
                self.logger.error(f"Screen dimensions are None: width={screen_width}, height={screen_height}")
                # Fallback geometry
                self.geometry("1800x1200")
                return
                
            if screen_width <= 0 or screen_height <= 0:
                self.logger.error(f"Invalid screen dimensions: width={screen_width}, height={screen_height}")
                # Fallback geometry
                self.geometry("1800x1200")
                return
            
            # Define window size
            window_width = 1800
            window_height = 1200
            
            # Calculate center position
            self.logger.debug(f"Calculating center: ({screen_width} - {window_width}) // 2")
            center_x = int((screen_width - window_width) // 2)
            self.logger.debug(f"Calculating center: ({screen_height} - {window_height}) // 2")
            center_y = int((screen_height - window_height) // 2)
            
            self.logger.debug(f"Calculated center position: x={center_x}, y={center_y}")
            
            # Ensure window doesn't go off-screen (minimum 10px margin)
            center_x = max(10, min(center_x, screen_width - window_width - 10))
            center_y = max(40, min(center_y, screen_height - window_height - 40))  # 40px top margin for taskbar
                
            # Set window geometry with center position
            self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
            
            self.logger.info(f"Window centered at {center_x},{center_y} with size {window_width}x{window_height} on screen {screen_width}x{screen_height}")
            
        except Exception as e:
            self.logger.exception(f"Window centering error: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            # Fallback to default geometry
            self.geometry("1800x1200")
    
    def on_window_resize(self, event):
        """Handle window resize for responsive design."""
        try:
            if event.widget == self and self.winfo_exists():  # Only handle main window resize
                try:
                    width = self.winfo_width()
                    height = self.winfo_height()
                    
                    # Update component sizes based on window size
                    self.update_component_scaling(width, height)
                except Exception as e:
                    self.logger.warning(f"Window resize handling warning: {e}")
        except Exception as e:
            # Suppress DPI scaling and update command errors
            if "invalid command name" not in str(e).lower():
                self.logger.warning(f"Window resize event error: {e}")
    
    def update_component_scaling(self, width, height):
        """Scale components based on window dimensions."""
        try:
            # Check if window still exists
            if not self.winfo_exists():
                return
                
            # Debug logging for width and height
            self.logger.debug(f"Component scaling: width={width} ({type(width)}), height={height} ({type(height)})")
            
            # Validate width and height before division
            if width is None or height is None:
                self.logger.error(f"Width or height is None: width={width}, height={height}")
                return
                
            if width <= 0 or height <= 0:
                self.logger.error(f"Invalid width or height: width={width}, height={height}")
                return
            
            # Calculate responsive font sizes
            base_font_size = max(10, width // 100)  # Minimum 10px
            large_font_size = max(12, width // 60)   # Minimum 12px
            
            self.logger.debug(f"Calculated font sizes: base={base_font_size}, large={large_font_size}")
            
            # Update chart dimensions
            chart_width = int(width * 0.45)
            chart_height = int(height * 0.45)
            
            # Update weather card width
            weather_card_width = int(width * 0.4)
            
            # Update search entry width
            search_width = int(width * 0.28)
            
            # Update main frame padding
            main_padding = max(10, width // 60)
            
            self.logger.debug(f"Calculated padding: main={main_padding}")
            
            # Apply scaling to components if they exist
            if hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
                self.search_entry.configure(width=search_width)
            
            # Update chart components if they exist
            if hasattr(self, 'temperature_chart') and hasattr(self.temperature_chart, 'update_size'):
                self.temperature_chart.update_size(chart_width, chart_height)
            
        except Exception as e:
            self.logger.warning(f"Component scaling error: {e}")
    
    def _create_widgets(self) -> None:
        """Create all UI widgets with clean design."""
        # Header
        self._create_header()
        
        # Main content area
        self._create_main_content()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self) -> None:
        """Create clean header with title and search."""
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=self.CARD_COLOR,
            corner_radius=0,
            height=100,
            border_width=0
        )
        
        # Header accent strip
        self.header_accent = ctk.CTkFrame(
            self.header_frame,
            fg_color=self.ACCENT_COLOR,
            height=2,
            corner_radius=0
        )
        
        # Title container
        self.title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        
        # Clean app title
        self.title_label = ctk.CTkLabel(
            self.title_container,
            text="⚡ PROJECT CODEFRONT",
            font=(DataTerminalTheme.FONT_FAMILY, 28, "bold"),
            text_color=self.ACCENT_COLOR
        )
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.title_container,
            text="Advanced Weather Intelligence System",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "normal"),
            text_color=self.TEXT_SECONDARY
        )
        
        # Enhanced search container
        self.search_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        
        # Initialize enhanced search component
        try:
            from ..components.enhanced_search import EnhancedSearchComponent
            self.enhanced_search = EnhancedSearchComponent(
                parent=self.search_container,
                weather_service=self.weather_service,
                on_location_selected=self._on_location_selected
            )
            
            # Position the enhanced search component
            self.enhanced_search.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
            self.search_container.grid_columnconfigure(0, weight=1)
            
            # Keep reference to search entry for compatibility
            self.search_entry = self.enhanced_search.search_entry
            
        except Exception as e:
            # Fallback to basic search if enhanced search fails
            self.logger.warning(f"Enhanced search failed, using basic search: {e}")
            self._create_basic_search()
    
    def _create_basic_search(self):
        """Create basic search as fallback."""
        # Search controls container
        self.search_controls = ctk.CTkFrame(self.search_container, fg_color="transparent")
        
        # Search bar
        self.search_entry = ctk.CTkEntry(
            self.search_controls,
            placeholder_text="🔍 Enter city name...",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            width=300,
            height=40,
            corner_radius=20,
            border_color=self.BORDER_COLOR,
            fg_color=self.BACKGROUND
        )
        self.search_entry.bind("<Return>", self._on_search)
        
        # Search button
        self.search_button = ctk.CTkButton(
            self.search_controls,
            text="SEARCH",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            width=100,
            height=40,
            corner_radius=20,
            fg_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.SUCCESS,
            command=self._search_weather
        )
        
        # Layout basic search
        self.search_controls.grid(row=0, column=0, sticky="e")
        self.search_entry.grid(row=0, column=0, padx=(0, 10))
        self.search_button.grid(row=0, column=1)
    
    def _on_enhanced_search(self, query: str):
        """Handle enhanced search callback."""
        try:
            if hasattr(self, '_search_weather'):
                self._search_weather(query)
            elif hasattr(self, '_perform_weather_update'):
                self.current_city = query
                self._perform_weather_update()
        except Exception as e:
            self.logger.error(f"Enhanced search callback failed: {e}")
    
    def _update_all_components_for_location(self, location_data: dict):
        """Update all dashboard components when a new location is selected."""
        try:
            self.logger.info(f"Updating all components for location: {location_data.get('name', 'Unknown')}")
            
            # Update location labels across the dashboard
            self._update_location_labels(location_data)
            
            # Update enhanced weather display if available
            self._update_enhanced_weather_display(location_data)
            
            # Update temperature charts
            self._update_temperature_charts(location_data)
            
            # Update maps component
            self._update_maps_component(location_data)
            
            # Update journal components with new location context
            self._update_journal_components(location_data)
            
            # Update activity suggester
            self._update_activity_suggester(location_data)
            
            # Update analytics components
            self._update_analytics_components(location_data)
            
            # Update any location-dependent settings
            self._update_location_settings(location_data)
            
            self.logger.info("All components updated successfully for new location")
            
        except Exception as e:
            self.logger.error(f"Error updating components for location: {e}")
    
    def _update_location_labels(self, location_data: dict):
        """Update all location labels throughout the dashboard."""
        try:
            display_name = location_data.get('display', location_data.get('name', 'Unknown Location'))
            
            # Update main location label
            if hasattr(self, 'location_label'):
                self.location_label.configure(text=f"📍 {display_name}")
            
            # Update enhanced weather display location
            if hasattr(self, 'enhanced_weather_display') and hasattr(self.enhanced_weather_display, 'location_label'):
                self.enhanced_weather_display.location_label.configure(text=display_name)
            
            # Update any other location labels
            location_elements = ['current_location_label', 'weather_location_label', 'header_location']
            for element_name in location_elements:
                if hasattr(self, element_name):
                    element = getattr(self, element_name)
                    if hasattr(element, 'configure'):
                        element.configure(text=f"📍 {display_name}")
                        
        except Exception as e:
            self.logger.error(f"Error updating location labels: {e}")
    
    def _update_enhanced_weather_display(self, location_data: dict):
        """Update the enhanced weather display component."""
        try:
            if hasattr(self, 'enhanced_weather_display'):
                # Update location information
                if hasattr(self.enhanced_weather_display, 'update_location'):
                    self.enhanced_weather_display.update_location(location_data)
                
                # Clear current weather data to force refresh
                if hasattr(self.enhanced_weather_display, 'current_weather'):
                    self.enhanced_weather_display.current_weather = None
                    
        except Exception as e:
            self.logger.error(f"Error updating enhanced weather display: {e}")
    
    def _update_temperature_charts(self, location_data: dict):
        """Update temperature charts with new location context."""
        try:
            # Update main temperature chart
            if hasattr(self, 'temperature_chart'):
                if hasattr(self.temperature_chart, 'update_location'):
                    self.temperature_chart.update_location(location_data)
                elif hasattr(self.temperature_chart, 'clear_data'):
                    self.temperature_chart.clear_data()
            
            # Update any other chart components
            chart_elements = ['forecast_chart', 'trend_chart', 'analytics_chart']
            for chart_name in chart_elements:
                if hasattr(self, chart_name):
                    chart = getattr(self, chart_name)
                    if hasattr(chart, 'update_location'):
                        chart.update_location(location_data)
                    elif hasattr(chart, 'refresh'):
                        chart.refresh()
                        
        except Exception as e:
            self.logger.error(f"Error updating temperature charts: {e}")
    
    def _update_maps_component(self, location_data: dict):
        """Update maps component with new location."""
        try:
            if hasattr(self, 'maps_component'):
                coordinates = {
                    'lat': location_data.get('lat'),
                    'lon': location_data.get('lon')
                }
                
                if coordinates['lat'] and coordinates['lon']:
                    if hasattr(self.maps_component, 'update_location'):
                        self.maps_component.update_location(coordinates['lat'], coordinates['lon'])
                    elif hasattr(self.maps_component, 'set_center'):
                        self.maps_component.set_center(coordinates['lat'], coordinates['lon'])
                        
        except Exception as e:
            self.logger.error(f"Error updating maps component: {e}")
    
    def _update_journal_components(self, location_data: dict):
        """Update journal components with new location context."""
        try:
            # Update weather journal
            if hasattr(self, 'weather_journal'):
                if hasattr(self.weather_journal, 'update_location'):
                    self.weather_journal.update_location(location_data)
            
            # Update journal manager
            if hasattr(self, 'journal_manager'):
                if hasattr(self.journal_manager, 'set_current_location'):
                    self.journal_manager.set_current_location(location_data)
                    
        except Exception as e:
            self.logger.error(f"Error updating journal components: {e}")
    
    def _update_activity_suggester(self, location_data: dict):
        """Update activity suggester with new location."""
        try:
            if hasattr(self, 'activity_suggester'):
                if hasattr(self.activity_suggester, 'update_location'):
                    self.activity_suggester.update_location(location_data)
                elif hasattr(self.activity_suggester, 'refresh_suggestions'):
                    self.activity_suggester.refresh_suggestions()
                    
        except Exception as e:
            self.logger.error(f"Error updating activity suggester: {e}")
    
    def _update_analytics_components(self, location_data: dict):
        """Update analytics components with new location context."""
        try:
            # Update mood analytics
            if hasattr(self, 'mood_analytics'):
                if hasattr(self.mood_analytics, 'update_location'):
                    self.mood_analytics.update_location(location_data)
            
            # Update any other analytics components
            analytics_elements = ['weather_analytics', 'trend_analytics', 'comparison_analytics']
            for analytics_name in analytics_elements:
                if hasattr(self, analytics_name):
                    analytics = getattr(self, analytics_name)
                    if hasattr(analytics, 'update_location'):
                        analytics.update_location(location_data)
                        
        except Exception as e:
            self.logger.error(f"Error updating analytics components: {e}")
    
    def _update_location_settings(self, location_data: dict):
        """Update location-dependent settings."""
        try:
            # Update timezone if available
            timezone = location_data.get('timezone')
            if timezone and hasattr(self, 'config_service'):
                if hasattr(self.config_service, 'set_timezone'):
                    self.config_service.set_timezone(timezone)
            
            # Update units based on location (metric for most countries, imperial for US)
            country = location_data.get('country', '')
            if country and hasattr(self, 'config_service'):
                units = 'imperial' if country.upper() in ['US', 'USA', 'UNITED STATES'] else 'metric'
                if hasattr(self.config_service, 'set_units'):
                    self.config_service.set_units(units)
                    
        except Exception as e:
            self.logger.error(f"Error updating location settings: {e}")
    
    def _on_location_selected(self, location_data: dict):
        """Handle location selection from enhanced search with comprehensive updates."""
        try:
            # Validate location data
            if not isinstance(location_data, dict):
                self.logger.error(f"Invalid location data type: {type(location_data)}")
                return
                
            # Extract location information
            city_name = location_data.get('name', '')
            display_name = location_data.get('display', '')
            coordinates = {
                'lat': location_data.get('lat'),
                'lon': location_data.get('lon')
            }
            
            # Use display name if available for better formatting, otherwise use name
            if display_name:
                self.current_city = display_name
            elif city_name:
                self.current_city = city_name
            else:
                self.logger.error("No valid city name found in location data")
                return
                
            self.logger.info(f"Location selected: {self.current_city}")
            
            # Store complete location data for other components
            self.current_location_data = location_data
            
            # Update weather service with new location
            if hasattr(self, 'weather_service') and self.weather_service:
                try:
                    # Set the new city in weather service
                    if hasattr(self.weather_service, 'set_city'):
                        self.weather_service.set_city(self.current_city)
                    elif hasattr(self.weather_service, 'set_location'):
                        self.weather_service.set_location(coordinates['lat'], coordinates['lon'])
                except Exception as e:
                    self.logger.warning(f"Failed to update weather service location: {e}")
            
            # Comprehensive dashboard updates
            self._update_all_components_for_location(location_data)
            
            # Trigger weather data refresh
            if hasattr(self, '_perform_weather_update'):
                self._perform_weather_update()
            else:
                self.logger.warning("_perform_weather_update method not available")
                
        except Exception as e:
            self.logger.error(f"Location selection callback failed: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
    
    def _create_main_content(self) -> None:
        """Create main content area with tabs."""
        # Main content frame
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        
        # Create tabview for different sections
        self.tabview = ctk.CTkTabview(
            self.main_frame,
            fg_color=self.BACKGROUND,
            segmented_button_fg_color=self.CARD_COLOR,
            segmented_button_selected_color=self.ACCENT_COLOR,
            segmented_button_selected_hover_color=DataTerminalTheme.SUCCESS,
            text_color=self.TEXT_PRIMARY,
            corner_radius=10
        )
        
        # Create all tabs
        self._create_tabs()
    
    def _create_status_bar(self) -> None:
        """Create status bar with system information."""
        self.status_frame = ctk.CTkFrame(
            self,
            fg_color=self.CARD_COLOR,
            corner_radius=0,
            height=30,
            border_width=0
        )
        
        # Status accent strip
        self.status_accent = ctk.CTkFrame(
            self.status_frame,
            fg_color=self.ACCENT_COLOR,
            height=1,
            corner_radius=0
        )
        
        # Status content
        self.status_content = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        
        # Last update label
        self.last_update_label = ctk.CTkLabel(
            self.status_content,
            text="Ready",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            text_color=self.TEXT_SECONDARY
        )
        
        # System status
        self.system_status_label = ctk.CTkLabel(
            self.status_content,
            text="● SYSTEM ONLINE",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            text_color=DataTerminalTheme.SUCCESS
        )
    
    def _setup_layout(self) -> None:
        """Setup the layout of all components with enhanced status bar."""
        # Status bar is already created in _configure_window at row 0
        
        # Header layout (moved to row 1)
        self.header_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        self.header_accent.grid(row=0, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        
        self.title_container.grid(row=1, column=0, sticky="w", padx=20, pady=10)
        self.title_label.grid(row=0, column=0, sticky="w")
        self.subtitle_label.grid(row=1, column=0, sticky="w")
        
        self.search_container.grid(row=1, column=2, sticky="e", padx=20, pady=10)
        
        # Layout enhanced search or basic search
        if hasattr(self, 'enhanced_search') and self.enhanced_search:
            # Enhanced search handles its own layout
            pass
        elif hasattr(self, 'search_controls'):
            # Basic search layout
            self.search_controls.grid(row=0, column=0, sticky="e")
            self.search_entry.grid(row=0, column=0, padx=(0, 10))
            self.search_button.grid(row=0, column=1)
        
        # Main content layout (moved to row 2)
        self.main_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        self.tabview.grid(row=0, column=0, sticky="nsew")
        
        # Legacy status bar layout (if exists) - moved to row 3
        if hasattr(self, 'status_frame'):
            self.status_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
            self.status_frame.grid_columnconfigure(1, weight=1)
            
            if hasattr(self, 'status_accent'):
                self.status_accent.grid(row=0, column=0, columnspan=3, sticky="ew")
            if hasattr(self, 'status_content'):
                self.status_content.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
                self.status_content.grid_columnconfigure(1, weight=1)
            
            if hasattr(self, 'last_update_label'):
                self.last_update_label.grid(row=0, column=0, sticky="w")
            if hasattr(self, 'system_status_label'):
                self.system_status_label.grid(row=0, column=2, sticky="e")
    
    def show_loading_state(self):
        """Show loading indicators on all data fields."""
        loading_text = "Loading..."
        if hasattr(self, 'temp_label'):
            self.temp_label.configure(text=loading_text)
        if hasattr(self, 'condition_label'):
            self.condition_label.configure(text=loading_text)
        if hasattr(self, 'feels_like_label'):
            self.feels_like_label.configure(text=loading_text)
        if hasattr(self, 'humidity_label'):
            self.humidity_label.configure(text=loading_text)
        
        # Disable refresh button
        if hasattr(self, 'refresh_button'):
            self.refresh_button.configure(state="disabled", text="⏳ Loading...")
    
    def hide_loading_state(self):
        """Hide loading indicators."""
        # Re-enable refresh button
        if hasattr(self, 'refresh_button'):
            self.refresh_button.configure(state="normal", text="🔄 Refresh")
        
        # Update last refresh time
        if hasattr(self, 'last_update_label'):
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M")
            self.last_update_label.configure(text=f"Updated: {current_time}")
    
    def _on_search(self, event=None):
        """Handle search entry submission"""
        try:
            search_text = self.search_entry.get().strip()
            
            if not search_text:
                if hasattr(self, 'logger'):
                    self.logger.warning("Empty search query")
                self._show_status_message("Please enter a city name", "warning")
                return
            
            if hasattr(self, 'logger'):
                self.logger.info(f"Search initiated for: {search_text}")
            
            # Show loading state
            self._show_status_message("Searching...", "info")
            
            # Trigger weather search - this should call your weather service
            if hasattr(self, 'weather_service') and self.weather_service:
                self._search_weather(search_text)
            else:
                if hasattr(self, 'logger'):
                    self.logger.error("Weather service not available")
                self._show_status_message("Weather service unavailable", "error")
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Search error: {e}")
            self._show_status_message("Search failed", "error")
    
    def _search_weather(self, city_name: str = None):
        """Perform weather search for the given city"""
        try:
            if city_name is None:
                city_name = self.search_entry.get().strip()
            
            if hasattr(self, 'logger'):
                self.logger.info(f"Fetching weather data for: {city_name}")
            
            # This is where you'd call your weather service
            # For now, let's add a placeholder that prevents the crash
            
            # Example of how this should work:
            # weather_data = self.weather_service.get_current_weather(city_name)
            # self._update_weather_display(weather_data)
            
            # Temporary placeholder to prevent crashes
            self._show_status_message(f"Weather search for '{city_name}' - Service integration needed", "info")
            
            # Clear the search entry
            self.search_entry.delete(0, 'end')
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Weather search failed for {city_name}: {e}")
            self._show_status_message(f"Failed to get weather for {city_name}", "error")
    
    def _show_status_message(self, message: str, message_type: str = "info"):
        """Display status message to user"""
        try:
            # If you have a status label in your UI
            if hasattr(self, 'last_update_label'):
                colors = {
                    "info": "#3B82F6",      # Blue
                    "success": "#10B981",   # Green
                    "warning": "#F59E0B",   # Amber
                    "error": "#EF4444"      # Red
                }
                
                color = colors.get(message_type, colors["info"])
                self.last_update_label.configure(text=message, text_color=color)
                
                # Auto-clear after 5 seconds
                self.after(5000, self._clear_status_message)
            
            # Also log the message
            if hasattr(self, 'logger'):
                getattr(self.logger, message_type if message_type != "warning" else "warning")(message)
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to show status message: {e}")
    
    def _clear_status_message(self):
        """Clear the status message by setting it to Ready"""
        try:
            if hasattr(self, 'last_update_label'):
                self.last_update_label.configure(text="Ready")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to clear status message: {e}")
    
    def _on_search_button_click(self):
        """Handle search button click"""
        self._on_search()
    
    def _setup_search_entry(self, parent):
        """Setup search entry with proper bindings"""
        try:
            import customtkinter as ctk
            self.search_entry = ctk.CTkEntry(
                parent,
                placeholder_text="Enter city name...",
                width=300,
                height=35
            )
            
            # Bind Enter key to search
            self.search_entry.bind("<Return>", self._on_search)
            
            # Optional: Bind focus events
            self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
            self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
            
            return self.search_entry
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to setup search entry: {e}")
            return None
    
    def _on_search_focus_in(self, event=None):
        """Handle search entry focus in"""
        if hasattr(self, 'search_entry'):
            # Could add placeholder behavior or styling changes here
            pass
    
    def _create_status_bar(self) -> None:
        """Create enhanced status bar with connection and system status."""
        try:
            # Status bar frame
            self.status_bar = ctk.CTkFrame(
                self,
                height=30,
                fg_color=self.CARD_COLOR,
                corner_radius=0
            )
            self.status_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
            self.status_bar.grid_columnconfigure(0, weight=1)
            self.status_bar.grid_columnconfigure(1, weight=0)
            self.status_bar.grid_columnconfigure(2, weight=0)
            
            # Status message label
            self.status_label = ctk.CTkLabel(
                self.status_bar,
                text="🟢 Ready - Weather dashboard initialized",
                font=ctk.CTkFont(size=12),
                text_color=self.TEXT_COLOR
            )
            self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            # Connection status indicator
            self.connection_status = ctk.CTkLabel(
                self.status_bar,
                text="🌐 Connected",
                font=ctk.CTkFont(size=12),
                text_color=self.ACCENT_COLOR
            )
            self.connection_status.grid(row=0, column=1, sticky="e", padx=10, pady=5)
            
            # System time indicator
            self.system_time = ctk.CTkLabel(
                self.status_bar,
                text="",
                font=ctk.CTkFont(size=12),
                text_color=self.TEXT_COLOR
            )
            self.system_time.grid(row=0, column=2, sticky="e", padx=10, pady=5)
            
            # Start time update
            self._update_system_time()
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to create status bar: {e}")
    
    def _update_system_time(self) -> None:
        """Update system time display."""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")
            if hasattr(self, 'system_time'):
                self.system_time.configure(text=f"🕐 {current_time}")
            # Schedule next update
            self.after(1000, self._update_system_time)
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to update system time: {e}")
    
    def update_status(self, message: str, status_type: str = "info") -> None:
        """Update status bar message with appropriate icon."""
        try:
            icons = {
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌",
                "loading": "🔄"
            }
            icon = icons.get(status_type, "ℹ️")
            
            if hasattr(self, 'status_label'):
                self.status_label.configure(text=f"{icon} {message}")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to update status: {e}")
    
    def update_connection_status(self, connected: bool) -> None:
        """Update connection status indicator."""
        try:
            if hasattr(self, 'connection_status'):
                if connected:
                    self.connection_status.configure(
                        text="🌐 Connected",
                        text_color=self.ACCENT_COLOR
                    )
                else:
                    self.connection_status.configure(
                        text="🔴 Disconnected",
                        text_color="#ff4444"
                    )
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to update connection status: {e}")
    
    def _on_search_focus_out(self, event=None):
        """Handle search entry focus out"""
        if hasattr(self, 'search_entry'):
            # Could add validation or styling changes here
            pass