"""Professional Weather Dashboard - Clean Capstone Design

Minimalist weather dashboard with professional 2-column layout,
focused on essential information and clean aesthetics.
"""

import customtkinter as ctk
from typing import Optional, List
import threading
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

from services.enhanced_weather_service import EnhancedWeatherService
from services.config_service import ConfigService
from models.weather_models import WeatherData, ForecastData
from services.logging_service import LoggingService
from ui.theme import DataTerminalTheme


class ProfessionalWeatherDashboard(ctk.CTk):
    """Professional weather dashboard with clean, minimal design."""
    
    # Data Terminal color scheme
    ACCENT_COLOR = DataTerminalTheme.PRIMARY      # Neon green
    BACKGROUND = DataTerminalTheme.BACKGROUND     # Dark background
    CARD_COLOR = DataTerminalTheme.CARD_BG        # Dark card background
    TEXT_PRIMARY = DataTerminalTheme.TEXT         # Light text
    TEXT_SECONDARY = DataTerminalTheme.TEXT_SECONDARY # Medium gray text
    BORDER_COLOR = DataTerminalTheme.BORDER       # Dark border
    
    def __init__(self):
        """Initialize professional weather dashboard."""
        super().__init__()
        
        # Setup services
        self.logging_service = LoggingService()
        self.logging_service.setup_logging()
        self.logger = self.logging_service.get_logger(__name__)
        
        self.config_service = ConfigService()
        self.weather_service = EnhancedWeatherService(self.config_service)
        
        # Data storage
        self.current_weather: Optional[WeatherData] = None
        self.forecast_data: Optional[List[ForecastData]] = None
        self.current_city: str = "London"
        self.chart_timeframe = "24h"
        
        # Configure window
        self._configure_window()
        
        # Create UI
        self._create_widgets()
        self._setup_layout()
        
        # Load initial data
        self._load_initial_data()
        
        self.logger.info("Professional Weather Dashboard initialized")
    
    def _configure_window(self) -> None:
        """Configure main window with professional styling."""
        self.title("Weather Dashboard")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Set dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Configure background
        self.configure(fg_color=self.BACKGROUND)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.winfo_screenheight() // 2) - (800 // 2)
        self.geometry(f"1200x800+{x}+{y}")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
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
            height=80
        )
        
        # App title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Weather Dashboard",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE, "bold"),
            text_color=self.TEXT_PRIMARY
        )
        
        # Search bar
        self.search_entry = ctk.CTkEntry(
            self.header_frame,
            placeholder_text="Search for a city...",
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
            self.header_frame,
            text="Search",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "normal"),
            width=80,
            height=40,
            corner_radius=20,
            fg_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.SUCCESS,
            command=self._search_weather
        )
    
    def _create_main_content(self) -> None:
        """Create main 2-column layout."""
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        
        # Configure 2-column grid
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Left column - Current weather
        self._create_weather_card()
        
        # Right column - Analytics
        self._create_analytics_panel()
    
    def _create_weather_card(self) -> None:
        """Create large current weather card."""
        self.weather_card = ctk.CTkFrame(
            self.main_frame,
            fg_color=self.CARD_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        
        # City name
        self.city_label = ctk.CTkLabel(
            self.weather_card,
            text="London",
            font=(DataTerminalTheme.FONT_FAMILY, 28, "bold"),
            text_color=self.TEXT_PRIMARY
        )
        
        # Large temperature display
        self.temp_label = ctk.CTkLabel(
            self.weather_card,
            text="22°C",
            font=(DataTerminalTheme.FONT_FAMILY, 72, "normal"),
            text_color=self.ACCENT_COLOR
        )
        
        # Weather condition
        self.condition_label = ctk.CTkLabel(
            self.weather_card,
            text="Partly Cloudy",
            font=(DataTerminalTheme.FONT_FAMILY, 18),
            text_color=self.TEXT_SECONDARY
        )
        
        # Essential info grid
        self.info_frame = ctk.CTkFrame(
            self.weather_card,
            fg_color="transparent"
        )
        
        # Feels like
        self.feels_like_label = ctk.CTkLabel(
            self.info_frame,
            text="Feels like 24°C",
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=self.TEXT_SECONDARY
        )
        
        # Humidity
        self.humidity_label = ctk.CTkLabel(
            self.info_frame,
            text="Humidity 65%",
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=self.TEXT_SECONDARY
        )
    
    def _create_analytics_panel(self) -> None:
        """Create simplified analytics panel."""
        self.analytics_card = ctk.CTkFrame(
            self.main_frame,
            fg_color=self.CARD_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        
        # Analytics title
        self.analytics_title = ctk.CTkLabel(
            self.analytics_card,
            text="Temperature Trend",
            font=(DataTerminalTheme.FONT_FAMILY, 20, "bold"),
            text_color=self.TEXT_PRIMARY
        )
        
        # Timeframe buttons
        self.timeframe_frame = ctk.CTkFrame(
            self.analytics_card,
            fg_color="transparent"
        )
        
        self.btn_24h = ctk.CTkButton(
            self.timeframe_frame,
            text="24h",
            width=60,
            height=32,
            corner_radius=16,
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            fg_color=self.ACCENT_COLOR,
            command=lambda: self._set_timeframe("24h")
        )
        
        self.btn_7d = ctk.CTkButton(
            self.timeframe_frame,
            text="7d",
            width=60,
            height=32,
            corner_radius=16,
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            fg_color=self.BACKGROUND,
            text_color=self.TEXT_SECONDARY,
            hover_color=self.BORDER_COLOR,
            command=lambda: self._set_timeframe("7d")
        )
        
        self.btn_30d = ctk.CTkButton(
            self.timeframe_frame,
            text="30d",
            width=60,
            height=32,
            corner_radius=16,
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            fg_color=self.BACKGROUND,
            text_color=self.TEXT_SECONDARY,
            hover_color=self.BORDER_COLOR,
            command=lambda: self._set_timeframe("30d")
        )
        
        # Chart container
        self.chart_frame = ctk.CTkFrame(
            self.analytics_card,
            fg_color="transparent"
        )
        
        # Create matplotlib chart
        self._create_chart()
    
    def _create_chart(self) -> None:
        """Create Data Terminal styled temperature chart."""
        # Create figure with dark styling
        self.fig = Figure(figsize=(6, 4), dpi=100, facecolor=DataTerminalTheme.CARD_BG)
        self.ax = self.fig.add_subplot(111)
        
        # Sample data (replace with real data)
        hours = np.arange(24)
        temps = 20 + 5 * np.sin(hours * np.pi / 12) + np.random.normal(0, 1, 24)
        
        # Plot with Data Terminal styling
        self.ax.plot(hours, temps, color=self.ACCENT_COLOR, linewidth=3, alpha=0.9)
        self.ax.fill_between(hours, temps, alpha=0.2, color=self.ACCENT_COLOR)
        
        # Data Terminal styling
        self.ax.set_xlabel('Hour', fontsize=12, color=self.TEXT_SECONDARY, fontfamily='monospace')
        self.ax.set_ylabel('Temperature (°C)', fontsize=12, color=self.TEXT_SECONDARY, fontfamily='monospace')
        self.ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color=DataTerminalTheme.CHART_GRID)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(self.BORDER_COLOR)
        self.ax.spines['bottom'].set_color(self.BORDER_COLOR)
        self.ax.tick_params(colors=self.TEXT_SECONDARY, labelsize=10)
        
        # Dark background
        self.ax.set_facecolor(DataTerminalTheme.CARD_BG)
        
        # Tight layout
        self.fig.tight_layout(pad=2.0)
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
        self.canvas.draw()
    
    def _create_status_bar(self) -> None:
        """Create clean status bar."""
        self.status_frame = ctk.CTkFrame(
            self,
            fg_color=self.CARD_COLOR,
            corner_radius=0,
            height=40,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=self.TEXT_SECONDARY
        )
    
    def _setup_layout(self) -> None:
        """Setup the layout with proper spacing."""
        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_propagate(False)
        
        # Header content
        self.title_label.pack(side="left", padx=40, pady=20)
        self.search_button.pack(side="right", padx=40, pady=20)
        self.search_entry.pack(side="right", padx=(0, 10), pady=20)
        
        # Main content
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        # Weather card
        self.weather_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.weather_card.grid_rowconfigure(3, weight=1)
        
        # Weather card content
        self.city_label.grid(row=0, column=0, pady=(40, 10))
        self.temp_label.grid(row=1, column=0, pady=10)
        self.condition_label.grid(row=2, column=0, pady=(0, 30))
        
        self.info_frame.grid(row=3, column=0, sticky="ew", padx=40, pady=(0, 40))
        self.feels_like_label.pack(pady=5)
        self.humidity_label.pack(pady=5)
        
        # Analytics card
        self.analytics_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.analytics_card.grid_rowconfigure(2, weight=1)
        
        # Analytics content
        self.analytics_title.grid(row=0, column=0, pady=(30, 20))
        
        self.timeframe_frame.grid(row=1, column=0, pady=(0, 20))
        self.btn_24h.pack(side="left", padx=5)
        self.btn_7d.pack(side="left", padx=5)
        self.btn_30d.pack(side="left", padx=5)
        
        self.chart_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Status bar
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.status_label.pack(side="left", padx=20, pady=10)
    
    def _load_initial_data(self) -> None:
        """Load initial weather data."""
        threading.Thread(target=self._fetch_weather_data, daemon=True).start()
    
    def _fetch_weather_data(self) -> None:
        """Fetch weather data in background thread."""
        try:
            self.status_label.configure(text="Loading weather data...")
            
            # Simulate API call (replace with real implementation)
            import time
            time.sleep(1)
            
            # Update UI on main thread
            self.after(0, self._update_weather_display)
            
        except Exception as e:
            self.logger.error(f"Failed to fetch weather data: {e}")
            self.after(0, lambda: self.status_label.configure(text="Error loading data"))
    
    def _update_weather_display(self) -> None:
        """Update weather display with current data."""
        # Update with real data when available
        self.city_label.configure(text=self.current_city)
        self.status_label.configure(text="Data updated successfully")
    
    def _on_search(self, event=None) -> None:
        """Handle search entry return key."""
        self._search_weather()
    
    def _search_weather(self) -> None:
        """Search for weather in specified city."""
        city = self.search_entry.get().strip()
        if city:
            self.current_city = city
            self.search_entry.delete(0, 'end')
            threading.Thread(target=self._fetch_weather_data, daemon=True).start()
    
    def _set_timeframe(self, timeframe: str) -> None:
        """Set chart timeframe and update styling."""
        self.chart_timeframe = timeframe
        
        # Reset all buttons
        for btn in [self.btn_24h, self.btn_7d, self.btn_30d]:
            btn.configure(
                fg_color=self.BACKGROUND,
                text_color=self.TEXT_SECONDARY
            )
        
        # Highlight selected button
        if timeframe == "24h":
            self.btn_24h.configure(fg_color=self.ACCENT_COLOR, text_color="white")
        elif timeframe == "7d":
            self.btn_7d.configure(fg_color=self.ACCENT_COLOR, text_color="white")
        elif timeframe == "30d":
            self.btn_30d.configure(fg_color=self.ACCENT_COLOR, text_color="white")
        
        # Update chart (implement with real data)
        self._update_chart()
    
    def _update_chart(self) -> None:
        """Update chart based on selected timeframe."""
        # Clear and redraw chart with new timeframe data
        self.ax.clear()
        
        # Sample data based on timeframe
        if self.chart_timeframe == "24h":
            x_data = np.arange(24)
            y_data = 20 + 5 * np.sin(x_data * np.pi / 12) + np.random.normal(0, 1, 24)
            xlabel = "Hour"
        elif self.chart_timeframe == "7d":
            x_data = np.arange(7)
            y_data = 18 + 8 * np.sin(x_data * np.pi / 3.5) + np.random.normal(0, 2, 7)
            xlabel = "Day"
        else:  # 30d
            x_data = np.arange(30)
            y_data = 15 + 10 * np.sin(x_data * np.pi / 15) + np.random.normal(0, 3, 30)
            xlabel = "Day"
        
        # Plot with consistent styling
        self.ax.plot(x_data, y_data, color=self.ACCENT_COLOR, linewidth=2.5, alpha=0.8)
        self.ax.fill_between(x_data, y_data, alpha=0.1, color=self.ACCENT_COLOR)
        
        # Clean styling
        self.ax.set_xlabel(xlabel, fontsize=12, color=self.TEXT_SECONDARY)
        self.ax.set_ylabel('Temperature (°C)', fontsize=12, color=self.TEXT_SECONDARY)
        self.ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(self.BORDER_COLOR)
        self.ax.spines['bottom'].set_color(self.BORDER_COLOR)
        
        self.fig.tight_layout(pad=2.0)
        self.canvas.draw()
    
    def run(self) -> None:
        """Start the application."""
        self.logger.info("Starting Professional Weather Dashboard")
        try:
            self.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
        finally:
            self.logger.info("Professional Weather Dashboard stopped")


def main():
    """Main entry point for professional dashboard."""
    app = ProfessionalWeatherDashboard()
    app.run()


if __name__ == "__main__":
    main()