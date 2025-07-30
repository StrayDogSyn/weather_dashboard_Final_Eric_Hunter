"""Layout Management Mixin

Handles UI layout, component creation, and responsive design.
"""

import customtkinter as ctk
from typing import Optional

from .base_dashboard import BaseDashboard
from ui.components.weather_display import WeatherDisplayFrame

# Enhanced features check
try:
    from ui.components.enhanced_search_bar import EnhancedSearchBarFrame
    ENHANCED_SEARCH_AVAILABLE = True
except ImportError:
    ENHANCED_SEARCH_AVAILABLE = False
    EnhancedSearchBarFrame = None

# Import standard search bar as fallback
try:
    from ui.components.search_bar import SearchBarFrame
except ImportError:
    SearchBarFrame = None


class LayoutMixin(BaseDashboard):
    """Mixin for UI layout and component management."""
    
    def __init__(self):
        """Initialize layout management."""
        super().__init__()
        
        # UI Components
        self.header_frame: Optional[ctk.CTkFrame] = None
        self.content_frame: Optional[ctk.CTkFrame] = None
        self.weather_display: Optional[WeatherDisplayFrame] = None
        self.search_bar: Optional[SearchBarFrame] = None
        self.enhanced_search_bar: Optional = None
        self.fallback_search_entry: Optional[ctk.CTkEntry] = None
        
        # Layout state
        self._current_scale = 1.0
    
    def _setup_ui(self):
        """Set up the main UI layout and components."""
        self._log_method_call("_setup_ui")
        
        if self.logger:
            self.logger.info("Starting UI setup...")
        
        # Configure grid weights for responsive design
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Content
        self.grid_columnconfigure(0, weight=1)
        
        if self.logger:
            self.logger.info("Creating header...")
        
        # Create main layout components
        self._create_header()
        
        if self.logger:
            self.logger.info("Creating content panel...")
        
        self._create_content_panel()
        
        if self.logger:
            self.logger.info("Applying responsive layout...")
        
        # Apply initial responsive layout
        self._update_responsive_layout()
        
        if self.logger:
            self.logger.info("UI setup complete")
    
    def _create_header(self):
        """Create the header section with branding and search."""
        self._log_method_call("_create_header")
        
        # Create header frame
        self.header_frame = ctk.CTkFrame(self, height=120, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_propagate(False)
        
        # Configure header grid
        self.header_frame.grid_rowconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=2)
        self.header_frame.grid_columnconfigure(2, weight=1)
        
        # Create header components
        self._create_branding_section()
        self._create_search_section()
        self._create_fallback_search()
    
    def _create_branding_section(self):
        """Create the branding/logo section."""
        branding_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        branding_frame.grid(row=0, column=0, sticky="w", padx=20, pady=10)
        
        # App title
        title_label = ctk.CTkLabel(
            branding_frame,
            text="Weather Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w")
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            branding_frame,
            text="JTC Capstone Project",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        subtitle_label.pack(anchor="w")
    
    def _create_search_section(self):
        """Create the main search section."""
        if self.logger:
            self.logger.info("Creating search section...")
            self.logger.info(f"use_enhanced_features: {getattr(self, 'use_enhanced_features', 'NOT_SET')}")
            self.logger.info(f"ENHANCED_SEARCH_AVAILABLE: {ENHANCED_SEARCH_AVAILABLE}")
        
        search_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        search_container.grid(row=0, column=1, sticky="ew", padx=20, pady=10)
        
        # Choose search component based on enhanced features
        if self.use_enhanced_features and ENHANCED_SEARCH_AVAILABLE:
            if self.logger:
                self.logger.info("Creating enhanced search...")
            self._create_enhanced_search(search_container)
        else:
            if self.logger:
                self.logger.info("Creating standard search...")
            self._create_standard_search(search_container)
    
    def _create_enhanced_search(self, parent):
        """Create enhanced search bar with autocomplete."""
        try:
            if EnhancedSearchBarFrame is None:
                raise ImportError("EnhancedSearchBarFrame not available")
            
            # Debug: Check if required methods exist
            if self.logger:
                self.logger.info("Checking for required methods...")
                self.logger.info(f"_on_suggestion_select exists: {hasattr(self, '_on_suggestion_select')}")
                self.logger.info(f"_on_city_search exists: {hasattr(self, '_on_city_search')}")
                if hasattr(self, '_on_suggestion_select'):
                    self.logger.info(f"_on_suggestion_select value: {self._on_suggestion_select}")
                if hasattr(self, '_on_city_search'):
                    self.logger.info(f"_on_city_search value: {self._on_city_search}")
            
            if not hasattr(self, '_on_suggestion_select'):
                if self.logger:
                    self.logger.error("_on_suggestion_select method not found! Available methods: %s", 
                                    [method for method in dir(self) if method.startswith('_on')])
                raise AttributeError("_on_suggestion_select method not available")
            
            if not hasattr(self, '_on_city_search'):
                if self.logger:
                    self.logger.error("_on_city_search method not found!")
                raise AttributeError("_on_city_search method not available")
            
            if self._on_suggestion_select is None:
                raise ValueError("_on_suggestion_select is None")
            
            if self._on_city_search is None:
                raise ValueError("_on_city_search is None")
            
            self.enhanced_search_bar = EnhancedSearchBarFrame(
                parent,
                on_search=self._on_city_search,
                on_suggestion_select=self._on_suggestion_select
            )
            self.enhanced_search_bar.pack(fill="x", expand=True)
            
            if self.logger:
                self.logger.info("✨ Enhanced search bar created")
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Enhanced search creation failed: {e}")
            self._create_standard_search(parent)
    
    def _create_standard_search(self, parent):
        """Create standard search bar."""
        if self.logger:
            self.logger.info(f"SearchBarFrame available: {SearchBarFrame is not None}")
            self.logger.info(f"SearchBarFrame value: {SearchBarFrame}")
            self.logger.info(f"_on_city_search available: {hasattr(self, '_on_city_search')}")
            if hasattr(self, '_on_city_search'):
                self.logger.info(f"_on_city_search value: {self._on_city_search}")
        
        if SearchBarFrame is None:
            if self.logger:
                self.logger.error("SearchBarFrame is None - cannot create standard search")
            return
        
        if not hasattr(self, '_on_city_search') or self._on_city_search is None:
            if self.logger:
                self.logger.error("_on_city_search is not available or None")
            return
        
        self.search_bar = SearchBarFrame(
            parent,
            on_search=self._on_city_search
        )
        self.search_bar.pack(fill="x", expand=True)
        
        if self.logger:
            self.logger.info("🔍 Standard search bar created")
    
    def _create_fallback_search(self):
        """Create fallback search entry for testing."""
        fallback_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        fallback_frame.grid(row=0, column=2, sticky="e", padx=20, pady=10)
        
        # Fallback search entry (initially hidden)
        self.fallback_search_entry = ctk.CTkEntry(
            fallback_frame,
            placeholder_text="Fallback search...",
            width=200
        )
        # Don't pack initially - will be shown if needed
    
    def _create_content_panel(self):
        """Create the main content panel with 2-column layout."""
        self._log_method_call("_create_content_panel")
        
        # Create content frame
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # Configure 2-column grid
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        
        # Create main frame for 2-column layout
        self.main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20, columnspan=2)
        
        # Configure main frame grid
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Left column - Current weather
        self._create_current_weather_section()
        
        # Right column - Analytics
        self._create_analytics_panel()
    
    def _create_current_weather_section(self):
        """Create current weather section with title and card."""
        from ..components.weather_display import WeatherDisplayFrame
        
        # Create a container for the section
        self.weather_section = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        
        # Section title
        self.weather_title = ctk.CTkLabel(
            self.weather_section,
            text="CURRENT WEATHER",
            font=("Consolas", 14, "bold"),
            text_color="#00ff41",
            anchor="w"
        )
        self.weather_title.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Create the weather display
        self.weather_display = WeatherDisplayFrame(self.weather_section)
        self.weather_display.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Position the section in the main frame
        self.weather_section.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    
    def _create_analytics_panel(self):
        """Create temperature forecast panel."""
        try:
            from ..components.temperature_chart import TemperatureChart
        except ImportError:
            self._log_debug("TemperatureChart not available, creating placeholder")
            self._create_analytics_placeholder()
            return
        
        # Create a container for the analytics section
        self.analytics_section = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        
        # Section title
        self.forecast_title = ctk.CTkLabel(
            self.analytics_section,
            text="INTERACTIVE TEMPERATURE ANALYSIS",
            font=("Consolas", 14, "bold"),
            text_color="#00ff41",
            anchor="w"
        )
        self.forecast_title.pack(anchor="w", padx=10, pady=(0, 10))
        
        self.analytics_card = ctk.CTkFrame(
            self.analytics_section,
            fg_color="#1a1a1a",
            corner_radius=16,
            border_width=1,
            border_color="#333333"
        )
        self.analytics_card.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Chart container - Enhanced Temperature Chart
        self.temperature_chart = TemperatureChart(
            self.analytics_card
        )
        self.temperature_chart.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Position the section in the main frame
        self.analytics_section.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    
    def _create_analytics_placeholder(self):
        """Create placeholder when TemperatureChart is not available."""
        # Create a container for the analytics section
        self.analytics_section = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        
        # Section title
        self.forecast_title = ctk.CTkLabel(
            self.analytics_section,
            text="INTERACTIVE TEMPERATURE ANALYSIS",
            font=("Consolas", 14, "bold"),
            text_color="#00ff41",
            anchor="w"
        )
        self.forecast_title.pack(anchor="w", padx=10, pady=(0, 10))
        
        self.analytics_card = ctk.CTkFrame(
            self.analytics_section,
            fg_color="#1a1a1a",
            corner_radius=16,
            border_width=1,
            border_color="#333333"
        )
        self.analytics_card.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Placeholder text
        placeholder_label = ctk.CTkLabel(
            self.analytics_card,
            text="Temperature Chart Loading...",
            font=("Consolas", 16),
            text_color="#666666"
        )
        placeholder_label.pack(expand=True)
        
        # Position the section in the main frame
        self.analytics_section.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    
    def _update_responsive_layout(self):
        """Update layout for responsive design."""
        try:
            # Get current window size
            window_width = self.winfo_width()
            window_height = self.winfo_height()
            
            # Calculate scale factor
            base_width = self.MIN_WINDOW_WIDTH
            scale_factor = max(0.8, min(2.0, window_width / base_width))
            
            # Update component scaling if changed
            if abs(scale_factor - self._current_scale) > 0.1:
                self._current_scale = scale_factor
                self._update_component_scaling(scale_factor)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Responsive layout update failed: {e}")
    
    def _update_component_scaling(self, scale_factor: float):
        """Update component scaling based on window size."""
        self._log_method_call("_update_component_scaling", scale_factor)
        
        try:
            # Scale header height
            base_header_height = 120
            new_header_height = int(base_header_height * scale_factor)
            if self.header_frame:
                self.header_frame.configure(height=new_header_height)
            
            # Update search bar scaling
            if hasattr(self.search_bar, 'update_scaling'):
                self.search_bar.update_scaling(scale_factor)
            
            if hasattr(self.enhanced_search_bar, 'update_scaling'):
                self.enhanced_search_bar.update_scaling(scale_factor)
            
            # Update weather display scaling
            if hasattr(self.weather_display, 'update_scaling'):
                self.weather_display.update_scaling(scale_factor)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Component scaling update failed: {e}")
    
    def create_fallback_search_entry(self):
        """Show and return the fallback search entry for testing."""
        if self.fallback_search_entry:
            self.fallback_search_entry.pack(side="right")
            return self.fallback_search_entry
        return None
    
    def force_search_focus(self):
        """Force focus to the search widget."""
        try:
            if self.enhanced_search_bar and hasattr(self.enhanced_search_bar, 'focus_search'):
                self.enhanced_search_bar.focus_search()
            elif self.search_bar and hasattr(self.search_bar, 'focus_search'):
                self.search_bar.focus_search()
            elif self.fallback_search_entry:
                self.fallback_search_entry.focus()
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to focus search: {e}")