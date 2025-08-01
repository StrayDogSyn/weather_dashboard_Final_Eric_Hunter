import customtkinter as ctk
from typing import Optional
import threading
from datetime import datetime
import logging

from src.services.enhanced_weather_service import EnhancedWeatherService
from src.services.config_service import ConfigService
from src.ui.theme import DataTerminalTheme

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class ProfessionalWeatherDashboard(ctk.CTk):
    """Professional weather dashboard with clean design."""
    
    def __init__(self, config_service=None):
        super().__init__()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.config_service = config_service or ConfigService()
        self.weather_service = EnhancedWeatherService(self.config_service)
        
        # State
        self.current_city = "London"
        
        # Configure window
        self.title("Professional Weather Dashboard")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create UI
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
        # Load initial data
        self.after(100, self._load_weather_data)
        
        self.logger.info("Dashboard UI created successfully")
    
    def _create_header(self):
        """Create professional header with PROJECT CODEFRONT branding."""
        self.header_frame = ctk.CTkFrame(
            self,
            height=100,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=0
        )
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_propagate(False)
        
        # Add accent strip
        accent_strip = ctk.CTkFrame(
            self.header_frame,
            height=3,
            fg_color=DataTerminalTheme.PRIMARY,
            corner_radius=0
        )
        accent_strip.pack(fill="x", side="top")
        
        # Title container
        title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_container.pack(side="left", padx=40, pady=20)
        
        # Main title with glow effect
        title_frame = ctk.CTkFrame(
            title_container,
            fg_color="transparent",
            border_width=1,
            border_color=DataTerminalTheme.PRIMARY
        )
        title_frame.pack()
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="⚡ PROJECT CODEFRONT",
            font=(DataTerminalTheme.FONT_FAMILY, 32, "bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        self.title_label.pack(padx=15, pady=5)
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            title_container,
            text="Advanced Weather Intelligence System",
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.subtitle_label.pack()
        
        # Search container on right
        search_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        search_container.pack(side="right", padx=40, pady=20)
        
        # Search controls
        search_controls = ctk.CTkFrame(search_container, fg_color="transparent")
        search_controls.pack()
        
        self.search_entry = ctk.CTkEntry(
            search_controls,
            placeholder_text="🔍 Enter city name...",
            width=300,
            height=40,
            corner_radius=20,
            border_color=DataTerminalTheme.BORDER,
            fg_color=DataTerminalTheme.BACKGROUND,
            text_color=DataTerminalTheme.TEXT,
            font=(DataTerminalTheme.FONT_FAMILY, 14)
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._search_weather())
        
        self.search_button = ctk.CTkButton(
            search_controls,
            text="SEARCH",
            width=100,
            height=40,
            corner_radius=20,
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.SUCCESS,
            text_color=DataTerminalTheme.BACKGROUND,
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            command=self._search_weather
        )
        self.search_button.pack(side="left")
        
        # Current location indicator
        self.location_label = ctk.CTkLabel(
            search_container,
            text=f"📍 Current: {self.current_city}",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.location_label.pack(pady=(5, 0))
    
    def _create_main_content(self):
        """Create tab view."""
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        # Create tabs
        self.weather_tab = self.tabview.add("Weather")
        self.journal_tab = self.tabview.add("Journal")
        self.activities_tab = self.tabview.add("Activities")
        self.settings_tab = self.tabview.add("Settings")
        
        # Configure tab grids
        self.weather_tab.grid_columnconfigure(0, weight=1)
        self.weather_tab.grid_rowconfigure(0, weight=1)
        
        self.journal_tab.grid_columnconfigure(0, weight=1)
        self.journal_tab.grid_rowconfigure(0, weight=1)
        
        self.activities_tab.grid_columnconfigure(0, weight=1)
        self.activities_tab.grid_rowconfigure(0, weight=1)
        
        self.settings_tab.grid_columnconfigure(0, weight=1)
        self.settings_tab.grid_rowconfigure(0, weight=1)
        
        # Create tab content
        self._create_weather_tab()
        self._create_journal_tab()
        self._create_activities_tab()
        self._create_settings_tab()
    
    def _create_weather_tab(self):
        """Create enhanced weather tab with proper layout."""
        self._create_weather_tab_content()
    
    def _create_weather_tab_content(self):
        """Create enhanced weather tab with proper layout."""
        # Configure grid for 2-column layout
        self.weather_tab.grid_columnconfigure(0, weight=1)
        self.weather_tab.grid_columnconfigure(1, weight=2)
        self.weather_tab.grid_rowconfigure(0, weight=1)
        
        # Left column - Current weather card with glassmorphic styling
        self.weather_card = ctk.CTkFrame(
            self.weather_tab,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=DataTerminalTheme.BORDER
        )
        self.weather_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Weather icon and city
        self.city_label = ctk.CTkLabel(
            self.weather_card,
            text="Loading...",
            font=(DataTerminalTheme.FONT_FAMILY, 28, "bold"),
            text_color=DataTerminalTheme.TEXT
        )
        self.city_label.pack(pady=(40, 10))
        
        # Large temperature display
        self.temp_label = ctk.CTkLabel(
            self.weather_card,
            text="--°C",
            font=(DataTerminalTheme.FONT_FAMILY, 72, "bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        self.temp_label.pack(pady=20)
        
        # Weather condition with icon
        self.condition_label = ctk.CTkLabel(
            self.weather_card,
            text="--",
            font=(DataTerminalTheme.FONT_FAMILY, 18),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.condition_label.pack(pady=(0, 30))
        
        # Weather metrics grid
        self._create_weather_metrics()
        
        # Right column - Forecast and charts
        self._create_forecast_section()
    
    def _create_weather_metrics(self):
        """Create weather metrics grid."""
        metrics_frame = ctk.CTkFrame(
            self.weather_card,
            fg_color="transparent"
        )
        metrics_frame.pack(fill="x", padx=30, pady=20)
        
        # Create metric cards
        metrics = [
            ("💧", "Humidity", "--"),
            ("💨", "Wind", "--"),
            ("🌡️", "Feels Like", "--"),
            ("👁️", "Visibility", "--"),
            ("🧭", "Pressure", "--"),
            ("☁️", "Cloudiness", "--")
        ]
        
        # Store metric labels for updates
        self.metric_labels = {}
        
        for i, (icon, name, value) in enumerate(metrics):
            metric_card = ctk.CTkFrame(
                metrics_frame,
                fg_color=DataTerminalTheme.BACKGROUND,
                corner_radius=8,
                border_width=1,
                border_color=DataTerminalTheme.BORDER
            )
            metric_card.pack(pady=5, fill="x")
            
            # Icon and name
            header_frame = ctk.CTkFrame(metric_card, fg_color="transparent")
            header_frame.pack(fill="x", padx=15, pady=(10, 5))
            
            icon_label = ctk.CTkLabel(
                header_frame,
                text=icon,
                font=(DataTerminalTheme.FONT_FAMILY, 16)
            )
            icon_label.pack(side="left")
            
            name_label = ctk.CTkLabel(
                header_frame,
                text=name,
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                text_color=DataTerminalTheme.TEXT_SECONDARY
            )
            name_label.pack(side="left", padx=(5, 0))
            
            # Value
            value_label = ctk.CTkLabel(
                metric_card,
                text=value,
                font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
                text_color=DataTerminalTheme.PRIMARY
            )
            value_label.pack(pady=(0, 10))
            
            # Store reference
            self.metric_labels[name.lower().replace(" ", "_")] = value_label
        
        # Temperature conversion toggle button at bottom left
        toggle_frame = ctk.CTkFrame(
            self.weather_card,
            fg_color="transparent"
        )
        toggle_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # Initialize temperature unit
        self.temp_unit = "C"  # Default to Celsius
        
        self.temp_toggle_btn = ctk.CTkButton(
            toggle_frame,
            text="°C / °F",
            width=80,
            height=30,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.HOVER,
            command=self._toggle_temperature_unit
        )
        self.temp_toggle_btn.pack(side="left")
    
    def _create_forecast_section(self):
        """Create forecast section."""
        forecast_frame = ctk.CTkFrame(
            self.weather_tab,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=DataTerminalTheme.BORDER
        )
        forecast_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Forecast title
        forecast_title = ctk.CTkLabel(
            forecast_frame,
            text="📊 5-Day Forecast",
            font=(DataTerminalTheme.FONT_FAMILY, 24, "bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        forecast_title.pack(pady=(20, 10))
        
        # Forecast cards container
        self.forecast_container = ctk.CTkScrollableFrame(
            forecast_frame,
            fg_color="transparent"
        )
        self.forecast_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Placeholder forecast cards
        for i in range(5):
            day_frame = ctk.CTkFrame(
                self.forecast_container,
                fg_color=DataTerminalTheme.BACKGROUND,
                corner_radius=12,
                border_width=1,
                border_color=DataTerminalTheme.BORDER
            )
            day_frame.pack(fill="x", pady=5)
            
            # Day info
            day_info = ctk.CTkFrame(day_frame, fg_color="transparent")
            day_info.pack(fill="x", padx=15, pady=10)
            
            day_label = ctk.CTkLabel(
                day_info,
                text=f"Day {i+1}",
                font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
                text_color=DataTerminalTheme.TEXT
            )
            day_label.pack(side="left")
            
            temp_label = ctk.CTkLabel(
                day_info,
                text="--°C",
                font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
                text_color=DataTerminalTheme.PRIMARY
            )
            temp_label.pack(side="right")
    
    def _search_weather(self):
        """Handle weather search functionality."""
        search_term = self.search_entry.get().strip()
        if search_term:
            # Update current city
            self.current_city = search_term
            self.location_label.configure(text=f"📍 Current: {self.current_city}")
            
            # Update weather display
            self.city_label.configure(text=self.current_city)
            
            # Clear search entry
            self.search_entry.delete(0, 'end')
            
            # Here you would typically call weather API
            # For now, just update the display with placeholder data
            self._update_weather_display()
    
    def _update_weather_display(self):
        """Update weather display with current data."""
        # Placeholder weather data - in real implementation, this would come from API
        self.temp_label.configure(text="22°C")
        self.condition_label.configure(text="⛅ Partly Cloudy")
        
        # Update metrics if they exist
        if hasattr(self, 'metric_labels'):
            metrics_data = {
                'humidity': '65%',
                'wind': '12 km/h',
                'feels_like': '24°C',
                'visibility': '10 km',
                'pressure': '1013 hPa',
                'cloudiness': '40%'
            }
            
            for key, value in metrics_data.items():
                if key in self.metric_labels:
                     self.metric_labels[key].configure(text=value)
    
    def _toggle_temperature_unit(self):
        """Toggle between Celsius and Fahrenheit."""
        if self.temp_unit == "C":
            self.temp_unit = "F"
            # Convert current temperature to Fahrenheit
            current_temp = self.temp_label.cget("text")
            if current_temp and current_temp != "--°C":
                try:
                    # Extract numeric value
                    temp_value = float(current_temp.replace("°C", ""))
                    fahrenheit = (temp_value * 9/5) + 32
                    self.temp_label.configure(text=f"{fahrenheit:.0f}°F")
                except ValueError:
                    self.temp_label.configure(text="--°F")
            
            # Update feels like temperature if available
            if hasattr(self, 'metric_labels') and 'feels_like' in self.metric_labels:
                feels_like_text = self.metric_labels['feels_like'].cget("text")
                if feels_like_text and feels_like_text != "--":
                    try:
                        temp_value = float(feels_like_text.replace("°C", ""))
                        fahrenheit = (temp_value * 9/5) + 32
                        self.metric_labels['feels_like'].configure(text=f"{fahrenheit:.0f}°F")
                    except ValueError:
                        pass
        else:
            self.temp_unit = "C"
            # Convert current temperature to Celsius
            current_temp = self.temp_label.cget("text")
            if current_temp and current_temp != "--°F":
                try:
                    # Extract numeric value
                    temp_value = float(current_temp.replace("°F", ""))
                    celsius = (temp_value - 32) * 5/9
                    self.temp_label.configure(text=f"{celsius:.0f}°C")
                except ValueError:
                    self.temp_label.configure(text="--°C")
            
            # Update feels like temperature if available
            if hasattr(self, 'metric_labels') and 'feels_like' in self.metric_labels:
                feels_like_text = self.metric_labels['feels_like'].cget("text")
                if feels_like_text and feels_like_text != "--":
                    try:
                        temp_value = float(feels_like_text.replace("°F", ""))
                        celsius = (temp_value - 32) * 5/9
                        self.metric_labels['feels_like'].configure(text=f"{celsius:.0f}°C")
                    except ValueError:
                        pass
    
    def _create_journal_tab(self):
        """Create journal tab content."""
        journal_frame = ctk.CTkFrame(self.journal_tab)
        journal_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Journal title
        journal_title = ctk.CTkLabel(
            journal_frame,
            text="Weather Journal",
            font=("Arial", 24, "bold")
        )
        journal_title.pack(pady=20)
        
        # Placeholder content
        journal_content = ctk.CTkLabel(
            journal_frame,
            text="Journal functionality will be implemented here.",
            font=("Arial", 16)
        )
        journal_content.pack(pady=50)
    
    def _create_activities_tab(self):
        """Create activities tab content."""
        activities_frame = ctk.CTkFrame(self.activities_tab)
        activities_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Activities title
        activities_title = ctk.CTkLabel(
            activities_frame,
            text="Weather-Based Activities",
            font=("Arial", 24, "bold")
        )
        activities_title.pack(pady=20)
        
        # Placeholder content
        activities_content = ctk.CTkLabel(
            activities_frame,
            text="Activity suggestions will be implemented here.",
            font=("Arial", 16)
        )
        activities_content.pack(pady=50)
    
    def _create_settings_tab(self):
        """Create settings tab content."""
        settings_frame = ctk.CTkFrame(self.settings_tab)
        settings_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Settings title
        settings_title = ctk.CTkLabel(
            settings_frame,
            text="Settings",
            font=("Arial", 24, "bold")
        )
        settings_title.pack(pady=20)
        
        # Theme selection
        theme_frame = ctk.CTkFrame(settings_frame)
        theme_frame.pack(pady=20, padx=20, fill="x")
        
        theme_label = ctk.CTkLabel(theme_frame, text="Theme:", font=("Arial", 16))
        theme_label.pack(side="left", padx=10, pady=10)
        
        self.theme_var = ctk.StringVar(value="dark")
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["dark", "light", "system"],
            variable=self.theme_var,
            command=self._change_theme
        )
        theme_menu.pack(side="left", padx=10, pady=10)
    
    def _create_status_bar(self):
        """Create status bar."""
        self.status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_frame.grid(row=2, column=0, sticky="ew")
        self.status_frame.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=("Arial", 12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Time label
        self.time_label = ctk.CTkLabel(
            self.status_frame,
            text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            font=("Arial", 12)
        )
        self.time_label.pack(side="right", padx=10, pady=5)
        
        # Update time every second
        self._update_time()
    
    def _update_time(self):
        """Update time display."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.configure(text=current_time)
        self.after(1000, self._update_time)
    
    def _search_weather(self):
        """Search for weather data."""
        city = self.search_entry.get().strip()
        if city:
            self.current_city = city
            self.city_label.configure(text=city)
            self.status_label.configure(text=f"Loading weather for {city}...")
            
            # Load weather data in background
            threading.Thread(target=self._load_weather_data, daemon=True).start()
    
    def _load_weather_data(self):
        """Load weather data for current city."""
        try:
            # Simulate weather data loading
            if hasattr(self, 'status_label'):
                self.after(0, lambda: self.status_label.configure(text="Loading weather data..."))
            
            # Update UI on main thread using the new method
            self.after(0, lambda: self._update_weather_display())
            
        except Exception as e:
            self.logger.error(f"Failed to load weather data: {e}")
            if hasattr(self, 'status_label'):
                self.after(0, lambda: self.status_label.configure(text="Failed to load weather data"))
    
    def _change_theme(self, theme):
        """Change application theme."""
        ctk.set_appearance_mode(theme)
        self.status_label.configure(text=f"Theme changed to {theme}")
    
    def center_window(self):
        """Center the window on screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

if __name__ == "__main__":
    app = ProfessionalWeatherDashboard()
    app.center_window()
    app.mainloop()