"""Search Bar Component

City search with autocomplete and suggestions.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional, List, Dict, Any
import threading
import time

from ui.theme import DataTerminalTheme
from utils.helpers import Debouncer


class SearchSuggestionFrame(ctk.CTkFrame):
    """Dropdown frame for search suggestions."""
    
    def __init__(self, parent, on_select: Callable[[Dict[str, str]], None], **kwargs):
        """Initialize suggestion frame."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("default"), **kwargs)
        
        self.on_select = on_select
        self.suggestion_buttons: List[ctk.CTkButton] = []
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Initially hidden
        self.grid_remove()
    
    def show_suggestions(self, suggestions: List[Dict[str, str]]) -> None:
        """Show suggestion dropdown."""
        # Clear existing buttons
        self.clear_suggestions()
        
        if not suggestions:
            self.grid_remove()
            return
        
        # Create suggestion buttons
        for i, suggestion in enumerate(suggestions[:5]):  # Limit to 5 suggestions
            button = ctk.CTkButton(
                self,
                text=suggestion.get('display', suggestion.get('name', '')),
                command=lambda s=suggestion: self._on_suggestion_click(s),
                **DataTerminalTheme.get_button_style("secondary")
            )
            button.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            self.suggestion_buttons.append(button)
        
        # Show the frame
        self.grid()
    
    def clear_suggestions(self) -> None:
        """Clear all suggestion buttons."""
        for button in self.suggestion_buttons:
            button.destroy()
        self.suggestion_buttons.clear()
        self.grid_remove()
    
    def _on_suggestion_click(self, suggestion: Dict[str, str]) -> None:
        """Handle suggestion button click."""
        self.on_select(suggestion)
        self.clear_suggestions()


