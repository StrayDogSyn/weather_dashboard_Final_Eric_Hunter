import tkinter as tk

import customtkinter as ctk

from src.ui.styles.component_styles import ComponentStyles
from src.ui.styles.layout_styles import LayoutStyles

try:
    from src.ui.components.search_components import EnhancedSearchBar
except ImportError:
    EnhancedSearchBar = None


class HeaderComponent(ctk.CTkFrame):
    """Professional header component with branding and search functionality."""

    def __init__(self, parent, on_search_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_search_callback = on_search_callback
        self.current_location_label = None
        self._setup_header()

    def _setup_header(self):
        """Setup the header with branding and search."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)

        # Title section
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=LayoutStyles.PADDING["medium"])

        # Main title
        title_label = ctk.CTkLabel(
            title_frame,
            text="PROJECT CODEFRONT",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1f2937", "#f9fafb"),
        )
        title_label.pack(anchor="w")

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Professional Weather Dashboard",
            font=ctk.CTkFont(size=12),
            text_color=("#6b7280", "#9ca3af"),
        )
        subtitle_label.pack(anchor="w")

        # Search section
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=0, column=1, sticky="ew", padx=LayoutStyles.PADDING["medium"])
        search_frame.grid_columnconfigure(0, weight=1)

        # Try enhanced search first, fallback to basic
        if EnhancedSearchBar and self.on_search_callback:
            try:
                self.search_bar = EnhancedSearchBar(
                    search_frame,
                    on_location_selected=self.on_search_callback,
                    placeholder="Search for a city...",
                )
                self.search_bar.grid(
                    row=0, column=0, sticky="ew", pady=LayoutStyles.PADDING["small"]
                )
            except Exception:
                self._create_basic_search(search_frame)
        else:
            self._create_basic_search(search_frame)

        # Location indicator
        location_frame = ctk.CTkFrame(self, fg_color="transparent")
        location_frame.grid(row=0, column=2, sticky="e", padx=LayoutStyles.PADDING["medium"])

        self.current_location_label = ctk.CTkLabel(
            location_frame,
            text="📍 Current: Not set",
            font=ctk.CTkFont(size=12),
            text_color=("#6b7280", "#9ca3af"),
        )
        self.current_location_label.pack(anchor="e")

    def _create_basic_search(self, parent):
        """Create basic search functionality as fallback."""
        search_container = ctk.CTkFrame(parent, fg_color="transparent")
        search_container.grid(row=0, column=0, sticky="ew")
        search_container.grid_columnconfigure(0, weight=1)

        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_container, placeholder_text="Enter city name...", **ComponentStyles.SEARCH_ENTRY
        )
        self.search_entry.grid(
            row=0, column=0, sticky="ew", padx=(0, LayoutStyles.SPACING["normal"])
        )
        self.search_entry.bind("<Return>", self._on_search_enter)

        # Search button
        search_button = ctk.CTkButton(
            search_container, text="🔍", width=40, height=35, command=self._on_search_click
        )
        search_button.grid(row=0, column=1, sticky="e")

    def _on_search_enter(self, event):
        """Handle search on Enter key."""
        self._perform_search()

    def _on_search_click(self):
        """Handle search button click."""
        self._perform_search()

    def _perform_search(self):
        """Perform the search operation."""
        if hasattr(self, "search_entry") and self.on_search_callback:
            city = self.search_entry.get().strip()
            if city:
                # Create a location result object similar to enhanced search
                location_result = {"display_name": city, "lat": None, "lon": None}
                self.on_search_callback(location_result)
                self.search_entry.delete(0, tk.END)

    def update_current_location(self, location_name):
        """Update the current location display."""
        if self.current_location_label:
            self.current_location_label.configure(text=f"📍 Current: {location_name}")

    def get_search_value(self):
        """Get current search value."""
        if hasattr(self, "search_entry"):
            return self.search_entry.get().strip()
        elif hasattr(self, "search_bar"):
            return getattr(self.search_bar, "get_value", lambda: "")() or ""
        return ""

    def clear_search(self):
        """Clear the search field."""
        if hasattr(self, "search_entry"):
            self.search_entry.delete(0, tk.END)
        elif hasattr(self, "search_bar") and hasattr(self.search_bar, "clear"):
            self.search_bar.clear()
