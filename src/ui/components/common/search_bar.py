"""Search Bar Component.

Reusable search bar component for location/city search functionality.
"""

from src.ui.theme import DataTerminalTheme
import customtkinter as ctk

class SearchBar(ctk.CTkFrame):
    """Reusable search bar component with enhanced functionality."""

    def __init__(
        self,
        parent,
        on_search=None,
        on_location_selected=None,
        placeholder="🔍 Enter city name...",
        **kwargs,
    ):
        """Initialize search bar.

        Args:
            parent: Parent widget
            on_search: Callback function for search action (search_term)
            on_location_selected: Callback for location selection (location_result)
            placeholder: Placeholder text for search entry
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.on_search = on_search
        self.on_location_selected = on_location_selected
        self.placeholder = placeholder

        # UI components
        self.search_entry = None
        self.search_button = None

        # Animation and interaction managers (optional)
        self.animation_manager = None
        self.micro_interactions = None

        # Track scheduled calls for cleanup
        self.scheduled_calls = set()

        self._create_ui()
        self._setup_interactions()

    def safe_after(self, delay_ms: int, callback, *args):
        """Safely schedule an after() call with error handling and tracking."""
        try:
            if not self.winfo_exists():
                return None
            
            if args:
                call_id = self.after(delay_ms, callback, *args)
            else:
                call_id = self.after(delay_ms, callback)
            self.scheduled_calls.add(call_id)
            return call_id
        except Exception as e:
            print(f"Error scheduling after() call: {e}")
            return None

    def _cleanup_scheduled_calls(self):
        """Cancel all scheduled calls to prevent TclError."""
        for call_id in self.scheduled_calls.copy():
            try:
                self.after_cancel(call_id)
            except Exception:
                pass
        self.scheduled_calls.clear()

    def destroy(self):
        """Override destroy to cleanup scheduled calls."""
        self._cleanup_scheduled_calls()
        super().destroy()

    def _create_ui(self):
        """Create the search bar UI components."""
        # Main search controls frame
        search_controls = ctk.CTkFrame(self, fg_color="transparent")
        search_controls.pack(fill="x")

        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_controls,
            placeholder_text=self.placeholder,
            width=450,
            height=40,
            corner_radius=20,
            border_color=DataTerminalTheme.BORDER,
            fg_color=DataTerminalTheme.BACKGROUND,
            text_color=DataTerminalTheme.TEXT,
            font=(DataTerminalTheme.FONT_FAMILY, 14),
        )
        self.search_entry.pack(side="left", padx=(0, 10))

        # Search button
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
            command=self._handle_search,
        )
        self.search_button.pack(side="left")

    def _setup_interactions(self):
        """Setup keyboard and interaction handlers."""
        # Bind Enter key to search
        self.search_entry.bind("<Return>", lambda e: self._handle_search())

        # Try to setup enhanced interactions if available
        self._setup_enhanced_interactions()

    def _setup_enhanced_interactions(self):
        """Setup enhanced animations and micro-interactions if available."""
        try:
            # Try to import and setup animation managers
            pass

            # Get parent's animation managers if available
            parent_widget = self.master
            while parent_widget:
                if hasattr(parent_widget, "animation_manager"):
                    self.animation_manager = parent_widget.animation_manager
                    break
                if hasattr(parent_widget, "micro_interactions"):
                    self.micro_interactions = parent_widget.micro_interactions
                    break
                parent_widget = getattr(parent_widget, "master", None)

            # Add micro-interactions to search button if available
            if self.micro_interactions:
                self.micro_interactions.add_hover_effect(self.search_button)
                self.micro_interactions.add_click_effect(self.search_button)

        except (ImportError, AttributeError):
            # Enhanced interactions not available, use basic functionality

            pass

    def _handle_search(self):
        """Handle search action with enhanced animations."""
        search_term = self.search_entry.get().strip()

        if search_term:
            # Add enhanced animations if available
            if self.micro_interactions:
                self.micro_interactions.add_ripple_effect(self.search_button)

            if self.animation_manager:
                self.animation_manager.pulse_animation(self.search_entry)

            # Call search callback
            if self.on_search:
                self.on_search(search_term)

            # Clear search entry with animation
            if self.animation_manager:
                self.animation_manager.fade_out(
                    self.search_entry, callback=lambda: self.search_entry.delete(0, "end")
                )
            else:
                self.search_entry.delete(0, "end")

        else:
            # Show warning for empty search
            if self.micro_interactions:
                self.micro_interactions.add_warning_pulse(self.search_entry)
            else:
                # Basic feedback - briefly change border color
                self._show_warning_feedback()

    def _show_warning_feedback(self):
        """Show basic warning feedback for empty search."""
        original_color = self.search_entry.cget("border_color")
        self.search_entry.configure(border_color="#ff6b6b")

        # Reset color after 1 second
        self.safe_after(1000, lambda: self.search_entry.configure(border_color=original_color))

    def handle_location_selected(self, location_result):
        """Handle location selection from enhanced search.

        Args:
            location_result: Location object with display_name, latitude, longitude, etc.
        """
        if self.on_location_selected:
            self.on_location_selected(location_result)

    def set_search_text(self, text):
        """Set the search entry text.

        Args:
            text: Text to set in search entry
        """
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, text)

    def get_search_text(self):
        """Get the current search entry text.

        Returns:
            str: Current search text
        """
        return self.search_entry.get().strip()

    def clear_search(self):
        """Clear the search entry."""
        self.search_entry.delete(0, "end")

    def set_placeholder(self, placeholder):
        """Update the placeholder text.

        Args:
            placeholder: New placeholder text
        """
        self.placeholder = placeholder
        self.search_entry.configure(placeholder_text=placeholder)

    def set_enabled(self, enabled):
        """Enable or disable the search bar.

        Args:
            enabled: True to enable, False to disable
        """
        state = "normal" if enabled else "disabled"
        self.search_entry.configure(state=state)
        self.search_button.configure(state=state)

    def focus_search(self):
        """Focus the search entry."""
        self.search_entry.focus()

    def set_search_callback(self, callback):
        """Update the search callback function.

        Args:
            callback: New search callback function
        """
        self.on_search = callback

    def set_location_callback(self, callback):
        """Update the location selection callback function.

        Args:
            callback: New location selection callback function
        """
        self.on_location_selected = callback

    def add_search_history(self, search_term):
        """Add a search term to history (for future enhancement).

        Args:
            search_term: Search term to add to history
        """
        # This could be enhanced to show search suggestions/history

    def show_suggestions(self, suggestions):
        """Show search suggestions (for future enhancement).

        Args:
            suggestions: List of suggestion strings
        """
        # This could be enhanced to show a dropdown with suggestions

    def hide_suggestions(self):
        """Hide search suggestions (for future enhancement)."""
        # This could be enhanced to hide the suggestions dropdown

class EnhancedSearchBar(SearchBar):
    """Enhanced search bar with autocomplete and location services."""

    def __init__(self, parent, location_service=None, **kwargs):
        """Initialize enhanced search bar.

        Args:
            parent: Parent widget
            location_service: Service for location search and geocoding
            **kwargs: Additional arguments passed to SearchBar
        """
        self.location_service = location_service
        self.suggestions_frame = None
        self.suggestion_labels = []

        super().__init__(parent, **kwargs)

    def _create_ui(self):
        """Create enhanced UI with suggestions dropdown."""
        super()._create_ui()

        # Create suggestions frame (initially hidden)
        self.suggestions_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        # Don't pack initially - will be shown when suggestions are available

    def _setup_interactions(self):
        """Setup enhanced interactions with autocomplete."""
        super()._setup_interactions()

        # Bind text change events for autocomplete
        self.search_entry.bind("<KeyRelease>", self._on_text_changed)
        self.search_entry.bind("<FocusOut>", lambda e: self.hide_suggestions())

    def _on_text_changed(self, event):
        """Handle text changes for autocomplete.

        Args:
            event: Tkinter event object
        """
        search_text = self.search_entry.get().strip()

        if len(search_text) >= 2 and self.location_service:
            # Get location suggestions
            try:
                suggestions = self.location_service.search_locations(search_text, limit=5)
                self.show_suggestions([s.display_name for s in suggestions])
            except Exception as e:
                print(f"Error getting location suggestions: {e}")
                self.hide_suggestions()
        else:
            self.hide_suggestions()

    def show_suggestions(self, suggestions):
        """Show autocomplete suggestions.

        Args:
            suggestions: List of suggestion strings
        """
        # Clear existing suggestions
        for label in self.suggestion_labels:
            label.destroy()
        self.suggestion_labels.clear()

        if not suggestions:
            self.hide_suggestions()
            return

        # Create suggestion labels
        for suggestion in suggestions[:5]:  # Limit to 5 suggestions
            label = ctk.CTkLabel(
                self.suggestions_frame,
                text=suggestion,
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                text_color=DataTerminalTheme.TEXT,
                anchor="w",
            )
            label.pack(fill="x", padx=8, pady=2)

            # Make clickable
            label.bind("<Button-1>", lambda e, s=suggestion: self._select_suggestion(s))
            label.bind(
                "<Enter>", lambda e, lbl=label: lbl.configure(text_color=DataTerminalTheme.PRIMARY)
            )
            label.bind(
                "<Leave>", lambda e, lbl=label: lbl.configure(text_color=DataTerminalTheme.TEXT)
            )

            self.suggestion_labels.append(label)

        # Show suggestions frame
        self.suggestions_frame.pack(fill="x", pady=(5, 0))

    def _select_suggestion(self, suggestion):
        """Handle suggestion selection.

        Args:
            suggestion: Selected suggestion string
        """
        self.set_search_text(suggestion)
        self.hide_suggestions()
        self._handle_search()

    def hide_suggestions(self):
        """Hide autocomplete suggestions."""
        if self.suggestions_frame:
            self.suggestions_frame.pack_forget()
