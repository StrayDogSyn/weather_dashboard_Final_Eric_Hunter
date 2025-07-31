"""UI Components Mixin

Contains all UI creation and layout methods for the dashboard.
"""

import customtkinter as ctk
from ui.theme import DataTerminalTheme


class UIComponentsMixin:
    """Mixin class containing UI component creation methods."""
    
    def _configure_window(self) -> None:
        """Configure main window properties."""
        self.title("Professional Weather Dashboard")
        self.configure(fg_color=self.BACKGROUND)
        
        # Set window icon if available
        try:
            self.iconbitmap("assets/weather_icon.ico")
        except Exception:
            pass  # Icon file not found, continue without it
        
        # Configure window size and position
        self.center_window()
        
        # Configure grid weights for responsive design
        self.grid_rowconfigure(1, weight=1)  # Main content area
        self.grid_columnconfigure(0, weight=1)
        
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
        
        # Search container for organizing search components
        self.search_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        
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
        """Setup the layout of all components."""
        # Header layout
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        self.header_accent.grid(row=0, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        
        self.title_container.grid(row=1, column=0, sticky="w", padx=20, pady=10)
        self.title_label.grid(row=0, column=0, sticky="w")
        self.subtitle_label.grid(row=1, column=0, sticky="w")
        
        self.search_container.grid(row=1, column=2, sticky="e", padx=20, pady=10)
        self.search_controls.grid(row=0, column=0, sticky="e")
        self.search_entry.grid(row=0, column=0, padx=(0, 10))
        self.search_button.grid(row=0, column=1)
        
        # Main content layout
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        self.tabview.grid(row=0, column=0, sticky="nsew")
        
        # Status bar layout
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        self.status_accent.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.status_content.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        self.status_content.grid_columnconfigure(1, weight=1)
        
        self.last_update_label.grid(row=0, column=0, sticky="w")
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
                self.after(5000, lambda: self.last_update_label.configure(text="Ready"))
            
            # Also log the message
            if hasattr(self, 'logger'):
                getattr(self.logger, message_type if message_type != "warning" else "warning")(message)
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to show status message: {e}")
    
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
    
    def _on_search_focus_out(self, event=None):
        """Handle search entry focus out"""
        if hasattr(self, 'search_entry'):
            # Could add validation or styling changes here
            pass