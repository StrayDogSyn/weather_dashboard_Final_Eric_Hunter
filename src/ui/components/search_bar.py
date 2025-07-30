"""Basic Search Bar Component

Simple search bar fallback when enhanced features are not available.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional

from ui.theme import DataTerminalTheme


class SearchBarFrame(ctk.CTkFrame):
    """Basic search bar component."""
    
    def __init__(self, parent, on_search: Callable[[str], None], **kwargs):
        """Initialize basic search bar."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("main"), **kwargs)
        
        self.on_search = on_search
        
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
        entry_style = DataTerminalTheme.get_entry_style()
        if 'font' in entry_style:
            del entry_style['font']
        
        self.search_entry = ctk.CTkEntry(
            self.search_container,
            placeholder_text="🔍 Search cities...",
            width=300,
            height=42,
            state="normal",
            font=("Segoe UI", 12),
            **entry_style
        )
        
        # Search button
        primary_style = DataTerminalTheme.get_button_style("primary")
        if 'font' in primary_style:
            del primary_style['font']
        
        self.search_button = ctk.CTkButton(
            self.search_container,
            text="SEARCH",
            width=85,
            height=42,
            font=("Segoe UI", 12, "bold"),
            command=self._on_search_click,
            **primary_style
        )
    
    def _setup_layout(self) -> None:
        """Arrange widgets."""
        # Main search container
        self.search_container.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.search_container.grid_columnconfigure(0, weight=1)
        
        # Search entry and button
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_button.grid(row=0, column=1, sticky="e")
    
    def _setup_bindings(self) -> None:
        """Setup event bindings."""
        self.search_entry.bind("<Return>", self._on_enter_key)
        
        # Set initial focus
        self.after(100, self._set_initial_focus)
    
    def _on_enter_key(self, event) -> None:
        """Handle Enter key press."""
        self._on_search_click()
    
    def _on_search_click(self) -> None:
        """Handle search button click."""
        query = self.search_entry.get().strip()
        if query and self.on_search:
            self.on_search(query)
    
    def _set_initial_focus(self) -> None:
        """Set initial focus to search entry."""
        try:
            self.search_entry.focus_set()
        except (AttributeError, RuntimeError):
            pass
    
    def get_search_text(self) -> str:
        """Get current search text."""
        return self.search_entry.get().strip()
    
    def set_search_text(self, text: str) -> None:
        """Set search text."""
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, text)
    
    def clear_search(self) -> None:
        """Clear search entry."""
        self.search_entry.delete(0, tk.END)
    
    def focus_search(self) -> None:
        """Focus the search entry."""
        try:
            self.search_entry.focus_set()
        except (AttributeError, RuntimeError):
            pass