class SearchBarFrame(ctk.CTkFrame):
    """Search bar with autocomplete functionality."""
    
    def __init__(self, parent, on_search: Callable[[str], None], 
                 on_suggestion_select: Callable[[Dict[str, str]], None], **kwargs):
        """Initialize search bar."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("main"), **kwargs)
        
        self.on_search = on_search
        self.on_suggestion_select = on_suggestion_select
        
        # Search state
        self.search_thread: Optional[threading.Thread] = None
        self.last_search_time = 0
        self.search_delay = 0.5  # Delay before searching
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
    
    def _create_widgets(self) -> None:
        """Create search widgets."""
        # Search container
        self.search_container = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        # Search entry
        self.search_entry = ctk.CTkEntry(
            self.search_container,
            placeholder_text="🔍 Enter city name...",
            height=40,
            **DataTerminalTheme.get_entry_style()
        )
        
        # Search button
        self.search_button = ctk.CTkButton(
            self.search_container,
            text="SEARCH",
            width=100,
            height=40,
            command=self._on_search_click,
            **DataTerminalTheme.get_button_style("primary")
        )
        
        # Current city display
        self.current_city_label = ctk.CTkLabel(
            self.search_container,
            text="",
            **DataTerminalTheme.get_label_style("caption")
        )
        
        # Suggestion dropdown
        self.suggestion_frame = SearchSuggestionFrame(
            self,
            on_select=self._on_suggestion_select
        )
    
    def _setup_layout(self) -> None:
        """Arrange widgets."""
        # Search container
        self.search_container.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.search_container.grid_columnconfigure(0, weight=1)
        
        # Search widgets
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_button.grid(row=0, column=1, sticky="e")
        self.current_city_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        
        # Suggestion dropdown (positioned below search container)
        self.suggestion_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
    
    def _setup_bindings(self) -> None:
        """Setup event bindings."""
        # Entry events
        self.search_entry.bind("<Return>", self._on_enter_key)
        self.search_entry.bind("<KeyRelease>", self._on_key_release)
        self.search_entry.bind("<FocusOut>", self._on_focus_out)
        
        # Click outside to hide suggestions
        self.bind("<Button-1>", self._on_click_outside)
    
    def _on_search_click(self) -> None:
        """Handle search button click."""
        query = self.search_entry.get().strip()
        if query:
            self.suggestion_frame.clear_suggestions()
            self.on_search(query)
    
    def _on_enter_key(self, event) -> None:
        """Handle Enter key press."""
        self._on_search_click()
    
    def _on_key_release(self, event) -> None:
        """Handle key release for autocomplete."""
        # Ignore special keys
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Tab', 'Return', 'Escape']:
            return
        
        query = self.search_entry.get().strip()
        
        if len(query) < 2:
            self.suggestion_frame.clear_suggestions()
            return
        
        # Debounce search requests
        self.last_search_time = time.time()
        
        if self.search_thread and self.search_thread.is_alive():
            return  # Previous search still running
        
        self.search_thread = threading.Thread(
            target=self._delayed_search,
            args=(query, self.last_search_time),
            daemon=True
        )
        self.search_thread.start()
    
    def _delayed_search(self, query: str, search_time: float) -> None:
        """Perform delayed search for autocomplete."""
        time.sleep(self.search_delay)
        
        # Check if this search is still relevant
        if search_time != self.last_search_time:
            return
        
        # Simulate city search (in real app, this would call weather service)
        suggestions = self._get_city_suggestions(query)
        
        # Update UI on main thread
        self.after(0, self._show_suggestions, suggestions)
    
    def _get_city_suggestions(self, query: str) -> List[Dict[str, str]]:
        """Get city suggestions for autocomplete."""
        # This is a simplified implementation
        # In a real app, this would call the weather service's search_cities method
        
        # Sample cities for demonstration
        sample_cities = [
            {'name': 'New York', 'country': 'US', 'display': 'New York, US'},
            {'name': 'London', 'country': 'GB', 'display': 'London, GB'},
            {'name': 'Paris', 'country': 'FR', 'display': 'Paris, FR'},
            {'name': 'Tokyo', 'country': 'JP', 'display': 'Tokyo, JP'},
            {'name': 'Sydney', 'country': 'AU', 'display': 'Sydney, AU'},
            {'name': 'Berlin', 'country': 'DE', 'display': 'Berlin, DE'},
            {'name': 'Moscow', 'country': 'RU', 'display': 'Moscow, RU'},
            {'name': 'Toronto', 'country': 'CA', 'display': 'Toronto, CA'},
            {'name': 'Mumbai', 'country': 'IN', 'display': 'Mumbai, IN'},
            {'name': 'Beijing', 'country': 'CN', 'display': 'Beijing, CN'},
        ]
        
        # Filter cities based on query
        query_lower = query.lower()
        matching_cities = [
            city for city in sample_cities
            if query_lower in city['name'].lower()
        ]
        
        return matching_cities[:5]  # Return top 5 matches
    
    def _show_suggestions(self, suggestions: List[Dict[str, str]]) -> None:
        """Show autocomplete suggestions."""
        self.suggestion_frame.show_suggestions(suggestions)
    
    def _on_suggestion_select(self, suggestion: Dict[str, str]) -> None:
        """Handle suggestion selection."""
        # Update search entry
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, suggestion.get('name', ''))
        
        # Clear suggestions
        self.suggestion_frame.clear_suggestions()
        
        # Trigger search
        self.on_suggestion_select(suggestion)
    
    def _on_focus_out(self, event) -> None:
        """Handle focus out event."""
        # Delay hiding suggestions to allow clicking on them
        self.after(200, self._check_and_hide_suggestions)
    
    def _on_click_outside(self, event) -> None:
        """Handle click outside search area."""
        # Check if click is outside suggestion frame
        widget = event.widget
        if not self._is_child_of(widget, self.suggestion_frame):
            self.suggestion_frame.clear_suggestions()
    
    def _check_and_hide_suggestions(self) -> None:
        """Check if suggestions should be hidden."""
        # Hide suggestions if search entry doesn't have focus
        if self.focus_get() != self.search_entry:
            self.suggestion_frame.clear_suggestions()
    
    def _is_child_of(self, widget, parent) -> bool:
        """Check if widget is a child of parent."""
        while widget:
            if widget == parent:
                return True
            widget = widget.master
        return False
    
    def set_current_city(self, city: str) -> None:
        """Set the current city display."""
        self.current_city_label.configure(text=f"Current: {city}")
    
    def clear_current_city(self) -> None:
        """Clear the current city display."""
        self.current_city_label.configure(text="")
    
    def get_search_text(self) -> str:
        """Get current search text."""
        return self.search_entry.get().strip()
    
    def set_search_text(self, text: str) -> None:
        """Set search text."""
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, text)
    
    def clear_search(self) -> None:
        """Clear search entry and suggestions."""
        self.search_entry.delete(0, tk.END)
        self.suggestion_frame.clear_suggestions()