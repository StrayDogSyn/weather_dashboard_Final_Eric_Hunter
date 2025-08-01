"""Maps Component - Interactive Google Maps Integration

Provides location selection, place search, and map visualization
for the weather dashboard application.
"""

import logging
import threading
import tkinter as tk
import webbrowser
from io import BytesIO
from typing import Callable, List, Optional, Tuple

import customtkinter as ctk
import requests
from PIL import Image, ImageTk

from services.config_service import ConfigService
from services.maps_service import (
    GoogleMapsService,
    PlaceResult,
)

from ..theme import DataTerminalTheme


class MapsComponent(ctk.CTkFrame):
    """Interactive Maps component with location search and visualization."""

    def __init__(
        self, parent, config_service: ConfigService, on_location_selected: Optional[Callable] = None
    ):
        """Initialize Maps component."""
        super().__init__(parent, fg_color="transparent")

        self.config_service = config_service
        self.maps_service = GoogleMapsService(config_service)
        self.on_location_selected = on_location_selected
        self.logger = logging.getLogger("weather_dashboard.maps_component")

        # Current state
        self.current_location: Optional[Tuple[float, float]] = None
        self.current_address: str = ""
        self.search_results: List[PlaceResult] = []
        self.selected_place: Optional[PlaceResult] = None

        # UI Colors from theme
        self.BACKGROUND = DataTerminalTheme.BACKGROUND
        self.CARD_COLOR = DataTerminalTheme.CARD_BG
        self.ACCENT_COLOR = DataTerminalTheme.PRIMARY
        self.TEXT_PRIMARY = DataTerminalTheme.TEXT
        self.TEXT_SECONDARY = DataTerminalTheme.TEXT_SECONDARY
        self.BORDER_COLOR = DataTerminalTheme.BORDER

        self._create_widgets()
        self.logger.info("🗺️ Maps component initialized")

    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header section
        self._create_header()

        # Main content area
        self._create_main_content()

    def _create_header(self) -> None:
        """Create header with search and controls."""
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=self.CARD_COLOR,
            corner_radius=12,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            self.header_frame,
            text="🗺️ MAPS & LOCATIONS",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE, "bold"),
            text_color=self.ACCENT_COLOR,
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        # Search controls
        search_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        search_frame.grid(row=0, column=1, sticky="ew", padx=20, pady=15)
        search_frame.grid_columnconfigure(0, weight=1)

        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search places, addresses, or landmarks...",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            fg_color=self.BACKGROUND,
            border_color=self.BORDER_COLOR,
            text_color=self.TEXT_PRIMARY,
            placeholder_text_color=self.TEXT_SECONDARY,
            height=40,
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<Return>", self._on_search)

        # Search button
        self.search_button = ctk.CTkButton(
            search_frame,
            text="Search",
            command=self._on_search,
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            fg_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.SUCCESS,
            text_color=self.BACKGROUND,
            width=100,
            height=40,
        )
        self.search_button.grid(row=0, column=1)

        # Current location button
        self.location_button = ctk.CTkButton(
            search_frame,
            text="📍 Current",
            command=self._get_current_location,
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            fg_color="transparent",
            border_width=1,
            border_color=self.ACCENT_COLOR,
            text_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.HOVER,
            width=80,
            height=40,
        )
        self.location_button.grid(row=0, column=2, padx=(10, 0))

    def _create_main_content(self) -> None:
        """Create main content area with map and results."""
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Left panel - Search results and details
        self._create_left_panel()

        # Right panel - Map visualization
        self._create_right_panel()

    def _create_left_panel(self) -> None:
        """Create left panel with search results and location details."""
        self.left_panel = ctk.CTkFrame(
            self.content_frame,
            fg_color=self.CARD_COLOR,
            corner_radius=12,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(1, weight=1)

        # Panel title
        panel_title = ctk.CTkLabel(
            self.left_panel,
            text="📍 SEARCH RESULTS",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            text_color=self.ACCENT_COLOR,
        )
        panel_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Scrollable results frame
        self.results_frame = ctk.CTkScrollableFrame(
            self.left_panel,
            fg_color="transparent",
            scrollbar_fg_color=self.BACKGROUND,
            scrollbar_button_color=self.ACCENT_COLOR,
            scrollbar_button_hover_color=DataTerminalTheme.SUCCESS,
        )
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.results_frame.grid_columnconfigure(0, weight=1)

        # Initial message
        self.no_results_label = ctk.CTkLabel(
            self.results_frame,
            text="🔍 Enter a search query to find places\nand locations on the map",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=self.TEXT_SECONDARY,
            justify="center",
        )
        self.no_results_label.grid(row=0, column=0, pady=50)

    def _create_right_panel(self) -> None:
        """Create right panel with map visualization."""
        self.right_panel = ctk.CTkFrame(
            self.content_frame,
            fg_color=self.CARD_COLOR,
            corner_radius=12,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)

        # Panel header
        map_header = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        map_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        map_header.grid_columnconfigure(0, weight=1)

        # Map title
        map_title = ctk.CTkLabel(
            map_header,
            text="🗺️ MAP VIEW",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            text_color=self.ACCENT_COLOR,
        )
        map_title.grid(row=0, column=0, sticky="w")

        # Map controls
        controls_frame = ctk.CTkFrame(map_header, fg_color="transparent")
        controls_frame.grid(row=0, column=1, sticky="e")

        # Open in browser button
        self.browser_button = ctk.CTkButton(
            controls_frame,
            text="🌐 Open in Browser",
            command=self._open_in_browser,
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            fg_color="transparent",
            border_width=1,
            border_color=self.ACCENT_COLOR,
            text_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.HOVER,
            width=120,
            height=30,
        )
        self.browser_button.grid(row=0, column=0, padx=(0, 10))

        # Directions button
        self.directions_button = ctk.CTkButton(
            controls_frame,
            text="🧭 Directions",
            command=self._get_directions,
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            fg_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.SUCCESS,
            text_color=self.BACKGROUND,
            width=100,
            height=30,
        )
        self.directions_button.grid(row=0, column=1)

        # Map display area
        self.map_frame = ctk.CTkFrame(self.right_panel, fg_color=self.BACKGROUND, corner_radius=8)
        self.map_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.map_frame.grid_columnconfigure(0, weight=1)
        self.map_frame.grid_rowconfigure(0, weight=1)

        # Map placeholder
        self.map_label = ctk.CTkLabel(
            self.map_frame,
            text="🗺️\n\nMap will appear here\nafter searching for a location",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE),
            text_color=self.TEXT_SECONDARY,
            justify="center",
        )
        self.map_label.grid(row=0, column=0, pady=50)

    def _on_search(self, event=None) -> None:
        """Handle search button click or Enter key."""
        query = self.search_entry.get().strip()
        if not query:
            return

        self.search_button.configure(text="Searching...", state="disabled")
        threading.Thread(target=self._perform_search, args=(query,), daemon=True).start()

    def _perform_search(self, query: str) -> None:
        """Perform place search in background thread."""
        try:
            self.logger.info(f"🔍 Searching for: {query}")

            # Search for places
            results = self.maps_service.search_places(query, location=self.current_location)

            # Update UI in main thread
            self.after(0, self._update_search_results, results)

        except Exception as e:
            self.logger.error(f"❌ Search failed: {e}")
            self.after(0, self._show_search_error, str(e))
        finally:

            def reset_search_button():
                self.search_button.configure(text="Search", state="normal")

            self.after(0, reset_search_button)

    def _update_search_results(self, results: List[PlaceResult]) -> None:
        """Update search results display."""
        # Clear existing results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.search_results = results

        if not results:
            # Show no results message
            no_results = ctk.CTkLabel(
                self.results_frame,
                text="❌ No results found\nTry a different search term",
                font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
                text_color=self.TEXT_SECONDARY,
                justify="center",
            )
            no_results.grid(row=0, column=0, pady=50)
            return

        # Display results
        for i, result in enumerate(results):
            self._create_result_card(result, i)

        self.logger.info(f"✅ Displayed {len(results)} search results")

    def _create_result_card(self, result: PlaceResult, index: int) -> None:
        """Create a card for a search result."""
        card = ctk.CTkFrame(
            self.results_frame,
            fg_color=self.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        card.grid(row=index, column=0, sticky="ew", pady=5)
        card.grid_columnconfigure(0, weight=1)

        # Make card clickable
        def on_click(event=None):
            self._select_place(result)

        card.bind("<Button-1>", on_click)

        # Place name
        name_label = ctk.CTkLabel(
            card,
            text=result.name,
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            text_color=self.TEXT_PRIMARY,
            anchor="w",
        )
        name_label.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        name_label.bind("<Button-1>", on_click)

        # Address
        address_label = ctk.CTkLabel(
            card,
            text=result.formatted_address,
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            text_color=self.TEXT_SECONDARY,
            anchor="w",
            wraplength=300,
        )
        address_label.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 5))
        address_label.bind("<Button-1>", on_click)

        # Details row
        details_frame = ctk.CTkFrame(card, fg_color="transparent")
        details_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        details_frame.grid_columnconfigure(1, weight=1)

        # Rating
        if result.rating:
            rating_label = ctk.CTkLabel(
                details_frame,
                text=f"⭐ {result.rating}",
                font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
                text_color=self.ACCENT_COLOR,
            )
            rating_label.grid(row=0, column=0, sticky="w")
            rating_label.bind("<Button-1>", on_click)

        # Select button
        select_button = ctk.CTkButton(
            details_frame,
            text="Select",
            command=lambda: self._select_place(result),
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            fg_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.SUCCESS,
            text_color=self.BACKGROUND,
            width=80,
            height=25,
        )
        select_button.grid(row=0, column=2, sticky="e")

    def _select_place(self, place: PlaceResult) -> None:
        """Select a place and update map."""
        self.selected_place = place
        self.current_location = (place.latitude, place.longitude)
        self.current_address = place.formatted_address

        self.logger.info(f"📍 Selected place: {place.name}")

        # Update map
        self._update_map()

        # Notify parent component
        if self.on_location_selected:
            self.on_location_selected(place.latitude, place.longitude, place.name)

    def _update_map(self) -> None:
        """Update map display with current location."""
        if not self.current_location:
            return

        try:
            # Get static map URL
            map_url = self.maps_service.get_static_map_url(
                center=self.current_location,
                zoom=15,
                size=(400, 300),
                markers=[self.current_location],
            )

            if map_url:
                # Load map image in background
                threading.Thread(target=self._load_map_image, args=(map_url,), daemon=True).start()
            else:
                self._show_map_placeholder("Map unavailable")

        except Exception as e:
            self.logger.error(f"❌ Failed to update map: {e}")
            self._show_map_placeholder("Map error")

    def _load_map_image(self, url: str) -> None:
        """Load map image from URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Load image
            image = Image.open(BytesIO(response.content))
            photo = ImageTk.PhotoImage(image)

            # Update UI in main thread
            self.after(0, self._display_map_image, photo)

        except Exception as e:
            self.logger.error(f"❌ Failed to load map image: {e}")
            self.after(0, self._show_map_placeholder, "Failed to load map")

    def _display_map_image(self, photo: ImageTk.PhotoImage) -> None:
        """Display map image in UI."""
        # Clear existing content
        for widget in self.map_frame.winfo_children():
            widget.destroy()

        # Display map image
        map_image_label = tk.Label(self.map_frame, image=photo, bg=self.BACKGROUND)
        map_image_label.image = photo  # Keep a reference
        map_image_label.grid(row=0, column=0, padx=10, pady=10)

        # Add location info
        info_frame = ctk.CTkFrame(self.map_frame, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        if self.selected_place:
            location_info = ctk.CTkLabel(
                info_frame,
                text=f"📍 {self.selected_place.name}\n{self.current_address}",
                font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
                text_color=self.TEXT_PRIMARY,
                justify="center",
            )
            location_info.pack(pady=5)

    def _show_map_placeholder(self, message: str) -> None:
        """Show placeholder message in map area."""
        # Clear existing content
        for widget in self.map_frame.winfo_children():
            widget.destroy()

        placeholder = ctk.CTkLabel(
            self.map_frame,
            text=f"🗺️\n\n{message}",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE),
            text_color=self.TEXT_SECONDARY,
            justify="center",
        )
        placeholder.grid(row=0, column=0, pady=50)

    def _show_search_error(self, error: str) -> None:
        """Show search error message."""
        # Clear existing results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        error_label = ctk.CTkLabel(
            self.results_frame,
            text=f"❌ Search Error\n{error}",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=DataTerminalTheme.ERROR,
            justify="center",
        )
        error_label.grid(row=0, column=0, pady=50)

    def _get_current_location(self) -> None:
        """Get user's current location (placeholder implementation)."""
        # This would typically use geolocation APIs
        # For now, we'll use a default location
        self.current_location = (40.7128, -74.0060)  # New York City
        self.current_address = "New York, NY, USA"

        self.logger.info("📍 Using default location: New York City")
        self._update_map()

        # Show message
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, "New York, NY")
        self._on_search()

    def _open_in_browser(self) -> None:
        """Open current location in Google Maps browser."""
        if not self.current_location:
            return

        lat, lng = self.current_location
        url = f"https://www.google.com/maps/@{lat},{lng},15z"
        webbrowser.open(url)
        self.logger.info(f"🌐 Opened location in browser: {lat}, {lng}")

    def _get_directions(self) -> None:
        """Get directions to selected location."""
        if not self.selected_place:
            return

        # Open directions in browser
        destination = self.selected_place.formatted_address.replace(" ", "+")
        url = f"https://www.google.com/maps/dir//{destination}"
        webbrowser.open(url)
        self.logger.info(f"🧭 Opened directions to: {self.selected_place.name}")

    def set_location(self, latitude: float, longitude: float, address: str = "") -> None:
        """Set location programmatically."""
        self.current_location = (latitude, longitude)
        self.current_address = address

        if address:
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, address)

        self._update_map()
        self.logger.info(f"📍 Location set to: {latitude}, {longitude}")

    def get_current_location(self) -> Optional[Tuple[float, float]]:
        """Get current selected location."""
        return self.current_location

    def clear_selection(self) -> None:
        """Clear current selection and reset map."""
        self.current_location = None
        self.current_address = ""
        self.selected_place = None
        self.search_results = []

        # Clear UI
        self.search_entry.delete(0, tk.END)

        # Clear results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.no_results_label = ctk.CTkLabel(
            self.results_frame,
            text="🔍 Enter a search query to find places\nand locations on the map",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=self.TEXT_SECONDARY,
            justify="center",
        )
        self.no_results_label.grid(row=0, column=0, pady=50)

        # Clear map
        self._show_map_placeholder("Map will appear here\nafter searching for a location")

        self.logger.info("🗑️ Maps selection cleared")
