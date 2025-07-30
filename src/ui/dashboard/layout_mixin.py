"""Layout Management Mixin

Handles UI layout, component creation, and responsive design.
"""

import customtkinter as ctk
from typing import Optional

from .base_dashboard import BaseDashboard
from ui.components.weather_display import WeatherDisplayFrame
from ui.components.search_bar import SearchBarFrame

# Enhanced features check
try:
    from ui.components.enhanced_search_bar import EnhancedSearchBarFrame
    ENHANCED_SEARCH_AVAILABLE = True
except ImportError:
    ENHANCED_SEARCH_AVAILABLE = False


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
        
        # Configure grid weights for responsive design
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Content
        self.grid_columnconfigure(0, weight=1)
        
        # Create main layout components
        self._create_header()
        self._create_content_panel()
        
        # Apply initial responsive layout
        self._update_responsive_layout()
    
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
        search_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        search_container.grid(row=0, column=1, sticky="ew", padx=20, pady=10)
        
        # Choose search component based on enhanced features
        if self.use_enhanced_features and ENHANCED_SEARCH_AVAILABLE:
            self._create_enhanced_search(search_container)
        else:
            self._create_standard_search(search_container)
    
    def _create_enhanced_search(self, parent):
        """Create enhanced search bar with autocomplete."""
        try:
            from ui.components.enhanced_search_bar import EnhancedSearchBarFrame
            
            self.enhanced_search_bar = EnhancedSearchBarFrame(
                parent,
                on_search=self._on_city_search,
                on_location_detect=self._on_location_detect,
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
        self.search_bar = SearchBarFrame(
            parent,
            on_search=self._on_city_search,
            on_location_detect=self._on_location_detect
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
        """Create the main content panel for weather display."""
        self._log_method_call("_create_content_panel")
        
        # Create content frame
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # Configure content grid
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Create weather display
        self.weather_display = WeatherDisplayFrame(self.content_frame)
        self.weather_display.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    
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