"""Enhanced Weather Dashboard - Advanced Features Integration

Main application with comprehensive weather data, advanced search, and enhanced UI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional
from datetime import datetime
import threading
import time

from .services.config_service import ConfigService
from .services.enhanced_weather_service import EnhancedWeatherService, EnhancedWeatherData
from .ui.enhanced_search_bar import EnhancedSearchBarFrame
from .ui.enhanced_weather_display import EnhancedWeatherDisplayFrame
from .ui.chart_display import ChartDisplayFrame


class LoadingOverlay(tk.Toplevel):
    """Loading overlay with smooth animations."""
    
    def __init__(self, parent, message="Loading..."):
        super().__init__(parent)
        self.parent = parent
        self.message = message
        self._setup_window()
        self._create_widgets()
        self._start_animation()
    
    def _setup_window(self):
        """Setup loading window properties."""
        self.title("")
        self.geometry("300x150")
        self.resizable(False, False)
        self.configure(bg="#1a1a1a")
        self.overrideredirect(True)
        
        # Center on parent
        self.transient(self.parent)
        self.grab_set()
        
        # Position in center of parent
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width // 2) - 150
        y = parent_y + (parent_height // 2) - 75
        
        self.geometry(f"300x150+{x}+{y}")
    
    def _create_widgets(self):
        """Create loading widgets."""
        # Main frame
        main_frame = tk.Frame(self, bg="#2a2a2a", relief="solid", bd=2)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Loading animation
        self.loading_label = tk.Label(
            main_frame,
            text="⚡",
            font=("Consolas", 24),
            fg="#00FFAB",
            bg="#2a2a2a"
        )
        self.loading_label.pack(pady=(20, 10))
        
        # Message
        self.message_label = tk.Label(
            main_frame,
            text=self.message,
            font=("Consolas", 12),
            fg="#FFFFFF",
            bg="#2a2a2a"
        )
        self.message_label.pack()
        
        # Progress dots
        self.dots_label = tk.Label(
            main_frame,
            text="",
            font=("Consolas", 12),
            fg="#888888",
            bg="#2a2a2a"
        )
        self.dots_label.pack(pady=(5, 20))
    
    def _start_animation(self):
        """Start loading animation."""
        self.animation_running = True
        self.dots_count = 0
        self._animate()
    
    def _animate(self):
        """Animate loading indicators."""
        if not self.animation_running:
            return
        
        # Animate dots
        dots = "." * (self.dots_count % 4)
        self.dots_label.config(text=dots)
        self.dots_count += 1
        
        # Animate lightning bolt
        colors = ["#00FFAB", "#00E676", "#00C853", "#00E676"]
        color = colors[self.dots_count % len(colors)]
        self.loading_label.config(fg=color)
        
        # Schedule next animation frame
        self.after(500, self._animate)
    
    def close_loading(self):
        """Close loading overlay."""
        self.animation_running = False
        self.grab_release()
        self.destroy()


class AutoRefreshManager:
    """Manages automatic weather data refresh."""
    
    def __init__(self, dashboard, interval_minutes=30):
        self.dashboard = dashboard
        self.interval_minutes = interval_minutes
        self.running = False
        self.thread = None
        self.logger = logging.getLogger('weather_dashboard.auto_refresh')
    
    def start(self):
        """Start auto-refresh."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"🔄 Auto-refresh started (every {self.interval_minutes} minutes)")
    
    def stop(self):
        """Stop auto-refresh."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        self.logger.info("⏹️ Auto-refresh stopped")
    
    def _refresh_loop(self):
        """Auto-refresh loop."""
        while self.running:
            try:
                # Wait for interval
                for _ in range(self.interval_minutes * 60):
                    if not self.running:
                        return
                    time.sleep(1)
                
                # Refresh current location if available
                if self.running and hasattr(self.dashboard, 'current_location'):
                    current_location = getattr(self.dashboard, 'current_location', None)
                    if current_location:
                        self.logger.info(f"🔄 Auto-refreshing weather for {current_location}")
                        self.dashboard.root.after(0, lambda: self.dashboard._search_weather(current_location, auto_refresh=True))
                
            except Exception as e:
                self.logger.error(f"❌ Auto-refresh error: {e}")


class EnhancedWeatherDashboard:
    """Enhanced Weather Dashboard with comprehensive features."""
    
    def __init__(self):
        """Initialize enhanced weather dashboard."""
        self.logger = logging.getLogger('weather_dashboard.enhanced_main')
        
        # Initialize services
        self.config = ConfigService()
        self.weather_service = EnhancedWeatherService(self.config)
        
        # State management
        self.current_location = None
        self.current_weather_data = None
        self.loading_overlay = None
        
        # Auto-refresh manager
        self.auto_refresh = AutoRefreshManager(self, interval_minutes=30)
        
        # Create main window
        self._create_main_window()
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
        
        # Start auto-refresh
        self.auto_refresh.start()
        
        self.logger.info("🚀 Enhanced Weather Dashboard initialized")
    
    def _create_main_window(self):
        """Create and configure main window."""
        self.root = tk.Tk()
        self.root.title("JTC Capstone Application - Enhanced Weather Terminal")
        self.root.geometry("1400x900")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(True, True)
        
        # Set minimum size
        self.root.minsize(1200, 800)
        
        # Configure grid weights for responsiveness
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def _create_widgets(self):
        """Create main dashboard widgets."""
        # Main container
        self.main_container = tk.Frame(self.root, bg="#0a0a0a")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Configure main container grid
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Header frame
        self.header_frame = tk.Frame(self.main_container, bg="#0a0a0a")
        
        # Title
        self.title_label = tk.Label(
            self.header_frame,
            text="⚡ Project CodeFront - Enhanced Weather Terminal",
            font=("Consolas", 24, "bold"),
            fg="#00FFAB",
            bg="#0a0a0a"
        )
        
        # Status bar
        self.status_frame = tk.Frame(self.header_frame, bg="#0a0a0a")
        
        self.last_updated_label = tk.Label(
            self.status_frame,
            text="Ready",
            font=("Consolas", 10),
            fg="#888888",
            bg="#0a0a0a"
        )
        
        # Refresh button
        self.refresh_button = tk.Button(
            self.status_frame,
            text="🔄 Refresh",
            font=("Consolas", 10),
            fg="#00FFAB",
            bg="#2a2a2a",
            activeforeground="#FFFFFF",
            activebackground="#00FFAB",
            relief="flat",
            padx=10,
            command=self._manual_refresh
        )
        
        # Auto-refresh indicator
        self.auto_refresh_label = tk.Label(
            self.status_frame,
            text="🔄 Auto-refresh: ON",
            font=("Consolas", 9),
            fg="#00FFAB",
            bg="#0a0a0a"
        )
        
        # Enhanced search bar
        self.search_frame = EnhancedSearchBarFrame(
            self.main_container,
            bg="#1a1a1a",
            search_callback=self._on_search,
            location_callback=self._on_location_detect
        )
        
        # Content area
        self.content_frame = tk.Frame(self.main_container, bg="#0a0a0a")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=2)
        self.content_frame.grid_columnconfigure(1, weight=1)
        
        # Enhanced weather display
        self.weather_display = EnhancedWeatherDisplayFrame(
            self.content_frame,
            bg="#1a1a1a"
        )
        
        # Chart display (existing)
        self.chart_display = ChartDisplayFrame(
            self.content_frame,
            bg="#1a1a1a"
        )
    
    def _setup_layout(self):
        """Setup widget layout."""
        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.status_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.last_updated_label.grid(row=0, column=0, sticky="w")
        self.auto_refresh_label.grid(row=0, column=1, padx=(10, 0))
        self.refresh_button.grid(row=0, column=2, sticky="e", padx=(10, 0))
        
        # Search
        self.search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Content
        self.content_frame.grid(row=2, column=0, sticky="nsew")
        
        # Weather display (left side)
        self.weather_display.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Chart display (right side)
        self.chart_display.grid(row=0, column=1, sticky="nsew")
    
    def _setup_bindings(self):
        """Setup event bindings."""
        # Keyboard shortcuts
        self.root.bind('<Control-r>', lambda e: self._manual_refresh())
        self.root.bind('<F5>', lambda e: self._manual_refresh())
        self.root.bind('<Control-f>', lambda e: self.search_frame.focus_search())
        
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _on_search(self, location: str):
        """Handle search request."""
        if not location.strip():
            return
        
        self.logger.info(f"🔍 Search requested for: {location}")
        self._search_weather(location)
    
    def _on_location_detect(self):
        """Handle location detection request."""
        self.logger.info("📍 Location detection requested")
        # For now, use a default location (in real app, use geolocation API)
        self._search_weather("London", auto_detected=True)
    
    def _search_weather(self, location: str, auto_refresh: bool = False, auto_detected: bool = False):
        """Search and display weather for location."""
        def search_thread():
            try:
                # Show loading overlay (only for manual searches)
                if not auto_refresh:
                    self.root.after(0, self._show_loading, "Fetching enhanced weather data...")
                
                # Fetch enhanced weather data
                weather_data = self.weather_service.get_enhanced_weather(location)
                
                # Update UI on main thread
                self.root.after(0, self._update_weather_display, weather_data, auto_refresh, auto_detected)
                
            except Exception as e:
                self.logger.error(f"❌ Weather search failed: {e}")
                self.root.after(0, self._handle_search_error, str(e), auto_refresh)
        
        # Run search in background thread
        threading.Thread(target=search_thread, daemon=True).start()
    
    def _show_loading(self, message: str):
        """Show loading overlay."""
        if self.loading_overlay:
            self.loading_overlay.close_loading()
        
        self.loading_overlay = LoadingOverlay(self.root, message)
    
    def _hide_loading(self):
        """Hide loading overlay."""
        if self.loading_overlay:
            self.loading_overlay.close_loading()
            self.loading_overlay = None
    
    def _update_weather_display(self, weather_data: EnhancedWeatherData, auto_refresh: bool = False, auto_detected: bool = False):
        """Update weather display with enhanced data."""
        try:
            # Hide loading
            if not auto_refresh:
                self._hide_loading()
            
            # Update current state
            self.current_location = f"{weather_data.city}, {weather_data.country}"
            self.current_weather_data = weather_data
            
            # Update weather display
            self.weather_display.update_weather_display(weather_data)
            
            # Update search bar
            self.search_frame.set_current_city(self.current_location)
            
            # Update chart display (if forecast available)
            try:
                forecast_data = self.weather_service.get_forecast(self.current_location)
                if forecast_data:
                    self.chart_display.update_chart(forecast_data)
            except Exception as e:
                self.logger.warning(f"Chart update failed: {e}")
            
            # Update status
            status_text = f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
            if auto_refresh:
                status_text += " (auto-refresh)"
            elif auto_detected:
                status_text += " (auto-detected location)"
            
            self.last_updated_label.config(text=status_text)
            
            self.logger.info(f"✅ Enhanced weather display updated for {self.current_location}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update weather display: {e}")
            if not auto_refresh:
                self._hide_loading()
            self._show_error(f"Display update failed: {str(e)}")
    
    def _handle_search_error(self, error_message: str, auto_refresh: bool = False):
        """Handle search errors."""
        if not auto_refresh:
            self._hide_loading()
            self._show_error(error_message)
        
        # Update status
        self.last_updated_label.config(text=f"Error: {error_message}")
    
    def _show_error(self, message: str):
        """Show error message."""
        messagebox.showerror("Weather Error", message)
    
    def _manual_refresh(self):
        """Handle manual refresh request."""
        if self.current_location:
            self.logger.info(f"🔄 Manual refresh for {self.current_location}")
            self._search_weather(self.current_location)
        else:
            self.logger.warning("No location to refresh")
            self._show_error("No location selected. Please search for a city first.")
    
    def _on_closing(self):
        """Handle application closing."""
        self.logger.info("🔚 Enhanced Weather Dashboard closing")
        
        # Stop auto-refresh
        self.auto_refresh.stop()
        
        # Close loading overlay if open
        if self.loading_overlay:
            self.loading_overlay.close_loading()
        
        # Destroy main window
        self.root.destroy()
    
    def run(self):
        """Run the enhanced weather dashboard."""
        try:
            self.logger.info("🚀 Starting Enhanced Weather Dashboard")
            
            # Load default location
            default_location = "London"  # Could be from config or last used location
            self._search_weather(default_location)
            
            # Start main loop
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"❌ Dashboard startup failed: {e}")
            raise


def main():
    """Main entry point for enhanced weather dashboard."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('enhanced_weather_dashboard.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Create and run enhanced dashboard
        dashboard = EnhancedWeatherDashboard()
        dashboard.run()
        
    except Exception as e:
        logging.error(f"❌ Enhanced Weather Dashboard failed to start: {e}")
        raise


if __name__ == "__main__":
    main()